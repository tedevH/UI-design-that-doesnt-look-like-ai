---
name: ui-design
description: Design, build, critique, or improve websites and app interfaces with product-specific art direction, strong visual hierarchy, and careful responsive execution. Use for marketing pages, software, mobile screens, portfolios, editorial pages, shops, events, tools, games, or feedback on a design made with this skill.
---

# UI design with a point of view

Make interfaces that feel designed for this product, this audience, and this moment. The goal is not to avoid a list of visual clichés. The goal is to make a clear idea visible in the page, then execute it with enough hierarchy, detail, and restraint that the idea feels inevitable.

Use the references in this skill as a working library, not a template catalog. A style label, font pairing, or checklist cannot replace a strong composition.

## What good work looks like

A strong result has:

- **A specific premise.** A person should be able to describe what makes this page belong to this product.
- **A clear first read.** The most important message or task is obvious, and secondary material has a deliberate order.
- **A memorable visual move.** One image, product scene, typographic gesture, data view, or composition gives the page its identity.
- **A coherent visual system.** Type, color, spacing, surfaces, imagery, and interaction all support the same idea.
- **Real content.** The page shows the product, work, offer, schedule, or information people came to see.
- **Careful behavior at real sizes.** Desktop and mobile feel composed, readable, and usable; mobile is not just a squeezed desktop.
- **Craft without decoration for its own sake.** Every visual detail has a job.

A page can be quiet, dense, playful, austere, bright, or dark. Do not force an overlap, a bright color block, a centerpiece illustration, animation, a serif headline, or a card grid when the brief does not call for it.

## Workflow

### 1. Read the brief and the project

For a project that already exists, inspect its structure before choosing a solution:

- Identify the framework, routes, existing components, tokens, fonts, and conventions.
- Look at the actual screen or page being changed, plus nearby pages that establish the product's visual language.
- Find available logos, photography, product screenshots, copy, and other brand assets.
- Keep working interactions and reuse the parts that already fit. Do not replace an existing app with a detached demo unless the user asks for a standalone concept.

For a standalone design, choose the simplest useful format. A single HTML file is a good preview format when there is no existing app to extend.

Script paths in this guide are relative to the skill directory. Run a script from that directory or use its full path. If a visual check reports that Playwright or Chromium is missing, run `bash scripts/setup.sh` once from the skill directory.

Decide the page type from the user's goal, not from visual appearance alone. Read the relevant section of `references/page-types.md`. For product-specific content and interaction, consult `references/product-patterns.md`; use it to identify what the user must see and do, never as a template. Infer ordinary missing details; ask only when a decision would materially change the design or required functionality.

### 2. Find the visual idea

Read the user's taste with `python3 scripts/taste.py`. User house rules and learned preferences take precedence. For a first-time user, choose a direction from `references/families.md` only if it helps. Treat families as ingredients, not fixed kits.

Write a short internal art direction before building. It should answer:

1. **Who is this for, and what should they feel or do?**
2. **What is the one idea that makes this page specific to this product?**
3. **What should the eye notice first, second, and third?**
4. **What visual form can express that idea best?** Consider the actual product UI, a supplied photograph, a custom illustration, a diagram, typography, data, material, or a combination.
5. **What is the restraint that keeps the page coherent?** For example, an unusual composition with quiet color, or vivid color with simple type.

Avoid choosing a design by stacking adjectives such as “modern, clean, premium.” Translate each useful adjective into a visible choice. “Premium” might mean a narrow palette, generous image scale, precise type, and tactile print detail; it does not automatically mean a serif and gold accents.

Do not make competing directions by default. Make one confident direction. When the user asks to compare, make a second direction that tests one meaningful variable, such as composition, image treatment, or density. Keep the content and quality level comparable.

### 3. Set the design system

Use the direction card in `references/quality-bar.md` when it helps the user understand or approve a direction. Keep it specific and useful; do not print a long token report for routine work.

- **Concept:** one sentence that states the page's visual premise.
- **Hierarchy:** the first, second, and third things a viewer should notice.
- **Composition:** the primary layout, focal area, proportions, and how the page changes as it scrolls.
- **Type:** chosen roles and behavior for display, reading, interface, and data text; use weights and sizes intentionally.
- **Color and surface:** palette roles, contrast, material, borders, shadows, and where restraint matters.
- **Image or graphic:** what the major visual shows, why it belongs, and how it is made or sourced.
- **Interaction:** the main action, meaningful states, and motion only where it improves feedback or atmosphere.
- **Responsive idea:** what reorganizes, disappears, or changes priority on small screens.
- **Avoid:** the few choices that would undermine this particular concept.

Choose tokens that serve the direction and implementation. Prefer a small role-based palette and a clear spacing/type scale. Reuse existing project tokens when they are good. Do not force exact universal values or a fixed palette size onto every brand.

### 4. Compose before decorating

Plan the page as a sequence of visual beats, not a stack of interchangeable sections. Decide what the opening screen communicates, where the focal object lives, how the next section changes the rhythm, and where practical information appears.

Give the focal area enough space and detail to carry its role. For software, show credible product UI rather than a marketing abstraction of it. For a service or shop, show the offer, object, place, or process. For editorial work, make the reading hierarchy and supporting material feel intentional.

