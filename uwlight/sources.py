"""Registry of data sources and their model constants.

The scattering model of Haltrin (1999) is used by several later papers, but
they do not all use the same numerical constants. Solonenko & Mobley (2015)
print (and compute with) a small-particle coefficient of 1.513, whereas
Haltrin's Eq. (6) gives 1.151302 and Williamson & Hollins use 1.1513.

Reproducing a published table therefore requires that source's own constants,
which is why they live here rather than in the equations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScatteringConstants:
    """Constants of the two-component scattering model.

    b(lam) = bw_coeff * (400/lam)**bw_exponent
           + Cs * small_coeff * (400/lam)**small_exponent
           + Cl * large_coeff * (400/lam)**large_exponent

    ``Cs`` and ``Cl`` are the small- and large-particle concentrations
    (g/m3). Note that Haltrin writes these as Cs, Cl and reserves Bs, Bl
    for the backscattering probabilities; Solonenko & Mobley and
    Williamson & Hollins rename the concentrations to Bs, Bl. This package
    follows Haltrin.
    """

    bw_coeff: float
    bw_exponent: float
    small_coeff: float
    small_exponent: float
    large_coeff: float
    large_exponent: float
    # Backscattering probabilities, Haltrin (1999) Eq. (4).
    small_backscatter_prob: float | None = None
    large_backscatter_prob: float | None = None


#: Haltrin (1999) Eqs. (5)-(7) as printed in the original paper.
HALTRIN1999 = ScatteringConstants(
    bw_coeff=0.005826,
    bw_exponent=4.322,
    small_coeff=1.151302,
    small_exponent=1.7,
    large_coeff=0.341074,
    large_exponent=0.3,
    small_backscatter_prob=0.039,
    large_backscatter_prob=6.4e-4,
)

#: Solonenko & Mobley (2015) Eqs. (8a)-(8d). The small-particle coefficient
#: 1.513 does not match Haltrin's 1.151302; the digit appears to have been
#: dropped in transcription. Their published tables were computed with 1.513,
#: so this value is required to reproduce them. See README section 6.
SOLONENKO2015_SCATTERING = ScatteringConstants(
    bw_coeff=0.00583,
    bw_exponent=4.322,
    small_coeff=1.513,
    small_exponent=1.7,
    large_coeff=0.3411,
    large_exponent=0.3,
)


@dataclass(frozen=True)
class Source:
    """A published set of inherent optical properties."""

    key: str
    citation: str
    doi: str | None
    quantities: tuple[str, ...]
    water_types: tuple[str, ...]
    wavelength_range_nm: tuple[float, float]
    measured: bool
    """True if a and b rest on measurements rather than on inversion of Kd."""
    scattering: ScatteringConstants | None = None
    caveats: tuple[str, ...] = field(default_factory=tuple)

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.key}: {self.citation}"


OCEANIC_TYPES = ("I", "IA", "IB", "II", "III")
COASTAL_TYPES = ("1C", "3C", "5C", "7C", "9C")
ALL_TYPES = OCEANIC_TYPES + COASTAL_TYPES

SOURCES: dict[str, Source] = {
    "williamson2022": Source(
        key="williamson2022",
        citation=(
            "C. A. Williamson and R. C. Hollins, 'Measured IOPs of Jerlov "
            "water types', Appl. Opt. 61, 9951-9961 (2022)"
        ),
        doi="10.1364/AO.470464",
        quantities=("a", "b"),
        water_types=("IB", "II", "III", "1C", "3C", "5C"),
        wavelength_range_nm=(300.0, 800.0),
        measured=True,
        scattering=HALTRIN1999,
        caveats=(
            "Measured data exist only between 412 and 715 nm. Values outside "
            "that band are model interpolation or extrapolation.",
            "Jerlov I, IA, 7C and 9C are absent: too few measurements.",
        ),
    ),
    "solonenko2015": Source(
        key="solonenko2015",
        citation=(
            "M. G. Solonenko and C. D. Mobley, 'Inherent optical properties "
            "of Jerlov water types', Appl. Opt. 54, 5392-5401 (2015)"
        ),
        doi="10.1364/AO.54.005392",
        quantities=("a", "b", "Kd", "Kd0", "KdH"),
        water_types=ALL_TYPES,
        wavelength_range_nm=(300.0, 700.0),
        measured=False,
        scattering=SOLONENKO2015_SCATTERING,
        caveats=(
            "a and b were obtained by inverting Kd, not by measurement.",
            "Table 7 duplicates rows for Jerlov 3C (675, 700 nm) and 5C "
            "(600-700 nm). b has been reconstructed from Eq. (8); a is absent.",
            "The small-particle scattering coefficient used here (1.513) does "
            "not match Haltrin (1999), which gives 1.151302.",
            "The paper's Kd0 column is a reference spectrum from Jerlov (1951, "
            "1968) and is not shipped: it disagrees with Jerlov (1976) by up to "
            "34 percent, falls below the paper's own absorption at 600 nm for "
            "types I, IA, IB and II, and is identical for 1C and III from 525 "
            "to 700 nm. Use source 'jerlov1976' or 'austin1986' for Kd.",
        ),
    ),
    "jerlov1976": Source(
        key="jerlov1976",
        citation="N. G. Jerlov, 'Marine Optics' (Elsevier, 1976), Table XXVII",
        doi=None,
        quantities=("Kd",),
        water_types=ALL_TYPES,
        wavelength_range_nm=(300.0, 715.0),
        measured=True,
        caveats=(
            "Austin & Petzold (1986) showed that Jerlov's type I values fall "
            "below the attenuation of pure sea water at several wavelengths "
            "and recommended replacing them; see source 'austin1986'.",
        ),
    ),
    "austin1986": Source(
        key="austin1986",
        citation=(
            "R. W. Austin and T. J. Petzold, 'Spectral dependence of the "
            "diffuse attenuation coefficient of light in ocean waters', "
            "Opt. Eng. 25(3), 471-479 (1986), Table VI"
        ),
        doi="10.1117/12.7973845",
        quantities=("Kd",),
        water_types=("I", "IA", "IB", "II", "III", "1C"),
        wavelength_range_nm=(350.0, 700.0),
        measured=False,
        caveats=(
            "The type I row is the attenuation of pure sea water. Only the "
            "475 nm column is Jerlov's original value; the rest come from the "
            "authors' model.",
            "Accuracy degrades beyond 590 nm: Austin & Petzold (1990) report "
            "a coefficient of variation of 31 percent at 670 nm.",
        ),
    ),
}


def get_source(key: str) -> Source:
    """Return the :class:`Source` registered under ``key``."""
    try:
        return SOURCES[key]
    except KeyError:
        known = ", ".join(sorted(SOURCES))
        raise KeyError(f"unknown source {key!r}; known sources: {known}") from None
