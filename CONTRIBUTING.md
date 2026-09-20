# Contributing

Thank you for looking. This is a small package with a narrow purpose, and the
bar for what goes in it is unusual, so this file sets out what that bar is
before you spend time on something.

## Getting help, and reporting a problem

Open an issue: <https://github.com/tishibashi-cpu/jerlov/issues>

There is no other support channel. Questions are welcome as issues; a question
that is hard to answer usually means the documentation is wrong somewhere.

**For a wrong number, say which number and against what.** A coefficient that
disagrees with a paper you have is the most useful report this package can
receive, and `DATA.md` exists because several such disagreements turned out to
be defects in the literature rather than here. Include the source you compared
against, and which edition of it, since the Jerlov classification has seven.

**For a bug, a short script that reproduces it is enough.** Say which version:

```python
import jerlov
print(jerlov.__version__, jerlov.__file__)
```

## Setting up

```bash
git clone https://github.com/tishibashi-cpu/jerlov
cd jerlov
python -m pip install -e ".[test]"
python -m pytest tests/ -q
for f in examples/*.py; do python "$f" > /dev/null || echo "FAILED $f"; done
```

Use `python -m pip` rather than `pip`; on machines with more than one Python
they are not always the same one, and the package needs setuptools 77 or later
to build.

`pip install -e .` matters for the examples too. `python examples/foo.py` puts
`examples/` on `sys.path`, not the current directory, so without an editable
install an installed copy of the package wins over the working tree. Each
example prints the version and path it loaded so that this is visible.

## What this package will accept

**Any number that is shipped must be traceable to a primary source, and
checkable against it.** That is the whole point of the package, and it is the
main thing that makes contributing here different from most projects.

A new set of coefficients needs all of:

1. **The paper itself**, not a table quoted from it. Record the DOI in
   `sources/README.md`, and the edition if the source has more than one.
2. **A script in `tools/`** that produces the CSV. Values transcribed from a
   printed page go in it as literals; values read from a dataset are read from
   `sources/`, which is not tracked.
3. **Checks inside that script** that test the result against the paper's own
   equations or against another table in the same paper, and that fail loudly.
   `tools/build_paulson1977.py` refits the published parameters from the table
   they were fitted to; `tools/build_boss2001.py` checks an analytic
   conversion factor against the definition it comes from.
4. **An entry in `DATA.md`** saying what the table is, what was verified, and
   what is known to be wrong with it.
5. **A regression test** in `tests/test_reproduces_papers.py` if the values
   can be checked against a printed table cell by cell.

Running every script in `tools/` must reproduce the shipped CSVs byte for
byte:

```bash
for f in tools/build_*.py; do python "$f" || break; done
git diff --stat jerlov/data/     # must be empty
```

If it is not empty, either the script or the table has drifted. **Explain the
difference before changing either.**

### Values that are wrong stay wrong

Where a published value is a defect, it is flagged, not repaired:

| Situation | What to do |
|---|---|
| Recoverable from the paper's own equations | Recover it, `status = reconstructed`, record the method |
| Not recoverable | Leave it empty, `status = missing` |
| Used but doubtful | Use it, `status = suspect`, record why |

Do not silently correct, interpolate over, or substitute a neighbouring value.
A repaired number is indistinguishable from a sound one at the point of use.

### Quantities the data do not determine are refused

`Water.bb` raises rather than returning a plausible backscattering ratio,
because the Jerlov classification does not determine one. If you find yourself
wanting to add a default for something, that is the signal to check whether
the quantity is actually determined; `DATA.md` section 10 is what that check
looked like the last time.

## Code

Runtime dependencies are **NumPy only**. `openpyxl`, `colour-science` and
`scipy` are build-time dependencies of `tools/` and must not leak into the
package. A related project has been broken since 2019 because a dependency
moved a module, and nobody noticed for seven years.

The declared lower bound is tested. `pyproject.toml` says `numpy>=1.22`, and
CI runs a job pinned to it. Use `jerlov._data.trapezoid` rather than
`np.trapezoid` or `np.trapz`: one arrived in NumPy 2.0 and the other left in
it. A test refuses either name anywhere in the repository.

Scalar input returns a scalar, arrays return arrays, matching `numpy.interp`.

## Tests

```bash
python -m pytest tests/ -q
```

Every test should fail for a reason you can state. The suite is not only about
the code:

| File | What it holds |
|---|---|
| `test_reproduces_papers.py` | Each paper's equations must reproduce its own tables |
| `test_packaging.py` | The repository agrees with itself: versions, counts, tables, metadata |
| `test_quoted_figures.py` | Every figure the documentation states, recomputed |
| the rest | Behaviour |

If you change a coefficient and a test in `test_quoted_figures.py` fails, the
sentence that quotes it needs updating too. That is what the test is for.

If you add a check, break it deliberately once and confirm it fails with a
message that says what to do. A check that has never failed has not been
tested.

## Documentation

`DATA.md` is where a number's provenance goes. `DECISIONS.md` is where a
choice goes, including the alternatives that were rejected and why; it is
append-only, and a reversal is a new entry saying so rather than an edit.

If you change what the package can do, update `.zenodo.json` as well. It is
read only when Zenodo archives a release, so nothing else notices when it goes
stale. It went stale four times before a test was added.

## Pull requests

Small and focused is easier to review than complete. Say in the description
what the change is for; if it adds data, say which paper and which edition.

CI runs the tests on Python 3.10 to 3.13, a job pinned to the oldest declared
NumPy, and every example. All of it should be green before review.

## Scope

`DECISIONS.md` section 12 lists what is deliberately out: solving the
radiative transfer equation, remote sensing reflectance, machine-learning
image restoration, and deriving new coefficients from primary observations.

That list has been wrong once. Shortwave heating was ruled out on a
similarity of subject matter rather than on whether the provenance could be
established, and was reversed in section 19. **If you think something on the
list belongs in, the argument to make is that its numbers can be traced and
checked**, not that it is related.

## Licence

Apache-2.0. Contributions are taken under the same licence. Data carried from
other sources keeps its own terms; the Williamson & Hollins tables are Crown
copyright under the Open Government Licence v3.0, recorded in `NOTICE`.
