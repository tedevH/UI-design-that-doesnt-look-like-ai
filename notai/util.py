"""Small shared helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Iterator


def slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"^https?://", "", text.strip().lower())
    text = re.sub(r"^www\.", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_len] or "page"


def read_list(path: Path) -> list[str]:
    """Lines of a text file, ignoring blanks and # comments."""
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def normalize_url(entry: str) -> str:
    return entry if re.match(r"^https?://", entry) else f"https://{entry}"


def read_jsonl(path: Path) -> Iterator[dict]:
    path = Path(path)
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def append_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def extract_html(text: str) -> str:
    """Pull a single HTML document out of a model response."""
    m = re.search(r"```(?:html)?\s*\n(.*?)```", text, re.S | re.I)
    if m and "<" in m.group(1):
        text = m.group(1)
    start = re.search(r"<!doctype html|<html", text, re.I)
    if start:
        text = text[start.start():]
        end = text.lower().rfind("</html>")
        if end != -1:
            text = text[: end + len("</html>")]
    return text.strip()
