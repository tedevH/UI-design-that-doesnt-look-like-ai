# Page types

Not everything is a business landing page. Identify the type first; it changes structure, density, copy and
what "beautiful" means. Pass the type to `check.py --type <type>` so it judges the right things.

## landing — marketing page for a business, product or project
Hero with a centerpiece, proof, what it is, how it works, details (menu, pricing, schedule), visit/contact.
Copy sells with specifics. 6–8 sections.

## app — a screen of a web app (study app, habit tracker, editor, inbox, planner, dashboard)
- Design **the app itself**, not a page about it: navigation (sidebar or tabs), the main working view, and
  the user's real data.
- Make it work: real interactions in vanilla JS — flashcards flip, the timer counts, tasks check off, tabs
  switch, a chart updates. Keep state in memory (and `localStorage` if useful).
- Show a believable, lived-in state: a named user, realistic content (actual vocabulary, real course names,
  dates relative to today), progress mid-way, one notification. Include one empty or completion state if there's room.
- Density is good when it's organized: clear hierarchy, aligned columns, consistent spacing, 13–15px UI text.
- Beauty comes from delight in the details: a satisfying progress ring, a streak flame drawn in SVG, card
  flip with a soft shadow, a calm color system for categories, a celebratory moment on completion.
- Study apps specifically: spaced repetition cues ("due today: 24"), a focus timer, decks or subjects with
  their own colors, a calm reading surface, keyboard shortcuts shown subtly (space to flip, 1–4 to grade).

## mobile — a phone app screen
Design at 390×844 inside a device-like frame centered on a soft background, or fill the viewport on mobile.
Thumb-reachable primary actions at the bottom, a tab bar, 16–17px body text, large touch targets (44px).
Show 2–3 key screens side by side on desktop if the brief is about the app as a whole.

## portfolio — a person's work or personal site
The work is the hero: large project tiles with drawn or typographic covers (or the person's own images),
a short sharp intro in their voice, selected projects with role/year/outcome, an about with personality,
contact. One signature interaction (hover reveals, a custom cursor label, an index list that previews).

## article — blog post, essay, newsletter, documentation page
Reading first: 65–72ch measure, 18–21px serif or humanist text, generous line-height, strong headings,
pull quotes, footnotes or sidenotes, figures with captions, a table of contents for long pieces. Docs add a
sidebar nav, code blocks with copy buttons, and callouts.

## commerce — a product or shop page
A large product visual (drawn, CSS-built, or the user's photos), variant selectors that work, price and
delivery clearly, details/specs in a calm table, reviews with substance, related items.

## event — event page, invitation, conference, wedding, party
The date, place and time unmissable; a strong poster-like centerpiece; schedule; people/speakers; how to get
there; RSVP that works (form with validation, confirmation state).

## tool — a single-purpose utility (calculator, converter, generator, timer)
The tool is the page: inputs and the live result above the fold, immediate feedback, sensible defaults,
copy/share actions, a short explanation below. Make the result the most beautiful thing on the page.

## game — a small playable or interactive piece
Playable on load, clear rules in one line, satisfying feedback (sound optional, motion yes), score and
restart, works with keyboard and touch.
