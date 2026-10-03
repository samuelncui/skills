import copy,importlib.util,json,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/course-guide-quick-reference/scripts'))
from course_documents import prepare,InputError,stage_figures,verify_guide_links

class CourseTests(unittest.TestCase):
 def setUp(self):self.data=json.loads((ROOT/'tests/fixtures/course-en-fr/source.json').read_text())
 def test_original_example(self):
  guide,quick,topics=prepare(self.data);self.assertEqual(len(topics),3);self.assertTrue(guide['blocks'])
 def test_flexible_concept_parts(self):
  self.data['topics'][0]['quick']={'blocks':[{'id':'speed.shortcut','text':['Distance over positive time.','Distance divisée par une durée positive.']}]}
  guide,quick,topics=prepare(self.data)
  self.assertIn('blocks',topics[0]['quick'])
 def test_cross_concept_quick_reference(self):
  target=self.data['topics'][1]['id']
  self.data['topics'][0]['quick']={'blocks':[{'id':'cross-concept','kind':'reference','target':'entry.'+target,'text':['Related concept','Notion associée']}]}
  prepare(self.data)
 def test_quick_staging_separate_from_guide(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'a.png').write_bytes(b'guide');(root/'b.png').write_bytes(b'quick');out=root/'out';out.mkdir()
   guide={'blocks':[{'id':'same','kind':'figure','image':'a.png'}]};quick={'blocks':[{'id':'same','kind':'figure','image':'b.png'}]}
   stage_figures(guide,root/'input.json',out,'guide');stage_figures(quick,root/'input.json',out,'quick')
   self.assertNotEqual(guide['blocks'][0]['image'],quick['blocks'][0]['image'])
   self.assertEqual((out/guide['blocks'][0]['image']).read_bytes(),b'guide')
   self.assertEqual((out/quick['blocks'][0]['image']).read_bytes(),b'quick')
 def test_unknown_related(self):
  self.data['topics'][0]['see_also']=['missing']
  with self.assertRaises(InputError):prepare(self.data)
 def test_duplicate_topic(self):
  self.data['topics'].append(copy.deepcopy(self.data['topics'][0]))
  with self.assertRaises(InputError):prepare(self.data)
 def test_alias_type(self):
  self.data['topics'][0]['aliases']=None
  with self.assertRaises(InputError):prepare(self.data)
 def test_duplicate_related(self):
  self.data['topics'][0]['see_also']=[self.data['topics'][1]['id']]*2
  with self.assertRaises(InputError):prepare(self.data)
 def test_related_type(self):
  self.data['topics'][0]['see_also']=[{}]
  with self.assertRaises(InputError):prepare(self.data)
 def test_missing_related_label(self):
  self.data['topics'][0]['see_also']=[self.data['topics'][1]['id']]
  del self.data['labels']['see_also']
  with self.assertRaises(InputError):prepare(self.data)
 def test_missing_labels(self):
  del self.data['labels']
  with self.assertRaises(InputError):prepare(self.data)
 def test_keyword_target(self):
  self.data['keywords'][0]['targets']=['unknown']
  with self.assertRaises(InputError):prepare(self.data)
 def test_keyword_duplicate(self):
  self.data['keywords'][0]['targets']=[self.data['topics'][0]['id']]*2
  with self.assertRaises(InputError):prepare(self.data)
 def link_fixture(self):
  aux=r'\PairMeasure{entry.area.guide}{6553600}{1966080}'+r'\zref@newlabel{pt-internal:entry.area.guide-L-start}{\posx{0}\posy{6553600}}'+r'\zref@newlabel{pt-internal:entry.area.guide-L-end}{\posx{0}\posy{4587520}}'+r'\newlabel{pt-internal:entry.area.guide-L}{{}{1}{}{Doc-Start}{}}'
  links=[{'source_page':0,'file':'notes.pdf','page':2,'rect':(0,100,80,110)},{'source_page':0,'file':'notes.pdf','page':2,'rect':(0,115,80,125)}]
  return aux,links
 def test_wrapped_logical_link(self):
  aux,links=self.link_fixture()
  self.assertEqual(verify_guide_links(aux,[200],links,{'area':3},'left'),1)
 def test_missing_logical_link(self):
  aux,_=self.link_fixture()
  with self.assertRaises(RuntimeError):verify_guide_links(aux,[200],[],{'area':3},'left')
 def test_wrong_logical_destination(self):
  aux,links=self.link_fixture();links[1]['page']=3
  with self.assertRaises(RuntimeError):verify_guide_links(aux,[200],links,{'area':3},'left')
 def test_figure_reserved_directory(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'guide').mkdir();(root/'guide/image.png').write_bytes(b'original image bytes')
   out=root/'output';out.mkdir()
   guide={'blocks':[{'id':'diagram','kind':'figure','image':'guide/image.png'}]}
   stage_figures(guide,root/'input.json',out)
   self.assertFalse((out/'guide').exists())
   self.assertEqual((out/guide['blocks'][0]['image']).read_bytes(),b'original image bytes')
 def test_figure_traversal(self):
  next(b for t in self.data['topics'] for b in t['guide_blocks'] if b.get('kind')=='figure')['image']='../private.png'
  with self.assertRaises(InputError):prepare(self.data)

if __name__=='__main__':unittest.main()
