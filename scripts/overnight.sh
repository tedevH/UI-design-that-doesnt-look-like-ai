#!/usr/bin/env bash
# Unattended run: generate with a local model for HOURS, keep the top-scoring pages,
# LoRA fine-tune a local model on them, then generate one test page with the adapter.
#   HOURS=7 scripts/overnight.sh
set -uo pipefail
cd "$(dirname "$0")/.."

HOURS=${HOURS:-7}
GEN_MODEL=${GEN_MODEL:-qwen2.5-coder:14b}
TOP=${TOP:-0.5}
NOTAI=${NOTAI:-.venv/bin/notai}
LOG=${LOG:-runs/overnight.log}
mkdir -p runs
exec > >(tee -a "$LOG") 2>&1

echo "== $(date) start: ${HOURS}h of generation with ${GEN_MODEL}"
ollama serve >/dev/null 2>&1 &
OLLAMA_PID=$!
sleep 5

"$NOTAI" batch --model "$GEN_MODEL" -n 2 --rounds 2 --target 0.6 --hours "$HOURS"

# Free the GPU memory Ollama holds before training (24 GB is not enough for both).
kill "$OLLAMA_PID" 2>/dev/null; sleep 5

echo "== $(date) building dataset (top ${TOP})"
"$NOTAI" dataset build --top "$TOP" || { echo "dataset build failed"; exit 1; }

TRAIN=$(wc -l < data/sft/train.jsonl | tr -d ' ')
ITERS=$(( TRAIN * 3 > 100 ? TRAIN * 3 : 100 ))   # ~3 epochs
echo "== $(date) fine-tuning on ${TRAIN} examples for ${ITERS} iters"
"$NOTAI" finetune --iters "$ITERS" || { echo "fine-tune failed"; exit 1; }

echo "== $(date) test generation with the adapter"
"$NOTAI" generate "Mail-in analog film lab in Edinburgh offering developing and scanning" \
  --backend mlx --adapter models/adapters/notai -n 2 --rounds 1 --family f00

echo "== $(date) done"
