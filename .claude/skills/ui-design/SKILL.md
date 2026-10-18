---
name: ui-design
description: Design websites, landing pages and UI that look made by a real design studio, not AI-generated or template-like, and keep learning the user's taste from their picks. Use when asked to design, build, mock up, redesign or restyle a website, landing page, homepage, marketing page or UI screen, or when the user gives feedback on a design produced with this skill.
---

# UI design that doesn't look like AI

You are the designer. This skill gives you the user's taste, a set of distinct style families, the rules
that separate studio work from AI templates, and scripts that render and check your pages. Work like a
studio: commit to a direction, build it with care, look at the result, fix it, then let the user choose.

## 0. Read the user's taste first

Read `references/taste.md` before anything else. It holds rules learned from this user's past picks and
comments. **Learned rules override the defaults in this skill.** Lean toward families they pick often;
avoid what they rejected.

## 1. Understand the brief

From the request, write down (for yourself) the audience, tone (3–4 adjectives), the concrete content the
page must show (menu with prices, pricing table, schedule, product UI…), and what would feel wrong for
this brand. Invent plausible specifics — names, prices, places, numbers with units. Ask the user only if
something essential is truly unknowable.

## 2. Choose two directions

Read `references/families.md`. Pick **two different style families** that fit the brief — one the user's
taste favors, and one they haven't seen much (so their taste keeps getting tested). If the user named a
style, make both variants within it but with different art directions.

For each, write an art direction: a one-line concept, palette (3–6 hex colors with roles), Google Fonts
pairing **with weights**, photo style (lens, light, grade), 6–8 sections each with its own composition,
and one signature move.

## 3. Build each page

One self-contained HTML file per variant, in the user's project (default `designs/<slug>/a.html` and
`b.html`). Follow `references/rules.md` exactly. Photos are `<img data-photo="…" data-aspect="…">` slots,
never web links.

## 4. Photos

Run `scripts/photos.py <page.html>` — it generates every photo slot locally with FLUX (free, ~1 minute per
photo; tell the user it's working). If it reports that local generation isn't available, leave the slots;
they render as labeled blocks.

## 5. Check and fix (always, before showing anything)

Run `scripts/check.py <page.html>`. It renders desktop and mobile screenshots and reports measured
problems: overlapping text, chunky type, fake telemetry, gradients, emoji icons, clichés, flat type scale.

- Fix every reported problem.
- **Look at both screenshots yourself** (Read the PNG paths it prints) and critique them honestly against
  `references/rules.md` and the art direction: hierarchy, spacing rhythm, alignment, contrast, whether it
  looks like a studio made it. Fix what you see.
- Re-run the check. Stop after it's clean and you'd be proud to show it (max 3 passes).

## 6. Present and ask

Show both variants: screenshot paths (desktop and mobile), the family and concept of each in one line, and
anything you're unsure about. Then ask the user **which one they prefer and why**, and whether anything
should change. Keep it to one question.

## 7. Learn from the answer (every time the user reacts)

Record it, even partial feedback ("A, but the font is too thin"):

```bash
scripts/feedback.py --brief "<brief>" --chosen <page that won> --rejected <page that lost> \
  --chosen-family <id> --rejected-family <id> --note "<the user's words>"
```

Use `--chosen`/`--rejected` only for a real pick; for comments on a single page use `--page <file> --note`.
The script logs the preference and refreshes the statistics in `references/taste.md`.

Then edit the **Learned rules** section of `references/taste.md` yourself: turn the user's comment into a
short, general rule ("Prefers serif display type over grotesk for hospitality", "Never use centered
heroes"). Merge with existing rules instead of duplicating; if a new comment contradicts an old rule, the
newer one wins — rewrite it. Keep at most 30 rules, most important first.

If they asked for changes, apply them to the chosen page, re-run the checks, and show it again.

## 8. Keep looping until the user is happy

This skill is a loop, not a one-shot. After recording feedback, immediately start the next round unless the
user says they're done (or only asked for one page):

- **Round 1:** two different families (step 2).
- **Next rounds:** keep the winner and push it further using the feedback, and pit it against **one
  challenger** that tests a single open question about the user's taste — a different type pairing, a
  bolder or quieter palette, denser or airier layout, photos vs illustration. Change one thing in the
  challenger so the pick teaches something specific. Say in one line what the challenger is testing.
- Re-read `references/taste.md` at the start of every round; it changed.
- Stop when the user says it's done, picks the same page twice with no changes, or asks to stop. Then hand
  over the final page and its screenshots.

## 9. Evolve the skill itself

`feedback.py` prints **EVOLVE** every 5 reactions. When it does, run `scripts/evolve.py` and follow its
instructions: it summarizes all the evidence (win rates per family, recurring comments, what the checks keep
catching), and you then edit this skill's own files so future designs start closer to the user's taste:

- `references/taste.md` → tighten the Learned rules (merge, reorder by evidence, drop rules contradicted
  by later picks) and update the **Family priority** list.
- `references/rules.md` → add any rule the user has confirmed at least twice to the **House rules learned
  from the user** section; never delete the original rules, only add or override.
- Then run `scripts/evolve.py --commit` to commit the changes with a summary, so every change to the skill
  is tracked in git and can be reverted.

Never change the scripts' behavior or remove safety checks while evolving — only taste, rules and
priorities.

## Scripts

All scripts locate the notai project themselves; run them with any Python (they re-launch inside the
project's virtual environment).

- `scripts/check.py page.html` — render + measured problems + screenshot paths
- `scripts/photos.py page.html [--style "..."]` — fill photo slots with local FLUX photos
- `scripts/feedback.py ...` — record a preference and refresh taste statistics
- `scripts/evolve.py [--commit]` — summarize all evidence for a self-update; `--commit` records it in git
