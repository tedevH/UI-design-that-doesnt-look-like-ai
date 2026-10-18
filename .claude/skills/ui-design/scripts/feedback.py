#!/usr/bin/env python3
"""Record the user's reaction to a design and refresh the taste statistics.

A pick between two variants:
  feedback.py --brief "..." --chosen a.html --rejected b.html \
              --chosen-family warm-crafted --rejected-family swiss-minimal --note "user's words"
A comment on one page:
  feedback.py --brief "..." --page a.html --note "the headline font is too thin"

Logs to taste/preferences.jsonl (kept in git so your taste is backed up), refreshes the statistics
block in references/taste.md, and adds picks as pairwise labels so the notai critic learns them too.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from _notai import SKILL, bootstrap

bootstrap()

PREFS = SKILL / "taste" / "preferences.jsonl"
TASTE = SKILL / "references" / "taste.md"
START, END = "<!-- stats:start -->", "<!-- stats:end -->"


def _shots_to_raw(page: Path) -> str | None:
    """Copy a checked page's screenshots into the notai dataset so the critic can use the pair."""
    from notai import config

    shots = page.parent / f"{page.stem}-shots"
    if not (shots / "desktop.png").exists():
        return None
    slug = "pref-" + hashlib.sha1(str(page.resolve()).encode()).hexdigest()[:10]
    d = config.RAW / slug
    d.mkdir(parents=True, exist_ok=True)
    for name in ("desktop.png", "mobile.png", "styles.json"):
        if (shots / name).exists():
            shutil.copy(shots / name, d / name)
    (d / "meta.json").write_text(json.dumps({"slug": slug, "url": str(page), "source": "preference"}, indent=2))
    return slug


def refresh_stats() -> None:
    rows = [json.loads(l) for l in PREFS.read_text().splitlines() if l.strip()] if PREFS.exists() else []
    picks = [r for r in rows if r.get("kind") == "pick"]
    wins, seen = Counter(), Counter()
    for r in picks:
        if r.get("chosen_family"):
            wins[r["chosen_family"]] += 1
            seen[r["chosen_family"]] += 1
        if r.get("rejected_family"):
            seen[r["rejected_family"]] += 1
    lines = [f"Updated {datetime.now():%Y-%m-%d %H:%M} from {len(rows)} reactions ({len(picks)} picks).", ""]
    if seen:
        lines += ["| Style family | Picked | Shown | Win rate |", "|---|---|---|---|"]
        for fam, n in sorted(seen.items(), key=lambda kv: (-(wins[kv[0]] + 1) / (kv[1] + 2), -kv[1])):
            lines.append(f"| {fam} | {wins[fam]} | {n} | {(wins[fam] + 1) / (n + 2):.0%} |")
        lines.append("")
        lines.append("Win rate is smoothed (a family needs several picks before it dominates).")
    else:
        lines.append("No picks yet — show two different families and ask.")
    notes = [r for r in rows if r.get("note")][-12:]
    if notes:
        lines += ["", "Recent comments (newest last):"]
        lines += [f"- {r['at'][:10]} [{r.get('chosen_family') or r.get('family') or 'page'}] \"{r['note']}\"" for r in notes]
    block = "\n".join(lines)
    text = TASTE.read_text()
    text = re.sub(re.escape(START) + r".*?" + re.escape(END), f"{START}\n{block}\n{END}", text, flags=re.S)
    TASTE.write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", default="")
    ap.add_argument("--chosen")
    ap.add_argument("--rejected")
    ap.add_argument("--chosen-family")
    ap.add_argument("--rejected-family")
    ap.add_argument("--page")
    ap.add_argument("--family")
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    row = {"at": datetime.now().isoformat(timespec="seconds"), "brief": a.brief, "note": a.note.strip()}
    if a.chosen and a.rejected:
        row.update(kind="pick", chosen=a.chosen, rejected=a.rejected,
                   chosen_family=a.chosen_family, rejected_family=a.rejected_family)
        ca, cb = _shots_to_raw(Path(a.chosen)), _shots_to_raw(Path(a.rejected))
        if ca and cb:
            from notai import config
            from notai.util import append_jsonl

            append_jsonl(config.LABELS, [{"kind": "pair", "a": ca, "b": cb, "winner": "a", "by": "user-via-skill",
                                          "at": row["at"]}])
    elif a.page or a.note:
        row.update(kind="comment", page=a.page, family=a.family)
    else:
        print(__doc__)
        return 2
    PREFS.parent.mkdir(parents=True, exist_ok=True)
    with PREFS.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    refresh_stats()
    print(f"recorded {row['kind']}; taste statistics updated in {TASTE}")
    print("Now update the 'Learned rules' section of references/taste.md from the user's words.")
    total = sum(1 for l in PREFS.read_text().splitlines() if l.strip())
    if total % 5 == 0:
        print(f"EVOLVE: {total} reactions recorded — run scripts/evolve.py and update the skill's taste and rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
