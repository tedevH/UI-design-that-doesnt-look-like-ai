# UI design that doesn't look like AI

A Claude Code skill that designs websites and landing pages the way a design studio would — and learns
**your** taste from every design you pick.

Ask Claude Code something like *"design a landing page for a natural wine bar in Lisbon"*. The skill:

1. **Reads your taste** — rules learned from your past picks override its defaults.
2. **Designs two directions** in different style families (editorial serif, Swiss minimal, warm crafted,
   playful color, quiet luxury, photo-led, product UI, expressive) — one you tend to like, one you haven't
   seen much, so your taste keeps getting tested.
3. **Builds, renders and checks** each page: overlapping text, chunky fonts, AI clichés (purple gradients,
   glass panels, emoji icons, "unlock your potential"), flat type scales. Claude also looks at its own
   desktop and mobile screenshots and fixes what it sees before you do.
4. **Adds photos** made for the page (optional): free on your Mac, or fast through Gemini.
5. **Asks which you prefer and why** — and keeps looping: the winner gets refined against one challenger
   that tests one thing about your taste, until you're happy.
6. **Learns.** Every reaction is recorded; every 5, Claude rewrites your taste rules from all the evidence.
   Your taste lives in `~/.claude/ui-design-data/taste/` with its own history, so updates to the skill never
   touch it and any change can be undone.

## Install

As a plugin (inside Claude Code):

```
/plugin marketplace add tedevH/UI-design-that-doesnt-look-like-ai
/plugin install ui-design@tedevh-design
```

Or as a plain skill:

```bash
git clone https://github.com/tedevH/UI-design-that-doesnt-look-like-ai ~/.claude/ui-design-skill
ln -s ~/.claude/ui-design-skill/skills/ui-design ~/.claude/skills/ui-design
```

The first time it runs, Claude runs `scripts/setup.sh` (about 2 minutes) and asks how to make photos:

| Mode | Speed | Cost | Needs |
|---|---|---|---|
| `local` | ~30–40 s per photo | free | Apple Silicon Mac, ~10 GB download (FLUX.1-schnell, Apache-2.0) |
| `gemini` | ~10 s per photo | ~$0.03 per photo | `GEMINI_API_KEY` |
| `none` | instant | free | — pages keep labeled photo slots |

Requirements: Python 3.10+ and Claude Code. Re-run `bash scripts/setup.sh` any time to change the photo mode.

## What's inside

```
skills/ui-design/
  SKILL.md                    the workflow Claude follows
  references/rules.md         type, color, layout, content and imagery rules; the AI-cliché bans
  references/families.md      eight style families, with notes on strong real sites in each
  references/taste-template.md   the blank taste every user starts from
  scripts/                    taste, check, photos, feedback, evolve, setup (+ a small renderer and detector)
```

## Where this came from

The `research` branch has the pipeline used to build this: scraping ~190 well-designed and corporate sites,
a vibecoded-page detector, a screenshot critic, style clustering, local-model fine-tuning experiments, and a
with/without-skill evaluation. The lessons from it are baked into `rules.md` and `families.md`; the skill
itself doesn't need any of it.
