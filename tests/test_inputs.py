import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import InputError,validate,tex_document,escape,content

class InputTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((ROOT/'tests/fixtures/garden-en-fr.json').read_text())
 def test_basic(self):validate(self.doc)
 def test_missing_translation(self):
  self.doc['blocks'][0]['text'][1]=''
  with self.assertRaises(InputError):validate(self.doc)
 def test_bad_language_type(self):
  self.doc['languages'][0]={}
  with self.assertRaises(InputError):validate(self.doc)
 def test_bad_kind_type(self):
  self.doc['blocks'][0]['kind']=[]
  with self.assertRaises(InputError):validate(self.doc)
 def test_bad_paper_type(self):
  self.doc['layout']={'paper':[]}
  with self.assertRaises(InputError):validate(self.doc)
 def test_duplicate_id(self):
  self.doc['blocks'].append(copy.deepcopy(self.doc['blocks'][0]))
  with self.assertRaises(InputError):validate(self.doc)
 def test_math_file_read(self):
  self.doc['blocks'][-1]['math']=r'\input{secret}'
  with self.assertRaises(InputError):validate(self.doc)
 def test_math_character_escape(self):
  self.doc['blocks'][-1]['math']='^^5cinput{secret}'
  with self.assertRaises(InputError):validate(self.doc)
 def test_literal_characters_escaped(self):
  self.assertEqual(escape('^^'),r'\textasciicircum{}\textasciicircum{}')
  self.assertIn(r'\textbackslash{}input',escape(r'\input{x}'))
 def test_list_item_pairs(self):
  tex=tex_document(self.doc,'bilingual')
  self.assertIn(r'\ParallelText{steps.item-1}',tex);self.assertIn(r'\ParallelText{steps.item-2}',tex)
 def test_parent_reference_anchors(self):
  self.doc['blocks'] += [{'id':'list-ref','kind':'reference','target':'steps','text':['Steps','Étapes']},{'id':'equation-ref','kind':'reference','target':'average','text':['Average','Moyenne']}]
  validate(self.doc)
  for mode in ['bilingual','left','right']:
   tex=tex_document(self.doc,mode)
   self.assertIn(r'\label{steps}',tex)
   self.assertIn(r'\ParallelText{average}',tex)
 def test_bad_run_direction_type(self):
  self.doc['blocks'][0]['text'][0]={'runs':[{'text':'word','direction':[]}]}
  with self.assertRaises(InputError):validate(self.doc)
 def test_directional_runs_on_ltr_profile(self):
  self.doc['blocks'][0]['text'][0]={'runs':[{'text':'word','direction':'ltr'}]}
  with self.assertRaises(InputError):validate(self.doc)
 def test_rtl_reference_suffix_isolated(self):
  block={'id':'ref','kind':'reference','target':'check','text':['See','انظر']}
  self.assertIn(r'\ParallelReference{check}',content(block,1,'ar'))
  block.update(file='notes.pdf',page=7)
  self.assertIn(r'\textenglish{(p.\,7)}',content(block,1,'ar'))
 def test_rtl_bullet_direction(self):
  block={'kind':'list','text':[['First'],['الأول']]}
  self.assertTrue(content(block,1,'ar').startswith(r'\begin{itemize}\item '))
 def test_right_cover(self):
  self.doc['layout']={'covers':True}
  tex=tex_document(self.doc,'right')
  self.assertIn(r'\ParallelSetup{mode=right}',tex)
  self.assertIn(r'\ParallelFrontCover{A small garden}{Un petit jardin}',tex)
  self.assertIn(r'\ParallelBackCover{A small garden}{Un petit jardin}',tex)
 def test_unresolved_reference(self):
  self.doc['blocks'].append({'id':'ref','kind':'reference','target':'missing','text':['See','Voir']})
  with self.assertRaises(InputError):validate(self.doc)
 def test_direction_controls(self):
  self.doc['title'][0]='A\u202eb'
  with self.assertRaises(InputError):validate(self.doc)
 def test_list_ids_collision(self):
  self.doc['blocks'].append({'id':'steps.item-1','text':['A','B']})
  with self.assertRaises(InputError):validate(self.doc)
 def test_schema_examples(self):
  for p in (ROOT/'skills/bilingual-pdf/examples').glob('*/source.json'):
   if p.name.startswith('course-'):continue
   validate(json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
