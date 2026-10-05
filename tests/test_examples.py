import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.collect_example_outputs import (ARTICLES, FORMS, INPUTS, PDFS, PREVIEWS, SHARED_IMAGES,
                                           collect_examples, check_examples)
from matrix_support import execute_matrix, implementation_fingerprint, BlockedCase, InfrastructureTimeout, run_command, repeat_text

class ExampleTests(unittest.TestCase):
    def fixture(self, root):
        import pymupdf
        matrix = root/'matrix'
        matrix.mkdir()
        source = root/'source'
        source.mkdir()
        for name in INPUTS:
            path = source/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'original input')
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=200, height=200)
            page.insert_text((20, 40), 'Public example')
            data = pdf.tobytes()
        for name in PDFS.values():
            path = matrix/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (matrix/'matrix.json').write_text(json.dumps({
            'ok': True, 'complete': False, 'implementation_sha256': implementation_fingerprint(source),
            'tests': [{'case': name, 'status': 'passed', 'passed': True}
                      for name in [pair+'-bilingual' for pair in ARTICLES]+['study-example-all']]}))
        (matrix/'private.log').write_text('must not be copied')
        return matrix, source

    def test_nine_pdfs_nine_previews_and_one_shared_pool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix, source = self.fixture(root)
            out = root/'bundle'
            records = collect_examples(matrix, out, source)
            self.assertEqual(len(records), 9)
            self.assertEqual(len(list(out.rglob('*.pdf'))), 9)
            self.assertTrue(all((out/name).is_file() for name in PREVIEWS))
            self.assertEqual(len(list((out/'skills/bilingual-pdf/examples/shared').glob('*.png'))), 7)
            self.assertTrue(all((out/'skills/study-notes/examples'/(form+'.pdf')).exists() for form in FORMS))
            self.assertFalse((out/'private.log').exists())
            self.assertEqual(check_examples(out, source), 9)

    def test_failed_incomplete_and_stale_evidence_rejected(self):
        for mode in ('failed', 'unrun', 'stale', 'missing'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                matrix, source = self.fixture(root)
                path = matrix/'matrix.json'
                data = json.loads(path.read_text())
                if mode == 'failed':
                    data['ok'] = False
                elif mode == 'unrun':
                    data['tests'][0]['status'] = 'unrun'
                elif mode == 'stale':
                    data['implementation_sha256'] = 'old'
                else:
                    data['tests'].pop()
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    collect_examples(matrix, root/'bundle', source)

    def test_missing_inputs_and_outputs_rejected(self):
        for kind in ('pdf', 'source'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                matrix, source = self.fixture(root)
                (matrix/next(iter(PDFS.values())) if kind == 'pdf' else source/INPUTS[0]).unlink()
                with self.assertRaises(ValueError):
                    collect_examples(matrix, root/'bundle', source)

    def test_manifests_portable_named_packages_and_no_operational_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix, source = self.fixture(root)
            out = root/'bundle'
            collect_examples(matrix, out, source)
            manifests = list(out.glob('skills/*/examples/MANIFEST.json'))
            self.assertEqual(len(manifests), 2)
            for path in manifests:
                raw = path.read_text()
                self.assertNotIn(str(root), raw)
                self.assertNotIn('updated_at', raw)
                data = json.loads(raw)
                self.assertTrue(data['source_hashes'])
                self.assertIn('bilingual-pdf', data['package_dependencies'])
                if 'study-notes' in str(path):
                    self.assertIn('study-notes', data['package_dependencies'])
                names = list(data['source_hashes'])+[x['path'] for x in data['files']+data['previews']]
                names += [name for hashes in data['package_dependencies'].values() for name in hashes]
                for name in names:
                    self.assertFalse(Path(name).is_absolute())
                    self.assertNotIn('..', Path(name).parts)
                    self.assertFalse(name.startswith('skills/'))

    def test_changed_or_extra_bundle_content_rejected(self):
        for kind in ('log', 'preview', 'shared', 'package'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                matrix, source = self.fixture(root)
                out = root/'bundle'
                collect_examples(matrix, out, source)
                if kind == 'log':
                    (out/'skills/bilingual-pdf/examples/private.log').write_text('not publishable')
                elif kind == 'preview':
                    (out/next(iter(PREVIEWS))).unlink()
                elif kind == 'shared':
                    (source/'skills/bilingual-pdf/examples/shared/layout-anatomy.png').write_bytes(b'changed')
                else:
                    (source/'skills/study-notes/assets/studytools.sty').write_bytes(b'changed')
                with self.assertRaises(ValueError):
                    check_examples(out, source)

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix, source = self.fixture(root)
            out = root/'bundle'
            out.mkdir()
            with self.assertRaises(ValueError):
                collect_examples(matrix, out, source)

    def test_pdf_with_private_path_rejected(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix, source = self.fixture(root)
            with pymupdf.open() as pdf:
                pdf.new_page()
                pdf.set_metadata({'subject': '/workspace/private/source'})
                pdf.save(matrix/next(iter(PDFS.values())))
            with self.assertRaisesRegex(ValueError, 'Machine-specific'):
                collect_examples(matrix, root/'bundle', source)

class MatrixRunnerTests(unittest.TestCase):
    def run_cases(self, root, run, selected=None, budget=0):
        args = argparse.Namespace(case=selected, budget_seconds=budget)
        with patch('matrix_support.implementation_fingerprint', return_value='unchanged'), contextlib.redirect_stdout(io.StringIO()):
            result = execute_matrix([('one',), ('two',)], run, root, args, 'unit')
        return result, json.loads((root/'matrix.json').read_text())

    def test_selected_success_is_not_a_full_pass_and_resume_does_not_retry_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            def run(case):
                calls.append(case[0])
                return {'case': case[0], 'passed': case[0] == 'one'}
            code, report = self.run_cases(root, run, ['one'])
            self.assertEqual(code, 0)
            self.assertFalse(report['complete'])
            self.assertEqual(report['tests'][1]['status'], 'not_requested')
            code, report = self.run_cases(root, run)
            self.assertEqual(code, 1)
            self.assertEqual(calls, ['one', 'two'])
            self.run_cases(root, run)
            self.assertEqual(calls, ['one', 'two'])

    def test_failed_assertions_are_visible_in_console_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = argparse.Namespace(case=None, budget_seconds=0)
            output = io.StringIO()
            def fail(case):
                return {'case': case[0], 'passed': False,
                        'checks': {'companion_target_resolves': False},
                        'documents': {'quick': {'errors': ['Missing named target']}}}
            with patch('matrix_support.implementation_fingerprint', return_value='unchanged'), contextlib.redirect_stdout(output):
                code = execute_matrix([('one',)], fail, root, args, 'diagnostic')
            self.assertEqual(code, 1)
            diagnostic = json.loads(output.getvalue().splitlines()[0])['diagnostics']
            self.assertFalse(diagnostic['checks']['companion_target_resolves'])
            self.assertEqual(diagnostic['documents']['quick']['errors'], ['Missing named target'])
            self.assertEqual(diagnostic, json.loads((root/'case-results/one.json').read_text()))

    def test_blocked_case_can_resume_with_preserved_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def blocked(case):
                raise BlockedCase('Missing tool')
            code, report = self.run_cases(root, blocked)
            self.assertEqual(code, 75)
            self.assertEqual([x['status'] for x in report['tests']], ['blocked', 'unrun'])
            code, report = self.run_cases(root, lambda case: {'case': case[0], 'passed': True})
            self.assertEqual(code, 0)
            self.assertTrue(report['complete'])
            self.assertEqual(report['tests'][0]['previous_attempts'][0]['status'], 'blocked')

    def test_command_timeout_reaps_owned_process_and_preserves_output(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(InfrastructureTimeout):
                run_command([sys.executable, '-c', 'import os,time; print(os.getpid(), flush=True); time.sleep(20)'],
                            cwd=root, timeout=.5)
            pid = int((root/'interrupted-command.log').read_text().strip())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def test_repeated_mixed_script_fixture_has_no_whitespace_only_runs(self):
        source={'runs':[{'text':'شرح ', 'direction':'rtl'},{'text':'API', 'direction':'ltr'}]}
        result=repeat_text(source)
        self.assertEqual(len(result['runs']),6)
        self.assertTrue(all(run['text'].strip() for run in result['runs']))
        self.assertEqual(source['runs'][-1]['text'],'API')
        self.assertEqual(''.join(run['text'] for run in result['runs']),'شرح API '*3)

    def test_insufficient_budget_reports_unrun(self):
        with tempfile.TemporaryDirectory() as directory:
            code, report = self.run_cases(Path(directory), lambda case: self.fail('Must not execute'), budget=.001)
            self.assertEqual(code, 75)
            self.assertEqual([x['status'] for x in report['tests']], ['unrun', 'unrun'])

class InstalledExampleTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]
    article_root = root/'skills/bilingual-pdf/examples'

    def test_all_editions_share_one_complete_article(self):
        documents = [json.loads((self.article_root/pair/'source.json').read_text()) for pair in ARTICLES]
        self.assertEqual(len(documents), 5)
        structure = None
        translations = {}
        for doc in documents:
            skeleton = [{k: v for k, v in block.items() if k not in ('text', 'headers', 'rows', 'image')} for block in doc['blocks']]
            if structure is None:
                structure = skeleton
            self.assertEqual(skeleton, structure)
            self.assertTrue(any(b.get('placement') == 'shared' for b in doc['blocks']))
            self.assertTrue(any(b.get('flow') == 'breakable' for b in doc['blocks']))
            self.assertEqual(doc['layout']['paragraph_flow'], 'breakable')
            self.assertFalse(any(b.get('break_before') for b in doc['blocks']))
            self.assertTrue({'continuing-prose', 'figures-and-references', 'shared-layout',
                             'localized-pipeline', 'quotation', 'routes-table'} <= {b['id'] for b in doc['blocks']})
            for side, language in enumerate(doc['languages']):
                text = {'title': doc['title'][side], 'blocks': [{k: b[k][side] for k in ('text', 'headers', 'rows') if k in b} for b in doc['blocks']]}
                if language in translations:
                    self.assertEqual(text, translations[language])
                translations[language] = text
        self.assertEqual(set(translations), {'en', 'fr', 'ar', 'he', 'zh-Hans', 'ja'})

    def test_example_asset_ownership_and_study_native_sources(self):
        import hashlib
        hashes = set()
        for pair in ARTICLES:
            source = self.article_root/pair/'source.json'
            for filename in ('main.tex', 'content.tex', 'languages.tex'):
                self.assertTrue((source.parent/filename).is_file())
            self.assertFalse((source.parent/'paralleltext.sty').exists())
            document = json.loads(source.read_text())
            for block in document['blocks']:
                if block.get('kind') != 'figure':
                    continue
                names = block['image'] if isinstance(block['image'], list) else [block['image']]
                for name in names:
                    image = (self.article_root/'shared'/name).resolve()
                    self.assertTrue(image.is_relative_to((self.article_root/'shared').resolve()) and image.is_file())
                    self.assertFalse((source.parent/name).exists())
                    if block.get('placement') == 'shared':
                        hashes.add(hashlib.sha256(image.read_bytes()).hexdigest())
                if block['id'] == 'localized-pipeline':
                    self.assertEqual(names, ['pipeline-'+language+'.png' for language in document['languages']])
                    self.assertNotEqual(hashlib.sha256((self.article_root/'shared'/names[0]).read_bytes()).digest(),
                                        hashlib.sha256((self.article_root/'shared'/names[1]).read_bytes()).digest())
        self.assertEqual(len(hashes), 1)
        self.assertFalse(list((self.article_root.parent/'assets').glob('*.png')))
        study = self.root/'skills/study-notes/examples'
        for name in [form+'.tex' for form in FORMS]+['source.md', 'source-map.json', 'entries.tex', 'decisions.tex']:
            self.assertTrue((study/name).is_file())
        self.assertFalse((self.root/'skills/study-notes/scripts/course_documents.py').exists())

if __name__ == '__main__':
    unittest.main()
