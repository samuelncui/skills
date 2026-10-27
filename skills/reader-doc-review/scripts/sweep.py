#!/usr/bin/env python3
"""List every sentence of a text or Markdown document that mentions each term.

Usage: python3 sweep.py DOCUMENT TERM [TERM ...] [--ignore-case]
Use it before and after editing a fact, so all statements of that fact are
changed together.
"""
import argparse
import re
import sys

# Sentence ends: CJK full stops always; Latin ones only before whitespace.
BOUNDARY = re.compile(r'(?<=[。！？；])|(?<=[.!?;])(?=\s)')


def sentences(text):
    """Yield (line number, sentence) for every non-empty sentence."""
    for number, line in enumerate(text.splitlines(), 1):
        for part in BOUNDARY.split(line):
            part = part.strip()
            if part:
                yield number, part


def sweep(text, terms, ignore_case=False):
    """Return {term: [(line number, sentence), ...]} in document order."""
    found = {}
    pairs = list(sentences(text))
    for term in terms:
        needle = term.casefold() if ignore_case else term
        found[term] = [(n, s) for n, s in pairs if needle in (s.casefold() if ignore_case else s)]
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('document')
    parser.add_argument('terms', nargs='+')
    parser.add_argument('--ignore-case', action='store_true')
    args = parser.parse_args(argv)
    try:
        with open(args.document, encoding='utf-8') as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        print('cannot read document: ' + str(error), file=sys.stderr)
        return 2
    for term, matches in sweep(text, args.terms, args.ignore_case).items():
        print('== {} ({})'.format(term, len(matches)))
        for number, sentence in matches:
            print('  L{}: {}'.format(number, sentence))
    return 0


if __name__ == '__main__':
    sys.exit(main())
