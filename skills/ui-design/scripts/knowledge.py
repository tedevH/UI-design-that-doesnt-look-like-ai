"""Deterministic, bounded retrieval and typed graph traversal for design guidance."""
from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = SKILL_DIR / "data" / "knowledge"
PRODUCTS_FILE = SKILL_DIR / "data" / "product-contexts.json"
GRAPH_FILE = KNOWLEDGE_DIR / "edges.json"

STOP = {"a", "an", "the", "and", "are", "as", "at", "be", "by", "can", "do", "for", "from", "has", "have", "how", "i", "if", "in", "into", "is", "it", "its", "me", "my", "of", "on", "or", "our", "please", "that", "their", "this", "to", "use", "we", "what", "which", "with", "you", "your", "make", "build", "design", "page", "app", "site", "website", "screen", "interface", "want", "need", "just", "only", "one", "first", "next", "ui", "ux", "redesign", "homepage"}
FIELD_WEIGHTS = {"title": 3.2, "aliases": 2.7, "tags": 1.8, "summary": 1.2, "supporting": 0.55}
DEFAULT_LIMIT = 5
MAX_LIMIT = 10
MAX_QUERY_TERMS = 96
MAX_SEEDS = 5
MAX_SEEDS_PER_DOMAIN = 2
MAX_HOPS = 3
MAX_EXPANSIONS = 36
MIN_DIRECT_SCORE = 1.8
MIN_PATH_SCORE = 1.4


def tokens(text: str) -> list[str]:
    """Normalize query text while preserving first occurrence and bounding work."""
    normalized = text.lower()
    # In editorial language, "long-form" is a content format, not a form control.
    normalized = re.sub(r"\b(?:long|short)[ -]form\b", lambda match: match.group(0).replace(" ", "-").replace("-form", "-format"), normalized)
    found = (token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 1 and token not in STOP)
    return list(dict.fromkeys(found))[:MAX_QUERY_TERMS]


@lru_cache(maxsize=1)
def load_graph() -> tuple[dict[str, dict], dict[str, list[dict]], dict[str, dict]]:
    """Load compact catalogs once per process; return nodes, outgoing edges, relation rules."""
    nodes: dict[str, dict] = {}
    products = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    for product in products["contexts"]:
        node_id = f"product:{product['id']}"
        supporting = []
        for field in ("primary_tasks", "decision_inputs", "content_to_show", "interaction_states", "visual_opportunities", "common_misses"):
            supporting.extend(product.get(field, []))
        nodes[node_id] = {
            "id": node_id,
            "domain": "product",
            "title": product["title"],
            "aliases": product.get("aliases", []),
            "summary": "; ".join(product.get("primary_tasks", [])[:2]),
            "tags": [],
            "supporting": supporting,
        }
    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        if path.name in {"edges.json", "relevance-cases.json"}:
            continue
        catalog = json.loads(path.read_text(encoding="utf-8"))
        for record in catalog.get("records", []):
            nodes[record["id"]] = {**record, "domain": catalog["domain"], "aliases": record.get("aliases", []), "supporting": []}
    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    relations = {item["id"]: item for item in graph["relations"]}
    adjacency = {node_id: [] for node_id in nodes}
    for edge in graph["edges"]:
        adjacency.setdefault(edge["from"], []).append(edge)
    for outgoing in adjacency.values():
        outgoing.sort(key=lambda edge: (edge["relation"], edge["to"]))
    return nodes, adjacency, relations


def _search_fields(node: dict) -> dict[str, str | list[str]]:
    return {"title": node["title"], "aliases": node.get("aliases", []), "tags": node.get("tags", []),
            "summary": node.get("summary", ""), "supporting": node.get("supporting", [])}


