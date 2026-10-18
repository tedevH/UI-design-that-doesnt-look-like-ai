"""Bake-off: the same briefs, style families, director and checks for several designer models,
rendered side by side so you can see which free models are good enough to use."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from . import config

SUGGESTED = [
    "gemini-3.8-flash",
    "groq:openai/gpt-oss-120b",
    "openrouter:nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter:google/gemma-4-31b-it:free",
    "openrouter:thinkingmachines/inkling:free",
    "openrouter:poolside/laguna-s-2.1:free",
]
BRIEFS = [
    ("Neighborhood bakery selling sourdough by subscription", "warm-crafted"),
    ("Developer tool that turns SQL queries into internal dashboards", "product-precise"),
    ("Independent architecture studio specializing in timber housing", "editorial-serif"),
]


def _available(model: str) -> bool:
    from .studio import OPENAI_COMPATIBLE

    provider, _, name = model.partition(":")
    if name and provider in OPENAI_COMPATIBLE:
        return bool(os.environ.get(OPENAI_COMPATIBLE[provider][1]))
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def run(models: list[str], briefs=BRIEFS, photos: int = 3, director: str | None = "gemma3:12b") -> Path:
    from PIL import Image, ImageDraw

    from .studio import run_cheap

    out = config.RUNS / f"bakeoff-{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True, exist_ok=True)
    ready = [m for m in models if _available(m)]
    for m in models:
        if m not in ready:
            print(f"skipping {m}: no API key in .env")
    results = []
    for brief, family in briefs:
        row = []
        for m in ready:
            print(f"\n=== {m} | {brief} [{family}]", flush=True)
            t0 = time.time()
            try:
                d, _ = run_cheap(brief, model=m, photos=photos, image_model="local", log=True,
                                 director_model=director, rounds=1, force_family=family)
                review = json.loads((d / "review.json").read_text()) if (d / "review.json").exists() else {}
                row.append({"model": m, "dir": str(d), "score": review.get("score"), "tells": review.get("tells", []),
                            "seconds": round(time.time() - t0)})
            except BaseException as e:  # SystemExit from a missing key or quota must not stop the bake-off
                if isinstance(e, KeyboardInterrupt):
                    raise
                print(f"failed: {str(e)[:200]}", flush=True)
                row.append({"model": m, "error": str(e)[:200]})
        results.append({"brief": brief, "family": family, "results": row})
        _sheet(out / f"{len(results)}-{family}.jpg", brief, row, Image, ImageDraw)
    (out / "results.json").write_text(json.dumps(results, indent=2))
    print(f"\nbake-off sheets in {out}")
    return out


def _sheet(path: Path, brief: str, row: list[dict], Image, ImageDraw) -> None:
    W, H = 520, 900
    sheet = Image.new("RGB", (max(1, len(row)) * (W + 10), H + 60), "white")
    d = ImageDraw.Draw(sheet)
    d.text((6, 4), brief, fill="black")
    for i, r in enumerate(row):
        x = i * (W + 10)
        label = r["model"].split(":")[-2] if r["model"].endswith(":free") else r["model"]
        if r.get("dir") and (Path(r["dir"]) / "desktop.png").exists():
            im = Image.open(Path(r["dir"]) / "desktop.png").convert("RGB")
            im = im.crop((0, 0, 1440, min(im.height, 2490))).resize((W, H))
            sheet.paste(im, (x, 56))
            d.text((x + 4, 22), f"{label[:60]}", fill="black")
            d.text((x + 4, 38), f"director {r.get('score')}/10  problems: {', '.join(r.get('tells') or []) or 'none'}"[:80], fill="black")
        else:
            d.text((x + 4, 22), f"{label[:60]}", fill="black")
            d.text((x + 4, 38), f"failed: {r.get('error', '')[:70]}", fill="red")
    sheet.save(path, quality=86)
