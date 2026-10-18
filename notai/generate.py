"""Generate → render → score → revise loop."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import config, prompts, stylebook, tells
from .backends import Backend
from .util import append_jsonl, extract_html, slugify

TELL_WEIGHT = 0.04


@dataclass
class Candidate:
    html: str
    dir: Path
    round: int
    index: int
    critic: float | None = None
    tells: list = field(default_factory=list)
    critique: str | None = None
    error: str | None = None

    @property
    def score(self) -> float:
        if self.error:
            return -1.0
        base = self.critic if self.critic is not None else 1.0
        return round(base - TELL_WEIGHT * tells.penalty(self.tells), 4)

    def summary(self) -> dict:
        return {"round": self.round, "index": self.index, "score": self.score, "critic": self.critic,
                "tells": [t.as_dict() for t in self.tells], "error": self.error}


def families() -> list[dict]:
    book = stylebook.load()
    return book["families"] if book else stylebook.DEFAULT_FAMILIES


def pick_family(brief: str, backend: Backend, family_id: str | None) -> dict:
    fams = families()
    if family_id and family_id != "auto":
        for f in fams:
            if f["id"] == family_id:
                return f
        raise SystemExit(f"No family '{family_id}'. Available: {', '.join(f['id'] for f in fams)}")
    answer = backend.complete("You match brands to visual style families.",
                              [{"role": "user", "content": prompts.choose_family_user(brief, fams)}],
                              temperature=0.2, max_tokens=50).strip().lower()
    for f in fams:
        if f["id"].lower() in answer:
            return f
    return random.choice(fams)


def _critique_image(png: Path) -> Path:
    """Top of the page, downscaled: what a vision model can usefully look at."""
    try:
        from PIL import Image
    except ImportError:
        return png
    img = Image.open(png).convert("RGB")
    img = img.crop((0, 0, img.width, min(img.height, 2400)))
    img.thumbnail((1024, 1706))
    out = png.with_name("critique.png")
    img.save(out)
    return out


def evaluate(c: Candidate, renderer, critic, backend: Backend, vision: bool) -> Candidate:
    c.dir.mkdir(parents=True, exist_ok=True)
    (c.dir / "page.html").write_text(c.html)
    if "<html" not in c.html.lower() and "<body" not in c.html.lower():
        c.error = "no HTML document in response"
        return c
    try:
        styles = renderer.capture(c.dir, html=c.html, mobile=True)
    except Exception as e:
        c.error = f"render failed: {str(e).splitlines()[0][:200]}"
        return c
    c.tells = tells.detect(c.html, styles)
    if critic:
        c.critic = round(critic.score_dir(c.dir), 4)
    if vision:
        c.critique = backend.critique(_critique_image(c.dir / "desktop.png"))
    (c.dir / "result.json").write_text(json.dumps({**c.summary(), "critique": c.critique}, indent=2))
    return c


def run(brief: str, backend: Backend, *, family: str | None = None, n: int = 3, rounds: int = 3,
        target: float = 0.85, vision: bool = False, critic_backend: Backend | None = None,
        log: bool = True) -> Candidate:
    from .critic import try_load
    from .render import Renderer

    critic = try_load()
    if critic is None:
        print("note: no trained critic yet; scoring with tells only (train one with `notai critic train`)")
    fam = pick_family(brief, backend, family)
    system = prompts.generation_system(fam)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = config.RUNS / f"{stamp}-{slugify(brief, 40)}"
    print(f"family: {fam['id']} — {fam.get('name', '')}\nrun dir: {run_dir}")

    best: Candidate | None = None
    history: list[dict] = []
    with Renderer() as renderer:
        for rnd in range(rounds):
            cands = []
            for i in range(n):
                t0 = time.time()
                if best is None:
                    directive = prompts.LAYOUT_DIRECTIVES[i % len(prompts.LAYOUT_DIRECTIVES)]
                    messages = [{"role": "user", "content": prompts.generation_user(brief, directive)}]
                else:
                    tell_lines = [f"{t.name}: {t.evidence}" for t in best.tells]
                    messages = [
                        {"role": "user", "content": prompts.generation_user(brief, "Keep the current layout direction.")},
                        {"role": "assistant", "content": f"```html\n{best.html}\n```"},
                        {"role": "user", "content": prompts.revision_user(best.critic, tell_lines, best.critique)},
                    ]
                raw = backend.complete(system, messages, temperature=0.9 if best is None else 0.6)
                c = Candidate(extract_html(raw), run_dir / f"r{rnd}-c{i}", rnd, i)
                evaluate(c, renderer, critic, critic_backend or backend, vision)
                print(f"  round {rnd} cand {i}: score {c.score:+.3f}  critic {c.critic}  "
                      f"tells {[t.name for t in c.tells]}  {c.error or ''} ({time.time() - t0:.0f}s)")
                cands.append(c)
                history.append(c.summary())
            round_best = max(cands, key=lambda c: c.score)
            if best is None or round_best.score > best.score:
                best = round_best
            if best.score >= target:
                break

    assert best is not None
    (run_dir / "best.html").write_text(best.html)
    (run_dir / "run.json").write_text(json.dumps({"brief": brief, "family": fam, "best": best.summary(),
                                                  "history": history}, indent=2))
    if log and not best.error:
        append_jsonl(config.GENERATIONS, [{
            "brief": brief, "family_id": fam["id"], "family": prompts.family_block(fam),
            "html": best.html, "score": best.score, "critic": best.critic,
            "tells": [t.name for t in best.tells], "backend": backend.name, "run": str(run_dir),
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }])
    print(f"best: score {best.score:+.3f} -> {run_dir / 'best.html'}")
    return best


def negatives(backend: Backend, briefs: list[str], limit: int | None = None) -> None:
    """Render deliberately lazy AI pages as vibecoded training examples."""
    from .render import Renderer

    briefs = briefs[:limit] if limit else briefs
    with Renderer() as r:
        for i, brief in enumerate(briefs, 1):
            model = getattr(backend, "model", None)
            tag = slugify(model if isinstance(model, str) else backend.name, 24)
            slug = f"neg-{tag}-{slugify(brief, 40)}"
            out = config.RAW / slug
            if (out / "meta.json").exists():
                continue
            print(f"[{i}/{len(briefs)}] {brief}")
            raw = backend.complete("You are a helpful web developer.",
                                   [{"role": "user", "content": prompts.NEGATIVE_USER.format(brief=brief)}], temperature=0.8)
            html = extract_html(raw)
            try:
                r.capture(out, html=html)
            except Exception as e:
                print(f"    render failed: {str(e).splitlines()[0][:160]}")
                continue
            (out / "page.html").write_text(html)
            (out / "meta.json").write_text(json.dumps({
                "slug": slug, "url": f"generated:{backend.name}:{tag}", "source": "vibe", "brief": brief,
                "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=2))
