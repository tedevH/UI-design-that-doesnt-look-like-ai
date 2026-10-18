"""Design notes: the local vision model studies every scraped site and writes down what it does.

Runs on Ollama (free, overnight-friendly). Each note rates the design, assigns one of the studio's
style families, and describes layout, type, color, imagery and section order in words a designer
model can use. Studio mode then gives the cloud designer the notes of several strong sites in the
chosen family, instead of one or two screenshots.
"""

from __future__ import annotations

import json

from . import config, tokens
from .families import BY_ID, FAMILIES

NOTES = config.DATA / "notes"

NOTE_SYSTEM = """\
You are a senior designer cataloguing reference websites for a design team.
You get screenshots of a site's homepage (desktop top, desktop further down, mobile top) and measured
facts. Write precise, reusable observations — what a designer could learn and apply elsewhere.

Style families (pick the closest one):
{families}

Return JSON only:
{{"family": "family id",
  "quality": 1-10 (10 = award-level craft; 5 = competent but generic corporate; be strict),
  "layout": "grid, alignment, hero composition, density",
  "typography": "faces (as seen), weights, sizes, case, tracking, pairing",
  "color": "palette and how color is used",
  "imagery": "photography/illustration/product UI and how it is framed",
  "sections": ["ordered list of homepage sections"],
  "what_makes_it_work": "the two or three decisions that make it good (or why it is generic)",
  "signature_move": "the single most distinctive idea"}}"""


def _families_text() -> str:
    return "\n".join(f"- {f['id']}: {f['name']} — {f['look']}" for f in FAMILIES)


def write_notes(model: str = "gemma3:12b", force: bool = False, limit: int | None = None) -> dict:
    from .director import Director
    from .label import human_labels
    from .scrape import iter_sites
    from .studio import fold_jpeg

    NOTES.mkdir(parents=True, exist_ok=True)
    director = Director(model)
    system = NOTE_SYSTEM.format(families=_families_text())
    done = skipped = failed = 0
    skipped_by_human = human_labels()
    for slug, meta, d in iter_sites():
        if meta.get("source") == "vibe" or slug.startswith("neg-") or skipped_by_human.get(slug) == "skip":
            continue
        out = NOTES / f"{slug}.json"
        if out.exists() and not force:
            skipped += 1
            continue
        if limit is not None and done >= limit:
            break
        try:
            from PIL import Image

            images = [fold_jpeg(d / "desktop.png", height=1400, width=768)]
            full = Image.open(d / "desktop.png")
            if full.height > 2600:  # a band from further down the page
                import io

                band = full.convert("RGB").crop((0, 1800, full.width, min(full.height, 3200)))
                band.thumbnail((768, 768))
                buf = io.BytesIO()
                band.save(buf, "JPEG", quality=85)
                images.append(buf.getvalue())
            if (d / "mobile.png").exists():
                images.append(fold_jpeg(d / "mobile.png", height=1600, width=390))
            styles = json.loads((d / "styles.json").read_text()) if (d / "styles.json").exists() else {}
            s = tokens.summary(styles)
            facts = (f"Site: {meta.get('url', slug)}\nFonts: {', '.join(s['fonts'])}; type sizes {s['type_sizes']}; "
                     f"text colors {s['text_colors']}; backgrounds {s['bg_colors']}; radius {s['radius']}px")
            note = director._chat(system, facts + "\n\nStudy the screenshots and write the note.", images)
            if note.get("family") not in BY_ID:
                note["family"] = None
            note.update({"slug": slug, "url": meta.get("url"), "source": meta.get("source"), "model": model})
            out.write_text(json.dumps(note, indent=2))
            done += 1
            print(f"  {slug:<34} {note.get('family') or '?':<16} quality {note.get('quality')}", flush=True)
        except Exception as e:
            failed += 1
            print(f"  {slug}: failed ({str(e)[:100]})", flush=True)
    return {"written": done, "skipped": skipped, "failed": failed, "dir": str(NOTES)}


def load_all() -> list[dict]:
    if not NOTES.exists():
        return []
    return [json.loads(p.read_text()) for p in sorted(NOTES.glob("*.json"))]


def for_family(family_id: str, min_quality: int = 7, k: int = 4) -> list[dict]:
    """The strongest notes in a family, best first."""
    notes = [n for n in load_all() if n.get("family") == family_id and _q(n) >= min_quality]
    return sorted(notes, key=_q, reverse=True)[:k]


def _q(n: dict) -> int:
    try:
        return int(n.get("quality") or 0)
    except (TypeError, ValueError):
        return 0


def as_text(n: dict) -> str:
    sections = " → ".join(map(str, (n.get("sections") or [])[:8]))
    return (f"[{n.get('url')}] quality {n.get('quality')}/10\n"
            f"  layout: {n.get('layout')}\n  type: {n.get('typography')}\n  color: {n.get('color')}\n"
            f"  imagery: {n.get('imagery')}\n  sections: {sections}\n"
            f"  why it works: {n.get('what_makes_it_work')}\n  signature: {n.get('signature_move')}")
