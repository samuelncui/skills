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
        source = root / 'source'; (source / 'examples').mkdir(parents=True)
        for name in INPUTS:
            path = source / 'examples' / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'original input')
        for name in ['skills/bilingual-pdf/scripts/bilingual_pdf.py','skills/bilingual-pdf/assets/paralleltext.sty','skills/bilingual-pdf/requirements.txt','skills/course-guide-quick-reference/scripts/course_documents.py']:
            p = source / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('public runtime')
        (matrix / 'private.log').write_text('must not be copied')
        return matrix, source

    def test_explicit_allowlist_and_relative_course_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root); out = root / 'bundle'
            records = collect_examples(matrix, out, source)
            self.assertEqual(len(records), 6)
            self.assertTrue((out / 'course-guide-quick-reference/three-concepts/notes.pdf').exists())
            self.assertTrue((out / 'course-guide-quick-reference/three-concepts/quick-reference.pdf').exists())
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

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); matrix, source = self.fixture(root); out = root / 'bundle'; out.mkdir()
            with self.assertRaises(ValueError): collect_examples(matrix, out, source)

if __name__ == '__main__': unittest.main()
