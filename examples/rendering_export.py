"""Water for a renderer: coefficients per RGB channel, a phase function's
g, and spectra, with how far each simplification moves them.

For people who render water, in film, games or simulation, and set its
absorption, scattering and phase function by eye:

    python examples/rendering_export.py            # print everything
    python examples/rendering_export.py out/       # also write the files

It fits one extinction, absorption and scattering coefficient per channel
of three RGB spaces to two Jerlov types, says how far one exponential per
channel is from the colour the spectrum gives, finds a Henyey-Greenstein
g for each of Petzold's eight stations in the two ways the package
offers, and writes one water as a Mitsuba 3 medium (RGB and spectral), a
pbrt-v4 medium (spectral) and the values of Blender's Volume Absorption
and Volume Scatter nodes (DECISIONS.md section 82). Nothing is rendered.
"""

import pathlib
import re
import sys
import warnings

import numpy as np

import jerlov


def rule(title):
    print(f"\n{title}\n" + "-" * len(title))


def _banner():
    """Say which copy of the package is being used.

    Running ``python examples/foo.py`` puts ``examples/`` on sys.path, not the
    current directory, so an installed copy wins over the working tree. That
    is easy to miss and gives confusing failures; ``pip install -e .`` in the
    repository is the usual fix.
    """
    print(f"jerlov {jerlov.__version__} from {jerlov.__file__}")


#: Williamson & Hollins (2022), the package's default source: a and b
#: measured, not inverted from Kd.
TYPES = ("III", "1C")
#: D65 as the light that enters the water: daylight above the surface.
#: Under water the light at that depth would be the honest choice.
ILLUMINANT = jerlov.d65()
#: The distances the scene's light travels through water.
RANGE_M = (0.5, 10.0)
RANGES_M = ((0.5, 5.0), (0.5, 10.0), (0.5, 20.0))
#: The water written out for the renderers, and the Petzold station whose
#: b at 530 nm is nearest its own.
RENDER_TYPE = "III"
#: Mitsuba 3's spectral variants sample 360-830 nm (MI_CIE_MIN and
#: MI_CIE_MAX) and, with Mitsuba 3.9.1, render NaN where a medium's
#: spectrum is not defined. Williamson & Hollins stop at 800 nm, so this
#: example holds the 800 nm values to 830 nm: its own choice, not the
#: package's, where the CIE x-bar has about a millionth of its weight.
SPECTRAL_RANGE_NM = (360.0, 800.0)
HELD_TO_NM = 830.0


def caught_by_type(caught, function, *args, **kwargs):
    """Call, recording the package's warnings by type to report them."""
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        warnings.simplefilter("always", jerlov.CoverageWarning)
        result = function(*args, **kwargs)
    caught.update(f"{w.category.__name__}: {summarised(str(w.message))}"
                  for w in seen)
    return result


def summarised(message):
    """A provenance warning lists every flagged wavelength; give ranges."""
    head, sep, tail = message.partition(" rests on flagged values: ")
    if not sep:
        return message
    found = {}
    for label, nm in re.findall(r"([\w ]+?) at ([\d.]+) nm", tail):
        found.setdefault(label.strip(), []).append(float(nm))
    parts = []
    for label, values in found.items():
        values = sorted(values)
        spans, start, last = [], values[0], values[0]
        for v in values[1:]:
            if v - last > 1:
                spans.append((start, last))
                start = v
            last = v
        spans.append((start, last))
        parts.append(label + " at " + ", ".join(
            f"{a:g}" if a == b else f"{a:g}-{b:g}" for a, b in spans) + " nm")
    return f"{head} rests on flagged values: {'; '.join(parts)}"


def rgb_part(caught):
    rule("1. One coefficient per channel")
    print(f"""Light of D65 crossing {RANGE_M[0]:g}-{RANGE_M[1]:g} m of water, fitted with one
exponential per channel. sigma_t is the extinction, the albedo sigma_s /
sigma_t, and "error" the largest relative difference between the
exponential and the channel's true transmittance over the range.""")
    table = {}
    for water_type in TYPES:
        water = jerlov.water(water_type)
        print(f"\n  Jerlov {water_type}, Williamson & Hollins (2022)")
        print(f"  {'space':<13}{'sigma_t (1/m)':>24}{'albedo':>21}"
              f"{'error':>19}")
        for space in jerlov.RGB_COLOUR_SPACES:
            out = caught_by_type(caught, jerlov.rgb_attenuation, water,
                                 colour_space=space, illuminant=ILLUMINANT,
                                 distance_range_m=RANGE_M)
            table[(water_type, space)] = out
            print(f"  {space:<13}"
                  f"{' '.join(f'{v:7.3f}' for v in out.sigma_t):>24}"
                  f"{' '.join(f'{v:6.3f}' for v in out.albedo):>21}"
                  f"{' '.join(f'{100 * v:5.1f}%' for v in out.max_relative_error_t):>19}")
    worst = {space: max(float(np.max(table[(t, space)].max_relative_error_t))
                        for t in TYPES)
             for space in jerlov.RGB_COLOUR_SPACES}
    red_worst = all(int(np.argmax(out.max_relative_error_t)) == 0
                    for out in table.values())
    which = ("The worst channel is red in every row"
             if red_worst else "The worst channel is not always red")
    print(f"""
{which}. The largest error is {100 * worst['acescg']:.0f} percent in ACEScg,
{100 * worst['rec2020']:.0f} in Rec. 2020 and {100 * worst['linear_srgb']:.0f} in linear sRGB, whose red channel is nearly
empty after a few metres of blue-green light.""")
    return table, worst, red_worst


