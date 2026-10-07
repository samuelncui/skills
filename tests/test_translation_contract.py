"""Objective v1 exchange regression tests; these do not grade translation quality."""
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
        self.assertEqual(CONTRACT.CONTRACT_VERSION, 1)
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

    def test_sync_preserves_all_content_and_invalidates_only_stale_target(self):
        doc = self.doc()
        doc["units"][2]["source"] = "The community shelf holds 13 packets."
        old = copy.deepcopy(doc)
        updated = CONTRACT.sync_document(doc)
        self.assertEqual(doc, old, "sync mutated its input")
        expected = copy.deepcopy(old)
        expected["units"][2]["source_hash"] = CONTRACT.source_digest(expected["units"][2]["source"])
        expected["units"][2]["status"] = "needs_review"
        self.assertEqual(updated, expected)
        self.assertEqual(CONTRACT.validate_document(updated), [])
        self.rejects(updated, "not ready", ready=True)
        self.assertEqual(CONTRACT.sync_document(updated), updated, "sync is not idempotent")

    def test_recording_review_is_one_slot_only_and_requires_current_source(self):
        doc = self.doc()
        original = copy.deepcopy(doc)
        uid = "intro"
        digest = doc["units"][2]["source_hash"]
        updated = CONTRACT.record_review(doc, uid, "Une nouvelle traduction vérifiée.",
                                         reviewed_source_hash=digest)
        self.assertEqual(doc, original)
        expected = copy.deepcopy(original)
        expected["units"][2]["target"] = "Une nouvelle traduction vérifiée."
        self.assertEqual(updated, expected)
        with self.assertRaisesRegex(ValueError, "reviewed source changed"):
            CONTRACT.record_review(doc, uid, "texte", reviewed_source_hash="0" * 64)
        with self.assertRaisesRegex(ValueError, "missing unit"):
            CONTRACT.record_review(doc, "absent", "texte", reviewed_source_hash=digest)
        with self.assertRaises(ValueError):
            CONTRACT.record_review(doc, uid, "", reviewed_source_hash=digest)

    def test_successive_review_updates_persist_one_master_and_exact_source(self):
        raw_source = (EXAMPLE.parent / "source.txt").read_bytes()
        master = self.doc()
        for unit in master["units"]:
            unit["target"] = unit["target_source_hash"] = None
            unit["status"] = "untranslated"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "master.json"
            CONTRACT.save_document(path, master)
            for selected in BASE["units"][:3]:
                master = json.loads(path.read_text())
                before = copy.deepcopy(master)
                master = CONTRACT.record_review(master, selected["id"], selected["target"],
                                                 reviewed_source_hash=selected["source_hash"])
                CONTRACT.save_document(path, master)
                for old, now in zip(before["units"], master["units"]):
                    self.assertEqual(old["source"], now["source"])
                    self.assertEqual(old["id"], now["id"])
                    if now["id"] != selected["id"]:
                        self.assertEqual(old, now)
                self.assertEqual(list(Path(directory).iterdir()), [path])
            self.assertEqual(json.loads(path.read_text()), master)
            self.assertEqual(sum(u["status"] == "reviewed" for u in master["units"]), 3)
        self.assertEqual((EXAMPLE.parent / "source.txt").read_bytes(), raw_source)

    def test_executed_preparation_readback_and_later_single_unit_update(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"master.json"
            command=[sys.executable,"-B",str(SKILL/"examples/guide/prepare_master.py"),"--output",str(path)]
            prepared=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(prepared.returncode,0,prepared.stderr)
            receipt=json.loads(prepared.stdout)
            self.assertTrue(receipt["preparation_readback"])
            master=json.loads(path.read_text())
            self.assertEqual(CONTRACT.untranslated_errors(master),[])
            self.assertEqual([u["source"] for u in master["units"]],[u["source"] for u in BASE["units"]])
            self.assertTrue(all(u["target"] is None for u in master["units"]))
            before=copy.deepcopy(master)
            unit=CONTRACT.unit_view(master,"intro",include_context=True)["unit"]
            update=[sys.executable,"-B",str(SKILL/"scripts/translation_contract.py"),"record-review",str(path),"--unit","intro","--source-hash",unit["source_hash"],"--target","A caller-reviewed example target."]
            recorded=subprocess.run(update,capture_output=True,text=True)
            self.assertEqual(recorded.returncode,0,recorded.stderr)
            result=json.loads(recorded.stdout)
            self.assertEqual(result["recorded_unit"],"intro")
            current=json.loads(path.read_text())
            for old,new in zip(before["units"],current["units"]):
                if old["id"]!="intro":self.assertEqual(old,new)
                else:self.assertEqual(new["source"],old["source"])
            self.assertEqual(list(Path(directory).iterdir()),[path])
            self.assertTrue(CONTRACT.untranslated_errors(current))
            rejected=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(rejected.returncode,0)

    def test_unit_view_is_complete_focused_and_read_only(self):
        master=self.doc();before=copy.deepcopy(master)
        view=CONTRACT.unit_view(master,"intro")
        self.assertEqual(view["unit"]["source"],master["units"][2]["source"])
        self.assertNotIn("context",view)
        self.assertNotIn("neighbor_sources",view)
        wider=CONTRACT.unit_view(master,"intro",include_context=True,neighbors=1)
        self.assertEqual(wider["context"],master["context"])
        self.assertEqual([u["id"] for u in wider["neighbor_sources"]],["preparing","dry"])
        cell=CONTRACT.unit_view(master,"bean-count")
        self.assertEqual(cell["table_context"],{"headers":["Crop","Packets"],"row":["Bean","3"]})
        self.assertTrue(CONTRACT.unit_view(master)["complete"])
        self.assertEqual(master,before)
        with self.assertRaises(ValueError):CONTRACT.unit_view(master,"missing")
        with self.assertRaises(ValueError):CONTRACT.unit_view(master,neighbors=-1)

    def test_preparation_cli_rejects_existing_targets_and_stale_review_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"master.json";path.write_text(json.dumps(BASE))
            command=[sys.executable,"-B",str(SKILL/"scripts/translation_contract.py")]
            rejected=subprocess.run(command+["validate",str(path),"--untranslated"],capture_output=True,text=True)
            self.assertNotEqual(rejected.returncode,0)
            self.assertIn("empty untranslated",rejected.stderr)
            original=path.read_bytes()
            result=subprocess.run(command+["record-review",str(path),"--unit","intro","--source-hash","0"*64,"--target","Changed"],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(path.read_bytes(),original)
            view=subprocess.run(command+["view",str(path),"--unit","intro"],capture_output=True,text=True)
            self.assertEqual(view.returncode,0,view.stderr)
            self.assertEqual(json.loads(view.stdout)["unit"]["id"],"intro")
            self.assertEqual(path.read_bytes(),original)

    def test_reviewed_row_or_short_list_composes_one_atomic_save(self):
        # Existing-API composition, not an automated semantic group classifier.
        for identifiers in (("bean-name", "bean-count"), ("dry", "label")):
            with self.subTest(identifiers=identifiers), tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/"master.json";master=self.doc()
                reviews=[(u["id"],u["target"],u["source_hash"]) for u in master["units"] if u["id"] in identifiers]
                for unit in master["units"]:
                    if unit["id"] in identifiers:unit.update(target=None,target_source_hash=None,status="untranslated")
                CONTRACT.save_document(path,master);before=copy.deepcopy(master)
                pending=master
                with patch.object(CONTRACT.os,"replace",wraps=CONTRACT.os.replace) as replacements:
                    for uid,target,digest in reviews:
                        pending=CONTRACT.record_review(pending,uid,target,reviewed_source_hash=digest)
                    CONTRACT.save_document(path,pending)
                    self.assertEqual(replacements.call_count,1)
                current=json.loads(path.read_text())
                self.assertEqual(master,before)
                self.assertEqual(current["blocks"],before["blocks"])
                self.assertEqual([u["id"] for u in current["units"]],[u["id"] for u in before["units"]])
                for old,new in zip(before["units"],current["units"]):
                    self.assertEqual(new["source"],old["source"])
                    self.assertEqual(new["source_hash"],old["source_hash"])
                    if old["id"] not in identifiers:self.assertEqual(new,old)
                    else:
                        self.assertEqual(new["status"],"reviewed")
                        self.assertEqual(new["target"],next(text for uid,text,_ in reviews if uid==old["id"]))
                self.assertEqual(list(Path(directory).iterdir()),[path])

    def test_stale_later_cell_leaves_entire_saved_group_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"master.json";master=self.doc()
            by_id={u["id"]:u for u in master["units"]}
            reviews=[("bean-name","Haricot",by_id["bean-name"]["source_hash"]),
                     ("bean-count","3",by_id["bean-count"]["source_hash"])]
            by_id["bean-count"]["source"]="4"
            master=CONTRACT.sync_document(master)
            CONTRACT.save_document(path,master);original=path.read_bytes();before=copy.deepcopy(master)
            with patch.object(CONTRACT.os,"replace",wraps=CONTRACT.os.replace) as replacements:
                with self.assertRaisesRegex(ValueError,"reviewed source changed"):
                    pending=master
                    for uid,target,digest in reviews:
                        pending=CONTRACT.record_review(pending,uid,target,reviewed_source_hash=digest)
                    CONTRACT.save_document(path,pending)
                self.assertEqual(replacements.call_count,0)
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(master,before)
            self.assertEqual(list(Path(directory).iterdir()),[path])

    def test_invalid_atomic_save_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "master.json"
            CONTRACT.save_document(path, BASE)
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                CONTRACT.save_document(path, {"invalid": True})
            self.assertEqual(path.read_bytes(), original)
            alias = Path(directory) / "alias.json"
            alias.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "symlink"):
                CONTRACT.save_document(alias, BASE)

    def test_cli_in_place_and_checkpoint_preserve_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, checkpoint = root / "master.json", root / "checkpoint.json"
            doc = self.doc()
            doc["units"][2]["source"] += " A new sentence."
            path.write_text(json.dumps(doc))
            command = [sys.executable, "-B", str(SKILL / "scripts/translation_contract.py")]
            result = subprocess.run(command + ["sync", str(path), "--in-place"],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            master = json.loads(path.read_text())
            self.assertEqual(master["units"][2]["target"], doc["units"][2]["target"])
            self.assertEqual(master["units"][2]["status"], "needs_review")
            before = path.read_bytes()
            result = subprocess.run(command + ["sync", str(path), "--output", str(checkpoint)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(json.loads(checkpoint.read_text()), master)
            result = subprocess.run(command + ["sync", str(path), "--output", str(checkpoint)],
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            result = subprocess.run(command + ["validate", str(path), "--ready"],
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)

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
            for content in ('{"schema_version": 1, "schema_version": 1}', '{"x": NaN}'):
                path.write_text(content)
                result = subprocess.run(command + ["validate", str(path)], cwd=directory,
                                        capture_output=True, text=True, timeout=15)
                self.assertNotEqual(result.returncode, 0)

    def test_review_status_cannot_establish_semantic_accuracy(self):
        doc = self.doc()
        doc["units"][2]["target"] = "This deliberately unrelated text is not a translation."
        self.assertEqual(CONTRACT.validate_document(doc, True), [],
                         "the structural checker must not pretend to judge semantic accuracy")


if __name__ == "__main__":
    unittest.main()