@lru_cache(maxsize=1)
def _search_index() -> tuple[dict[str, dict], dict[str, set[str]], dict[str, dict], dict[str, list[dict]], dict[str, dict]]:
    nodes, adjacency, relations = load_graph()
    prepared: dict[str, dict] = {}
    document_frequency: dict[str, set[str]] = {}
    for node_id, node in nodes.items():
        field_tokens = {}
        for field, value in _search_fields(node).items():
            values = value if isinstance(value, list) else [value]
            terms = set(tokens(" ".join(str(item) for item in values)))
            field_tokens[field] = terms
            for term in terms:
                document_frequency.setdefault(term, set()).add(node_id)
        prepared[node_id] = field_tokens
    return nodes, document_frequency, prepared, adjacency, relations


def _direct_candidates(query_terms: list[str], query_text: str) -> list[dict]:
    nodes, document_frequency, prepared, _, _ = _search_index()
    query = set(query_terms)
    normalized_query = " ".join(query_terms)
    candidates = []
    for node_id, node in nodes.items():
        matched_by_field: dict[str, list[str]] = {}
        score = 0.0
        for field, terms in prepared[node_id].items():
            matched = query & terms
            if not matched:
                continue
            matched_by_field[field] = sorted(matched)
            field_weight = FIELD_WEIGHTS[field]
            for term in matched:
                df = len(document_frequency.get(term, ()))
                idf = math.log1p((len(nodes) + 0.5) / (df + 0.5))
                score += idf * field_weight
        alias_values = [node["title"], *node.get("aliases", []), *node.get("tags", [])]
        phrase = max((len(tokens(value)) for value in alias_values if len(tokens(value)) > 1 and " ".join(tokens(value)) in normalized_query), default=0)
        if phrase:
            score += 2.5 + 0.25 * phrase
        if score >= MIN_DIRECT_SCORE:
            candidates.append({
                "id": node_id,
                "score": score,
                "matched_terms": sorted(query & set().union(*prepared[node_id].values())),
                "matched_fields": matched_by_field,
                "phrase_match": phrase > 0,
            })
    return sorted(candidates, key=lambda row: (-row["score"], row["id"]))


def _select_seeds(candidates: list[dict], context_id: str | None) -> list[dict]:
    nodes, _, _, _, _ = _search_index()
    selected = []
    domains: dict[str, int] = {}
    if context_id:
        explicit_id = f"product:{context_id}"
        if explicit_id in nodes:
            explicit = next((row for row in candidates if row["id"] == explicit_id), None)
            selected.append(explicit or {"id": explicit_id, "score": 6.0, "matched_terms": [], "matched_fields": {}, "phrase_match": False, "explicit": True})
            domains["product"] = 1
    for candidate in candidates:
        if len(selected) >= MAX_SEEDS:
            break
        if candidate["score"] < MIN_DIRECT_SCORE:
            continue
        if any(seed["id"] == candidate["id"] for seed in selected):
            continue
        domain = nodes[candidate["id"]]["domain"]
        if domains.get(domain, 0) >= MAX_SEEDS_PER_DOMAIN:
            continue
        selected.append(candidate)
        domains[domain] = domains.get(domain, 0) + 1
    return selected


