"""Public action registry, exact edits, gates and atomic packet regressions."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/bilingual-translation/scripts/workflow.py'
spec = importlib.util.spec_from_file_location('action_workflow', SCRIPT)
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)
C = W.core

class ActionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.master = self.root/'master.jsonl'
        self.source = self.root/'source.md'

    def act(self, op, **fields):
        return W.execute(self.master, [{'op':op, **fields}])[0]

    def prepare(self, text='# Title\r\n\r\nFirst.\r\n\r\nSecond.\r\n'):
        self.source.write_bytes(text.encode())
        return self.act('prepare init', source=str(self.source))

    def save(self, block, target=None):
        return self.act('translate save', ref=block['ref'], targets={u['id']:target or 'T '+u['source'] for u in block['units']})

    def translate(self, target=None):
        block=self.act('translate next')
        while not block.get('complete'):
            result=self.save(block,target)
            self.assertNotIn('units',result)
            self.assertNotIn('next',result)
            block=self.act('translate next')

    def reviewed(self):
        block=self.act('review next')
        while not block.get('complete'):
            result=self.act('review accept',ref=block['ref'])
            self.assertNotIn('units',result)
            block=self.act('review next')

    def test_end_to_end_schema_source_ready_and_exchange(self):
        self.prepare();before=self.source.read_bytes()
        schema=json.loads((SCRIPT.parents[1]/'schemas/translation-workflow.schema.json').read_text())
        validator=Draft202012Validator(schema)
        validator.validate(C.load_jsonl(self.master))
        with self.assertRaises(ValueError): self.act('validate',ready=True)
        with self.assertRaises(ValueError): C.to_exchange_document(C.load_jsonl(self.master))
        with self.assertRaises(TypeError): C.to_exchange_document(C.load_jsonl(self.master), require_ready=False)
        self.translate();validator.validate(C.load_jsonl(self.master))
        with self.assertRaises(ValueError): self.act('validate',ready=True)
        self.reviewed();self.act('validate',ready=True)
        validator.validate(C.load_jsonl(self.master,True))
        out=self.root/'exchange.json';self.act('export',output=str(out))
        exchange=json.loads(out.read_text());self.assertEqual(C.exchange.validate_document(exchange,True),[])
        self.assertEqual(self.source.read_bytes(),before)
        with self.assertRaises(ValueError): self.act('export',output=str(out))

    def test_prepare_blocks_translate_until_all_batches_and_splits(self):
        response=self.prepare('A'*2048+'\n\n'+'B'*2048+'\n\n'+'C'*2048+'\n\n'+'D'*2048+'\n\nTail.')
        self.assertEqual(response['characters'],8192)
        with self.assertRaises(ValueError): self.act('translate next')
        self.act('prepare init',ref=response['ref'])
        self.act('translate next')

    def test_registry_shared_between_single_and_run(self):
        self.prepare()
        spec=W.COMMANDS['status'];original=spec.handler
        with patch.object(spec,'handler',wraps=original) as handler:
            one=self.act('status');two=W.execute(self.master,[{'op':'status'}],batch=True)[0]
            self.assertEqual(one,two);self.assertEqual(handler.call_count,2)
        for batch in (False,True):
            with self.assertRaises(ValueError):W.execute(self.master,[{'op':'status','extra':True}],batch=batch)

    def test_run_save_next_atomic_and_exact_replay(self):
        self.prepare();block=self.act('translate next')
        packet=[{'op':'translate save','ref':block['ref'],'targets':{u['id']:'Target' for u in block['units']}},{'op':'translate next'}]
        with patch.object(C.os,'replace',wraps=C.os.replace) as replacements:
            result=W.execute(self.master,packet,batch=True);self.assertEqual(replacements.call_count,1)
        before=self.master.read_bytes();self.assertEqual(W.execute(self.master,packet,batch=True),result)
        self.assertEqual(self.master.read_bytes(),before)
        self.assertIn('units',result[-1]);self.assertNotIn('units',result[0])

    def test_late_failure_rolls_back_all_prior_actions(self):
        self.prepare();block=self.act('translate next');before=self.master.read_bytes()
        packet=[{'op':'todo add','ref':block['ref'],'text':'Check wording'},
                {'op':'translate save','ref':block['ref'],'targets':{'wrong':'No'}}]
        with self.assertRaises(W.ActionError) as raised:W.execute(self.master,packet,batch=True)
        self.assertEqual(raised.exception.line,2);self.assertFalse(raised.exception.committed)
        self.assertEqual(self.master.read_bytes(),before)

    def test_more_than_one_read_or_read_before_mutation_or_export_rejected(self):
        self.prepare();before=self.master.read_bytes()
        for packet in ([{'op':'translate next'},{'op':'review next'}],
                       [{'op':'translate next'},{'op':'status'}],
                       [{'op':'export','output':str(self.root/'out.json')}]):
            with self.assertRaises(ValueError):W.execute(self.master,packet,batch=True)
            self.assertEqual(self.master.read_bytes(),before)

    def test_todo_does_not_stale_text_ref_and_blocks_ready(self):
        self.prepare('One.\n\nTwo.');self.translate();block=self.act('review next')
        packet=[{'op':'todo add','ref':block['ref'],'text':'Verify exact term','units':[block['units'][0]['id']]},
                {'op':'review accept','ref':block['ref']}]
        W.execute(self.master,packet,batch=True)
        with self.assertRaises(ValueError):self.act('validate',ready=True)
        reread=self.act('review next',units=[block['units'][0]['id']])
        self.assertEqual(reread['todos'][0]['id'],'todo-1')
        W.execute(self.master,[{'op':'todo resolve','ref':reread['ref'],'id':'todo-1'},
                              {'op':'review accept','ref':reread['ref']}],batch=True)
        self.act('validate',ready=True)

    def test_patch_unique_exact_and_local_rereview_without_implicit_accept(self):
        self.prepare('One.\n\nTwo.');self.translate();block=self.act('review next')
        uid=block['units'][0]['id']
        patched=self.act('review patch',ref=block['ref'],edits=[{'unit':uid,'old':'One','new':'First'}])
        self.assertNotIn('units',patched)
        pending=C.load_jsonl(self.master)['document']['workflow']['active']
        with self.assertRaises(ValueError):self.act('review accept',ref=pending['ref'])
        response=self.act('review next')
        self.assertEqual([u['id'] for u in response['units']],[uid])
        self.assertEqual(response['units'][0]['target'],'T First.')
        self.assertNotEqual(response['ref'],block['ref'])
        with self.assertRaises(ValueError):self.act('review accept',ref=block['ref'])
        self.act('review accept',ref=response['ref'])
        next_block=self.act('review next');self.assertEqual([u['source'] for u in next_block['units']],['Two.'])

    def test_patch_next_returns_changed_block_and_patch_accept_forbidden(self):
        self.prepare('One.');self.translate();block=self.act('review next')
        edit={'op':'review patch','ref':block['ref'],'edits':[{'unit':block['units'][0]['id'],'old':'One','new':'New'}]}
        before=self.master.read_bytes()
        with self.assertRaises(ValueError):W.execute(self.master,[edit,{'op':'review accept','ref':block['ref']}],batch=True)
        self.assertEqual(self.master.read_bytes(),before)
        results=W.execute(self.master,[edit,{'op':'review next'}],batch=True)
        self.assertNotIn('units',results[0]);self.assertEqual(results[-1]['units'][0]['target'],'T New.')

    def test_patch_ambiguity_overlap_and_noop_leave_master_unchanged(self):
        self.prepare('One.');self.translate('abab and abab');block=self.act('review next');uid=block['units'][0]['id']
        cases=[[{'unit':uid,'old':'abab','new':'X'}],[{'unit':uid,'old':'absent','new':'X'}],
               [{'unit':uid,'old':'abab and','new':'X'},{'unit':uid,'old':'and abab','new':'Y'}],
               [{'unit':uid,'old':'and','new':'and'}]]
        before=self.master.read_bytes()
        for edits in cases:
            with self.subTest(edits=edits),self.assertRaises(ValueError):self.act('review patch',ref=block['ref'],edits=edits)
            self.assertEqual(self.master.read_bytes(),before)

    def test_long_target_never_changes_source_group_or_paginates(self):
        self.prepare('One.\n\nTwo.');self.translate('译'*20000);block=self.act('review next')
        self.assertEqual(len(block['units']),2)
        self.assertEqual([len(u['target']) for u in block['units']],[20000,20000])
        self.assertNotIn('continue',block)

    def test_global_restart_from_active_requires_whole_review_again(self):
        self.prepare('One.\n\nTwo.');self.translate();self.reviewed()
        selected=self.act('review next',units=['u000001'])
        result=self.act('review restart',ref=selected['ref']);self.assertTrue(result['review_restarted'])
        self.assertEqual(result['progress']['percent'],0)
        with self.assertRaises(ValueError):self.act('validate',ready=True)
        self.reviewed();self.act('validate',ready=True)

    def test_corrupt_source_and_failed_atomic_write_preserve_saved_bytes(self):
        self.prepare('One.');block=self.act('translate next');before=self.master.read_bytes()
        with patch.object(C.os,'replace',side_effect=OSError('fail')):
            with self.assertRaises(ValueError):self.save(block)
        self.assertEqual(self.master.read_bytes(),before)
        data=C.load_jsonl(self.master);data['units'][0]['source']='Changed'
        with self.assertRaises(ValueError):C.validate(data)

    def test_cli_jsonl_same_object_conflict_and_line_errors(self):
        self.prepare('One.')
        command=[sys.executable,'-B',str(SCRIPT),'--master',str(self.master)]
        result=subprocess.run(command+['translate','next'],input='',capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        lines=[json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual([x['record_type'] for x in lines],['unit','receipt'])
        ref=lines[-1]['ref'];uid=lines[0]['id']
        packet={'op':'translate save','ref':ref,'targets':{uid:'Target'}}
        result=subprocess.run(command+['translate','save'],input=json.dumps(packet)+'\n',capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertNotIn('source',result.stdout)
        before=self.master.read_bytes()
        result=subprocess.run(command+['review','next'],input=json.dumps({'op':'status'})+'\n',capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertEqual(self.master.read_bytes(),before)
        result=subprocess.run(command+['run'],input='{"op":"status"}\n{bad}\n',capture_output=True,text=True)
        self.assertEqual(json.loads(result.stderr)['line'],2)
        self.assertEqual(self.master.read_bytes(),before)

    def test_stdout_defaults_are_lossless_and_do_not_mutate_results(self):
        result = {'units': [
            {'id':'u1', 'parent_id':'u1', 'part_index':0, 'has_more':False,
             'source':'original', 'heading_path':['Heading']},
            {'id':'u2.1', 'parent_id':'u2', 'part_index':0, 'has_more':True,
             'source':'first', 'heading_path':['Heading']},
            {'id':'u2.2', 'parent_id':'u2', 'part_index':1, 'has_more':False,
             'source':'last', 'heading_path':['Heading']}],
            'context':{}, 'pending':[], 'oversize':[], 'ref':'short-ref',
            'progress':{'phase':'prepare','completed':18,'total':18,'unit':'codepoints','percent':100}}
        original=copy.deepcopy(result)
        records=list(W.output_records([result]))
        self.assertEqual(result,original)
        for source, record in zip(original['units'], records[:-1]):
            self.assertEqual(record.pop('record_type'),'unit')
            self.assertEqual(record.get('parent_id',record['id']),source['parent_id'])
            self.assertEqual(record.get('part_index',0),source['part_index'])
            self.assertEqual(record.get('has_more',False),source['has_more'])
            self.assertEqual(record['heading_path'],source['heading_path'])
        receipt=records[-1]
        self.assertEqual(receipt,{'record_type':'receipt','ref':'short-ref','progress':'prepare 18/18 codepoints (100%)'})
        self.assertNotIn('parent_id',records[0])
        self.assertTrue(records[1]['has_more'])
        self.assertEqual(records[2]['parent_id'],'u2')
        self.assertEqual(records[2]['part_index'],1)

    def test_stdout_retains_nonempty_metadata_and_compacts_ack_counts(self):
        result={'context':{'summary':'Keep this'},'pending':['u1'],
                'oversize':[{'id':'u1','characters':2049}], 'saved':['u1','u2'],
                'accepted':['u3']}
        original=copy.deepcopy(result)
        receipt=list(W.output_records([result]))[0]
        self.assertEqual(result,original)
        self.assertEqual(receipt['saved'],2)
        self.assertEqual(receipt['accepted'],1)
        for key in ('context','pending','oversize'):
            self.assertEqual(receipt[key],result[key])

    def test_stdout_retry_and_storage_remain_identical(self):
        self.prepare('Source.\n')
        block=self.act('translate next')
        packet=[{'op':'translate save','ref':block['ref'],
                 'targets':{u['id']:'Target.' for u in block['units']}}]
        saved=W.execute(self.master,packet)
        before=self.master.read_bytes()
        replay=W.execute(self.master,packet)
        self.assertEqual(list(W.output_records(saved)),list(W.output_records(replay)))
        self.assertEqual(list(W.output_records(saved))[0]['saved'],len(block['units']))
        self.assertEqual(self.master.read_bytes(),before)
        self.assertIsInstance(saved[0]['saved'],list)

    def test_progress_text_rollback_and_exact_packet_replay(self):
        self.prepare('One.\n\nTwo.\n')
        self.translate()
        review=self.act('review next')
        self.act('review accept',ref=review['ref'])
        review=self.act('review next',units=[review['units'][0]['id']])
        packet=[{'op':'review restart','ref':review['ref']},{'op':'review next'}]
        result=W.execute(self.master,packet,batch=True)
        before=self.master.read_bytes()
        records=list(W.output_records(result))
        receipts=[r for r in records if r['record_type']=='receipt']
        self.assertEqual(receipts[0]['progress'],'review 0/2 units (0%)')
        self.assertIsInstance(result[0]['progress'],dict)
        self.assertEqual(records,list(W.output_records(W.execute(self.master,packet,batch=True))))
        self.assertEqual(self.master.read_bytes(),before)

if __name__=='__main__':unittest.main()
