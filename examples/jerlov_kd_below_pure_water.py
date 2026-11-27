"""Why does Jerlov's Kd lie below the absorption of pure water in places?

An open question, with numbers (OPEN_QUESTIONS.md, question 7). For those
who use Jerlov's types in the red, or who measure Kd themselves:

    python examples/jerlov_kd_below_pure_water.py

Austin & Petzold (1986) pointed out that some of Jerlov's Kd for type I
are less than the absorption of pure water alone, which a diffuse
attenuation cannot be, and recommended replacing them (DATA.md section 3).
This example says where and by how much, in both editions, and works out
how much of it one mechanism can give: a broad filter, by Marshall &
Smith's (1990) Eq. (37). The other mechanism they name, Raman scattering,
is not computed (DECISIONS.md section 130).
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


#: The wavelengths Jerlov printed from 400 to 700 nm (both editions).
PRINTED = np.arange(400.0, 701.0, 25.0)
TYPES = ("I", "IA", "IB", "II")
EDITIONS = ("jerlov1968", "jerlov1976")
#: The two published pure water absorptions the package carries that reach
#: the red, and how far each reaches.
PURE = {"smith1981": 800.0, "pope1997": 727.5}
#: The layer Jerlov's types describe (Jerlov 1976, p. 133).
LAYER_M = 10.0
#: Gaussian filters, full width at half maximum, nm.
WIDTHS = (2.0, 10.0, 20.0, 40.0, 60.0)
CENTRES = (600.0, 675.0, 700.0)


def aw(wavelengths, source, caught):
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        out = np.asarray(jerlov.pure_water_absorption_table(
            wavelengths, source=source), dtype=float)
    for w in seen:
        if issubclass(w.category, jerlov.ProvenanceWarning):
            caught.add(str(w.message).split(":")[0] + ": "
                       + str(w.message).split(": ", 2)[1].split(" (")[0])
        else:                               # pragma: no cover
            warnings.warn_explicit(w.message, w.category, w.filename,
                                   w.lineno)
    return out


def where_part(caught):
    """Jerlov's Kd over pure water's absorption, where it is below 1."""
    rule("1. Where Jerlov's Kd lies below pure water's absorption")
    below = {}
    for source in PURE:
        a = aw(PRINTED, source, caught)
        for edition in EDITIONS:
            for t in TYPES:
                kd = np.asarray(jerlov.water(t, source=edition).kd(PRINTED))
                ratio = kd / a
                low = {float(w): float(r) for w, r in zip(PRINTED, ratio)
                       if r < 1}
                below[(source, edition, t)] = low
                if low:
                    cells = ", ".join(f"{w:.0f} nm {r:.3f}"
                                      for w, r in low.items())
                    print(f"  {edition} {t:>2} / {source}: {cells}")
    least = {}
    for source in PURE:
        for edition in EDITIONS:
            values = below[(source, edition, "I")]
            w = min(values, key=values.get)
            least[(source, edition)] = (w, values[w])
            print(f"  type I, {edition} over {source}: least "
                  f"{values[w]:.3f} at {w:.0f} nm")
    return dict(below=below, least=least)


def rounding_part():
    """How far the printed figures' rounding can move Kd."""
    rule("2. Could rounding do it?")
    red = PRINTED >= 600
    kd76 = np.asarray(jerlov.water("I", source="jerlov1976").kd(PRINTED))[red]
    steps = np.round(kd76 / 0.005, 6)
    assert np.all(steps == np.round(steps)), "1976 Kd not in steps of 0.005"
    worst76 = float(np.max(0.0025 / kd76))
    kd68 = np.asarray(jerlov.water("I", source="jerlov1968").kd(PRINTED))
    percent = np.round(100.0 * np.exp(-kd68))      # printed transmittance
    lo = -np.log((percent + 0.5) / 100.0)
    hi = -np.log((percent - 0.5) / 100.0)
    worst68 = float(np.max(((hi - lo) / 2 / kd68)[red]))
    print(f"  1976: Kd printed in steps of 0.005 per metre; half a step is at "
          f"most {100 * worst76:.1f} percent of Kd from 600 to 700 nm.")
    print(f"  1968: transmittance printed in whole percent per metre; half a "
          f"percent moves Kd by at most {100 * worst68:.1f} percent there.")
    return dict(worst76=worst76, worst68=worst68)