def refusal_part(caught):
    rule("2. Where a channel turns negative")
    water = jerlov.water("IB")
    far = 20.0
    try:
        caught_by_type(caught, jerlov.rgb_attenuation, water,
                       colour_space="linear_srgb", illuminant=ILLUMINANT,
                       distance_range_m=(RANGE_M[0], far))
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError("expected the clear water to be refused")
    reach = float(message.split("up to about ")[1].split(" m")[0])
    wider = caught_by_type(caught, jerlov.rgb_attenuation, water,
                           colour_space="acescg", illuminant=ILLUMINANT,
                           distance_range_m=(RANGE_M[0], far))
    print(f"""Jerlov IB, linear sRGB, {RANGE_M[0]:g}-{far:g} m, is refused:

  {message}

The light left after {reach:.1f} m is a blue-green outside the sRGB gamut, and
the red matching function of sRGB is negative there, so the red "light"
is negative: no exponential reaches it. In ACEScg the same water fits,
with sigma_t {', '.join(f'{v:.3f}' for v in wider.sigma_t)} 1/m and a worst error of
{100 * float(np.max(wider.max_relative_error_t)):.0f} percent.""")
    return reach


def range_part(caught):
    rule("3. The range decides the fit")
    water = jerlov.water(RENDER_TYPE)
    print(f"""Jerlov {RENDER_TYPE} in ACEScg, D65, over three ranges of distance:
""")
    print(f"  {'range (m)':<12}{'sigma_t (1/m)':>24}{'error':>21}")
    errors = {}
    for distances in RANGES_M:
        out = caught_by_type(caught, jerlov.rgb_attenuation, water,
                             colour_space="acescg", illuminant=ILLUMINANT,
                             distance_range_m=distances)
        errors[distances] = out
        print(f"  {f'{distances[0]:g}-{distances[1]:g}':<12}"
              f"{' '.join(f'{v:7.3f}' for v in out.sigma_t):>24}"
              f"{' '.join(f'{100 * v:5.1f}%' for v in out.max_relative_error_t):>21}")
    red = [float(errors[d].sigma_t[0]) for d in RANGES_M]
    print(f"""
The red coefficient falls from {red[0]:.3f} to {red[-1]:.3f} 1/m as the range grows: what
survives far is the part of the channel's light the water attenuates
least. A scene seen within a few metres and one seen across twenty want
different numbers.""")
    return errors


def phase_part():
    rule("4. A Henyey-Greenstein g for Petzold's stations")
    print("""HG made to scatter each station's B/S beyond 90 degrees, and made to
have its mean cosine. "short" is how many times smaller than the
measurement the HG is at 0.1 degree.
""")
    print(f"  {'station':<10}{'g (B/S)':>9}{'short':>8}"
          f"{'g (cos)':>10}{'its B/S':>9}{'measured':>10}{'short':>8}")
    fits = {}
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        by_ratio = jerlov.henyey_greenstein_fit(f, method="backscatter_ratio")
        with warnings.catch_warnings():
            # The mean cosine counts the report's extension below 0.1
            # degree at full weight; the share is printed after the table.
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            by_cosine = jerlov.henyey_greenstein_fit(f, method="mean_cosine")
        fits[station] = (by_ratio, by_cosine, f.fraction_below_0_1_deg)
        print(f"  {station:<10}{by_ratio.g:>9.3f}"
              f"{np.exp(-by_ratio.log_ratio[0]):>8.0f}"
              f"{by_cosine.g:>10.3f}{by_cosine.backscatter_ratio:>9.4f}"
              f"{by_cosine.measured_backscatter_ratio:>10.4f}"
              f"{np.exp(-by_cosine.log_ratio[0]):>8.0f}")
    below = [v[2] for v in fits.values()]
    deficit = [1 - v[1].backscatter_ratio / v[1].measured_backscatter_ratio
               for v in fits.values()]
    short = [float(np.exp(-fit.log_ratio[0]))
             for v in fits.values() for fit in v[:2]]
    print(f"""
Matched to the mean cosine, HG backscatters {100 * min(deficit):.0f} to {100 * max(deficit):.0f} percent less
than the station did. That mean cosine counts the {100 * min(below):.1f} to
{100 * max(below):.1f} percent of the scattering below 0.1 degree, which Petzold's
report extended with a power law rather than measured. Matched to B/S,
which was measured, g is lower. Either way HG falls {min(short):.0f} to {max(short):.0f} times
short of sea water's forward peak at 0.1 degree, and the renderer will
use one g at every wavelength, Petzold's being for a band in the green.""")
    return fits, deficit, short


