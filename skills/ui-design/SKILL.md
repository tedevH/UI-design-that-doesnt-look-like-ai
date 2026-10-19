---
name: ui-design
description: Design beautiful websites and app interfaces that look made by a real design studio, not AI-generated or template-like, and keep learning the user's taste from their picks. Use when asked to design, build, mock up, redesign or restyle a website, landing page, web or mobile app screen (study app, dashboard, planner, tracker), portfolio, blog or docs page, shop page, event page, tool or small game, or when the user reacts to a design made with this skill.
---

# UI design that doesn't look like AI

You are the designer. This skill gives you the user's learned taste, ten distinct style families, page-type
playbooks (landing pages, apps, mobile, portfolios, articles, shops, events, tools, games), the rules that
separate studio work from AI templates, a guide to making pages genuinely beautiful, and scripts that render
and check your work. Work like a
studio: commit to a direction, make its visuals yourself, build it with care, look at the result, fix it, let the user choose, learn.

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

## 2. Choose two directions

Read `references/families.md`. Pick **two different style families**: one the taste file favors, one the
user hasn't seen much (so their taste keeps being tested). If the user named a style, make both within it
with different art directions. For each, write an art direction: one-line concept, palette (3–6 hex colors
with roles), Google Fonts pairing **with weights**, the **graphic language** (what you'll draw — illustration
style, patterns, diagrams, product UI — and its stroke, detail and color rules), 6–8 sections each composed
differently, the **centerpiece visual** (see `references/beauty.md` §1), and one signature move. Skip the
photo-led family unless the user gave you their own photos.

## 3. Build

One self-contained HTML file per variant in the user's project (default `designs/<slug>/a.html` and `b.html`).
Follow `references/rules.md` (the floor) **and** `references/beauty.md` (the ceiling). Build the centerpiece
first and give it real care — it's what makes the page. Draw visuals yourself (inline SVG, CSS, typography,
product UI in HTML); use the user's photos if they gave any; no stock or generated photos. Apps, tools and
games must actually work.

## 4. Imagery

Graphics first (see "Imagery" in `references/rules.md`). If the user gave you their own photos, use them with
relative paths. If a section truly needs a photo only the client has (their team, their venue), leave a
labeled slot — `data-photo="Your photo: …"` — at most 2–3 per page, and tell the user what to send.
Only if the user explicitly asks for generated photos, run `python3 scripts/photos.py <page.html> --style
"…"` in the background (local ≈ 30–40 s per photo) and keep working.

## 5. Check, fix, then make it beautiful (always, before showing anything)

Run `python3 scripts/check.py <page.html> --type <page type>`. It renders desktop and mobile screenshots and
reports measured problems: overlapping text, chunky type, fake telemetry, AI gradients, emoji icons,
clichés, stock photos, flat type scale.

1. Fix every reported problem.
2. **Look at both screenshots yourself** (Read the PNG paths it prints) and fix what's off: hierarchy,
   spacing rhythm, alignment, contrast, mobile layout.
3. **Beauty pass:** go through the checklist at the end of `references/beauty.md` against the screenshot and
   fix every "no" — centerpiece, depth, color moment, expressive type, texture, motion. If it's merely tidy,
   push the centerpiece and color further.
4. Re-run the check and look again. Stop when it's clean and you'd genuinely be proud to ship it (at most
   3 passes).

## 6. Present and ask

Show both variants once they're clean. Give the screenshot paths, each variant's family and
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
- `scripts/check.py page.html --type <type>` — render + measured problems + screenshot paths
- `scripts/photos.py page.html [--style …] [--mode local|gemini]` — generated photos, only when asked
- `scripts/feedback.py …` — record a pick or comment
- `scripts/evolve.py [--commit]` — gather evidence / save an evolved taste
- `scripts/setup.sh` — one-time setup; re-run to change the photo mode
