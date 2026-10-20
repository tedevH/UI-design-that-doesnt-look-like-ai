#!/usr/bin/env python3
"""Validate design catalogs, directed relationships, and retrieval quality fixtures."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

from knowledge import KNOWLEDGE_DIR, PRODUCTS_FILE, load_graph, rank


def main() -> int:
    failures: list[str] = []
    try:
        nodes, adjacency, relations = load_graph()
        graph = json.loads((KNOWLEDGE_DIR / "edges.json").read_text(encoding="utf-8"))
        product_data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Catalog load failed: {exc}", file=sys.stderr)
        return 1

    def fail(message: str) -> None:
        failures.append(message)

    raw_ids = [f"product:{item['id']}" for item in product_data["contexts"]]
    for catalog_path in KNOWLEDGE_DIR.glob("*.json"):
        if catalog_path.name in {"edges.json", "relevance-cases.json"}:
            continue
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            raw_ids.extend(record["id"] for record in catalog.get("records", []))
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            fail(f"{catalog_path.name}: invalid catalog data: {exc}")
    if len(raw_ids) != len(set(raw_ids)):
        fail("node IDs must be globally unique across product and knowledge catalogs")

    for node_id, node in nodes.items():
        if not node.get("title") or not node.get("domain"):
            fail(f"{node_id}: title and domain are required")
        if node["domain"] != "product" and (not node.get("summary") or len(node.get("tags", [])) < 2):
            fail(f"{node_id}: knowledge nodes require a summary and at least two tags")
    for relation_id, relation in relations.items():
        if not relation.get("label") or not relation.get("description"):
            fail(f"{relation_id}: relation needs a label and description")
        if not 0 < relation.get("weight", 0) <= 1:
            fail(f"{relation_id}: traversal weight must be in (0, 1]")

    seen_edges = set()
    for edge in graph.get("edges", []):
        source, target, relation_id = edge.get("from"), edge.get("to"), edge.get("relation")
        if source not in nodes:
            fail(f"edge source does not resolve: {source}")
            continue
        if target not in nodes:
            fail(f"edge target does not resolve: {target}")
            continue
        if relation_id not in relations:
            fail(f"edge relation does not resolve: {relation_id}")
            continue
        relation = relations[relation_id]
        if nodes[source]["domain"] not in relation["from_domains"] or nodes[target]["domain"] not in relation["to_domains"]:
            fail(f"edge violates relationship direction/domain: {source} -{relation_id}-> {target}")
        key = (source, relation_id, target)
        if key in seen_edges:
            fail(f"duplicate graph edge: {source} -{relation_id}-> {target}")
        seen_edges.add(key)
    missing_products = [f"product:{item['id']}" for item in product_data["contexts"] if not adjacency.get(f"product:{item['id']}")]
    if missing_products:
        fail(f"product contexts need outgoing graph links: {', '.join(missing_products)}")

    cases_path = KNOWLEDGE_DIR / "relevance-cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
    relevant = 0
    recalled = 0
    reciprocal_ranks = []
    runtimes_ms = []
    for case in cases:
        started = perf_counter()
        try:
            results = rank(case["brief"], limit=5, context_id=case.get("context_seed"), max_hops=case.get("max_hops", 3))
        except (ValueError, KeyError) as exc:
            fail(f"query {case['brief']!r} failed: {exc}")
            continue
        runtimes_ms.append((perf_counter() - started) * 1000)
        result_ids = [row["id"] for row in results]
        expected = case.get("expected")
        if expected is None:
            if results:
                fail(f"weak-match case should return nothing: {case['brief']!r}; got {result_ids}")
            continue
        expected_ids = [expected, *case.get("expected_all", [])]
        case_hits = sum(item in result_ids for item in expected_ids)
        relevant += len(expected_ids)
        recalled += case_hits
        if expected in result_ids:
            reciprocal_ranks.append(1 / (result_ids.index(expected) + 1))
        else:
            reciprocal_ranks.append(0)
            fail(f"relevance miss: {case['brief']!r}; expected {expected}; got {result_ids}")
        missing_additional = [item for item in case.get("expected_all", []) if item not in result_ids]
        if missing_additional:
            fail(f"multi-intent miss: {case['brief']!r}; missing {missing_additional}; got {result_ids}")
        expected_path = case.get("expected_path")
        if expected_path:
            path_result = next((row for row in results if row["id"] == expected), None)
            if not path_result or path_result.get("path") != expected_path:
                fail(f"path miss: {case['brief']!r}; expected {expected_path}; got {path_result.get('path') if path_result else None}")

    if failures:
        print("Knowledge validation failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    mrr = sum(reciprocal_ranks) / max(1, len(reciprocal_ranks))
    mean_ms = sum(runtimes_ms) / max(1, len(runtimes_ms))
    print(f"Validated {len(nodes)} nodes, {len(seen_edges)} typed directed edges, and outgoing links for all {len(product_data['contexts'])} product contexts.")
    print(f"Retrieval benchmark: recall@5 {recalled}/{relevant}, MRR {mrr:.3f}; mean lookup {mean_ms:.2f} ms across {len(cases)} fixtures in one local Python process.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
