"""Shared paths and input checking for the rebuild scripts.

The primary sources are not kept in version control. When one is missing the
scripts must say what to fetch and from where, rather than raise a traceback.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT / "sources"
DATA_DIR = ROOT / "uwlight" / "data"

FIGSHARE = (
    "figshare DOI 10.6084/m9.figshare.20290782, Version 3\n"
    "  Williamson, C. A. and Hollins, R. C. (2022), 'Dataset to accompany\n"
    "  paper: Measured inherent optical properties of Jerlov water types'.\n"
    "  Crown copyright, Dstl. Open Government Licence v3.0."
)


def require(relative_path: str, origin: str = FIGSHARE) -> pathlib.Path:
    """Return an input path, or explain how to obtain it and exit."""
    path = SOURCES_DIR / relative_path
    if path.exists():
        return path
    print(
        f"missing input: {path}\n\n"
        f"Download it from:\n  {origin}\n\n"
        f"Unpack it so that the file above exists, then run this script again.\n"
        f"See sources/README.md.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def report(name: str, rows: int) -> None:
    print(f"wrote {DATA_DIR / name} ({rows} data rows)")
