"""Collect screenshots and computed styles from a list of sites."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from . import config
from .util import normalize_url, read_list, slugify


def allowed_by_robots(url: str) -> bool:
    parts = urlparse(url)
    import urllib.request

    rp = urllib.robotparser.RobotFileParser()
    try:
        req = urllib.request.Request(f"{parts.scheme}://{parts.netloc}/robots.txt",
                                     headers={"User-Agent": config.USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as r:  # RobotFileParser.read() has no timeout
            rp.parse(r.read().decode("utf-8", "ignore").splitlines())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False  # same rule RobotFileParser applies: access to robots.txt denied
        return True  # missing robots.txt: no rules
    except Exception:
        return True  # unreachable robots.txt: treat as no rules
    return rp.can_fetch(config.USER_AGENT, url)


def scrape(list_path: Path, source: str, limit: int | None = None, delay: float = 2.0,
           force: bool = False, mobile: bool = True) -> None:
    from .render import Renderer

    entries = read_list(list_path)[:limit]
    done = failed = skipped = 0
    with Renderer() as r:
        for i, entry in enumerate(entries, 1):
            url = normalize_url(entry)
            slug = slugify(url)
            out = config.RAW / slug
            if (out / "meta.json").exists() and not force:
                skipped += 1
                continue
            if not allowed_by_robots(url):
                print(f"[{i}/{len(entries)}] robots.txt disallows {url}, skipping")
                skipped += 1
                continue
            print(f"[{i}/{len(entries)}] {url}")
            try:
                styles = r.capture(out, url=url, mobile=mobile)
            except Exception as e:
                print(f"    failed: {str(e).splitlines()[0][:160]}")
                failed += 1
                continue
            meta = {
                "slug": slug, "url": url, "source": source, "title": styles.get("title", ""),
                "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            (out / "meta.json").write_text(json.dumps(meta, indent=2))
            done += 1
            time.sleep(delay)
    print(f"done: {done} captured, {skipped} skipped, {failed} failed -> {config.RAW}")


def iter_sites():
    """Yield (slug, meta, dir) for every captured site."""
    if not config.RAW.exists():
        return
    for d in sorted(config.RAW.iterdir()):
        meta_path = d / "meta.json"
        if meta_path.exists() and (d / "desktop.png").exists():
            yield d.name, json.loads(meta_path.read_text()), d
