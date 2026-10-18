"""Studio mode: art direction → full pages with generated photography → visual judging → revision.

Uses Gemini for everything: picking reference sites, writing art directions, writing the HTML,
generating the photos the HTML asks for, and judging rendered screenshots against the references.
The rule-based tells and the critic are reported, but the choice of page is made by looking at it.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import config, tells
from .config import need
from .util import extract_html, slugify

ASPECTS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
MAX_PHOTOS = 7

REFERENCE_PICK = """\
You are choosing visual references for a web design project.
Brief: {brief}

Candidate reference sites (all well designed):
{sites}

Pick the {k} whose craft, mood and level of polish would best inspire a page for this brief.
Variety is good. Return JSON: {{"picks": ["slug", ...]}}"""

ART_DIRECTION = """\
You are the creative director at a top design studio (think Pentagram, Collins, Locomotive, Instrument).
The attached screenshots are references for the level of craft we want — study their typography, color,
photography, composition and confidence. Do not copy them.

Brief: {brief}

Propose {n} genuinely different art directions. Each must be bold and specific enough that two designers
would build nearly the same page from it. Avoid the generic startup look and avoid timid beige minimalism.

Return JSON:
{{"directions": [{{
  "name": "...",
  "concept": "one or two sentences: the idea that makes this brand memorable",
  "palette": [{{"hex": "#...", "role": "background | text | signature color used as large fields | accent | ..."}}],
  "type": {{"display": "Google Font family", "text": "Google Font family", "notes": "sizes, weights, case, tracking"}},
  "photo_style": "lens, light, color grade, subject matter — consistent across all photos",
  "sections": [{{"name": "...", "content": "what it says/shows, concretely", "layout": "composition, e.g. full-bleed photo with type overlapping the bottom edge"}}],
  "signature_detail": "one memorable design move"
}}]}}
Use 4–6 palette colors including one confident signature color. Use 6–8 sections, each composed differently."""

BUILD = """\
Build this landing page. You are a world-class designer-developer; this should look like it won an award.

Brief: {brief}

Art direction:
{direction}

Requirements:
- One self-contained HTML file. Hand-written CSS in <style> (CSS custom properties for the palette),
  Google Fonts via <link>. Vanilla JS only if an interaction needs it.
- Photography is essential. Use <img data-photo="detailed description of one photograph" data-aspect="16:9" alt="...">
  for every photo (aspects: 1:1, 3:4, 4:3, 4:5, 3:2, 16:9, 21:9, 9:16). Real photos will be generated from
  your descriptions in the art direction's photo style, so describe subject, framing and light precisely.
  Use 4–{max_photos} photos and make them big: full-bleed heroes, split screens, asymmetric grids, overlaps.
  Never draw placeholder boxes, ovals or empty frames. Use object-fit: cover.
- Implement every section from the art direction with its own composition. Use the signature color as large
  fields (whole sections or big blocks), not just accents. Display type should be large and expressive.
- Craft: a consistent spacing scale, deliberate alignment, hover states and subtle transitions, a real
  header and footer, responsive down to 390px wide with no horizontal scroll.
- Copy: specific, believable names, prices, times, addresses and details. Short, confident sentences.
- Avoid the AI-template look: purple/blue gradients, glassmorphism, emoji icons, centered hero followed by
  three identical icon cards, and words like unlock, elevate, seamless, revolutionize, empower.

Return only the HTML file in a ```html code block."""

JUDGE = """\
You are judging candidate landing pages for: {brief}
The first {r} images are references showing the craft level we want. Then come {n} candidates, in order,
labeled by their position (candidate 0, 1, ...). Each candidate image is the top part of its page.

Judge as a top design director: visual impact, typography, color, photography, composition, polish,
and whether it looks like a real studio made it rather than a template or an AI.
Return JSON: {{"scores": [1-10 per candidate], "best": index,
"fixes": ["specific, concrete fixes for the best candidate, naming elements and values", ...]}}"""

REVISE = """\
Here is the current page (HTML below) and its screenshot. A design director asked for these fixes:
{fixes}

Apply them and push the craft further while keeping the art direction. Keep the same data-photo
descriptions for photos you keep (they are already generated); new ones are allowed.
Return the full revised HTML file in a ```html code block.

