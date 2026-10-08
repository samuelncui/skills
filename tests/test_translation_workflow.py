"""JSONL state-machine regressions; semantic decisions remain an agent review."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/bilingual-translation/scripts/translation_workflow.py"
SPEC = importlib.util.spec_from_file_location("workflow", SCRIPT)
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.md"
        self.receipt = self.root / "read.json"
        self.master = self.root / "master.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def prepare(self, text="# Title\r\n\r\nFirst source.\r\n\r\nSecond source.\r\n"):
        self.source.write_bytes(text.encode("utf-8"))
        page = W.read_source(self.source, self.receipt)
        pages = page["text"]
        while not page["complete"]:
            page = W.read_source(self.source, self.receipt, page["token"])
            pages += page["text"]
        self.assertEqual(pages, text)
        W.ack_source(self.source, self.receipt, page["source_hash"], page["token"])
        W.initialize(self.source, self.receipt, self.master)
        return W.load_jsonl(self.master)

    def payload(self, block, target="Translated."):
        return {"operation_id": "op-" + block["block_id"], "block_id": block["block_id"],
                "revision": block["revision"], "source_hashes": block["source_hashes"],
                "targets": {u["id"]: target for u in block["units"]}}

    def test_preread_version_and_init_gate(self):
        text = "A" * (W.READ_PAGE + 3)
        self.source.write_text(text, encoding="utf-8")
        first = W.read_source(self.source, self.receipt)
        self.assertFalse(first["complete"])
        with self.assertRaisesRegex(ValueError, "complete"):
            W.ack_source(self.source, self.receipt, first["source_hash"], first["token"])
        with self.assertRaisesRegex(ValueError, "acknowledge"):
            W.initialize(self.source, self.receipt, self.master)
        with self.assertRaises(ValueError):
            W.read_source(self.source, self.receipt, "wrong")
        last = W.read_source(self.source, self.receipt, first["token"])
        self.assertEqual(W.read_source(self.source, self.receipt, first["token"]), last)
        W.ack_source(self.source, self.receipt, last["source_hash"], last["token"])
        self.source.write_text(text + ".", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "acknowledge"):
            W.initialize(self.source, self.receipt, self.master)

    def test_markdown_source_first_structure_exact_reconstruction(self):
        text = "# 标题\r\n\r\n## 部分\r\n\r\nCafe\u0301 😀 sentence.\r\nNext line.\r\n\r\n- One\r\n- Two\r\n\r\n| Key | Value |\r\n| --- | --- |\r\n| A | B |\r\n"
        data = self.prepare(text)
        self.assertEqual([b["type"] for b in data["document"]["blocks"]],
                         ["heading", "heading", "paragraph", "list", "table"])
        self.assertTrue(all(u["target"] is None for u in data["units"]))
        self.assertEqual(data["units"][2]["heading_path"], ["u000001", "u000002"])
        self.assertEqual(data["units"][2]["source"], "Cafe\u0301 😀 sentence.\r\nNext line.")
        self.assertEqual(data["document"]["source"]["sha256"], W.digest(text))
        self.assertEqual(W.to_legacy_document(data, False)["units"][2]["source"], data["units"][2]["source"])

    def test_lossless_semantic_splits_unicode_and_hard_cap(self):
        parts = ["😀" * 1000 + ".  ", "e\u0301" * 600 + ".\r\n", "尾" * 500 + "."]
        source = "".join(parts)
        data = self.prepare(source)
        self.assertEqual(W.oversized(data)[0]["characters"], len(source))
        with self.assertRaisesRegex(ValueError, "oversized"):
            W.next_block(self.master)
        unit = data["units"][0]
        for offsets in ([True], [0], [len(source)], [10, 10], [20, 10], [1]):
            with self.subTest(offsets=offsets), self.assertRaises(ValueError):
                W.split_unit(self.master, unit["id"], offsets, unit["source_hash"], 0)
        result = W.split_unit(self.master, unit["id"], [len(parts[0]), len(parts[0]) + len(parts[1])],
                              unit["source_hash"], 0)
        children = W.load_jsonl(self.master)["units"]
        self.assertEqual([u["source"] for u in children], parts)
        self.assertEqual("".join(u["source"] for u in children), source)
        self.assertEqual([u["part_index"] for u in children], [0, 1, 2])
        self.assertEqual([u["has_more"] for u in children], [True, True, False])
        self.assertEqual(result["reconstruction_hash"], W.digest(source))
        self.assertEqual(len(W.next_block(self.master)["units"][0]["source"]), len(parts[0]))

    def test_cap_boundary_and_bounded_context(self):
        data = self.prepare("# " + ("Heading " * 100) + "\n\n" + "😀" * 2048)
        for _ in range(2):
            block = W.next_block(self.master)
            self.assertLessEqual(block["source_characters"], 2048)
            self.assertLessEqual(len(block["context"]["text"]), 1024)
            W.commit(self.master, self.payload(block))
        self.assertTrue(W.next_block(self.master)["complete"])

    def test_pending_restart_and_no_skip(self):
        self.prepare()
        first = W.next_block(self.master)
        self.assertEqual(W.next_block(self.master), first)
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), "next", str(self.master)],
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), first)
        before = self.master.read_bytes()
        bad = self.payload(first)
        bad["targets"] = {"u000002": "Wrong unit"}
        with self.assertRaisesRegex(ValueError, "exact active IDs"):
            W.commit(self.master, bad)
        self.assertEqual(self.master.read_bytes(), before)
        receipt = W.commit(self.master, self.payload(first))
        second = W.next_block(self.master)
        self.assertNotEqual(second["ids"], first["ids"])
        self.assertEqual(W.commit(self.master, self.payload(first)), receipt)
        self.assertEqual(W.next_block(self.master), second)

    def test_target_only_exact_ids_hashes_revision_and_operation_id(self):
        self.prepare()
        block = W.next_block(self.master)
        good = self.payload(block)
        cases = []
        for key, value in (("revision", True), ("revision", 0), ("block_id", "invented"),
                           ("source_hashes", {}), ("targets", {block["ids"][0]: ""})):
            bad = copy.deepcopy(good)
            bad[key] = value
            cases.append(bad)
        bad = copy.deepcopy(good)
        bad["source"] = "Replacement source"
        cases.append(bad)
        before = self.master.read_bytes()
        for bad in cases:
            with self.subTest(payload=bad), self.assertRaises(ValueError):
                W.commit(self.master, bad)
            self.assertEqual(self.master.read_bytes(), before)
        W.commit(self.master, good)
        changed = copy.deepcopy(good)
        changed["targets"][block["ids"][0]] = "Different retry"
        with self.assertRaisesRegex(ValueError, "reused"):
            W.commit(self.master, changed)

    def test_failed_atomic_save_does_not_advance(self):
        self.prepare()
        block = W.next_block(self.master)
        before = self.master.read_bytes()
        with patch.object(W.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaisesRegex(OSError, "interrupted"):
                W.commit(self.master, self.payload(block))
        self.assertEqual(self.master.read_bytes(), before)
        self.assertEqual(W.next_block(self.master), block)
        W.commit(self.master, self.payload(block))
        self.assertNotEqual(W.next_block(self.master)["ids"], block["ids"])
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_review_is_separate_and_hash_bound(self):
        self.prepare("First.")
        block = W.next_block(self.master)
        W.commit(self.master, self.payload(block))
        data = W.load_jsonl(self.master)
        self.assertEqual(data["units"][0]["status"], "draft")
        with self.assertRaisesRegex(ValueError, "reviewed"):
            W.load_jsonl(self.master, True)
        unit = data["units"][0]
        payload = {"operation_id": "review-one", "revision": data["document"]["revision"],
                   "unit": unit["id"], "source_hash": unit["source_hash"],
                   "target_hash": unit["target_hash"], "reviewer": "test-reviewer", "note": ""}
        bad = dict(payload, target_hash="0" * 64)
        with self.assertRaisesRegex(ValueError, "stale"):
            W.review(self.master, bad)
        receipt = W.review(self.master, payload)
        self.assertEqual(W.review(self.master, payload), receipt)
        W.load_jsonl(self.master, True)
        self.assertEqual(W.to_legacy_document(W.load_jsonl(self.master))["units"][0]["status"], "reviewed")

    def test_order_hash_child_and_malformed_state_rejected(self):
        data = self.prepare("First.\n\nSecond.")
        cases = []
        bad = copy.deepcopy(data)
        bad["document"]["blocks"].reverse()
        cases.append(bad)
        for field, value in (("source", "changed"), ("id", "bad id"), ("has_more", True),
                             ("part_index", 1), ("order", 2), ("heading_path", ["unknown"])):
            bad = copy.deepcopy(data)
            bad["units"][0][field] = value
            cases.append(bad)
        bad = copy.deepcopy(data)
        bad["document"]["source_layout"].reverse()
        cases.append(bad)
        for bad in cases:
            with self.subTest(data=bad), self.assertRaises(ValueError):
                W.validate(bad)
        self.master.write_text('{"record_type":"document","record_type":"document"}\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            W.load_jsonl(self.master)

    def test_parallel_idempotent_commit_and_stale_writer(self):
        self.prepare("Only.")
        block = W.next_block(self.master)
        payload = self.root / "payload.json"
        payload.write_text(json.dumps(self.payload(block)), encoding="utf-8")
        command = [sys.executable, "-B", str(SCRIPT), "commit", str(self.master),
                   "--payload", str(payload)]
        procs = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for _ in range(2)]
        results = [p.communicate(timeout=10) for p in procs]
        self.assertEqual([p.returncode for p in procs], [0, 0], results)
        self.assertEqual(json.loads(results[0][0]), json.loads(results[1][0]))
        data = W.load_jsonl(self.master)
        self.assertEqual(data["document"]["revision"], block["revision"] + 1)
        self.assertEqual(len(data["document"]["workflow"]["operations"]), 1)

    def test_parallel_different_commits_only_one_wins(self):
        self.prepare("Only.")
        block = W.next_block(self.master)
        procs = []
        for i in range(2):
            payload = self.payload(block, "Target " + str(i))
            payload["operation_id"] += str(i)
            file = self.root / ("payload" + str(i) + ".json")
            file.write_text(json.dumps(payload), encoding="utf-8")
            procs.append(subprocess.Popen([sys.executable, "-B", str(SCRIPT), "commit",
                         str(self.master), "--payload", str(file)], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True))
        results = [p.communicate(timeout=10) for p in procs]
        self.assertEqual(sorted(p.returncode for p in procs), [0, 1], results)
        self.assertEqual(W.load_jsonl(self.master)["document"]["revision"], block["revision"] + 1)

    def test_output_exists_and_rich_markdown_are_explicit_failures(self):
        self.prepare("A source.")
        with self.assertRaisesRegex(ValueError, "exists"):
            W.initialize(self.source, self.receipt, self.master)
        for text in ("```python\nx=1\n```", "> quote", "    nested", "![alt](asset.png)"):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "native route"):
                W.import_markdown(text)

    def test_malformed_json_shapes_and_boolean_revisions_are_rejected(self):
        data = self.prepare("Only.")
        for bad in (None, [], {"document": None, "units": []}):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                W.validate(bad)
        bad = copy.deepcopy(data)
        bad["document"]["preread"]["acknowledged"] = 1
        with self.assertRaises(ValueError):
            W.validate(bad)
        W.next_block(self.master)
        bad = W.load_jsonl(self.master)
        bad["document"]["workflow"]["active"]["revision"] = True
        with self.assertRaises(ValueError):
            W.validate(bad)

    def test_schema_agrees_with_source_split_active_and_reviewed_records(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((SCRIPT.parents[1] / "schemas/translation-workflow.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        data = self.prepare("\ufeff# Title\r\n\r\n" + "x" * 2048)
        self.assertEqual(data["document"]["blocks"][0]["type"], "heading")
        self.assertEqual(data["units"][0]["source"], "Title")
        self.assertEqual(list(validator.iter_errors(data)), [])
        block = W.next_block(self.master)
        self.assertEqual(list(validator.iter_errors(W.load_jsonl(self.master))), [])
        W.commit(self.master, self.payload(block))
        self.assertEqual(list(validator.iter_errors(W.load_jsonl(self.master))), [])
        data["units"][0]["unexpected"] = True
        self.assertTrue(list(validator.iter_errors(data)))
        with self.assertRaises(ValueError):
            W.validate(data)

    def test_revision_preserves_source_and_invalidates_review(self):
        self.prepare("First.")
        block = W.next_block(self.master)
        W.commit(self.master, self.payload(block))
        data = W.load_jsonl(self.master)
        unit = data["units"][0]
        W.review(self.master, {"operation_id": "review-first", "revision": data["document"]["revision"],
                 "unit": unit["id"], "source_hash": unit["source_hash"],
                 "target_hash": unit["target_hash"], "reviewer": "agent", "note": ""})
        data = W.load_jsonl(self.master, True)
        correction = {"operation_id": "correct-first", "revision": data["document"]["revision"],
                      "unit": unit["id"], "source_hash": unit["source_hash"],
                      "target_hash": unit["target_hash"], "target": "Corrected translation."}
        bad = dict(correction, target_hash="0" * 64)
        with self.assertRaisesRegex(ValueError, "stale"):
            W.revise(self.master, bad)
        receipt = W.revise(self.master, correction)
        self.assertEqual(W.revise(self.master, correction), receipt)
        revised = W.load_jsonl(self.master)
        self.assertEqual(revised["units"][0]["source"], unit["source"])
        self.assertEqual(revised["units"][0]["status"], "draft")
        self.assertIsNone(revised["units"][0]["review"])
        with self.assertRaisesRegex(ValueError, "reviewed"):
            W.load_jsonl(self.master, True)

    def test_draft_export_is_explicit_and_never_allows_empty_targets(self):
        self.prepare("First.")
        command = [sys.executable, "-B", str(SCRIPT), "export", str(self.master),
                   "--output", str(self.root / "out.json")]
        result = subprocess.run(command + ["--allow-draft"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("all targets saved", result.stderr)
        W.commit(self.master, self.payload(W.next_block(self.master)))
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("reviewed", result.stderr)
        result = subprocess.run(command + ["--allow-draft"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["review_gate"])

    def test_clean_installed_workflow_has_no_repository_dependency(self):
        import shutil
        installed = self.root / "installed"
        shutil.copytree(SCRIPT.parents[1], installed)
        run = subprocess.run([sys.executable, "-B", str(installed / "scripts/translation_workflow.py"),
                              "--help"], cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("read-source", run.stdout)


if __name__ == "__main__":
    unittest.main()
