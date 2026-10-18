from notai import prompts, stylebook, util


def test_extract_html_from_fenced_response():
    raw = "Here you go:\n```html\n<!doctype html><html><body>hi</body></html>\n```\nEnjoy"
    assert util.extract_html(raw) == "<!doctype html><html><body>hi</body></html>"


def test_extract_html_without_fence():
    raw = "Sure! <!DOCTYPE html><html><body>x</body></html> trailing"
    assert util.extract_html(raw) == "<!DOCTYPE html><html><body>x</body></html>"


def test_slugify():
    assert util.slugify("https://www.Linear.app/") == "linear-app"


def _member(slug, **over):
    f = {k: 0.0 for k in __import__("notai.tokens", fromlist=["x"]).FEATURE_NAMES}
    f.update(body_size=16, type_scale=4.0, serif_share=0.6, words_per_screen=90, radius_median=0, border_share=0.5)
    f.update(over)
    s = {"fonts": ["newsreader", "ibm plex sans"], "text_colors": ["#1d1b18"], "bg_colors": ["#f3efe6"]}
    return {"slug": slug, "features": f, "summary": s}


def test_stylebook_describe_and_rules():
    fam = stylebook.describe([_member("a"), _member("b"), _member("c")])
    assert fam["traits"]["type"] == "serif-led"
    assert fam["traits"]["shape"] == "sharp"
    assert fam["traits"]["density"] == "airy"
    fam["id"] = "f00"
    rules = stylebook.rules(fam)
    assert any("borders" in r for r in rules)
    assert "Style family" in prompts.family_block({**fam, "rules": rules})


def test_default_families_render_into_prompt():
    for fam in stylebook.DEFAULT_FAMILIES:
        system = prompts.generation_system(fam)
        assert fam["rules"][0] in system
        assert "Never do any of these" in system
