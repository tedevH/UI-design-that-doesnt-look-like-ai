#!/usr/bin/env python3
"""Render a page (desktop + mobile) and report measured design problems.

usage: check.py page.html
Prints facts, problems (with evidence), and the screenshot paths to look at.
"""

import json
import sys
from pathlib import Path

from _notai import bootstrap

bootstrap()

from notai import tells  # noqa: E402
from notai.director import facts  # noqa: E402
from notai.render import Renderer  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    page = Path(sys.argv[1]).resolve()
    html = page.read_text()
    shots = page.parent / f"{page.stem}-shots"
    with Renderer() as r:
        styles = r.capture(shots, url=page.as_uri(), mobile=True)
    found = tells.detect(html, styles)
    print("FACTS")
    print(facts(html, styles, found))
    print("\nPROBLEMS" + (" (fix all of these)" if found else ": none measured"))
    for t in found:
        print(f"  [{'!' * t.severity:<3}] {t.name}: {t.evidence}")
    empty = html.count("data-photo=") - html.count('src="images/')
    if empty > 0:
        print(f"\nNOTE: {empty} photo slot(s) have no image yet — run photos.py to fill them.")
    print("\nSCREENSHOTS (look at both)")
    print(f"  desktop: {shots / 'desktop.png'}")
    print(f"  mobile:  {shots / 'mobile.png'}")
    (shots / "check.json").write_text(json.dumps({"tells": [t.as_dict() for t in found],
                                                  "overlaps": styles.get("overlaps", 0)}, indent=2))
    return 1 if any(t.severity >= 2 for t in found) else 0


if __name__ == "__main__":
    sys.exit(main())
