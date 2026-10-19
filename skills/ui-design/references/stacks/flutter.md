# Flutter

Use this when the project already uses Flutter. Preserve its routing, state-management, theming, and widget conventions.

## Shape the implementation

- Use Material or Cupertino widgets according to the product's platform and visual intent; don't mix them without a reason.
- Keep reusable widgets parameterized around meaningful behavior and data, not long lists of style flags.
- Use the existing theme for semantic colors, type, and shapes.
- Prefer constraints and flexible layout to fixed pixel dimensions; use lazy builders for long lists.

## Responsive and accessible behavior

- Check text scaling, platform safe areas, keyboard insets, and narrow device widths.
- Use semantic labels and ensure custom-painted content has an accessible description or equivalent text.
- Support focus traversal and keyboard input for desktop/web targets when those are in scope.
- Make asynchronous, empty, and error states legible and recoverable.

## Review

Preview the actual target platforms and text scales. Verify navigation, keyboard behavior, and high-contrast or reduced-motion settings where supported.
