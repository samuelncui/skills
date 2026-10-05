"""Structural root-document contracts; prose ownership still requires review.

Run through normal discovery: python3 -m unittest discover -s tests
The small Markdown reader handles inline/reference links, images and fences used
by these guides. It is intentionally not a general Markdown or shell interpreter.
"""
import posixpath
import re
import shlex
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit


LOCALES = ('', '.zh-CN', '.ja', '.fr', '.de')
ROOT = Path(__file__).resolve().parents[1]


def markdown_structure(text):
    """Return destination URLs and (language, contents) fenced examples."""
    prose, fences, body = [], [], []
    opening = None
    for line in text.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if opening is not None:
            if match and match[1][0] == opening[0] and len(match[1]) >= opening[1] and not match[2].strip():
                fences.append((opening[2], '\n'.join(body)))
                opening, body = None, []
            else:
                body.append(line)
        elif match:
            opening = (match[1][0], len(match[1]), match[2].strip())
        else:
            prose.append(line)
    if opening is not None:
        fences.append(('unclosed-fence', '\n'.join(body)))
    text = '\n'.join(prose)
    definitions = {}
    definition = re.compile(r'^ {0,3}\[([^\]]+)\]:\s*(<[^>]+>|\S+).*$', re.M)
    normalize = lambda value: ' '.join(value.casefold().split())
    for match in definition.finditer(text):
        definitions[normalize(match[1])] = match[2].strip('<>')
    text = definition.sub('', text)
    # Destination suffixes also find both links in linked-image syntax.
    destinations = [m[1].strip('<>') for m in re.finditer(r'\]\(\s*(<[^>]+>|[^\s)]+)', text)]
    reference = re.compile(r'\[([^\[\]]+)\]\[([^\]]*)\]')
    for match in reference.finditer(text):
        label = normalize(match[2] or match[1])
        if label in definitions:
            destinations.append(definitions[label])
    text = reference.sub('', text)
    # Shortcut references are valid only when there is a matching definition.
    for match in re.finditer(r'\[([^\[\]]+)\](?!\()', text):
        label = normalize(match[1])
        if label in definitions:
            destinations.append(definitions[label])
    return destinations, fences


def root_contract(root, filename):
    """Return stable diagnostic categories; never judge translated prose."""
    skills = {p.parent.name for p in (root / 'skills').glob('*/SKILL.md')}
    errors = []
    if not skills:
        return ['empty-skill-catalog']
    destinations, fences = markdown_structure((root / filename).read_text(encoding='utf-8'))
    seen = Counter()
    for destination in destinations:
        url = urlsplit(destination)
        path = unquote(url.path)
        if url.scheme or url.netloc:
            # These repository-hosted links have the same ownership as local links.
            if url.netloc.lower() == 'github.com' and path.startswith('/samuelncui/skills/blob/'):
                components = path.split('/', 5)
                path = components[5] if len(components) == 6 else ''
            else:
                continue
        path = posixpath.normpath(path)
        if path == 'skills' or path.startswith('skills/'):
            parts = path.split('/')
            if len(parts) < 2 or parts[1] not in skills:
                errors.append('unknown-skill-target')
                continue
            skill = parts[1]
            guide = root / 'skills' / skill / filename
            expected = 'skills/' + skill + '/' + filename
            if not guide.is_file():
                errors.append('missing-localized-guide')
            if path != expected or url.fragment or url.query:
                errors.append('skill-entry-boundary')
                continue
            if not (root / path).is_file():
                errors.append('missing-entry-target')
            seen[skill] += 1
    for skill in skills:
        if seen[skill] != 1:
            errors.append('catalog-cardinality')
    for language, contents in fences:
        if language not in ('sh', 'bash', 'shell'):
            errors.append('non-install-example')
            continue
        for line in contents.splitlines():
            if not line.strip():
                continue
            try:
                words = shlex.split(line)
            except ValueError:
                errors.append('non-install-command')
                continue
            if len(words) != 6 or words[:5] != ['npx', 'skills', 'add', 'samuelncui/skills', '--skill'] or words[5] not in skills:
                errors.append('non-install-command')
    return errors


