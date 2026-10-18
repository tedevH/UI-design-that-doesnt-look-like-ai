"""Score an eval run from scripts/eval_skill.sh: same checks and the same blind director for both sides.

usage: .venv/bin/python scripts/score_eval.py designs/eval/<timestamp>
Writes results.json, results.md and one side-by-side sheet per brief into that folder.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from notai import tells
from notai.director import Director
from notai.render import Renderer
from notai.studio import fold_jpeg

BRIEFS = ["Pediatric dental practice in Austin", "API monitoring tool for startups",
          "Independent bookstore and café in Portland"]


def main(run: Path) -> None:
    director = Director("gemma3:12b")
    rows = []
    with Renderer() as r:
        for i, brief in enumerate(BRIEFS):
            row = {"brief": brief}
            for side in ("plain", "skill"):
                page = run / f"{side}-{i}" / "page.html"
                if not page.exists():
                    row[side] = {"error": "no page produced"}
                    continue
                shots = run / f"{side}-{i}" / "score-shots"
                styles = r.capture(shots, url=page.resolve().as_uri(), mobile=True)
                html = page.read_text()
                found = tells.detect(html, styles)
                review = director.critique(brief, "any style that fits the brand", fold_jpeg(shots / "desktop.png", width=768), html, styles)
                row[side] = {"tells": [t.name for t in found], "penalty": tells.penalty(found),
                             "overlaps": styles.get("overlaps", 0), "director": review["score"],
                             "issues": [i.get("problem") for i in review["issues"][:3]],
                             "height_screens": round((styles.get("docHeight") or 0) / 900, 1)}
                print(f"{side:<5} {brief[:40]:<40} director {review['score']}/10  problems {row[side]['tells']}", flush=True)
            rows.append(row)
            sheet(run, i, brief)
    (run / "results.json").write_text(json.dumps(rows, indent=2))
    lines = ["| Brief | Plain AI (no skill) | With skill |", "|---|---|---|"]
    for row in rows:
        cell = lambda s: (f"director {s['director']}/10, problems: {', '.join(s['tells']) or 'none'}"
                          if "director" in s else s.get("error", ""))
        lines.append(f"| {row['brief']} | {cell(row['plain'])} | {cell(row['skill'])} |")
    (run / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def sheet(run: Path, i: int, brief: str) -> None:
    W, H = 640, 1040
    out = Image.new("RGB", (W * 2 + 10, H + 34), "white")
    d = ImageDraw.Draw(out)
    for k, side in enumerate(("plain", "skill")):
        p = run / f"{side}-{i}" / "score-shots" / "desktop.png"
        if p.exists():
            im = Image.open(p).convert("RGB")
            im = im.crop((0, 0, 1440, min(im.height, 2340))).resize((W, H))
            out.paste(im, (k * (W + 10), 30))
        d.text((k * (W + 10) + 4, 8), f"{'PLAIN AI (no skill)' if side == 'plain' else 'WITH SKILL'} — {brief}", fill="black")
    out.save(run / f"compare-{i}.jpg", quality=86)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
