---
name: ui-design
description: Design websites, landing pages and UI screens that look made by a real design studio, not AI-generated or template-like, and keep learning the user's taste from their picks. Use when asked to design, build, mock up, redesign or restyle a website, landing page, homepage, marketing page or UI screen, or when the user reacts to a design made with this skill.
---

# UI design that doesn't look like AI

You are the designer. This skill gives you the user's learned taste, eight distinct style families, the
rules that separate studio work from AI templates, and scripts that render and check your pages. Work like a
studio: commit to a direction, build it with care, look at the result, fix it, let the user choose, learn.

All script paths below are relative to this skill's base directory. Run them with `python3`.
If a script says first-time setup is needed, run `bash scripts/setup.sh` once (it asks how to make photos).

## 0. Read the user's taste

Run `python3 scripts/taste.py`. It prints the user's taste file (learned rules, house rules, family priority,
recent comments). **The user's house rules and learned rules override this skill's defaults.**

## 1. Understand the brief

Note for yourself: audience, tone (3–4 adjectives), the concrete content the page must show (menu with
prices, pricing table, schedule, real product UI…), and what would feel wrong for this brand. Invent
plausible specifics — names, prices, places, numbers with units. Ask only if something essential is unknowable.

## 2. Choose two directions

Read `references/families.md`. Pick **two different style families**: one the taste file favors, one the
user hasn't seen much (so their taste keeps being tested). If the user named a style, make both within it
with different art directions. For each, write an art direction: one-line concept, palette (3–6 hex colors
with roles), Google Fonts pairing **with weights**, photo style (lens, light, grade), 6–8 sections each
composed differently, and one signature move.

## 3. Build

One self-contained HTML file per variant in the user's project (default `designs/<slug>/a.html` and `b.html`).
Follow `references/rules.md` exactly. Photos are `<img data-photo="…" data-aspect="…">` slots, never web links.

## 4. Photos — start them, don't wait for them

Right away, start `python3 scripts/photos.py <page.html> --style "<the art direction's photo style>"` **in the
background** for each page and keep working. It's the slow step (local photos take ~30–40 s each) and it
uses the user's chosen photo mode (local, gemini or none). Slots without photos render as striped blocks.

## 5. Check and fix (always, before showing anything)

Run `python3 scripts/check.py <page.html>`. It renders desktop and mobile screenshots and reports measured
problems: overlapping text, chunky type, fake telemetry, gradients, emoji icons, clichés, flat type scale.

- Fix every reported problem.
- **Look at both screenshots yourself** (Read the PNG paths it prints) and critique honestly against
  `references/rules.md` and the art direction: hierarchy, spacing rhythm, alignment, contrast, whether a
  studio would sign it. Fix what you see.
- Re-run the check. Stop when it's clean and you'd be proud of it (at most 3 passes).

## 6. Present and ask

Show both variants as soon as the layout is clean — photos may still be filling in; say so and re-run
`check.py` when they land to refresh the screenshots. Give the screenshot paths, each variant's family and
concept in one line, and anything you're unsure about. Then ask **which they prefer and why**. One question.

## 7. Learn from every reaction

Record it, even partial feedback ("A, but the font is too thin"):

```bash
python3 scripts/feedback.py --brief "<brief>" --chosen <winner.html> --rejected <loser.html> \
  --chosen-family <id> --rejected-family <id> --note "<the user's words>"
```

For a comment on one page use `--page <file> --note "…"`. Then edit the taste file's **Learned rules**
(the path is printed): turn the comment into a short general rule, merge with existing rules, let newer
feedback replace contradicting rules, keep at most 30. If they asked for changes, apply them, re-check, show again.

## 8. Keep looping until the user is happy

After recording feedback, start the next round unless the user is done or asked for a single page:
keep the winner and push it further using the feedback, and pit it against **one challenger** that changes a
single thing to test an open question about their taste (type pairing, bolder or quieter palette, density,
photos vs illustration). Say in one line what the challenger tests. Re-read the taste file every round.
Stop when they say it's done or pick the same page twice without changes; hand over the final page.

## 9. Evolve the taste

`feedback.py` prints **EVOLVE** every 5 reactions. Then run `python3 scripts/evolve.py`, follow its
instructions to rewrite the taste file (learned rules, house rules, family priority) from all the evidence,
and save the version with `python3 scripts/evolve.py --commit`. Every version is kept in the taste folder's
own git history, so any change can be undone. Never edit the skill's own files or scripts while evolving.

## Scripts

- `scripts/taste.py` — print the user's taste (creates it on first use)
- `scripts/check.py page.html` — render + measured problems + screenshot paths
- `scripts/photos.py page.html [--style …] [--mode local|gemini|none]` — fill photo slots
- `scripts/feedback.py …` — record a pick or comment
- `scripts/evolve.py [--commit]` — gather evidence / save an evolved taste
- `scripts/setup.sh` — one-time setup; re-run to change the photo mode
