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

# USD, Standard paid tier, from ai.google.dev/gemini-api/docs/pricing (Oct 2026). (input/M, output incl. thinking/M)
TEXT_PRICES = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
}
IMAGE_PRICES = {"gemini-3.1-flash-lite-image": 0.0336, "gemini-3.1-flash-image": 0.067, "local": 0.0}

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
- Photography is essential. Never link images from the web. Use <img data-photo="detailed description of one photograph" data-aspect="16:9" alt="...">
  for every photo (aspects: 1:1, 3:4, 4:3, 4:5, 3:2, 16:9, 21:9, 9:16). Real photos will be generated from
  your descriptions in the art direction's photo style, so describe subject, framing and light precisely.
  Use {min_photos}–{max_photos} photos and make them big: full-bleed heroes, split screens, asymmetric grids, overlaps.
  Never draw placeholder boxes, ovals or empty frames. Use object-fit: cover.
- Graphics: where the style or brand suits illustration (playful, expressive, product, diagrams, maps,
  patterns, icons), draw custom graphics as inline SVG in the palette — simple, confident shapes. Keep each
  SVG under ~60 lines and never repeat long path data.
- Implement every section from the art direction with its own composition. Use color the way the art
  direction says (large color fields where it calls for them, restraint where it doesn't).
- Typography follows the art direction's fonts and weights exactly. Never use ultra-heavy or extended display
  faces (Archivo Black, Unbounded, Anton, Bebas Neue, Dela Gothic One, Syne ExtraBold, Big Shoulders, Monument-
  style wides) and never font-weight 800–900 for display. Headlines are sentence case unless 1–3 words.
  Hierarchy comes from size, spacing and contrast, not from piling on weight.
- No fake telemetry or system-status decoration (coordinates, "SYS STATUS", serial numbers, sector codes,
  live counters, monospace label clutter) unless the product is literally an engineering tool.
- Fit: every word must stay fully visible at 1440px and at 390px. Size display type with clamp() and
  viewport units sized to the longest word, allow wrapping, and never let text overflow or be clipped.
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


FAMILY_DIRECTION = """\
You are the creative director at a top design studio. Brief: {brief}

Write one art direction for EACH of these style families, in this order. Commit fully to each family's
look and typography; the attached screenshots show one reference site per family, in the same order.
{families}

Then pick the direction that fits this brand best.

Return JSON:
{{"directions": [{{
  "family": "family id",
  "name": "...",
  "concept": "one or two sentences: the idea that makes this brand memorable",
  "palette": [{{"hex": "#...", "role": "..."}}],
  "type": {{"display": "Google Font family", "display_weight": 400, "text": "Google Font family", "notes": "sizes, case, tracking"}},
  "photo_style": "lens, light, color grade, subject matter — consistent across all photos",
  "sections": [{{"name": "...", "content": "what it says/shows, concretely", "layout": "composition"}}],
  "signature_detail": "one memorable design move"
}}], "best": index}}
Use 3–6 palette colors and 6–8 sections, each composed differently."""


class BudgetExceeded(RuntimeError):
    pass


class QuotaExhausted(RuntimeError):
    pass


class Studio:
    def __init__(self, model: str | None = None, image_model: str = "gemini-3.1-flash-image",
                 thinking: str | None = None):
        from .backends import Gemini

        g = Gemini(model or config.DEFAULT_GEMINI_MODEL)
        self.client, self.types, self.model = g.client, g.types, g.model
        self.image_model = image_model
        self.thinking = thinking
        self.usage = {"input": 0, "output": 0, "images": 0, "calls": 0}
        self.budget: float | None = None  # USD; checked before every call
        self.spent_before = 0.0  # spend from earlier runs in the same batch

    def _guard(self, next_cost: float) -> None:
        if self.budget is None:
            return
        so_far = self.spent_before + (self.cost() or 0.0)
        if so_far + next_cost > self.budget:
            raise BudgetExceeded(f"stopping: ${so_far:.3f} spent, next call could pass the ${self.budget:.2f} limit")

    @staticmethod
    def _with_retry(call, tries: int = 6):
        """Free-tier keys hit per-minute limits (429) and the API has transient 5xx: wait and retry."""
        import time

        for attempt in range(tries):
            try:
                return call()
            except Exception as e:
                code = getattr(e, "code", None) or getattr(e, "status_code", None)
                if "PerDay" in str(e):  # daily free quota used up: waiting won't help until the reset
                    raise QuotaExhausted("daily free quota used up for this model") from e
                if code not in (429, 500, 502, 503, 504) or attempt == tries - 1:
                    raise
                m = re.search(r"retry in ([\d.]+)s", str(e), re.I)
                wait = float(m.group(1)) + 1 if m else min(120, 10 * 2 ** attempt)
                print(f"    rate limited ({code}); waiting {wait:.0f}s", flush=True)
                time.sleep(wait)

    def cost(self) -> float | None:
        """Measured cost in USD from token counts, or None if a model's price is unknown."""
        tp, ip = TEXT_PRICES.get(self.model), IMAGE_PRICES.get(self.image_model)
        if not tp or (self.usage["images"] and ip is None):
            return None
        return (self.usage["input"] * tp[0] + self.usage["output"] * tp[1]) / 1e6 + self.usage["images"] * (ip or 0)

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
        tp = TEXT_PRICES.get(self.model, (2.0, 12.0))
        self._guard(30000 * tp[1] / 1e6)  # worst case for one call: ~30k output tokens
        cfg = self.types.GenerateContentConfig(
            temperature=temperature, max_output_tokens=65536,
            response_mime_type="application/json" if json_out else None,
            thinking_config=self.types.ThinkingConfig(thinking_level=self.thinking) if self.thinking else None)
        r = self._with_retry(lambda: self.client.models.generate_content(
            model=self.model, contents=self._parts(items), config=cfg))
        u = r.usage_metadata
        if u:
            self.usage["input"] += u.prompt_token_count or 0
            self.usage["output"] += (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
        self.usage["calls"] += 1
        return r.text or ""

    def photo(self, prompt: str, aspect: str, style: str, out: Path) -> bool:
        if out.exists():
            return True
        self._guard(IMAGE_PRICES.get(self.image_model, 0.07))
        if self.image_model == "local":  # FLUX.1-schnell on this Mac: free
            from . import localimage

            try:
                localimage.generate(f"{prompt}. Style: {style}. Photograph, no text, no watermark.", aspect, out)
                self.usage["images"] += 1
                return True
            except Exception as e:
                print(f"    local photo failed ({aspect}): {str(e)[:160]}")
                return False
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
                    self.usage["images"] += 1
                    return True
        except BudgetExceeded:
            raise
        except Exception as e:
            print(f"    photo failed ({aspect}): {str(e)[:120]}")
        return False

    # ---- pipeline pieces ----

    def references(self, brief: str, k: int = 3, width: int = 900) -> list[tuple[str, bytes]]:
        from .label import resolved_labels
        from .scrape import iter_sites

        good = resolved_labels()
        sites = {slug: meta for slug, meta, _ in iter_sites() if good.get(slug) == 1 and not slug.startswith("neg-")}
        if not sites:
            return []
        listing = "\n".join(f"{s}: {m.get('title', '')[:80]}" for s, m in sites.items())
        try:
            picks = parse_json(self.ask([REFERENCE_PICK.format(brief=brief, sites=listing, k=k)], json_out=True))["picks"]
        except Exception:
            picks = list(sites)[:k]
        return [(s, fold_jpeg(config.RAW / s / "desktop.png", width=width)) for s in picks if s in sites][:k]

    def directions(self, brief: str, refs, n: int) -> list[dict]:
        text = self.ask([ART_DIRECTION.format(brief=brief, n=n)] + [img for _, img in refs], json_out=True)
        return parse_json(text)["directions"][:n]

    def build(self, brief: str, direction: dict, max_photos: int = MAX_PHOTOS) -> str:
        return extract_html(self.ask([BUILD.format(brief=brief, direction=json.dumps(direction, indent=2),
                                                    min_photos=min(4, max_photos), max_photos=max_photos)]))

    def fill_photos(self, html: str, style: str, d: Path, limit: int = MAX_PHOTOS) -> str:
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
        jobs = dict(list(jobs.items())[:limit])
        with ThreadPoolExecutor(max_workers=1 if self.image_model == "local" else 4) as ex:
            list(ex.map(lambda kv: self.photo(kv[0], kv[1][0], style, kv[1][1]), jobs.items()))

        made = [p for _, p in jobs.values() if p.exists()]
        spare = iter(made * 4)

        def swap(m):
            tag = m.group(0)
            desc = re.search(r"data-photo=\"([^\"]+)\"", tag).group(1)
            aspect, path = jobs.get(desc, (None, None))
            if not path or not path.exists():
                # Over the photo budget (or a failed photo): reuse one we have rather than show a broken image.
                path = next(spare, None)
                if path is None:
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
            return parse_json(self.ask(items, json_out=True, temperature=0.2))
        except Exception:
            return {"best": 0, "scores": [], "fixes": []}


def own_photos_only(html: str) -> str:
    """Turn hotlinked web images (e.g. random stock URLs) into data-photo slots described by their alt text,
    so every photo on a page is one we generate for it, never an unrelated image off the internet."""
    def swap(m):
        tag = m.group(0)
        if "data-photo=" in tag:
            return tag
        if not re.search(r"\ssrc=\"https?://", tag):
            return tag
        alt = re.search(r"\salt=\"([^\"]*)\"", tag)
        desc = (alt.group(1) if alt and alt.group(1).strip() else "photograph that fits this section").replace('"', "'")
        tag = re.sub(r"\ssrc=\"[^\"]*\"", "", tag)
        return tag.replace("<img", f'<img data-photo="{desc}" data-aspect="4:3"', 1)

    return re.sub(r"<img\b[^>]*>", swap, html)


def parse_json(text: str):
    """First JSON value in a model response; tolerates code fences and trailing text."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1] or [0])
    return json.JSONDecoder().raw_decode(text[start:])[0]


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


def run_cheap(brief: str, model: str = "gemini-3.8-flash", image_model: str = "gemini-3.1-flash-lite-image",
              photos: int = 4, polish: bool = False, log: bool = True,
              budget: float | None = None, spent_before: float = 0.0,
              director_model: str | None = None, rounds: int = 2) -> tuple[Path, float]:
    """One page per brief: plan three directions in text, build only the strongest, photos for that page only.

    photos=0 is text-only (for training data): the page keeps its data-photo slots and no images are made.
    director_model (an Ollama vision model, e.g. gemma3:4b) turns on the local art director: it expands the
    brief, reviews each render, and sends up to `rounds` revision requests to the cloud model.
    Returns (final dir, measured USD for this run)."""
    import random
    from collections import Counter

    from . import families as fam
    from .render import Renderer
    from .util import read_jsonl

    studio = Studio(model, image_model=image_model, thinking="medium")
    studio.budget, studio.spent_before = budget, spent_before
    run_dir = config.RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-cheap-{slugify(brief, 40)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    director = None
    full_brief = brief
    if director_model:
        from .director import Director, log_review

        director = Director(director_model)
        spec = director.expand_brief(brief)
        (run_dir / "brief.json").write_text(json.dumps(spec, indent=2))
        extra = []
        if spec.get("audience"):
            extra.append(f"Audience: {spec['audience']}")
        if spec.get("tone"):
            extra.append(f"Tone: {spec['tone']}")
        if spec.get("must_show"):
            extra.append("Must show: " + "; ".join(map(str, spec["must_show"][:6])))
        if spec.get("avoid"):
            extra.append("Avoid: " + "; ".join(map(str, spec["avoid"][:5])))
        full_brief = brief + ("\n" + "\n".join(extra) if extra else "")
        print(f"director brief: {' | '.join(extra)[:220]}", flush=True)

    # Offer the three least-used families so a batch spreads across aesthetics; the model picks the fit.
    usage = Counter(r.get("family_id") for r in read_jsonl(config.GENERATIONS) if r.get("backend") == "gemini-studio")
    cands = fam.candidates(usage, k=3, seed=hash(brief) & 0xFFFF)
    from . import notes as notes_mod

    refs, family_notes = [], {}
    for f in cands:  # one reference screenshot per family, chosen locally (no model call)
        strong = notes_mod.for_family(f["id"], min_quality=7, k=3)
        family_notes[f["id"]] = strong
        have = [n["slug"] for n in strong if (config.RAW / n["slug"] / "desktop.png").exists()]
        have = have[:1] or [r for r in f["refs"] if (config.RAW / r / "desktop.png").exists()]
        if have:
            slug = random.Random(brief).choice(have)
            refs.append((slug, fold_jpeg(config.RAW / slug / "desktop.png", width=640)))
    print(f"families offered: {', '.join(f['id'] for f in cands)}  refs: {', '.join(s for s, _ in refs)}", flush=True)
    def family_entry(i, f):
        entry = f"{i}. [{f['id']}] {fam.describe(f)}"
        if family_notes.get(f["id"]):
            entry += "\n   Notes on strong real sites in this family (learn the principles, don't copy):\n" + \
                "\n".join("   " + notes_mod.as_text(n).replace("\n", "\n   ") for n in family_notes[f["id"]])
        return entry

    listing = "\n".join(family_entry(i, f) for i, f in enumerate(cands))
    plan = parse_json(studio.ask([FAMILY_DIRECTION.format(brief=full_brief, families=listing)] + [img for _, img in refs],
                                 json_out=True))
    directions = plan["directions"]
    pick = plan.get("best", 0)
    pick = pick if isinstance(pick, int) and 0 <= pick < len(directions) else 0
    direction = directions[pick]
    family_id = direction.get("family") if direction.get("family") in fam.BY_ID else cands[min(pick, len(cands) - 1)]["id"]
    family_text = fam.describe(fam.BY_ID[family_id])
    (run_dir / "directions.json").write_text(json.dumps(plan, indent=2))
    print(f"family: {family_id}  direction: {direction.get('name')} — {direction.get('concept', '')[:100]}", flush=True)

    def photos_for(raw: str) -> str:
        return studio.fill_photos(raw, direction.get("photo_style", ""), run_dir, limit=photos) if photos else raw

    raw_html = own_photos_only(studio.build(full_brief, direction, max_photos=photos or 4))
    versions = []  # (dir, raw_html, html, review)
    with Renderer() as r:
        d = run_dir / "page"
        html = photos_for(raw_html)
        _render(r, d, html)
        versions.append([d, raw_html, html, None])

        if director:
            for k in range(rounds + 1):
                d, raw, html, _ = versions[-1]
                styles = json.loads((d / "styles.json").read_text())
                try:
                    review = director.critique(full_brief, family_text, fold_jpeg(d / "desktop.png", width=768), raw, styles)
                except Exception as e:  # a failed critique should never lose the page
                    print(f"  director failed ({str(e)[:100]}); keeping the page as is", flush=True)
                    break
                versions[-1][3] = review
                (d / "review.json").write_text(json.dumps(review, indent=2))
                log_review(run_dir, k, review)
                print(f"  director round {k}: score {review['score']}/10, {review['verdict']}, "
                      f"{len(review['issues'])} issues {review['tells'] or ''}", flush=True)
                for it in review["issues"][:4]:
                    print(f"    - {it.get('where', '')}: {str(it.get('fix', ''))[:110]}", flush=True)
                if review["verdict"] == "accept" or k == rounds:
                    break
                revised = own_photos_only(extract_html(studio.ask([director.revision_request(review, raw)])))
                if "<html" not in revised.lower():
                    break
                d = run_dir / f"rev{k + 1}"
                html = photos_for(revised)
                _render(r, d, html)
                versions.append([d, revised, html, None])
        elif polish:
            shot = fold_jpeg(d / "desktop.png", width=640)
            verdict = studio.judge(brief, refs, [shot])
            if verdict.get("fixes"):
                fixes = "\n".join(f"- {f}" for f in verdict["fixes"])
                revised = extract_html(studio.ask([REVISE.format(fixes=fixes, html=raw_html), shot]))
                if "<html" in revised.lower():
                    d = run_dir / "polished"
                    html = photos_for(revised)
                    _render(r, d, html)
                    versions.append([d, revised, html, None])

    # Best version: fewest measured problems first (reliable), then the director's score (noisier).
    def rank(v):
        rv = v[3] or {}
        return (-len(rv.get("tells", [])), rv.get("score", 0))
    final_dir, raw_html, html, review = max(versions, key=rank) if director else versions[-1]

    cost = studio.cost()
    cost_usd = round(cost, 4) if cost is not None else None
    (run_dir / "cost.json").write_text(json.dumps({**studio.usage, "usd": cost_usd, "model": model,
                                                   "image_model": image_model}, indent=2))
    found = tells.detect(html, json.loads((final_dir / "styles.json").read_text()))
    print(f"tells: {[t.name for t in found] or 'none'}")
    print(f"cost: ${cost_usd}  ({studio.usage['input']} in / {studio.usage['output']} out tokens, "
          f"{studio.usage['images']} images, {studio.usage['calls']} calls)")
    print(f"final: {final_dir / 'page.html'}")
    if log:
        from .util import append_jsonl

        append_jsonl(config.GENERATIONS, [{
            "brief": brief, "family_id": family_id,
            "family": f"Style: {fam.BY_ID[family_id]['name']}. {direction.get('name', '')}: {direction.get('concept', '')}",
            "html": raw_html, "score": (review or {}).get("score", 8) / 10, "backend": "gemini-studio",
            "run": str(run_dir), "tells": [t.name for t in found], "usd": cost_usd,
            "at": datetime.now().isoformat(timespec="seconds"),
        }])
    return final_dir, cost_usd or 0.0
