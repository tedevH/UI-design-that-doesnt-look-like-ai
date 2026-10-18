from notai import tokens


def test_purple_gradient_detection():
    assert tokens.is_purple_gradient("linear-gradient(90deg, rgb(168, 85, 247), rgb(59, 130, 246))")
    assert tokens.is_purple_gradient("linear-gradient(#8b5cf6, #ec4899)")
    assert not tokens.is_purple_gradient("linear-gradient(rgb(245, 240, 230), rgb(230, 222, 205))")
    assert not tokens.is_purple_gradient("linear-gradient(#f97316, #facc15)")


def test_features_shape_and_values():
    styles = {
        "viewport": {"w": 1440, "h": 900}, "docHeight": 1800,
        "fonts": {"newsreader": 300, "ibm plex sans": 2000},
        "fontSizes": {"17": 2000, "88": 300},
        "textColors": {"#1d1b18": 2000, "#8a2f1d": 50}, "bgColors": {"#f3efe6": 9000},
        "radii": {"0": 10}, "boxes": 10, "borderedBoxes": 6, "words": 400,
    }
    f = tokens.features(styles)
    assert set(f) == set(tokens.FEATURE_NAMES)
    assert f["type_scale"] > 5
    assert f["dark_bg"] == 0
    assert f["neutral_warmth"] > 0
    assert f["radius_median"] == 0
    assert len(tokens.vector(styles)) == len(tokens.FEATURE_NAMES)


def test_empty_styles_do_not_crash():
    assert len(tokens.vector({})) == len(tokens.FEATURE_NAMES)
    assert tokens.summary({})["fonts"] == []
