#!/usr/bin/env python3
"""Create an offline, task-centered design brief from a request and optional stack."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from knowledge import rank as rank_knowledge

SKILL_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = SKILL_DIR / "data" / "product-contexts.json"
STACK_DIR = SKILL_DIR / "references" / "stacks"
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "i", "in",
    "into", "is", "it", "its", "make", "my", "of", "on", "or", "our", "page", "screen", "that",
    "the", "their", "this", "to", "use", "we", "with", "you", "your", "website", "app", "interface",
    "build", "create", "design", "redesign", "improve", "beautiful", "modern", "clean", "responsive",
    "simple", "better", "please", "want", "need", "help", "make", "ui", "ux", "screen", "site", "web",
}


def words(text: str) -> list[str]:
    """Normalize words and retain useful hyphenated terms as separate tokens."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 1 and w not in STOP_WORDS]


def load_catalog() -> dict:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read product context catalog at {DATA_FILE}: {exc}") from None
    contexts = data.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        raise SystemExit("Product context catalog has no contexts.")
    return data


def searchable(context: dict) -> str:
    fields = [context.get("title", ""), *context.get("aliases", [])]
    for key in ("primary_tasks", "decision_inputs", "content_to_show", "interaction_states", "visual_opportunities", "common_misses"):
        fields.extend(context.get(key, []))
    return " ".join(fields).lower()


def rank_contexts(brief: str, contexts: list[dict]) -> list[dict]:
    query_terms = set(words(brief))
    if not query_terms:
        return []
    docs = []
    df: dict[str, int] = {}
    for context in contexts:
        term_set = set(words(searchable(context)))
        docs.append((context, term_set))
        for term in term_set:
            df[term] = df.get(term, 0) + 1

    ranked = []
    n = len(contexts)
    for context, term_set in docs:
        overlap = query_terms & term_set
        score = sum(math.log(1 + n / (1 + df[term])) for term in overlap)
        # Exact multi-word aliases are stronger intent evidence than loose word overlap.
        normalized_brief = " ".join(words(brief))
        alias_hits = [alias for alias in context.get("aliases", []) if " ".join(words(alias)) in normalized_brief]
        score += 3.0 * len(alias_hits)
        if score:
            ranked.append({
                "context": context,
                "score": round(score, 3),
                "matched_terms": sorted(overlap),
                "matched_aliases": alias_hits,
            })
    return sorted(ranked, key=lambda row: (-row["score"], row["context"]["title"]))


def resolve_context(args, contexts: list[dict], ranked: list[dict]) -> dict | None:
    if args.context:
        for context in contexts:
            if context["id"] == args.context:
                return context
        raise SystemExit(f"Unknown context id: {args.context}")
    return ranked[0]["context"] if ranked else None


def render_markdown(brief: str, context: dict | None, ranked: list[dict], stack: str | None, top: int) -> str:
    lines = ["# Design planning brief", "", f"**Request:** {brief}", ""]
    if context:
        row = next((r for r in ranked if r["context"]["id"] == context["id"]), None)
        lines += [f"## Product context: {context['title']}", ""]
        if row:
            evidence = ", ".join(row["matched_aliases"] or row["matched_terms"][:6]) or "explicitly selected"
            lines.append(f"Catalog match evidence: {evidence}. This is a relevance hint, not a confidence score or a visual style assignment.")
            lines.append("")
        for label, key in (
            ("Primary user tasks", "primary_tasks"),
            ("Questions to resolve", "decision_inputs"),
            ("Content that should be real and visible", "content_to_show"),
            ("Interaction states to consider", "interaction_states"),
            ("Visual opportunities", "visual_opportunities"),
            ("Common failures to guard against", "common_misses"),
        ):
            lines.append(f"### {label}")
            lines.extend(f"- {item}" for item in context.get(key, []))
            lines.append("")
    else:
        lines += ["## Product context", "", "No catalog match stood out. Infer the user's task and evidence from the brief, or rerun with `--context <id>` after reviewing `--list`.", ""]

    knowledge = rank_knowledge(brief, limit=top)
    if knowledge:
        lines += ["## Connected design knowledge", "", "Retrieved task patterns and checks (relevance hints, not style prescriptions):", ""]
        for item in knowledge:
            evidence = ", ".join(item["matched_terms"]) or f"related to {item['related_to']}"
            lines.append(f"- **{item['title']}** ({item['domain']}) — {item['summary']} *Evidence: {evidence}.*")
        lines.append("")
    lines += ["## Direction decisions", "", "Resolve these from the user's product, assets, brand, and content. The catalog does not choose a style recipe.", "",
              "- What should the user understand or do first?", "- What specific product detail can become the focal material?",
              "- Which visual form best expresses it: interface, data, image, typography, diagram, object, or scene?",
              "- What will stay quiet so the focal idea reads clearly?", "- What changes on narrow screens to preserve the same intent?", ""]
    if stack:
        lines += [f"## Stack guidance: {stack}", "", stack, ""]
    if ranked:
        lines += ["## Other catalog matches", ""]
        alternatives = [r for r in ranked if not context or r["context"]["id"] != context["id"]][:max(0, top - 1)]
        for row in alternatives:
            evidence = ", ".join(row["matched_aliases"] or row["matched_terms"][:5])
            lines.append(f"- **{row['context']['title']}** — matched: {evidence}")
        if not alternatives:
            lines.append("No other contexts matched the request.")
        lines.append("")
    lines += ["## Final review", "", "Use `references/quality-bar.md` to critique the rendered page. Do not treat this lookup, a style signal, or a generated score as proof of quality."]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    catalog = load_catalog()
    contexts = catalog["contexts"]
    stack_files = sorted(STACK_DIR.glob("*.md"))
    stack_ids = [path.stem for path in stack_files if path.stem != "README"]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", nargs="?", help="product or page request to plan")
    parser.add_argument("--context", help="select a catalog context by id, overriding search")
    parser.add_argument("--stack", choices=stack_ids, help="append implementation guidance for this stack")
    parser.add_argument("--top", type=int, default=3, help="number of relevant contexts to consider (default: 3)")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="write the plan to a file instead of stdout")
    parser.add_argument("--list", action="store_true", help="list product context ids and stack guides")
    args = parser.parse_args()

    if args.list:
        for context in contexts:
            print(f"context  {context['id']:<24} {context['title']}")
        for stack_id in stack_ids:
            print(f"stack    {stack_id}")
        return 0
    if not args.brief:
        parser.error("brief is required unless --list is used")
    if args.top < 1 or args.top > 10:
        parser.error("--top must be between 1 and 10")

    ranked = rank_contexts(args.brief, contexts)
    knowledge = rank_knowledge(args.brief, limit=args.top)
    context = resolve_context(args, contexts, ranked)
    stack_text = None
    if args.stack:
        stack_text = (STACK_DIR / f"{args.stack}.md").read_text(encoding="utf-8")
    if args.format == "json":
        output = json.dumps({
            "brief": args.brief,
            "selected_context": context,
            "matches": [{"id": row["context"]["id"], "title": row["context"]["title"], "relevance": row["score"],
                         "matched_terms": row["matched_terms"], "matched_aliases": row["matched_aliases"]}
                        for row in ranked[:args.top]],
            "knowledge": knowledge,
            "stack": args.stack,
            "stack_guidance": stack_text,
        }, indent=2, ensure_ascii=False) + "\n"
    else:
        output = render_markdown(args.brief, context, ranked, stack_text, args.top)
    if args.output:
        destination = args.output.expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output, encoding="utf-8")
        print(f"Wrote plan to {destination}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