```html
{html}
```"""


class Studio:
    def __init__(self, model: str | None = None, image_model: str = "gemini-3.1-flash-image"):
        from .backends import Gemini

        g = Gemini(model or config.DEFAULT_GEMINI_MODEL)
        self.client, self.types, self.model = g.client, g.types, g.model
        self.image_model = image_model

    # ---- model calls ----

    def _parts(self, items) -> list:
        """Strings stay text; Paths / bytes become images."""
        parts = []
        for it in items:
            if isinstance(it, (bytes, bytearray)):
                parts.append(self.types.Part.from_bytes(data=bytes(it), mime_type="image/jpeg"))
            else:
                parts.append(self.types.Part.from_text(text=str(it)))
        return parts

    def ask(self, items, json_out: bool = False, temperature: float = 1.0) -> str:
        cfg = self.types.GenerateContentConfig(
            temperature=temperature, max_output_tokens=65536,
            response_mime_type="application/json" if json_out else None)
        r = self.client.models.generate_content(model=self.model, contents=self._parts(items), config=cfg)
        return r.text or ""

    def photo(self, prompt: str, aspect: str, style: str, out: Path) -> bool:
        if out.exists():
            return True
        full = (f"A single photograph — one frame, not a collage or diptych. No text, logos or watermarks. "
                f"Style: {style}. Subject: {prompt}")
        try:
            r = self.client.models.generate_content(
                model=self.image_model, contents=full,
                config=self.types.GenerateContentConfig(
                    response_modalities=["IMAGE"], image_config=self.types.ImageConfig(aspect_ratio=aspect)))
            for p in r.candidates[0].content.parts:
                if p.inline_data:
                    out.write_bytes(p.inline_data.data)
                    return True
        except Exception as e:
            print(f"    photo failed ({aspect}): {str(e)[:120]}")
        return False

    # ---- pipeline pieces ----

    def references(self, brief: str, k: int = 3) -> list[tuple[str, bytes]]:
        from .label import resolved_labels
        from .scrape import iter_sites

        good = resolved_labels()
        sites = {slug: meta for slug, meta, _ in iter_sites() if good.get(slug) == 1 and not slug.startswith("neg-")}
        if not sites:
            return []
        listing = "\n".join(f"{s}: {m.get('title', '')[:80]}" for s, m in sites.items())
        try:
            picks = json.loads(self.ask([REFERENCE_PICK.format(brief=brief, sites=listing, k=k)], json_out=True))["picks"]
        except Exception:
            picks = list(sites)[:k]
        return [(s, fold_jpeg(config.RAW / s / "desktop.png")) for s in picks if s in sites][:k]

    def directions(self, brief: str, refs, n: int) -> list[dict]:
        text = self.ask([ART_DIRECTION.format(brief=brief, n=n)] + [img for _, img in refs], json_out=True)
        return json.loads(text)["directions"][:n]

    def build(self, brief: str, direction: dict) -> str:
        return extract_html(self.ask([BUILD.format(brief=brief, direction=json.dumps(direction, indent=2),
                                                    max_photos=MAX_PHOTOS)]))

    def fill_photos(self, html: str, style: str, d: Path) -> str:
        """Generate every data-photo image (in parallel) and point the <img> at the file."""
        photos_dir = config.RUNS / "_photos"
        photos_dir.mkdir(parents=True, exist_ok=True)
        tags = re.findall(r"<img\b[^>]*\bdata-photo=\"([^\"]+)\"[^>]*>", html)
        jobs = {}
        for desc in dict.fromkeys(tags):
            tag = re.search(r"<img\b[^>]*\bdata-photo=\"" + re.escape(desc) + r"\"[^>]*>", html).group(0)
            m = re.search(r"data-aspect=\"([\d:]+)\"", tag)
            aspect = m.group(1) if m and m.group(1) in ASPECTS else "4:3"
            key = hashlib.sha1(f"{style}|{desc}|{aspect}".encode()).hexdigest()[:16]
            jobs[desc] = (aspect, photos_dir / f"{key}.jpg")
        jobs = dict(list(jobs.items())[:MAX_PHOTOS + 2])
        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(lambda kv: self.photo(kv[0], kv[1][0], style, kv[1][1]), jobs.items()))

        def swap(m):
            tag = m.group(0)
            desc = re.search(r"data-photo=\"([^\"]+)\"", tag).group(1)
            aspect, path = jobs.get(desc, (None, None))
            if not path or not path.exists():
                return tag
            rel = f"../../_photos/{path.name}"  # pages live in runs/<run>/<cand>/
            tag = re.sub(r"\ssrc=\"[^\"]*\"", "", tag)
            return tag.replace("<img", f'<img src="{rel}"', 1)

        return re.sub(r"<img\b[^>]*\bdata-photo=\"[^\"]+\"[^>]*>", swap, html)

    def judge(self, brief: str, refs, shots: list[bytes]) -> dict:
        items = [JUDGE.format(brief=brief, r=len(refs), n=len(shots))] + [img for _, img in refs]
        for i, s in enumerate(shots):
            items += [f"candidate {i}:", s]
        try:
            return json.loads(self.ask(items, json_out=True, temperature=0.2))
        except Exception:
            return {"best": 0, "scores": [], "fixes": []}


def fold_jpeg(png: Path, height: int = 2400, width: int = 900) -> bytes:
    Image = need("PIL.Image", "critic")
    im = Image.open(png).convert("RGB")
    im = im.crop((0, 0, im.width, min(im.height, height)))
    im.thumbnail((width, width * height // 1440))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def _render(renderer, d: Path, html: str) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / "page.html").write_text(html)
    renderer.capture(d, url=(d / "page.html").resolve().as_uri(), mobile=True)


def run(brief: str, n: int = 3, revise: bool = True, model: str | None = None, log: bool = True) -> Path:
    from .render import Renderer

    studio = Studio(model)
    run_dir = config.RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-studio-{slugify(brief, 40)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    refs = studio.references(brief)
    print(f"references: {', '.join(s for s, _ in refs)}", flush=True)
    directions = studio.directions(brief, refs, n)
    (run_dir / "directions.json").write_text(json.dumps(directions, indent=2))
    for i, dr in enumerate(directions):
        print(f"  direction {i}: {dr.get('name')} — {dr.get('concept', '')[:110]}", flush=True)

    with ThreadPoolExecutor(max_workers=n) as ex:
        pages = list(ex.map(lambda dr: studio.build(brief, dr), directions))
    pages = [studio.fill_photos(html, dr.get("photo_style", ""), run_dir) for html, dr in zip(pages, directions)]

    shots = []
    with Renderer() as r:
        for i, html in enumerate(pages):
            _render(r, run_dir / f"c{i}", html)
            shots.append(fold_jpeg(run_dir / f"c{i}" / "desktop.png"))
        verdict = studio.judge(brief, refs, shots)
        best = int(verdict.get("best", 0)) if str(verdict.get("best", "0")).isdigit() else 0
        best = best if 0 <= best < len(pages) else 0
        print(f"judge scores: {verdict.get('scores')}  best: {best}", flush=True)
        final_html, final_dir = pages[best], run_dir / f"c{best}"

        if revise and verdict.get("fixes"):
            fixes = "\n".join(f"- {f}" for f in verdict["fixes"])
            print(f"revising with fixes:\n{fixes}", flush=True)
            raw = studio.ask([REVISE.format(fixes=fixes, html=final_html), shots[best]])
            revised = studio.fill_photos(extract_html(raw), directions[best].get("photo_style", ""), run_dir)
            if "<html" in revised.lower():
                _render(r, run_dir / "final", revised)
                final_html, final_dir = revised, run_dir / "final"

    (run_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))
    if log:
        from .util import append_jsonl

        scores = verdict.get("scores") or []
        dr = directions[best]
        append_jsonl(config.GENERATIONS, [{
            "brief": brief, "family_id": "studio",
            "family": f"Art direction: {dr.get('name', '')}. {dr.get('concept', '')}",
            # Keep the data-photo slots, not local file paths: that's what a model should learn to write.
            "html": re.sub(r'\ssrc="\.\./\.\./_photos/[^"]+"', "", final_html),
            "score": (scores[best] / 10) if best < len(scores) and isinstance(scores[best], (int, float)) else 0.0,
            "backend": "gemini-studio", "run": str(run_dir),
            "at": datetime.now().isoformat(timespec="seconds"),
        }])
    found = tells.detect(final_html, json.loads((final_dir / "styles.json").read_text()))
    print(f"tells: {[t.name for t in found] or 'none'}")
    print(f"final: {final_dir / 'page.html'}")
    return final_dir
