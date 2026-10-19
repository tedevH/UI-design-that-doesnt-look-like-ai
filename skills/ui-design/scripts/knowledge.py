"""Fast, offline retrieval over the UI design skill's connected catalogs."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = SKILL_DIR / "data" / "knowledge"
PRODUCTS_FILE = SKILL_DIR / "data" / "product-contexts.json"

# Explicit editorial edges from broad task contexts into the smaller catalogs.
PRODUCT_LINKS = {
    "saas-product": ["pattern:product-proof", "style:product-evidence", "ux:truthful-content"],
    "analytics-operations": ["pattern:decision-dashboard", "chart:time-series", "ux:data-context"],
    "finance-tools": ["pattern:comparison", "style:quiet-precision", "ux:comparison-integrity"],
    "learning-product": ["pattern:guided-task", "style:playful-utility", "ux:accessible-controls"],
    "hospitality-travel": ["pattern:search-results", "style:place-and-material", "ux:comparison-integrity"],
    "commerce-store": ["pattern:comparison", "style:content-led", "ux:truthful-content"],
    "portfolio-work": ["pattern:editorial-index", "style:typographic", "ux:content-hierarchy"],
    "editorial-publishing": ["pattern:editorial-index", "style:typographic", "ux:content-hierarchy"],
    "events-community": ["pattern:search-results", "style:place-and-material", "ux:accessible-controls"],
    "utility-tool": ["pattern:single-purpose-tool", "style:quiet-precision", "ux:input-feedback"],
    "booking-marketplace": ["pattern:search-results", "pattern:comparison", "ux:filter-state"],
    "public-information": ["pattern:guided-task", "style:place-and-material", "ux:truthful-content"],
    "developer-tool": ["pattern:product-proof", "style:product-evidence", "ux:recovery"],
    "media-entertainment": ["pattern:media-library", "style:content-led", "ux:accessible-controls"],
}

STOP = {"a", "an", "the", "and", "for", "with", "from", "that", "this", "into", "your", "make", "build", "design", "page", "app", "site", "website", "screen", "interface", "use", "want", "need", "please"}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1 and t not in STOP]


def load_records() -> tuple[list[dict], dict[str, set[str]]]:
    records: list[dict] = []
    links: dict[str, set[str]] = {}
    product_data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    for product in product_data["contexts"]:
        node_id = f"product:{product['id']}"
        fields = [product.get("title", ""), *product.get("aliases", [])]
        for key in ("primary_tasks", "decision_inputs", "content_to_show", "interaction_states", "visual_opportunities", "common_misses"):
            fields.extend(product.get(key, []))
        records.append({"id": node_id, "domain": "product", "title": product["title"], "summary": "; ".join(product.get("primary_tasks", [])[:2]), "tags": fields, "connects": PRODUCT_LINKS.get(product["id"], [])})
    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        catalog = json.loads(path.read_text(encoding="utf-8"))
        for record in catalog.get("records", []):
            records.append({**record, "domain": catalog["domain"]})
    for record in records:
        links[record["id"]] = set(record.get("connects", []))
    # Make authored links traversable from either endpoint without duplicating link data.
    for source, destinations in list(links.items()):
        for destination in destinations:
            links.setdefault(destination, set()).add(source)
    return records, links


def rank(brief: str, limit: int = 5) -> list[dict]:
    """Rank all catalog records and inspect only one-hop neighbors of top seeds."""
    records, links = load_records()
    query = set(tokens(brief))
    if not query:
        return []
    docs = []
    df: dict[str, int] = {}
    for record in records:
        terms = set(tokens(" ".join([record["title"], record.get("summary", ""), *record.get("tags", [])])))
        docs.append((record, terms))
        for term in terms:
            df[term] = df.get(term, 0) + 1
    ranked = []
    for record, terms in docs:
        matched = query & terms
        if not matched:
            continue
        score = sum(math.log1p(len(records) / (1 + df[term])) for term in matched)
        exact_tag = any(" ".join(tokens(tag)) in " ".join(tokens(brief)) for tag in record.get("tags", []) if len(tokens(tag)) > 1)
        score += 1.25 if exact_tag else 0
        ranked.append({"record": record, "score": score, "matched_terms": sorted(matched)})
    ranked.sort(key=lambda row: (-row["score"], row["record"]["id"]))
    seeds = ranked[: min(3, limit)]
    # Product context is already rendered by plan.py; use it as a graph seed
    # without repeating the same context in the cross-domain recommendations.
    selected = {row["record"]["id"]: row for row in seeds if row["record"]["domain"] != "product"}
    by_id = {record["id"]: record for record in records}
    # Bounded expansion: never recurse, and cap neighbors per seed.
    for seed in seeds:
        for neighbor_id in sorted(links.get(seed["record"]["id"], set()))[:4]:
            if neighbor_id not in by_id or neighbor_id in selected or by_id[neighbor_id]["domain"] == "product":
                continue
            selected[neighbor_id] = {"record": by_id[neighbor_id], "score": seed["score"] * 0.32, "matched_terms": [], "related_to": seed["record"]["id"]}
    results = sorted(selected.values(), key=lambda row: (-row["score"], row["record"]["id"]))[:limit]
    return [{"id": row["record"]["id"], "domain": row["record"]["domain"], "title": row["record"]["title"],
             "summary": row["record"].get("summary", ""), "relevance": round(row["score"], 3),
             "matched_terms": row.get("matched_terms", []), "related_to": row.get("related_to")} for row in results]
