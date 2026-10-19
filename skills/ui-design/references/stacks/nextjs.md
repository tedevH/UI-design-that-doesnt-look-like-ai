# Next.js

Use this when the project is already on Next.js. Preserve its routing model, server/client boundaries, data conventions, and installed component system.

## Shape the implementation

- Keep pages and layouts aligned with the existing App Router or Pages Router structure; do not migrate routing as a side effect of a visual change.
- Prefer server-rendered content where interaction is not needed. Add client components only around behavior that needs browser state or events.
- Avoid pulling large client-only dependencies into a mostly static page.
- Keep metadata page-specific and use the framework's established image, font, and navigation patterns where the project already relies on them.
- Treat loading, not-found, error, and empty routes as part of the design where relevant.

## Responsive and accessible behavior

- Verify focus and state across client transitions, dialogs, and navigation.
- Keep essential content available without animation or delayed client hydration.
- Avoid layout shift from late fonts and media; preserve meaningful dimensions and responsive crops.

## Review

Run the existing project route and build workflow. Check both the route and any shared layout that changed. Do not validate a Next.js screen by exporting an unrelated standalone mockup.
