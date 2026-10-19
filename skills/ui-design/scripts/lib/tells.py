"""Rule-based detector for the vibecoded look.

Works on raw HTML/CSS text alone (zero dependencies), and gets more precise when
given the computed styles extracted from a rendered page.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from . import tokens


@dataclass
class Tell:
    name: str
    severity: int  # 1 = minor, 2 = clear, 3 = signature AI look
    evidence: str

    def as_dict(self) -> dict:
        return asdict(self)


CLICHES = [
    "unlock", "supercharge", "elevate your", "seamless", "seamlessly", "revolutionize",
    "next-generation", "next-gen", "empower", "effortlessly", "cutting-edge", "game-changer",
    "game changing", "get started today", "trusted by thousands", "all-in-one",
    "take your .{1,20} to the next level", "transform the way", "streamline your",
    "harness the power", "in today's fast-paced", "unleash", "skyrocket", "10x your",
    "built for the future", "the future of", "say goodbye to", "join thousands",
    "lightning-fast", "blazing fast", "world-class", "state-of-the-art",
]
PLACEHOLDERS = [r"lorem ipsum", r"john doe", r"jane doe", r"\bacme\b", r"your company", r"example\.com",
                r"placeholder", r"\bcompany name\b"]
TAILWIND_DEFAULT_ACCENTS = r"\b(?:bg|text|from|via|to|border|ring)-(?:indigo|violet|purple|fuchsia)-(?:4|5|6)00\b"
CHUNKY_FONTS = ("archivo black", "unbounded", "anton", "bebas", "dela gothic", "big shoulders", "monument",
                "syne", "druk", "league gothic", "oswald", "chakra petch", "rubik mono", "archivo expanded")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F900-\U0001F9FF]")


def _visible_text(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def from_html(html: str) -> list[Tell]:
    found: list[Tell] = []
    low = html.lower()
    text = _visible_text(html)
    text_low = text.lower()

    def add(name, sev, evidence):
        found.append(Tell(name, sev, evidence[:160]))

    # Gradients
    tw_grad = re.findall(r"\bfrom-(?:purple|violet|indigo|fuchsia|pink)-\d00\b[^\"']*?\bto-(?:blue|cyan|pink|purple|indigo|violet)-\d00", low)
    css_grads = [g for g in re.findall(r"linear-gradient\([^;\"]*\)", low) if tokens.is_purple_gradient(_hex_to_rgb_css(g))]
    if tw_grad or css_grads:
        add("purple_gradient", 3, (tw_grad or css_grads)[0])
    if re.search(r"bg-clip-text|background-clip:\s*text|-webkit-background-clip:\s*text", low):
        add("gradient_text", 3, "background-clip: text on headline")

    # Typography
    fonts = set(re.findall(r"family=([a-z+]+)", low)) | set(re.findall(r"font-family:\s*['\"]?([a-z \-]+)", low))
    fonts = {f.replace("+", " ").strip() for f in fonts}
    if fonts and fonts <= {"inter", "system-ui", "sans-serif", "-apple-system", "ui-sans-serif", "roboto", "poppins"}:
        add("generic_type_only", 2, f"only generic sans fonts: {', '.join(sorted(fonts))}")
    elif not fonts and "font-sans" in low:
        add("generic_type_only", 2, "Tailwind default font-sans, no typeface chosen")
    if "poppins" in fonts or "montserrat" in fonts:
        add("template_font", 1, "Poppins/Montserrat: template-default display fonts")

    chunky = [f for f in fonts if any(c in f for c in CHUNKY_FONTS)]
    heavy = re.findall(r"font-weight:\s*(?:800|900|black|extra-?bold)", low) + re.findall(r"\bfont-(?:extrabold|black)\b", low)
    if chunky or len(heavy) >= 2:
        add("chunky_type", 2, ", ".join(chunky[:3]) or f"{len(heavy)} display rules at weight 800–900")

    # Fake "system status" decoration: coordinates, sector/serial codes, status readouts.
    gimmicks = (len(re.findall(r"\d{1,3}\.\d+°\s*[NSEW]|\d+°\s*\d+['′]", text))
                + len(re.findall(r"\b(?:SYS(?:TEM)?[ _]STATUS|SECTOR \d+|LIVE TELEMETRY|STATUS:|PROTOCOL|SERIAL|LAT:|LON:)", text))
                + len(re.findall(r"\b[A-Z]{2,}[-_/ ]\d{2,}[A-Z0-9-]*\b", text)) // 3)
    if gimmicks >= 4:
        add("telemetry_gimmick", 2, f"{gimmicks} status/coordinate/serial-code labels")

    # Shape and surface
    big_round = len(re.findall(r"\brounded-(?:2xl|3xl|full)\b", low)) + len(re.findall(r"border-radius:\s*(?:1[6-9]|[2-9]\d)px", low))
    if big_round >= 4:
        add("big_radius_everywhere", 2, f"{big_round} large-radius declarations")
    if re.search(r"backdrop-blur|backdrop-filter:\s*blur", low):
        add("glassmorphism", 2, "backdrop blur panels")
    shadows = len(re.findall(r"\bshadow-(?:lg|xl|2xl)\b", low)) + len(re.findall(r"box-shadow:[^;]*\d{2}px", low))
    if shadows >= 4:
        add("heavy_shadows", 1, f"{shadows} large drop shadows")
    if re.search(r"shadow-(?:purple|indigo|violet|blue|pink)-\d00|0 0 \d{2,}px rgba?\([^)]*(?:139|168|99), ?(?:92|85|102)", low):
        add("glow", 2, "colored glow shadows")
    if len(re.findall(TAILWIND_DEFAULT_ACCENTS, low)) >= 3:
        add("tailwind_default_accent", 2, "unmodified indigo/violet/purple Tailwind accents")

    # Layout
    cards = len(re.findall(r"\b(?:md|lg):grid-cols-3\b", low))
    if cards >= 2:
        add("three_card_grids", 2, f"{cards} three-column card grids")
    elif cards == 1:
        add("three_card_grids", 1, "three-column card grid")
    if re.search(r"<(?:section|header)[^>]*class=\"[^\"]*text-center[^\"]*\"[^>]*>\s*(?:<[^>]+>\s*)*<h1", low):
        add("centered_hero", 1, "centered hero headline")
    sections = len(re.findall(r"<section", low))
    if sections and len(set(re.findall(r"<section[^>]*class=\"([^\"]*)\"", low))) == 1 and sections >= 4:
        add("uniform_sections", 1, f"{sections} sections with identical classes")

    # Imagery: stock photos and pages that lean on photo slots instead of their own visuals
    stock = re.findall(r"(?:unsplash|pexels|pixabay|shutterstock|istockphoto|gettyimages|picsum\.photos|placehold|placekitten|loremflickr)\.", low)
    if stock:
        add("stock_photos", 3, f"{len(stock)} stock/placeholder image link(s) — draw graphics or use the user's photos")
    slots = len(re.findall(r"<img\b(?![^>]*\ssrc=)[^>]*data-photo=", low))
    if slots >= 4:
        add("photo_slot_heavy", 2, f"{slots} empty photo slots — draw the visuals instead; keep at most 2–3 slots for the client's own photos")

    # Content
    emoji = EMOJI.findall(text)
    if len(emoji) >= 3:
        add("emoji_icons", 3, f"{len(emoji)} emoji in page text: {''.join(emoji[:6])}")
    hits = [c for c in CLICHES if re.search(c, text_low)]
    if hits:
        add("cliche_copy", 3 if len(hits) >= 4 else 2 if len(hits) >= 2 else 1, ", ".join(hits[:6]))
    ph = [p for p in PLACEHOLDERS if re.search(p, text_low)]
    if ph:
        add("placeholder_content", 2, ", ".join(p.replace("\\b", "") for p in ph))
    stats = re.findall(r"\b\d{1,3}(?:,\d{3})*\+|\b\d{2}(?:\.\d)?%|\b\d+k\+", text_low)
    if len(stats) >= 3:
        add("round_vanity_stats", 1, ", ".join(stats[:5]))
    if re.search(r"(?:md|lg):grid-cols-3[^>]*>\s*(?:<div[^>]*>\s*){1,3}<svg", low) and text_low.count("feature") >= 2:
        add("icon_feature_cards", 1, "icon + title + blurb feature cards")

    return found


def from_styles(styles: dict) -> list[Tell]:
    f = tokens.features(styles)
    found: list[Tell] = []
    if f["purple_gradient"]:
        found.append(Tell("purple_gradient", 3, "rendered purple/blue gradient"))
    if f["gradient_text"]:
        found.append(Tell("gradient_text", 3, f"{int(f['gradient_text'])} gradient-filled text elements"))
    if f["generic_font_share"] > 0.95 and f["n_fonts"] <= 1:
        found.append(Tell("generic_type_only", 2, "one generic sans typeface for everything"))
    if f["type_scale"] < 2.5:
        found.append(Tell("flat_type_scale", 1, f"largest/body text ratio {f['type_scale']:.1f}"))
    if f["large_radius_share"] > 0.6:
        found.append(Tell("big_radius_everywhere", 2, f"{f['large_radius_share']:.0%} of boxes have radius >= 12px"))
    if f["blur"] >= 2:  # one blurred sticky nav is common on good sites; many blurred panels is not
        found.append(Tell("glassmorphism", 2 if f["blur"] >= 5 else 1, f"{int(f['blur'])} blurred surfaces"))
    if f["shadow_share"] > 0.5:
        found.append(Tell("heavy_shadows", 1, f"{f['shadow_share']:.0%} of boxes have shadows"))
    if f["card_rows"] >= 2:
        found.append(Tell("three_card_grids", 2 if f["card_rows"] >= 3 else 1, f"{int(f['card_rows'])} rows of identical cards"))
    if f["centered_hero"]:
        found.append(Tell("centered_hero", 1, "centered hero headline"))
    if f["emoji"] >= 3:
        found.append(Tell("emoji_icons", 3, f"{int(f['emoji'])} emoji"))
    overlaps = (styles or {}).get("overlaps") or 0
    if overlaps:
        found.append(Tell("text_overlap", 3, f"{overlaps} places where text overlaps other text"))
    return found


def detect(html: str | None = None, styles: dict | None = None) -> list[Tell]:
    """All tells, de-duplicated by name keeping the highest severity."""
    best: dict[str, Tell] = {}
    for t in (from_html(html) if html else []) + (from_styles(styles) if styles else []):
        if t.name not in best or t.severity > best[t.name].severity:
            best[t.name] = t
    return sorted(best.values(), key=lambda t: (-t.severity, t.name))


def penalty(tells: list[Tell]) -> int:
    return sum(t.severity for t in tells)


def _hex_to_rgb_css(css: str) -> str:
    """Expand #rgb shorthand so is_purple_gradient can read it."""
    return re.sub(r"#([0-9a-f])([0-9a-f])([0-9a-f])\b", lambda m: "#" + "".join(c * 2 for c in m.groups()), css)
