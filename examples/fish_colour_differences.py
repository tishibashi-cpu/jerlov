"""How far apart two colours stay, as a fish's cones count them.

For anyone working on fish vision or visual ecology: what a stretch of water
does to the difference between two colours, measured the way the
receptor-noise model of Vorobyev & Osorio (1998) measures it, for a fish
whose cones have been characterised, *Dicentrarchus labrax*, from Brill et
al. (2019).

    python examples/fish_colour_differences.py

It does not say what a fish notices, or at what distance it can tell two
colours apart. That would need a threshold and a level of receptor noise,
neither of which is known for this species, and it is a prediction of
visibility, which this package does not make. It says how fast the
difference shrinks, and which conclusions survive the uncertainty in the
fish's cones (DECISIONS.md section 65).
"""

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


#: Brill, R. W., Horodysky, A. Z., Place, A. R., Larkin, M. E. M. and
#: Reimschuessel, R. (2019), PLOS ONE 14(6), e0214347,
#: doi:10.1371/journal.pone.0214347, Table 4 (p. 12): fish fed 0 and 1.5
#: percent taurine, three pigments, alpha-band only ("Tri, alpha").
BRILL_GFRKD = (388.0, 501.0, 603.0)   # the Govardovskii et al. template
BRILL_SSH = (389.0, 512.0, 611.0)     # the Stavenga et al. template, best fit
SHIFT_NM = 15.0

WL = np.arange(332.0, 701.0, 2.0)     # the template holds above 330 nm
DEPTH_M = 5.0
TYPES = ("II", "III", "1C")
NEAR_M = 0.5                          # Delta S is a share of its value here
DISTANCES = np.round(np.arange(NEAR_M, 40.0001, 0.05), 2)
SHOWN_M = (1.0, 2.0, 4.0, 8.0)
#: Brill et al.'s values with equal noise, the variant shown first.
BASELINE = ("GFRKD (Brill et al.)", "equal")

#: Neither value matters to the result: both cancel (see part 3).
BACKSCATTER_RATIO = 0.01
FACE_IRRADIANCE_RATIO = 0.3


def step(edge_nm):
    return 1.0 / (1.0 + np.exp(-(WL - edge_nm) / 15.0))


#: Smooth stand-ins for paints, diffuse reflectance 0 to 1.
PAINTS = {
    "red": 0.05 + 0.75 * step(600.0),
    "green": 0.05 + 0.75 * step(500.0) * (1.0 - step(570.0)),
    "blue": 0.05 + 0.75 * (1.0 - step(500.0)),
    "white": np.full_like(WL, 0.8),
    "white without UV": 0.05 + 0.75 * step(400.0),
}
PAIRS = (("red", "green"), ("blue", "green"), ("white", "white without UV"))


def lambda_max_sets():
    """The eight sets of peaks the conclusions are tested against."""
    sets = {"GFRKD (Brill et al.)": BRILL_GFRKD,
            "SSH values": BRILL_SSH}
    names = ("short", "middle", "long")
    for i, name in enumerate(names):
        for sign in (-1, 1):
            peaks = list(BRILL_GFRKD)
            peaks[i] += sign * SHIFT_NM
            sets[f"{name} {sign * SHIFT_NM:+.0f} nm"] = tuple(peaks)
    return sets


def noise_settings():
    """Equal noise, or one cone twice as noisy: only the ratios matter."""
    settings = {"equal": np.ones(3)}
    for i, name in enumerate(("short", "middle", "long")):
        e = np.ones(3)
        e[i] = 2.0
        settings[f"{name} cone 2x noisier"] = e
    return settings


def sensitivities(peaks, caught):
    """The three cones, alpha-band only, as Brill et al. fitted them."""
    curves = []
    for peak in peaks:
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", jerlov.ProvenanceWarning)
            curves.append(jerlov.visual_pigment_template(
                WL, lambda_max=peak, chromophore="A1", beta=False))
        caught.update(peak for w in record
                      if issubclass(w.category, jerlov.ProvenanceWarning))
    return np.stack(curves, axis=1)


def surface_photons():
    """D65, scaled to photons: a catch counts photons, and the constant
    that converts energy to photons cancels when catches are scaled."""
    d65_wl, d65 = jerlov.d65()
    return np.interp(WL, d65_wl, d65) * WL


