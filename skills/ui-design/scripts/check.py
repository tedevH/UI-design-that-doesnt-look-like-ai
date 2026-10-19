#!/usr/bin/env python3
"""Render a standalone page and report objective issues plus style signals for review."""

import json
import sys
from pathlib import Path

from _env import bootstrap

bootstrap()

from lib import audit, tells, tokens  # noqa: E402
from lib.render import Renderer  # noqa: E402

PAGE_TYPES = ["landing", "app", "mobile", "portfolio", "article", "commerce", "event", "tool", "game"]
LANDING_ONLY = {"centered_hero", "three_card_grids", "uniform_sections", "round_vanity_stats", "icon_feature_cards"}


def facts(styles: dict) -> str:
    summary = tokens.summary(styles)
    viewport = styles.get("viewport") or {}
    audit_data = styles.get("audit") or {}
    return "\n".join([
        f"- viewport: {viewport.get('w', '?')} × {viewport.get('h', '?')}px",
        f"- fonts: {', '.join(summary['fonts']) or 'unknown'}",
        f"- type sizes: {summary['type_sizes']}; largest/body ratio {summary['type_scale']}",
        f"- text colors: {summary['text_colors']}; backgrounds: {summary['bg_colors']}",
        f"- page height: {round((styles.get('docHeight') or 0) / (viewport.get('h') or 900), 1)} screens",
        f"- horizontal overflow: {max(0, (audit_data.get('scrollWidth') or viewport.get('w', 0)) - viewport.get('w', 0))}px",
        f"- overlapping text boxes: {styles.get('overlaps', 0)}",
    ])


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("page", help="standalone HTML file to render")
    ap.add_argument("--type", default="landing", choices=PAGE_TYPES, help="page type for contextual style signals")
    a = ap.parse_args()

    page = Path(a.page).expanduser().resolve()
    if not page.is_file():
        ap.error(f"page not found: {page}")
    html = page.read_text(encoding="utf-8")
    shots = page.parent / f"{page.stem}-shots"

    with Renderer() as renderer:
        styles = renderer.capture(shots, url=page.as_uri(), mobile=True)

    viewports = styles.get("viewports") or {"desktop": styles}
    desktop = viewports.get("desktop") or styles
    issues = audit.inspect(styles)
    signals = tells.detect(html, desktop)
    if a.type != "landing":
        signals = [signal for signal in signals if signal.name not in LANDING_ONLY]

    print("DESKTOP\n" + facts(desktop))
    print("\nOBJECTIVE CHECKS" + (": no measured issues" if not issues else " (review and fix these)"))
    for finding in issues:
        print(f"  [{finding.severity.upper()}] {finding.code} ({finding.viewport}): {finding.evidence}")
        print(f"    → {finding.recommendation}")

    print("\nSTYLE SIGNALS (prompts for human review; not pass/fail)")
    if not signals:
        print("  none detected")
    for signal in signals:
        print(f"  [{signal.severity}] {signal.name}: {signal.evidence}")
        print("    Review in context; this pattern can be right when the brief calls for it.")

    if "mobile" in viewports:
        mobile = viewports["mobile"]
        mobile_audit = mobile.get("audit") or {}
        print("\nMOBILE")
        print(f"  viewport: {mobile.get('viewport', {}).get('w', '?')} × {mobile.get('viewport', {}).get('h', '?')}px")
        print(f"  document width: {mobile_audit.get('scrollWidth', '?')}px")
        print(f"  text overlaps: {mobile.get('overlaps', 0)}")

    print(f"\nSCREENSHOTS\n  desktop: {shots / 'desktop.png'}")
    if "mobile" in viewports:
        print(f"  mobile:  {shots / 'mobile.png'}")

    report = {
        "page": str(page),
        "type": a.type,
        "objective_findings": [finding.as_dict() for finding in issues],
        "style_signals": [signal.as_dict() for signal in signals],
        "viewports": {
            name: {
                "viewport": data.get("viewport"),
                "audit": data.get("audit"),
                "overlaps": data.get("overlaps", 0),
            }
            for name, data in viewports.items()
        },
    }
    (shots / "check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 1 if any(finding.severity == "error" for finding in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