def rank(brief: str, limit: int = DEFAULT_LIMIT, context_id: str | None = None, max_hops: int = MAX_HOPS) -> list[dict]:
    """Retrieve direct matches, then traverse typed outgoing edges in bounded rounds.

    Scores rank this query's evidence; they are neither probabilities nor quality scores.
    Every returned non-product result carries direct match evidence or its graph path.
    """
    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    if max_hops < 0 or max_hops > MAX_HOPS:
        raise ValueError(f"max_hops must be between 0 and {MAX_HOPS}")
    query_terms = tokens(brief)
    if not query_terms:
        return []
    nodes, _, _, adjacency, relations = _search_index()
    candidates = _direct_candidates(query_terms, brief)
    seeds = _select_seeds(candidates, context_id)
    direct_by_id = {row["id"]: row for row in candidates}
    discovered: dict[str, dict] = {
        row["id"]: {**row, "path": [row["id"]], "relations": [], "hops": 0,
                    "path_score": row["score"], "seed_id": row["id"], "direct": True}
        for row in candidates if nodes[row["id"]]["domain"] != "product"
    }
    frontier = [{**seed, "path": [seed["id"]], "relations": [], "hops": 0, "path_score": seed["score"], "seed_id": seed["id"]} for seed in seeds]
    expansions = 0

    # Each round is one edge farther from a seed. Duplicate nodes keep their strongest
    # path; no cycles are followed, and both hop count and total edge expansions are capped.
    for _ in range(max_hops):
        next_frontier = []
        frontier.sort(key=lambda state: (-state["path_score"], state["id"], state["seed_id"]))
        for state in frontier:
            for edge in adjacency.get(state["id"], []):
                if expansions >= MAX_EXPANSIONS:
                    break
                if edge["to"] in state["path"]:
                    continue
                expansions += 1
                relation = relations[edge["relation"]]
                path_score = state["path_score"] * relation["weight"]
                if path_score < MIN_PATH_SCORE:
                    continue
                path = [*state["path"], edge["to"]]
                relation_chain = [*state["relations"], edge["relation"]]
                destination = edge["to"]
                direct = direct_by_id.get(destination)
                display_score = max(path_score, direct["score"] if direct else 0)
                candidate = {
                    "id": destination,
                    "score": display_score,
                    "path_score": path_score,
                    "path": path,
                    "relations": relation_chain,
                    "hops": len(relation_chain),
                    "seed_id": state["seed_id"],
                    "matched_terms": direct["matched_terms"] if direct else [],
                    "matched_fields": direct["matched_fields"] if direct else {},
                    "phrase_match": direct["phrase_match"] if direct else False,
                    "direct": direct is not None,
                }
                previous = discovered.get(destination)
                if previous is None or (candidate["score"], -candidate["hops"]) > (previous["score"], -previous["hops"]):
                    discovered[destination] = candidate
                elif candidate["direct"] and candidate["hops"] > previous["hops"]:
                    # Preserve the best lexical rank while retaining a useful graph path
                    # when direct evidence and a contextual route both exist.
                    candidate["score"] = max(candidate["score"], previous["score"])
                    discovered[destination] = candidate
                if len(path) - 1 < max_hops:
                    next_frontier.append({**candidate, "path_score": path_score})
            if expansions >= MAX_EXPANSIONS:
                break
        frontier = next_frontier
        if not frontier or expansions >= MAX_EXPANSIONS:
            break

    output = []
    for node_id, item in discovered.items():
        node = nodes[node_id]
        # Product context is already rendered by the planner, but remains a traversal seed.
        if node["domain"] == "product":
            continue
        if item["direct"]:
            evidence = "Matched " + ", ".join(item["matched_terms"])
            if item["matched_fields"]:
                evidence += " in " + ", ".join(item["matched_fields"])
            if item["hops"]:
                labels = [relations[relation]["label"] for relation in item["relations"]]
                evidence += f"; connected via {' → '.join(labels)}"
        else:
            path_titles = [nodes[path_id]["title"] for path_id in item["path"]]
            relation_labels = [relations[relation]["label"] for relation in item["relations"]]
            evidence = "Reached via " + " → ".join(path_titles)
            evidence += " (" + " → ".join(relation_labels) + ")"
        output.append({
            "id": node_id,
            "domain": node["domain"],
            "title": node["title"],
            "summary": node.get("summary", ""),
            "relevance": round(item["score"], 3),
            "matched_terms": item["matched_terms"],
            "matched_fields": item["matched_fields"],
            "path": item["path"],
            "relations": item["relations"],
            "hops": item["hops"],
            "evidence": evidence,
        })
    output.sort(key=lambda row: (-row["relevance"], row["hops"], row["id"]))
    # Cap repeated domains to preserve a useful mix across different kinds of guidance.
    balanced = []
    per_domain: dict[str, int] = {}
    for item in output:
        if per_domain.get(item["domain"], 0) >= 2:
            continue
        balanced.append(item)
        per_domain[item["domain"]] = per_domain.get(item["domain"], 0) + 1
        if len(balanced) >= limit:
            break
    return balanced
