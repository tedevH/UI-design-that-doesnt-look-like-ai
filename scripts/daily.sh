#!/usr/bin/env bash
# Daily free-tier collection: spend each free Gemini model's daily quota on new training pages,
# with the local art director reviewing every page. Text only (no paid images). Safe to rerun:
# briefs already done are skipped, and each batch stops itself when the quota runs out.
#   scripts/daily.sh            # normally run by launchd at 03:30 local (just after the Pacific reset)
set -uo pipefail
cd "$(dirname "$0")/.."

NOTAI=${NOTAI:-.venv/bin/notai}
DIRECTOR=${DIRECTOR:-gemma3:12b}
MODELS=${MODELS:-"gemini-3.8-flash gemini-3-flash-preview"}
mkdir -p runs
LOG="runs/daily-$(date +%Y%m%d).log"
exec >>"$LOG" 2>&1
echo "== $(date) daily run (director: $DIRECTOR)"

STARTED_OLLAMA=""
if ! curl -s -m 3 http://127.0.0.1:11434/api/tags >/dev/null; then
  ollama serve >/dev/null 2>&1 &
  STARTED_OLLAMA=$!
  sleep 5
fi

for m in $MODELS; do
  echo "== $(date) model $m"
  "$NOTAI" studio --photos 0 --model "$m" --director "$DIRECTOR" --rounds 1 --hours 3
done

CLEAN=$(.venv/bin/python - <<'PY'
from notai import config
from notai.dataset import EXCLUDE_TELLS
from notai.util import read_jsonl
rows = [r for r in read_jsonl(config.GENERATIONS) if r.get("backend") == "gemini-studio"]
print(sum(1 for r in rows if not set(r.get("tells") or []) & EXCLUDE_TELLS))
PY
)
echo "== $(date) done. clean training pages so far: $CLEAN"
[ -n "$STARTED_OLLAMA" ] && kill "$STARTED_OLLAMA" 2>/dev/null
exit 0
