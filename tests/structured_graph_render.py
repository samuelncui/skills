#!/usr/bin/env python3
"""Scoped installed structured-graph PDF checks and independent native equivalence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

import pymupdf as fitz
from matrix_support import (
    ROOT, add_matrix_arguments, execute_matrix, initialize_output, run_command,
)

CASES = [('parcel-paired', 'paired'), ('parcel-left', 'left'),
         ('parcel-right', 'right'), ('native-equivalence', 'paired')]

# This authored native manuscript is an independent rendering oracle. It does
# not import generated fragments or reproduce the importer's emission algorithm.
SMALL_GRAPH = {
    'schema_version': 1, 'languages': ['en', 'fr'],
    'title': ['Measure a strip', 'Mesurez une bande'],
    'entry': 'record-length', 'seed_order': ['record-length'],
    'nodes': [{
        'key': 'record-length', 'kind': 'procedure', 'function': 'result',
        'title': ['Record the length', 'Notez la longueur'],
        'prerequisites': ['Use centimetres.', 'Utilisez des centimètres.'],
        'steps': [{'text': ['Record 5 cm.', 'Notez 5 cm.']}],
        'stop': ['The length is recorded.', 'La longueur est notée.'],
    }],
}
NATIVE_DECLARATIONS = r"""
\StudyDeclareGraphNode{record-length}{1}{procedure}{result}{Record the length}{Notez la longueur}
"""
NATIVE_BODY = r"""
\ParallelParagraph{manual-title}
  {\StudyGraphInstruction{Measure a strip}}
  {\StudyGraphInstruction{Mesurez une bande}}
\StudyGraphNode{record-length}
\ParallelParagraph{manual-context}
  {\StudyGraphField{context}{Use centimetres.}}
  {\StudyGraphField{context}{Utilisez des centimètres.}}
\ParallelParagraph{manual-step}
  {\StudyGraphStep{1}{Record 5 cm.}}
  {\StudyGraphStep{1}{Notez 5 cm.}}
\ParallelParagraph{manual-stop}
  {\StudyGraphField{result}{The length is recorded.}}
  {\StudyGraphField{result}{La longueur est notée.}}
