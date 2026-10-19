#!/usr/bin/env bash
# One-time setup for the ui-design skill (~2 minutes, plus the photo model if you pick local photos).
#   bash setup.sh                 # asks which photo mode you want
#   bash setup.sh --photos none   # local | gemini | none
set -euo pipefail
DATA="${UI_DESIGN_DATA:-$HOME/.claude/ui-design-data}"
MODE="${2:-}"
[ "${1:-}" = "--photos" ] || MODE=""
mkdir -p "$DATA"

if [ -z "$MODE" ]; then
  echo "How should the skill make photos for pages?"
  echo "  local  - FLUX on this Mac: free, ~30-40 s per photo, ~10 GB download (Apple Silicon only)"
  echo "  gemini - Google's image model: ~10 s and ~\$0.03 per photo, needs GEMINI_API_KEY"
  echo "  none   - leave labeled photo slots in the page"
  read -r -p "photos [none]: " MODE
  MODE="${MODE:-none}"
fi
case "$MODE" in local|gemini|none) ;; *) echo "unknown photo mode: $MODE"; exit 1 ;; esac

echo "== Python environment in $DATA/venv"
if command -v uv >/dev/null 2>&1; then
  uv venv -q --python 3.12 "$DATA/venv"
  PIP=(uv pip install -q --python "$DATA/venv/bin/python")
else
  python3 -m venv "$DATA/venv"
  PIP=("$DATA/venv/bin/pip" install -q)
fi
"${PIP[@]}" playwright "pillow<13"
"$DATA/venv/bin/python" -m playwright install chromium >/dev/null

if [ "$MODE" = "local" ]; then
  echo "== Local photo model (FLUX.1-schnell, 4-bit, ~10 GB)"
  "${PIP[@]}" mflux "pillow<13" huggingface_hub
  "$DATA/venv/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('madroid/flux.1-schnell-mflux-4bit')"
elif [ "$MODE" = "gemini" ]; then
  "${PIP[@]}" google-genai
  [ -n "${GEMINI_API_KEY:-}" ] || echo "Note: set GEMINI_API_KEY in your shell profile (free key: https://aistudio.google.com/apikey)."
fi

printf '{"photos": "%s"}\n' "$MODE" > "$DATA/config.json"
echo "== Done. Photo mode: $MODE (change it any time by re-running this script)."
