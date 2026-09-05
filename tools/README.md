# Rebuilding the coefficient tables

These scripts are the record of how every value in `uwlight/data/` was
obtained. Running them must reproduce the shipped CSVs byte for byte; if it
does not, either the scripts or the CSVs have drifted and the difference must
be explained before either is changed.

```
pip install numpy openpyxl
for f in tools/build_*.py; do python "$f" || break; done
git diff --stat uwlight/data/     # must be empty
```

Two of the scripts need no input and will run immediately;
the others stop with a message naming the file to fetch and its DOI.

`openpyxl` is needed only here, never at run time.

Each script prints the checks it performs. They are not decoration: the
duplicated rows in Solonenko & Mobley Table 7 were found by exactly these
comparisons.

Every table has a script. Those whose values are transcribed from a paper
rather than read from a dataset keep the numbers as literals and check them
against the paper's own equations before writing anything.
