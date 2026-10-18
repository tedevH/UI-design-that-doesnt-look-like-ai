"""Hand-written style families for studio mode.

Each page is assigned one family so a batch covers genuinely different aesthetics instead of
collapsing onto one look. References are scraped sites that show the family at its best.
"""

from __future__ import annotations

FAMILIES = [
    {
        "id": "editorial-serif",
        "name": "Editorial serif",
        "look": "A beautifully typeset magazine. Serif display in regular or light weight, often italic for "
                "emphasis; a calm sans or serif for text; warm paper or ink-on-cream palette; columns, pull "
                "quotes, captions, generous margins.",
        "type": "Display: Newsreader, Fraunces (opsz, weight 300–500), Instrument Serif, Cormorant. Text: "
                "Newsreader, Source Serif 4, or Inter Tight 400. Headlines in sentence case.",
        "refs": ["stripe-press", "are-na", "sequoiacap-com", "ycombinator-com", "ghost-org"],
    },
    {
        "id": "swiss-minimal",
        "name": "Swiss minimal",
        "look": "Strict grid, lots of white space, black and white plus one clear color. Hierarchy from size "
                "and position, not weight. Thin rules, precise alignment, restrained motion.",
        "type": "One neutral grotesk (Geist, Hanken Grotesk, Schibsted Grotesk) at 400–500; large display "
                "sizes in regular weight with tight tracking. No heavy weights.",
        "refs": ["vercel-com", "nextjs-org", "culturedcode-com", "pentagram-com", "linear-app"],
    },
    {
        "id": "warm-crafted",
        "name": "Warm crafted",
        "look": "Tactile and human: earthy palette (clay, olive, oat, terracotta), soft photography of hands and "
                "materials, rounded image corners, relaxed rhythm, handmade details.",
        "type": "Soft serif display (Gambetta-like: Lora, Libre Caslon Display, Fraunces soft) at 400–500 with "
                "a humanist sans for text (Figtree, Karla). Sentence case.",
        "refs": ["allbirds-com", "everlane-com", "ouraring-com", "glossier-com", "rapha-cc"],
    },
    {
        "id": "playful-color",
        "name": "Playful color",
        "look": "Confident flat color fields (two or three saturated colors that clash nicely), custom inline-SVG "
                "illustrations and friendly shapes, stickers and badges, bouncy but tidy layout, light background.",
        "type": "Rounded or quirky grotesk (Bricolage Grotesque 500–600, DM Sans, Outfit) — friendly, not "
                "heavy. Mix sizes for energy rather than piling on weight.",
        "refs": ["gumroad-com", "duolingo-com", "cash-app", "headspace-com", "mercury-com"],
    },
    {
        "id": "quiet-luxury",
        "name": "Quiet luxury",
        "look": "Expensive restraint: huge white or stone space, a few large monochrome or muted photographs, "
                "tiny tracked uppercase labels, slow pace, almost no color.",
        "type": "Light or regular display serif or fashion sans (Cormorant Garamond 300, Italiana, Jost 300) "
                "with small tracked labels (letter-spacing 0.15em). Never bold.",
        "refs": ["leica-camera-com", "everlane-com", "wearecollins-com", "rapha-cc", "apple-com"],
    },
    {
        "id": "photo-led",
        "name": "Photo-led immersive",
        "look": "Cinematic, full-bleed photography carries the page; type sits on or beside images; dark or "
                "photo-derived palette; long scroll of image-and-caption scenes.",
        "type": "Medium-weight grotesk (Inter Tight 500, Manrope 500) or elegant serif; display large but not "
                "heavy; captions small.",
        "refs": ["nike-com", "squarespace-com", "rivian-com", "sonos-com", "monzo-com"],
    },
    {
        "id": "product-precise",
        "name": "Product precise",
        "look": "For software: the product itself shown as crisp, realistic UI built in HTML/CSS (tables, "
                "panels, code), subtle grays, one accent, dense information with clear hierarchy.",
        "type": "Clean grotesk (Geist, Inter Tight 400–600) plus a mono (Geist Mono, JetBrains Mono) only for "
                "code and data.",
        "refs": ["stripe-com", "linear-app", "raycast-com", "resend-com", "supabase-com"],
    },
    {
        "id": "expressive",
        "name": "Expressive experimental",
        "look": "One daring idea — type as image, an unusual grid, an oversized number, a custom SVG graphic, a "
                "striking color or photo treatment — executed with discipline everywhere else. Feels like a design "
                "studio site.",
        "type": "Characterful display (Instrument Serif italic, Space Grotesk, Syne 500, Fraunces italic) at "
                "regular weight, paired with a neutral text face.",
        "refs": ["teenage-engineering", "readymag-com", "instrument-com", "metalab-com", "spline-design"],
    },
]

BY_ID = {f["id"]: f for f in FAMILIES}


def candidates(usage: dict[str, int], k: int = 3, seed: int = 0) -> list[dict]:
    """The k least-used families so far (ties broken by a seeded shuffle), to keep a batch varied."""
    import random

    order = FAMILIES[:]
    random.Random(seed).shuffle(order)
    order.sort(key=lambda f: usage.get(f["id"], 0))
    return order[:k]


def describe(f: dict) -> str:
    return f"{f['name']} — {f['look']} Typography: {f['type']}"
