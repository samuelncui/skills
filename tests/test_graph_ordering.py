"""Generic ordering contracts; no source-learning material or renderer imports.

Run from a clean checkout:
    python3 -B -m unittest discover -s tests -p 'test_graph_ordering.py' -v
"""

import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import unittest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills/study-notes/scripts/graph_ordering.py"
)
SPEC = importlib.util.spec_from_file_location("graph_ordering", MODULE_PATH)
graph_ordering = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(graph_ordering)


def crossing_score(order, edges):
    """Independent oracle: an edge contributes once to every cut it crosses."""
    distinct = set(tuple(edge) for edge in edges)
    result = 0
    for boundary in range(1, len(order)):
        left = set(order[:boundary])
        result += sum((source in left) != (target in left) for source, target in distinct)
    return result


def oracle(keys, entry, edges):
    """Enumerate by stable rank, using cut crossings rather than position spans."""
    remainder = [key for key in keys if key != entry]
    candidates = [
        (entry,) + suffix for suffix in itertools.permutations(remainder)
    ]
    # min keeps the first equal-scoring candidate: the supplied-rank tie order.
    order = min(candidates, key=lambda candidate: crossing_score(candidate, edges))
    return list(order), crossing_score(order, edges)


class GraphOrderingTests(unittest.TestCase):
    def assert_report(self, report, keys, entry, edges):
        self.assertEqual(report["order"][0], entry)
        self.assertEqual(len(report["order"]), len(keys))
        self.assertEqual(set(report["order"]), set(keys))
        self.assertEqual(report["baseline"], [entry] + [key for key in keys if key != entry])
        self.assertEqual(report["score"], crossing_score(report["order"], edges))
        self.assertEqual(report["baseline_score"], crossing_score(report["baseline"], edges))
        self.assertLessEqual(report["score"], report["baseline_score"])
        self.assertEqual(json.loads(json.dumps(report, allow_nan=False)), report)
        self.assertEqual(report["algorithm_version"], "1")
        self.assertEqual(report["exact"], report["certified_optimal"])

    def test_known_path_improves_with_entry_fixed(self):
        keys = ["entry", "far", "near", "end"]
        edges = [["entry", "near"], ["near", "far"], ["far", "end"]]
        report = graph_ordering.optimize(keys, "entry", edges)
        self.assert_report(report, keys, "entry", edges)
        self.assertEqual(report["baseline_score"], 5)
        self.assertEqual(report["score"], 3)
        self.assertEqual(report["order"], ["entry", "near", "far", "end"])
        self.assertEqual(report["evaluations"], 6)
        self.assertTrue(report["certified_optimal"])
        self.assertEqual(report["method"], "exhaustive")
        self.assertEqual(report["config"], {
            "exact_limit": 9, "max_exact_limit": 9, "budget": 60000,
        })

    def test_unique_directed_transitions_self_loops_and_stable_edge_report(self):
        keys = ["z", "entry", "a"]
        edges = [
            ["a", "entry"], ["entry", "a"], ["entry", "a"],
            ["z", "z"], ["entry", "entry"],
        ]
        report = graph_ordering.optimize(keys, "entry", edges)
        self.assert_report(report, keys, "entry", edges)
        self.assertEqual(report["edges"], [["entry", "a"], ["a", "entry"]])
        self.assertEqual(report["baseline_score"], 4)
        self.assertEqual(report["score"], 2)
        self.assertEqual(report, graph_ordering.optimize(keys, "entry", reversed(edges)))

    def test_rank_ties_preserve_complete_baseline_including_disconnected_keys(self):
        for keys, entry, edges in (
            (["z", "a", "entry", "β"], "entry", []),
            (["entry", "z", "a", "b"], "entry",
             [("entry", "z"), ("entry", "a"), ("entry", "b")]),
        ):
            with self.subTest(keys=keys):
                report = graph_ordering.optimize(keys, entry, edges)
                self.assert_report(report, keys, entry, edges)
                self.assertEqual(report["order"], report["baseline"])

    def test_singleton_is_exact_and_self_loop_is_ignored(self):
        report = graph_ordering.optimize(("only",), "only", [("only", "only")], budget=1)
        self.assert_report(report, ["only"], "only", [("only", "only")])
        self.assertEqual(report["edges"], [])
        self.assertEqual(report["evaluations"], 1)
        self.assertTrue(report["exact"])

    def test_small_graphs_match_independent_cut_oracle(self):
        rng = random.Random(20261007)
        for size in range(2, 8):
            # Spelling intentionally differs from the stable rank order.
            keys = ["key-" + str(20 - index) for index in range(size)]
            for shape in ("chain", "cycle", "disconnected", "mixed"):
                with self.subTest(size=size, shape=shape):
                    if shape == "chain":
                        edges = list(zip(keys, keys[1:]))
                    elif shape == "cycle":
                        edges = list(zip(keys, keys[1:] + keys[:1]))
                    elif shape == "disconnected":
                        edges = [(keys[-1], keys[0])]
                    else:
                        edges = [
                            (source, target) for source in keys for target in keys
                            if rng.randrange(4) == 0
                        ]
                        edges += edges[:2]  # Duplicates are not additional weight.
                    entry = keys[size // 2]
                    report = graph_ordering.optimize(keys, entry, edges)
                    self.assert_report(report, keys, entry, edges)
                    expected_order, expected_score = oracle(keys, entry, edges)
                    self.assertEqual(report["order"], expected_order)
                    self.assertEqual(report["score"], expected_score)
                    self.assertEqual(report["evaluations"], math.factorial(size - 1))
                    self.assertTrue(report["certified_optimal"])

    def test_maximum_exact_boundary_ignores_heuristic_budget(self):
        keys = ["node-" + str(index) for index in range(9)]
        edges = list(zip(keys, keys[1:]))
        report = graph_ordering.optimize(keys, keys[0], edges, budget=1)
        self.assert_report(report, keys, keys[0], edges)
        self.assertTrue(report["exact"])
        self.assertEqual(report["evaluations"], 40320)
        self.assertEqual(report["score"], 8)

    def test_large_graph_is_deterministic_bounded_and_improves(self):
        keys = ["entry"] + ["node-" + str(index) for index in range(1, 12)]
        chain = keys[:1] + keys[1::2] + keys[2::2]
        edges = list(zip(chain, chain[1:])) + [(chain[5], chain[3]), (chain[-1], "entry")]
        report = graph_ordering.optimize(keys, "entry", edges, budget=1200)
        self.assert_report(report, keys, "entry", edges)
        self.assertFalse(report["exact"])
        self.assertEqual(report["method"], "bounded-local-search")
        self.assertLessEqual(report["evaluations"], 1200)
        self.assertLess(report["score"], report["baseline_score"])
        self.assertEqual(report, graph_ordering.optimize(keys, "entry", list(reversed(edges)), budget=1200))
        self.assertEqual(report, graph_ordering.optimize(keys, "entry", edges + edges[:3], budget=1200))

    def test_heuristic_budget_boundary_retains_best_evaluated_baseline(self):
        keys = ["node-" + str(index) for index in range(10)]
        edges = [(keys[0], keys[-1]), (keys[-1], keys[2])]
        for budget in (1, 2, 5, 30):
            with self.subTest(budget=budget):
                report = graph_ordering.optimize(keys, keys[0], edges, budget=budget)
                self.assert_report(report, keys, keys[0], edges)
                self.assertFalse(report["certified_optimal"])
                self.assertLessEqual(report["evaluations"], budget)
                if budget == 1:
                    self.assertEqual(report["order"], report["baseline"])
                    self.assertEqual(report["evaluations"], 1)

    def test_configurable_exact_limit_and_heuristic_ties(self):
        keys = ["z", "entry", "a", "β"]
        report = graph_ordering.optimize(keys, "entry", [], exact_limit=1, budget=100)
        self.assert_report(report, keys, "entry", [])
        self.assertFalse(report["exact"])
        self.assertEqual(report["order"], report["baseline"])
        self.assertLess(report["evaluations"], 100)
        self.assertEqual(report["config"]["exact_limit"], 1)

    def test_inputs_are_not_mutated_and_reports_do_not_alias_them(self):
        keys = ["entry", "b", "a"]
        edges = [["entry", "a"], ["a", "b"]]
        expected_keys, expected_edges = list(keys), [list(edge) for edge in edges]
        report = graph_ordering.optimize(keys, "entry", edges)
        self.assertEqual(keys, expected_keys)
        self.assertEqual(edges, expected_edges)
        report["order"].clear()
        report["baseline"].clear()
        report["edges"][0].clear()
        self.assertEqual(keys, expected_keys)
        self.assertEqual(edges, expected_edges)

    def test_invalid_keys_entry_edges_and_configuration(self):
        cases = [
            ({"keys": []}, ValueError),
            ({"keys": "ab"}, TypeError),
            ({"keys": {"a", "b"}}, TypeError),
            ({"keys": {"a": 1, "b": 2}}, TypeError),
            ({"keys": ["a", "a"]}, ValueError),
            ({"keys": ["a", ""]}, ValueError),
            ({"keys": ["a", 3]}, ValueError),
            ({"entry": "missing"}, ValueError),
            ({"entry": []}, ValueError),
            ({"edges": None}, TypeError),
            ({"edges": "ab"}, TypeError),
            ({"edges": {"a": "b"}}, TypeError),
            ({"edges": ["ab"]}, ValueError),
            ({"edges": [["a"]]}, ValueError),
            ({"edges": [["a", "b", "a"]]}, ValueError),
            ({"edges": [{"a", "b"}]}, ValueError),
            ({"edges": [["a", "missing"]]}, ValueError),
            ({"edges": [["missing", "missing"]]}, ValueError),
            ({"edges": [["a", []]]}, ValueError),
            ({"exact_limit": 0}, ValueError),
            ({"exact_limit": 10}, ValueError),
            ({"exact_limit": True}, TypeError),
            ({"exact_limit": 2.5}, TypeError),
            ({"budget": 0}, ValueError),
            ({"budget": -1}, ValueError),
            ({"budget": False}, TypeError),
            ({"budget": 1.5}, TypeError),
        ]
        for replacement, error in cases:
            with self.subTest(replacement=replacement):
                arguments = {"keys": ["a", "b"], "entry": "a", "edges": []}
                arguments.update(replacement)
                with self.assertRaises(error):
                    graph_ordering.optimize(**arguments)


if __name__ == "__main__":
    unittest.main()
