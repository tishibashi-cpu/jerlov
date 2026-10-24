"""Print the GitHub Release text for a version, from its CHANGELOG section.

The release workflow runs this when it publishes a version (DECISIONS.md
section 51), so that the Release says what CHANGELOG.md says and nothing is
written twice:

    python tools/release_notes.py 0.19.2

The text is the section's body, under a heading naming the package and the
version. CHANGELOG.md wraps its lines at 79 characters, and GitHub shows
every line break in a Release as a break, so the lines of each paragraph
and list item are joined. A version without a section, or with an empty
one, is an error: the workflow stops before anything is uploaded.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


_STARTS_A_LINE = re.compile(r"^\s*(?:[-*+] |\d+\. |#)")


def unwrap(text: str) -> str:
    """Join wrapped lines into one line per paragraph or list item."""
    lines: list[str] = []
    joining = False
    for line in text.splitlines():
        if not line.strip():
            lines.append("")
            joining = False
        elif joining and not _STARTS_A_LINE.match(line):
            lines[-1] += " " + line.strip()
        else:
            lines.append(line.rstrip())
            joining = True
    return "\n".join(lines)


def release_notes(version: str, changelog: str) -> str:
    """The Release text for ``version`` from the text of CHANGELOG.md."""
    heading = re.compile(rf"^## {re.escape(version)} — \d{{4}}-\d{{2}}-\d{{2}}$",
                         re.M)
    found = heading.search(changelog)
    if found is None:
        raise ValueError(f"CHANGELOG.md has no section for {version}")
    rest = changelog[found.end():]
    following = re.search(r"^## ", rest, re.M)
    body = (rest[:following.start()] if following else rest).strip()
    if not body:
        raise ValueError(f"CHANGELOG.md's section for {version} is empty")
    return f"## jerlov {version}\n\n{unwrap(body)}\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python tools/release_notes.py VERSION", file=sys.stderr)
        return 2
    try:
        text = release_notes(argv[1], (ROOT / "CHANGELOG.md").read_text(
            encoding="utf-8"))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
