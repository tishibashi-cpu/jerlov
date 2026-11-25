# Rebuilding the coefficient tables

These scripts are the record of how every value in `jerlov/data/` was
obtained. Running them must reproduce the shipped CSVs byte for byte; if it
does not, either the scripts or the CSVs have drifted and the difference must
be explained before either is changed.

```
pip install numpy openpyxl colour-science
for f in tools/build_*.py; do python "$f" || break; done
git diff --stat jerlov/data/     # must be empty
```

Eighteen of the scripts read no file and will run immediately: seventeen carry
their numbers as literals, and `build_cie.py` takes the CIE tables from
`colour-science`. The others stop with a message naming the file to fetch
and its DOI.

`openpyxl` and `colour-science` are needed only here, never at run time.
`build_usgs2017.py` needs `ASCIIdata_splib07a.zip` from the USGS Spectral
Library Version 7 data release (DOI `10.5066/F7RR1WDJ`).
`build_mobley_rho.py` needs `rhoTable_AO1999.txt` and `rhoTable_AO2015.txt`
from the Ocean Optics Web Book's page "Surface Reflectance Factors".
Two figshare datasets are needed, `20290782` and `21710252`; the scripts name
them and their DOIs when they are missing.
`build_cie.py` uses `colour-science` as a carrier for the CIE tabulations;
see DATA.md section 12.

Each script prints the checks it performs. They are not decoration: the
duplicated rows in Solonenko & Mobley Table 7 were found by exactly these
comparisons.

Every table has a script. Those whose values are transcribed from a paper
rather than read from a dataset keep the numbers as literals and check them
against the paper's own equations before writing anything.

Some files here build no table. `release_notes.py` prints a version's
GitHub Release text from CHANGELOG.md (DECISIONS.md section 51).
`site_pages.py` writes the pages of the site made from the package's
values, `docs/pages/dive.html`, `disagree.html`, `waters.html` and
`shallow.html`, and the figures in `docs/figures/`, from the templates in
`site_pages/` (DECISIONS.md sections 109, 120 and 121); run it again after a
change to any value they use, and at every release.
`nygard1973_levels.py` and its transcription `nygard1973_quanta.csv` are
the analysis of DECISIONS.md section 55, Nygård's measured profiles of
quanta checked against Jerlov's IB, and `smith1973_blue.py` with
`smith1973_blue.csv` that of section 56, Smith's spectra at the same
stations; `morel1973_levels.py` and `baird1973_chlorophyll.py`, with their
CSVs, those of section 58, Morel's profiles and the chlorophyll. The
transcriptions are not shipped.

## Test data, not shipped

`qaa_test_data.py` writes `tests/data/`, the data the tests of the
quasi-analytical algorithm check against (DECISIONS.md section 67): part of
the synthetic data set of IOCCG Report 5 (2006) and the results stored in
the QAA_v6 spreadsheet, both distributed by the IOCCG and placed in
`sources/ioccg/`. It needs `xlrd` and `openpyxl`. Its output is not in the
wheel. Running it must reproduce `tests/data/` byte for byte.


`osoaa_closure.py` writes `examples/data/osoaa_closure/`, 408 runs of the
radiative transfer code OSOAA (CNES, GPL v3, commit `8e4914f`) on
Williamson & Hollins's IOPs, for DATA.md section 39 (DECISIONS.md section
90). It needs a built copy of OSOAA, whose path it takes as an argument,
about half an hour on four cores, and about 20 GB of scratch space for
the runs' own files; OSOAA is not part of the package
and is not run in CI. Its output is not in the wheel; `examples/closure_with_jerlov_kd.py` reads it.

`kd_monte_carlo.py` computes the Kd of a homogeneous water by Monte Carlo,
and `python tools/kd_monte_carlo.py --check` runs its checks; `kd_closure.py`
uses it to write `examples/data/kd_closure/runs.csv`, the 240 runs of
DATA.md section 39 (DECISIONS.md section 92), in about forty minutes on four
cores. Each run is seeded. `osoaa_closure.py`'s runs, made again in 1.15.5
with the phase function corrected (DECISIONS.md section 93), are a second
calculation beside them; those of the version that was wrong are kept in
`examples/data/osoaa_closure_f11_too_small/`.

`sm_closure.py` (1.15.6, DECISIONS.md section 94) uses the Monte Carlo
with its two options, pure water's own scattering and a sky, to write
`examples/data/sm_closure/runs.csv`: 2457 runs of Solonenko & Mobley's
IOPs, to set beside their HydroLight Kd, and of Williamson & Hollins's
again, in about half an hour on four cores. Each cell's runs share a seed.
`osoaa_sm_closure.py` runs OSOAA, built as for `osoaa_closure.py`, on the
same cells of Solonenko & Mobley's and writes
`examples/data/osoaa_sm_closure/`, 286 runs, by hand outside CI. Both are
for DATA.md section 40; `examples/closure_with_jerlov_kd.py` reads them.

`blue_end.py` (1.15.7, DECISIONS.md section 95) reads four files of the
Williamson & Hollins dataset from `sources/20290782/`, checks each against
figshare's MD5, reduces them into `examples/data/blue_end/` (the Kd, a and
b of every campaign, with its type, and the matched set as it is), and
runs the Monte Carlo on each matched entry's own a and b, 2365 runs, in
about fifteen minutes on four cores; `--closing` writes the a that would
close each blue cell. DATA.md section 41.

`below_0_1.py` (1.15.8, DECISIONS.md section 96) runs the Monte Carlo at
Petzold's eight stations with and without the report's extension below
0.1 degree, 96 runs in a few minutes, and writes
`examples/data/below_0_1/runs.csv`, which part 3 of
`examples/phase_function_choice.py` reads.

`forward_scatter_mc.py` (1.23.0, DECISIONS.md section 107) follows a
collimated beam through three of Petzold's waters with the same sampler and
counts the light crossing a plane within 0.5 to 20 degrees of the beam's
direction, against single scattering, `jerlov.forward_scatter`'s quantity:
48 cases in a few seconds, written to
`examples/data/forward_scatter/monte_carlo.csv`, which
`tests/test_forward_scatter.py` reads. DATA.md section 49.
