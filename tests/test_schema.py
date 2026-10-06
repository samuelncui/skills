"""Maintained JSON Schema/runtime conformance and documented semantic boundaries."""
import copy,json,sys,unittest
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import InputError,validate,tex_parts

SCHEMA=json.loads((ROOT/'skills/bilingual-pdf/schemas/document.schema.json').read_text())
VALIDATOR=Draft202012Validator(SCHEMA)
BASE={'languages':['en','fr'],'title':['Title','Titre'],'blocks':[{'id':'body','text':['Text.','Texte.']}]}

def runtime_accepts(value):
    try:validate(copy.deepcopy(value));return True
    except (InputError,TypeError,ValueError):return False

class SchemaTests(unittest.TestCase):
    def agrees(self,value,expected):
        self.assertEqual(VALIDATOR.is_valid(value),expected)
        self.assertEqual(runtime_accepts(value),expected)
    def test_schema_self_check(self):
        Draft202012Validator.check_schema(SCHEMA)
    def test_every_curated_document_matches_schema_and_runtime(self):
        documents=list((ROOT/'skills/bilingual-pdf/examples').glob('*/source.json'))
        self.assertEqual(len(documents),5)
        for path in documents:
            with self.subTest(pair=path.parent.name):self.agrees(json.loads(path.read_text()),True)
    def test_text_boundaries(self):
        for value,expected in [('ordinary',True),('line\nnext',True),('a\tb',True),('',False),('  ',False),('bad\x00text',False),('bad\u202etext',False)]:
            with self.subTest(value=repr(value)):
                doc=copy.deepcopy(BASE);doc['blocks'][0]['text'][0]=value;self.agrees(doc,expected)
    def test_global_and_per_paragraph_flow(self):
        for global_flow in ('keep','breakable'):
            for local in (None,'keep','atomic','breakable'):
                with self.subTest(global_flow=global_flow,local=local):
                    doc=copy.deepcopy(BASE);doc['layout']={'paragraph_flow':global_flow}
                    if local:doc['blocks'][0]['flow']=local
                    self.agrees(doc,True)
                    _,locale,body=tex_parts(validate(doc),'bilingual')
                    self.assertIn('paragraph-flow='+global_flow,locale)
                    self.assertIn(r'\ParallelParagraph',body)
                    if local:self.assertIn('[flow='+('keep' if local=='atomic' else local)+']',body)
        for location in ('global','local'):
            doc=copy.deepcopy(BASE)
            if location=='global':doc['layout']={'paragraph_flow':'sometimes'}
            else:doc['blocks'][0]['flow']='sometimes'
            self.agrees(doc,False)
    def test_flow_is_not_silently_applied_to_quotes_or_references(self):
        doc=copy.deepcopy(BASE);doc['layout']={'paragraph_flow':'breakable'}
        doc['blocks'] += [{'id':'quote','kind':'quote','text':['Quote.','Citation.']},{'id':'ref','kind':'reference','target':'body','text':['See','Voir']}]
        body=tex_parts(validate(doc),'bilingual')[2]
        self.assertIn(r'\ParallelText{quote}',body)
        self.assertIn(r'\ParallelText{ref}',body)
    def test_rich_table_cells_are_explicit_and_rtl_only(self):
        latin={'runs':[{'text':'JSON','direction':'ltr'},{'text':' نص','direction':'rtl'}]}
        for language in ('ar','he','fr'):
            doc={'languages':['en',language],'title':['Table','جدول' if language=='ar' else ('טבלה' if language=='he' else 'Tableau')],
                 'blocks':[{'id':'table','kind':'table','text':['Caption','Caption'],'headers':[['Route'],[latin]],'rows':[[['Native']],[[latin]]]}]}
            with self.subTest(language=language):
                self.agrees(doc,language in ('ar','he'))
                if language in ('ar','he'):
                    body=tex_parts(validate(doc),'bilingual')[2]
                    self.assertIn(r'\textenglish{JSON}',body)
                    self.assertNotIn(r'\input{',body)
    def test_table_caption_is_optional_without_inventing_content(self):
        doc=copy.deepcopy(BASE)
        doc['blocks']=[{'id':'table','kind':'table','headers':[['Crop'],['Culture']],
                        'rows':[[['Bean']],[['Haricot']]]}]
        original=copy.deepcopy(doc)
        self.agrees(doc,True)
        body=tex_parts(validate(doc),'bilingual')[2]
        self.assertEqual(doc,original)
        self.assertIn(r'\ParallelText{table.row-0}',body)
        self.assertNotIn('table.caption',body)
        for bad in (None,[],['',''],['Caption'],['Caption',' ']):
            with self.subTest(caption=bad):
                value=copy.deepcopy(doc);value['blocks'][0]['text']=bad
                self.agrees(value,False)
        doc['blocks'][0]['text']=['Record','Relevé']
        self.agrees(doc,True)
        self.assertIn(r'\ParallelText{table.caption}{Record}{Relevé}',tex_parts(validate(doc),'bilingual')[2])
        for kind in ('paragraph','heading','list','figure','equation','quote','reference'):
            value=copy.deepcopy(BASE);value['blocks'][0]['kind']=kind;del value['blocks'][0]['text']
            with self.subTest(kind=kind):self.agrees(value,False)

    def test_unknown_root_and_block_extensions_are_preserved_but_layout_is_closed(self):
        doc=copy.deepcopy(BASE);doc['extension']={'x':1};doc['blocks'][0]['unused']={'x':2};self.agrees(doc,True)
        doc['layout']={'unexpected':True};self.agrees(doc,False)
    def test_documented_semantic_checks_remain_runtime_gates(self):
        cases=[]
        x=copy.deepcopy(BASE);x['blocks'].append(copy.deepcopy(x['blocks'][0]));cases.append(x)
        x=copy.deepcopy(BASE);x['blocks'].append({'id':'ref','kind':'reference','target':'absent','text':['See','Voir']});cases.append(x)
        x=copy.deepcopy(BASE);x['layout']={'font_size':14,'leading':9};cases.append(x)
        for doc in cases:
            with self.subTest(doc=doc):
                self.assertTrue(VALIDATOR.is_valid(doc))
                self.assertFalse(runtime_accepts(doc))

if __name__=='__main__':unittest.main()
