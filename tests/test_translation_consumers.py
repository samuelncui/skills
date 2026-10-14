"""Compact workflow -> installed PDF export and semantic exchange -> installed HTML render.

The original fixture pairs are supplied content, not model-generated translations.
Review attestations exercise the protocol; these assertions do not grade meaning.
Real PDF compilation and browser inspection remain separate integration profiles.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_bilingual_html import DocumentTree, texts

ROOT = Path(__file__).resolve().parents[1]


class TranslationConsumerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.install_into(self.root)

    def install_into(self, root):
        """Use unrelated discovered paths, with no repository working directory."""
        self.root = root
        self.translation = root / "semantic owner" / "installed"
        self.pdf = root / "typesetter elsewhere"
        self.html = root / "web tools" / "renderer"
        for name, installed in (("bilingual-translation", self.translation),
                                ("bilingual-pdf", self.pdf),
                                ("bilingual-html", self.html)):
            shutil.copytree(ROOT / "skills" / name, installed,
                            ignore=shutil.ignore_patterns("__pycache__"))
        self.work = root / "working document"
        self.work.mkdir()
        self.master = self.work / "master.jsonl"

    def run_cli(self, script, *args, check=True, json_output=True, input_text=None):
        env = {key: value for key, value in os.environ.items()
               if key not in {"PYTHONPATH", "PYTHONHOME"}}
        result = subprocess.run([sys.executable, "-B", str(script), *map(str, args)],
                                cwd=self.work, env=env, capture_output=True,
                                text=True, timeout=30, input=input_text)
        if not check:
            return result
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout) if json_output else result.stdout

    def workflow(self, op, *, check=True, **fields):
        raw = self.run_cli(self.translation / "scripts/workflow.py",
                           "--master", self.master, *op.split(), check=check,
                           json_output=False,
                           input_text=json.dumps({"op": op, **fields}, ensure_ascii=False))
        if not check:
            return raw
        records = [json.loads(line) for line in raw.splitlines()]
        self.assertEqual(records[-1]["record_type"], "receipt")
        self.assertTrue(all(r["record_type"] == "unit" for r in records[:-1]))
        result = {k: v for k, v in records[-1].items() if k != "record_type"}
        result["units"] = [{k: v for k, v in r.items() if k != "record_type"}
                           for r in records[:-1]]
        return result

    def prepare_reviewed_master(self):
        fixture = json.loads((ROOT / "tests/fixtures/translation-chunks.json").read_text())
        chunks = fixture["chunks"]
        chunks[-1][0] += (" The log should also name the next person responsible for checking the "
                          "open condition, so that storing an object does not leave its next step unassigned.")
        chunks[-1][1] += "记录还应注明由谁负责下一次检查尚未满足的条件，以免物品入库后无人负责后续工作。"
        self.expected = ([fixture["title"]] + chunks + [
            ["Checklist", "检查清单"],
            ["Record the date.", "记录日期。"],
            ["State unresolved conditions.", "说明尚未解决的条件。"],
            ["Stage", "阶段"], ["Record", "记录"],
            ["Before work", "工作前"], ["Reported problem", "反映的问题"],
            ["After work", "工作后"], ["Observed result", "观察结果"],
            fixture["after"],
        ])
        self.parent_pairs = [fixture["title"],
                             ["".join(x[0] for x in chunks), "".join(x[1] for x in chunks)],
                             *self.expected[4:]]
        source = ("# " + fixture["title"][0] + "\n\n" +
                  "".join(pair[0] for pair in chunks) + "\n\n## Checklist\n\n" +
                  "- Record the date.\n- State unresolved conditions.\n\n" +
                  "| Stage | Record |\n| --- | --- |\n" +
                  "| Before work | Reported problem |\n| After work | Observed result |\n\n" +
                  fixture["after"][0] + "\n")
        self.source = self.work / "source.md"
        self.source.write_bytes(source.encode("utf-8"))
        page = self.workflow("prepare init", source=str(self.source),
                             source_lang="en", target_lang="zh-Hans", context={
            "summary": "Keep observations, tentative explanations and unresolved conditions distinct in a community repair log.",
            "audience": "community workshop volunteers",
        })
        self.assertEqual([u["source"] for u in page["units"]],
                         [pair[0] for pair in self.parent_pairs])
        self.assertEqual(len(page["oversize"]), 1)
        parent = page["oversize"][0]
        initialized = self.workflow("prepare split", ref=page["ref"], unit=parent["id"],
                                    cuts=[{"left": chunks[i][0][-48:],
                                           "right": chunks[i+1][0][:48]}
                                          for i in range(len(chunks)-1)])
        self.assertTrue(initialized["complete"])
        self.assertEqual(initialized.get("pending", []), [])
        targets = dict(self.expected)
        seen = []
        block = self.workflow("translate next")
        while not block.get("complete"):
            self.assertLessEqual(sum(len(u["source"]) for u in block["units"]), 2048)
            seen.extend(u["source"] for u in block["units"])
            saved = self.workflow("translate save", ref=block["ref"], targets={
                u["id"]: targets[u["source"]] for u in block["units"]})
            self.assertNotIn("next", saved)
            block = self.workflow("translate next")
        self.assertEqual(seen, [pair[0] for pair in self.expected])

        # Consumers must reject the very same manuscript before its review pass.
        pending = self.run_cli(self.pdf / "scripts/bilingual_pdf.py", "export", self.master,
                               "--translation-skill", self.translation,
                               "--output", self.work / "unreviewed-pdf", check=False)
        self.assertNotEqual(pending.returncode, 0)
        self.assertFalse((self.work / "unreviewed-pdf").exists())
        pending = self.workflow("export", output=str(self.work / "unreviewed.json"), check=False)
        self.assertNotEqual(pending.returncode, 0)
        self.assertFalse((self.work / "unreviewed.json").exists())

        seen_review = []
        block = self.workflow("review next")
        while not block.get("complete"):
            seen_review.extend((u["source"], u["target"]) for u in block["units"])
            accepted = self.workflow("review accept", ref=block["ref"],
                                     reviewer="supplied-fixture",
                                     note="Protocol fixture: supplied original pairs, not automatic semantic certification.")
            self.assertNotIn("next", accepted)
            block = self.workflow("review next")
        self.assertEqual(seen_review, [tuple(pair) for pair in self.expected])
        self.assertTrue(self.workflow("validate")["valid"])
        self.assertEqual(self.source.read_bytes(), source.encode("utf-8"))

    def test_compact_master_reaches_independently_installed_consumers(self):
        self.prepare_reviewed_master()
        before = self.master.read_bytes()
        records = [json.loads(line) for line in before.splitlines()]
        header, units = records[0], records[1:]
        pdf_out = self.work / "pdf-project"
        result = self.run_cli(self.pdf / "scripts/bilingual_pdf.py", "export", self.master,
                              "--translation-skill", self.translation, "--output", pdf_out)
        self.assertTrue(result["ok"])
        self.assertEqual([json.loads(line) for line in
                          (pdf_out / "translation-source.jsonl").read_bytes().splitlines()], records)
        mapping = json.loads((pdf_out / "translation-map.json").read_text())
        self.assertNotIn("contract_version", mapping)
        self.assertEqual(set(mapping["unit_mapping"]),
                         {unit["id"] for unit in units} | {parent["id"] for parent in header["parents"]})
        self.assertEqual((pdf_out / "paralleltext.sty").read_bytes(),
                         (self.pdf / "assets/paralleltext.sty").read_bytes())
        self.assertEqual((pdf_out / "content.tex").read_text().count("\\ParallelProseChunk"), 4)

        exchange = self.work / "reviewed-exchange.json"
        self.workflow("export", output=str(exchange))
        exchange_data = json.loads(exchange.read_text())
        self.assertEqual(exchange_data["blocks"], header["blocks"])
        self.assertEqual(exchange_data["languages"], header["languages"])
        self.assertEqual([(u["source"], u["target"]) for u in exchange_data["units"]],
                         [tuple(pair) for pair in self.parent_pairs])
        self.assertEqual([u["id"] for u in exchange_data["units"]],
                         [parent["id"] for parent in header["parents"]])
        self.assertTrue(all(u["status"] == "reviewed" for u in exchange_data["units"]))

        validator_hash = hashlib.sha256(
            (self.translation / "scripts/translation_contract.py").read_bytes()).hexdigest()
        imported = self.work / "html-import"
        self.run_cli(self.html / "scripts/bilingual_html.py", "import-pairs", exchange,
                     "--translation-skill", self.translation,
                     "--validator-sha256", validator_hash, "--tested-revision", "isolated-fixture",
                     "--output", imported, json_output=False)
        layout = json.loads((imported / "layout.json").read_text())
        self.assertEqual([b["type"] for b in layout["blocks"]],
                         ["heading", "paragraph", "heading", "list", "table", "paragraph"])
        self.assertEqual(layout["languages"], header["languages"])
        self.assertEqual(json.loads((imported / "import-record.json").read_text()),
                         {"validator_sha256": validator_hash,
                          "tested_revision": "isolated-fixture"})
        site = self.work / "html-site"
        self.run_cli(self.html / "scripts/bilingual_html.py", "render",
                     imported / "layout.json", "--output", site, json_output=False)
        tree = DocumentTree((site / "index.html").read_text())
        self.assertEqual([node["attrs"]["data-pair-id"] for node in tree.pairs()],
                         [unit["id"] for unit in exchange_data["units"]])
        self.assertEqual([tuple(texts(child) for child in node["children"]) for node in tree.pairs()],
                         [tuple(pair) for pair in self.parent_pairs])
        self.assertEqual(len(tree.by_tag("ul")), 1)
        self.assertEqual(len(tree.by_tag("table")), 1)
        self.assertEqual(len(tree.by_tag("th")), 2)
        self.assertEqual(len(tree.by_tag("td")), 4)
        self.assertTrue((site / "style.css").is_file())
        self.assertTrue((site / "LICENSE").is_file())
        self.assertEqual(self.master.read_bytes(), before)
        self.assertEqual(json.loads(exchange.read_text()), exchange_data)


if __name__ == "__main__":
    unittest.main()
