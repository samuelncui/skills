"""Public contracts of the reader-doc-review helper scripts."""
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/reader-doc-review/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sweep = load('sweep')
textdiff = load('textdiff')


class SweepTests(unittest.TestCase):
    def test_every_statement_of_a_term_is_listed_with_its_line(self):
        text = ('Volunteers check every tool. Loans last seven days.\n\n'
                '志愿者在归还时检查工具。押金只收电动工具。\n'
                '| FAQ | When do volunteers check tools? On return. |\n')
        found = sweep.sweep(text, ['check', '检查', 'deposit'])
        self.assertEqual(found['check'], [(1, 'Volunteers check every tool.'),
                                          (4, '| FAQ | When do volunteers check tools?')])
        self.assertEqual(found['检查'], [(3, '志愿者在归还时检查工具。')])
        self.assertEqual(found['deposit'], [])

    def test_ignore_case_and_cli_output(self):
        self.assertEqual(sweep.sweep('Deposit only for power tools.', ['deposit'], ignore_case=True)['deposit'],
                         [(1, 'Deposit only for power tools.')])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'doc.md'
            path.write_text('A deposit applies. No deposit for ladders.\n', encoding='utf-8')
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(sweep.main([str(path), 'deposit']), 0)
        self.assertEqual(out.getvalue().splitlines(),
                         ['== deposit (2)', '  L1: A deposit applies.', '  L1: No deposit for ladders.'])

    def test_missing_document_is_an_error(self):
        self.assertEqual(sweep.main(['/nonexistent/document.md', 'x']), 2)


class TextDiffTests(unittest.TestCase):
    BEFORE = ('# Guide\n\nVolunteers check every tool.\n\n![Flow](flow.png)\n'
              'Loans last seven days.\n')

    def test_only_changed_lines_are_reported_and_blank_lines_ignored(self):
        after = self.BEFORE.replace('check every tool.', 'check tools on return.') + '\n\n'
        result = textdiff.compare(self.BEFORE, after)
        self.assertEqual(result['changed'], 1)
        self.assertEqual(result['removed'], ['Volunteers check every tool.'])
        self.assertEqual(result['added'], ['Volunteers check tools on return.'])
        self.assertFalse(result['figures_changed'])

    def test_figure_reference_changes_are_listed(self):
        after = self.BEFORE.replace('![Flow](flow.png)', '<img src="flow-v2.png" alt="Flow">')
        result = textdiff.compare(self.BEFORE, after)
        self.assertTrue(result['figures_changed'])
        self.assertEqual((result['figures_before'], result['figures_after']), (['flow.png'], ['flow-v2.png']))

    def test_change_budget_sets_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            before, after = Path(directory) / 'before.md', Path(directory) / 'after.md'
            before.write_text(self.BEFORE, encoding='utf-8')
            after.write_text(self.BEFORE.replace('seven', 'ten').replace('every', 'each'), encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(textdiff.main([str(before), str(after), '--max-changed', '2']), 0)
                self.assertEqual(textdiff.main([str(before), str(after), '--max-changed', '1']), 1)
                self.assertEqual(textdiff.main([str(before), str(Path(directory) / 'missing.md')]), 2)


if __name__ == '__main__':
    unittest.main()
