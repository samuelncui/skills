"""Objective semantic exchange regression tests; these do not grade translation quality."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/bilingual-translation"
SPEC = importlib.util.spec_from_file_location("translation_contract", SKILL / "scripts/translation_contract.py")
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)
EXAMPLE = SKILL / "examples/guide/translation.json"
BASE = json.loads(EXAMPLE.read_text(encoding="utf-8"))
SCHEMA = json.loads((SKILL / "schemas/translation.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


class TranslationContractTests(unittest.TestCase):
    def doc(self):
        return copy.deepcopy(BASE)

    def rejects(self, data, fragment=None, ready=False):
        errors = CONTRACT.validate_document(data, require_ready=ready)
        self.assertTrue(errors, "invalid document was accepted")
        if fragment:
            self.assertIn(fragment, "\n".join(errors))

    def test_schema_and_complete_example(self):
        Draft202012Validator.check_schema(SCHEMA)
        self.assertFalse(hasattr(CONTRACT, "CONTRACT_VERSION"))
        self.assertNotIn("schema_version", BASE)
        self.assertTrue(VALIDATOR.is_valid(BASE))
        self.assertEqual(CONTRACT.validate_document(BASE, require_ready=True), [])
        self.assertEqual({u["kind"] for u in BASE["units"]},
                         {"title", "heading", "paragraph", "list_item",
                          "table_cell", "caption", "alt_text"})
        before = self.doc()
        CONTRACT.validate_document(BASE, require_ready=True)
        self.assertEqual(BASE, before)

    def test_source_snapshot_and_asset_integrity(self):
        root = EXAMPLE.parent
        manifest = json.loads((root / "MANIFEST.json").read_text())
        raw = (root / manifest["source"]["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest["source"]["sha256"])
        self.assertEqual(len(raw), manifest["source"]["bytes"])
        self.assertEqual([u["id"] for u in BASE["units"]],
                         [u["id"] for u in manifest["units"]])
        for unit, span in zip(BASE["units"], manifest["units"]):
            exact = raw[span["start"]:span["end"]]
            self.assertEqual(exact.decode("utf-8"), unit["source"])
            self.assertEqual(hashlib.sha256(exact).hexdigest(), unit["source_hash"])
            self.assertEqual(unit["source_hash"], span["sha256"])
        for entry in manifest["assets"]:
            asset = (root / entry["path"]).read_bytes()
            self.assertEqual(len(asset), entry["bytes"])
            self.assertEqual(hashlib.sha256(asset).hexdigest(), entry["sha256"])
            self.assertTrue(asset.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_missing_extra_and_wrong_type_fields(self):
        cases = [None, [], {"schema_version": 1}]
        for key in ("languages", "units", "blocks"):
            doc = self.doc()
            del doc[key]
            cases.append(doc)
        for key, value in (("schema_version", True), ("schema_version", 2),
                           ("units", []), ("blocks", []), ("rich", {})):
            doc = self.doc()
            doc[key] = value
            cases.append(doc)
        for data in cases:
            with self.subTest(data=data):
                self.assertFalse(VALIDATOR.is_valid(data))
                self.rejects(data)

    def test_plain_unicode_and_literal_markup_are_not_executed(self):
        for text in ("عدد 12", "雪と水", "x < 5 & y > 2",
                     "<script>alert('literal')</script>", r"\input{literal}",
                     "line\nnext\tcell", "e\u0301"):
            with self.subTest(text=text):
                doc = self.doc()
                unit = doc["units"][2]
                unit["source"] = text
                unit["source_hash"] = CONTRACT.source_digest(text)
                unit["target"] = None
                unit["target_source_hash"] = None
                unit["status"] = "untranslated"
                self.assertTrue(VALIDATOR.is_valid(doc))
                self.assertEqual(CONTRACT.validate_document(doc), [])
                self.assertEqual(unit["source"], text)

    def test_unsupported_rich_text_and_unsafe_controls(self):
        for value in ({"runs": [{"text": "rich"}]}, "", " \t\n",
                      "bad\0text", "bad\u202etext", "bad\u2067text", "\ud800"):
            for field in ("source", "target"):
                with self.subTest(field=field, value=repr(value)):
                    doc = self.doc()
                    doc["units"][2][field] = value
                    self.assertFalse(VALIDATOR.is_valid(doc))
                    self.rejects(doc)

    def test_hash_uses_exact_utf8_without_normalization(self):
        self.assertEqual(CONTRACT.source_digest("abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertNotEqual(CONTRACT.source_digest("é"), CONTRACT.source_digest("e\u0301"))
        self.assertNotEqual(CONTRACT.source_digest("text"), CONTRACT.source_digest("text "))
        doc = self.doc()
        doc["units"][2]["source"] += " "
        self.rejects(doc, "source_hash")

    def test_stable_ids_and_identifier_boundaries(self):
        doc = self.doc()
        doc["units"][2]["id"] = "intro.part-1:stable"
        doc["blocks"][2]["unit"] = "intro.part-1:stable"
        doc["units"].reverse()
        self.assertEqual(CONTRACT.validate_document(doc, True), [])
        for field, value in (("id", "bad\n"), ("id", "12"), ("source_hash", "a" * 64 + "\n")):
            bad = self.doc()
            bad["units"][0][field] = value
            self.assertFalse(VALIDATOR.is_valid(bad))
            self.rejects(bad)

    def test_language_roles_are_independent_of_layout(self):
        doc = self.doc()
        doc["languages"] = {"source": {"tag": "ar", "dir": "rtl"},
                            "target": {"tag": "ja", "dir": "ltr"}}
        self.assertEqual(CONTRACT.validate_document(doc, True), [])
        for tag in ("", "en_US", "en\n"):
            doc["languages"]["source"]["tag"] = tag
            self.assertFalse(VALIDATOR.is_valid(doc))
            self.rejects(doc)

    def test_duplicate_missing_and_unused_ids(self):
        doc = self.doc()
        doc["units"].append(copy.deepcopy(doc["units"][0]))
        self.rejects(doc, "duplicate ID")
        doc = self.doc()
        doc["blocks"][2]["unit"] = "absent"
        self.rejects(doc, "missing unit")
        doc = self.doc()
        doc["blocks"].append(copy.deepcopy(doc["blocks"][2]))
        self.rejects(doc, "exactly one structural use")
        doc = self.doc()
        doc["blocks"].pop(2)
        self.rejects(doc, "found 0")

    def test_group_kinds_and_real_table_cells(self):
        mutations = [
            lambda d: d["blocks"][0].update(level=2),
            lambda d: d["blocks"][3]["items"].__setitem__(0, "intro"),
            lambda d: d["blocks"][4]["headers"].__setitem__(0, "dry"),
            lambda d: d["blocks"][6].update(alt="figure-caption"),
            lambda d: d["blocks"][4]["rows"][0].pop(),
        ]
        for mutate in mutations:
            doc = self.doc()
            mutate(doc)
            self.assertTrue(VALIDATOR.is_valid(doc), "case should target semantic structure")
            self.rejects(doc)
        for mutate in (lambda d: d["blocks"][3].update(items=[]),
                       lambda d: d["blocks"][4].update(headers=[]),
                       lambda d: d["blocks"][6].pop("alt")):
            doc = self.doc()
            mutate(doc)
            self.assertFalse(VALIDATOR.is_valid(doc))
            self.rejects(doc)

    def test_table_caption_is_optional_without_unused_unit(self):
        doc = self.doc()
        del doc["blocks"][4]["caption"]
        doc["units"] = [u for u in doc["units"] if u["id"] != "table-caption"]
        self.assertEqual(CONTRACT.validate_document(doc, True), [])

    def test_asset_paths_are_relative_and_literal(self):
        for path in ("../shelf.png", "/shelf.png", "assets/../shelf.png", "assets/./shelf.png",
                     "assets//shelf.png", "https://example.com/a.png", "a.png?x=1",
                     r"assets\shelf.png", "a.png\n", "assets/"):
            with self.subTest(path=path):
                doc = self.doc()
                doc["blocks"][6]["asset"] = path
                self.assertFalse(VALIDATOR.is_valid(doc))
                self.rejects(doc)

    def test_draft_untranslated_and_needs_review_states(self):
        for status in ("draft", "needs_review", "untranslated"):
            with self.subTest(status=status):
                doc = self.doc()
                unit = doc["units"][2]
                unit["status"] = status
                if status == "untranslated":
                    unit["target"] = unit["target_source_hash"] = None
                self.assertEqual(CONTRACT.validate_document(doc), [])
                self.rejects(doc, "not ready", ready=True)
        doc = self.doc()
        doc["units"][2]["target"] = None
        self.rejects(doc, "null target")
        doc = self.doc()
        doc["units"][2]["status"] = "untranslated"
        self.rejects(doc, "nonempty target")

    def test_stale_target_requires_needs_review(self):
        for status in ("draft", "reviewed"):
            doc = self.doc()
            doc["units"][2]["status"] = status
            doc["units"][2]["target_source_hash"] = "0" * 64
            self.rejects(doc, "stale")
            doc["units"][2]["status"] = "needs_review"
            self.assertEqual(CONTRACT.validate_document(doc), [])
            self.rejects(doc, "not ready", ready=True)

    def test_validation_rejects_stale_source_without_mutating_any_content(self):
        doc = self.doc()
        doc["units"][2]["source"] += " Changed."
        before = copy.deepcopy(doc)
        for ready in (False, True):
            self.rejects(doc, "source_hash", ready=ready)
            self.assertEqual(doc, before)

    def test_exchange_exposes_no_authoring_helpers_or_commands(self):
        for name in ("sync_document", "record_review", "save_document", "untranslated_errors", "unit_view"):
            self.assertFalse(hasattr(CONTRACT, name), name)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exchange.json"
            path.write_text(json.dumps(BASE))
            before = path.read_bytes()
            command = [sys.executable, "-B", str(SKILL / "scripts/translation_contract.py")]
            for args in (["sync", str(path), "--in-place"],
                         ["record-review", str(path), "--unit", "intro", "--target", "Changed"],
                         ["view", str(path), "--unit", "intro"],
                         ["validate", str(path), "--untranslated"]):
                with self.subTest(args=args):
                    result = subprocess.run(command + args, capture_output=True, text=True, timeout=15)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_validation_cli_is_read_only_for_valid_and_stale_exchange(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exchange.json"
            command = [sys.executable, "-B", str(SKILL / "scripts/translation_contract.py")]
            for stale in (False, True):
                doc = self.doc()
                if stale:
                    doc["units"][2]["source"] += " Changed."
                path.write_text(json.dumps(doc))
                before = path.read_bytes()
                for flags in ([], ["--ready"]):
                    result = subprocess.run(command + ["validate", str(path)] + flags,
                                            capture_output=True, text=True, timeout=15)
                    self.assertEqual(result.returncode, int(stale), result.stderr)
                    self.assertEqual(path.read_bytes(), before)
                self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_installed_copy_is_self_contained_and_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / "translation-only"
            shutil.copytree(SKILL, installed)
            command = [sys.executable, "-I", str(installed / "scripts/translation_contract.py")]
            result = subprocess.run(command + ["validate", str(installed / "examples/guide/translation.json"), "--ready"],
                                    cwd=directory, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Semantic accuracy is not checked", result.stdout)
            path = Path(directory) / "bad.json"
            for content in ('{"units": [], "units": []}', '{"x": NaN}'):
                path.write_text(content)
                result = subprocess.run(command + ["validate", str(path)], cwd=directory,
                                        capture_output=True, text=True, timeout=15)
                self.assertNotEqual(result.returncode, 0)

    def test_review_status_cannot_establish_semantic_accuracy(self):
        doc = self.doc()
        doc["units"][2]["target"] = "This deliberately unrelated text is not a translation."
        self.assertEqual(CONTRACT.validate_document(doc, True), [],
                         "the structural checker must not pretend to judge semantic accuracy")


class WorkflowWriteSafetyTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("contract_write_workflow", SKILL / "scripts/workflow.py")
        self.workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.workflow)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.master = self.root / "master.jsonl"

    def prepare(self, text):
        source, receipt = self.root / "source.md", self.root / "read.json"
        source.write_bytes(text.encode("utf-8"))
        page = self.workflow.read_source(source, receipt)
        self.assertTrue(page["complete"])
        self.workflow.initialize(source, receipt, self.master, page["ref"])
        return self.workflow.next_block(self.master)

    def test_table_and_list_groups_use_one_atomic_save_without_source_changes(self):
        for text in ("| Crop | Count |\n| --- | --- |\n| Bean | 3 |\n",
                     "- Dry packets\n- Label packets\n"):
            with self.subTest(text=text):
                # Each case uses a distinct workflow directory.
                self.root = Path(self.temp.name) / str(len(list(Path(self.temp.name).iterdir())))
                self.root.mkdir()
                self.master = self.root / "master.jsonl"
                block = self.prepare(text)
                core = self.workflow.core
                before = core.load_jsonl(self.master)
                targets = {u["id"]: "Translated " + u["source"] for u in block["units"]}
                with patch.object(core.os, "replace", wraps=core.os.replace) as replace:
                    saved = self.workflow.mutate(self.master, "save", {"ref": block["ref"], "targets": targets})
                self.assertEqual(replace.call_count, 1)
                self.assertEqual(saved["saved"], list(targets))
                after = core.load_jsonl(self.master)
                self.assertEqual(after["document"]["source"], before["document"]["source"])
                self.assertEqual(after["document"]["blocks"], before["document"]["blocks"])
                for old, new in zip(before["units"], after["units"], strict=True):
                    for key in old.keys() - {"target", "target_hash", "target_source_hash", "status", "review"}:
                        self.assertEqual(old[key], new[key])
                    self.assertEqual(new["target"], targets[new["id"]])
                    self.assertEqual(new["status"], "draft")
                    self.assertIsNone(new["review"])
                self.assertEqual((self.root / "source.md").read_bytes(), text.encode("utf-8"))
                self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_stale_later_cell_rejects_whole_group_without_save(self):
        block = self.prepare("| Crop | Count |\n| --- | --- |\n| Bean | 3 |\n")
        core = self.workflow.core
        data = core.load_jsonl(self.master)
        data["units"][-1]["source"] = "4"
        # Simulate external corruption after dispatch; the actor cannot edit source.
        self.master.write_text("\n".join(json.dumps(v) for v in [data["document"]] + data["units"]) + "\n")
        before = self.master.read_bytes()
        payload = {"ref": block["ref"], "targets": {u["id"]: "Translated" for u in block["units"]}}
        with patch.object(core.os, "replace", wraps=core.os.replace) as replace:
            with self.assertRaises(ValueError):
                self.workflow.mutate(self.master, "save", payload)
        self.assertEqual(replace.call_count, 0)
        self.assertEqual(self.master.read_bytes(), before)
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_invalid_later_target_and_symlink_save_preserve_master(self):
        block = self.prepare("First.\n\nSecond.\n")
        targets = {u["id"]: "Translated" for u in block["units"]}
        before = self.master.read_bytes()
        invalid = dict(targets)
        invalid[block["units"][-1]["id"]] = ""
        with self.assertRaises(ValueError):
            self.workflow.mutate(self.master, "save", {"ref": block["ref"], "targets": invalid})
        alias = self.root / "alias.jsonl"
        alias.symlink_to(self.master)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.workflow.mutate(alias, "save", {"ref": block["ref"], "targets": targets})
        self.assertEqual(self.master.read_bytes(), before)
        self.assertTrue(alias.is_symlink())
        self.assertEqual(list(self.root.glob(".*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
