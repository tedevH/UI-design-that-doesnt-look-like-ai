#!/usr/bin/env python3
"""Fill every <img data-photo="..."> slot in a page with a locally generated photo (FLUX, free).

usage: photos.py page.html [--style "35mm film, warm window light"]
Photos are saved next to the page in images/ and referenced relatively. Already-made photos are reused.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

from _notai import bootstrap

bootstrap()

from notai.studio import own_photos_only  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--style", default="editorial photography, natural light, true-to-life color")
    ap.add_argument("--max", type=int, default=8)
    a = ap.parse_args()
    page = Path(a.page).resolve()
    html = own_photos_only(page.read_text())
    try:
        from notai import localimage
    except Exception as e:  # mflux not installed in this environment
        print(f"local photo generation isn't available ({e}); leaving the slots as they are")
        return 0
    images = page.parent / "images"
    images.mkdir(exist_ok=True)
    made = {}

    def swap(m):
        tag = m.group(0)
        desc = re.search(r'data-photo="([^"]+)"', tag).group(1)
        aspect = (re.search(r'data-aspect="([\d:]+)"', tag) or [None, "4:3"])[1]
        name = hashlib.sha1(f"{a.style}|{desc}|{aspect}".encode()).hexdigest()[:12] + ".jpg"
        out = images / name
        if not out.exists():
            if len(made) >= a.max:
                return tag
            print(f"  photo {len(made) + 1}: {desc[:80]} ({aspect})", flush=True)
            try:
                localimage.generate(f"{desc}. Style: {a.style}. Photograph, no text, no watermark.", aspect, out)
            except Exception as e:
                print(f"    failed: {str(e)[:120]}")
                return tag
            made[desc] = out
        tag = re.sub(r'\ssrc="[^"]*"', "", tag)
        return tag.replace("<img", f'<img src="images/{name}"', 1)

    html = re.sub(r'<img\b[^>]*\bdata-photo="[^"]+"[^>]*>', swap, html)
    page.write_text(html)
    print(f"done: {len(made)} new photo(s) in {images}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
