"""The version is written in three files, so it drifts.

It has drifted twice: once between `pyproject.toml` and `jerlov/__init__.py`,
and once between the working tree and an installed copy. Both were found by
someone noticing a wrong number in output, which is not a method.

These checks only apply to a source tree. Running the suite against an
installed wheel skips them, because `pyproject.toml` and `CITATION.cff` are
not shipped.
"""

from __future__ import annotations

import pathlib
import re

import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree",
)


def _declared(path: pathlib.Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(), re.MULTILINE)
    assert match, f"no version found in {path.name}"
    return match.group(1).strip()


@source_tree
def test_the_three_declared_versions_agree():
    toml = _declared(ROOT / "pyproject.toml", r'^version = "(.+?)"')
    cff = _declared(ROOT / "CITATION.cff", r"^version: (.+)$")
    assert jerlov.__version__ == toml, (
        f"jerlov/__init__.py says {jerlov.__version__}, "
        f"pyproject.toml says {toml}"
    )
    assert jerlov.__version__ == cff, (
        f"jerlov/__init__.py says {jerlov.__version__}, "
        f"CITATION.cff says {cff}"
    )


@source_tree
def test_the_version_looks_like_a_release():
    assert re.fullmatch(r"\d+\.\d+\.\d+", jerlov.__version__), (
        f"{jerlov.__version__!r} is not a plain release version"
    )


@source_tree
def test_the_package_under_test_is_the_one_in_this_tree():
    """Guards the sys.path trap that made the examples load an old install."""
    imported = pathlib.Path(jerlov.__file__).resolve().parent
    assert imported == ROOT / "jerlov", (
        f"tests import jerlov from {imported}, not from {ROOT / 'jerlov'}; "
        "run `pip install -e .` in the repository"
    )


@source_tree
def test_every_shipped_table_is_listed_in_DATA_md():
    """A table nobody documented is a table with no provenance."""
    documented = (ROOT / "DATA.md").read_text()
    for csv in sorted((ROOT / "jerlov" / "data").glob("*.csv")):
        assert csv.name in documented, f"{csv.name} is not mentioned in DATA.md"


@source_tree
def test_every_shipped_table_has_a_build_script_or_is_explained():
    """Each table should be regenerable; tools/README.md says so."""
    scripts = " ".join(p.read_text() for p in (ROOT / "tools").glob("*.py"))
    for csv in sorted((ROOT / "jerlov" / "data").glob("*.csv")):
        assert csv.name in scripts, f"no build script writes {csv.name}"


# -- the documentation counts itself -------------------------------------

_SPELLED = ["zero", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
            "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
            "twenty", "twenty-one", "twenty-two", "twenty-three",
            "twenty-four", "twenty-five"]
WORDS = {word: value for value, word in enumerate(_SPELLED)}
WORDS.update({word.capitalize(): value
              for value, word in enumerate(_SPELLED)})


def _numbered_sections(text: str) -> int:
    return len(re.findall(r"^## \d+\. ", text, re.MULTILINE))


def _confirmed_sections(text: str) -> int:
    return len(re.findall(r"^## \d+\..*\(confirmed", text, re.MULTILINE))


@source_tree
def test_DATA_md_counts_its_own_sections():
    """The opening summary is written by hand and has drifted three times."""
    text = (ROOT / "DATA.md").read_text()
    match = re.search(r"^(\w+) entries are recorded below\. (\w+) are confirmed",
                      text, re.MULTILINE)
    assert match, "DATA.md no longer opens with a countable summary"
    claimed_total, claimed_confirmed = (WORDS[g] for g in match.groups())
    assert claimed_total == _numbered_sections(text)
    assert claimed_confirmed == _confirmed_sections(text)


@source_tree
def test_the_zenodo_record_will_carry_what_it_should():
    """`.zenodo.json` is only read at archive time, so nothing else checks it."""
    import json

    record = json.loads((ROOT / ".zenodo.json").read_text())
    assert record["upload_type"] == "software"
    assert record["license"] == "Apache-2.0"
    assert record["creators"], "a record with no author is not citable"
    for creator in record["creators"]:
        assert creator.get("orcid"), (
            f"{creator['name']} has no ORCID, so the record will not attach "
            "to their publication list"
        )
    # Every source the package ships data from should be reachable from the
    # record, not only from DATA.md.
    derived = [r["identifier"] for r in record["related_identifiers"]
               if r["relation"] == "isDerivedFrom"]
    assert len(derived) >= 8, derived


