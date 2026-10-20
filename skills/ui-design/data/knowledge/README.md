# Connected design knowledge

These catalogs describe reusable composition patterns, visual approaches, chart choices, and UX checks. `product-contexts.json` supplies task-centered entry points. Nodes live in separate JSON catalogs; all relationships live in `edges.json` so edge meaning and traversal direction can be reviewed in one place.

## Graph loop

1. **Retrieve direct evidence.** Normalize and cap the query at 96 distinct terms. Search title, aliases, tags, summary, and supporting product context with different field weights and inverse document frequency. Exact multi-word matches receive a small bonus. A phrase match remains evidence of topical relevance, never quality.
2. **Choose seed nodes.** Keep up to five strong candidates, with no more than two per domain. A selected `--context` is pinned as a seed even when the brief has little lexical overlap.
3. **Traverse in rounds.** Follow directed, typed edges for up to three hops and 36 examined edges. Each relation has an explicit source/target domain, readable label, and decay weight. Cycles are blocked within a path; duplicate destinations keep their strongest route.
4. **Explain and balance results.** Product nodes guide traversal but are omitted from connected recommendations because the planner already prints the selected product context. Other results show matched fields/terms or a human-readable path. Results are capped by `--top` and at two per domain. Weak queries can return no graph recommendations.

The implementation uses only the Python standard library and small local JSON catalogs. It loads and indexes the graph once per process, makes no network requests, and does not recursively explore without bounds. `--graph-hops 0` returns direct knowledge matches only; the default is three hops.

## Data contract

Every node has a globally unique ID, domain, title, summary, and searchable tags (product nodes are assembled from `product-contexts.json`). Every edge has `from`, `to`, and a relation ID from `edges.json`. A relation defines allowed source and destination domains, a user-readable label and description, and a traversal weight in `(0, 1]`. Edges are directed: the reverse route exists only when it is explicitly authored.

Add relationships for a real task connection, not just to make the graph appear dense. Every product context needs at least one outgoing edge. Avoid duplicate routes that say the same thing, generic tags, universal style claims, and fabricated product evidence. Keep source data and implementation guidance in their appropriate catalogs.

## Validation

From the skill directory run:

```bash
python3 scripts/validate_knowledge.py
python3 -m unittest discover -s tests -v
```

The validator checks global ID uniqueness, schemas, edge endpoints and domain direction, all product-context links, relevance, graph-only paths, weak-match behavior, and multi-intent cases. Its recall, MRR, and timing figures describe this small retrieval fixture only; they do not measure visual or design quality.
