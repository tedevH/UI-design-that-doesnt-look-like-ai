"""Local labeling app: mark screenshots good / vibecoded, or pick the better of two."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import config
from .scrape import iter_sites
from .util import append_jsonl, read_jsonl


def human_labels() -> dict[str, str]:
    """Latest single label per slug ('good' | 'vibe' | 'skip'); undo rows remove it."""
    out: dict[str, str] = {}
    for row in read_jsonl(config.LABELS):
        if row.get("kind") == "single":
            out[row["slug"]] = row["label"]
        elif row.get("kind") == "undo":
            out.pop(row["slug"], None)
    return out


def pair_labels() -> list[tuple[str, str, float]]:
    """(a, b, p_a_better) for every pairwise judgment."""
    out = []
    for row in read_jsonl(config.LABELS):
        if row.get("kind") == "pair":
            p = {"a": 1.0, "b": 0.0, "tie": 0.5}[row["winner"]]
            out.append((row["a"], row["b"], p))
    return out


def resolved_labels() -> dict[str, int]:
    """slug -> 1 (good) / 0 (vibecoded). Human labels override the scrape source prior."""
    human = human_labels()
    out = {}
    for slug, meta, _ in iter_sites():
        label = human.get(slug) or meta.get("source")
        if label == "good":
            out[slug] = 1
        elif label == "vibe":
            out[slug] = 0
    return out


class Handler(BaseHTTPRequestHandler):
    mode = "single"

    def log_message(self, *args):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            body = (config.ASSETS / "label.html").read_text().replace("__MODE__", self.mode).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif url.path == "/api/next":
            self._json(self._next(parse_qs(url.query).get("mode", [self.mode])[0]))
        elif url.path.startswith("/img/"):
            _, _, slug, name = url.path.split("/", 3)
            path = (config.RAW / slug / name).resolve()
            if config.RAW.resolve() not in path.parents or not path.exists() or path.suffix != ".png":
                self.send_error(404)
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        row = json.loads(self.rfile.read(length) or b"{}")
        if row.get("kind") not in {"single", "pair", "undo"}:
            self._json({"error": "bad kind"}, 400)
            return
        row["at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        append_jsonl(config.LABELS, [row])
        self._json({"ok": True})

    def _next(self, mode: str):
        sites = list(iter_sites())
        human = human_labels()
        done = len(human)
        if not sites:
            return {"empty": True, "message": "No captured sites yet. Run `notai scrape` or `notai negatives` first."}
        if mode == "pair":
            if len(sites) < 2:
                return {"empty": True, "message": "Need at least two captured sites."}
            a, b = random.sample(sites, 2)
            return {"mode": "pair", "a": _card(a), "b": _card(b), "progress": len(pair_labels())}
        todo = [s for s in sites if s[0] not in human]
        if not todo:
            return {"empty": True, "message": f"All {done} sites labeled. Try pair mode."}
        return {"mode": "single", "site": _card(random.choice(todo)), "progress": done, "total": len(sites)}


def _card(site) -> dict:
    slug, meta, d = site
    return {"slug": slug, "url": meta.get("url", ""), "source": meta.get("source", ""),
            "has_mobile": (d / "mobile.png").exists()}


def serve(mode: str = "single", port: int = 8765) -> None:
    Handler.mode = mode
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Labeling at http://127.0.0.1:{port}  (mode: {mode}, writing {config.LABELS})  Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