class DocumentationBoundaryTests(unittest.TestCase):
    def fixture(self, root, locale=''):
        filename = 'README' + locale + '.md'
        for skill in ('alpha', 'beta'):
            directory = root / 'skills' / skill
            directory.mkdir(parents=True, exist_ok=True)
            (directory / 'SKILL.md').write_text('# Agent workflow\n')
        for skill in ('alpha', 'beta'):
            for suffix in LOCALES:
                (root / 'skills' / skill / ('README' + suffix + '.md')).write_text('# Guide\n')
        text = ('# Any translated heading\n\n'
                '- [alpha](skills/alpha/' + filename + '): LaTeX and JSON documents.\n'
                '- [beta](skills/beta/' + filename + '): Software tests.\n'
                '[Checks](tests/README.md) [License](LICENSE)\n'
                '```sh\nnpx skills add samuelncui/skills --skill alpha\n```\n')
        (root / filename).write_text(text)
        return filename, text

    def test_repository_roots(self):
        for suffix in LOCALES:
            with self.subTest(locale=suffix or 'en'):
                self.assertEqual(root_contract(ROOT, 'README' + suffix + '.md'), [])

    def test_catalog_all_locales_and_free_prose(self):
        for suffix in LOCALES:
            with self.subTest(locale=suffix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                filename, text = self.fixture(root, suffix)
                (root / filename).write_text(text.replace('Any translated heading', '自由な見出し / Utilisation').replace('LaTeX and JSON documents.', 'Fonts, JSON, LaTeX and configurable layouts.'))
                self.assertEqual(root_contract(root, filename), [])

    def test_deep_destinations_and_images_rejected(self):
        cases = (
            '[API](skills/alpha/references/native.md#build)',
            '[Config](./skills/alpha/references/configuration.md)',
            '[Data](skills/alpha/schemas/document.json)',
            '[Script](skills/alpha/scripts/render.py)',
            '[![Preview](skills/alpha/examples/preview.png)](skills/alpha/examples/output.pdf)',
            '[API][guide]\n\n[guide]: skills/alpha/references/native.md',
            '![Preview][image]\n\n[image]: skills/alpha/examples/preview.png',
            '[API][]\n\n[api]: skills/alpha/references/native.md',
            '[API]\n\n[api]: skills/alpha/references/native.md',
            '[API](skills/alpha/../alpha/references/native.md)',
            '[API](skills/alpha/%72eferences/native.md)',
            '[API](https://github.com/samuelncui/skills/blob/main/skills/alpha/references/native.md)',
            '[Build](skills/alpha/README.md#build)',
        )
        for extra in cases:
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                filename, text = self.fixture(root)
                (root / filename).write_text(text + extra + '\n')
                self.assertIn('skill-entry-boundary', root_contract(root, filename))

    def test_reference_entry_links_and_linked_image_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            filename, text = self.fixture(root)
            text = text.replace('[alpha](skills/alpha/README.md)', '[alpha][entry]') + '\n[entry]: <skills/alpha/README.md> "Guide"\n'
            (root / filename).write_text(text)
            self.assertEqual(root_contract(root, filename), [])
        links, _ = markdown_structure('[![image](skills/a/p.png)](skills/a/p.pdf)')
        self.assertEqual(links, ['skills/a/p.png', 'skills/a/p.pdf'])

    def test_missing_duplicate_and_wrong_locale_entries(self):
        for mode, expected in (('missing', 'catalog-cardinality'), ('duplicate', 'catalog-cardinality'), ('wrong-locale', 'skill-entry-boundary'), ('missing-guide', 'missing-localized-guide')):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                filename, text = self.fixture(root, '.fr')
                if mode == 'missing':
                    text = '\n'.join(line for line in text.splitlines() if not line.startswith('- [beta]'))
                elif mode == 'duplicate':
                    text += '\n[beta](skills/beta/' + filename + ')\n'
                elif mode == 'wrong-locale':
                    text = text.replace('skills/alpha/README.fr.md', 'skills/alpha/README.md')
                else:
                    (root / 'skills/alpha/README.fr.md').unlink()
                (root / filename).write_text(text)
                self.assertIn(expected, root_contract(root, filename))

    def test_only_installation_fences(self):
        cases = (
            ('sh', 'python3 scripts/render.py input.json', 'non-install-command'),
            ('sh', 'export BILINGUAL_PDF_SKILL=/some/path', 'non-install-command'),
            ('sh', 'npx skills add samuelncui/skills --skill unknown', 'non-install-command'),
            ('sh', 'npx skills add samuelncui/skills --skill alpha && make', 'non-install-command'),
            ('tex', '\\ParallelSetup{paragraph-flow=breakable}', 'non-install-example'),
            ('json', '{"layout": {}}', 'non-install-example'),
        )
        for language, command, expected in cases:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                filename, text = self.fixture(root)
                (root / filename).write_text(text + '\n~~~' + language + '\n' + command + '\n~~~\n')
                self.assertIn(expected, root_contract(root, filename))

    def test_new_skill_installation_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            filename, text = self.fixture(root)
            (root / 'skills/gamma').mkdir()
            (root / 'skills/gamma/SKILL.md').write_text('# New workflow\n')
            (root / 'skills/gamma' / filename).write_text('# New guide\n')
            (root / filename).write_text(text + '\n[gamma](skills/gamma/' + filename + ')\n```bash\nnpx skills add samuelncui/skills --skill gamma\n```\n')
            self.assertEqual(root_contract(root, filename), [])

    def test_new_skill_cannot_use_agent_entry_as_missing_guide_fallback(self):
        for suffix in LOCALES:
            with self.subTest(locale=suffix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                filename, text = self.fixture(root, suffix)
                (root / 'skills/gamma').mkdir()
                (root / 'skills/gamma/SKILL.md').write_text('# New workflow\n')
                (root / filename).write_text(text + '\n[gamma](skills/gamma/SKILL.md)\n')
                errors = root_contract(root, filename)
                self.assertIn('missing-localized-guide', errors)
                self.assertIn('skill-entry-boundary', errors)
                (root / filename).write_text(text + '\n[gamma](skills/gamma/' + filename + ')\n')
                self.assertIn('missing-entry-target', root_contract(root, filename))
                (root / 'skills/gamma' / filename).write_text('# Human guide\n')
                self.assertEqual(root_contract(root, filename), [])

    def test_owning_guide_remains_free_to_document_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            filename, _ = self.fixture(root)
            (root / 'skills/alpha/README.md').write_text('[Native](references/native.md)\n![Example](examples/preview.png)\n```tex\n\\SomeNativeCommand{}\n```\n')
            self.assertEqual(root_contract(root, filename), [])

    def test_empty_catalog_and_unclosed_example_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(root_contract(root, 'README.md'), ['empty-skill-catalog'])
            filename, text = self.fixture(root)
            (root / filename).write_text(text + '\n```sh\nmake\n')
            self.assertIn('non-install-example', root_contract(root, filename))


if __name__ == '__main__':
    unittest.main()
