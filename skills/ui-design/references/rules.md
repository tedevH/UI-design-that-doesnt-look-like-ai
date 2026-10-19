# Rules

These are the floor. `beauty.md` is the ceiling — read both. A page that only follows these rules is clean
but not finished.

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
- Banned clichés: purple/blue/pink "AI" gradients, gradient-filled text, neon glow, glassmorphism panels
  everywhere, default gray drop shadows on every card.
- Allowed and encouraged when done with craft (see `beauty.md`): subtle on-palette gradients, grain,
  layered palette-tinted shadows, a single frosted element over a rich background, depth and overlap.
- One consistent corner-radius system (e.g. 6px for controls, 12px for cards) — not one big radius on everything.

## Layout
- A real grid with intentional asymmetry. Every section composed differently.
- Never the AI template: centered hero → three identical icon cards → testimonial → CTA band. On landing
  pages avoid grids of icon + title + blurb cards altogether: show features as a list with real detail, a
  diagram, an annotated view of the product, a timeline, or sections with different layouts.
- Buttons never wrap: labels are short and `white-space: nowrap`; long things like phone numbers are links, not pills.
- Fixed headers never cover content: add top padding equal to the header height.
- No negative margins or absolute positioning that makes text collide.

## Content
- Write the copy in the language the user wrote the request in, unless they ask for another. Local names,
  places and dish or product names can stay in the local language.
- Specific, believable copy: names, prices, times, addresses, numbers with units. Short confident sentences.
- Show the actual thing: the menu, the product UI built in HTML, the schedule, the work.
- Never: unlock, elevate, seamless, revolutionize, empower, effortless, supercharge, next-generation,
  cutting-edge, all-in-one, "get started today", "trusted by thousands", lorem ipsum, John Doe, Acme,
  round vanity stats without context, emoji used as icons.
- No fake telemetry decoration (coordinates, "SYSTEM STATUS", serial codes, sector labels, monospace label
  clutter) unless the product is literally an engineering tool.

## Imagery — graphics first, never stock
Most good sites don't use stock photos. Their visuals are the brand's own: typography, illustration,
color, the product itself, and the client's real photos. So:

- **Default to graphics you make in code:** custom inline SVG illustrations, icons, patterns, diagrams, maps,
  charts, typographic compositions (a huge numeral, a word set as image), CSS shapes and color fields, and
  for software the real product UI built in HTML. Pick one graphic language per page and keep it consistent.
- **The user's own photos:** if they give you photos (files, a folder, or URLs of their own site), use them
  with `<img src="…" alt="…">` and `object-fit: cover`, and design around them.
- **Photos only the client can provide** (their team, venue, actual products): if the page truly needs one,
  leave a slot and say so — `<img data-photo="Your photo: the shop counter at opening time" data-aspect="4:3"
  alt="…">`. It renders as a labeled striped block. Use at most 2–3 slots; never build the page around them.
- **Never** hotlink web images, never use stock photography, and never generate photos unless the user
  explicitly asks for generated photos (then run `scripts/photos.py`).

### Icons — almost never
Generic line icons are the most recognizable AI-template tell: a heart, clock, house, chat bubble, calendar,
shield or star in a tinted rounded square above every feature; a sparkle or icon in front of every badge,
label, list item or stat; checkmark bullets everywhere.
- **Don't decorate with icons.** No icon tiles, no icon-before-every-label, no icon bullets, no icon in pills
  or eyebrow labels, no star/heart/sparkle ornaments, no icon libraries (Lucide, Heroicons, Font Awesome,
  Material Icons, Feather, Phosphor). Let typography, numbers, color and layout carry meaning.
- **Functional icons only, in interfaces:** navigation, buttons and inputs in apps and tools (play, search,
  close, settings, arrows) — small (16–20px), one consistent stroke, never inside colored tiles.
- **When a visual would genuinely help, draw something specific** to this brand as part of the art direction
  (the clinic's yellow front door, a sardine tin, a kiln) at a meaningful size — not a symbol standing in
  for an idea.
- Instead of icon bullets use numbers, en dashes, small caps labels or plain well-spaced text.

### Graphics craft
- One style per page: same stroke width (e.g. 1.5 or 2px, `stroke-linecap: round`), same corner logic,
  colors only from the palette, consistent level of detail.
- Draw specific things for this brand (a sardine tin, a kiln, a route map, the dashboard) — no generic blobs,
  waves, abstract gradients, floating 3D shapes or clip-art people.
- Keep each SVG under ~60 lines with a `viewBox`, scale it with CSS, `aria-hidden="true"` when decorative.
  Never repeat long path data; build patterns with `<pattern>` or CSS backgrounds.
- Graphics should do work: explain a process, show the product, carry the hero. Decoration alone is noise.

## Craft checklist (look at the screenshot)
- Is there one clear focal point above the fold?
- Does spacing have rhythm — tight within groups, generous between sections?
- Do edges align to a grid? Is anything floating?
- Is body text comfortably readable (contrast ≥ 4.5:1, size, measure)?
- Would a design director believe a studio made this for this specific brand?


The user's **House rules** in their taste file override everything in this file.
