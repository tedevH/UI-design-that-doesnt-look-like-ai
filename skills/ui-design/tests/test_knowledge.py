"""Fast, dependency-free checks for the connected catalog and planner contract."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from knowledge import load_records, rank  # noqa: E402


class KnowledgeTests(unittest.TestCase):
    def test_graph_edges_are_resolvable_and_bidirectional(self):
        records, links = load_records()
        ids = {record["id"] for record in records}
        self.assertEqual(len(ids), len(records))
        for source, destinations in links.items():
            self.assertIn(source, ids)
            for destination in destinations:
                self.assertIn(destination, ids)
                self.assertIn(source, links[destination])

    def test_query_returns_relevant_pattern_and_explicit_evidence(self):
        results = rank("finance dashboard compare pricing plans", limit=5)
        self.assertTrue(results)
        self.assertTrue(any(row["domain"] in {"patterns", "ux", "charts"} for row in results))
        self.assertTrue(any(row["matched_terms"] for row in results))

    def test_expansion_is_bounded(self):
        self.assertLessEqual(len(rank("analytics dashboard time series chart", limit=4)), 4)

    def test_planner_includes_graph_recommendations_in_json(self):
        script = SCRIPTS / "plan.py"
        output = subprocess.check_output([sys.executable, str(script), "analytics dashboard time series", "--format", "json"], text=True)
        payload = json.loads(output)
        self.assertTrue(payload["knowledge"])
        self.assertIn("matches", payload)


if __name__ == "__main__":
    unittest.main()
