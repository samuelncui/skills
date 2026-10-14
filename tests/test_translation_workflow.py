"""Strict persisted JSONL integrity through the single public action executor."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/bilingual-translation/scripts/workflow.py"
SPEC = importlib.util.spec_from_file_location("workflow", SCRIPT)
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)
W = F.core


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.md"
        self.master = self.root / "master.jsonl"

    def act(self, op, **fields):
        return F.execute(self.master, [{"op": op, **fields}])[0]

    def prepare(self, text="First.\n\nSecond."):
        self.source.write_bytes(text.encode())
        self.act("prepare init", source=str(self.source))
        return W.load_jsonl(self.master)

    def save(self, block):
        return self.act("translate save", ref=block["ref"],
                        targets={u["id"]: "Translated." for u in block["units"]})

    def write_corrupt(self, data):
        self.master.write_text("\n".join(json.dumps(v) for v in
            [data["document"]] + data["units"]) + "\n")

    def test_markdown_structure_exact_unicode_crlf_reconstruction(self):
        text = ("\ufeff# 标题\r\n\r\n## 部分\r\n\r\nCafe\u0301 😀 sentence.\r\nNext line.\r\n\r\n"
                "- One\r\n- Two\r\n\r\n| Key | Value |\r\n| --- | --- |\r\n| A | B |\r\n")
        data = self.prepare(text)
        self.assertEqual([b["type"] for b in data["document"]["blocks"]],
                         ["heading", "heading", "paragraph", "list", "table"])
        self.assertEqual(data["units"][2]["heading_path"], ["u000001", "u000002"])
        self.assertEqual(data["units"][2]["source"], "Cafe\u0301 😀 sentence.\r\nNext line.")
        self.assertEqual(data["document"]["source"]["sha256"], W.digest(text))
        self.assertEqual(self.source.read_bytes(), text.encode())
        W.validate(data)
        with self.assertRaises(ValueError):
            W.to_exchange_document(data)

    def test_anchor_split_schema_and_source_preservation_through_review(self):
        parts = ["😀" * 1000 + ".  ", "e\u0301" * 600 + ".\r\n", "尾" * 500 + "."]
        text = "".join(parts)
        self.source.write_bytes(text.encode())
        first = self.act("prepare init", source=str(self.source))
        schema = json.loads((SCRIPT.parents[1] / "schemas/translation-workflow.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        validator.validate(W.load_jsonl(self.master))
        self.act("prepare split", ref=first["ref"], unit="u000001", cuts=[
            {"left": "😀.  ", "right": "e\u0301"}, {"left": "e\u0301.\r\n", "right": "尾"}])
        data = W.load_jsonl(self.master)
        self.assertEqual([u["source"] for u in data["units"]], parts)
        self.assertEqual([u["has_more"] for u in data["units"]], [True, True, False])
        for phase in ("translate", "review"):
            while True:
                block = self.act(phase + " next")
                validator.validate(W.load_jsonl(self.master))
                if block.get("complete"):
                    break
                if phase == "translate":
                    self.save(block)
                else:
                    self.act("review accept", ref=block["ref"])
                validator.validate(W.load_jsonl(self.master))
        W.load_jsonl(self.master, require_ready=True)
        self.assertEqual(self.source.read_bytes(), text.encode())

    def test_order_source_hash_child_and_layout_corruption_rejected(self):
        data = self.prepare()
        mutations = [
            lambda d: d["document"]["blocks"].reverse(),
            lambda d: d["document"]["source_layout"].reverse(),
        ]
        for field, value in (("source", "changed"), ("id", "bad id"), ("has_more", True),
                             ("part_index", 1), ("order", 2), ("heading_path", ["unknown"])):
            mutations.append(lambda d, k=field, v=value: d["units"][0].__setitem__(k, v))
        for mutate in mutations:
            bad = copy.deepcopy(data); mutate(bad)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                W.validate(bad)
        # A locally consistent unit hash cannot defeat complete source reconstruction.
        bad = copy.deepcopy(data)
        bad["units"][0]["source"] = "Changed."
        bad["units"][0]["source_hash"] = W.digest("Changed.")
        with self.assertRaises(ValueError):
            W.validate(bad)

    def test_malformed_shapes_boolean_counters_and_extra_fields(self):
        data = self.prepare("Only.")
        for bad in (None, [], {"document": None, "units": []}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                W.validate(bad)
        changes = [
            (("document",), "revision", True),
            (("document",), "version", 1),
            (("document",), "contract_version", 2),
            (("document",), "preread", {}),
            (("document", "preparation"), "cursor", True),
            (("document", "preparation"), "complete", 1),
            (("document", "workflow"), "sequence", True),
            (("document", "workflow"), "review_round", True),
            (("document", "workflow"), "seen", ["bogus"]),
        ]
        for path, key, value in changes:
            bad = copy.deepcopy(data); place = bad
            for part in path:
                place = place[part]
            place[key] = value
            with self.subTest(path=path, key=key), self.assertRaises(ValueError):
                W.validate(bad)
        bad = copy.deepcopy(data); bad["units"][0]["unexpected"] = True
        with self.assertRaises(ValueError):
            W.validate(bad)

    def test_active_binding_and_journal_corruption_reject_before_writes(self):
        self.prepare(); self.act("translate next")
        good = W.load_jsonl(self.master)
        cases = []
        for key, value in (("binding", "0" * 64), ("ref", "1-wrong"),
                           ("delivered", 1), ("ids", ["u000002", "u000001"])):
            bad = copy.deepcopy(good); bad["document"]["workflow"]["active"][key] = value
            cases.append(bad)
        for key, record in (("_compact_active", {}), ("0" * 64, None),
                            ("0" * 64, {"request_hash": "1" * 64, "receipt": {}})):
            bad = copy.deepcopy(good)
            bad["document"]["workflow"]["operations"][key] = record
            cases.append(bad)
        for bad in cases:
            self.write_corrupt(bad)
            before = self.master.read_bytes()
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): W.validate(bad)
                with self.assertRaises(ValueError): self.act("status")
                with self.assertRaises(ValueError): self.act("translate next")
                self.assertEqual(self.master.read_bytes(), before)

    def test_duplicate_json_keys_and_nonrecord_shapes(self):
        for text in ('{"record_type":"document","record_type":"document"}\n',
                     'null\n', '[]\n', '{}\n', '\n', '{"record_type":"unit"}\n'):
            self.master.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                W.load_jsonl(self.master)

    def test_review_hashes_bind_exact_current_source_and_target(self):
        self.prepare("One.")
        self.save(self.act("translate next"))
        with self.assertRaises(ValueError): self.act("validate", ready=True)
        block = self.act("review next")
        self.act("review accept", ref=block["ref"])
        data = W.load_jsonl(self.master, require_ready=True)
        unit = data["units"][0]
        self.assertEqual(unit["review"]["source_hash"], unit["source_hash"])
        self.assertEqual(unit["review"]["target_hash"], unit["target_hash"])
        for key in ("source_hash", "target_hash"):
            bad = copy.deepcopy(data); bad["units"][0]["review"][key] = "0" * 64
            with self.assertRaises(ValueError): W.validate(bad)
        unit["target"] = "Changed"; unit["target_hash"] = W.digest("Changed")
        with self.assertRaises(ValueError): W.validate(data)

    def test_startup_failure_invalid_source_and_symlinks_preserve_inputs(self):
        self.source.write_text("One.")
        before = self.source.read_bytes()
        with patch.object(W.os, "link", side_effect=OSError("interrupted")):
            with self.assertRaises(ValueError):
                self.act("prepare init", source=str(self.source))
        self.assertFalse(self.master.exists())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(list(self.root.glob(".*.tmp")), [])
        destination_alias = self.root / "destination-alias.jsonl"
        destination_alias.symlink_to(self.master)
        with self.assertRaises(ValueError):
            F.execute(destination_alias, [{"op": "prepare init", "source": str(self.source)}])
        self.assertFalse(self.master.exists())
        for text in ("\x00bad", "```python\nx=1\n```", "> quote", "    nested", "![alt](asset.png)"):
            self.source.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.act("prepare init", source=str(self.source))
            self.assertFalse(self.master.exists())
        self.source.write_bytes(b"\xff")
        with self.assertRaises(UnicodeError):
            self.act("prepare init", source=str(self.source))

    def test_single_writer_core_has_no_removed_authoring_entrypoints(self):
        for name in ("initialize", "read_source", "ack_source", "next_block", "commit",
                     "review", "revise", "split_unit", "main"):
            self.assertFalse(hasattr(W, name), name)
        self.assertIs(F.COMMANDS, F.actions.COMMANDS)


if __name__ == "__main__":
    unittest.main()
