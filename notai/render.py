"""Headless Chromium rendering shared by scraping and generation."""

from __future__ import annotations

import json
from pathlib import Path

from . import config

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
MAX_HEIGHT = 6000


class Renderer:
    """Keeps one browser open across many captures. Use as a context manager."""

    def __init__(self, timeout_ms: int = 30000):
        self.timeout_ms = timeout_ms
        self._extract_js = (config.ASSETS / "extract.js").read_text()

    def __enter__(self):
        sync_api = config.need("playwright.sync_api", "scrape")
        self._pw = sync_api.sync_playwright().start()
        try:
            self.browser = self._pw.chromium.launch()
        except Exception as e:  # browsers not downloaded yet
            self._pw.stop()
            raise SystemExit(f"{e}\n\nRun once:  playwright install chromium") from None
        return self

    def __exit__(self, *exc):
        self.browser.close()
        self._pw.stop()

    def _page(self, viewport: dict, mobile: bool):
        ctx = self.browser.new_context(
            viewport=viewport,
            user_agent=None if mobile else config.USER_AGENT,
            is_mobile=mobile,
            has_touch=mobile,
            device_scale_factor=1,
        )
        page = ctx.new_page()
        page.set_default_timeout(self.timeout_ms)
        return ctx, page

    def _load(self, page, url: str | None, html: str | None) -> None:
        if html is not None:
            page.set_content(html, wait_until="load")
        else:
            page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass  # long-polling sites never go idle; what's loaded is enough
        # Scroll through once so lazy images and scroll-triggered sections appear.
        page.evaluate(
            """async () => {
                const step = window.innerHeight * 0.8;
                const max = Math.min(document.documentElement.scrollHeight, 6000);
                for (let y = 0; y < max; y += step) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
                window.scrollTo(0, 0);
                await new Promise(r => setTimeout(r, 300));
            }"""
        )

    def _shot(self, page, path: Path, viewport: dict) -> None:
        height = page.evaluate("() => document.documentElement.scrollHeight")
        h = max(viewport["height"], min(int(height or 0), MAX_HEIGHT))
        page.screenshot(path=str(path), full_page=True, clip={"x": 0, "y": 0, "width": viewport["width"], "height": h})

    def capture(self, out_dir: Path, *, url: str | None = None, html: str | None = None, mobile: bool = True) -> dict:
        """Screenshot desktop (and mobile) into out_dir and return extracted styles."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        ctx, page = self._page(DESKTOP, mobile=False)
        try:
            self._load(page, url, html)
            styles = page.evaluate(self._extract_js)
            self._shot(page, out_dir / "desktop.png", DESKTOP)
        finally:
            ctx.close()

        if mobile:
            ctx, page = self._page(MOBILE, mobile=True)
            try:
                self._load(page, url, html)
                self._shot(page, out_dir / "mobile.png", MOBILE)
            finally:
                ctx.close()

        (out_dir / "styles.json").write_text(json.dumps(styles))
        return styles
