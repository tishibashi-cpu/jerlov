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

Two of the scripts need no input and will run immediately;
the others stop with a message naming the file to fetch and its DOI.

`openpyxl` and `colour-science` are needed only here, never at run time.
`build_cie.py` uses `colour-science` as a carrier for the CIE tabulations;
see DATA.md section 12.

Each script prints the checks it performs. They are not decoration: the
duplicated rows in Solonenko & Mobley Table 7 were found by exactly these
comparisons.

Every table has a script. Those whose values are transcribed from a paper
rather than read from a dataset keep the numbers as literals and check them
against the paper's own equations before writing anything.
