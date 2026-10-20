# UI design that doesn't look like AI

A design skill for building and improving websites and app interfaces with product-specific art direction, deliberate composition, and careful implementation. It is for landing pages, software, dashboards, mobile screens, portfolios, editorial pages, shops, events, utilities, and small games.

The central idea is simple: a design should grow from the product, its audience, and the work a person came to do. A list of banned styles cannot make a page distinctive. This skill helps turn a brief into a visual premise, build that premise in the user's project, and critique the rendered result at desktop and mobile sizes.

## What it does

1. **Reads the project before designing.** It identifies the stack, existing visual language, available assets, and relevant screens, then works in that context.
2. **Finds a product-specific visual premise.** A short direction card connects audience, task, hierarchy, composition, visual system, interaction, responsive behavior, and restraint.
3. **Uses references as prompts, not templates.** Page-type guidance, product patterns, and style families help ask better questions without prescribing a stock layout. A complete Fieldnote dashboard specimen shows one direction carried through content, data, and responsive structure.
4. **Builds real content and behavior.** It prioritizes credible product UI, useful page content, working controls, truthful claims, and the assets the user actually has. An offline, typed knowledge graph connects task contexts to relevant patterns and checks; stack guides tailor implementation advice to common web and native platforms.
5. **Inspects rendered work.** The standalone HTML checker captures desktop and mobile screenshots, reports measurable layout/accessibility signals separately from subjective style signals, and saves a JSON report. It does not claim to judge beauty automatically.
6. **Learns the user's preferences.** Feedback can update a personal taste file without modifying the shared skill or skill reference files.

## Install

As a plugin inside Claude Code:

```text
/plugin marketplace add tedevH/UI-design-that-doesnt-look-like-ai
/plugin install ui-design@tedevh-design
```

Or as a plain skill:

```bash
git clone https://github.com/tedevH/UI-design-that-doesnt-look-like-ai ~/.claude/ui-design-skill
ln -s ~/.claude/ui-design-skill/skills/ui-design ~/.claude/skills/ui-design
```

Requirements: Python 3.10+ and Claude Code. The first visual check needs the optional Python and headless browser environment; install it from the skill directory:

```bash
bash scripts/setup.sh
```

To draft a product-specific plan and include implementation guidance for an existing stack:

```bash
python3 skills/ui-design/scripts/plan.py "Energy dashboard for a small facilities team" --stack react
python3 skills/ui-design/scripts/plan.py --list
```

The planner works offline using curated task contexts and bounded, directed graph traversal. Matches include evidence or a graph path and are relevance hints, not style assignments. Use `--graph-hops 0` for direct matches only. For standalone HTML visual checks:

```bash
python3 skills/ui-design/scripts/check.py ./page.html --type landing
```

Supported page types: `landing`, `app`, `mobile`, `portfolio`, `article`, `commerce`, `event`, `tool`, and `game`. The checker writes screenshots and `check.json` next to the input file. For an existing application, use its actual dev server and inspect the real route; the standalone checker is not a substitute for application-level visual review.

Generated photos are off by default. Optional photo generation can be configured with `bash scripts/setup.sh --photos local` or `--photos gemini`; see the setup script for requirements and cost details.

## What's inside

```text
skills/ui-design/
  SKILL.md                         workflow for art direction, implementation, and critique
  data/
    product-contexts.json          searchable product-task and interaction catalog
    knowledge/                     graph node catalogs, typed relationships, and relevance cases
    README.md                       catalog schema and editorial contribution rules
  references/
    stacks/README.md               stack guide index; separate files cover web and native platforms
    evaluation.md                 blind, repeatable comparison protocol
    page-types.md                  page-specific quality and structure prompts
    product-patterns.md            tasks, content, and interaction by product context
    quality-bar.md                 direction card, critique order, evaluation guidance
    families.md                    optional visual vocabulary and references
    rules.md                       practical design and implementation guidance
    beauty.md                      composition, image, type, and visual craft
    taste-template.md              starter preferences for a new user
  examples/
    brief-to-direction.md          worked example from request to responsive design decisions
    showcase/tide-station.html     complete data-led responsive interface specimen
    showcase/README.md             direction notes and sample-data caveat
  scripts/
    check.py                        standalone render, measurements, and style signals
    plan.py                         offline task retrieval, bounded graph traversal, and brief generator
    knowledge.py                    field-weighted search and evidence-carrying traversal loop
    validate_knowledge.py           catalog, edge, path, and relevance validator
  tests/
    test_knowledge.py               dependency-free planner and graph checks
    lib/audit.py                    objective layout and accessibility signals
    lib/tells.py                    subjective heuristics for human review
    taste.py, feedback.py, evolve.py personal preference workflow
    setup.sh, photos.py             optional environment and photo tools
```

## Quality and limits

The checker can report things such as horizontal overflow, broken images, missing accessible names, and possible contrast issues. It also detects patterns that merit a human look. Those style signals are not pass/fail rules: a centered hero, serif typeface, icon library, gradient, or card grid can be exactly right for a particular brief.

A polished result still requires looking at the actual render and judging purpose, identity, hierarchy, composition, specificity, coherence, rhythm, responsive behavior, and finish. For meaningful comparisons, follow `references/evaluation.md`: hold the brief and implementation context constant, anonymize outputs, and compare the renders independently against the same rubric. The included dashboard is an illustrative specimen with fictional readings; it is not evidence of user preference or product performance. Its browser visual review is still pending.

## Research

The `research` branch contains experiments behind the project, including site analysis, style clustering, and evaluation work. Those experiments informed the references, but the installed skill uses its own small rendering and feedback workflow.
