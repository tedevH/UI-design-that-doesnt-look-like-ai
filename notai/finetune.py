"""LoRA fine-tuning with mlx-lm on Apple Silicon."""

from __future__ import annotations

import subprocess
import sys

from . import config
from .config import need


def lora(model: str = config.DEFAULT_MLX_MODEL, iters: int = 600, layers: int = 16, lr: float = 5e-6,
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
        "--grad-checkpoint", "--mask-prompt", "--save-every", "20", "--steps-per-eval", "20", *(extra or []),
    ]
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)
    _fall_back_if_nan(adapter)
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


def _finite(path) -> bool:
    import mlx.core as mx

    return all(not mx.isnan(v).any().item() for v in mx.load(str(path)).values())


def _fall_back_if_nan(adapter) -> None:
    """Small datasets can make LoRA training diverge late. If the final weights are NaN,
    use the newest checkpoint that is still finite."""
    import shutil

    final = adapter / "adapters.safetensors"
    if _finite(final):
        return
    for ckpt in sorted(adapter.glob("*_adapters.safetensors"), reverse=True):
        if _finite(ckpt):
            shutil.copy(ckpt, final)
            print(f"final weights were NaN; using checkpoint {ckpt.name}")
            return
    raise SystemExit("training diverged (NaN) and no finite checkpoint exists; lower --lr or --iters")
