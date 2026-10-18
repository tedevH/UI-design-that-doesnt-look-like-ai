"""The local art director: a small model that never writes the page itself.

It sharpens the brief before the cloud model designs, then reviews every render (screenshot plus
measured facts from the renderer) and turns what it sees into concrete revision requests for the
cloud model. Runs on Ollama, so judging costs nothing; every critique is logged so the director can
later be fine-tuned on your own taste.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime
from pathlib import Path

from . import config, tells, tokens
from .config import need

DEFAULT_MODEL = "gemma3:4b"  # sees images; small enough to run beside everything else

BRIEF_SYSTEM = """\
You prepare design briefs for a designer. Expand the client's one-line brief into specifics a designer
needs. Be concrete and plausible; invent details where needed. Return JSON:
{"audience": "...", "tone": "three or four adjectives",
 "must_show": ["specific content the page must contain, e.g. the weekly menu with prices", "..."],
 "avoid": ["things that would feel wrong for this brand", "..."]}"""

CRITIC_SYSTEM = """\
You are a demanding art director reviewing a rendered landing page.
Brief: {brief}
Intended style: {family}

You get a screenshot of the top of the page and FACTS measured by the renderer. Facts are reliable;
trust them over your impression. Grey or empty boxes are photo slots that are filled later — ignore them.

Judge typography, hierarchy, spacing, color, composition, and whether it fits the brief and style.
Return JSON only:
{{"score": 1-10, "verdict": "accept" or "revise",
  "issues": [{{"where": "which element/section", "problem": "what is wrong", "fix": "a concrete change, with CSS values or new copy"}}]}}
List at most 5 issues, most important first. Every measured problem in FACTS must appear as an issue.
Use "accept" only if score >= 8 and FACTS list no problems."""

REVISION_REQUEST = """\
The art director reviewed the rendered page (score {score}/10) and asks for these changes:
{issues}

Apply every change, keep everything that already works and the overall art direction, and keep the
existing data-photo descriptions. Return the full revised HTML file in a ```html code block.

```html
{html}
```"""


class Director:
    def __init__(self, model: str = DEFAULT_MODEL, host: str = "http://127.0.0.1:11434"):
        self.httpx = need("httpx", "generate")
        self.model, self.host = model, host.rstrip("/")

    def _chat(self, system: str, user: str, images: list[bytes] | None = None) -> dict:
        msg = {"role": "user", "content": user}
        if images:
            msg["images"] = [base64.b64encode(i).decode() for i in images]
        for attempt in range(3):  # Ollama occasionally 500s when a model is (re)loading under memory pressure
            try:
                r = self.httpx.post(f"{self.host}/api/chat", timeout=600, json={
                    "model": self.model, "stream": False, "format": "json",
                    "messages": [{"role": "system", "content": system}, msg],
                    "options": {"temperature": 0.2, "num_ctx": 8192},
                })
            except self.httpx.ConnectError:
                raise SystemExit(f"Can't reach Ollama at {self.host}. Start it with `ollama serve`.") from None
            if r.status_code < 500 or attempt == 2:
                break
            import time

            time.sleep(5 * (attempt + 1))
        r.raise_for_status()
        text = r.json()["message"]["content"]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.S)
            return json.loads(m.group(0)) if m else {}

    def expand_brief(self, brief: str) -> dict:
        return self._chat(BRIEF_SYSTEM, f"Client brief: {brief}")

    def critique(self, brief: str, family: str, screenshot: bytes, html: str, styles: dict) -> dict:
        found = tells.detect(html, styles)
        out = self._chat(CRITIC_SYSTEM.format(brief=brief, family=family),
                         "FACTS:\n" + facts(html, styles, found) + "\n\nReview the page.", [screenshot])
        issues = [i for i in out.get("issues", []) if isinstance(i, dict) and i.get("fix")]
        # Measured problems are never dropped, even if the small model forgets them.
        seen = " ".join(json.dumps(i).lower() for i in issues)
        for t in found:
            if t.severity >= 2 and t.name.replace("_", " ") not in seen:
                issues.append({"where": "page", "problem": f"{t.name}: {t.evidence}", "fix": FIXES.get(t.name, "remove it")})
        try:
            score = max(1, min(10, int(out.get("score", 5))))
        except (TypeError, ValueError):
            score = 5
        hard = any(t.severity >= 2 for t in found)
        verdict = "accept" if score >= 8 and not hard and out.get("verdict") == "accept" else "revise"
        return {"score": score, "verdict": verdict, "issues": issues[:6], "tells": [t.name for t in found]}

    def revision_request(self, review: dict, html: str) -> str:
        lines = "\n".join(f"- {i.get('where', '')}: {i.get('problem', '')} → {i.get('fix', '')}" for i in review["issues"])
        return REVISION_REQUEST.format(score=review["score"], issues=lines, html=html)


FIXES = {
    "text_overlap": "give every positioned element space of its own: remove negative margins/absolute offsets that make text collide, add top padding under fixed headers",
    "chunky_type": "switch display type to the style family's face at weight 400–600; no extended or ultra-black fonts",
    "telemetry_gimmick": "remove coordinates, status readouts, serial codes and monospace label clutter",
    "big_radius_everywhere": "use one small radius (0–8px) consistently",
    "glassmorphism": "replace blurred translucent panels with solid surfaces",
    "purple_gradient": "remove gradients; use flat palette colors",
    "gradient_text": "make headlines a solid color",
    "emoji_icons": "remove emoji; use typography or simple line icons",
    "cliche_copy": "rewrite with specific, concrete language",
    "generic_type_only": "use the style family's typefaces instead of a generic sans",
}


def facts(html: str, styles: dict, found) -> str:
    s = tokens.summary(styles)
    f = tokens.features(styles)
    lines = [
        f"- fonts in use: {', '.join(s['fonts']) or 'unknown'}",
        f"- type sizes (px): {s['type_sizes']}; largest/body ratio {s['type_scale']}",
        f"- main colors: text {s['text_colors']}, backgrounds {s['bg_colors']}",
        f"- page height: {round((styles.get('docHeight') or 0) / 900, 1)} screens; ~{round(f['words_per_screen'])} words per screen",
        f"- overlapping text boxes: {styles.get('overlaps', 0)}",
    ]
    if found:
        lines.append("- measured problems: " + "; ".join(f"{t.name} ({t.evidence})" for t in found))
    else:
        lines.append("- measured problems: none")
    return "\n".join(lines)


def log_review(run_dir: Path, round_: int, review: dict) -> None:
    from .util import append_jsonl

    append_jsonl(config.DATA / "reviews.jsonl", [{
        "run": str(run_dir), "round": round_, **review, "at": datetime.now().isoformat(timespec="seconds"),
    }])
