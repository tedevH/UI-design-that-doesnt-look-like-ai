---
name: ui-design
description: Design beautiful websites and app interfaces that look made by a real design studio, not AI-generated or template-like, and keep learning the user's taste from their picks. Use when asked to design, build, mock up, redesign or restyle a website, landing page, web or mobile app screen (study app, dashboard, planner, tracker), portfolio, blog or docs page, shop page, event page, tool or small game, or when the user reacts to a design made with this skill.
---

# UI design that doesn't look like AI

You are the designer. This skill gives you the user's learned taste, ten distinct style families, page-type
playbooks (landing pages, apps, mobile, portfolios, articles, shops, events, tools, games), the rules that
separate studio work from AI templates, a guide to making pages genuinely beautiful, and scripts that render
and check your work. Work like a
studio: commit to a direction, make its visuals yourself, build it right the first time, check it once,
show it, learn from the reaction.

All script paths below are relative to this skill's base directory. Run them with `python3`.
If a script says first-time setup is needed, run `bash scripts/setup.sh --photos none` once (~2 minutes).

## 0. Read the user's taste

Run `python3 scripts/taste.py`. It prints the user's taste file (learned rules, house rules, family priority,
recent comments). **The user's house rules and learned rules override this skill's defaults.**

## 1. Understand the brief

First decide the **page type** and read its section in `references/page-types.md` — a study app is not a
landing page. Then note for yourself: who uses it, the tone (3–4 adjectives), the concrete content it must
show (the flashcard deck, the pricing table, the schedule, the real product UI…), and what would feel wrong.
Invent plausible specifics — names, numbers with units, real-looking data. Ask only if something essential
is unknowable.

## Speed

Aim for roughly the time a plain request would take, plus a minute for checking. Get it right while
writing instead of in loops: keep planning to a few lines in your head (no long written plans), write the
page once, then make small targeted `Edit`s — never rewrite the whole file to fix something. One design by
default; a second only when the user asks to compare.

## 2. Choose a direction

Skim `references/families.md` and pick **one** family — the one the taste file favors for this kind of
brief, or the best fit if there's no taste yet. Decide quickly: palette (3–6 hex), Google Fonts pairing with
weights, the graphic language, the **centerpiece visual** (`references/beauty.md` §1), and the sections.
If the user asks for options, make a second page in a clearly different family. Skip photo-led unless the
user gave you their own photos.

## 3. Build — right the first time

One self-contained HTML file (default `designs/<slug>/page.html`; `b.html` for a second direction). Write it
in a single pass with the whole bar in mind: `references/rules.md` (the floor) and `references/beauty.md`
(the ceiling) — a rich centerpiece, depth, one bold color moment, an expressive type moment, texture,
gentle motion. Draw visuals yourself (inline SVG, CSS, typography, product UI in HTML); no generic icons,
no stock or generated photos; use the user's photos if they gave any. Apps, tools and games must work.
If a section truly needs a photo only the client has, leave a labeled `data-photo="Your photo: …"` slot
(at most 2–3) and tell the user what to send. Generated photos only if the user explicitly asks
(`python3 scripts/photos.py <page> --style "…"`, run in the background).

## 4. One check, one fix pass

Run `python3 scripts/check.py <page.html> --type <page type>` (≈5 s). Then, in one pass:
- fix every problem it reports with small `Edit`s;
- Read the **desktop** screenshot once and fix what's clearly off — broken layout, a weak or missing
  centerpiece, poor contrast, something that looks templated (the beauty checklist in `beauty.md`, as a
  quick scan, not a separate round).

Re-run `check.py` only if it reported a `[!!!]` problem; otherwise you're done. Never more than two checks.

## 5. Present and ask

Show the page: the screenshot paths, the family and concept in one line, and anything you're unsure about.
Ask what they think — what to change, or whether they'd like a second direction to compare. One question.

## 6. Learn from every reaction

Record it, even partial feedback ("A, but the font is too thin"):

```bash
python3 scripts/feedback.py --brief "<brief>" --chosen <winner.html> --rejected <loser.html> \
  --chosen-family <id> --rejected-family <id> --note "<the user's words>"
```

Use `--chosen`/`--rejected` when they compared two pages; for a reaction to one page use
`--page <file> --family <id> --note "…"`. Then edit the taste file's **Learned rules**
(the path is printed): turn the comment into a short general rule, merge with existing rules, let newer
feedback replace contradicting rules, keep at most 30. If they asked for changes, apply them, re-check, show again.

## 7. Keep going until the user is happy

After recording feedback, apply their changes with targeted edits and show it again. When they want options
(or you're unsure what they'd like), make **one challenger** next to the current page that changes a single
thing — type pairing, bolder or quieter palette, density, illustration style — so their pick teaches
something specific. Say in one line what the challenger tests. Re-read the taste file every round.
Stop when they say it's done or pick the same page twice without changes; hand over the final page.

## 8. Evolve the taste

`feedback.py` prints **EVOLVE** every 5 reactions. Then run `python3 scripts/evolve.py`, follow its
instructions to rewrite the taste file (learned rules, house rules, family priority) from all the evidence,
and save the version with `python3 scripts/evolve.py --commit`. Every version is kept in the taste folder's
own git history, so any change can be undone. Never edit the skill's own files or scripts while evolving.

## Scripts

- `scripts/taste.py` — print the user's taste (creates it on first use)
- `scripts/check.py page.html --type <type>` — render + measured problems + screenshot paths
- `scripts/photos.py page.html [--style …] [--mode local|gemini]` — generated photos, only when asked
- `scripts/feedback.py …` — record a pick or comment
- `scripts/evolve.py [--commit]` — gather evidence / save an evolved taste
- `scripts/setup.sh` — one-time setup; re-run to change the photo mode