@source_tree
def test_the_README_agrees_with_DATA_md_on_the_count():
    data = (ROOT / "DATA.md").read_text()
    readme = (ROOT / "README.md").read_text()
    match = re.search(r"(\w+) entries are\s+documented there: (\w+) confirmed",
                      readme)
    assert match, "the README no longer states the count"
    assert WORDS[match.group(1)] == _numbered_sections(data)
    assert WORDS[match.group(2)] == _confirmed_sections(data)


@source_tree
def test_the_zenodo_description_agrees_with_DATA_md():
    """It has now gone stale four times, and only an archive run reads it."""
    import json

    record = json.loads((ROOT / ".zenodo.json").read_text())
    data = (ROOT / "DATA.md").read_text()
    description = record["description"]

    match = re.search(r"(\w+) entries are documented, (\w+) of them confirmed",
                      description)
    assert match, "the Zenodo description no longer states a countable summary"
    assert WORDS[match.group(1)] == _numbered_sections(data), (
        f".zenodo.json says {match.group(1)}, DATA.md has "
        f"{_numbered_sections(data)} sections"
    )
    assert WORDS[match.group(2)] == _confirmed_sections(data)


@source_tree
def test_the_zenodo_record_names_every_shipped_module():
    """A capability the record does not mention is one nobody will find."""
    record = __import__("json").loads((ROOT / ".zenodo.json").read_text())
    described = record["description"].lower()
    for module, phrase in (
        ("scene.py", "veiling"),
        ("colour.py", "srgb"),
        ("shortwave.py", "shortwave"),
        ("backscattering.py", "backscattering coefficient"),
        ("water.py", "scattering coefficients"),
    ):
        assert (ROOT / "jerlov" / module).exists()
        assert phrase in described, (
            f"{module} ships but the Zenodo description never mentions "
            f"{phrase!r}"
        )


@source_tree
def test_every_module_can_find_the_tables_it_reads():
    """A missing data file should fail here, not thirteen tests later.

    `jerlov/data/boss2001_chi.csv` once failed to reach a working copy, and
    the first sign of it was thirteen unrelated-looking FileNotFoundErrors
    deep inside the backscattering tests.
    """
    shipped = {p.name for p in (ROOT / "jerlov" / "data").glob("*.csv")}
    wanted = set()
    for module in (ROOT / "jerlov").glob("*.py"):
        wanted |= set(re.findall(r'_rows\(\s*"([^"]+\.csv)"', module.read_text()))
    assert wanted, "no module reads a table any more, which cannot be right"
    missing = sorted(wanted - shipped)
    assert not missing, (
        f"these are read by jerlov/*.py but not present in jerlov/data/: "
        f"{missing}. Run the matching script in tools/."
    )


@source_tree
def test_every_build_script_produces_a_shipped_table():
    """The other direction: a script whose output never arrived."""
    shipped = {p.name for p in (ROOT / "jerlov" / "data").glob("*.csv")}
    for script in sorted((ROOT / "tools").glob("build_*.py")):
        written = set(re.findall(r'DATA_DIR / "([^"]+\.csv)"', script.read_text()))
        written |= set(re.findall(r'report\(\s*"([^"]+\.csv)"', script.read_text()))
        assert written, f"{script.name} writes no table"
        missing = sorted(written - shipped)
        assert not missing, (
            f"{script.name} writes {missing}, which is not in jerlov/data/"
        )


@source_tree
def test_nothing_reaches_for_a_numpy_2_only_name():
    """`numpy.trapezoid` arrived in NumPy 2.0 and `numpy.trapz` left in it.

    `jerlov._data.trapezoid` resolves whichever exists. This has now been got
    wrong twice: once in colour.py, shipped in 0.1.1, and once in the
    backscattering tests, caught by CI before release. Both times the local
    NumPy was new enough for it to pass.
    """
    offenders = []
    for path in list(ROOT.glob("jerlov/*.py")) + list(ROOT.glob("tests/*.py")) \
            + list(ROOT.glob("tools/*.py")) + list(ROOT.glob("examples/*.py")):
        text = path.read_text()
        for name in ("np.trapezoid", "np.trapz", "numpy.trapezoid",
                     "numpy.trapz"):
            if name + "(" in text:
                offenders.append(f"{path.relative_to(ROOT)}: {name}")
    assert not offenders, (
        "use jerlov._data.trapezoid instead, which resolves whichever name "
        f"the installed NumPy has: {offenders}"
    )
