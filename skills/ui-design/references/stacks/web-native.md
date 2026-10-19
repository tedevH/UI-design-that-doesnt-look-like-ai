# Native HTML, CSS, and JavaScript

Use this when the project is a small standalone page, a prototype that needs no build system, or an existing site already using browser primitives.

## Shape the implementation

- Use semantic landmarks (`header`, `nav`, `main`, `section`, `footer`) and native controls before adding custom roles.
- Keep structure, visual tokens, and interaction code easy to inspect. For a compact standalone example, one HTML file can be appropriate; move CSS and scripts out when the page grows.
- Prefer CSS Grid and Flexbox for layout; use absolute positioning for intentional overlays, not primary page structure.
- Use custom properties for the small set of semantic roles: text, surfaces, borders, accent, spacing, and type.
- Use native form constraints where useful, then provide nearby, specific error feedback.

## Responsive and accessible behavior

- Build around content fit and intrinsic sizing; use `minmax(0, 1fr)`, `min-width: 0`, and sensible wrapping for dense children.
- Preserve heading order and visible keyboard focus. Do not remove outlines without a strong replacement.
- Respect `prefers-reduced-motion`; avoid motion as the only carrier of status or meaning.
- Check zoom, narrow widths, long labels, empty states, and unavailable assets.

## Review

Inspect the actual rendered page at a wide and narrow viewport. Verify navigation anchors, form submission feedback, control names, contrast, and overflow. A static checker can spot signals but cannot verify intent or usability.
