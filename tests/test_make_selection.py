"""Public Make orchestration regression; compiler calls are stubbed, not PDF builds."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

class MakeSelection(unittest.TestCase):
    def test_whitespace_separated_product_selection(self):
        for separator in [' ', '\t', '\n']:
            with self.subTest(separator=repr(separator)), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)
                shutil.copyfile(ROOT/'skills/study-notes/examples/Makefile', path/'Makefile')
                (path/'compiler.py').write_text('import pathlib,sys\nwith pathlib.Path("calls.txt").open("a") as f: f.write(" ".join(sys.argv[1:])+"\\n")\n')
                p = subprocess.run(['make', 'BILINGUAL_PDF_SKILL='+str(ROOT/'skills/bilingual-pdf'), 'STUDY_NOTES_SKILL='+str(ROOT/'skills/study-notes'), 'LATEXMK='+sys.executable+' compiler.py', 'PRODUCTS='+separator.join(['notes','quick-reference'])], cwd=path, capture_output=True, text=True, timeout=20)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual((path/'calls.txt').read_text().splitlines(), ['notes.tex','quick-reference.tex'])
                self.assertIn('StudyBuildNotestrue', (path/'.build-products.tex').read_text())

if __name__ == '__main__':
    unittest.main(verbosity=2)
