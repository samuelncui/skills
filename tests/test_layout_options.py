import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import InputError,validate,tex_parts

class LayoutOptionTests(unittest.TestCase):
 def setUp(self):
  self.doc={'languages':['en','fr'],'title':['Example','Exemple'],'blocks':[{'id':'paragraph','kind':'paragraph','text':['Text.','Texte.']}]}
 def test_breakable_uses_canonical_flow(self):
  self.doc['blocks'][0]['flow']='breakable'
  self.assertIn(r'\ParallelProse{paragraph}',tex_parts(validate(self.doc),'bilingual')[2])
 def test_atomic_remains_bounded(self):
  self.doc['blocks'][0]['flow']='atomic'
  self.assertIn(r'\ParallelText{paragraph}',tex_parts(validate(self.doc),'bilingual')[2])
 def test_bad_flow_is_rejected(self):
  for value in ['auto',True,{},None]:
   self.doc['blocks'][0]['flow']=value
   with self.assertRaises(InputError):validate(self.doc)
 def test_flow_cannot_silently_affect_heading(self):
  self.doc['blocks'][0].update(kind='heading',flow='breakable')
  with self.assertRaises(InputError):validate(self.doc)
 def test_shared_figure_uses_one_helper(self):
  self.doc['blocks'][0].update(kind='figure',placement='shared',image='path.png')
  self.assertIn(r'\ParallelWideFigure{paragraph}',tex_parts(validate(self.doc),'bilingual')[2])
 def test_caption_id_collision_is_rejected(self):
  self.doc['blocks'][0].update(kind='figure',placement='shared',image='path.png')
  self.doc['blocks'].append({'id':'paragraph.caption','text':['Caption.','Légende.']})
  with self.assertRaises(InputError):validate(self.doc)
 def test_nonfigure_placement_is_rejected(self):
  self.doc['blocks'][0]['placement']='shared'
  with self.assertRaises(InputError):validate(self.doc)

if __name__=='__main__':unittest.main()
