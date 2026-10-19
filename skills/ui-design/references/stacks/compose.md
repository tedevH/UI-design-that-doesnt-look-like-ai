# Jetpack Compose

Use this when the project already uses Jetpack Compose. Follow existing navigation, state-hoisting, Material, and design-token conventions.

## Shape the implementation

- Keep state ownership at the lowest common owner that needs it; expose events from reusable UI instead of hiding business logic in a leaf.
- Use lazy containers for long collections and stable item keys when identity matters.
- Use Material components when the product follows Material behavior; customize through the project's theme rather than ad hoc color and shape values.
- Prefer platform semantics and Compose modifiers for descriptions, roles, and state.

## Responsive and accessible behavior

- Use density-independent layout and account for system insets and the software keyboard.
- Support font scaling; avoid fixed heights that clip text.
- Make controls reachable by keyboard and screen reader, with coherent traversal and meaningful state announcements.
- Check compact and expanded device layouts instead of assuming one phone width.

## Review

Run the screen in representative emulator sizes and font scales. Inspect navigation, IME behavior, state restoration, and loading/error variants.