def nearest_station(water):
    b = float(caught_by_type(set(), water.b, 530.0))
    return min(jerlov.PETZOLD_STATIONS,
               key=lambda s: abs(jerlov.petzold_scattering(s).b - b)), b


def numbers(values, digits=6):
    return ", ".join(f"{v:.{digits}g}" for v in values)


def files_part(caught):
    rule("5. Into a renderer")
    water = jerlov.water(RENDER_TYPE)
    station, b530 = nearest_station(water)
    g = jerlov.henyey_greenstein_fit(jerlov.petzold_scattering(station),
                                     method="backscatter_ratio").g
    srgb = caught_by_type(caught, jerlov.rgb_attenuation, water,
                          colour_space="linear_srgb", illuminant=ILLUMINANT,
                          distance_range_m=RANGE_M)
    aces = caught_by_type(caught, jerlov.rgb_attenuation, water,
                          colour_space="acescg", illuminant=ILLUMINANT,
                          distance_range_m=RANGE_M)
    spectra = caught_by_type(caught, jerlov.spectral_coefficients, water,
                             range_nm=SPECTRAL_RANGE_NM)
    held = np.arange(SPECTRAL_RANGE_NM[1] + 1, HELD_TO_NM + 1)
    wl = np.concatenate([spectra.wavelengths, held])

    def to_830(values):
        return np.concatenate([values, np.full(held.size, values[-1])])
    print(f"""Jerlov {RENDER_TYPE}; the phase function of {station}, whose b at 530 nm is
nearest this water's ({jerlov.petzold_scattering(station).b:.3f} against {b530:.3f} 1/m), matched
to its B/S: g = {g:.4f}. One scene unit is taken to be one metre.""")

    scale = float(np.max(srgb.sigma_t))
    mitsuba_rgb = f"""<medium type="homogeneous" id="water">
    <!-- Jerlov {RENDER_TYPE}, Williamson & Hollins (2022); linear sRGB, D65,
         fitted over {RANGE_M[0]:g}-{RANGE_M[1]:g} m (jerlov {jerlov.__version__}) -->
    <rgb name="sigma_t" value="{numbers(srgb.sigma_t / scale)}"/>
    <float name="scale" value="{scale:.6g}"/>
    <rgb name="albedo" value="{numbers(srgb.albedo)}"/>
    <phase type="hg">
        <float name="g" value="{g:.4f}"/>
    </phase>
</medium>
"""

    def pairs(values):
        return ", ".join(f"{w:g}:{v:.6g}" for w, v in zip(wl, to_830(values)))

    mitsuba_spectral = f"""<medium type="homogeneous" id="water">
    <!-- Jerlov {RENDER_TYPE}, Williamson & Hollins (2022), at their own wavelengths,
         {SPECTRAL_RANGE_NM[0]:g}-{SPECTRAL_RANGE_NM[1]:g} nm; the {SPECTRAL_RANGE_NM[1]:g} nm values held to {HELD_TO_NM:g} nm
         (jerlov {jerlov.__version__}) -->
    <spectrum name="sigma_t" value="{pairs(spectra.c)}"/>
    <spectrum name="albedo" value="{pairs(spectra.albedo)}"/>
    <phase type="hg">
        <float name="g" value="{g:.4f}"/>
    </phase>
</medium>
"""

    def flat(values):
        return " ".join(f"{w:g} {v:.6g}" for w, v in zip(wl, to_830(values)))

    pbrt = f"""# Jerlov {RENDER_TYPE}, Williamson & Hollins (2022), at their own wavelengths,
# {SPECTRAL_RANGE_NM[0]:g}-{SPECTRAL_RANGE_NM[1]:g} nm; the {SPECTRAL_RANGE_NM[1]:g} nm values held to {HELD_TO_NM:g} nm
# (jerlov {jerlov.__version__})
MakeNamedMedium "water" "string type" "homogeneous"
    "spectrum sigma_a" [ {flat(spectra.a)} ]
    "spectrum sigma_s" [ {flat(spectra.b)} ]
    "float scale" 1 "float g" {g:.4f}
"""
    absorption_density = float(np.max(aces.sigma_a))
    scatter_density = float(np.max(aces.sigma_s))
    absorption_colour = 1 - aces.sigma_a / absorption_density
    scatter_colour = aces.sigma_s / scatter_density
    blender = f"""Working Space: ACEScg (Render Properties, Color Management)
Volume Absorption: Color {numbers(absorption_colour, 4)}, Density {absorption_density:.4g}
Volume Scatter:    Color {numbers(scatter_colour, 4)}, Density {scatter_density:.4g}, Anisotropy {g:.4f}
"""
    texts = {"water_mitsuba_rgb.xml": mitsuba_rgb,
             "water_mitsuba_spectral.xml": mitsuba_spectral,
             "water.pbrt": pbrt,
             "water_blender.txt": blender}

    def shown(text):
        lines = []
        for line in text.splitlines():
            lines.append(line if len(line) <= 76 else line[:72] + " ...")
        return "\n".join("    " + line for line in lines)

    print(f"""
Mitsuba 3, an RGB variant (its RGB is linear sRGB). Mitsuba's documentation
asks for RGB values in [0, 1], so sigma_t is divided by its largest value
and that goes in scale. The red channel of this fit is off by up to
{100 * float(srgb.max_relative_error_t[0]):.0f} percent over the range:

{shown(mitsuba_rgb)}

Mitsuba 3, a spectral variant: the {spectra.wavelengths.size} samples of a and b as the source gives
them, no RGB step. Mitsuba samples 360-830 nm and renders NaN where a
medium's spectrum stops short, so the {SPECTRAL_RANGE_NM[1]:g} nm values are held to {HELD_TO_NM:g} nm,
this example's choice:

{shown(mitsuba_spectral)}

pbrt-v4 renders spectrally and turns RGB into a spectrum, so it is given
the same spectra. Its scale multiplies both coefficients:

{shown(pbrt)}

Blender, whose Volume Absorption and Volume Scatter nodes take a colour and
a density; its manual gives absorption = (1 - Color) x Density and
scattering = Color x Density, per channel. In ACEScg, fitted over
{RANGE_M[0]:g}-{RANGE_M[1]:g} m, which leaves red off by up to {100 * float(aces.max_relative_error_t[0]):.0f} percent:

{shown(blender)}""")
    if len(sys.argv) > 1:
        out = pathlib.Path(sys.argv[1])
        out.mkdir(parents=True, exist_ok=True)
        for name, text in texts.items():
            (out / name).write_text(text)
        print(f"\nWritten to {out}: {', '.join(texts)}")
    else:
        print("\nGive a directory on the command line to write these files.")
    return dict(station=station, g=g, srgb=srgb, aces=aces,
                spectra=spectra, texts=texts, wavelengths=wl,
                blender=(absorption_colour, absorption_density,
                         scatter_colour, scatter_density))


