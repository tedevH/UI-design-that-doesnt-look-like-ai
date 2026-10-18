"""Project paths. Everything is relative to NOTAI_HOME (default: current directory)."""

from __future__ import annotations

import os
from pathlib import Path

HOME = Path(os.environ.get("NOTAI_HOME", ".")).resolve()

DATA = HOME / "data"
RAW = DATA / "raw"
CACHE = DATA / "cache"
SITES = DATA / "sites"
LABELS = DATA / "labels.jsonl"
GENERATIONS = DATA / "generations.jsonl"
BRIEFS = DATA / "briefs.txt"
STYLEBOOK = DATA / "stylebook.json"
SFT = DATA / "sft"

MODELS = HOME / "models"
CRITIC = MODELS / "critic.joblib"
ADAPTERS = MODELS / "adapters"

RUNS = HOME / "runs"

ASSETS = Path(__file__).parent / "assets"

USER_AGENT = "notai-research-bot/0.1 (+https://github.com/tedevH/UI-design-that-doesnt-look-like-ai)"

DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_MLX_MODEL = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-5-5"
DEFAULT_GEMINI_MODEL = os.environ.get("NOTAI_GEMINI_MODEL", "gemini-2.5-pro")
DEFAULT_EMBED_MODEL = "google/siglip-base-patch16-224"


def _load_dotenv(path: Path) -> None:
    """KEY=VALUE lines from a local .env (kept out of git) fill in unset environment variables."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv(HOME / ".env")


def need(module: str, extra: str):
    """Import a heavy optional dependency or exit with an install hint."""
    import importlib

    try:
        return importlib.import_module(module)
    except ImportError:
        raise SystemExit(
            f"Missing dependency '{module}'. Install it with:  uv pip install -e '.[{extra}]'"
        ) from None
