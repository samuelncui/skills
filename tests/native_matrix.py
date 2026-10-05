#!/usr/bin/env python3
"""Build ordinary authored LaTeX in isolated projects; no Python body generation."""
import argparse
from matrix_support import add_matrix_arguments, initialize_output, execute_matrix, run_command, repeat_text, first_sentence
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--structured-matrix', type=Path)
add_matrix_arguments(parser)
args = parser.parse_args()
work = initialize_output(args.output,args.resume)
for name in ('bilingual-pdf',):
    shutil.copytree(ROOT/'skills'/name, work/name, ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
style = work/'bilingual-pdf/assets/paralleltext.sty'
qa_script = work/'bilingual-pdf/scripts/bilingual_pdf.py'
def stage_assets(project):
    for asset in (work/'bilingual-pdf/assets').iterdir():
        if asset.suffix in ('.sty','.tex'):
            shutil.copyfile(asset,project/asset.name)
    # Pixel comparisons need the same raster inputs as structured export:
    # opaque RGB samples without density/ancillary metadata. Installed-example
    # cases above keep and validate the untouched original shared image pool.
    from PIL import Image
    for asset in (work/'bilingual-pdf/examples/shared').glob('*.png'):
        with Image.open(asset) as original:
            rgba=original.convert('RGBA')
            background=Image.new('RGBA',original.size,'white')
            background.alpha_composite(rgba)
            background.convert('RGB').save(project/asset.name)
    main=project/'main.tex'
    main.write_text(main.read_text().replace(r'\graphicspath{{../shared/}}',r'\graphicspath{{./}}'))

def minimal_project(project):
    project.mkdir(exist_ok=True)
    shutil.copyfile(style,project/'paralleltext.sty')
    (project/'main.tex').write_text('\\documentclass[10pt,twoside]{article}\n\\usepackage{paralleltext}\n\\input{languages.tex}\n\\begin{document}\n\\input{content.tex}\n\\end{document}\n')
    shutil.copyfile(work/'bilingual-pdf/examples/en-zh-Hans/languages.tex',project/'languages.tex')
    (project/'content.tex').write_text(r'\ParallelText{first}{A minimal authored document.}{一个简单的原生文档。}')

BUILD = ['latexmk', '-norc', '-xelatex', '-interaction=nonstopmode', '-halt-on-error', '-latexoption=-no-shell-escape']

def check_pdf(path, paired=True, covers=False):
    command = [sys.executable, str(qa_script), 'validate', str(path)]
    if paired: command.append('--paired')
    if covers: command.append('--covers')
    proc = run_command(command, cwd=path.parent, capture_output=True, text=True, timeout=60)
    return proc.returncode, json.loads(proc.stdout)

def run_build(case):
    name, project, expected, diagnostic, paired, covers = case
    proc = run_command(BUILD+['main.tex'], cwd=project, capture_output=True, text=True, timeout=105)
    (project/'build.stdout').write_text(proc.stdout+proc.stderr)
    if expected == 'compile-error':
        ok = proc.returncode != 0 and diagnostic in (proc.stdout+proc.stderr)
        return {'case': name, 'passed': ok, 'expected': diagnostic, 'compile_exit': proc.returncode}
    if proc.returncode:
        return {'case': name, 'passed': False, 'compile_exit': proc.returncode, 'error': proc.stdout[-2500:]}
    code, report = check_pdf(project/'main.pdf', paired, covers)
    ok = code == (4 if expected == 'qa-error' else 0)
    if name.startswith('installed-') and ok:
        recorder=(project/'main.fls').read_text()
        inputs=[(project/line[6:]).resolve() for line in recorder.splitlines() if line.startswith('INPUT ')]
        report['installed_skill_assets_without_example_copies']=not (project/'paralleltext.sty').exists() and style.resolve() in inputs
        report['no_source_checkout_inputs']=not any(path.is_relative_to(ROOT/'skills') for path in inputs)
        ok=ok and report['installed_skill_assets_without_example_copies'] and report['no_source_checkout_inputs']
    if expected == 'qa-error': ok = ok and any(diagnostic in e for e in report['errors'])
    if name == 'labels-and-equations' and ok:
        aux = (project/'main.aux').read_text()
        ok = bool(re.search(r'\\newlabel\{eq:first\}\{\{1\}', aux) and re.search(r'\\newlabel\{eq:second\}\{\{2\}', aux))
        report['single_equation_counter_steps'] = ok
    if name == 'arabic-equations' and ok:
        import pymupdf
        with pymupdf.open(project/'main.pdf') as pdf:
            plus=[c['origin'] for block in pdf[0].get_text('rawdict')['blocks'] if block['type']==0 for line in block['lines'] for span in line['spans'] for c in span['chars'] if c['c']=='+']
        ok=len(plus)==2 and abs(plus[0][1]-plus[1][1])<0.05
        report['shared_equation_baselines_aligned']=ok
    if name == 'right-booklet' and ok:
        import pymupdf
        with pymupdf.open(project/'main.pdf') as pdf:
            ok = 'English cover' not in ''.join(p.get_text() for p in pdf)
        report['unselected_cover_language_absent'] = ok
    if name.startswith('flow-') and ok:
        aux=(project/'main.aux').read_text()
        labels={m[1]:int(m[2]) for m in re.finditer(r'\\newlabel\{pt-internal:([^{}]+)\}\{\{[^{}]*\}\{(\d+)\}',aux)}
        crossed=all(labels.get('long-prose-'+side+'-finish',0)>labels.get('long-prose-'+side,0) for side in ['L','R'])
        report['both_paragraphs_cross_pages']=crossed;ok=ok and crossed
    if name.startswith('article-') and ok:
        from layout_checks import quote_geometry, article_features
        languages={'en-fr':['en','fr'],'en-zh-Hans':['en','zh-Hans'],'en-ar':['en','ar'],'en-he':['en','he'],'zh-Hans-ja':['zh-Hans','ja']}[name[8:]]
        quote=quote_geometry(project/'main.pdf',languages)
        report['quote_geometry']=quote
        features=article_features(project/'main.pdf');report['article_features']=features
        ok=ok and quote['ok'] and features['ok']
    if (name.startswith('article-') or name.startswith('flow-') or name.startswith('shared-photo-')) and args.structured_matrix and ok:
        import pymupdf
        original = args.structured_matrix/((name[8:]+'-bilingual') if name.startswith('article-') else name)/'document.pdf'
        with pymupdf.open(original) as a, pymupdf.open(project/'main.pdf') as b:
            equal = len(a) == len(b) and all(a[i].get_pixmap(alpha=False).samples == b[i].get_pixmap(alpha=False).samples for i in range(len(a)))
        ok = ok and equal
        report['native_and_structured_pixels_identical'] = equal
        report['comparison_raster_inputs'] = 'Matched opaque RGB pixels without ancillary density metadata; installed-original cases are separate'
    return {'case': name, 'passed': ok, 'compile_exit': proc.returncode, 'qa_exit': code, 'result': report}

cases = []
for name in ('en-fr', 'en-zh-Hans', 'en-ar', 'en-he', 'zh-Hans-ja'):
    cases.append(('installed-'+name,work/'bilingual-pdf/examples'/name,'ok','',True,False))
    project = work/('article-'+name)
    shutil.copytree(work/'bilingual-pdf/examples'/name, project, ignore=shutil.ignore_patterns('*.pdf', '*preview.png'),dirs_exist_ok=True)
    stage_assets(project)
    cases.append(('article-'+name, project, 'ok', '', True, False))
# Native helpers are exercised directly, with no JSON/Python renderer at build time.
sys.path.insert(0,str(work/'bilingual-pdf/scripts'))
from bilingual_pdf import escape, language_text
for name in ('en-fr','en-zh-Hans','en-ar','en-he','zh-Hans-ja'):
    data=json.loads((work/'bilingual-pdf/examples'/name/'source.json').read_text())
    passage=next(b['text'] for b in data['blocks'] if b['id']=='continuing-prose')
    title='\\ParallelTitle{'+escape(data['title'][0])+'}{'+escape(data['title'][1])+'}\n'
    for prefix in ('flow-','shared-photo-'):
        project=work/(prefix+name);shutil.copytree(work/'bilingual-pdf/examples'/name,project,dirs_exist_ok=True);stage_assets(project)
        if prefix=='flow-':
            body='\\ParallelProse{long-prose}{'+language_text(repeat_text(passage[0]),data['languages'][0])+'}{'+language_text(repeat_text(passage[1]),data['languages'][1])+'}\n\\ParallelParagraph{after-flow}{'+escape(first_sentence(passage[0]))+'}{'+escape(first_sentence(passage[1]))+'}'
        else:
            captions={'en':'Shared photograph.','fr':'Photographie partagée.','zh-Hans':'共用照片。','ar':'صورة مشتركة.','ja':'共有写真。','he':'תרשים משותף.'}
            (project/'images').mkdir(exist_ok=True);shutil.copyfile(project/'layout-anatomy.png',project/'images/layout-anatomy.png')
            body='\\ParallelWideFigure{photo}{images/layout-anatomy.png}{'+captions[data['languages'][0]]+'}{'+captions[data['languages'][1]]+'}\n\\ParallelParagraph{after-photo}{'+escape(first_sentence(passage[0]))+'}{'+escape(first_sentence(passage[1]))+'}'
        (project/'content.tex').write_text(title+body+'\n')
        cases.append((prefix+name,project,'ok','',True,False))

for name, body, expected, diagnostic, paired, covers in [
    ('minimal-authoring', None, 'ok', '', True, False),
    ('labels-and-equations', r'\ParallelText{foo}{First.}{第一段。}\ParallelText{foo-L}{Second.}{第二段。}\ParallelEquation{eq:first}{a+b=c}\ParallelEquation{eq:second}{x=y}\ParallelText{links}{\ParallelReference{foo}{First}; \ParallelReference{foo-L}{second}; equations \ref{eq:first}, \ref{eq:second}.}{\ParallelReference{foo}{第一段}；\ParallelReference{foo-L}{第二段}；公式 \ref{eq:first}、\ref{eq:second}。}', 'ok', '', True, False),
    ('duplicate-id', r'\ParallelText{same}{One.}{一。}\ParallelText{same}{Two.}{二。}', 'compile-error', 'Duplicate paired ID', True, False),
    ('reserved-id', r'\ParallelText{pt-internal:bad}{One.}{一。}', 'compile-error', 'Reserved paired ID namespace', True, False),
    ('oversize-native', '\\ParallelText{long}{'+'Long paragraph. '*3000+'}{'+'很长的段落。'*3000+'}', 'compile-error', 'PAIR TOO TALL', True, False),
    ('missing-glyph-native', r'\ParallelText{glyph}{A unicorn 🦄.}{独角兽。}', 'qa-error', 'Missing character:', True, False),
    ('right-booklet', r'\ParallelFrontCover{English cover}{中文封面}\ParallelText{one}{English body.}{中文正文。}\ParallelBackCover{English cover}{中文封底}', 'ok', '', False, True),
]:
    project = work/name
    minimal_project(project)
    if body is not None: (project/'content.tex').write_text(body+'\n')
    if name == 'right-booklet':
        p = project/'languages.tex'; p.write_text(p.read_text().replace('{paired}', '{right}').replace('mode=paired','mode=right'))
    cases.append((name, project, expected, diagnostic, paired, covers))
# A shared numbered expression must also work in a native RTL language context.
project = work/'arabic-equations'
minimal_project(project)
(project/'languages.tex').write_text((work/'bilingual-pdf/examples/en-ar/languages.tex').read_text())
(project/'content.tex').write_text(r'\ParallelEquation{sum}{a+b=c}\ParallelText{explanation}{A shared equation.}{معادلة مشتركة.}'+'\n')
cases.append(('arabic-equations', project, 'ok', '', True, False))

raise SystemExit(execute_matrix(cases,run_build,work,args,'native'))
