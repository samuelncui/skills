"""Pure preparation contract tests: complete delivery and lossless semantic cuts."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "preparation", ROOT / "skills/bilingual-translation/scripts/preparation.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def reconstructed(data):
    groups = {}
    for unit in data["units"]:
        groups.setdefault(unit["parent_id"], []).append(unit["source"])
    return "".join(piece["text"] if "text" in piece else "".join(groups[piece["parent"]])
                   for piece in data["document"]["source_layout"])


class PreparationTests(unittest.TestCase):
    def test_create_preserves_structure_crlf_and_no_alias(self):
        source = "\ufeff# 标题\r\n\r\nCafe\u0301 😀.\r\nNext line.\r\n\r\n- One\r\n- Two\r\n\r\n| A | B |\r\n| --- | --- |\r\n| C | D |\r\n"
        context = {"summary": "Bilingual example"}
        data = P.create(source, context=context)
        context["summary"] = "Changed"
        self.assertEqual(data["document"]["context"]["summary"], "Bilingual example")
        self.assertEqual(reconstructed(data), source)
        self.assertNotIn("version", data["document"])
        self.assertNotIn("preread", data["document"])
        response = P.deliver(data)
        self.assertTrue(response["complete"])
        self.assertEqual(response["units"][0]["level"], 1)
        self.assertEqual(response["units"][1]["source"], "Cafe\u0301 😀.\r\nNext line.")
        self.assertEqual(response["units"][2]["list_index"], 0)
        self.assertEqual(response["units"][-1]["table_column"], 1)
        response["units"][0]["heading_path"].append("changed")
        self.assertEqual(data["units"][0]["heading_path"], [])

    def test_full_paragraph_budget_and_tail_coverage(self):
        paragraphs = [str(i) + "x" * 1499 for i in range(7)]
        data = P.create("\n\n".join(paragraphs))
        first = P.deliver(data)
        self.assertEqual([v["source"] for v in first["units"]], paragraphs[:6])
        self.assertEqual(first["characters"], 9000)
        self.assertFalse(first["complete"])
        last = P.deliver(data)
        self.assertEqual([v["source"] for v in last["units"]], paragraphs[6:])
        self.assertTrue(last["complete"])
        self.assertEqual(last["progress"]["percent"], 100)
        self.assertNotEqual(first["ref"], last["ref"])
        with self.assertRaises(ValueError):
            P.deliver(data)

    def test_multiple_oversize_all_delivered_and_gate_until_split(self):
        paragraphs = [("A" * 1500 + " END. " + "B" * 1500),
                      ("C" * 1500 + " STOP. " + "D" * 1500),
                      "E" * 2048, "F" * 1500, "tail"]
        data = P.create("\n\n".join(paragraphs))
        first = P.deliver(data)
        self.assertEqual(len(first["units"]), 4)
        self.assertEqual([v["id"] for v in first["oversize"]], ["u000001", "u000002"])
        self.assertEqual(first["oversize"][0]["minimum_parts"], 2)
        with self.assertRaises(ValueError):
            P.deliver(data)
        P.split(data, first["ref"], "u000001", [{"left": " END. ", "right": "BBB"}])
        data["document"]["revision"] += 1
        self.assertEqual(P.batch_reference(data), first["ref"])
        with self.assertRaises(ValueError):
            P.deliver(data)
        ack = P.split(data, first["ref"], "u000002", [{"left": " STOP.", "right": " DDD"}])
        self.assertEqual(ack["pending"], [])
        self.assertFalse(ack["complete"])
        tail = P.deliver(data)
        self.assertEqual([v["source"] for v in tail["units"]], ["tail"])
        self.assertTrue(tail["complete"])
        self.assertEqual(reconstructed(data), "\n\n".join(paragraphs))

    def test_large_paragraph_not_truncated_and_unicode_lossless(self):
        parts = ["😀" * 1000 + ".  ", "e\u0301" * 600 + ".\r\n", "尾" * 500 + "."]
        source = "".join(parts)
        data = P.create(source)
        response = P.deliver(data)
        self.assertEqual(response["units"][0]["source"], source)
        self.assertFalse(response["complete"])
        ack = P.split(data, response["ref"], "u000001", [
            {"left": "😀.  ", "right": "e\u0301"},
            {"left": "e\u0301.\r\n", "right": "尾"}])
        self.assertTrue(ack["complete"])
        self.assertEqual([v["source"] for v in data["units"]], parts)
        self.assertEqual([v["has_more"] for v in data["units"]], [True, True, False])
        self.assertEqual([v["part_index"] for v in data["units"]], [0, 1, 2])
        self.assertEqual(reconstructed(data), source)
        self.assertEqual(data["document"]["revision"], 0)

    def test_huge_single_unit_is_full_delivery(self):
        source = "a" * 20000
        response = P.deliver(P.create(source))
        self.assertEqual(response["units"][0]["source"], source)
        self.assertEqual(response["oversize"][0]["minimum_parts"], 10)
        self.assertFalse(response["complete"])

    def test_invalid_anchor_inputs_leave_data_unchanged(self):
        source = "A" * 1500 + " end. " + "B" * 1500
        data = P.create(source)
        ref = P.deliver(data)["ref"]
        cases = [None, [], [1500], [True],
                 [{"left": "", "right": "A"}],
                 [{"left": True, "right": "A"}],
                 [{"left": "missing", "right": "A"}],
                 [{"left": "A", "right": "A"}],
                 [{"left": " end. ", "right": "BB", "extra": 1}],
                 [{"left": " end. ", "right": "BB"}] * 2,
                 [{"left": "A end. ", "right": "BB"},
                  {"left": "AA", "right": "A end."}],
                 [{"left": "A", "right": "A" * 1499 + " end. "}]]
        for cuts in cases:
            with self.subTest(cuts=cuts):
                before = copy.deepcopy(data)
                with self.assertRaises(ValueError):
                    P.split(data, ref, "u000001", cuts)
                self.assertEqual(data, before)
        for bad_ref, bad_id in [("wrong", "u000001"), (ref, "u000002")]:
            before = copy.deepcopy(data)
            with self.assertRaises(ValueError):
                P.split(data, bad_ref, bad_id, [{"left": " end. ", "right": "BB"}])
            self.assertEqual(data, before)

    def test_anchor_diagnostics_count_overlapping_matches_and_bound_context(self):
        data = P.create("A" * 3000)
        ref = P.deliver(data)["ref"]
        before = copy.deepcopy(data)
        for cuts, expected in [([{"left": "missing", "right": "A"}], 0),
                               ([{"left": "A", "right": "A"}], 2999)]:
            with self.subTest(expected=expected), self.assertRaises(P.PreparationError) as caught:
                P.split(data, ref, "u000001", cuts)
            details = caught.exception.details
            self.assertEqual(details["match_count"], expected)
            self.assertEqual(details["cut_index"], 0)
            self.assertEqual(len(details["contexts"]), min(expected, 3))
            for context in details["contexts"]:
                self.assertLessEqual(len(context["left"]), 24)
                self.assertLessEqual(len(context["right"]), 24)
            self.assertEqual(data, before)

    def test_oversize_diagnostics_report_each_bad_child_without_full_source(self):
        source = "A" * 2200 + " end. " + "B" * 2300
        data = P.create(source)
        ref = P.deliver(data)["ref"]
        before = copy.deepcopy(data)
        with self.assertRaises(P.PreparationError) as caught:
            P.split(data, ref, "u000001", [{"left": " end. ", "right": "BB"}])
        children = caught.exception.details["children"]
        self.assertEqual([v["characters"] for v in children], [2206, 2300])
        self.assertEqual([v["excess"] for v in children], [158, 252])
        self.assertEqual([v["part_index"] for v in children], [0, 1])
        for child in children:
            for boundary in ("start", "end"):
                for side in ("left", "right"):
                    self.assertLessEqual(len(child[boundary][side]), 24)
        self.assertEqual(data, before)

    def test_not_pending_and_source_tampering_rejected(self):
        data = P.create("short")
        response = P.deliver(data)
        with self.assertRaises(ValueError):
            P.split(data, response["ref"], "u000001", [{"left": "sh", "right": "ort"}])
        data = P.create("A" * 1500 + " end. " + "B" * 1500)
        ref = P.deliver(data)["ref"]
        data["units"][0]["source"] += "!"
        with self.assertRaises(ValueError):
            P.split(data, ref, "u000001", [{"left": " end. ", "right": "BB"}])


if __name__ == "__main__":
    unittest.main()
