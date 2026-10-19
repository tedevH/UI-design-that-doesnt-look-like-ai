# Product context catalog

`product-contexts.json` is a small, offline index that helps a designer retrieve relevant task questions and content/state prompts from a short brief. It deliberately does not contain a visual style, color scheme, font prescription, or layout template for any industry.

## Record shape

Each context has a stable `id`, a human-readable `title`, searchable `aliases`, and six arrays:

- `primary_tasks`: the user goals that should shape the experience;
- `decision_inputs`: questions that resolve an underspecified brief;
- `content_to_show`: information needed to make the interface credible and useful;
- `interaction_states`: states likely to matter for the task;
- `visual_opportunities`: possible ways to make relevant content carry visual identity;
- `common_misses`: risks worth checking for, not universal prohibitions.

The catalog is intentionally editorial and compact. Add a context when it contributes a distinct task model. Prefer enriching an existing context over adding near-duplicates. Use examples and qualifiers rather than making universal claims. Keep a clear distinction between verified product facts and mockup assumptions.

The planner uses lexical relevance ranking with match evidence. Scores are ranking signals only; they are not probabilities, recommendations of visual style, or a measure of design quality. Review the retrieved content against the user's actual product.

## Connected catalogs

Related patterns, visual approaches, chart choices, and UX checks live in [`knowledge/`](knowledge/README.md). Those files use stable IDs and explicit links. The planner ranks brief matches, then follows a bounded one-hop neighborhood; it does not load a large runtime or make a network request. Run `python3 scripts/validate_knowledge.py` from the skill directory to check schemas, links, and representative relevance cases, or `python3 -m unittest discover -s tests -v` for the planner contract checks.
