"""Fast, dependency-free checks for directed graph traversal and planner output."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from knowledge import load_graph, rank, tokens  # noqa: E402


class KnowledgeTests(unittest.TestCase):
    def test_all_product_contexts_have_valid_typed_directed_edges(self):
        nodes, adjacency, relations = load_graph()
        products = [node_id for node_id, node in nodes.items() if node["domain"] == "product"]
        self.assertEqual(len(products), 15)
        for product_id in products:
            self.assertTrue(adjacency[product_id], product_id)
        for source, outgoing in adjacency.items():
            for edge in outgoing:
                self.assertIn(edge["to"], nodes)
                self.assertIn(nodes[source]["domain"], relations[edge["relation"]]["from_domains"])
                self.assertIn(nodes[edge["to"]]["domain"], relations[edge["relation"]]["to_domains"])

    def test_query_returns_direct_evidence_and_readable_graph_path(self):
        direct_results = rank("podcast collection for later listening")
        media = next(row for row in direct_results if row["id"] == "pattern:media-library")
        self.assertTrue(media["matched_terms"])
        results = rank("deep cut archive", context_id="media-entertainment")
        access = next(row for row in results if row["id"] == "ux:accessible-controls")
        self.assertEqual(access["path"], ["product:media-entertainment", "pattern:media-library", "ux:accessible-controls"])
        self.assertIn("Reached via", access["evidence"])

    def test_explicit_context_can_seed_graph_discovery_without_query_overlap(self):
        results = rank("unknown task phrasing", context_id="media-entertainment")
        self.assertIn("pattern:media-library", {row["id"] for row in results})

    def test_weak_query_does_not_receive_fabricated_recommendations(self):
        self.assertEqual(rank("blorpt qzx frobnicate"), [])

    def test_traversal_obeys_hop_and_result_budgets(self):
        results = rank("podcast media library", limit=4, context_id="media-entertainment", max_hops=1)
        self.assertLessEqual(len(results), 4)
        self.assertTrue(all(row["hops"] <= 1 for row in results))
        self.assertEqual(rank("podcast", max_hops=0)[0]["hops"], 0)

    def test_long_form_editorial_query_does_not_match_form_controls(self):
        results = rank("podcast interviews in a long-form archive", max_hops=0)
        self.assertIn("pattern:media-library", {row["id"] for row in results})
        self.assertNotIn("ux:input-feedback", {row["id"] for row in results})
        self.assertNotIn("pattern:guided-task", {row["id"] for row in results})

    def test_query_tokenization_is_bounded(self):
        self.assertLessEqual(len(tokens("keyword " * 500)), 1)
        self.assertLessEqual(len(tokens(" ".join(f"token{i}" for i in range(200)))), 96)

    def test_planner_json_contains_paths_and_evidence(self):
        script = SCRIPTS / "plan.py"
        output = subprocess.check_output([sys.executable, str(script), "podcast collection for later listening", "--format", "json"], text=True)
        payload = json.loads(output)
        self.assertTrue(payload["knowledge"])
        self.assertTrue(all(row["evidence"] and row["path"] for row in payload["knowledge"]))
        self.assertIn("matches", payload)

    def test_planner_does_not_select_a_context_from_filler_words(self):
        script = SCRIPTS / "plan.py"
        output = subprocess.check_output([sys.executable, str(script), "a page that is just blorpt qzx frobnicate", "--format", "json"], text=True)
        payload = json.loads(output)
        self.assertIsNone(payload["selected_context"])
        self.assertEqual(payload["knowledge"], [])


if __name__ == "__main__":
    unittest.main()