def radiances(water_type, backscatter_ratio=BACKSCATTER_RATIO,
              face_ratio=FACE_IRRADIANCE_RATIO):
    """The water's own light along the path, and each paint's light at
    each distance, in photons."""
    iops = jerlov.water(water_type, source="solonenko2015")
    scene = jerlov.Scene.at_depth(
        iops, DEPTH_M, surface_photons(), WL,
        kd=jerlov.water(water_type, source="jerlov1976"))
    water_light = jerlov.veiling_radiance_estimate(
        iops, scene.downwelling, WL, backscatter_ratio=backscatter_ratio)
    seen = {name: np.array([scene.observe(
        paint, float(d), veiling_radiance=water_light,
        face_irradiance_ratio=face_ratio).radiance for d in DISTANCES])
        for name, paint in PAINTS.items()}
    return water_light, seen


def catches(radiance, water_light, cones):
    """Each cone's catch, scaled so that the water's own light gives 1."""
    background = jerlov.integrate_response(water_light, WL, cones, WL)
    return np.array([jerlov.integrate_response(r, WL, cones, WL)
                     for r in np.atleast_2d(radiance)]) / background


def relative_distance(q_a, q_b, noise):
    """Delta S at each distance as a share of Delta S at NEAR_M."""
    d_s = jerlov.receptor_noise_distance(q_a, q_b, noise=noise)
    return d_s / d_s[0]


def half_distance(share):
    """The first distance at which the share falls to a half; inf if it
    does not within the distances computed."""
    below = np.nonzero(share <= 0.5)[0]
    if below.size == 0:
        return float("inf")
    i = below[0]
    d0, d1, s0, s1 = DISTANCES[i - 1], DISTANCES[i], share[i - 1], share[i]
    return float(d0 + (s0 - 0.5) * (d1 - d0) / (s0 - s1))


def compute(backscatter_ratio=BACKSCATTER_RATIO,
            face_ratio=FACE_IRRADIANCE_RATIO, sets=None, noises=None):
    """d_half for every water, pair, set of peaks and noise setting."""
    sets = lambda_max_sets() if sets is None else sets
    noises = noise_settings() if noises is None else noises
    caught = set()
    cones = {name: sensitivities(peaks, caught)
             for name, peaks in sets.items()}
    halves, shares = {}, {}
    for water_type in TYPES:
        water_light, seen = radiances(water_type, backscatter_ratio,
                                      face_ratio)
        for set_name, curves in cones.items():
            q = {name: catches(r, water_light, curves)
                 for name, r in seen.items()}
            for noise_name, noise in noises.items():
                for a, b in PAIRS:
                    share = relative_distance(q[a], q[b], noise)
                    key = (water_type, f"{a} / {b}", set_name, noise_name)
                    halves[key] = half_distance(share)
                    shares[key] = share
    return dict(halves=halves, shares=shares, caught=sorted(caught),
                sets=sets, noises=noises)


def orderings(halves, sets, noises):
    """For each variant, the pairs in each water and the waters for each
    pair, ordered by d_half, longest first."""
    pairs = [f"{a} / {b}" for a, b in PAIRS]
    out = {}
    for s in sets:
        for n in noises:
            for w in TYPES:
                out[("pairs in", w, s, n)] = tuple(sorted(
                    pairs, key=lambda p: -halves[(w, p, s, n)]))
            for p in pairs:
                out[("waters for", p, s, n)] = tuple(sorted(
                    TYPES, key=lambda w: -halves[(w, p, s, n)]))
    return out


def verdicts(order, sets, noises):
    """An ordering is a finding only if every variant gives the same one;
    otherwise, which variants differ from Brill et al.'s values with equal
    noise."""
    result = {}
    for kind, subject in {(k[0], k[1]) for k in order}:
        baseline = order[(kind, subject, BASELINE[0], BASELINE[1])]
        differ = [f"{s}, {n} noise" for s in sets for n in noises
                  if order[(kind, subject, s, n)] != baseline]
        result[(kind, subject)] = dict(holds=not differ, baseline=baseline,
                                       broken_by=differ)
    return result


def metres(value):
    return "beyond 40 m" if np.isinf(value) else f"{value:.1f} m"


def long_wave_margin():
    """How little the cut at 700 nm leaves out: the share of the long-wave
    cone's catch of the water's own light that comes from 680-700 nm.
    Jerlov's own Kd ends at 700 nm; beyond it the dataset extrapolates."""
    caught = set()
    cone = sensitivities(BRILL_GFRKD, caught)[:, 2]
    shares = {}
    for w in TYPES:
        water_light, _ = radiances(w)
        per_nm = water_light * cone
        shares[w] = float(per_nm[WL >= 680].sum() / per_nm.sum())
    return shares


