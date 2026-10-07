"""Optional translation-v1 adapter; legacy rendering remains independent."""
import copy
import importlib.util
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
from import_translation import load_contract, convert_pairs, read_json
from bilingual_pdf import InputError, tex_parts


def fixture(contract):
    texts = [
        ("title", "title", "A paired guide", "Un guide bilingue"),
        ("intro", "heading", "Read one pair", "Lisez une paire"),
        ("paragraph", "paragraph", "Keep 12 items, not 10.", "Gardez 12 éléments, pas 10."),
        ("item.A", "list_item", "Review the source.", "Relisez la source."),
        ("item.B", "list_item", "Save the pair.", "Enregistrez la paire."),
        ("table.head", "table_cell", "State", "État"),
        ("table.cell", "table_cell", "Reviewed", "Relu"),
        ("table.caption", "caption", "One paired cell.", "Une cellule bilingue."),
        ("figure.caption", "caption", "A shared image.", "Une image partagée."),
        ("figure.alt", "alt_text", "Two connected boxes.", "Deux cases reliées."),
    ]
    units = [{"id": i, "kind": k, "source": s, "target": t, "source_hash": contract.source_digest(s), "target_source_hash": contract.source_digest(s), "status": "reviewed"} for i,k,s,t in texts]
    return {"schema_version": 1, "languages": {"source": {"tag": "en", "dir": "ltr"}, "target": {"tag": "fr", "dir": "ltr"}},
        "units": units, "blocks": [
            {"type": "heading", "unit": "title", "level": 1},
            {"type": "heading", "unit": "intro", "level": 2},
            {"type": "paragraph", "unit": "paragraph"},
            {"type": "list", "ordered": False, "items": ["item.A", "item.B"]},
            {"type": "table", "headers": ["table.head"], "rows": [["table.cell"]], "caption": "table.caption"},
            {"type": "figure", "asset": "diagram.png", "caption": "figure.caption", "alt": "figure.alt"}]}


class TranslationPDFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract(TRANSLATION)

    def setUp(self):
        self.data = fixture(self.contract)

    def test_exact_text_roles_and_traceability(self):
        original = copy.deepcopy(self.data)
        result = convert_pairs(self.data, self.contract)
        self.assertEqual(self.data, original)
        self.assertEqual(result["languages"], ["en", "fr"])
        self.assertEqual(result["blocks"][1]["text"], ["Keep 12 items, not 10.", "Gardez 12 éléments, pas 10."])
        self.assertEqual(result["translation"]["content"], original)
        self.assertEqual(set(result["translation"]["unit_mapping"]), {x["id"] for x in original["units"]})
        self.assertEqual(result["blocks"][3]["rows"], [[["Reviewed"]], [["Relu"]]])
        self.assertFalse(result["translation"]["unit_mapping"]["figure.alt"]["pdf_alt_encoded"])

    def test_source_role_can_be_physical_right(self):
        result = convert_pairs(self.data, self.contract, "right")
        self.assertEqual(result["languages"], ["fr", "en"])
        self.assertEqual(result["translation"]["column_roles"], ["target", "source"])
        self.assertEqual(result["blocks"][2]["text"], [["Relisez la source.", "Enregistrez la paire."], ["Review the source.", "Save the pair."]])
        self.assertEqual(result["translation"]["content"]["languages"]["source"]["tag"], "en")

    def test_stale_or_unreviewed_content_stops_before_mapping(self):
        for field, value in (("source", "Keep 15 items."), ("status", "draft")):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["units"][2][field] = value
                with self.assertRaisesRegex(InputError, "not ready"):
                    convert_pairs(data, self.contract)

    def test_unsupported_semantics_are_actionable(self):
        cases = [
            (lambda d: d["blocks"][3].update(ordered=True), "native enumerate"),
            (lambda d: d["blocks"][1].update(level=3), "deeper headings"),
            (lambda d: d["languages"]["target"].update(tag="de"), "Unsupported PDF profile"),
            (lambda d: d["languages"]["target"].update(dir="rtl"), "direction"),
        ]
        for mutate, message in cases:
            with self.subTest(message=message):
                data=copy.deepcopy(self.data);mutate(data)
                with self.assertRaisesRegex(InputError,message):
                    convert_pairs(data,self.contract)

    def test_text_is_escaped_by_existing_canonical_exporter(self):
        unit=self.data["units"][2]
        unit["source"]=r"Literal \input{secret} & 20%"
        unit["source_hash"]=unit["target_source_hash"]=self.contract.source_digest(unit["source"])
        result=convert_pairs(self.data,self.contract)
        body=tex_parts(result,"bilingual")[2]
        self.assertIn(r"\textbackslash{}input\{secret\} \& 20\%",body)
        self.assertNotIn(r"\input{secret}",body)

    def test_installed_paths_and_new_output_preservation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            renderer=root/"renderer with spaces";translation=root/"independent content"
            shutil.copytree(PDF,renderer)
            shutil.copytree(TRANSLATION,translation)
            source=root/"pairs.json";source.write_text(json.dumps(self.data))
            output=root/"layout.json"
            command=[sys.executable,str(renderer/"scripts/import_translation.py"),str(source),"--translation-skill",str(translation),"--output",str(output)]
            first=subprocess.run(command,cwd=root,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            before=output.read_bytes()
            second=subprocess.run(command,cwd=root,capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)
            self.assertIn("already exists",second.stderr)
            self.assertEqual(output.read_bytes(),before)
            self.assertEqual(json.loads(source.read_text()),self.data)

    def test_imported_caption_preserves_its_supplied_label_once(self):
        unit=next(x for x in self.data["units"] if x["id"]=="figure.caption")
        unit["source"]="Figure 1. A shared image."
        unit["source_hash"]=unit["target_source_hash"]=self.contract.source_digest(unit["source"])
        result=convert_pairs(self.data,self.contract)
        self.assertEqual(result["blocks"][-1].get("caption_prefix"),"none")
        body=tex_parts(result,"bilingual")[2]
        self.assertIn(r"\renewcommand\ParallelFigureLabel{}",body)
        self.assertEqual(body.count("Figure 1. A shared image."),1)

    def test_caption_prefix_schema_and_runtime_agree(self):
        import jsonschema
        from bilingual_pdf import validate
        schema=json.loads((PDF/"schemas/document.schema.json").read_text())
        result=convert_pairs(self.data,self.contract)
        for value in ("automatic","none"):
            result["blocks"][-1]["caption_prefix"]=value
            validate(result);jsonschema.Draft202012Validator(schema).validate(result)
        for value in ("hidden",False,[],None):
            result["blocks"][-1]["caption_prefix"]=value
            with self.subTest(value=value),self.assertRaises(InputError):validate(result)
            self.assertTrue(list(jsonschema.Draft202012Validator(schema).iter_errors(result)))
        result["blocks"][-1]["caption_prefix"]="automatic"
        result["blocks"][1]["caption_prefix"]="none"
        with self.assertRaises(InputError):validate(result)
        self.assertTrue(list(jsonschema.Draft202012Validator(schema).iter_errors(result)))

    def test_ambiguous_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"input.json"
            for value in ('{"units":[],"units":[]}', '{"version":NaN}'):
                path.write_text(value)
                with self.subTest(value=value),self.assertRaises(InputError):
                    read_json(path)

    def test_missing_or_incompatible_dependency_is_actionable(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            with self.assertRaisesRegex(InputError,"Discover the installed"):
                load_contract(path)
            (path/"scripts").mkdir();(path/"SKILL.md").write_text("fixture")
            (path/"scripts/translation_contract.py").write_text("CONTRACT_VERSION=9\n")
            with self.assertRaisesRegex(InputError,"version 1"):
                load_contract(path)


if __name__ == "__main__":
    unittest.main()
