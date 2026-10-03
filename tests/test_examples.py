import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.collect_example_outputs import INPUTS, PDFS, collect_examples, check_examples

class ExampleTests(unittest.TestCase):
    def fixture(self, root):
        matrix = root / 'matrix'; matrix.mkdir()
        (matrix / 'matrix.json').write_text(json.dumps({'ok': True}))
        for name in PDFS.values():
            p = matrix / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'public example')
        source = root / 'source'; source.mkdir()
        for name in INPUTS:
            path = source / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'original input')
        (matrix / 'private.log').write_text('must not be copied')
        return matrix, source

    def test_explicit_allowlist_and_relative_course_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root); out = root / 'bundle'
            records = collect_examples(matrix, out, source)
            self.assertEqual(len(records), 6)
            self.assertTrue((out / 'skills/course-guide-quick-reference/examples/notes.pdf').exists())
            self.assertTrue((out / 'skills/course-guide-quick-reference/examples/quick-reference.pdf').exists())
            self.assertFalse((out / 'private.log').exists())
            self.assertTrue(all(not Path(x['path']).is_absolute() for x in records))
            self.assertEqual(check_examples(out, source), 6)

    def test_failed_matrix_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root)
            (matrix / 'matrix.json').write_text('{"ok": false}')
            with self.assertRaises(ValueError): collect_examples(matrix, root / 'bundle', source)

    def test_missing_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root)
            (matrix / next(iter(PDFS.values()))).unlink()
            with self.assertRaises(ValueError): collect_examples(matrix, root / 'bundle', source)

    def test_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root)
            (source / INPUTS[0]).unlink()
            with self.assertRaises(ValueError): collect_examples(matrix, root / 'bundle', source)

    def test_unlisted_example_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root); out = root / 'bundle'
            collect_examples(matrix, out, source)
            (out / 'skills/bilingual-pdf/examples/private.log').write_text('not publishable')
            with self.assertRaises(ValueError): check_examples(out, source)

    def test_manifests_use_only_installed_example_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root); out = root / 'bundle'
            collect_examples(matrix, out, source)
            manifests = list(out.glob('skills/*/examples/MANIFEST.json'))
            self.assertEqual(len(manifests), 2)
            for path in manifests:
                data = json.loads(path.read_text())
                self.assertTrue(data['source_hashes'])
                for name in list(data['source_hashes']) + [x['path'] for x in data['files']]:
                    self.assertFalse(Path(name).is_absolute())
                    self.assertNotIn('..', Path(name).parts)
                    self.assertFalse(name.startswith('skills/'))

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root); out = root / 'bundle'; out.mkdir()
            with self.assertRaises(ValueError): collect_examples(matrix, out, source)


class InstalledExampleTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]
    article_root = root / 'skills/bilingual-pdf/examples'

    def test_all_editions_share_one_complete_article(self):
        documents = [json.loads(p.read_text()) for p in sorted(self.article_root.glob('*/source.json'))]
        self.assertEqual(len(documents), 4)
        structure = None
        translations = {}
        for doc in documents:
            skeleton = [{k: v for k, v in b.items() if k not in ('text', 'headers', 'rows')} for b in doc['blocks']]
            if structure is None: structure = skeleton
            self.assertEqual(skeleton, structure)
            self.assertTrue(any(b.get('placement') == 'shared' for b in doc['blocks']))
            self.assertTrue(any(b.get('flow') == 'breakable' for b in doc['blocks']))
            self.assertFalse(any(b.get('break_before') for b in doc['blocks']))
            for side, language in enumerate(doc['languages']):
                text = {'title': doc['title'][side], 'blocks': [{k: b[k][side] for k in ('text', 'headers', 'rows') if k in b} for b in doc['blocks']]}
                if language in translations: self.assertEqual(text, translations[language])
                translations[language] = text
        self.assertEqual(set(translations), {'en', 'fr', 'ar', 'zh-Hans', 'ja'})

    def test_each_example_is_self_contained(self):
        import hashlib
        hashes = set()
        for source in self.article_root.glob('*/source.json'):
            for filename in ('main.tex', 'content.tex', 'languages.tex', 'paralleltext.sty'):
                self.assertTrue((source.parent / filename).is_file())
            for block in json.loads(source.read_text())['blocks']:
                if block.get('kind') == 'figure':
                    image = (source.parent / block['image']).resolve()
                    self.assertTrue(image.is_relative_to(source.parent.resolve()) and image.is_file())
                    if block.get('placement') == 'shared': hashes.add(hashlib.sha256(image.read_bytes()).hexdigest())
        self.assertEqual(len(hashes), 1)
        course = self.root / 'skills/course-guide-quick-reference/examples'
        for name in ('notes.tex', 'quick-reference.tex', 'source.md', 'source-map.json'):
            self.assertTrue((course / name).is_file())
        self.assertFalse((self.root / 'examples').exists() and any((self.root / 'examples').rglob('*.*')))

if __name__ == '__main__': unittest.main()
