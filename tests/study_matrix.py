#!/usr/bin/env python3
"""Native study integration: selected forms, isolated installs, references and errors.

Run serial bounded batches with --budget-seconds 95, then --resume against the
same unchanged source tree. Focused runtime regressions remain in
native_regressions.py; this suite tests end-to-end workflow contracts.
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
import pymupdf
from matrix_support import add_matrix_arguments, initialize_output, execute_matrix, run_command

ROOT = Path(__file__).resolve().parents[1]
BUILD = ['latexmk', '-norc', '-xelatex', '-interaction=nonstopmode', '-halt-on-error',
         '-latexoption=-no-shell-escape']
FORMS = ('notes', 'quick-reference', 'keyword-index', 'decision-tree')

def undefined_reference_diagnostics(log):
    """Preserve wrapped warning labels, not only LaTeX's final summary."""
    warnings = re.findall(r'(?:LaTeX|Package [^\n]+) Warning:[\s\S]*?(?=\n\s*\n|\Z)', log)
    return [warning for warning in warnings if 'undefined' in warning.lower()]

def pdf_links(pdf, project):
    """Inspect PDF actions: PyMuPDF may expose named links as LAUNCH/NAMED."""
    records = []
    for page in pdf:
        for link in page.get_links():
            action = pdf.xref_get_key(link['xref'], 'A/S')[1]
            record = dict(link, action=action)
            if action == '/GoToR':
                record['file'] = pdf.xref_get_key(link['xref'], 'A/F')[1]
                record['target'] = pdf.xref_get_key(link['xref'], 'A/D')[1]
                target_path = project/record['file']
                record['target_resolves'] = False
                if target_path.is_file() and not Path(record['file']).is_absolute() and '..' not in Path(record['file']).parts:
                    with pymupdf.open(target_path) as target:
                        record['target_resolves'] = record['target'] in target.resolve_names()
            records.append(record)
    return records

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    add_matrix_arguments(parser)
    args = parser.parse_args()
    work = initialize_output(args.output, args.resume)
    renderer = work/'unrelated engines'/'chosen renderer'
    study = work/'independent workflows'/'native study'
    for source, target in ((ROOT/'skills/bilingual-pdf', renderer), (ROOT/'skills/study-notes', study)):
        shutil.copytree(source, target, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pdf', '*preview.png', '*.aux',
                                                     '*.log', '*.fls', '*.fdb_latexmk', '*.xdv', '*.out'))
    sys.path.insert(0, str(renderer/'scripts'))
    from bilingual_pdf import check_pdf
    environment = {**os.environ, 'BILINGUAL_PDF_SKILL': str(renderer), 'STUDY_NOTES_SKILL': str(study),
                   'TEXINPUTS': str(study/'assets')+'//:'+str(renderer/'assets')+'//:'}

    def build(project, name='main'):
        proc = run_command(BUILD+[name+'.tex'], cwd=project, env=environment, timeout=105)
        (project/(name+'.stdout')).write_text(proc.stdout+proc.stderr)
        return proc

    def qa(project, name, minimum_margin=5):
        report = check_pdf(project/(name+'.pdf'), False, True, minimum_margin)
        log = (project/(name+'.log')).read_text()
        warnings = [line for line in log.splitlines() if any(token in line for token in
                    ('Overfull', 'Missing character:', 'undefined references', 'multiply defined',
                     'No hyphenation patterns'))]
        report['errors'] += warnings
        report['undefined_reference_details'] = undefined_reference_diagnostics(log)
        recorder = (project/(name+'.fls')).read_text()
        inputs = [(project/line[6:]).resolve() for line in recorder.splitlines() if line.startswith('INPUT ')]
        report['explicit_installed_packages_used'] = (renderer/'assets/paralleltext.sty').resolve() in inputs
        if name not in ('companion-one', 'companion-two'):
            report['explicit_installed_packages_used'] &= (study/'assets/studytools.sty').resolve() in inputs
        report['no_checkout_inputs'] = not any(path.is_relative_to(ROOT/'skills') for path in inputs)
        report['ok'] = report['ok'] and not report['errors'] and report['explicit_installed_packages_used'] and report['no_checkout_inputs']
        return report

    def example(case):
        ident, products = case['name'], case.get('products')
        project = work/ident
        shutil.copytree(study/'examples', project, dirs_exist_ok=True)
        env = dict(environment)
        env.pop('PRODUCTS', None)
        if products is not None:
            env['PRODUCTS'] = products
        if case.get('missing'):
            env.pop('BILINGUAL_PDF_SKILL')
        proc = run_command(['make', 'LATEXMK='+' '.join(BUILD)], cwd=project, env=env, timeout=105)
        (project/'build.stdout').write_text(proc.stdout+proc.stderr)
        if case.get('error'):
            return {'case': ident, 'passed': proc.returncode != 0 and case['error'] in proc.stdout+proc.stderr,
                    'compile_exit': proc.returncode, 'expected_error': case['error']}
        forms = products.split() if products is not None else ['notes', 'quick-reference']
        reports = {form: qa(project, form) for form in forms} if proc.returncode == 0 else {}
        actual = {path.stem for path in project.glob('*.pdf')}
        checks = {'only_selected_forms_exist': actual == set(forms),
                  'documents_pass': len(reports) == len(forms) and all(report['ok'] for report in reports.values())}
        for form in forms:
            if form == 'notes' or not (project/(form+'.pdf')).exists():
                continue
            with pymupdf.open(project/(form+'.pdf')) as pdf:
                links = pdf_links(pdf, project)
                remote = [link for link in links if link['action'] == '/GoToR']
                checks[form+'_companion_policy'] = (bool(remote) if 'notes' in forms and form != 'decision-tree' else not remote)
                checks[form+'_portable_companion_paths'] = all(link.get('file') == 'notes.pdf' and link['target_resolves'] for link in remote)
                checks[form+'_local_links_resolve'] = any(link['action'] == '/GoTo' for link in links) and all(0 <= link.get('page', -1) < len(pdf)
                    for link in links if link['action'] == '/GoTo')
                if form in ('quick-reference', 'keyword-index'):
                    text = '\n'.join(page.get_text() for page in pdf)
                    checks[form+'_single_registry'] = 'Aliases' in text and 'Decision Tree' in text and 'Quick Reference' in text
                    checks[form+'_has_alphabet_tabs'] = any(
                        word[4] in ('A', 'D', 'Q') and (word[0] < 30 or word[0] > page.rect.width-35)
                        for page in pdf for word in page.get_text('words'))
                    if form == 'keyword-index':
                        checks['index_omits_concept_bodies'] = 'Choose a method from observable conditions.' not in text
                    else:
                        checks['quick_preserves_concept_bodies'] = 'observable conditions' in text
        return {'case': ident, 'passed': proc.returncode == 0 and all(checks.values()),
                'compile_exit': proc.returncode, 'checks': checks, 'documents': reports,
                'error': proc.stdout[-1800:] if proc.returncode else None}

    def write_project(ident, preamble, body):
        project = work/ident
        project.mkdir(exist_ok=True)
        (project/'main.tex').write_text(r'\documentclass[10pt,twoside]{article}'+'\n'+
            r'\usepackage{studytools}'+'\n'+preamble+'\n'+r'\begin{document}'+'\n'+body+'\n'+r'\end{document}'+'\n')
        return project

    registry = r'''
\StudyAlphabetNavigation
\ParallelSetup{tabs=true,tab-height=5mm,tab-top=24mm,tab-step=7mm}
\StudyDeclareConcept[lookup=shared,context-left=Meaning one,context-right=Meaning one,notes-source=first]{alpha}{alpha}{Shared headword}{Shared headword}{first-section}{
 \ParallelText{detail-one}{PRIMARYDETAIL}{PRIMARYDETAIL}
 \clearpage
 \StudySubentry{precise}{\ParallelText{precise-body}{SUBENTRYDETAIL}{SUBENTRYDETAIL}}
}
\StudyDeclareSubentry{precise}{alpha}{Exact subentry}{Exact subentry}{second-section}
\StudyDeclareConcept[lookup=shared,context-left=Meaning two,context-right=Meaning two,notes-source=second]{beta}{alpha}{Shared headword}{Shared headword}{other-section}{
 \ParallelText{detail-two}{SECONDMEANING}{SECONDMEANING}
}
\StudyDeclareRoute[lookup=shared]{redundant}{alpha}{Shared headword}{Shared headword}
\StudyRouteTarget{redundant}{alpha}{}{}
\StudyDeclareAlias{alias}{alias}{Alias route}{Alias route}{precise}
\StudyDeclareRoute{zebra}{zebra}{Zebra route}{Zebra route}
\StudyRouteTarget{zebra}{beta}{Second sense}{Second sense}
\StudyRouteTarget{zebra}{precise}{Exact detail}{Exact detail}
'''
    def native(case):
        ident = case['name']
        preamble, body = case['preamble'], case['body']
        if case.get('registry'):
            preamble = registry
            if case.get('companions'):
                preamble += r'\StudyDeclareNotesSource{first}{First notes}{First notes}{companion-one}{companion-one.pdf}'
                preamble += r'\StudyDeclareNotesSource{second}{Second notes}{Second notes}{companion-two}{companion-two.pdf}'
        project = write_project(ident, preamble, body)
        if case.get('companions'):
            for name, content in (
                ('companion-one', r'\pagenumbering{roman}\ParallelSection{first-section}{First notes}{First notes}\ParallelText{one}{First explanation.}{First explanation.}\clearpage\ParallelSection{second-section}{Second section}{Second section}\ParallelText{two}{Precise detail.}{Precise detail.}'),
                ('companion-two', r'\ParallelSection{other-section}{Other notes}{Other notes}\ParallelText{three}{Independent source.}{Independent source.}')):
                (project/(name+'.tex')).write_text(r'\documentclass[10pt,twoside]{article}\usepackage{paralleltext}\begin{document}'+content+r'\end{document}')
                proc = build(project, name)
                if proc.returncode:
                    return {'case': ident, 'passed': False, 'error': 'Companion build failed', 'compile_exit': proc.returncode}
        if case.get('incompatible'):
            (project/'paralleltext.sty').write_text(r'\ProvidesPackage{paralleltext}\newcommand\ParallelTextAPIVersion{1}')
        proc = build(project)
        if case.get('error'):
            transcript = proc.stdout+proc.stderr
            return {'case': ident, 'passed': proc.returncode != 0 and case['error'].lower() in transcript.lower(),
                    'compile_exit': proc.returncode, 'expected_error': case['error']}
        if proc.returncode:
            return {'case': ident, 'passed': False, 'compile_exit': proc.returncode, 'error': proc.stdout[-1800:]}
        report = qa(project, 'main')
        if case.get('qa_error'):
            return {'case': ident, 'passed': not report['ok'] and any(case['qa_error'] in error for error in report['errors']),
                    'expected_qa_error': case['qa_error'], 'result': report}
        checks = {}
        with pymupdf.open(project/'main.pdf') as pdf:
            text = '\n'.join(page.get_text() for page in pdf)
            links = pdf_links(pdf, project)
            checks['local_links_resolve'] = any(link['action'] == '/GoTo' for link in links) and all(0 <= link.get('page', -1) < len(pdf)
                for link in links if link['action'] == '/GoTo')
            if case.get('registry'):
                checks['group_heading_once_per_side'] = text.count('Shared headword\n') == 2
                checks['both_distinct_meanings_visible'] = 'Meaning one' in text and 'Meaning two' in text
                checks['routes_interleaved_in_one_sequence'] = text.index('Alias route') < text.index('Shared headword') < text.index('Zebra route')
                checks['subentry_and_parent_named'] = 'Exact subentry' in text and 'Meaning one' in text
                if case.get('companions'):
                    checks['full_bodies_retained'] = all(token in text for token in ('PRIMARYDETAIL', 'SECONDMEANING', 'SUBENTRYDETAIL'))
                    remote = [link for link in links if link['action'] == '/GoToR']
                    checks['named_sources_remain_distinct'] = {link.get('file') for link in remote} == {'companion-one.pdf', 'companion-two.pdf'} and all(link['target_resolves'] for link in remote)
                    aux = (project/'main.aux').read_text()
                    labels = {match[1]: int(match[2]) for match in re.finditer(r'\\newlabel\{study:([^{}]+)\}\{\{[^{}]*\}\{(\d+)\}', aux)}
                    checks['subentry_destination_is_its_own_page'] = labels.get('precise', 0) > labels.get('alpha', 0) > 0
                    checks['subentry_link_targets_its_own_page'] = any(link.get('page') == labels.get('precise', 0)-1 for link in links if link['action'] == '/GoTo')
                    checks['roman_companion_folio_visible'] = bool(re.search(r'(?:page|p\.)\s+ii', text))
                else:
                    checks['index_omits_bodies'] = not any(token in text for token in ('PRIMARYDETAIL', 'SECONDMEANING', 'SUBENTRYDETAIL'))
                    checks['standalone_index_has_no_external_links'] = not any(link['action'] == '/GoToR' for link in links)
            if case.get('decision'):
                checks['typed_return_and_continuation_visible'] = 'After obtaining' in text and 'Required next step' in text
                checks['clarification_return_label_separates_target'] = bool(re.search(r'return\s+to\s+choose\b', text))
                checks['all_nodes_render_once_per_side'] = all(text.count(token) == 2 for token in ('CLARIFYACTION', 'METHODACTION', 'FINALACTION'))
        return {'case': ident, 'passed': report['ok'] and all(checks.values()), 'result': report, 'checks': checks}

    decision = r'''
\StudyDeclareQuestion{choose}{Choose a method?}{Choose a method?}
\StudyChoice{choose}{A}{Known input}{Known input}{method}
\StudyChoice{choose}{B}{Already checked}{Already checked}{finish}
\StudyUnknown{choose}{}{}{clarify}
\StudyDeclareLeaf{method}{Method}{Method}{\ParallelText{method-body}{METHODACTION}{METHODACTION}}
\StudyContinue{method}{finish}{Check the result}{Check the result}
\StudyDeclareClarification{clarify}{Get missing data}{Get missing data}{\ParallelText{clarify-body}{CLARIFYACTION}{CLARIFYACTION}}{choose}
\StudyDeclareLeaf{finish}{Finish}{Finish}{\ParallelText{finish-body}{FINALACTION}{FINALACTION}}
'''
    concept = r'\StudyDeclareConcept{one}{one}{One}{One}{}{\ParallelText{one-body}{Body.}{Body.}}'
    cases = [{'name': 'study-example-default'}]
    cases += [{'name': 'study-standalone-'+form, 'products': form} for form in FORMS]
    cases += [{'name': 'study-example-all', 'products': ' '.join(FORMS)},
              {'name': 'missing-dependency', 'missing': True, 'error': 'Set BILINGUAL_PDF_SKILL'},
              {'name': 'unknown-product', 'products': 'unknown', 'error': 'Unknown product'},
              {'name': 'empty-products', 'products': '', 'error': 'Select at least one product'},
              {'name': 'native-registry-quick', 'native': True, 'registry': True, 'companions': True,
               'preamble': '', 'body': r'\StudyPrintQuickReference'},
              {'name': 'native-registry-index', 'native': True, 'registry': True,
               'preamble': '', 'body': r'\StudyPrintKeywordIndex'},
              {'name': 'native-decision-types', 'native': True, 'decision': True,
               'preamble': decision, 'body': r'\StudyPrintDecisionTree{choose}'}]
    cases.append({'name': 'missing-declared-companion', 'native': True,
                  'preamble': r'\StudyDeclareNotesSource{lost}{Lost notes}{Lost notes}{missing}{missing.pdf}\StudyDeclareConcept[notes-source=lost]{entry}{entry}{Entry}{Entry}{section}{\ParallelText{body}{Content.}{Content.}}',
                  'body': r'\StudyPrintQuickReference', 'qa_error': 'undefined references'})
    invalid = [
        ('incompatible-dependency', '', '', 'Unsupported native renderer API'),
        ('duplicate-study-id', concept+concept, '', 'Duplicate study ID'),
        ('empty-sort-key', r'\StudyDeclareConcept{one}{}{One}{One}{}{Body}', '', 'Empty sort key'),
        ('invalid-study-id', r'\StudyDeclareConcept{1bad}{one}{One}{One}{}{Body}', '', 'Invalid study ID'),
        ('unknown-target', r'\StudyDeclareAlias{alias}{alias}{Alias}{Alias}{missing}', '', 'Unknown study target'),
        ('alias-chain', concept+r'\StudyDeclareAlias{alias}{alias}{Alias}{Alias}{one}\StudyDeclareAlias{chain}{chain}{Chain}{Chain}{alias}', '', 'is another route'),
        ('empty-route', r'\StudyDeclareRoute{route}{route}{Route}{Route}', '', 'has no targets'),
        ('different-group-sort', concept+r'\StudyDeclareRoute[lookup=one]{route}{other}{One}{One}\StudyRouteTarget{route}{one}{}{}', '', 'different sort keys'),
        ('missing-sense-context', concept+r'\StudyDeclareConcept[lookup=one]{two}{one}{One}{One}{}{Body}', '', 'Missing left sense label'),
        ('unknown-subentry-parent', r'\StudyDeclareSubentry{sub}{missing}{Sub}{Sub}{}', '', 'unknown parent'),
        ('missing-unknown-route', decision.replace(r'\StudyUnknown{choose}{}{}{clarify}', ''), r'\StudyPrintDecisionTree{choose}', 'has no unknown route'),
        ('duplicate-choice', decision+r'\StudyChoice{choose}{A}{Again}{Again}{finish}', '', 'Duplicate choice'),
        ('forward-cycle', decision.replace(r'\StudyContinue{method}{finish}', r'\StudyContinue{method}{choose}'), r'\StudyPrintDecisionTree{choose}', 'Decision cycle'),
        ('invalid-return-target', decision.replace('{choose}\n'+r'\StudyDeclareLeaf', '{finish}\n'+r'\StudyDeclareLeaf'), r'\StudyPrintDecisionTree{choose}', 'returns to a non-question'),
        ('empty-method', r'\StudyDeclareLeaf{method}{Method}{Method}{}', '', 'has no method'),
        ('unknown-decision-target', decision.replace(r'{Known input}{Known input}{method}', r'{Known input}{Known input}{missing}'), r'\StudyPrintDecisionTree{choose}', 'Unknown decision target'),
    ]
    cases += [{'name': name, 'native': True, 'preamble': preamble, 'body': body, 'error': error,
               'incompatible': name == 'incompatible-dependency'} for name, preamble, body, error in invalid]
    return execute_matrix(cases, lambda case: native(case) if case.get('native') else example(case),
                          work, args, 'study', name=lambda case: case['name'])

if __name__ == '__main__':
    raise SystemExit(main())