def apparent(centre, fwhm, source, caught):
    """Eq. (37) of Marshall & Smith (1990), averaged over the layer, with K
    the absorption of pure water; None where the filter (to 3 sigma) leaves
    the table."""
    sigma = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    if centre + 3 * sigma > PURE[source]:
        return None
    grid = np.arange(centre - 3 * sigma, centre + 3 * sigma + 1e-9,
                     min(0.25, sigma / 8))
    k = aw(grid, source, caught)
    h = np.exp(-0.5 * ((grid - centre) / sigma) ** 2)
    surface = jerlov_trapezoid(h, grid)
    bottom = jerlov_trapezoid(h * np.exp(-k * LAYER_M), grid)
    return float(-np.log(bottom / surface) / LAYER_M)


def jerlov_trapezoid(y, x):
    return float(np.sum((y[1:] + y[:-1]) * np.diff(x)) / 2.0)


def filter_part(least, below, caught):
    rule("3. How much a broad filter alone can do (Marshall & Smith Eq. 37)")
    print(f"  K = pure water's absorption, a flat source, averaged over "
          f"0-{LAYER_M:.0f} m; the apparent K over the absorption:")
    table = {}
    for source in PURE:
        for centre in CENTRES:
            a0 = float(aw(np.array([centre]), source, caught)[0])
            row = {}
            for w in WIDTHS:
                k = apparent(centre, w, source, caught)
                row[w] = None if k is None else k / a0
            table[(source, centre)] = row
            cells = "  ".join(f"{w:>4.0f} nm {'  -  ' if r is None else f'{r:.3f}'}"
                              for w, r in row.items())
            print(f"  {source:>9} {centre:.0f} nm: {cells}")
    reach = {}
    for source in PURE:
        for edition in EDITIONS:
            for centre in CENTRES:
                r = below[(source, edition, "I")].get(centre)
                if r is None:
                    continue
                row = table[(source, centre)]
                narrowest = next((w for w in WIDTHS if row[w] is not None
                                  and row[w] <= r), None)
                reach[(source, edition, centre)] = (r, narrowest)
                tried = [w for w in WIDTHS if row[w] is not None]
                verdict = (f"a {narrowest:.0f} nm filter reaches it"
                           if narrowest is not None else
                           f"no filter up to {tried[-1]:.0f} nm reaches it"
                           + ("" if tried[-1] == WIDTHS[-1] else
                              " (wider ones leave the table)"))
                print(f"  type I {edition} over {source} at {centre:.0f} nm "
                      f"is {r:.3f}: {verdict}")
    return dict(table=table, reach=reach)


QUOTES = (
    ("Marshall & Smith (1990), p. 71",
     "Raman scattering along with excessive filter bandwidths in irradiance "
     "measurements accounts for observations of anomalous diffuse "
     "attenuation coefficients"),
    ("p. 77",
     "deep in the water column Raman scattering causes the effective "
     "attenuation coefficient to decrease significantly below the value "
     "expected without Raman scattering, while near the surface, Raman "
     "scattering has relatively little effect on K"),
    ("p. 78", "The filter tails are a significant source of this problem. "
     "In general, real filters have longer tails than predicted by the "
     "Gaussian"),
    ("p. 83", "near surface effects on reflectance and attenuation "
     "coefficients, at most ~20%"),
    ("Jerlov (1976), p. 128",
     "Most data result from sporadic observations with one to three colour "
     "filters having a broad band width"),
)


def main():
    _banner()
    caught = set()
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        where = where_part(caught)
        rounding = rounding_part()
        filters = filter_part(where["least"], where["below"], caught)
    rule("4. In the sources' words (Raman scattering is not computed here)")
    for who, text in QUOTES:
        print(f'  {who}: "{text}"')
    rule("Warnings")
    for message in sorted(caught):
        print(f"  ProvenanceWarning: {message}")
    rule("Before you use any of this")
    print("""  - Part 3 uses pure water's absorption as K. A real water's Kd is larger,
    so the apparent K of a real water is larger too; what part 3 shows is
    how far a filter alone lowers it, not what Jerlov's filters did.
  - Jerlov does not give his filters' widths; Gaussian filters of 2 to 60 nm
    stand in for them, and a flat source for the sunlight.
  - The Gaussians are cut at three standard deviations. The light that
    reaches 10 m through a filter comes mostly from its short-wavelength
    tail, where water absorbs less, so where the tail is cut moves the
    result; real filters' tails are longer (Marshall & Smith, p. 78).
  - Smith & Baker print their absorption every 10 nm, interpolated here; at
    710 nm the package marks their value suspect, and a broad filter at
    700 nm reaches it. Pope & Fry stop at 727.5 nm, so only the narrower
    filters are computed with them there.
  - Raman scattering is quoted, not computed: it needs the light field at
    the exciting wavelengths, a radiative transfer calculation.
""")
    return dict(where=where, rounding=rounding, filters=filters,
                caught=sorted(caught))


if __name__ == "__main__":
    main()
