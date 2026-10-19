#!/usr/bin/env python3
"""Render a page (desktop + mobile) and report measured design problems.

usage: check.py page.html
Prints facts, problems with evidence, and the two screenshot paths to look at.
Exit code 1 if anything serious was found.
"""

import json
import sys
from pathlib import Path

from _env import bootstrap

bootstrap()

from lib import tells, tokens  # noqa: E402
from lib.render import Renderer  # noqa: E402


def facts(styles: dict) -> str:
    s, f = tokens.summary(styles), tokens.features(styles)
    return "\n".join([
        f"- fonts in use: {', '.join(s['fonts']) or 'unknown'}",
        f"- type sizes (px): {s['type_sizes']}; largest/body ratio {s['type_scale']}",
        f"- main colors: text {s['text_colors']}, backgrounds {s['bg_colors']}",
        f"- page height: {round((styles.get('docHeight') or 0) / 900, 1)} screens; ~{round(f['words_per_screen'])} words per screen",
        f"- overlapping text boxes: {styles.get('overlaps', 0)}",
    ])


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
    print("FACTS\n" + facts(styles))
    print("\nPROBLEMS" + (" (fix all of these)" if found else ": none measured"))
    for t in found:
        print(f"  [{'!' * t.severity:<3}] {t.name}: {t.evidence}")
    empty = html.count("data-photo=") - html.count('src="images/')
    if empty > 0:
        print(f"\nNOTE: {empty} slot(s) waiting for the user's own photos (shown as striped blocks). Tell the user what to send.")
    print(f"\nSCREENSHOTS (look at both)\n  desktop: {shots / 'desktop.png'}\n  mobile:  {shots / 'mobile.png'}")
    (shots / "check.json").write_text(json.dumps({"tells": [t.as_dict() for t in found],
                                                  "overlaps": styles.get("overlaps", 0)}, indent=2))
    return 1 if any(t.severity >= 2 for t in found) else 0


if __name__ == "__main__":
    sys.exit(main())
