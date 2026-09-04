# Rebuilding the coefficient tables

These scripts are the record of how every value in `uwlight/data/` was
obtained. Running them must reproduce the shipped CSVs byte for byte; if it
does not, either the scripts or the CSVs have drifted and the difference must
be explained before either is changed.

```
pip install numpy openpyxl
python tools/build_austin1986.py
python tools/build_jerlov1976_and_solonenko2015.py
python tools/build_williamson2022_iop.py
python tools/build_williamson2022_measured.py
git diff --stat uwlight/data/     # must be empty
```

`openpyxl` is needed only here, never at run time.

Each script prints the checks it performs. They are not decoration: the
duplicated rows in Solonenko & Mobley Table 7 were found by exactly these
comparisons.

`smart2007_b_from_c.csv` has no script; it is a ten-row transcription of
Table 1 of Smart (2007) and is checked in `tests/test_api.py`.
