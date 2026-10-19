# SvelteKit

Use this when the project already uses SvelteKit. Preserve its route structure, form actions, load functions, and server/client boundaries.

## Shape the implementation

- Keep route data loading and form submission in the conventions already used by the project.
- Use component state for local interaction; do not move server-owned data into client state without a reason.
- Use semantic elements and native form behavior as the default.
- Keep reactive statements understandable and avoid duplicating derived values.
- Preserve the project's transition and styling conventions; a transition should clarify a state change, not delay task completion.

## Responsive and accessible behavior

- Make pending, invalid, success, and empty states explicit for forms and asynchronous content.
- Preserve focus and provide keyboard-operable menus, dialogs, and toggles.
- Check that conditional blocks do not cause abrupt layout shifts or lose a user's entered values.

## Review

Run the actual SvelteKit route and inspect desktop and mobile rendering. Exercise server actions and navigation affected by the change.
