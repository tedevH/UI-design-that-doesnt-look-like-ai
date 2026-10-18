"""Build a fine-tuning set from the generate loop's best outputs."""

from __future__ import annotations

import random

from . import config, prompts
from .util import read_jsonl, write_jsonl


def build(min_score: float = 0.8, valid_frac: float = 0.1, seed: int = 0, top: float | None = None) -> dict:
    rows = list(read_jsonl(config.GENERATIONS))
    total = len(rows)
    if top:
        # Relative cut: keep the best `top` fraction, for when absolute scores are all low.
        scores = sorted((r.get("score", -1) for r in rows), reverse=True)
        min_score = scores[max(0, int(len(scores) * top) - 1)] if scores else 0.0
    best: dict[str, dict] = {}
    for row in rows:
        if row.get("score", -1) < min_score:
            continue
        key = row["brief"].strip().lower() + "|" + row.get("family_id", "")
        if key not in best or row["score"] > best[key]["score"]:
            best[key] = row

    examples = [{
        "messages": [
            # Compact system prompt: the model should learn the style, not read a rulebook.
            {"role": "system", "content": prompts.COMPACT_RULES},
            {"role": "user", "content": f"{r['family']}\n\nBrief: {r['brief']}"},
            {"role": "assistant", "content": f"```html\n{r['html']}\n```"},
        ]
    } for r in best.values()]

    if len(examples) < 2:
        raise SystemExit(f"Only {len(examples)} generations scored >= {min_score} (of {total}). "
                         "Run `notai batch` to generate more, or lower --min-score.")
    random.Random(seed).shuffle(examples)
    n_valid = max(1, int(len(examples) * valid_frac))
    write_jsonl(config.SFT / "valid.jsonl", examples[:n_valid])
    write_jsonl(config.SFT / "train.jsonl", examples[n_valid:])
    return {"generations": total, "min_score": round(min_score, 4), "kept": len(examples), "train": len(examples) - n_valid, "valid": n_valid,
            "dir": str(config.SFT)}
