"""LoRA fine-tuning with mlx-lm on Apple Silicon."""

from __future__ import annotations

import subprocess
import sys

from . import config
from .config import need


def lora(model: str = config.DEFAULT_MLX_MODEL, iters: int = 600, layers: int = 16, lr: float = 1e-5,
         max_seq: int = 8192, name: str = "notai", extra: list[str] | None = None) -> str:
    need("mlx_lm", "finetune")
    if not (config.SFT / "train.jsonl").exists():
        raise SystemExit("No training data. Run `notai dataset build` first.")
    adapter = config.ADAPTERS / name
    adapter.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", model, "--train", "--data", str(config.SFT),
        "--adapter-path", str(adapter), "--iters", str(iters), "--num-layers", str(layers),
        "--learning-rate", str(lr), "--batch-size", "1", "--max-seq-length", str(max_seq),
        "--grad-checkpoint", "--mask-prompt", *(extra or []),
    ]
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"adapter saved to {adapter}\ntry it:  notai generate \"<brief>\" --backend mlx --adapter {adapter}")
    return str(adapter)


def fuse(model: str = config.DEFAULT_MLX_MODEL, name: str = "notai") -> str:
    need("mlx_lm", "finetune")
    adapter = config.ADAPTERS / name
    out = config.MODELS / f"{name}-fused"
    cmd = [sys.executable, "-m", "mlx_lm", "fuse", "--model", model, "--adapter-path", str(adapter), "--save-path", str(out)]
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"fused model at {out}  (use with --backend mlx --model {out})")
    return str(out)
