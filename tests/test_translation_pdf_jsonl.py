"""Real JSONL workflow-to-PDF integration; no second manuscript is authored."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "skills/bilingual-pdf"
TRANSLATION = ROOT / "skills/bilingual-translation"
sys.path.insert(0, str(PDF / "scripts"))
import bilingual_pdf as pdf
import import_translation as adapter


def make_master(root, *, source_side="en", stress=False):
    """Original supplied text pairs; gates record fixture review, not machine meaning."""
    workflow = adapter.load_workflow(TRANSLATION)
    fixture = json.loads((ROOT / "tests/fixtures/translation-chunks.json").read_text())
    pairs = fixture["chunks"]
    if stress:
        # Layout-only extremes deliberately repeat supplied text, not translations.
        pairs = [[a * (3 if i == 0 else 2 if i == 2 else 1), b * (1 if i % 2 == 0 else 6)]
                 for i, (a, b) in enumerate(pairs)]
    if source_side == "zh-Hans":
        fixture = {**fixture, "title": fixture["title"][::-1], "after": fixture["after"][::-1]}
        pairs = [pair[::-1] for pair in pairs]
    source = root / "source.md"
    source.write_text("# " + fixture["title"][0] + "\n\n" +
                      "".join(pair[0] for pair in pairs) + "\n\n" + fixture["after"][0] + "\n")
    receipt = root / "preread.json"
    page = workflow.read_source(source, receipt)
    while not page["complete"]:
        page = workflow.read_source(source, receipt, page["token"])
    workflow.ack_source(source, receipt, page["source_hash"], page["token"])
    master = root / "master.jsonl"
    workflow.initialize(source, receipt, master, source_lang=source_side,
                        target_lang="zh-Hans" if source_side == "en" else "en",
                        context={"audience": "community volunteers"})
    data = workflow.load_jsonl(master)
    parent = data["units"][1]
    offsets = []
    for pair in pairs[:-1]:
        offsets.append((offsets[-1] if offsets else 0) + len(pair[0]))
    workflow.split_unit(master, parent["id"], offsets, parent["source_hash"], data["document"]["revision"])
    targets = [fixture["title"][1]] + [pair[1] for pair in pairs] + [fixture["after"][1]]
    for index, target in enumerate(targets):
        block = workflow.next_block(master)
        uid = block["ids"][0]
        saved = workflow.commit(master, {"operation_id": "save" + str(index),
                    "revision": block["revision"], "block_id": block["block_id"],
                    "source_hashes": block["source_hashes"], "targets": {uid: target}})
        unit = next(u for u in workflow.load_jsonl(master)["units"] if u["id"] == uid)
        workflow.review(master, {"operation_id": "review" + str(index), "revision": saved["revision"],
                    "unit": uid, "source_hash": unit["source_hash"], "target_hash": unit["target_hash"],
                    "reviewer": "original-fixture-author",
                    "note": "Supplied original fixture pair; stress repetition is layout-only."})
    return master, workflow.load_jsonl(master, require_ready=True)


class JSONLPDFTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.master, self.data = make_master(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_direct_jsonl_preserves_master_and_exact_parent(self):
        original = copy.deepcopy(self.data)
        result = adapter.read_translation(self.master, TRANSLATION)
        self.assertEqual(self.data, original)
        self.assertEqual(result["translation"]["content"], original)
        paragraph = result["blocks"][0]
        self.assertEqual(len(paragraph["chunks"]), 3)
        for i, role in enumerate(("source", "target")):
            units = self.data["units"][1:4]
            self.assertEqual("".join(c["text"][i] for c in paragraph["chunks"]), "".join(u[role] for u in units))
            self.assertEqual(paragraph["text"][i], "".join(u[role] for u in units))
        mapping = result["translation"]["unit_mapping"]
        self.assertTrue(all(u["id"] in mapping for u in self.data["units"]))
        self.assertEqual([mapping[u["id"]]["has_more"] for u in self.data["units"][1:4]], [True, True, False])

    def test_chunk_output_and_selected_join_use_canonical_package(self):
        result = adapter.read_translation(self.master, TRANSLATION)
        bilingual = pdf.tex_parts(result, "bilingual")[2]
        self.assertEqual(bilingual.count(r"\begin{ParallelProseGroup}"), 2)
        self.assertEqual(bilingual.count(r"\ParallelProseChunk"), 4)
        self.assertNotIn(r"\begin{minipage}", bilingual)
        selected = pdf.tex_parts(result, "right")[2]
        self.assertNotIn(r"\ParallelProseChunk", selected)
        self.assertIn(pdf.escape(result["blocks"][0]["text"][1]), selected)
        self.assertIn(r"\ParallelProse{pair-1}", selected)

    def test_roles_reverse_without_mutating_semantic_source(self):
        result = adapter.read_translation(self.master, TRANSLATION, "right")
        self.assertEqual(result["languages"], ["zh-Hans", "en"])
        self.assertEqual(result["blocks"][0]["chunks"][0]["text"],
                         [self.data["units"][1]["target"], self.data["units"][1]["source"]])
        self.assertEqual(result["translation"]["content"], self.data)

    def test_runtime_schema_and_boundaries(self):
        import jsonschema
        result = adapter.read_translation(self.master, TRANSLATION)
        schema = json.loads((PDF / "schemas/document.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(result)
        mutations = [
            lambda x: x["blocks"][0].update(kind="heading"),
            lambda x: x["blocks"][0].update(flow="keep"),
            lambda x: x["blocks"][0].update(chunks=[]),
            lambda x: x["blocks"][0]["chunks"][0].update(text=["", "目标"]),
            lambda x: x["blocks"][0]["chunks"][0].update(id="pt-title"),
        ]
        for mutate in mutations:
            candidate = copy.deepcopy(result)
            mutate(candidate)
            with self.subTest(mutate=mutate), self.assertRaises(pdf.InputError):
                pdf.validate(candidate)
            self.assertTrue(list(jsonschema.Draft202012Validator(schema).iter_errors(candidate)))
        candidate = copy.deepcopy(result)
        candidate["blocks"][0]["chunks"][0]["text"][0] = candidate["blocks"][0]["chunks"][0]["text"][0].rstrip()
        with self.assertRaisesRegex(pdf.InputError, "concatenate exactly"):
            pdf.validate(candidate)
        candidate = copy.deepcopy(result)
        candidate["blocks"][0]["chunks"][0]["id"] = candidate["blocks"][1]["id"]
        with self.assertRaisesRegex(pdf.InputError, "collide"):
            pdf.validate(candidate)

    def test_export_direct_from_independent_install_preserves_jsonl(self):
        renderer = self.root / "separate renderer"
        translation = self.root / "content tools elsewhere"
        shutil.copytree(PDF, renderer)
        shutil.copytree(TRANSLATION, translation)
        out = self.root / "portable"
        cmd = [sys.executable, str(renderer / "scripts/bilingual_pdf.py"), "export", str(self.master),
               "--translation-skill", str(translation), "--output", str(out)]
        run = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        preserved = adapter.load_workflow(translation).load_jsonl(out / "translation-source.jsonl", require_ready=True)
        self.assertEqual(preserved, self.data)
        mapping = json.loads((out / "translation-map.json").read_text())
        self.assertEqual(mapping["contract_version"], 2)
        self.assertEqual((out / "paralleltext.sty").read_bytes(), (PDF / "assets/paralleltext.sty").read_bytes())
        again = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(again.returncode, 0)
        missing = subprocess.run([sys.executable, str(renderer / "scripts/bilingual_pdf.py"), "export",
                                  str(self.master), "--output", str(self.root / "missing")],
                                 cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("--translation-skill", missing.stdout)

    def test_legacy_metadata_is_ignored_and_provenance_never_clobbered(self):
        result = adapter.read_translation(self.master, TRANSLATION)
        for index, value in enumerate((None, "private note", {"content": {}}, {"contract_version": 2, "content": {}})):
            candidate = copy.deepcopy(result)
            candidate["translation"] = value
            out = self.root / ("legacy" + str(index))
            pdf.export_document(candidate, self.master, out, "bilingual")
            self.assertFalse((out / "translation-map.json").exists())
        occupied = self.root / "occupied"
        occupied.mkdir()
        existing = occupied / "translation-source.jsonl"
        existing.write_text("preserve me")
        with self.assertRaisesRegex(pdf.InputError, "already exists"):
            pdf.write_project(result, self.master, occupied, "bilingual")
        self.assertEqual(existing.read_text(), "preserve me")
        self.assertFalse((occupied / "document.tex").exists())
        collection = self.root / "collection"
        collection.mkdir()
        for stem in ("first", "second"):
            pdf.write_project(result, self.master, collection, "bilingual", stem=stem)
            self.assertTrue((collection / (stem + "-translation-source.jsonl")).exists())

    def test_managed_build_tracks_and_protects_master(self):
        from unittest.mock import patch
        result = adapter.read_translation(self.master, TRANSLATION)
        out = self.root / "managed"
        with patch.object(pdf, "compile_project", return_value={"ok": True}):
            pdf.build_document(result, self.master, out, "bilingual")
            manifest = json.loads((out / pdf.BUILD_MANIFEST).read_text())
            self.assertIn("translation-source.jsonl", manifest["files"])
            self.assertIn("translation-map.json", manifest["files"])
            before = (out / "translation-source.jsonl").stat().st_mtime_ns
            pdf.build_document(result, self.master, out, "bilingual")
            self.assertEqual((out / "translation-source.jsonl").stat().st_mtime_ns, before)
            (out / "translation-source.jsonl").write_text("user edit")
            with self.assertRaises(pdf.InputError):
                pdf.build_document(result, self.master, out, "bilingual")
            self.assertEqual((out / "translation-source.jsonl").read_text(), "user edit")

    def test_direct_cli_layout_override_without_second_manuscript(self):
        original = self.master.read_bytes()
        out = self.root / "configured"
        command = [sys.executable, str(PDF / "scripts/bilingual_pdf.py"), "export", str(self.master),
                   "--translation-skill", str(TRANSLATION), "--layout", '{"font_size":10.5,"leading":14}',
                   "--output", str(out)]
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("body-size=10.5,body-leading=14", (out / "languages.tex").read_text())
        self.assertEqual(self.master.read_bytes(), original)
        self.assertFalse((self.root / "layout.json").exists())
        for invalid in ('[]', '{"font_size":2}', '{"unknown":true}'):
            command[command.index("--layout") + 1] = invalid
            command[-1] = str(self.root / "invalid-layout")
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse((self.root / "invalid-layout").exists())

    def test_heading_before_chunks_selects_flow_safe_native_helper(self):
        result = adapter.read_translation(self.master, TRANSLATION)
        result["blocks"].insert(0, {"id": "section", "kind": "heading", "text": ["A heading", "标题"]})
        body = pdf.tex_parts(result, "bilingual")[2]
        self.assertIn(r"\ParallelProseSection{section}", body)
        ordinary = copy.deepcopy(result)
        ordinary["blocks"][1].pop("chunks")
        self.assertIn(r"\ParallelSection{section}", pdf.tex_parts(ordinary, "bilingual")[2])

    def test_stale_order_source_or_review_rejected_before_output(self):
        mutations = [
            lambda x: x["units"][1].update(has_more=False),
            lambda x: x["units"][1].update(source=x["units"][1]["source"] + "altered"),
            lambda x: x["units"][1].update(target="altered"),
            lambda x: x["units"][1].update(order=99),
            lambda x: x["units"][1].update(status="draft", review=None),
        ]
        for index, mutate in enumerate(mutations):
            candidate = copy.deepcopy(self.data)
            mutate(candidate)
            path = self.root / ("invalid" + str(index) + ".jsonl")
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in
                                    [candidate["document"]] + candidate["units"]))
            with self.subTest(index=index), self.assertRaises(pdf.InputError):
                adapter.read_translation(path, TRANSLATION)


if __name__ == "__main__":
    unittest.main()
