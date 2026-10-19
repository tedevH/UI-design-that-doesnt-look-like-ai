#!/usr/bin/env python3
"""Self-update for the ui-design skill.

  evolve.py           print all the evidence about the user's taste and what to update
  evolve.py --commit  commit the skill's updated taste/rules to git (after you've edited them)

Evidence: family win rates (with how many times each was shown), every comment grouped by whether it was
about a winner or a loser, recurring words in comments, and the problems the checks caught in pages the
user reacted to. Only your personal taste.md changes — never the skill's own files or scripts.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from _env import PREFS, SKILL, TASTE, TASTE_DIR, bootstrap, ensure_taste

bootstrap(needs_env=False)
STOP = set("the a an and or but to of in on for it is this that too more less very really not just i like "
           "dont don't its it's be with than so make feels feel looks look bit kind".split())


def rows():
    return [json.loads(l) for l in PREFS.read_text().splitlines() if l.strip()] if PREFS.exists() else []


def report() -> int:
    rs = rows()
    if not rs:
        print("No reactions recorded yet — nothing to evolve from.")
        return 0
    picks = [r for r in rs if r.get("kind") == "pick"]
    wins, shown = Counter(), Counter()
    for r in picks:
        if r.get("chosen_family"):
            wins[r["chosen_family"]] += 1
            shown[r["chosen_family"]] += 1
        if r.get("rejected_family"):
            shown[r["rejected_family"]] += 1
    print(f"EVIDENCE from {len(rs)} reactions ({len(picks)} picks)\n")
    print("Family win rates (smoothed; low counts are weak evidence):")
    for fam, n in sorted(shown.items(), key=lambda kv: -(wins[kv[0]] + 1) / (kv[1] + 2)):
        print(f"  {fam:<18} picked {wins[fam]}/{n}  ({(wins[fam] + 1) / (n + 2):.0%})")

    print("\nComments on pages the user chose:")
    for r in picks:
        if r.get("note"):
            print(f"  + [{r.get('chosen_family')}] {r['note']}")
    print("\nComments on single pages:")
    for r in rs:
        if r.get("kind") == "comment" and r.get("note"):
            print(f"  * [{r.get('family') or 'page'}] {r['note']}")

    words = Counter(w for r in rs for w in re.findall(r"[a-z']+", (r.get("note") or "").lower()) if w not in STOP and len(w) > 2)
    if words:
        print("\nRecurring words in comments:", ", ".join(f"{w} ×{n}" for w, n in words.most_common(12) if n > 1) or "none repeated yet")

    caught = Counter()
    for r in rs:
        for key in ("chosen", "rejected", "page"):
            if r.get(key):
                chk = Path(r[key]).parent / f"{Path(r[key]).stem}-shots" / "check.json"
                if chk.exists():
                    caught.update(t["name"] for t in json.loads(chk.read_text()).get("tells", []))
    if caught:
        print("\nProblems the checks caught in these pages:", ", ".join(f"{k} ×{v}" for k, v in caught.most_common()))
        print("  (frequent ones mean a rule in rules.md needs to be stated more strongly)")

    print("""
NOW UPDATE THE TASTE FILE: {TASTE}
1. Rewrite 'Learned rules' from this evidence (merge, order by strength, drop rules later picks
   contradict; max 30).
2. Set 'Family priority' (best first; mark weak evidence as tentative).
3. Move preferences confirmed at least twice into 'House rules' — these override the skill's rules.md.
4. Run: scripts/evolve.py --commit""".format(TASTE=TASTE))
    return 0


def commit() -> int:
    ensure_taste()
    n = len(rows())
    subprocess.run(["git", "-C", str(TASTE_DIR), "add", "--", "taste.md"], check=True)
    if subprocess.run(["git", "-C", str(TASTE_DIR), "diff", "--cached", "--quiet"]).returncode == 0:
        print("nothing changed in your taste")
        return 0
    msg = f"Evolve taste from {n} reactions"
    subprocess.run(["git", "-C", str(TASTE_DIR), "commit", "-q", "-m", msg], check=True)
    print(f"saved this version of your taste ({n} reactions). Undo with: git -C {TASTE_DIR} revert HEAD")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    sys.exit(commit() if ap.parse_args().commit else report())
