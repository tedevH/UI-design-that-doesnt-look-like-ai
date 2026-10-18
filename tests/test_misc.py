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


def test_dataset_top_fraction(tmp_path, monkeypatch):
    from notai import config, dataset

    monkeypatch.setattr(config, "GENERATIONS", tmp_path / "g.jsonl")
    monkeypatch.setattr(config, "SFT", tmp_path / "sft")
    util.write_jsonl(config.GENERATIONS, [
        {"brief": f"b{i}", "family_id": "f", "family": "F", "html": "<html></html>", "score": i / 10}
        for i in range(10)
    ])
    out = dataset.build(top=0.5)
    assert out["kept"] == 5 and out["min_score"] == 0.5


def test_budget_guard_stops_before_overspend():
    import pytest

    from notai import studio

    s = studio.Studio.__new__(studio.Studio)
    s.model, s.image_model = "gemini-3.8-flash", "gemini-3.1-flash-lite-image"
    s.usage = {"input": 0, "output": 1_000_000, "images": 0, "calls": 1}  # $3.75 spent
    s.budget, s.spent_before = 4.0, 0.0
    s._guard(0.10)  # $3.85 is fine
    with pytest.raises(studio.BudgetExceeded):
        s._guard(0.50)  # $4.25 is not


def test_parse_json_tolerates_fences_and_trailing_text():
    from notai.studio import parse_json

    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('{"best": 2}\n{"extra": true}') == {"best": 2}
