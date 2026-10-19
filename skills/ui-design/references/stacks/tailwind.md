# Tailwind CSS

Use this when the project already uses Tailwind. Follow its configured version, theme, utilities, and component conventions rather than assuming defaults.

## Shape the implementation

- Define project colors and type roles in the existing theme when they are reused; avoid scattering one-off values across a page.
- Use utilities for local composition and extract components only when there is a meaningful reuse or semantic boundary.
- Keep responsive variants readable. If a class string obscures the layout logic, use the project's established component or CSS pattern.
- Avoid arbitrary values that duplicate existing tokens. One intentional exception is better than several near-duplicates.
- Do not impose a universal radius, spacing scale, or default accent on a brand that already has a system.

## Responsive and accessible behavior

- Design from content constraints: allow titles, chips, buttons, and table cells to wrap or reflow.
- Use `focus-visible` states and preserve reduced-motion behavior.
- Check dark mode only when the project supports it; ensure both themes preserve semantic color roles.

## Review

Inspect computed styles and rendered states at the target widths. Utility classes can look plausible while container constraints or inherited styles still cause overflow.
