"""Turn extracted computed styles (styles.json) into numeric design features."""

from __future__ import annotations

import colorsys
import math
import statistics

SERIF_HINTS = ("serif", "garamond", "times", "georgia", "caslon", "baskerville", "playfair",
               "canela", "tiempos", "freight", "lora", "merriweather", "fraunces", "domaine",
               "editorial", "publico", "lyon", "signifier", "gt super", "reckless")
MONO_HINTS = ("mono", "code", "courier", "consolas", "menlo", "jetbrains", "fira code")
GENERIC_SANS = ("inter", "system-ui", "-apple-system", "blinkmacsystemfont", "segoe ui",
                "roboto", "helvetica", "arial", "sans-serif", "ui-sans-serif", "open sans")

FEATURE_NAMES = [
    "n_fonts", "generic_font_share", "serif_share", "mono_share",
    "n_font_sizes", "body_size", "max_size", "type_scale", "display_tracking",
    "n_text_colors", "n_bg_colors", "dark_bg", "accent_saturation", "neutral_warmth",
    "gradient_area", "purple_gradient", "gradient_text",
    "radius_median", "large_radius_share", "shadow_share", "border_share", "blur",
    "n_spacing", "grid8_share", "emoji", "card_rows", "centered_hero",
    "images_per_screen", "words_per_screen",
]


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def luminance(h: str) -> float:
    r, g, b = hex_to_rgb(h)
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def hsv(h: str) -> tuple[float, float, float]:
    return colorsys.rgb_to_hsv(*hex_to_rgb(h))


def _weighted_top(d: dict, cover: float = 0.9) -> list[tuple[str, float]]:
    """Keys that together cover `cover` of total weight, largest first."""
    items = sorted(((k, float(v)) for k, v in (d or {}).items()), key=lambda kv: -kv[1])
    total = sum(v for _, v in items) or 1.0
    out, acc = [], 0.0
    for k, v in items:
        out.append((k, v))
        acc += v
        if acc / total >= cover:
            break
    return out


def _share(d: dict, pred) -> float:
    total = sum(d.values()) if d else 0
    return sum(v for k, v in d.items() if pred(k)) / total if total else 0.0


