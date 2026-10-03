import copy, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import InputError,validate,tex_parts,content

class ConfigurationTests(unittest.TestCase):
 def setUp(self):
  self.doc={'languages':['en','fr'],'title':['Example','Exemple'],'blocks':[{'id':'a','text':['Text.','Texte.']}]}
 def locale(self):return tex_parts(validate(self.doc),'bilingual')[1]
 def test_default_needs_no_style_overrides(self):
  self.assertIn(r'\ParallelSetup{mode=paired}',self.locale())
  self.assertNotIn(r'\geometry{',self.locale())
 def test_geometry_delegates_to_native_setup(self):
  self.doc['layout']={'inner_mm':24,'outer_mm':16,'binding_mm':3,'twoside':True,'paper':'letter'}
  self.assertIn('geometry={letterpaper,twoside=true,inner=24mm,outer=16mm,bindingoffset=3mm}',self.locale())
 def test_sparse_reading_profile_keeps_profile_size(self):
  self.doc['layout']={'profile':'reading','divider':{'enabled':True}}
  self.assertIn('profile=reading,mode=paired,divider=true',self.locale())
  self.assertNotIn('body-size=',self.locale())
 def test_profile_then_explicit_override(self):
  self.doc['layout']={'profile':'bound','outer_mm':20}
  self.assertIn('profile=bound,mode=paired,geometry={outer=20mm}',self.locale())
 def test_custom_divider_is_data_not_tex(self):
  self.doc['layout']={'divider':{'enabled':True,'color':'112233','width_pt':.6,'style':'dotted'}}
  locale=self.locale()
  self.assertIn(r'\definecolor{parallel.adapter.divider}{HTML}{112233}',locale)
  self.assertIn('divider-width=0.6pt',locale)
 def test_folio_prefix_is_escaped(self):
  self.doc['layout']={'page_numbers':{'numbering':'roman','position':'header-inner','prefix':r'\input{x}%','suffix':'!'}}
  locale=self.locale()
  self.assertIn('page-numbering=roman,page-number-position=header-inner',locale.replace('page-number-position=header-inner,page-numbering=roman','page-numbering=roman,page-number-position=header-inner'))
  self.assertIn(r'\textbackslash{}input\{x\}\%',locale)
  self.assertIn(r'\thepage{}!',locale)
 def test_bad_nested_options_are_rejected(self):
  values=[{'divider':{'color':r'\input{x}'}},{'divider':{'width_pt':-1}}, {'divider':{'width_pt':True}}, {'divider':{'style':'execute at begin picture=evil'}}, {'divider':{'other':1}}, {'page_numbers':{'numbering':'bad'}}, {'page_numbers':{'position':'bad'}}, {'page_numbers':{'prefix':True}}, {'page_numbers':{'prefix':'line\nbreak'}}, {'page_numbers':{'other':1}}]
  for layout in values:
   with self.subTest(layout=layout):
    self.doc['layout']=layout
    with self.assertRaises(InputError):validate(self.doc)
 def test_external_reference_uses_printed_folio_without_changing_target(self):
  block={'id':'ref','kind':'reference','file':'notes.pdf','page':3,'page_label':'iii','target':'topic.area','text':['Notes','Notes']}
  self.assertIn(r'\href[page=3]',content(block,0,'en'))
  self.assertIn(r'(p.\,iii)',content(block,0,'en'))
 def test_unknown_layout_is_not_silently_ignored(self):
  self.doc['layout']={'innner_mm':24}
  with self.assertRaises(InputError):validate(self.doc)
 def test_geometry_ranges_and_types(self):
  for layout in [{'inner_mm':0},{'binding_mm':-1},{'twoside':'yes'},{'paper':{}},{'profile':None},{'font_size':12,'leading':10}]:
   with self.subTest(layout=layout):
    self.doc['layout']=layout
    with self.assertRaises(InputError):validate(self.doc)

if __name__=='__main__':unittest.main()
