"""Render the card a link to the site shows when shared: DECISIONS.md
section 120.

    python tools/og_image.py            # writes docs/extra/og.png

A page of 1200 by 630 pixels, the front page's figure
(docs/figures/kd_types.svg, written by tools/site_pages.py) with the
package's name and line, rendered by a headless Chromium (``--screenshot``):
the one named by the environment variable CHROME, or else the first of
``chromium``, ``chromium-browser`` and ``google-chrome`` on the PATH, or
else Playwright's at /opt/pw-browsers/chromium. A browser is this tool's
need, not the package's; the PNG is committed, and docs/conf.py copies it
to the site's root. Run it after tools/site_pages.py when the figure
changes.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGURE = ROOT / "docs" / "figures" / "kd_types.svg"
OUT = ROOT / "docs" / "extra" / "og.png"
SIZE = (1200, 630)

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><style>
html, body {{ margin: 0; }}
body {{ width: {w}px; height: {h}px; background: #ffffff; color: #12232b;
  font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  display: grid; grid-template-columns: 430px 1fr; align-items: center; }}
.text {{ padding: 0 20px 0 56px; }}
h1 {{ font-size: 76px; margin: 0 0 14px; letter-spacing: -0.01em; }}
p {{ font-size: 27px; line-height: 1.35; margin: 0 0 18px; color: #2c4450; }}
.url {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 17px; white-space: nowrap;
  color: #0b6e8a; }}
.fig {{ padding-right: 28px; }}
.fig svg {{ width: 100%; height: auto; display: block; }}
</style></head><body>
<div class="text"><h1>jerlov</h1>
<p>The Jerlov optical water types, with provenance: absorption, scattering
and Kd from the papers that published them.</p>
<div class="url">tishibashi-cpu.github.io/jerlov</div></div>
<div class="fig">{svg}</div>
</body></html>
"""


def browser() -> str:
    import os
    import shutil

    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in ("chromium", "chromium-browser", "google-chrome"):
        if shutil.which(name):
            return shutil.which(name)
    found = sorted(pathlib.Path("/opt/pw-browsers").glob(
        "chromium-*/chrome-linux*/chrome"))
    if found:
        return str(found[-1])
    raise SystemExit("no Chromium found; set CHROME to one")


def main(out: pathlib.Path = OUT) -> None:
    import subprocess
    import tempfile

    html = PAGE.format(w=SIZE[0], h=SIZE[1], svg=FIGURE.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        page = pathlib.Path(tmp) / "card.html"
        page.write_text(html)
        subprocess.run([browser(), "--headless", "--no-sandbox",
                        "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1",
                        f"--window-size={SIZE[0]},{SIZE[1]}",
                        f"--screenshot={out.resolve()}", page.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
