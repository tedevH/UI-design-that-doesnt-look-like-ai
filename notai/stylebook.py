"""Cluster good sites into distinct style families with concrete, prompt-ready rules."""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path

from . import config, tokens
from .config import need


def _median(values, default=0.0):
    values = [v for v in values if v is not None]
    return float(statistics.median(values)) if values else default


def describe(members: list[dict]) -> dict:
    """Aggregate member features/summaries into one family description. Pure Python."""
    feats = [m["features"] for m in members]
    summ = [m["summary"] for m in members]
    f = lambda k: _median([x[k] for x in feats])

    font_counts = Counter(font for s in summ for font in s["fonts"][:2])
    text_counts = Counter(c for s in summ for c in s["text_colors"][:2])
    bg_counts = Counter(c for s in summ for c in s["bg_colors"][:2])
    body = f("body_size") or 16
    scale = f("type_scale") or 3.0

    traits = {
        "tone": "dark" if f("dark_bg") >= 0.5 else "light",
        "type": "serif-led" if f("serif_share") > 0.25 else "mono-technical" if f("mono_share") > 0.2 else "grotesk",
        "shape": "sharp" if f("radius_median") <= 4 else "soft" if f("radius_median") >= 12 else "rounded",
        "density": "dense" if f("words_per_screen") > 260 else "airy" if f("words_per_screen") < 110 else "balanced",
        "layout": "centered" if f("centered_hero") >= 0.5 else "left-aligned",
        "surface": "bordered" if f("border_share") > f("shadow_share") else "shadowed" if f("shadow_share") > 0.2 else "flat",
        "imagery": "image-heavy" if f("images_per_screen") > 3 else "type-only" if f("images_per_screen") < 0.6 else "some imagery",
    }
    name = f"{traits['tone']} {traits['type']} · {traits['shape']} · {traits['density']}"

    sizes = sorted({round(body * r) for r in (0.8, 1, 1.25, 1.6, 2.2, scale)})
    return {
        "name": name,
        "traits": traits,
        "fonts_seen": [k for k, _ in font_counts.most_common(4)],
        "type": {"body_px": round(body), "scale_ratio": round(scale, 2), "suggested_sizes_px": sizes,
                 "tracking_em": round(f("display_tracking"), 3)},
        "palette": {"text": [k for k, _ in text_counts.most_common(3)], "background": [k for k, _ in bg_counts.most_common(3)],
                    "accent_saturation": round(f("accent_saturation"), 2), "neutral_warmth": round(f("neutral_warmth"), 3)},
        "shape": {"radius_px": round(f("radius_median")), "shadow_share": round(f("shadow_share"), 2),
                  "border_share": round(f("border_share"), 2)},
        "density": {"words_per_screen": round(f("words_per_screen")), "images_per_screen": round(f("images_per_screen"), 1)},
        "examples": [m["slug"] for m in members[:5]],
        "size": len(members),
    }


def rules(family: dict) -> list[str]:
    """Concrete directives for the generation prompt."""
    t, p, s, tr = family["type"], family["palette"], family["shape"], family["traits"]
    warmth = p["neutral_warmth"]
    neutral = "slightly warm neutrals (paper, stone, ink)" if warmth > 0.01 else "slightly cool neutrals (fog, slate, graphite)" if warmth < -0.01 else "true neutrals"
    out = [
        f"Tone: {tr['tone']} background with {neutral}; never pure #000 on pure #fff.",
        f"Type: {tr['type']} — body {t['body_px']}px, display text about {t['scale_ratio']}x body. Use sizes from {t['suggested_sizes_px']}.",
        f"Display tracking around {t['tracking_em']}em (negative = tighter) on large headings.",
        f"Accent: one accent color, saturation about {p['accent_saturation']}, used on fewer than 5% of pixels.",
        f"Corners: {s['radius_px']}px radius, applied consistently.",
        "Separate surfaces with 1px borders and background shifts, not drop shadows." if s["border_share"] >= s["shadow_share"] else "Shadows only on elements that actually float (menus, dialogs).",
        f"Density: {tr['density']} — about {family['density']['words_per_screen']} words per screen.",
        f"Hero: {tr['layout']}; imagery: {tr['imagery']}.",
    ]
    if family.get("fonts_seen"):
        out.append(f"Typefaces used by sites in this family (for reference, pick free alternatives from Google Fonts): {', '.join(family['fonts_seen'])}.")
    return out


