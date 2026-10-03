import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import InputError,validate,tex_parts,export_document

class StructuredTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((ROOT/'examples/bilingual-pdf/en-zh-Hans/source.json').read_text())
 def table(self):return next(x for x in self.doc['blocks'] if x['kind']=='table')
 def test_native_package_route(self):
  main,locale,body=tex_parts(self.doc,'bilingual')
  self.assertIn(r'\usepackage{paralleltext}',main)
  self.assertIn(r'\input{content.tex}',main)
  self.assertIn(r'\setotherlanguage{chinese}',locale)
  self.assertIn(r'\ParallelFigure',body)
  self.assertIn(r'\begin{quote}',body)
  self.assertIn(r'\begin{tabularx}',body)
 def test_table_rows_align_individually(self):
  body=tex_parts(self.doc,'bilingual')[2]
  for i in range(len(self.table()['rows'][0])+1):
   self.assertIn(r'\ParallelText{notes-table.row-'+str(i)+'}',body)
 def test_table_row_count(self):
  self.table()['rows'][1].pop()
  with self.assertRaises(InputError):validate(self.doc)
 def test_table_cell_count(self):
  self.table()['rows'][1][0].append('extra')
  with self.assertRaises(InputError):validate(self.doc)
 def test_table_header_plain_text(self):
  self.table()['headers'][0][0]={'runs':[{'text':'Header','direction':'ltr'}]}
  with self.assertRaises(InputError):validate(self.doc)
 def test_generated_table_id_collision(self):
  self.doc['blocks'].append({'id':'notes-table.row-1','text':['a','甲']})
  with self.assertRaises(InputError):validate(self.doc)
 def test_reserved_title_id(self):
  self.doc['blocks'][0]['id']='pt-title'
  with self.assertRaises(InputError):validate(self.doc)
 def test_page_break_type(self):
  self.doc['blocks'][0]['break_before']='yes'
  with self.assertRaises(InputError):validate(self.doc)
 def test_text_does_not_become_tex(self):
  self.doc['blocks'][1]['text'][0]=r'\input{private} & 10%'
  body=tex_parts(validate(self.doc),'bilingual')[2]
  self.assertIn(r'\textbackslash{}input\{private\} \& 10\%',body)
  self.assertNotIn(r'\input{private}',body)
 def test_export_preserves_existing_directory(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';out.mkdir();(out/'keep').write_text('unchanged')
   with self.assertRaises(InputError):export_document(self.doc,ROOT/'examples/bilingual-pdf/en-zh-Hans/source.json',out,'bilingual')
   self.assertEqual((out/'keep').read_text(),'unchanged')

if __name__=='__main__':unittest.main()
