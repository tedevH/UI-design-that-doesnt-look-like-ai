#!/usr/bin/env bash
# A/B test of the ui-design skill: the same briefs designed by headless Claude Code with and without the
# skill, then scored the same way (measured problems + the local director, which doesn't know which is which).
#   scripts/eval_skill.sh                  # uses the three default briefs
# Runs count against your Claude plan's usage. Results: designs/eval/<timestamp>/
set -uo pipefail
cd "$(dirname "$0")/.."
REPO="$PWD"
OUT="designs/eval/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
BRIEFS=(
  "Pediatric dental practice in Austin"
  "API monitoring tool for startups"
  "Independent bookstore and café in Portland"
)
echo "results in $OUT"

for i in "${!BRIEFS[@]}"; do
  b="${BRIEFS[$i]}"
  # Without the skill: a clean folder with no project skills, plain request.
  P="$REPO/$OUT/plain-$i"; mkdir -p "$P"
  ( cd "$P" && claude -p "Design a landing page for: $b. Write one self-contained HTML file named page.html in the current directory. Do not ask questions." \
      --permission-mode acceptEdits --allowedTools Write Read Edit > claude.log 2>&1 ) &
done
wait

for i in "${!BRIEFS[@]}"; do
  b="${BRIEFS[$i]}"
  S="$OUT/skill-$i"; mkdir -p "$S"
  # With the skill: run inside the project so .claude/skills/ui-design is available.
  claude -p "Use the ui-design skill to design a landing page for: $b. This is an automated test, so: make ONE variant only (skip the second variant and skip asking the user or recording feedback). Write it to $S/page.html, then run the skill's photos.py and check.py on it and fix every problem before finishing." \
      --permission-mode acceptEdits --allowedTools Write Read Edit Skill "Bash(python3:*)" "Bash(.claude/skills/ui-design/scripts/*)" \
      > "$S/claude.log" 2>&1
  echo "done: skill-$i"
done
echo "all pages generated in $OUT"