Use contrast in more than color: scale, alignment, whitespace, density, crop, line, texture, shape, and pace can all create emphasis. Variation should be purposeful. Repeating the same section composition is as weak as changing every section without a reason.

A page does not need a large hero image. If the idea is typographic, data-led, or task-led, give that form the same level of care: choose its scale, framing, supporting detail, and relationship to the rest of the page.

### 5. Build for the user's context

- Follow the existing stack, design system, accessibility patterns, and code conventions when editing an app.
- For a new project with no stack, choose a simple maintainable approach that fits the request. Use standalone HTML only when it is the right deliverable.
- Use the user's assets and brand information first. Do not invent logos, testimonials, customer counts, prices, product claims, or personal details.
- When facts are missing, use clearly plausible sample content only where a mockup requires it; do not present fabricated claims as real.
- Use real interface text and meaningful states. Buttons should do what they say, forms should respond, and navigation should lead somewhere useful.
- Source imagery intentionally. Prefer provided assets or project assets. If external imagery is appropriate, use an image source allowed by the project and make the dependency clear. Do not hotlink random images. Never generate a photo unless the user asks for one.
- Create custom graphics when a specific visual needs one. Avoid generic blobs, floating shapes, and icon tiles as filler. Functional icons are fine when they improve recognition or navigation.
- Keep content and controls readable with keyboard navigation, visible focus, sufficient contrast, reduced-motion support, and touch-friendly targets.
- Do not remove a user's existing content or visual identity simply to make a cleaner concept.

### 6. Render and critique the actual result

Run the visual checker for standalone HTML:

```bash
python3 scripts/check.py <page.html> --type <landing|app|mobile|portfolio|article|commerce|event|tool|game>
```

For an existing project, use its available dev/build workflow and a browser to inspect the actual route. Use the most relevant local rendering or preview tools available. Do not treat source code inspection as visual QA.

Inspect both desktop and mobile screenshots. Judge the page against its art direction, not just against a detector's list:

**Art direction**
- Can you state the specific idea in one sentence?
- Does the opening screen communicate it at a glance?
- Is there a clear focal point and a useful first read?
- Does the page feel specific to this brand and task, or could it be swapped onto another product unchanged?

**Composition**
- Are scale, alignment, spacing, crop, and density intentional?
- Does the page have a visual rhythm as you scroll?
- Does mobile have its own hierarchy and workable controls?
- Is important content visible without clipping, collisions, or needless scrolling?

**Craft**
- Is type readable and expressive in the right places?
- Do color and surfaces support the concept and keep text legible?
- Are imagery and graphics crisp, coherent, and meaningful?
- Do interactions have useful states and feedback?
- Are accessibility and reduced-motion basics respected?

Use the critique order in `references/quality-bar.md` and fix the earliest consequential mismatch first: purpose, identity, hierarchy, composition, or specificity. Do not spend the fix pass polishing tiny details while the page still has no strong idea. Re-render after meaningful changes. Do not accept a clean detector report as proof of a beautiful page; do not add a visual flourish just to satisfy a checklist.

For HTML checks, look at both screenshots printed by `check.py`. Fix all serious measured issues and clear visual defects. A second check is appropriate after fixes. Keep the loop short and targeted; stop when the agreed visual direction is present and the design is coherent at the tested sizes.

### 7. Present the work

Show the actual result where possible: open the page or preview, and include desktop and mobile screenshots when useful. Briefly say what changed, name the concept, and mention any remaining placeholder or assumption. Ask one focused question when user feedback would guide a meaningful next pass.

If the user asks for changes, apply them in the existing direction. If they ask for alternatives, make one challenger that changes a named variable. Do not silently restart the design each round.

### 8. Learn from feedback

Record reactions, including partial feedback:

```bash
python3 scripts/feedback.py --brief "<brief>" --page <file> --family <id> --note "<user's words>"
```

For a choice between alternatives, record both with `--chosen`, `--rejected`, `--chosen-family`, and `--rejected-family`. Translate feedback into a short learned preference, not a one-off rule that overfits a single page. Newer explicit preferences replace contradictory older ones.

When `feedback.py` prints `EVOLVE`, read the evidence from `python3 scripts/evolve.py`, update the user's taste file based on repeated signals, then save it with `python3 scripts/evolve.py --commit`. Never modify the skill files while evolving a user's personal taste.

## Reference guide

- `references/page-types.md` — what visual quality means for different kinds of pages
- `references/product-patterns.md` — task, content, and interaction prompts by product context
- `references/quality-bar.md` — direction card, critique order, and evaluation guidance
- `examples/brief-to-direction.md` — worked example translating a request into content and responsive design decisions
- `references/families.md` — optional art-direction vocabulary and references
- `references/rules.md` — practical design and implementation defaults
- `references/beauty.md` — deeper composition, image, type, and visual craft guidance
- `scripts/taste.py` — read personal design preferences
- `scripts/check.py` — render and inspect a standalone HTML page
- `scripts/feedback.py` — record a user reaction
- `scripts/evolve.py` — review feedback and save taste updates
- `scripts/photos.py` — generate photos only when explicitly requested
- `scripts/setup.sh` — install the optional local rendering environment
