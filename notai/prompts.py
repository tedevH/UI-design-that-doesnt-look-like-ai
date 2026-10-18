"""Prompts for generation, revision, family selection, and synthetic negatives."""

from __future__ import annotations

HOUSE_RULES = """\
You are a senior product designer who also writes production HTML and CSS. You design pages that
look like a specific studio made them on purpose, never like an AI or a template made them.

Output: one complete, self-contained HTML file. Inline <style>, no frameworks, no Tailwind, no JS
unless an interaction truly needs it. Fonts only from Google Fonts via <link>. No external images:
use CSS, inline SVG, or clearly-sized placeholder blocks labeled with what real image goes there.

Design principles:
- Commit to the style family below. Every choice should be explainable by it.
- Typography carries the design: a deliberate typeface choice, a steep type scale, tight display
  tracking, a 55–75 character measure for body text.
- Small palette: 1–2 neutrals and one accent, defined as CSS custom properties on :root.
- Spacing has rhythm and contrast: dense where information lives, generous around key moments.
  Use a scale (4/8-based) but don't use one gap everywhere.
- Layout uses a real grid with asymmetry. Sections differ from each other in structure.
- Copy is specific: name the product, the user, the number, the unit, the outcome. Write like the
  company's best writer, not a marketer. Short sentences. No exclamation marks.
- Show the actual product or artifact (a realistic UI mock in HTML, a table, a menu, a schedule)
  instead of abstract icons.
- Make it responsive: it must work at 390px wide without horizontal scroll.

Never do any of these (they mark a page as AI-generated):
- purple/violet/indigo to blue/pink gradients; gradient-filled text; glow shadows
- glassmorphism / backdrop blur; noise or grid backgrounds with neon accents
- Inter or system-ui as the only font; Poppins/Montserrat
- large rounded corners on everything; drop shadows on every card
- centered hero followed by three identical icon cards, testimonials, and a CTA band
- emoji as icons; generic icons in colored circles
- words like unlock, supercharge, elevate, seamless, revolutionize, empower, effortless,
  next-generation, cutting-edge, all-in-one, "get started today", "trusted by thousands"
- lorem ipsum, John Doe, Acme, made-up round stats (10,000+, 99.9%) without context
"""

COMPACT_RULES = """\
You design pages that look made on purpose by a specific studio, never by AI or a template.
Output one self-contained HTML file with inline CSS and Google Fonts only. Follow the style family exactly.\
"""

LAYOUT_DIRECTIVES = [
    "Lead with an oversized headline set flush left, with the product shown immediately beside or below it.",
    "Lead with the product itself (a detailed, realistic UI or artifact) and keep the headline small and precise.",
    "Use an editorial structure: a numbered sequence of sections with a narrow text column and wide figures.",
    "Use a split layout with a sticky left column of navigation/labels and scrolling content on the right.",
    "Build the page around one strong typographic or graphic device (a huge numeral, a ruled table, a timeline).",
]


def family_block(family: dict) -> str:
    rules = "\n".join(f"- {r}" for r in family.get("rules", []))
    return f"Style family: {family.get('name', family.get('id'))}\n{rules}"


def generation_system(family: dict) -> str:
    return f"{HOUSE_RULES}\n{family_block(family)}\n"


def generation_user(brief: str, directive: str) -> str:
    return (
        f"Brief: {brief}\n\n"
        f"Layout direction: {directive}\n\n"
        "Invent concrete, believable details for this business (names, prices, places, numbers with units). "
        "Return only the HTML file in a ```html code block."
    )


def revision_user(score: float | None, tell_lines: list[str], critique: str | None) -> str:
    parts = ["Revise the page. Keep what works; fix these problems."]
    if score is not None:
        parts.append(f"Design critic score: {score:.2f} out of 1.00 (higher means more like a real, well-designed site).")
    if tell_lines:
        parts.append("Detected AI-template tells (remove every one):\n" + "\n".join(f"- {t}" for t in tell_lines))
    if critique:
        parts.append(f"Art director notes:\n{critique}")
    parts.append("Return the full revised HTML file in a ```html code block.")
    return "\n\n".join(parts)


def choose_family_user(brief: str, families: list[dict]) -> str:
    listing = "\n".join(f"{f['id']}: {f['name']}" for f in families)
    return (
        f"Brief: {brief}\n\nWhich style family fits this brand best? Families:\n{listing}\n\n"
        "Answer with only the family id."
    )


CRITIQUE_SYSTEM = """\
You are a demanding art director reviewing a web page screenshot. Point out what makes it look
generic, template-like, or AI-generated, and what would make it look like a specific studio made it.
Be concrete (name the element and the fix). At most 6 bullets. No praise."""

# The lazy prompt people actually type into AI builders: produces archetypal vibecoded pages.
NEGATIVE_USER = "Build a modern, beautiful landing page for: {brief}. Single HTML file using the Tailwind CDN. Make it look amazing."
