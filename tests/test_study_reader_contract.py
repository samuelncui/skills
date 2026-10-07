"""Reader-facing contract of the curated native graph example, not a semantic audit."""
import re
import unittest
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]

def reader_errors(pdf_path, declarations):
    keys = re.findall(r'\\StudyDeclareGraphNodeAuto\{([^}]+)\}', declarations)
    errors = []
    with pymupdf.open(pdf_path) as pdf:
        text = ' '.join(page.get_text() for page in pdf)
        if not keys:
            errors.append('No native auto-numbered declarations')
        for number, key in enumerate(keys, 1):
            if not re.search(r'\bN'+str(number)+r'\b', text):
                errors.append('Missing reader number N'+str(number))
            if key in text:
                errors.append('Internal key visible: '+key)
        colors = {s['color'] for page in pdf for b in page.get_text('dict')['blocks']
                  for line in b.get('lines', []) for s in line['spans']}
        if not {0x0b4f8a, 0x006b5b} <= colors:
            errors.append('Question/solution role colors missing')
        names = pdf.resolve_names()
        for page in pdf:
            for link in page.get_links():
                if pdf.xref_get_key(link['xref'], 'A/S')[1] == '/GoTo':
                    target = pdf.xref_get_key(link['xref'], 'A/D')[1]
                    if target not in names and link.get('page', -1) < 0:
                        errors.append('Unresolved graph destination')
    return errors

class StudyReaderContract(unittest.TestCase):
    def test_curated_graph_reader_identity_and_roles(self):
        example = ROOT/'skills/study-notes/examples'
        self.assertEqual(reader_errors(example/'decision-tree.pdf', (example/'decisions.tex').read_text()), [])

if __name__ == '__main__':
    unittest.main()