def is_purple_gradient(css: str) -> bool:
    """True if a gradient mixes violet/indigo/magenta hues with blue or pink (the AI-default look)."""
    import re

    hues = []
    for m in re.finditer(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", css):
        r, g, b = (int(x) / 255 for x in m.groups())
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if s > 0.35 and v > 0.3:
            hues.append(h * 360)
    for m in re.finditer(r"#([0-9a-fA-F]{6})\b", css):
        h, s, v = hsv(m.group(1))
        if s > 0.35 and v > 0.3:
            hues.append(h * 360)
    purple = any(250 <= h <= 320 for h in hues)
    partner = any((190 <= h < 250) or (320 < h <= 350) for h in hues)
    return purple and (partner or len(hues) >= 2)


def features(styles: dict) -> dict[str, float]:
    s = styles or {}
    vh = (s.get("viewport") or {}).get("h") or 900
    screens = max(1.0, (s.get("docHeight") or vh) / vh)

    fonts = s.get("fonts") or {}
    top_fonts = _weighted_top(fonts)
    sizes = {int(float(k)): v for k, v in (s.get("fontSizes") or {}).items() if float(k) > 0}
    body_size = max(sizes, key=sizes.get) if sizes else 16
    max_size = max(sizes) if sizes else body_size

    # Median letter-spacing in em across text that sets it (tight display tracking = deliberate type).
    ls = s.get("letterSpacing") or {}
    tracking = statistics.median([float(k) for k in ls]) if ls else 0.0

    text_colors = s.get("textColors") or {}
    bg_colors = s.get("bgColors") or {}
    top_bg = _weighted_top(bg_colors, 0.95)
    main_bg = top_bg[0][0] if top_bg else "#ffffff"

    all_colors = [k for k, _ in _weighted_top(text_colors, 0.97)] + [k for k, _ in top_bg]
    sats = [hsv(c)[1] for c in all_colors]
    accent_sat = max(sats) if sats else 0.0
    neutrals = [c for c in all_colors if hsv(c)[1] < 0.15]
    warmth = 0.0
    if neutrals:
        warmth = statistics.mean(hex_to_rgb(c)[0] - hex_to_rgb(c)[2] for c in neutrals)

    gradients = s.get("gradients") or []
    page_area = (s.get("viewport") or {}).get("w", 1440) * (s.get("docHeight") or vh)
    gradient_area = min(1.0, sum(g.get("area", 0) for g in gradients) / page_area) if page_area else 0.0
    purple = float(any(is_purple_gradient(g.get("css", "")) for g in gradients))

    radii = {int(float(k)): v for k, v in (s.get("radii") or {}).items()}
    radius_vals = [r for r, n in radii.items() for _ in range(int(n))]
    boxes = s.get("boxes") or 0

    spacing = {int(float(k)): v for k, v in (s.get("spacing") or {}).items()}
    rows = s.get("rows") or []
    hero = s.get("hero") or {}

    return {
        "n_fonts": float(len(top_fonts)),
        "generic_font_share": _share(fonts, lambda f: any(g in f for g in GENERIC_SANS)),
        "serif_share": _share(fonts, lambda f: any(h in f for h in SERIF_HINTS) and "sans" not in f),
        "mono_share": _share(fonts, lambda f: any(h in f for h in MONO_HINTS)),
        "n_font_sizes": float(len(_weighted_top(sizes, 0.95))),
        "body_size": float(body_size),
        "max_size": float(max_size),
        "type_scale": max_size / body_size if body_size else 1.0,
        "display_tracking": tracking,
        "n_text_colors": float(len(_weighted_top(text_colors, 0.95))),
        "n_bg_colors": float(len(top_bg)),
        "dark_bg": float(luminance(main_bg) < 0.2),
        "accent_saturation": accent_sat,
        "neutral_warmth": warmth,
        "gradient_area": gradient_area,
        "purple_gradient": purple,
        "gradient_text": float(s.get("gradientText") or 0),
        "radius_median": float(statistics.median(radius_vals)) if radius_vals else 0.0,
        "large_radius_share": sum(1 for r in radius_vals if r >= 12) / len(radius_vals) if radius_vals else 0.0,
        "shadow_share": (s.get("shadowedBoxes") or 0) / boxes if boxes else 0.0,
        "border_share": (s.get("borderedBoxes") or 0) / boxes if boxes else 0.0,
        "blur": float(s.get("blur") or 0),
        "n_spacing": float(len(_weighted_top(spacing, 0.9))),
        "grid8_share": _share(spacing, lambda v: v % 8 == 0 or v % 4 == 0),
        "emoji": float(s.get("emoji") or 0),
        "card_rows": float(sum(1 for r in rows if r.get("similar") and 3 <= r.get("n", 0) <= 4)),
        "centered_hero": float(bool(hero.get("centered"))),
        "images_per_screen": (s.get("images") or 0) / screens,
        "words_per_screen": (s.get("words") or 0) / screens,
    }


def vector(styles: dict) -> list[float]:
    f = features(styles)
    # log-compress counts so one huge value doesn't dominate the critic.
    out = []
    for name in FEATURE_NAMES:
        v = f[name]
        out.append(math.log1p(v) if v > 1 else v)
    return out


def summary(styles: dict) -> dict:
    """Human-readable design tokens for prompts and the stylebook."""
    s = styles or {}
    fonts = [f for f, _ in _weighted_top(s.get("fonts") or {}, 0.9)][:3]
    sizes = sorted({int(float(k)) for k, _ in _weighted_top(s.get("fontSizes") or {}, 0.95)})
    text = [c for c, _ in _weighted_top(s.get("textColors") or {}, 0.9)][:4]
    bg = [c for c, _ in _weighted_top(s.get("bgColors") or {}, 0.95)][:4]
    f = features(s)
    return {
        "fonts": fonts,
        "type_sizes": sizes[:10],
        "text_colors": text,
        "bg_colors": bg,
        "radius": f["radius_median"],
        "shadows": round(f["shadow_share"], 2),
        "borders": round(f["border_share"], 2),
        "type_scale": round(f["type_scale"], 2),
        "dark": bool(f["dark_bg"]),
        "centered_hero": bool(f["centered_hero"]),
    }
