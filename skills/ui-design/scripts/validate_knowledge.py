#!/usr/bin/env python3
"""Validate catalog shape, graph edges, and a small retrieval relevance set."""
from __future__ import annotations

import json
import sys
from time import perf_counter
from pathlib import Path

from knowledge import KNOWLEDGE_DIR, PRODUCTS_FILE, load_records, rank


def main() -> int:
    failures: list[str] = []
    try:
        records, links = load_records()
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Catalog load failed: {exc}", file=sys.stderr)
        return 1
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        failures.append("record IDs must be globally unique")
    id_set = set(ids)
    for record in records:
        for field in ("id", "domain", "title", "summary"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                failures.append(f"{record.get('id', '<unknown>')}: missing non-empty {field}")
        if record.get("domain") != "product" and len(record.get("summary", "").split()) < 8:
            failures.append(f"{record.get('id')}: summary needs at least 8 words of actionable guidance")
        if not isinstance(record.get("tags"), list) or not record["tags"]:
            failures.append(f"{record.get('id')}: tags must be a non-empty list")
        for target in record.get("connects", []):
            if target not in id_set:
                failures.append(f"{record['id']}: unresolved edge to {target}")
    for path in [PRODUCTS_FILE, *KNOWLEDGE_DIR.glob("*.json")]:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{path.name}: invalid JSON: {exc}")

    cases_path = KNOWLEDGE_DIR / "relevance-cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
    hits = 0
    reciprocal_ranks = []
    query_times = []
    for case in cases:
        started = perf_counter()
        results = rank(case["brief"], limit=5)
        query_times.append(perf_counter() - started)
        result_ids = [row["id"] for row in results]
        if case["expected"] in result_ids:
            hits += 1
            reciprocal_ranks.append(1 / (result_ids.index(case["expected"]) + 1))
        else:
            reciprocal_ranks.append(0)
            failures.append(f"relevance miss: {case['brief']!r}; expected {case['expected']}; got {[row['id'] for row in results]}")

    if failures:
        print("Knowledge validation failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    mean_query_ms = 1000 * sum(query_times) / max(1, len(query_times))
    mrr = sum(reciprocal_ranks) / max(1, len(reciprocal_ranks))
    print(f"Validated {len(records)} records and {sum(len(v) for v in links.values()) // 2} undirected edges.")
    print(f"Retrieval benchmark: hit@5 {hits}/{len(cases)}, MRR {mrr:.3f}, mean lookup {mean_query_ms:.2f} ms (local process, in-memory Python benchmark).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
