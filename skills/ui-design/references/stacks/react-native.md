# React Native

Use this when the project already uses React Native. Follow the existing navigation, component library, styling, and platform-specific conventions.

## Shape the implementation

- Use native controls and platform conventions where they fit; account for iOS and Android differences rather than forcing pixel parity.
- Respect safe areas, keyboard avoidance, status/navigation bars, and the project's navigation model.
- Keep state and list identity stable; use the project's established list virtualization for long content.
- Avoid web-only assumptions such as hover as the sole feedback or browser-specific semantics.

## Responsive and accessible behavior

- Support font scaling and dynamic text lengths; do not hard-code content heights.
- Provide accessible labels, roles, hints, and selected/disabled states for custom controls.
- Check tap areas, focus behavior with hardware keyboards, and screen-reader order.
- Make loading and offline states visible when network access is part of the task.

## Review

Inspect on both iOS and Android when the change uses platform-sensitive behavior. Include small and large devices and keyboard-visible states when forms are involved.