"""


def normalized(text):
    return ' '.join(re.sub(r'(?<=\w)-\n(?=\w)', '', text).split()).replace('’', "'")


def install(directory):
    study = directory / 'installed-learning'
    renderer = directory / 'dependencies' / 'rendering'
    for source, destination in ((ROOT / 'skills/study-notes', study),
                                (ROOT / 'skills/bilingual-pdf', renderer)):
        shutil.copytree(source, destination, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('examples', '__pycache__', '*.pyc'))
    env = dict(os.environ, TEXINPUTS=f'{study}/assets//:{renderer}/assets//:',
               PYTHONPATH='')
    return study, renderer, env


def generate(source, destination, study, renderer, env):
    # A bounded matrix resume can retain a fully generated project. Verify it
    # before compiling again, and preserve any interrupted partial generation.
    if destination.exists():
        report_file = destination / 'graph-report.json'
        if report_file.exists():
            report = json.loads(report_file.read_text())
            payload = json.dumps(json.loads(source.read_text()), ensure_ascii=False,
                                 sort_keys=True, separators=(',', ':')).encode()
            if hashlib.sha256(payload).hexdigest() != report['source_sha256']:
                raise AssertionError('Resumed graph source changed')
            for filename, digest in report['outputs'].items():
                if hashlib.sha256((destination / filename).read_bytes()).hexdigest() != digest:
                    raise AssertionError('Resumed generated output changed: ' + filename)
            return report
        index = 1
        while destination.with_name(f'incomplete-generated-{index}').exists():
            index += 1
        destination.rename(destination.with_name(f'incomplete-generated-{index}'))
    proc = run_command(
        [sys.executable, str(study / 'scripts/structured_graph.py'), str(source),
         '--bilingual-pdf-skill', str(renderer), '--output', str(destination)],
        cwd=source.parent, env=env, timeout=30)
    (source.parent / 'import.log').write_text(proc.stdout + proc.stderr)
    if proc.returncode:
        raise AssertionError('Installed importer failed: ' + (proc.stdout + proc.stderr)[-1500:])
    report = json.loads((destination / 'graph-report.json').read_text())
    for filename, digest in report['outputs'].items():
        if hashlib.sha256((destination / filename).read_bytes()).hexdigest() != digest:
            raise AssertionError('Generated output hash mismatch: ' + filename)
    return report


def compile_pdf(directory, source, env):
    (directory / 'main.tex').write_text(source)
    for turn in (1, 2):
        proc = run_command(
            ['xelatex', '-no-shell-escape', '-interaction=nonstopmode',
             '-halt-on-error', 'main.tex'], cwd=directory, env=env, timeout=40)
        log = proc.stdout + proc.stderr
        (directory / f'compile-{turn}.log').write_text(log)
        if proc.returncode:
            raise AssertionError('Native compile failed: ' + log[-1500:])
    if re.search(r'Overfull \\[hv]box|Missing character:|undefined references|'
                 r'Reference .* undefined|multiply defined', log):
        raise AssertionError('Layout, glyph or reference diagnostic')
    return fitz.open(directory / 'main.pdf'), (directory / 'main.aux').read_text()


def labels(aux):
    """Public semantic labels and actual destinations, excluding incidental IDs."""
    pattern = r'\\newlabel\{(graph:[^}]+)\}\{\{([^}]*)\}\{([^}]*)\}\{[^}]*\}\{([^}]+)\}'
    return {name: (number, page, destination)
            for name, number, page, destination in re.findall(pattern, aux)}


def require_destinations(document, aux, expected):
    anchors = labels(aux)
    names = document.resolve_names()
    for anchor in expected:
        if anchor not in anchors or anchors[anchor][2] not in names:
            raise AssertionError('Missing public PDF destination: ' + anchor)
    return anchors


def require_link(document, destination):
    names = document.resolve_names()
    if destination not in names:
        raise AssertionError('Missing link target: ' + destination)
    target = names[destination]
    for page in document:
        for link in page.get_links():
            if link.get('nameddest') == destination:
                return
            if (link.get('kind') == fitz.LINK_GOTO and
                link.get('page') == target.get('page') and
                abs(link.get('to', fitz.Point(-1000, -1000)).y - target['to'][1]) < 1):
                return
    raise AssertionError('No clickable link to actual destination: ' + destination)


def save_pages(document, directory):
    for number, page in enumerate(document, 1):
        page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(directory / f'page-{number}.png')


def check_parcel(document, aux, graph, report, mode, work):
    text = normalized('\n'.join(page.get_text() for page in document))
    crosswalk = report['crosswalk']
    expected_keys = {node['key'] for node in graph['nodes']}
    if {entry['key'] for entry in crosswalk} != expected_keys or len(crosswalk) != 6:
        raise AssertionError('Six visible nodes must have one crosswalk identity each')
    if [entry['reader_id'] for entry in crosswalk] != [f'N{n}' for n in range(1, 7)]:
        raise AssertionError('Reader identities are not contiguous N1 through N6')
    if set(re.findall(r'\bN[0-9]+\b', text)) != {f'N{n}' for n in range(1, 7)}:
        raise AssertionError('Rendered Nx identities differ from the six-node registry')
    sides = (0, 1) if mode == 'paired' else ((0,) if mode == 'left' else (1,))
    by_key = {node['key']: node for node in graph['nodes']}
    for entry in crosswalk:
        for side in sides:
            heading = entry['reader_id'] + ' · ' + normalized(by_key[entry['key']]['title'][side])
            if heading not in text:
                raise AssertionError('Numbered current-language heading missing: ' + heading)
    caller = by_key['pack-parcel']
    call = caller['steps'][0]['call']
    for side in sides:
        for value in (graph['title'][side], call['when'][side], call['outputs'][side],
                      caller['steps'][1]['text'][side]):
            if normalized(value) not in text:
                raise AssertionError('Source helper content missing: ' + value)
    if mode == 'left' and normalized(graph['title'][1]) in text:
        raise AssertionError('Right-edition title leaked into left output')
    if mode == 'right' and normalized(graph['title'][0]) in text:
        raise AssertionError('Left-edition title leaked into right output')
    for side, return_label, resume_label in (
        (0, 'When called:', 'Continue at: Step 2'),
        (1, "En cas d'appel", 'Reprendre à'),
    ):
        if side in sides:
            if text.count(return_label) != 2 or resume_label not in text:
                raise AssertionError('Helper return exits or localized resume instruction missing')
    if any(key in text for key in expected_keys):
        raise AssertionError('An internal graph key leaked into reader text')
    if 'Otherwise, ordinary next:' in text:
        raise AssertionError('A return-only exit gained an ordinary route')
    expected_anchors = ['graph:' + key for key in expected_keys]
    expected_anchors += ['graph:pack-parcel:step:2', 'graph:pack-parcel:completion-check']
    anchors = require_destinations(document, aux, expected_anchors)
    require_link(document, anchors['graph:choose-material'][2])
    require_link(document, anchors['graph:pack-parcel:step:2'][2])
    edges = {tuple(edge) for edge in report['ordering']['edges']}
    for key in call['return_exits']:
        if (key, 'pack-parcel') not in edges:
            raise AssertionError('Declared helper return transition absent: ' + key)
    # Each edition is independently generated; compare any completed sibling
    # reports so a mode-dependent reorder cannot silently pass the full profile.
    for name, _ in CASES[:3]:
        sibling = work / name / 'generated' / 'graph-report.json'
        if sibling.exists():
            if json.loads(sibling.read_text())['crosswalk'] != crosswalk:
                raise AssertionError('Generated crosswalk differs between editions')


def run_case(case, work):
    name, mode = case
    directory = work / name
    directory.mkdir(exist_ok=True)
    study, renderer, env = install(directory)
    template = (ROOT / 'skills/study-notes/examples/structured-graph.tex').read_text()
    template = template.replace(r'\ParallelSelect{paired}', r'\ParallelSelect{' + mode + '}')
    source = directory / 'graph.json'
    if name == 'native-equivalence':
        source.write_text(json.dumps(SMALL_GRAPH, ensure_ascii=False, indent=2) + '\n')
    else:
        shutil.copyfile(ROOT / 'skills/study-notes/examples/structured-graph.json', source)
    generated = directory / 'generated'
    report = generate(source, generated, study, renderer, env)
    with compile_pdf(generated, template, env)[0] as document:
        aux = (generated / 'main.aux').read_text()
        if name == 'native-equivalence':
            native = directory / 'native'
            native.mkdir(exist_ok=True)
            native_source = template.replace(r'\input{graph-declarations.tex}', NATIVE_DECLARATIONS)
            native_source = native_source.replace(r'\input{graph-body.tex}', NATIVE_BODY)
            with compile_pdf(native, native_source, env)[0] as oracle:
                native_aux = (native / 'main.aux').read_text()
                # Independent paragraph boundaries change PDF object reading
                # order. Compare visible text per language column, not storage
                # order across the two columns; this is not a tagged-PDF claim.
                def column_text(pdf):
                    columns = [[], []]
                    for page in pdf:
                        middle = page.rect.width / 2
                        for side, bounds in enumerate(((0, middle), (middle, page.rect.width))):
                            columns[side].append(page.get_text(clip=fitz.Rect(
                                bounds[0], 0, bounds[1], page.rect.height)))
                    return [normalized(' '.join(parts)) for parts in columns]
                if len(document) != len(oracle) or column_text(document) != column_text(oracle):
                    raise AssertionError('Generated PDF text differs from independently authored native text')
                expected = ('graph:record-length', 'graph:record-length:step:1')
                generated_labels = require_destinations(document, aux, expected)
                native_labels = require_destinations(oracle, native_aux, expected)
                if {key: value[:2] for key, value in generated_labels.items()} != {
                        key: value[:2] for key, value in native_labels.items()}:
                    raise AssertionError('Semantic AUX label numbers/pages differ from native manuscript')
                save_pages(oracle, native)
        else:
            check_parcel(document, aux, json.loads(source.read_text()), report, mode, work)
        save_pages(document, generated)
        return {'case': name, 'passed': True, 'errors': [], 'pages': len(document),
                'crosswalk': report['crosswalk'], 'source_sha256': report['source_sha256'],
                'outputs': report['outputs'], 'pymupdf_version': fitz.VersionBind}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    add_matrix_arguments(parser)
    args = parser.parse_args()
    work = initialize_output(args.output, args.resume)
    return execute_matrix(CASES, lambda case: run_case(case, work), work, args,
                          'structured-graph-render')


if __name__ == '__main__':
    raise SystemExit(main())
