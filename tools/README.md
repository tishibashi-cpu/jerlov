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

Eleven of the scripts read no file and will run immediately: ten carry
their numbers as literals, and `build_cie.py` takes the CIE tables from
`colour-science`. The others stop with a message naming the file to fetch
and its DOI.

`openpyxl` and `colour-science` are needed only here, never at run time.
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
`nygard1973_levels.py` and its transcription `nygard1973_quanta.csv` are
the analysis of DECISIONS.md section 55, Nygård's measured profiles of
quanta checked against Jerlov's IB, and `smith1973_blue.py` with
`smith1973_blue.csv` that of section 56, Smith's spectra at the same
stations; `morel1973_levels.py` and `baird1973_chlorophyll.py`, with their
CSVs, those of section 58, Morel's profiles and the chlorophyll. The
transcriptions are not shipped.
