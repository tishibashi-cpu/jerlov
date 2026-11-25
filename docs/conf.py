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
exclude_patterns = ["_build", "pages", "extra"]
# Pages made from the package's values by tools/site_pages.py, copied to the
# site's root as they are (DECISIONS.md sections 109 and 120), and files a
# search engine or a sharing card asks for there (sections 112 and 120).
html_extra_path = ["pages", "extra"]
# Gives every page a canonical link, and the sitemap its addresses
# (section 112).
html_baseurl = "https://tishibashi-cpu.github.io/jerlov/"
#: The pages html_extra_path copies that a reader should find.
_EXTRA_PAGES = ("dive.html", "disagree.html", "waters.html", "shallow.html")

# The theme's layout with a card for sharing (DECISIONS.md section 120).
templates_path = ["_templates"]
html_context = {"theme_og_root": html_baseurl}

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
.. _OPEN_QUESTIONS.md: {GITHUB}OPEN_QUESTIONS.md
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


def _sitemap(app, exception):
    """Write sitemap.xml: every page built from a source file, and the pages
    of section 109. Search Console reads it (DECISIONS.md section 112)."""
    if exception is not None or app.builder.format != "html":
        return
    import os
    from xml.sax.saxutils import escape

    pages = [app.builder.get_target_uri(name)
             for name in sorted(app.env.found_docs)]
    pages += list(_EXTRA_PAGES)
    urls = "".join(f"  <url><loc>{escape(html_baseurl + p)}</loc></url>\n"
                   for p in pages)
    path = os.path.join(app.outdir, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + urls + "</urlset>\n")


def setup(app):
    app.connect("autodoc-process-docstring", _constant_docstring)
    app.connect("build-finished", _sitemap)
