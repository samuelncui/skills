#!/usr/bin/env python3
"""Skip PDF renders only for explicitly understood, unrelated changes."""
import argparse
from pathlib import PurePosixPath
import re
import subprocess


GUIDES = {'README.md', 'README.zh-CN.md', 'README.ja.md', 'README.fr.md', 'README.de.md'}
INDEPENDENT_SKILLS = {'testing-workflow', 'write-if-statements'}
NON_RENDER_FILES = {
    'AGENTS.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
    'tests/README.md', 'tests/test_documentation_boundaries.py',
    'tests/test_package_tool.py', 'tests/test_conditionals.py',
    'tools/check_package.py',
}


def unrelated_to_render(path):
    parts = PurePosixPath(path).parts
    if not parts or path.startswith('/') or '..' in parts:
        return False
    if path in NON_RENDER_FILES or path in GUIDES:
        return True
    if len(parts) >= 3 and parts[0] == 'skills':
        if parts[1] in INDEPENDENT_SKILLS:
            return True
        if len(parts) == 3 and (parts[2] in GUIDES or parts[2] in {'SKILL.md', 'LICENSE'}):
            return True
        if len(parts) >= 4 and parts[2] == 'references' and path.endswith('.md'):
            return True
    return False


def needs_render(paths, *, force=False):
    """Unknown paths and empty/incomplete scope retain the full render gate."""
    return force or not paths or any(not unrelated_to_render(path) for path in paths)


def changed_paths(base, head):
    # Event SHAs only: no revisions/options from untrusted filenames or shell text.
    if not all(re.fullmatch(r'[0-9a-fA-F]{40}', value or '') and set(value) != {'0'}
               for value in (base, head)):
        return None
    try:
        result = subprocess.run(
            ['git', 'diff', '--no-renames', '--name-only', '-z', base, head, '--'],
            check=True, capture_output=True, timeout=30,
        )
        return [path.decode('utf-8') for path in result.stdout.split(b'\0') if path]
    except (subprocess.SubprocessError, OSError, UnicodeError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='')
    parser.add_argument('--head', default='')
    parser.add_argument('--event', default='')
    parser.add_argument('--ref', default='')
    args = parser.parse_args()
    force = args.event not in {'push', 'pull_request'} or args.ref.startswith('refs/tags/')
    render = needs_render(changed_paths(args.base, args.head), force=force)
    print('render=' + str(render).lower())


if __name__ == '__main__':
    main()