def main():
    _banner()
    r = compute()
    margin = long_wave_margin()
    halves, sets, noises = r["halves"], r["sets"], r["noises"]
    pairs = [f"{a} / {b}" for a, b in PAIRS]

    rule("1. The fish")
    print(f"""Dicentrarchus labrax, from Brill et al. (2019),
PLOS ONE 14(6), e0214347, Table 4 (p. 12): three pigments fitted to the
whole eye's photopic ERG, alpha-band only, an A1 chromophore assumed.
  with the Govardovskii et al. template   {", ".join(f"{p:g}" for p in BRILL_GFRKD)} nm  (used here)
  with the Stavenga et al. template       {", ".join(f"{p:g}" for p in BRILL_SSH)} nm  (fitted better)
The Govardovskii et al. values go into the Govardovskii et al. template,
as they were fitted. Its long-wave peak, and some of the variants below,
lie beyond the longest A1 pigment Govardovskii et al. measured, so the
template warned for {", ".join(f"{p:g}" for p in r["caught"])} nm; the
template there is their claim that it holds, not their fit.""")

    rule("2. How fast the difference shrinks")
    print(f"""Two painted surfaces side by side at the same distance, along a
horizontal path at {DEPTH_M:g} m. The catches are scaled to those of the
water's own light, the background along the path, and Delta S, the
distance between the two in units of receptor noise, is shown as a share
of its value at {NEAR_M:g} m. Equal noise in the three cones.
""")
    header = "".join(f"{d:>7g} m" for d in SHOWN_M)
    for w in TYPES:
        print(f"  Jerlov {w:<3}                 {header}     half at")
        for p in pairs:
            share = r["shares"][(w, p, BASELINE[0], BASELINE[1])]
            cells = "".join(
                f"{share[np.argmin(np.abs(DISTANCES - d))]:9.2f}"
                for d in SHOWN_M)
            half = halves[(w, p, BASELINE[0], BASELINE[1])]
            print(f"    {p:<26}{cells}   {metres(half)}")
        print()

    rule("3. What the cones' uncertainty does to it")
    print(f"""The same, for {len(sets)} sets of peaks (Brill et al.'s, the SSH values,
and each peak moved {SHIFT_NM:g} nm either way) and {len(noises)} noise settings (equal,
or one cone twice as noisy): {len(sets) * len(noises)} variants. The range of the
distance at which the difference halves:
""")
    for w in TYPES:
        for p in pairs:
            values = [halves[(w, p, s, n)] for s in sets for n in noises]
            print(f"  Jerlov {w:<3} {p:<26} {metres(min(values)):>8} to "
                  f"{metres(max(values))}")
    order = orderings(halves, sets, noises)
    judged = verdicts(order, sets, noises)
    print("""
An ordering is called a finding only if all the variants give it.
""")
    for (kind, subject), v in sorted(judged.items()):
        listed = " > ".join(v["baseline"])
        if v["holds"]:
            print(f"  holds        {kind} {subject}: {listed}")
        else:
            print(f"  depends on   {kind} {subject}: {listed} with Brill et "
                  f"al.'s values, but not with: {', '.join(v['broken_by'])}")
    print(f"""
The backscatter ratio ({BACKSCATTER_RATIO:g}) and the light on the faces
({FACE_IRRADIANCE_RATIO:g} of the downwelling) set how bright the water's light
and the paints are, but they scale the difference and the background
alike, and so cancel from the share.""")

    rule("Before you use any of this")
    print(f"""  - The peaks come from the ERG of the whole eye, fitted with an assumed
    A1 chromophore, in hatchery-reared juveniles on experimental diets;
    single cones were not measured, and fish of other ages, diets or
    waters may differ.
  - No receptor noise or cone ratio has been measured for the species.
    Only the ratios of the noise matter here, and they are varied, not
    known.
  - Vorobyev & Osorio's model is for colours near the background, in
    bright light, for large static targets. Close to the paints the first
    is not met; the shares are of a distance the model computes, not of
    what a fish sees.
  - The water along the path is Solonenko & Mobley's a and b, inverted
    from Jerlov's Kd rather than measured, since the measured set does not
    reach the short-wave cone. The light above 700 nm, where Jerlov's own
    Kd ends, is left out: 680-700 nm gives the long-wave cone {100 * min(margin.values()):.1f} to {100 * max(margin.values()):.1f}
    percent of its catch of the water's own light.
  - Only Jerlov II, III and 1C are covered, not turbid coastal water.
    Jerlov's Kd for 7C and 9C has no values below 350 nm, where the
    short-wave cone needs them, and Solonenko & Mobley's a for 3C and 5C
    has gaps in the red, where the long-wave cone does.
  - The sky is D65 and the paints are smooth stand-ins; measured spectra
    should replace both.
  - Nothing here says at what distance a fish can tell two colours apart,
    or whether it does.
""")
    return dict(halves=halves, judged=judged, caught=r["caught"],
                shares=r["shares"], margin=margin)


if __name__ == "__main__":
    main()
