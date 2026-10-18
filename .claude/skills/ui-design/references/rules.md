# Rules

## Output
- One self-contained HTML file. Hand-written CSS in `<style>` with the palette as CSS custom properties.
  Google Fonts via `<link>`. Vanilla JS only when an interaction needs it. No frameworks, no Tailwind.
- Responsive down to 390px with no horizontal scroll. Every word visible at 390px and 1440px: size display
  type with `clamp()`, allow wrapping, never clip.

## Typography
- Use the art direction's fonts **at the stated weights**. Hierarchy comes from size, spacing and contrast,
  not from piling on weight.
- Never: Archivo Black, Unbounded, Anton, Bebas Neue, Dela Gothic One, Syne ExtraBold, Big Shoulders,
  Monument-style extended faces, or display weights 800–900.
- Headlines in sentence case unless 1–3 words. Body 16–18px, line-height 1.45–1.6, measure 55–75ch.
- Inter, system-ui or Poppins alone is not a typographic choice.

## Color and surface
- 3–6 colors from the art direction. Use color the way the family says: big color fields for playful or
  expressive, restraint for luxury and Swiss.
- No purple/blue/pink gradients, no gradient text, no glow, no glassmorphism (blurred translucent panels).
- One consistent corner radius (0–8px unless the family says soft). Borders and background shifts over
  drop shadows.

## Layout
- A real grid with intentional asymmetry. Every section composed differently.
- Never the AI template: centered hero → three identical icon cards → testimonial → CTA band.
- Fixed headers never cover content: add top padding equal to the header height.
- No negative margins or absolute positioning that makes text collide.

## Content
- Specific, believable copy: names, prices, times, addresses, numbers with units. Short confident sentences.
- Show the actual thing: the menu, the product UI built in HTML, the schedule, the work.
- Never: unlock, elevate, seamless, revolutionize, empower, effortless, supercharge, next-generation,
  cutting-edge, all-in-one, "get started today", "trusted by thousands", lorem ipsum, John Doe, Acme,
  round vanity stats without context, emoji used as icons.
- No fake telemetry decoration (coordinates, "SYSTEM STATUS", serial codes, sector labels, monospace label
  clutter) unless the product is literally an engineering tool.

## Imagery
- Photos are `<img data-photo="precise description: subject, framing, light" data-aspect="16:9" alt="…">`
  with `object-fit: cover`. Aspects: 1:1, 3:4, 4:3, 4:5, 3:2, 16:9, 21:9, 9:16. Never link web images.
- Use 3–6 photos and make them matter: full-bleed, split screens, asymmetric grids.
- Where the brand suits illustration, draw custom inline SVG in the palette — simple, confident shapes,
  under ~60 lines each, never repeating long path data.

## Craft checklist (look at the screenshot)
- Is there one clear focal point above the fold?
- Does spacing have rhythm — tight within groups, generous between sections?
- Do edges align to a grid? Is anything floating?
- Is body text comfortably readable (contrast ≥ 4.5:1, size, measure)?
- Would a design director believe a studio made this for this specific brand?
