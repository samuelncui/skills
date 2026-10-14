"""Independent public protocol invariants for atomic action packets."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/bilingual-translation/scripts/workflow.py'
spec = importlib.util.spec_from_file_location('independent_protocol', SCRIPT)
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)

class ProtocolReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.master = self.root / 'master.jsonl'
        self.source = self.root / 'source.md'

    def act(self, op, **fields):
        return W.execute(self.master, [{'op': op, **fields}])[0]

    def prepare(self, text='One.\n\nTwo.\n\nThree.'):
        self.source.write_bytes(text.encode())
        return self.act('prepare init', source=str(self.source))

    def translate(self):
        while True:
            block = self.act('translate next')
            if block.get('complete'):
                return
            self.act('translate save', ref=block['ref'], targets={u['id']: 'Target '+u['source'] for u in block['units']})

    def cli(self, body, command='run'):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), '--master', str(self.master), command], input=body, capture_output=True, text=True, timeout=15)

    def test_unknown_operation_diagnostic_does_not_echo_payload(self):
        self.prepare()
        secret = 'private-path-or-hash-' + 'a'*1024
        result = self.cli(json.dumps({'op': secret})+'\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stderr)
        self.assertLess(len(result.stderr), 500)
        self.assertFalse(json.loads(result.stderr)['committed'])

    def test_noncontiguous_patch_only_invalidates_changed_units(self):
        self.prepare(); self.translate()
        first = self.act('review next')
        self.act('review accept', ref=first['ref'])
        block = self.act('review next', units=['u000001','u000002','u000003'])
        self.act('review patch', ref=block['ref'], edits=[{'unit':'u000001','old':'One','new':'First'}, {'unit':'u000003','old':'Three','new':'Third'}])
        data = W.core.load_jsonl(self.master)
        self.assertEqual([u['status'] for u in data['units']], ['needs_review','reviewed','needs_review'])
        read = self.act('review next')
        self.assertEqual([u['id'] for u in read['units']], ['u000001','u000003'])
        self.act('review accept', ref=read['ref'])
        self.act('validate', ready=True)

    def test_todo_scope_filter_and_closed_items(self):
        self.prepare('One.\n\n# Heading\n\nTwo.'); self.translate()
        first = self.act('review next')
        self.act('todo add', ref=first['ref'], text='Local', units=['u000001'])
        self.act('todo add', ref=first['ref'], text='Global')
        self.act('review accept', ref=first['ref'])
        second = self.act('review next')
        self.assertEqual([t['text'] for t in second['todos']], ['Global'])
        before = self.master.read_bytes()
        with self.assertRaises(ValueError): self.act('todo resolve', ref=second['ref'], id='todo-1')
        self.assertEqual(self.master.read_bytes(), before)
        self.act('todo resolve', ref=second['ref'], id='todo-2')
        self.assertNotIn('todos', self.act('review next'))

    def test_fail_after_valid_patch_rolls_back_target_and_delivery(self):
        self.prepare(); self.translate(); block = self.act('review next')
        before = self.master.read_bytes()
        packet = [{'op':'review patch','ref':block['ref'],'edits':[{'unit':'u000001','old':'One','new':'First'}]}, {'op':'todo resolve','ref':block['ref'],'id':'todo-unknown'}]
        with self.assertRaises(W.ActionError) as caught: W.execute(self.master, packet, batch=True)
        self.assertEqual(caught.exception.line, 2)
        self.assertFalse(caught.exception.committed)
        self.assertEqual(self.master.read_bytes(), before)
        self.act('review accept', ref=block['ref'])

    def test_post_replace_failure_is_recoverable_and_identical_retry_is_noop(self):
        self.prepare(); block=self.act('translate next')
        packet=[{'op':'translate save','ref':block['ref'],'targets':{u['id']:'Target' for u in block['units']}},{'op':'translate next'}]
        original = W.core._save
        def saved_then_failed(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError('simulated post-commit fsync error')
        with patch.object(W.core, '_save', side_effect=saved_then_failed):
            result=W.execute(self.master, packet, batch=True)
        before=self.master.read_bytes()
        self.assertEqual(W.execute(self.master, packet, batch=True), result)
        self.assertEqual(self.master.read_bytes(), before)

    def test_actual_parallel_competing_packets_have_one_winner(self):
        self.prepare(); block=self.act('translate next')
        command=[sys.executable,'-B',str(SCRIPT),'--master',str(self.master),'run']
        processes=[]
        for target in ('Alpha','Beta'):
            body=json.dumps({'op':'translate save','ref':block['ref'],'targets':{u['id']:target for u in block['units']}})+'\n'
            p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            p.stdin.write(body);p.stdin.close();p.stdin=None
            processes.append(p)
        outputs=[p.communicate(timeout=15) for p in processes]
        self.assertEqual(sorted(p.returncode for p in processes),[0,1],outputs)
        self.assertEqual(len({u['target'] for u in W.core.load_jsonl(self.master)['units']}),1)

    def test_invalid_review_note_reports_action_line_and_rolls_back(self):
        self.prepare(); self.translate(); block = self.act('review next')
        before = self.master.read_bytes()
        packet = [{'op':'todo add','ref':block['ref'],'text':'Check'},
                  {'op':'review accept','ref':block['ref'],'note':'bad\u0001note'}]
        result = self.cli('\n'.join(json.dumps(item) for item in packet)+'\n')
        self.assertNotEqual(result.returncode, 0)
        error = json.loads(result.stderr)
        self.assertEqual(error.get('line'), 2)
        self.assertEqual(error.get('op'), 'review accept')
        self.assertFalse(error['committed'])
        self.assertEqual(self.master.read_bytes(), before)

    def test_restart_ref_packet_replays_without_advancing_round_or_active(self):
        self.prepare(); self.translate()
        block = self.act('review next')
        packet = [{'op':'review restart','ref':block['ref']}, {'op':'review next'}]
        result = W.execute(self.master, packet, batch=True)
        before = self.master.read_bytes()
        self.assertEqual(W.execute(self.master, packet, batch=True), result)
        self.assertEqual(self.master.read_bytes(), before)
        with self.assertRaises(ValueError):
            W.execute(self.master, [packet[0], {'op':'status'}], batch=True)
        self.assertEqual(self.master.read_bytes(), before)
        # A fresh delivered reference still permits a genuinely new full review.
        self.act('review accept', ref=result[-1]['ref'])
        self.act('validate', ready=True)
        revisit = self.act('review next', units=['u000001'])
        fresh = self.act('review restart', ref=revisit['ref'])
        self.assertTrue(fresh['review_restarted'])
        with self.assertRaises(ValueError): self.act('validate', ready=True)

    def test_todo_add_resolve_preserves_current_review_reference(self):
        self.prepare(); self.translate()
        block = self.act('review next')
        todo = self.act('todo add', ref=block['ref'], text='Local check', units=['u000001'])
        read = self.act('review next')
        self.assertEqual(read['ref'], block['ref'])
        self.act('todo resolve', ref=block['ref'], id=todo['todo'])
        self.assertEqual(self.act('review next')['ref'], block['ref'])
        self.act('review accept', ref=block['ref'])
        self.act('validate', ready=True)

    def test_split_exact_2048_unicode_and_original_source_preserved(self):
        left='😀'*2046+'e\u0301';right=' 尾。'
        page=self.prepare(left+right)
        before=self.source.read_bytes()
        self.assertEqual(page['oversize'][0]['characters'],2051)
        result=self.act('prepare split',ref=page['ref'],unit='u000001',cuts=[{'left':'😀e\u0301','right':' 尾'}])
        self.assertTrue(result['complete'])
        data=W.core.load_jsonl(self.master)
        self.assertEqual([u['source'] for u in data['units']],[left,right])
        self.assertEqual(self.source.read_bytes(),before)
        self.assertEqual(len(self.act('translate next')['units'][0]['source']),2048)

    def test_normal_workflow_body_delivery_exactly_three_source_passes(self):
        source='One.\n\nTwo.\n\nThree.'
        preparation=self.prepare(source)
        collected={'prepare':[], 'translate':[], 'review':[]}
        collected['prepare'].extend(u['source'] for u in preparation['units'])
        for phase in ('translate','review'):
            while True:
                read=self.act(phase+' next')
                if read.get('complete'):break
                collected[phase].extend(u['source'] for u in read['units'])
                if phase=='translate':
                    ack=self.act('translate save',ref=read['ref'],targets={u['id']:'T '+u['source'] for u in read['units']})
                else:ack=self.act('review accept',ref=read['ref'])
                self.assertNotIn('units',ack)
                self.assertNotIn('next',ack)
        self.assertEqual(collected,dict.fromkeys(collected,['One.','Two.','Three.']))
        self.act('validate',ready=True)

if __name__ == '__main__': unittest.main()
