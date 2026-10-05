"""Exercise conservative CI impact decisions without running the PDF matrix."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ci_scope', ROOT / 'tools/classify_ci_changes.py')
ci_scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_scope)


class CIScopeTests(unittest.TestCase):
    def test_documentation_and_independent_skills_skip_render(self):
        paths = ['AGENTS.md', 'README.zh-CN.md', 'tests/README.md',
                 'skills/bilingual-pdf/README.fr.md', 'skills/study-notes/SKILL.md',
                 'skills/bilingual-pdf/references/latex.md',
                 'skills/testing-workflow/examples/test_tags.py',
                 'skills/write-if-statements/examples/conditionals.py',
                 'tests/test_conditionals.py', 'tests/test_package_tool.py',
                 'tests/test_documentation_boundaries.py', 'tools/check_package.py']
        self.assertFalse(ci_scope.needs_render(paths))

    def test_render_shared_unknown_and_classifier_changes_keep_full_gate(self):
        paths = ['skills/bilingual-pdf/assets/paralleltext.sty',
                 'skills/study-notes/assets/studytools.sty',
                 'skills/bilingual-pdf/examples/en-fr/content.json',
                 'skills/study-notes/examples/coverage-review.md',
                 'tests/fixtures/garden-en-fr.json', 'tests/study_matrix.py',
                 'tools/export_native_examples.py', 'tools/tutorial-content.json',
                 'requirements.txt', '.github/workflows/validate.yml',
                 'tools/classify_ci_changes.py', 'tests/test_ci_scope.py',
                 'skills/new-skill/scripts/run.py', 'unknown.md',
                 '/README.md', '../README.md']
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(ci_scope.needs_render(['README.md', path]))

    def test_empty_unknown_or_forced_scope_keeps_full_gate(self):
        for paths in ([], None):
            self.assertTrue(ci_scope.needs_render(paths))
        self.assertTrue(ci_scope.needs_render(['README.md'], force=True))

    def test_invalid_or_unreadable_revisions_keep_full_gate(self):
        for revision in ('', '0' * 40, '--all', 'main'):
            with self.subTest(revision=revision):
                self.assertIsNone(ci_scope.changed_paths(revision, 'a' * 40))
        with patch.object(ci_scope.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'git')):
            self.assertTrue(ci_scope.needs_render(ci_scope.changed_paths('a' * 40, 'b' * 40)))

    def test_nul_delimited_paths_and_deletions_are_preserved(self):
        result = subprocess.CompletedProcess([], 0, stdout=b'README.md\0odd\npath.py\0')
        with patch.object(ci_scope.subprocess, 'run', return_value=result) as run:
            paths = ci_scope.changed_paths('a' * 40, 'b' * 40)
        self.assertEqual(paths, ['README.md', 'odd\npath.py'])
        self.assertIn('--no-renames', run.call_args.args[0])
        self.assertTrue(ci_scope.needs_render(paths))

    def test_real_git_diff_preserves_old_render_path_on_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode().strip()
            git('init', '-q')
            git('config', 'user.name', 'Fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            (root / 'renderer.py').write_text('example\n')
            git('add', '.'); git('commit', '-qm', 'Base fixture')
            base = git('rev-parse', 'HEAD')
            git('mv', 'renderer.py', 'README.md'); git('commit', '-qm', 'Rename fixture')
            head = git('rev-parse', 'HEAD')
            command = ['python3', str(ROOT / 'tools/classify_ci_changes.py'), '--base', base, '--head', head]
            self.assertEqual(subprocess.check_output(command + ['--event', 'push'], cwd=root, text=True).strip(), 'render=true')
            base = head
            (root / 'README.md').write_text('changed guide\n')
            git('add', '.'); git('commit', '-qm', 'Docs fixture')
            head = git('rev-parse', 'HEAD')
            command = ['python3', str(ROOT / 'tools/classify_ci_changes.py'), '--base', base, '--head', head]
            for event, ref, expected in [('push', 'refs/heads/main', 'false'),
                                         ('pull_request', 'refs/pull/1/merge', 'false'),
                                         ('workflow_dispatch', 'refs/heads/main', 'true'),
                                         ('push', 'refs/tags/v1', 'true')]:
                with self.subTest(event=event, ref=ref):
                    output = subprocess.check_output(command + ['--event', event, '--ref', ref], cwd=root, text=True)
                    self.assertEqual(output.strip(), 'render=' + expected)


if __name__ == '__main__':
    unittest.main()
