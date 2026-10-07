"""Renderer public-contract tests; run with unittest, no third-party packages."""
import copy
import hashlib
from html.parser import HTMLParser
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "bilingual-html"
TRANSLATION_SKILL = ROOT / "skills" / "bilingual-translation"
SPEC = importlib.util.spec_from_file_location("bilingual_html", SKILL / "scripts" / "bilingual_html.py")
RENDERER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDERER)


class DocumentTree(HTMLParser):
    """Small HTML tree for asserting public structure instead of string snapshots."""
    VOID = {"meta", "link", "img", "br", "hr", "input"}

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = {"tag": "root", "attrs": {}, "children": []}
        self.stack = [self.root]
        self.nodes = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "children": [], "parent": self.stack[-1]}
        self.stack[-1]["children"].append(node)
        self.nodes.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if len(self.stack) > 1 and self.stack[-1]["tag"] == tag:
            self.stack.pop()
        else:
            raise AssertionError(f"Unbalanced HTML end tag: {tag}")

    def handle_data(self, text):
        self.stack[-1]["children"].append(text)

    def by_tag(self, tag):
        return [node for node in self.nodes if node["tag"] == tag]

    def pairs(self):
        return [node for node in self.nodes if "data-pair-id" in node["attrs"]]


def texts(node):
    return "".join(child if isinstance(child, str) else texts(child) for child in node["children"])


def example():
    return json.loads((SKILL / "examples" / "tutorial" / "layout.json").read_text(encoding="utf-8"))


def pair(identifier="p", source="Source", target="Cible"):
    return {"id": identifier, "source": source, "target": target}


def minimal():
    return {"layout_version": 1,
            "languages": {"source": {"tag": "en", "dir": "ltr"}, "target": {"tag": "fr", "dir": "ltr"}},
            "blocks": [{"type": "paragraph", "pair": pair()}]}


class BilingualHTMLTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_input(self, data=None, name="input.json"):
        path = self.base / name
        path.write_text(json.dumps(data if data is not None else minimal(), ensure_ascii=False), encoding="utf-8")
        return path

    def run_cli(self, skill, *args):
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([sys.executable, str(skill / "scripts" / "bilingual_html.py"), *map(str, args)],
                              cwd=self.base, env=environment, capture_output=True, text=True, timeout=20)

    def test_literal_text_and_attribute_injection_are_escaped(self):
        data = minimal()
        attack = '<script>alert("x")</script> & <img src=x onerror=alert(1)> \\alpha'
        data["blocks"][0]["pair"] = pair("safe", attack, 'Une "citation" & <em>texte</em>')
        data["config"] = {"browser_title": '</title><script>alert(2)</script>'}
        rendered = RENDERER.render_html(data)
        tree = DocumentTree(rendered)
        self.assertFalse(tree.by_tag("script"))
        self.assertFalse(tree.by_tag("img"))
        self.assertEqual(texts(tree.pairs()[0]["children"][0]), attack)
        self.assertEqual(texts(tree.by_tag("title")[0]), data["config"]["browser_title"])
        self.assertIn("&lt;script&gt;", rendered)

    def test_every_pair_has_source_then_target_in_one_logical_container(self):
        data = example()
        tree = DocumentTree(RENDERER.render_html(data))
        self.assertGreater(len(tree.pairs()), 20)
        for node in tree.pairs():
            children = [x for x in node["children"] if isinstance(x, dict)]
            self.assertEqual([x["attrs"].get("data-role") for x in children], ["source", "target"])
            self.assertEqual([x["attrs"].get("lang") for x in children], ["en", "fr"])
        ids = [node["attrs"]["data-pair-id"] for node in tree.pairs()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertLess(ids.index("title"), ids.index("intro"))
        self.assertLess(ids.index("figure-alt"), ids.index("figure-caption"))

    def test_physical_order_does_not_change_roles_or_mobile_order(self):
        data = minimal()
        data["config"] = {"desktop_order": "target-first"}
        data["languages"]["source"] = {"tag": "ar", "dir": "rtl"}
        data["languages"]["target"] = {"tag": "en", "dir": "ltr"}
        data["blocks"][0]["pair"] = pair("rtl", "مرحبا بالعالم", "Hello world")
        tree = DocumentTree(RENDERER.render_html(data))
        self.assertEqual(tree.by_tag("body")[0]["attrs"]["class"], "target-first")
        children = tree.pairs()[0]["children"]
        self.assertEqual([(x["attrs"]["data-role"], x["attrs"]["lang"], x["attrs"]["dir"]) for x in children],
                         [("source", "ar", "rtl"), ("target", "en", "ltr")])
        css = (SKILL / "assets" / "style.css").read_text()
        self.assertIn('grid-template-areas: "target source"', css)
        mobile = css.split("@media (max-width: 48rem)", 1)[1].split("@media print", 1)[0]
        self.assertIn('grid-template-areas: "source" "target"', mobile)
        self.assertIn(".pair, .target-first .pair", mobile)

    def test_table_headers_rows_and_cells_are_real_table_elements(self):
        tree = DocumentTree(RENDERER.render_html(example()))
        self.assertEqual(len(tree.by_tag("table")), 1)
        self.assertEqual(len(tree.by_tag("thead")), 1)
        self.assertEqual(len(tree.by_tag("tbody")), 1)
        self.assertEqual(len(tree.by_tag("th")), 2)
        self.assertEqual(len(tree.by_tag("td")), 6)
        self.assertEqual(len(tree.by_tag("tr")), 4)
        for header in tree.by_tag("th"):
            self.assertEqual(header["attrs"].get("scope"), "col")
            self.assertEqual(header["parent"]["tag"], "tr")
        for cell in tree.by_tag("th") + tree.by_tag("td"):
            self.assertEqual(len(cell["children"]), 1)
            self.assertIn("data-pair-id", cell["children"][0]["attrs"])
        self.assertEqual(tree.by_tag("caption")[0]["parent"]["tag"], "table")

    def test_table_scroll_regions_are_named_and_keyboard_focusable(self):
        for with_caption in (True, False):
            data = example()
            table = next(block for block in data["blocks"] if block["type"] == "table")
            if not with_caption:
                table.pop("caption", None)
            tree = DocumentTree(RENDERER.render_html(data))
            region = tree.by_tag("table")[0]["parent"]
            self.assertEqual(region["attrs"].get("role"), "region")
            self.assertEqual(region["attrs"].get("tabindex"), "0")
            cue = next(node for node in region["children"] if isinstance(node, dict)
                       and node["attrs"].get("class") == "table-scroll-cue")
            self.assertEqual(cue["attrs"].get("aria-hidden"), "true")
            expected = table.get("caption", table["headers"][0])["id"]
            self.assertEqual(region["attrs"].get("aria-labelledby"), "pair-" + expected)
            self.assertTrue(any(node["attrs"].get("id") == "pair-" + expected for node in tree.nodes))

    def test_lists_figures_and_paired_alt_descriptions(self):
        tree = DocumentTree(RENDERER.render_html(example()))
        self.assertEqual(len(tree.by_tag("ol")), 1)
        self.assertEqual(len(tree.by_tag("ul")), 1)
        self.assertEqual(len(tree.by_tag("figure")), 1)
        self.assertEqual(len(tree.by_tag("img")), 1)
        image = tree.by_tag("img")[0]
        labelled = image["attrs"]["aria-labelledby"].split()
        index = {node["attrs"]["id"]: node for node in tree.nodes if "id" in node["attrs"]}
        self.assertEqual([index[x]["attrs"]["lang"] for x in labelled], ["en", "fr"])
        self.assertEqual(image["attrs"]["alt"], texts(index[labelled[0]]))
        self.assertIs(index[labelled[0]]["parent"], index[labelled[1]]["parent"])
        self.assertEqual(tree.by_tag("figcaption")[0]["parent"]["tag"], "figure")

    def test_malformed_documents_report_errors_without_mutation(self):
        variations = [
            None, [], {}, {"layout_version": 2},
        ]
        def changed(path, value):
            data = minimal()
            cursor = data
            for key in path[:-1]:
                cursor = cursor[key]
            cursor[path[-1]] = value
            return data
        variations += [
            changed(["layout_version"], True),
            changed(["languages", "source", "tag"], 'en" onload="x'),
            changed(["languages", "target", "dir"], "auto"),
            changed(["languages", "source"], []),
            changed(["blocks"], []),
            changed(["blocks"], [{"type": "html", "html": "<b>x</b>"}]),
            changed(["blocks", 0, "pair", "id"], "9bad"),
            changed(["blocks", 0, "pair", "source"], " "),
            changed(["blocks", 0, "pair", "target"], None),
            changed(["blocks", 0, "pair", "target"], "bad\x00text"),
            changed(["blocks", 0, "pair", "target"], "\ud800"),
            changed(["blocks"], [{"type": "heading", "level": True, "pair": pair()}]),
            changed(["blocks"], [{"type": "list", "ordered": "yes", "items": []}]),
            changed(["blocks"], [{"type": "table", "headers": [pair("h")], "rows": [[], [pair("c"), pair("d")]]}]),
            changed(["blocks"], [{"type": "paragraph", "pair": pair()}, {"type": "paragraph", "pair": pair()}]),
        ]
        for data in variations:
            before = copy.deepcopy(data)
            with self.subTest(data=repr(data)):
                self.assertTrue(RENDERER.validate_document(data))
                self.assertEqual(data, before)

    def test_styles_reject_injection_and_allow_sparse_safe_configuration(self):
        data = minimal()
        data["config"] = {"styles": {"source_font": ["Noto Sans", "sans-serif"], "target_font": ["serif"],
                                    "background": "#ffffff", "column_gap": "2rem", "line_height": 1.7,
                                    "source_weight": 1, "target_weight": 1.5}}
        source = self.write_input(data)
        output = RENDERER.render_document(source, self.base / "page")
        css = (output / "style.css").read_text()
        self.assertIn('--source-font: "Noto Sans", sans-serif;', css)
        self.assertIn("--target-weight: 1.5fr;", css)
        for styles in ({"background": "red; background:url(https://example.test)"},
                       {"source_font": ["x\"; color:red"]}, {"font_size": "0px"},
                       {"column_gap": "1001rem"}, {"line_height": True}, {"line_height": float("nan")},
                       {"unknown": "x"}):
            data["config"]["styles"] = styles
            self.assertTrue(RENDERER.validate_document(data), styles)
        data["config"] = {"desktop_order": "left-right"}
        self.assertTrue(RENDERER.validate_document(data))

    def test_portable_render_preserves_assets_and_is_deterministic(self):
        source = SKILL / "examples" / "tutorial" / "layout.json"
        one = RENDERER.render_document(source, self.base / "one")
        two = RENDERER.render_document(source, self.base / "two")
        inventory = {p.relative_to(one): p.read_bytes() for p in one.rglob("*") if p.is_file()}
        self.assertEqual(inventory, {p.relative_to(two): p.read_bytes() for p in two.rglob("*") if p.is_file()})
        self.assertEqual(inventory[Path("images/pairs.png")], (source.parent / "images/pairs.png").read_bytes())
        self.assertEqual(set(inventory), {Path("index.html"), Path("style.css"), Path("LICENSE"), Path("images/pairs.png")})
        tree = DocumentTree((one / "index.html").read_text())
        self.assertFalse(tree.by_tag("script"))
        self.assertEqual([x["attrs"].get("href") for x in tree.by_tag("link")], ["style.css"])
        self.assertTrue(all("://" not in x["attrs"]["src"] for x in tree.by_tag("img")))

    def test_asset_traversal_urls_symlinks_and_invalid_png_are_rejected(self):
        data = minimal()
        data["blocks"] = [{"type": "figure", "asset": "picture.png", "caption": pair("caption"), "alt": pair("alt")}]
        for bad in ("../image.png", "/image.png", "https://example.test/a.png", "x\\a.png", "x//a.png",
                    "./a.png", "picture.svg", "x/../a.png"):
            data["blocks"][0]["asset"] = bad
            self.assertTrue(RENDERER.validate_document(data), bad)
        data["blocks"][0]["asset"] = "picture.png"
        source = self.write_input(data)
        with self.assertRaises(RENDERER.RenderError):
            RENDERER.render_document(source, self.base / "missing")
        png = SKILL / "examples" / "tutorial" / "images" / "pairs.png"
        (self.base / "picture.png").symlink_to(png)
        with self.assertRaisesRegex(RENDERER.RenderError, "Symlink"):
            RENDERER.render_document(source, self.base / "symlink")
        (self.base / "picture.png").unlink()
        (self.base / "picture.png").write_bytes(b"not a PNG")
        with self.assertRaises(RENDERER.RenderError):
            RENDERER.render_document(source, self.base / "invalid")
        (self.base / "picture.png").write_bytes(png.read_bytes() + b"<script>")
        with self.assertRaisesRegex(RENDERER.RenderError, "after IEND"):
            RENDERER.render_document(source, self.base / "trailing")
        (self.base / "picture.png").write_bytes(png.read_bytes()[:-5])
        with self.assertRaises(RENDERER.RenderError):
            RENDERER.render_document(source, self.base / "truncated")
        (self.base / "linked").symlink_to(png.parent, target_is_directory=True)
        data["blocks"][0]["asset"] = "linked/pairs.png"
        source = self.write_input(data)
        with self.assertRaisesRegex(RENDERER.RenderError, "Symlink"):
            RENDERER.render_document(source, self.base / "directory-link")
        self.assertFalse((self.base / "invalid").exists())

    def test_output_never_overwrites_and_rejects_symlink_ancestors(self):
        source = self.write_input()
        output = self.base / "existing"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_text("keep")
        with self.assertRaisesRegex(RENDERER.RenderError, "already exists"):
            RENDERER.render_document(source, output)
        self.assertEqual(sentinel.read_text(), "keep")
        with self.assertRaisesRegex(RENDERER.RenderError, "already exists"):
            RENDERER.render_document(source, source)
        (self.base / "link").symlink_to(output, target_is_directory=True)
        with self.assertRaisesRegex(RENDERER.RenderError, "Symlink"):
            RENDERER.render_document(source, self.base / "link" / "new")
        with self.assertRaisesRegex(RENDERER.RenderError, "parent"):
            RENDERER.render_document(source, self.base / "absent" / "new")
        self.assertFalse((self.base / "absent").exists())

    def test_duplicate_json_keys_invalid_json_and_cli_error_exit(self):
        source = self.base / "bad.json"
        for value in ('{"layout_version":1,"layout_version":1}', "{", '{"number":NaN}'):
            source.write_text(value)
            with self.assertRaises(RENDERER.RenderError):
                RENDERER.load_json(source)
        source.write_text("{}")
        result = self.run_cli(SKILL, "render", source, "--output", self.base / "output")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)
        self.assertFalse((self.base / "output").exists())

    def test_clean_html_only_installation_renders_without_translation(self):
        installed = self.base / "installed-html"
        shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns("__pycache__", "site"))
        source = self.write_input()
        result = self.run_cli(installed, "render", source, "--output", self.base / "rendered")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.base / "rendered" / "index.html").is_file())
        self.assertFalse((self.base / "bilingual-translation").exists())
        self.assertNotIn(str(ROOT), (self.base / "rendered" / "index.html").read_text())

    def test_actual_separately_discovered_translation_adapter_and_pins(self):
        installed = self.base / "installed-html"
        semantic = self.base / "unrelated-location" / "content-skill"
        shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns("__pycache__", "site"))
        shutil.copytree(TRANSLATION_SKILL, semantic, ignore=shutil.ignore_patterns("__pycache__"))
        source = semantic / "examples" / "guide" / "translation.json"
        source_before = source.read_bytes()
        validator_hash = hashlib.sha256((semantic / "scripts" / "translation_contract.py").read_bytes()).hexdigest()
        result = self.run_cli(installed, "import-pairs", source, "--translation-skill", semantic,
                              "--contract-version", "1", "--validator-sha256", validator_hash,
                              "--tested-revision", "test-fixture", "--output", self.base / "imported")
        self.assertEqual(result.returncode, 0, result.stderr)
        imported = json.loads((self.base / "imported" / "layout.json").read_text())
        original = json.loads(source_before)
        tree = DocumentTree(RENDERER.render_html(imported))
        content = {x["attrs"]["data-pair-id"]: tuple(texts(c) for c in x["children"]) for x in tree.pairs()}
        self.assertEqual(content, {x["id"]: (x["source"], x["target"]) for x in original["units"]})
        self.assertEqual([x["type"] for x in imported["blocks"]], [x["type"] for x in original["blocks"]])
        self.assertEqual(imported["languages"], original["languages"])
        record = json.loads((self.base / "imported" / "import-record.json").read_text())
        self.assertEqual(record, {"translation_contract": 1, "validator_sha256": validator_hash,
                                  "tested_revision": "test-fixture"})
        rendered = self.run_cli(installed, "render", self.base / "imported" / "layout.json",
                                "--output", self.base / "final")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(source.read_bytes(), source_before)
        for figure in [x for x in original["blocks"] if x["type"] == "figure"]:
            self.assertEqual((self.base / "final" / figure["asset"]).read_bytes(),
                             (source.parent / figure["asset"]).read_bytes())

    def test_import_rejects_missing_dependency_wrong_pin_and_unready_content(self):
        source = TRANSLATION_SKILL / "examples" / "guide" / "translation.json"
        with self.assertRaisesRegex(RENDERER.RenderError, "separately installed"):
            RENDERER.import_pairs(source, self.base / "missing", None)
        with self.assertRaisesRegex(RENDERER.RenderError, "must provide"):
            RENDERER.import_pairs(source, self.base / "missing", self.base)
        with self.assertRaisesRegex(RENDERER.RenderError, "validator-sha256"):
            RENDERER.import_pairs(source, self.base / "bad-hash", TRANSLATION_SKILL, validator_sha256="0" * 64)
        with self.assertRaisesRegex(RENDERER.RenderError, "version 1"):
            RENDERER.import_pairs(source, self.base / "bad-version", TRANSLATION_SKILL, contract_version=2)
        original = json.loads(source.read_text())
        for changes in ({"target": None, "status": "untranslated", "target_source_hash": None},
                        {"status": "needs_review", "target_source_hash": "0" * 64},
                        {"source_hash": "0" * 64}):
            changed = copy.deepcopy(original)
            changed["units"][0].update(changes)
            input_path = self.write_input(changed)
            with self.assertRaisesRegex(RENDERER.RenderError, "not ready"):
                RENDERER.import_pairs(input_path, self.base / "not-ready", TRANSLATION_SKILL)
        self.assertFalse((self.base / "not-ready").exists())

    def test_jpeg_baseline_progressive_and_malformed_framing(self):
        data = minimal()
        data["blocks"] = [{"type": "figure", "asset": "picture.jpg", "caption": pair("caption"), "alt": pair("alt")}]
        source = self.write_input(data)
        for i, name in enumerate(("pairs.jpg", "pairs-progressive.jpg")):
            original = (SKILL / "examples" / "tutorial" / "images" / name).read_bytes()
            (self.base / "picture.jpg").write_bytes(original)
            result = RENDERER.render_document(source, self.base / f"jpeg-{i}")
            self.assertEqual((result / "picture.jpg").read_bytes(), original)
        baseline = (SKILL / "examples" / "tutorial" / "images" / "pairs.jpg").read_bytes()
        oversized = bytearray(baseline)
        frame = baseline.index(b"\xff\xc0")
        oversized[frame + 7:frame + 9] = (16001).to_bytes(2, "big")
        for invalid in (b"not a JPEG", b"\xff\xd8\xff\xd9", b"\xff\xd8\xff\xe0\x00\x01",
                        baseline[:-10], baseline + b"trailing", bytes(oversized)):
            (self.base / "picture.jpg").write_bytes(invalid)
            with self.assertRaises(RENDERER.RenderError):
                RENDERER.render_document(source, self.base / "bad-jpeg")
            self.assertFalse((self.base / "bad-jpeg").exists())

    def assert_example_manifest_current(self):
        examples = SKILL / "examples"
        manifest = json.loads((examples / "MANIFEST.json").read_text(encoding="utf-8"))
        records = manifest["files"]
        paths = [record["path"] for record in records]
        self.assertEqual(len(paths), len(set(paths)), "Duplicate example manifest paths")
        actual = {str(path.relative_to(examples)) for path in examples.rglob("*")
                  if path.is_file() and path.name != "MANIFEST.json" and "__pycache__" not in path.parts}
        self.assertEqual(set(paths), actual, "Example manifest inventory drift")
        for record in records:
            relative = Path(record["path"])
            self.assertFalse(relative.is_absolute() or ".." in relative.parts)
            path = examples / relative
            self.assertTrue(path.resolve().is_relative_to(examples.resolve()))
            contents = path.read_bytes()
            self.assertEqual(record["bytes"], len(contents), record["path"])
            self.assertEqual(record["sha256"], hashlib.sha256(contents).hexdigest(), record["path"])

    def test_curated_site_matches_current_renderer(self):
        self.assert_example_manifest_current()
        source = SKILL / "examples" / "tutorial" / "layout.json"
        generated = RENDERER.render_document(source, self.base / "current")
        shipped = source.parent / "site"
        self.assertEqual({p.relative_to(generated): p.read_bytes() for p in generated.rglob("*") if p.is_file()},
                         {p.relative_to(shipped): p.read_bytes() for p in shipped.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
