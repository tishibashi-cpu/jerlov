"""The documentation site (DECISIONS.md section 63): the numbers its pages
print are computed by the package, and its reference covers the API."""

from __future__ import annotations

import doctest
import inspect
import pathlib
import re
import warnings

import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree",
)

PAGES = ["index.rst", "guides/light_at_depth.rst", "guides/euphotic_zone.rst",
         "guides/colours_through_water.rst"]


@source_tree
@pytest.mark.parametrize("page", PAGES)
def test_every_number_a_page_prints_is_what_the_package_computes(page):
    with warnings.catch_warnings():
        # The euphotic zone guide says why jerlov1977_quanta warns for IA,
        # II and 1C; the warning goes to stderr, which doctest does not read.
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        result = doctest.testfile(str(DOCS / page), module_relative=False,
                                  verbose=False, report=True)
    assert result.attempted > 0
    assert result.failed == 0


@source_tree
def test_the_guides_are_all_tested_and_all_listed():
    guides = sorted(p.relative_to(DOCS).as_posix()
                    for p in DOCS.glob("guides/*.rst"))
    assert guides == sorted(PAGES[1:])
    index = (DOCS / "index.rst").read_text()
    for guide in guides:
        assert guide.removesuffix(".rst") in index, guide


@source_tree
def test_the_api_reference_covers_all_and_nothing_else():
    text = (DOCS / "api.rst").read_text()
    names = re.findall(
        r"^\.\. (?:auto)?(?:function|class|data|exception):: (\w+)", text,
        re.MULTILINE)
    assert len(names) == len(set(names))
    assert set(names) == set(jerlov.__all__)


@source_tree
def test_the_examples_page_lists_every_example():
    text = (DOCS / "examples.rst").read_text()
    listed = set(re.findall(r"`(\w+\.py) <", text))
    shipped = {p.name for p in (ROOT / "examples").glob("*.py")}
    assert listed == shipped


@source_tree
def test_the_site_is_built_with_warnings_as_errors():
    workflow = (ROOT / ".github" / "workflows" / "docs.yml").read_text()
    assert "sphinx-build -W --keep-going" in workflow
    assert re.search(r"sphinx==\d+\.\d+\.\d+", workflow)


# -- the topics and the map (DECISIONS.md section 106) ------------------------

TOPICS = sorted(p.relative_to(DOCS).as_posix()
                for p in DOCS.glob("topics/*.rst"))


@source_tree
def test_the_topics_are_all_listed():
    index = (DOCS / "index.rst").read_text()
    assert len(TOPICS) == 6
    for page in TOPICS + ["choosing.rst"]:
        assert page.removesuffix(".rst") in index, page


def _linked(text):
    """Names a page links to the API by: :func:`~jerlov.x`, :meth:`...`."""
    return set(re.findall(r":(?:func|meth|class|data):`~?jerlov\.([\w.]+)`",
                          text))


@source_tree
def test_the_map_has_every_public_function():
    text = (DOCS / "choosing.rst").read_text()
    linked = _linked(text)
    mentioned = linked | set(re.findall(r"``jerlov\.(\w+)``", text))
    functions = {n for n in jerlov.__all__
                 if inspect.isfunction(getattr(jerlov, n))}
    covered = {m.split(".")[0] for m in mentioned}
    missing = sorted((functions | {"Water", "Scene"}) - covered)
    assert not missing, f"the map does not say when to use {missing}"


@source_tree
@pytest.mark.parametrize("page", ["choosing.rst"] + TOPICS)
def test_every_name_a_page_gives_exists_and_is_public(page):
    text = (DOCS / page).read_text()
    names = _linked(text) | set(re.findall(r"\bjerlov\.(\w+(?:\.\w+)?)",
                                           text))
    assert names
    for name in names:
        head, _, attribute = name.partition(".")
        assert head in jerlov.__all__, f"{page}: jerlov.{name}"
        if attribute:
            assert hasattr(getattr(jerlov, head), attribute), \
                f"{page}: jerlov.{name}"
