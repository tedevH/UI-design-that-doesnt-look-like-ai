"""Shared bootstrap: find the notai project this skill lives in, run inside its virtualenv."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent.parent  # <repo>/.claude/skills/ui-design
VENV_PY = REPO / ".venv" / "bin" / "python"


def bootstrap() -> None:
    """Re-exec under the project's venv if needed, and point notai at the project's data."""
    if VENV_PY.exists() and Path(sys.executable).resolve() != VENV_PY.resolve() and not os.environ.get("NOTAI_SKILL_REEXEC"):
        os.environ["NOTAI_SKILL_REEXEC"] = "1"
        os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])
    os.environ.setdefault("NOTAI_HOME", str(REPO))
    sys.path.insert(0, str(REPO))
