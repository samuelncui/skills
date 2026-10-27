#!/usr/bin/env python3
"""Compare two exports of a document and report changed text lines and figures.

Usage: python3 textdiff.py BEFORE AFTER [--max-changed N]
Blank lines and trailing spaces are ignored. Figure references are Markdown
images and HTML img src attributes; any change in them is listed separately.
Exits 1 when more than N lines changed, so an edit can be held to its plan.
"""
import argparse
import difflib
import json
import re
import sys

FIGURE = re.compile(r'!\[[^\]]*\]\(\s*<?([^)\s>]+)|<img\b[^>]*\bsrc="([^"]+)"')


def lines(text):
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def figures(text):
    return [a or b for a, b in FIGURE.findall(text)]


def compare(before, after):
    """Return removed/added lines and figure lists for two document texts."""
    old, new = lines(before), lines(after)
    removed, added = [], []
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            removed.extend(old[i1:i2])
            added.extend(new[j1:j2])
    old_figures, new_figures = figures(before), figures(after)
    return {
        'changed': max(len(removed), len(added)),
        'removed': removed,
        'added': added,
        'figures_changed': old_figures != new_figures,
        'figures_before': old_figures,
        'figures_after': new_figures,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('before')
    parser.add_argument('after')
    parser.add_argument('--max-changed', type=int)
    args = parser.parse_args(argv)
    try:
        texts = []
        for path in (args.before, args.after):
            with open(path, encoding='utf-8') as handle:
                texts.append(handle.read())
    except (OSError, UnicodeDecodeError) as error:
        print('cannot read document: ' + str(error), file=sys.stderr)
        return 2
    result = compare(*texts)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.max_changed is not None and result['changed'] > args.max_changed:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
