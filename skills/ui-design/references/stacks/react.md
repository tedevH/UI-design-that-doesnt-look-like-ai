# React

Use this when the project already uses React. Follow the repository's existing router, styling, component, and state conventions before adding new abstractions.

## Shape the implementation

- Build components around meaningful UI responsibilities or repeated behavior, not every wrapper element.
- Keep data and state ownership clear. Derive display values from source state instead of maintaining duplicate state.
- Use stable keys for mapped content. Avoid index keys when items can reorder or be inserted.
- Use native elements and labels; add ARIA only when native semantics do not express the required behavior.
- Keep event handlers attached to the control that owns the action and provide a visible result for every action.

## Responsive and accessible behavior

- Preserve focus when dialogs, menus, or conditional panels open and close; support keyboard dismissal when appropriate.
- Handle loading, error, empty, and success states as interface states, not just network conditions.
- Avoid broad global CSS changes when the project has scoped styles or tokens.
- Test long content, lists, validation messages, and responsive layouts, not only the first viewport.

## Review

Use the project's actual dev server and route. Inspect the rendered component at desktop and mobile sizes and exercise its interactions; source-only review cannot establish visual quality.
