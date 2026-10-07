"""Generic structural/importer contract tests; no private source fixtures."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'skills/study-notes/scripts'))
import structured_graph as graph

class StructuredGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = graph.load_renderer(ROOT/'skills/bilingual-pdf')
    def setUp(self):
        self.data = json.loads((ROOT/'skills/study-notes/examples/structured-graph.json').read_text())
    def render(self, **kwargs):
        return graph.render(self.data, self.renderer, **kwargs)
    def reject(self, text=None, **kwargs):
        with self.assertRaisesRegex(ValueError, text or '.'):
            self.render(**kwargs)
    def test_generic_helper_convergence_all_visible_nodes_numbered(self):
        before = copy.deepcopy(self.data)
        declarations, body, report, assets = self.render()
        self.assertEqual(self.data, before)
        self.assertEqual(len(report['crosswalk']), 6)
        self.assertEqual([x['reader_id'] for x in report['crosswalk']], ['N'+str(n) for n in range(1,7)])
        self.assertEqual(declarations.count('\\StudyDeclareGraphNode'), 6)
        self.assertNotIn('StudyDeclareGraphTerminal', declarations)
        self.assertIn('\\StudyGraphHelperCall{choose-material}', body)
        self.assertEqual(body.count('\\StudyGraphReturnExit'), 4)
        self.assertIn(['use-paper','pack-parcel'], report['ordering']['edges'])
        self.assertEqual(len(report['fields']), len(list(graph.content_fields(self.data))))
        self.assertTrue(all(x['emitted'] for x in report['fields']))
        self.assertEqual(report['source_sha256'], graph.digest(before))
        self.assertEqual(report['seed_order'], before['seed_order'])
        self.assertEqual(report['outputs']['graph-body.tex'], hashlib.sha256(body.encode()).hexdigest())
        self.assertFalse(assets)
    def test_one_node_exact_native_equivalence_plain_text(self):
        self.data = {'schema_version':1,'languages':['en','fr'],'title':['Plan','Plan'], 'entry':'finish',
                     'seed_order':['finish'], 'nodes':[{'key':'finish','kind':'procedure','function':'result',
                     'title':['Finish','Terminer'],'steps':[{'text':['A & B cost $2.','A et B coûtent 2 $.']}],
                     'stop':['Done.','Terminé.']}]}
        declarations, body, _, _ = self.render()
        native_declarations = '% Derived from structured graph; edit the JSON source.\n\\StudyDeclareGraphNode{finish}{1}{procedure}{result}{Finish}{Terminer}\n'
        native_body = '\\ParallelParagraph{graph-introduction}{\\StudyGraphInstruction{Plan}}{\\StudyGraphInstruction{Plan}}\n\n\\StudyGraphNode{finish}\n\n\\ParallelParagraph{graph-finish-body}{\n\\StudyGraphStep{1}{A \\& B cost \\$2.}\n\\StudyGraphField{result}{Done.}}{\n\\StudyGraphStep{1}{A et B coûtent 2 \\$.}\n\\StudyGraphField{result}{Terminé.}}\n'
        self.assertEqual(declarations, native_declarations)
        self.assertEqual(body, native_body)
    def test_bad_structure_table(self):
        cases = [
            lambda d:d.update(extra='discard me'),
            lambda d:d['nodes'][0].update(extra='discard me'),
            lambda d:d.update(schema_version=2),
            lambda d:d['nodes'][0]['choices'][0].update(target='missing'),
            lambda d:d['nodes'][0].update(key='N1'),
            lambda d:d['seed_order'].pop(),
            lambda d:d['nodes'][0]['title'].pop(),
            lambda d:d['nodes'][0].update(steps=[{'text':['Bad','Incorrect']}]),
            lambda d:d['nodes'][1].update(choices=d['nodes'][0]['choices']),
            lambda d:d['nodes'][1].update(stop=['Bad','Incorrect']),
            lambda d:d['nodes'][0]['prerequisites'].__setitem__(0,'bad\x00text'),
            lambda d:d['nodes'][0]['prerequisites'].__setitem__(0,'bad\u202etext'),
            lambda d:d.update(languages=['bad','en']),
        ]
        source = copy.deepcopy(self.data)
        for mutate in cases:
            with self.subTest(mutate=mutate):
                self.data = copy.deepcopy(source); mutate(self.data); self.reject()
    def test_explicit_loop_and_no_termination_claim(self):
        node = self.data['nodes'][-1]
        del node['stop']; node['next']='choose-wrap'
        self.reject('Cycle')
        node['loop'] = {x:['Keep the current parcel.','Conservez le colis actuel.'] for x in ['carried','progress','continue_when','exit_when']}
        self.assertIn('\\StudyGraphLoop', self.render()[1])
    def test_call_resume_exit_and_nested_rejections(self):
        source = copy.deepcopy(self.data)
        for change in [lambda c:c['resume'].update(step=99),lambda c:c.update(return_exits=['choose-wrap']),
                       lambda c:c.update(return_exits=['label-parcel']),lambda c:c.update(target='pack-parcel')]:
            self.data=copy.deepcopy(source);change(self.data['nodes'][1]['steps'][0]['call']);self.reject()
        self.data=copy.deepcopy(source)
        self.data['nodes'][3]['steps'][0]['call']=copy.deepcopy(self.data['nodes'][1]['steps'][0]['call'])
        self.data['nodes'][3]['steps'][0]['call']['resume']={'node':'use-paper','step':'completion_check'}
        self.data['nodes'][3]['completion_check']=['Check','Vérifiez']
        self.reject('Nested')
    def test_call_context_forward_resume_and_exit_conflicts(self):
        source=copy.deepcopy(self.data)
        self.data['nodes'][1]['steps'][0]['call']['resume']['step']=1
        self.reject('follow')
        self.data=copy.deepcopy(source)
        self.data['nodes'][0]['choices'][1]['target']='use-paper'
        self.reject('call context')
        self.data=copy.deepcopy(source)
        # One helper would pass through another call's return-only instruction.
        self.data['nodes'][3]['next']='use-padding'
        self.data['nodes'][1]['steps'][0]['call']['return_exits']=['use-padding']
        self.data['nodes'][-1]['steps'][0]['call']={
            'target':'use-paper','when':['Now','Maintenant'],'outputs':['Paper','Papier'],
            'resume':{'node':'label-parcel','step':'completion_check'},'return_exits':['use-paper']}
        self.data['nodes'][-1]['completion_check']=['Check the label.','Vérifiez l’étiquette.']
        self.reject('disagree')

    def test_no_silent_rich_field_flattening(self):
        source_hash = hashlib.sha256(b'An original demonstration source.').hexdigest()
        self.data['sources']=[{'key':'packing-guide','sha256':source_hash,'title':['Packing guide','Guide d’emballage']}]
        rich={'runs':[{'kind':'text','text':'Use '},{'kind':'math','text':r'\frac{1}{2}'},
              {'kind':'text','text':' of the space; '},{'kind':'reference','source':'packing-guide','sha256':source_hash,'locator':'Section 2'},
              {'kind':'node','target':'label-parcel'}]}
        self.data['nodes'][1]['fields']=[{'key':'measurement','role':'support','text':[rich,copy.deepcopy(rich)]}]
        body=self.render()[1]
        self.assertIn(r'\(\frac{1}{2}\)',body)
        self.assertIn('Packing guide, Section 2',body)
        self.assertIn('Guide d’emballage, Section 2',body)
        self.assertIn(r'\StudyGraphReference{label-parcel}',body)
        rich['runs'][3]['sha256']='0'*64;self.reject('Stale')
    def test_math_and_native_trust_boundaries(self):
        for text in [r'\input{secrets}',r'\csname input\endcsname',r'^^5cinput',r'\frac{1}{2',r'}x{',r'\write18{run}']:
            self.data['nodes'][0]['prerequisites']=[{'runs':[{'kind':'math','text':text}]}]*2
            self.reject()
        self.data['nodes'][0]['prerequisites']=[r'\input{literal}',r'\input{littéral}']
        self.assertIn(r'\textbackslash{}input\{literal\}',self.render()[1])
        self.data['nodes'][0]['prerequisites']=[{'runs':[{'kind':'native','text':r'\emph{Trusted}'}]}]*2
        self.reject('trusted-native')
        self.assertIn(r'\emph{Trusted}',self.render(trusted_native=True)[1])
    def test_asset_containment_and_resource_checks(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); assets=root/'assets';assets.mkdir()
            Image.new('RGB',(5,5),'white').save(assets/'safe.png')
            Image.new('RGB',(5,5),'white').save(root/'outside.png')
            (assets/'escape.png').symlink_to(root/'outside.png')
            figure={'path':'safe.png','caption':['A blank sample.','Un exemple vierge.']}
            self.data['nodes'][-1]['figures']=[figure]
            self.reject('asset root')
            self.assertEqual(len(self.render(asset_root=assets)[3]),1)
            body=self.render(asset_root=assets)[1]
            self.assertIn('\\ParallelFigure{graph-label-parcel-figure-1}{assets/graph-',body)
            source=root/'with-figure.json';source.write_text(json.dumps(self.data))
            output=root/'generated'
            proc=subprocess.run([sys.executable,str(ROOT/'skills/study-notes/scripts/structured_graph.py'),
                str(source),'--bilingual-pdf-skill',str(ROOT/'skills/bilingual-pdf'),
                '--asset-root',str(assets),'--output',str(output)],capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stderr)
            copied=list((output/'assets').glob('*.png'))
            self.assertEqual(len(copied),1)
            self.assertEqual(copied[0].read_bytes(),(assets/'safe.png').read_bytes())
            for path in ['../outside.png','/outside.png','escape.png','missing.png','safe.tex','https://invalid.example/a.png']:
                figure['path']=path;self.reject(asset_root=assets)
    def test_strict_json_and_numeric_key_boundaries(self):
        for text in ['{"nodes":[],"nodes":[]}', '{"value":NaN}', '{"value":Infinity}']:
            with self.assertRaises(ValueError):
                graph.load_graph(text)
        self.data['ordering']={'exact_limit':9.0,'budget':60000.0}
        self.assertTrue(self.render()[2]['ordering']['exact'])
        self.data['nodes'][0]['key']='choose-wrap\n'
        self.reject()

    def test_whitespace_runs_preserve_rich_prose(self):
        self.data['nodes'][0]['prerequisites']=[{'runs':[{'kind':'text','text':'Measure'},
            {'kind':'text','text':' '},{'kind':'math','text':'x'}]}]*2
        self.assertIn(r'Measure \(x\)',self.render()[1])
        self.data['nodes'][0]['prerequisites']=[{'runs':[{'kind':'text','text':' '}]}]*2
        self.reject('nonblank')

    def test_return_edges_do_not_activate_orphan_callers(self):
        def node(key, **extra):
            return {'key':key,'kind':'procedure','function':'action','title':[key,key],**extra}
        self.data={'schema_version':1,'languages':['en','en'],'title':['Route','Route'],'entry':'start',
            'seed_order':['start','shared-exit','done','orphan-caller'], 'nodes':[
            node('start',next='shared-exit'),node('shared-exit',next='done'),node('done',stop=['Done','Done']),
            node('orphan-caller',steps=[{'text':['Call','Call'],'call':{'target':'shared-exit','when':['Now','Now'],
                'outputs':['Value','Value'],'resume':{'node':'orphan-caller','step':2},'return_exits':['shared-exit']}},
                {'text':['Resume','Resume']}],stop=['Done','Done'])]}
        self.reject('Unreachable')

    def test_unreachable_and_unknown_metadata(self):
        self.data['nodes'][0]['choices']=[self.data['nodes'][0]['choices'][1]]
        self.reject('Unreachable')
    def test_clean_install_and_cli_no_sibling_assumption(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);study=root/'installed'/'learning';pdf=root/'separate'/'typesetter'
            shutil.copytree(ROOT/'skills/study-notes',study)
            shutil.copytree(ROOT/'skills/bilingual-pdf',pdf)
            output=root/'derived'
            command=[sys.executable,str(study/'scripts/structured_graph.py'),str(study/'examples/structured-graph.json'),
                     '--bilingual-pdf-skill',str(pdf),'--output',str(output)]
            proc=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertTrue(json.loads(proc.stdout)['ok'])
            self.assertTrue((output/'graph-report.json').is_file())
            proc=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=30)
            self.assertNotEqual(proc.returncode,0)

if __name__=='__main__':
    unittest.main()
