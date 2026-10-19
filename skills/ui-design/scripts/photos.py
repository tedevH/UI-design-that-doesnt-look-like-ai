#!/usr/bin/env python3
"""Fill every <img data-photo="..."> slot in a page with a generated photo.

usage: photos.py page.html [--style "35mm film, warm window light"] [--mode local|gemini|none]
Mode defaults to what setup.sh chose. Photos are saved next to the page in images/ and referenced
relatively; already-made photos are reused. Web-linked images are turned into slots first.
Run it in the background right after building the page: it's the slow step (local ≈ 30–40 s/photo).
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

from _env import bootstrap, config

bootstrap()

ASPECTS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}


def own_photos_only(html: str) -> str:
    """Hotlinked web images become data-photo slots described by their alt text."""
    def swap(m):
        tag = m.group(0)
        if "data-photo=" in tag or not re.search(r'\ssrc="https?://', tag):
            return tag
        alt = re.search(r'\salt="([^"]*)"', tag)
        desc = (alt.group(1) if alt and alt.group(1).strip() else "photograph that fits this section").replace('"', "'")
        return re.sub(r'\ssrc="[^"]*"', "", tag).replace("<img", f'<img data-photo="{desc}" data-aspect="4:3"', 1)
    return re.sub(r"<img\b[^>]*>", swap, html)


def gemini_photo(prompt: str, aspect: str, out: Path) -> None:
    from google import genai
    from google.genai import types

    client = genai.Client()
    r = client.models.generate_content(
        model=os.environ.get("UI_DESIGN_GEMINI_IMAGE_MODEL", "gemini-3.1-flash-lite-image"), contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio=aspect)))
    for p in r.candidates[0].content.parts:
        if p.inline_data:
            out.write_bytes(p.inline_data.data)
            return
    raise RuntimeError("no image returned")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--style", default="editorial photography, natural light, true-to-life color")
    ap.add_argument("--mode", default=config().get("photos", "none"), choices=["local", "gemini", "none"])
    ap.add_argument("--max", type=int, default=6)
    a = ap.parse_args()
    page = Path(a.page).resolve()
    html = own_photos_only(page.read_text())
    if a.mode == "none":
        page.write_text(html)
        print("photo mode is 'none': leaving labeled slots (change with setup.sh)")
        return 0
    if a.mode == "local":
        from lib import localimage
    images = page.parent / "images"
    images.mkdir(exist_ok=True)
    made = []

    def swap(m):
        tag = m.group(0)
        desc = re.search(r'data-photo="([^"]+)"', tag).group(1)
        aspect = (re.search(r'data-aspect="([\d:]+)"', tag) or [None, "4:3"])[1]
        aspect = aspect if aspect in ASPECTS else "4:3"
        name = hashlib.sha1(f"{a.mode}|{a.style}|{desc}|{aspect}".encode()).hexdigest()[:12] + ".jpg"
        out = images / name
        if not out.exists():
            if len(made) >= a.max:
                return tag
            prompt = f"A single photograph, no text, no watermark. {desc}. Style: {a.style}."
            print(f"  photo {len(made) + 1}: {desc[:80]} ({aspect})", flush=True)
            try:
                if a.mode == "local":
                    localimage.generate(prompt, aspect, out)
                else:
                    gemini_photo(prompt, aspect, out)
            except Exception as e:
                print(f"    failed: {str(e)[:150]}")
                return tag
            made.append(out)
        return re.sub(r'\ssrc="[^"]*"', "", tag).replace("<img", f'<img src="images/{name}"', 1)

    html = re.sub(r'<img\b[^>]*\bdata-photo="[^"]+"[^>]*>', swap, html)
    page.write_text(html)
    print(f"done: {len(made)} new photo(s) in {images}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
