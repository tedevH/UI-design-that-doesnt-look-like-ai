# Vue

Use this when the project already uses Vue. Follow the existing component API style, router, store, and styling approach.

## Shape the implementation

- Keep component props and emitted events explicit; avoid hiding important data flow in broad global state.
- Use computed values for derived presentation and keep watchers for side effects that cannot be expressed as derivation.
- Keep keys stable in `v-for` when rows can change order or state.
- Prefer native interactive elements and use the existing form and validation conventions.
- Scope styles where the project does; check global selectors before changing shared tokens.

## Responsive and accessible behavior

- Connect labels to inputs and ensure custom selects, menus, and tabs retain keyboard behavior.
- Make conditional content announce or expose its state through the right native or ARIA semantics.
- Include loading, empty, invalid, and completion states for data-driven components.

## Review

Inspect the route in the project's app, not an isolated component screenshot. Test a narrow viewport and the interactive states the component introduces.