def build(k: int | None = None, use_embeddings: bool = False, out: Path = config.STYLEBOOK) -> dict:
    np = need("numpy", "critic")
    cluster = need("sklearn.cluster", "critic")
    pre = need("sklearn.preprocessing", "critic")
    decomposition = need("sklearn.decomposition", "critic")
    from .label import resolved_labels
    from .scrape import iter_sites

    labels = resolved_labels()
    members = []
    for slug, meta, d in iter_sites():
        if labels.get(slug) != 1 or not (d / "styles.json").exists():
            continue
        styles = json.loads((d / "styles.json").read_text())
        members.append({"slug": slug, "url": meta.get("url"), "features": tokens.features(styles),
                        "summary": tokens.summary(styles), "vec": tokens.vector(styles)})
    if len(members) < 8:
        raise SystemExit(f"Need at least 8 good sites with styles to build a stylebook (have {len(members)}).")

    X = pre.StandardScaler().fit_transform(np.array([m["vec"] for m in members]))
    if use_embeddings:
        emb_dir = config.CACHE / "emb" / config.DEFAULT_EMBED_MODEL.replace("/", "__")
        embs = [np.load(emb_dir / f"{m['slug']}.npy") if (emb_dir / f"{m['slug']}.npy").exists() else None for m in members]
        if all(e is not None for e in embs):
            E = decomposition.PCA(n_components=min(12, len(members) - 1)).fit_transform(np.stack(embs))
            X = np.concatenate([X, pre.StandardScaler().fit_transform(E)], axis=1)
        else:
            print("embeddings missing for some sites (run `notai critic train` first); using style features only")

    k = k or max(4, min(16, len(members) // 8))
    km = cluster.KMeans(n_clusters=k, n_init=10, random_state=0).fit(X)
    families = []
    for c in range(k):
        idx = [i for i, l in enumerate(km.labels_) if l == c]
        if not idx:
            continue
        # Order members by closeness to the centroid so examples are the most typical.
        idx.sort(key=lambda i: float(((X[i] - km.cluster_centers_[c]) ** 2).sum()))
        fam = describe([members[i] for i in idx])
        fam["id"] = f"f{c:02d}"
        fam["rules"] = rules(fam)
        families.append(fam)
    families.sort(key=lambda f: -f["size"])

    book = {"families": families, "n_sites": len(members)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(book, indent=2))
    out.with_suffix(".md").write_text(to_markdown(book))
    return book


def to_markdown(book: dict) -> str:
    lines = ["# Stylebook", "", f"{len(book['families'])} families from {book['n_sites']} good sites.", ""]
    for f in book["families"]:
        lines += [f"## {f['id']} — {f['name']} ({f['size']} sites)", "", "Examples: " + ", ".join(f["examples"]), ""]
        lines += [f"- {r}" for r in f["rules"]] + [""]
    return "\n".join(lines)


def load(path: Path = config.STYLEBOOK) -> dict | None:
    return json.loads(Path(path).read_text()) if Path(path).exists() else None


# Used until the user has built a stylebook from their own data.
DEFAULT_FAMILIES = [
    {"id": "editorial", "name": "light serif-led · sharp · balanced",
     "rules": ["Tone: warm off-white paper (#f5f1e8-ish) with near-black ink (#1c1b19-ish).",
               "Type: a high-contrast serif for display (e.g. Fraunces, Newsreader, Instrument Serif) with a plain grotesk for UI text; display about 4.5x body.",
               "Tight display tracking (-0.02em), generous line-height for body (1.55), 60–70ch measure.",
               "Accent: one ink-like accent (oxblood, forest, or cobalt) used sparingly for links and one button.",
               "Corners: 0–2px. Rules (1px lines) separate sections; no shadows.",
               "Layout: left-aligned hero, asymmetric 12-column grid, a large numeral or pull-quote as a graphic element."]},
    {"id": "swiss-tool", "name": "light grotesk · sharp · dense",
     "rules": ["Tone: cool white (#fafafa) and graphite (#16181d); grey scale does most of the work.",
               "Type: one strong grotesk (e.g. Geist, Inter Tight, Space Grotesk) in 3–4 sizes; display about 3.5x body; tabular numbers for data.",
               "Accent: a single saturated color (signal orange or electric blue) for the primary action only.",
               "Corners: 4–6px everywhere. 1px borders, no gradients, no blur.",
               "Layout: left-aligned headline with a real product screenshot or data table on the right; dense information below.",
               "Copy: short, specific, technical. Name the integration, the number, the unit."]},
    {"id": "brutal-mono", "name": "light mono-technical · sharp · airy",
     "rules": ["Tone: stark: off-white (#f2f2ee) and true black text; one loud accent (acid yellow or red) used in blocks.",
               "Type: a monospace (e.g. JetBrains Mono, IBM Plex Mono) for everything or paired with a condensed grotesk; huge display size (6x body).",
               "Corners: 0px. Thick 2px borders. Visible grid lines.",
               "Layout: uneven columns, oversized labels, content that intentionally breaks the grid.",
               "Copy: blunt and short."]},
    {"id": "dark-product", "name": "dark grotesk · rounded · balanced",
     "rules": ["Tone: near-black (#0e0f11) with off-white text (#ecebe8), NOT a purple/blue neon look.",
               "Type: a refined grotesk with tight tracking; display about 4x body; subdued grey for secondary text.",
               "Accent: one desaturated color (sage, sand, or ice) — no gradients on text or buttons.",
               "Corners: 8px. Surfaces separated by subtle 1px borders (#ffffff14), no glow, no glass.",
               "Layout: product UI shown large and crisp; sections vary in layout (split, full-bleed, list)."]},
    {"id": "warm-consumer", "name": "light serif-led · soft · airy",
     "rules": ["Tone: warm cream, terracotta or olive accents; feels physical and crafted.",
               "Type: a friendly serif or soft grotesk for display, generous size; body 17–18px.",
               "Imagery: real photography of the product in use, full-bleed, with text overlapping or beside it.",
               "Corners: one consistent soft radius (12px) on images only; buttons can be pills.",
               "Copy: warm, specific, sensory; no startup clichés."]},
]
