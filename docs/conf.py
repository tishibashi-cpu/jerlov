"""Sphinx configuration for the jerlov documentation site.

DECISIONS.md section 63. Built by .github/workflows/docs.yml with
`sphinx-build -W --keep-going -b html docs docs/_build/html`.
"""

import pkgutil

from sphinx.pycode import ModuleAnalyzer

import jerlov

project = "jerlov"
author = "T. Ishibashi"
copyright = "T. Ishibashi; Apache-2.0"
release = jerlov.__version__
version = release

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
napoleon_google_docstring = False
autodoc_member_order = "bysource"
autodoc_typehints = "signature"
# Types by their own names, not the module paths 1.0 does not promise.
python_use_unqualified_type_names = True
exclude_patterns = ["_build"]

html_theme = "alabaster"
html_title = f"jerlov {release}"
html_theme_options = {
    "description": "The Jerlov optical water types, with provenance",
    "github_user": "tishibashi-cpu",
    "github_repo": "jerlov",
    "github_button": False,
    # The default 940px cuts the docstrings' 79-character lines.
    "page_width": "1140px",
    "body_max_width": "none",
}

GITHUB = "https://github.com/tishibashi-cpu/jerlov/blob/main/"
rst_epilog = f"""
.. _DECISIONS.md: {GITHUB}DECISIONS.md
.. _DATA.md: {GITHUB}DATA.md
.. _CHANGELOG.md: {GITHUB}CHANGELOG.md
.. _CONTRIBUTING.md: {GITHUB}CONTRIBUTING.md
.. _issues: https://github.com/tishibashi-cpu/jerlov/issues
"""


def _attribute_docs():
    """The docstrings of the module-level constants, by name.

    They are written below each constant in the module that defines it, so
    autodoc, documenting `jerlov.SOURCES`, does not find them and falls
    back to the docstring of `dict` (DECISIONS.md section 63).
    """
    docs = {}
    for info in pkgutil.iter_modules(jerlov.__path__):
        analyzer = ModuleAnalyzer.for_module(f"jerlov.{info.name}")
        for (scope, name), lines in analyzer.find_attr_docs().items():
            if scope == "":
                docs.setdefault(name, list(lines))
    return docs


_CONSTANT_DOCS = _attribute_docs()


def _constant_docstring(app, what, name, obj, options, lines):
    if what == "data" and name.startswith("jerlov."):
        lines[:] = _CONSTANT_DOCS.get(name.split(".", 1)[1], [])


def setup(app):
    app.connect("autodoc-process-docstring", _constant_docstring)
