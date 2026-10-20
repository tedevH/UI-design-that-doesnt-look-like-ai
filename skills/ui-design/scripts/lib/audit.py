"""Objective checks for rendered pages; subjective style signals stay separate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Finding:
    code: str
    severity: str
    viewport: str
    evidence: str
    recommendation: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def inspect_view(name: str, styles: dict[str, Any]) -> list[Finding]:
    """Turn browser-extracted measurements into actionable, non-aesthetic findings."""
    a = (styles or {}).get("audit") or {}
    out: list[Finding] = []

    width = int(a.get("viewportWidth") or (styles.get("viewport") or {}).get("w") or 0)
    scroll_width = int(a.get("scrollWidth") or width)
    overflow = max(0, scroll_width - width)
    if overflow > 2:
        out.append(Finding(
            "horizontal_overflow", "error", name, f"document is {overflow}px wider than the {width}px viewport",
            "Find the element extending past the viewport; make the layout reflow without hiding essential content."
        ))

    edge = (styles or {}).get("edgeText") or []
    if edge:
        out.append(Finding(
            "text_at_viewport_edge", "error", name, f"text touches the screen edge: {'; '.join(edge[:3])}",
            "Restore side padding on the containing section (a padding shorthand often overrides a wrapper's horizontal padding)."
        ))

    for src in (a.get("brokenImages") or [])[:5]:
        out.append(Finding(
            "broken_image", "error", name, src[:120],
            "Fix the asset path or replace it with an available image."
        ))

    missing_alt = int(a.get("imagesMissingAlt") or 0)
    if missing_alt:
        out.append(Finding(
            "image_alt_missing", "warning", name, f"{missing_alt} visible image(s) have no alt attribute",
            "Add useful alt text, or alt=\"\" when the image is decorative."
        ))

    for item in (a.get("unlabeledControls") or [])[:5]:
        out.append(Finding(
            "control_name_missing", "warning", name, str(item)[:120],
            "Give the control a visible label or an accessible name."
        ))

    for item in (a.get("lowContrast") or [])[:5]:
        out.append(Finding(
            "text_contrast_low", "warning", name, str(item)[:160],
            "Check the foreground and actual background colors; increase contrast when the text is essential."
        ))

    small_targets = int(a.get("targetsUnder24px") or 0)
    if small_targets:
        out.append(Finding(
            "small_target", "info", name, f"{small_targets} visible interactive target(s) are under 24px in one dimension",
            "Review whether each target has enough hit area and spacing, especially on touch screens."
        ))

    if not a.get("documentTitle"):
        out.append(Finding(
            "document_title_missing", "warning", name, "document has no title",
            "Add a concise, page-specific document title."
        ))

    if not a.get("documentLanguage"):
        out.append(Finding(
            "document_language_missing", "warning", name, "html element has no lang attribute",
            "Set the document language on the html element."
        ))

    multiple_h1 = int(a.get("h1Count") or 0)
    if multiple_h1 > 1:
        out.append(Finding(
            "multiple_primary_headings", "info", name, f"{multiple_h1} visible h1 elements",
            "Review the heading hierarchy and make the page's primary heading clear."
        ))

    return out


def inspect(styles: dict[str, Any]) -> list[Finding]:
    """Inspect desktop and mobile measurements when available."""
    viewports = (styles or {}).get("viewports") or {}
    if not viewports:
        viewports = {"desktop": styles or {}}
    findings: list[Finding] = []
    for name in ("desktop", "mobile"):
        if name in viewports and viewports[name]:
            findings.extend(inspect_view(name, viewports[name]))
    return findings
