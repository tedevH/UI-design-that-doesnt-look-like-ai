# SwiftUI

Use this when the project already uses SwiftUI. Respect its navigation, state, data, and design-system conventions.

## Shape the implementation

- Prefer native SwiftUI controls and platform behaviors unless the brief calls for a custom interaction.
- Keep view composition focused; extract subviews where they improve reuse, previewing, or state clarity.
- Make state ownership explicit and avoid duplicated sources of truth.
- Use system semantic colors and type roles when the app follows platform conventions; introduce custom tokens only when the brand needs them.
- Use native navigation and presentation patterns instead of imitating web navigation inside a native app.

## Responsive and accessible behavior

- Support Dynamic Type and check that controls expand for larger text.
- Add accessibility labels and values to custom-drawn controls; ensure reading order matches visual order.
- Respect safe areas, keyboard appearance, reduced motion, and platform contrast settings.
- Keep touch targets comfortable and make destructive actions clear and recoverable.

## Review

Preview representative device sizes and larger text settings. Exercise navigation, sheets, keyboard entry, and any custom control in the running app.
