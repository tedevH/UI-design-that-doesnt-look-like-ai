"""Shared setup for the skill's scripts: where data lives, and running inside the skill's own Python env.

Everything personal or heavy lives outside the skill folder, so updating the skill never touches it:
  ~/.claude/ui-design-data/venv     Python environment (made by setup.sh)
  ~/.claude/ui-design-data/taste/   your learned taste: taste.md + preferences.jsonl (its own git history)
  ~/.claude/ui-design-data/config.json   photo mode: local | gemini | none
Override the location with UI_DESIGN_DATA.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("UI_DESIGN_DATA", Path.home() / ".claude" / "ui-design-data"))
VENV_PY = DATA / "venv" / "bin" / "python"
TASTE_DIR = DATA / "taste"
TASTE = TASTE_DIR / "taste.md"
PREFS = TASTE_DIR / "preferences.jsonl"


def bootstrap(needs_env: bool = True) -> None:
    """Re-run under the skill's virtualenv (if set up) and make scripts/lib importable."""
    if needs_env and VENV_PY.exists() and Path(sys.executable).resolve() != VENV_PY.resolve() \
            and not os.environ.get("UI_DESIGN_REEXEC"):
        os.environ["UI_DESIGN_REEXEC"] = "1"
        os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])
    if needs_env and not VENV_PY.exists():
        sys.exit(f"First-time setup needed. Run:  bash {SKILL / 'scripts' / 'setup.sh'}")
    sys.path.insert(0, str(SKILL / "scripts"))


def config() -> dict:
    p = DATA / "config.json"
    return json.loads(p.read_text()) if p.exists() else {"photos": "none"}


def ensure_taste() -> Path:
    """Create the personal taste file from the template on first use (with its own git history)."""
    if not TASTE.exists():
        TASTE_DIR.mkdir(parents=True, exist_ok=True)
        TASTE.write_text((SKILL / "references" / "taste-template.md").read_text())
        import subprocess

        if subprocess.run(["git", "init", "-q", str(TASTE_DIR)], capture_output=True).returncode == 0:
            subprocess.run(["git", "-C", str(TASTE_DIR), "add", "taste.md"], capture_output=True)
            subprocess.run(["git", "-C", str(TASTE_DIR), "commit", "-q", "-m", "Start with a blank taste"],
                           capture_output=True)
    return TASTE
