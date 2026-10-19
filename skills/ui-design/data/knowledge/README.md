# Connected design knowledge

The JSON files in this directory are small, hand-authored catalogs, organized by what they help decide: composition patterns, visual approaches, charts, and UX checks. `product-contexts.json` remains the task-context catalog. Each record has a stable ID, title, summary, search tags, and explicit `connects` edges to related records.

The planner uses lightweight lexical retrieval over these records. It ranks a brief against all records, then follows at most one edge from the strongest matches. It does not walk the full graph, fetch remote data, load ML dependencies, or interpret rank as a quality score. This keeps lookup deterministic and inexpensive while exposing relationships between task, composition, visual form, and interaction.

Add a record only when it contributes distinct guidance. Prefer specific, actionable summaries and explicit edges over expanding tags to chase query matches. IDs are unique across all catalogs. Links must resolve. Keep advice stack-agnostic here; implementation-specific guidance belongs in `references/stacks/`.