def main():
    _banner()
    caught = set()
    table, worst, red_worst = rgb_part(caught)
    reach = refusal_part(caught)
    errors = range_part(caught)
    fits, deficit, short = phase_part()
    files = files_part(caught)
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print("""  - Williamson & Hollins's a and b outside 412-715 nm are their model's
    extrapolation (the warnings above). The ends of the visible spectrum
    count for little in a colour, but they are not measurements; the
    spectra for the renderers also hold the 800 nm values to 830 nm.
  - The light entering the water is D65, daylight above the surface. Light
    at depth is bluer, and the RGB coefficients depend on it.
  - One exponential per channel is the renderer's simplification, not
    the water's; the errors printed are what it costs over the stated
    ranges, and they grow with the range.
  - Henyey-Greenstein cannot match sea water's forward peak, and one g
    serves every wavelength. Petzold's eight waters are particular waters
    on particular days in 1971, not Jerlov types.
  - The files are scene descriptions only. The two Mitsuba media were
    loaded and rendered once by hand, in a small test scene with Mitsuba
    3.9.1, outside CI; the pbrt-v4 text and the Blender values follow those
    programs' own documentation and were not run.
""")
    return dict(table=table, worst=worst, red_worst=red_worst, reach=reach,
                errors=errors, fits=fits, deficit=deficit, short=short,
                files=files, caught=caught)


if __name__ == "__main__":
    main()
