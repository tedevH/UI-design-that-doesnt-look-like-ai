from pathlib import Path

from notai import tells

FIX = Path(__file__).parent / "fixtures"


def names(found):
    return {t.name for t in found}


def test_vibecoded_page_has_many_tells():
    found = tells.detect((FIX / "vibecoded.html").read_text())
    n = names(found)
    assert len(found) >= 5
    assert {"purple_gradient", "gradient_text", "glassmorphism", "emoji_icons", "cliche_copy"} <= n
    assert tells.penalty(found) >= 15


def test_editorial_page_is_clean():
    found = tells.detect((FIX / "editorial.html").read_text())
    assert len(found) <= 1, found


def test_style_tells():
    styles = {
        "viewport": {"w": 1440, "h": 900}, "docHeight": 3600,
        "fonts": {"inter": 5000}, "fontSizes": {"16": 4000, "24": 500},
        "gradients": [{"css": "linear-gradient(90deg, rgb(168, 85, 247), rgb(59, 130, 246))", "area": 200000}],
        "gradientText": 1, "radii": {"24": 30, "0": 2}, "boxes": 32, "shadowedBoxes": 20, "blur": 3,
        "rows": [{"n": 3, "similar": True}, {"n": 3, "similar": True}], "hero": {"centered": True}, "emoji": 4,
    }
    n = names(tells.from_styles(styles))
    assert {"purple_gradient", "gradient_text", "generic_type_only", "flat_type_scale",
            "big_radius_everywhere", "glassmorphism", "three_card_grids", "emoji_icons"} <= n


def test_detect_dedupes_keeping_highest_severity():
    html = '<div class="text-center">Unlock</div>'
    styles = {"hero": {"centered": True}, "fontSizes": {"16": 1, "64": 1}}
    found = tells.detect(html, styles)
    assert len([t for t in found if t.name == "centered_hero"]) <= 1
