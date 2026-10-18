"""Build a fine-tuning set from the generate loop's best outputs."""

from __future__ import annotations

import random

from . import config, prompts
from .util import read_jsonl, write_jsonl


def build(min_score: float = 0.8, valid_frac: float = 0.1, seed: int = 0) -> dict:
    best: dict[str, dict] = {}
    total = 0
    for row in read_jsonl(config.GENERATIONS):
        total += 1
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
    return {"generations": total, "kept": len(examples), "train": len(examples) - n_valid, "valid": n_valid,
            "dir": str(config.SFT)}
