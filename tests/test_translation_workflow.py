"""JSONL integrity regressions exercised through the public workflow facade."""
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
SCRIPT = ROOT / "skills/bilingual-translation/scripts/workflow.py"
SPEC = importlib.util.spec_from_file_location("workflow", SCRIPT)
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)
W = F.core


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
        page = F.read_source(self.source, self.receipt)
        pages = page["text"]
        while not page["complete"]:
            page = F.read_source(self.source, self.receipt, page["ref"])
            pages += page["text"]
        self.assertEqual(pages, text)
        F.initialize(self.source, self.receipt, self.master, page["ref"])
        return W.load_jsonl(self.master)

    def payload(self, block, target="Translated."):
        return {"ref": block["ref"], "targets": {u["id"]: target for u in block["units"]}}

    def accept(self, block):
        return {"ref": block["ref"], "reviewer": "test-reviewer", "note": ""}

    def test_preread_source_integrity_and_init_gate(self):
        text = "A" * (W.READ_PAGE + 3)
        self.source.write_text(text, encoding="utf-8")
        first = F.read_source(self.source, self.receipt)
        self.assertFalse(first["complete"])
        with self.assertRaises(ValueError):
            F.initialize(self.source, self.receipt, self.master, first["ref"])
        with self.assertRaises(ValueError):
            F.read_source(self.source, self.receipt, "wrong")
        last = F.read_source(self.source, self.receipt, first["ref"])
        self.assertEqual(F.read_source(self.source, self.receipt, first["ref"]), last)
        self.source.write_text(text + ".", encoding="utf-8")
        with self.assertRaises(ValueError):
            F.initialize(self.source, self.receipt, self.master, last["ref"])
        self.assertFalse(self.master.exists())

    def test_markdown_source_first_structure_exact_reconstruction(self):
        text = "# 标题\r\n\r\n## 部分\r\n\r\nCafe\u0301 😀 sentence.\r\nNext line.\r\n\r\n- One\r\n- Two\r\n\r\n| Key | Value |\r\n| --- | --- |\r\n| A | B |\r\n"
        data = self.prepare(text)
        self.assertEqual([b["type"] for b in data["document"]["blocks"]],
                         ["heading", "heading", "paragraph", "list", "table"])
        self.assertTrue(all(u["target"] is None for u in data["units"]))
        self.assertEqual(data["units"][2]["heading_path"], ["u000001", "u000002"])
        self.assertEqual(data["units"][2]["source"], "Cafe\u0301 😀 sentence.\r\nNext line.")
        self.assertEqual(data["document"]["source"]["sha256"], W.digest(text))
        self.assertEqual(W.to_exchange_document(data, False)["units"][2]["source"],
                         data["units"][2]["source"])

    def test_lossless_semantic_splits_unicode_and_hard_cap(self):
        parts = ["😀" * 1000 + ".  ", "e\u0301" * 600 + ".\r\n", "尾" * 500 + "."]
        source = "".join(parts)
        self.source.write_bytes(source.encode("utf-8"))
        page = F.read_source(self.source, self.receipt)
        self.assertEqual(page["oversize"][0]["characters"], len(source))
        uid = page["oversize"][0]["id"]
        for offsets in (None, [True], [0], [len(source)], [10, 10], [20, 10], [1]):
            with self.subTest(offsets=offsets), self.assertRaises(ValueError):
                F.initialize(self.source, self.receipt, self.master, page["ref"],
                             splits=None if offsets is None else {uid: offsets})
            self.assertFalse(self.master.exists())
        F.initialize(self.source, self.receipt, self.master, page["ref"],
                     splits={uid: [len(parts[0]), len(parts[0]) + len(parts[1])]})
        data = W.load_jsonl(self.master)
        children = data["units"]
        self.assertEqual([u["source"] for u in children], parts)
        self.assertEqual("".join(u["source"] for u in children), source)
        self.assertEqual([u["part_index"] for u in children], [0, 1, 2])
        self.assertEqual([u["has_more"] for u in children], [True, True, False])
        self.assertEqual(data["document"]["source"]["sha256"], W.digest(source))
        self.assertEqual(len(F.next_block(self.master)["units"][0]["source"]), len(parts[0]))

    def test_cap_boundary_and_bounded_context(self):
        self.prepare("# " + ("Heading " * 100) + "\n\n" + "😀" * 2048)
        for _ in range(2):
            block = F.next_block(self.master, include_context=True)
            self.assertLessEqual(sum(len(u["source"]) for u in block["units"]), 2048)
            self.assertLessEqual(len(block.get("context", {}).get("text", "")), 1024)
            F.mutate(self.master, "save", self.payload(block))
        self.assertTrue(F.next_block(self.master)["complete"])

    def test_pending_restart_and_no_skip(self):
        self.prepare()
        first = F.next_block(self.master)
        self.assertEqual(F.next_block(self.master), first)
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), "translate", "next", str(self.master)],
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), first)
        before = self.master.read_bytes()
        bad = self.payload(first)
        bad["targets"] = {"u000002": "Wrong unit"}
        with self.assertRaisesRegex(ValueError, "exact active IDs"):
            F.mutate(self.master, "save", bad)
        self.assertEqual(self.master.read_bytes(), before)
        receipt = F.mutate(self.master, "save", self.payload(first))
        second = F.next_block(self.master)
        self.assertNotEqual(second["units"], first["units"])
        self.assertEqual(F.mutate(self.master, "save", self.payload(first)), receipt)
        self.assertEqual(F.next_block(self.master), second)

    def test_target_only_exact_ids_reference_and_replay(self):
        self.prepare()
        block = F.next_block(self.master)
        good = self.payload(block)
        cases = []
        for key, value in (("ref", True), ("ref", 0), ("ref", "999999-apple"),
                           ("targets", {}), ("targets", {block["units"][0]["id"]: ""}),
                           ("targets", {block["units"][0]["id"]: "\ud800"})):
            bad = copy.deepcopy(good)
            bad[key] = value
            cases.append(bad)
        cases.append(dict(good, source="Replacement source"))
        before = self.master.read_bytes()
        for bad in cases:
            with self.subTest(payload=bad), self.assertRaises(ValueError):
                F.mutate(self.master, "save", bad)
            self.assertEqual(self.master.read_bytes(), before)
        F.mutate(self.master, "save", good)
        changed = self.payload(block, "Different retry")
        with self.assertRaisesRegex(ValueError, "reused"):
            F.mutate(self.master, "save", changed)

    def test_failed_atomic_save_does_not_advance(self):
        self.prepare()
        block = F.next_block(self.master)
        before = self.master.read_bytes()
        with patch.object(W.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaisesRegex(OSError, "interrupted"):
                F.mutate(self.master, "save", self.payload(block))
        self.assertEqual(self.master.read_bytes(), before)
        self.assertEqual(F.next_block(self.master), block)
        F.mutate(self.master, "save", self.payload(block))
        self.assertNotEqual(F.next_block(self.master)["units"], block["units"])
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_review_is_separate_and_hash_bound(self):
        self.prepare("First.")
        block = F.next_block(self.master)
        with self.assertRaises(ValueError):
            F.next_block(self.master, "review")
        F.mutate(self.master, "save", self.payload(block))
        self.assertEqual(W.load_jsonl(self.master)["units"][0]["status"], "draft")
        with self.assertRaisesRegex(ValueError, "reviewed"):
            W.load_jsonl(self.master, True)
        block = F.next_block(self.master, "review")
        before = self.master.read_bytes()
        with self.assertRaisesRegex(ValueError, "stale"):
            F.mutate(self.master, "accept", dict(self.accept(block), ref="999999-apple"))
        self.assertEqual(self.master.read_bytes(), before)
        receipt = F.mutate(self.master, "accept", self.accept(block))
        self.assertEqual(F.mutate(self.master, "accept", self.accept(block)), receipt)
        data = W.load_jsonl(self.master, True)
        unit = data["units"][0]
        self.assertEqual(unit["review"]["source_hash"], unit["source_hash"])
        self.assertEqual(unit["review"]["target_hash"], unit["target_hash"])
        self.assertEqual(W.to_exchange_document(data)["units"][0]["status"], "reviewed")
        unit["target"] = "Tampered"
        with self.assertRaises(ValueError):
            W.validate(data)

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
        block = F.next_block(self.master)
        revision = W.load_jsonl(self.master)["document"]["revision"]
        payload = self.root / "payload.json"
        payload.write_text(json.dumps(self.payload(block)), encoding="utf-8")
        command = [sys.executable, "-B", str(SCRIPT), "translate", "save", str(self.master),
                   "--payload", str(payload)]
        procs = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for _ in range(2)]
        results = [p.communicate(timeout=10) for p in procs]
        self.assertEqual([p.returncode for p in procs], [0, 0], results)
        self.assertEqual(json.loads(results[0][0]), json.loads(results[1][0]))
        data = W.load_jsonl(self.master)
        self.assertEqual(data["document"]["revision"], revision + 1)
        self.assertEqual(len([k for k in data["document"]["workflow"]["operations"]
                              if k.startswith("_compact_receipt:")]), 1)

    def test_parallel_different_commits_only_one_wins(self):
        self.prepare("Only.")
        block = F.next_block(self.master)
        revision = W.load_jsonl(self.master)["document"]["revision"]
        procs = []
        for i in range(2):
            payload = self.payload(block, "Target " + str(i))
            file = self.root / ("payload" + str(i) + ".json")
            file.write_text(json.dumps(payload), encoding="utf-8")
            procs.append(subprocess.Popen([sys.executable, "-B", str(SCRIPT), "translate", "save",
                         str(self.master), "--payload", str(file)], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True))
        results = [p.communicate(timeout=10) for p in procs]
        self.assertEqual(sorted(p.returncode for p in procs), [0, 1], results)
        self.assertEqual(W.load_jsonl(self.master)["document"]["revision"], revision + 1)

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
        F.next_block(self.master)
        bad = W.load_jsonl(self.master)
        bad["document"]["revision"] = True
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
        while True:
            block = F.next_block(self.master)
            self.assertEqual(list(validator.iter_errors(W.load_jsonl(self.master))), [])
            if block.get("complete"):
                break
            F.mutate(self.master, "save", self.payload(block))
        while True:
            block = F.next_block(self.master, "review")
            if block.get("complete"):
                break
            F.mutate(self.master, "accept", self.accept(block))
            self.assertEqual(list(validator.iter_errors(W.load_jsonl(self.master))), [])
        data["units"][0]["unexpected"] = True
        self.assertTrue(list(validator.iter_errors(data)))
        with self.assertRaises(ValueError):
            W.validate(data)

    def test_revision_preserves_source_and_invalidates_review(self):
        self.prepare("First.")
        F.mutate(self.master, "save", self.payload(F.next_block(self.master)))
        block = F.next_block(self.master, "review")
        F.mutate(self.master, "accept", self.accept(block))
        unit = W.load_jsonl(self.master, True)["units"][0]
        block = F.next_block(self.master, "review", unit_id=unit["id"])
        correction = self.payload(block, "Corrected translation.")
        before = self.master.read_bytes()
        with self.assertRaisesRegex(ValueError, "stale"):
            F.mutate(self.master, "revise", dict(correction, ref="999999-apple"))
        self.assertEqual(self.master.read_bytes(), before)
        receipt = F.mutate(self.master, "revise", correction)
        self.assertEqual(F.mutate(self.master, "revise", correction), receipt)
        revised = W.load_jsonl(self.master)
        self.assertEqual(revised["units"][0]["source"], unit["source"])
        self.assertEqual(revised["units"][0]["source_hash"], unit["source_hash"])
        self.assertEqual(revised["units"][0]["status"], "draft")
        self.assertIsNone(revised["units"][0]["review"])
        with self.assertRaisesRegex(ValueError, "reviewed"):
            W.load_jsonl(self.master, True)
        F.mutate(self.master, "accept", self.accept(receipt["next"]))
        W.load_jsonl(self.master, True)

    def test_draft_export_is_explicit_and_never_allows_empty_targets(self):
        self.prepare("First.")
        command = [sys.executable, "-B", str(SCRIPT), "export", str(self.master),
                   "--output", str(self.root / "out.json")]
        result = subprocess.run(command + ["--allow-draft"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("all targets saved", result.stderr)
        F.mutate(self.master, "save", self.payload(F.next_block(self.master)))
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("review", result.stderr)
        result = subprocess.run(command + ["--allow-draft"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["review_gate"])

    def test_clean_installed_workflow_has_no_repository_dependency(self):
        import shutil
        installed = self.root / "installed"
        shutil.copytree(SCRIPT.parents[1], installed)
        run = subprocess.run([sys.executable, "-B", str(installed / "scripts/workflow.py"),
                              "--help"], cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("prepare", run.stdout)


if __name__ == "__main__":
    unittest.main()
