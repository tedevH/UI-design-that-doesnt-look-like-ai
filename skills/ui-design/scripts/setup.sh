#!/usr/bin/env bash
# One-time setup for the ui-design skill (~2 minutes).
#   bash setup.sh                   # default: no generated photos (the skill draws graphics, uses your photos)
#   bash setup.sh --photos local    # optional: generated photos on this Mac (FLUX, ~10 GB, Apple Silicon)
#   bash setup.sh --photos gemini   # optional: generated photos via Gemini (~$0.03 each, GEMINI_API_KEY)
set -euo pipefail
DATA="${UI_DESIGN_DATA:-$HOME/.claude/ui-design-data}"
MODE="${2:-}"
[ "${1:-}" = "--photos" ] || MODE=""
mkdir -p "$DATA"

# The skill draws its own graphics and uses your photos; generated photos are optional and off by default.
MODE="${MODE:-none}"
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
