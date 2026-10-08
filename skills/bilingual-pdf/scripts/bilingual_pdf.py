#!/usr/bin/env python3
"""Render validated paired content with the bundled LaTeX semantic-block template."""
import argparse
import hashlib
import json
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER_API_VERSION = 1
PROFILES = {
    'en': {'font': 'Latin Modern Roman', 'direction': 'ltr', 'locale': 'en'},
    'fr': {'font': 'Latin Modern Roman', 'direction': 'ltr', 'locale': 'fr'},
    'zh-Hans': {'font': 'Noto Serif CJK SC', 'direction': 'ltr', 'locale': 'zh'},
    'zh-Hant': {'font': 'Noto Serif CJK TC', 'direction': 'ltr', 'locale': 'zh'},
    'ja': {'font': 'Noto Serif CJK JP', 'direction': 'ltr', 'locale': 'ja'},
    'ar': {'font': 'Noto Naskh Arabic', 'direction': 'rtl', 'locale': 'ar'},
    'he': {'font': 'DejaVu Sans', 'direction': 'rtl', 'locale': 'he'},
}
MATH_COMMANDS = {'frac','sqrt','sum','prod','int','infty','alpha','beta','gamma','theta','sigma','mu','pi','Delta','times','cdot','pm','leq','geq','neq','approx','log','ln','exp','sin','cos','left','right','mathrm','mathbf','text','quad','qquad','overline','hat','bar'}

class InputError(ValueError): pass

def figure_images(block):
    """One shared image or an ordered pair of localized column images."""
    image=block.get('image')
    images=image if isinstance(image,list) else [image]
    if isinstance(image,list) and (len(image)!=2 or block.get('placement')=='shared'):
        raise InputError('Paired figures require two image paths; shared figures require one')
    for path in images:
        if not isinstance(path,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]*\.(?:png|jpg|jpeg)',path) or '..' in Path(path).parts:
            raise InputError('Figure image must be a relative PNG/JPEG path without traversal')
    return images

def resolve_image(input_path,relative,asset_root=None):
    """Resolve only inside the explicitly selected asset root, including symlinks."""
    figure_images({'image':relative})
    base=Path(asset_root).resolve() if asset_root is not None else Path(input_path).resolve().parent
    if not base.is_dir():raise InputError('Asset root must be an existing directory')
    source=(base/relative).resolve()
    if not source.is_relative_to(base):raise InputError('Figure escapes the asset root')
    if not source.is_file():raise InputError('Missing figure inside asset root: '+relative)
    return source

def escape(text):
    substitutions = {'\\':r'\textbackslash{}','{':r'\{','}':r'\}','$':r'\$','&':r'\&','#':r'\#','%':r'\%','_':r'\_','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(substitutions.get(c,c) for c in text)

def text_value(value):
    if isinstance(value,dict):
        if set(value)!={'runs'} or not isinstance(value['runs'],list) or not value['runs']:raise InputError('Rich text requires nonempty runs')
        for run in value['runs']:
            if not isinstance(run,dict) or set(run)!={'text','direction'} or not isinstance(run['direction'],str) or run['direction'] not in {'ltr','rtl'} or not isinstance(run['text'],str):raise InputError('Each run requires text and ltr/rtl direction')
            text_value(run['text'])
        return value
    if not isinstance(value,str) or not value.strip(): raise InputError('Nonempty text is required')
    if any(ord(c)<32 and c not in '\n\t' for c in value): raise InputError('Control character in text')
    if any(c in value for c in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069'): raise InputError('Supply logical text without embedded directional controls')
    return value

def validate(data):
    if not isinstance(data,dict): raise InputError('Document must be an object')
    languages=data.get('languages')
    if not isinstance(languages,list) or len(languages)!=2 or any(not isinstance(x,str) or x not in PROFILES for x in languages): raise InputError('Exactly two supported language profile IDs are required')
    if set(languages)=={'zh-Hans','zh-Hant'}:raise InputError('Mixed simplified/traditional Chinese profiles need a separately tested native language configuration')
    title=data.get('title')
    if not isinstance(title,list) or len(title)!=2: raise InputError('title must contain two strings')
    for x in title:
        if not isinstance(x,str):raise InputError('Titles must be plain strings')
        text_value(x)
    blocks=data.get('blocks')
    if not isinstance(blocks,list) or not blocks: raise InputError('blocks must be a nonempty list')
    ids=set()
    for b in blocks:
        if not isinstance(b,dict):raise InputError('Block must be an object')
        ident=b.get('id','')
        if not isinstance(ident,str) or not re.fullmatch(r'[a-z][a-z0-9.-]{0,79}',ident) or ident in ids:raise InputError('Block IDs must be unique lowercase identifiers')
        if ident=='pt-title':raise InputError('pt-title is reserved for the document title')
        ids.add(ident)
        if not isinstance(b.get('break_before',False),bool):raise InputError('break_before must be boolean')
        kind=b.get('kind','paragraph')
        if not isinstance(kind,str) or kind not in {'paragraph','heading','list','equation','reference','figure','quote','table'}:raise InputError('Unsupported block kind: '+str(kind))
        if 'flow' in b and (kind!='paragraph' or b['flow'] not in ('atomic','keep','breakable')):raise InputError('flow is keep, breakable or atomic (keep alias), for paragraph blocks only')
        if 'placement' in b and (kind!='figure' or b['placement'] not in ('paired','shared')):raise InputError('placement is paired or shared, for figures only')
        if 'caption_prefix' in b and (kind!='figure' or b['caption_prefix'] not in ('automatic','none')):raise InputError('caption_prefix is automatic or none, for figures only')
        pair=b.get('text',[]) if kind=='table' else b.get('text')
        if kind=='table' and 'text' not in b:pass
        elif not isinstance(pair,list) or len(pair)!=2:raise InputError('Each block needs exactly two paired texts')
        if kind=='list':
            if any(not isinstance(x,list) or not x for x in pair):raise InputError('List block needs two nonempty lists')
            if len(pair[0])!=len(pair[1]):raise InputError('List items must be aligned')
            for side in pair:
                for x in side:text_value(x)
        else:
            for x in pair:text_value(x)
        for index, value in enumerate(pair):
            values=value if kind=='list' else [value]
            if PROFILES[languages[index]]['direction']!='rtl' and any(isinstance(x,dict) for x in values):raise InputError('Explicit directional runs currently require an RTL paragraph')
        if 'chunks' in b:
            if kind!='paragraph' or b.get('flow','breakable')!='breakable':
                raise InputError('chunks require a breakable paragraph')
            chunks=b['chunks']
            if not isinstance(chunks,list) or not chunks:raise InputError('chunks must be a nonempty list')
            for chunk in chunks:
                if not isinstance(chunk,dict) or set(chunk)!={'id','text'}:raise InputError('Each chunk requires exactly id and text')
                cid=chunk['id']
                if not isinstance(cid,str) or not re.fullmatch(r'[a-z][a-z0-9.-]{0,79}',cid) or cid=='pt-title':raise InputError('Chunk IDs must be lowercase identifiers')
                texts=chunk['text']
                if not isinstance(texts,list) or len(texts)!=2 or any(not isinstance(x,str) for x in texts):raise InputError('Chunk text needs exactly two plain strings')
                for x in texts:text_value(x)
            if any(not isinstance(x,str) for x in pair) or [ ''.join(c['text'][i] for c in chunks) for i in range(2)]!=pair:
                raise InputError('Chunk text must concatenate exactly to its parent text; preserve all spaces')
        if kind=='figure':
            figure_images(b)
        if kind=='reference':
            target=b.get('target')
            if not isinstance(target,str) or not re.fullmatch(r'[a-z][a-z0-9.-]{0,79}',target):raise InputError('Reference target must be an identifier')
            if 'file' in b:
                if not isinstance(b['file'],str) or not re.fullmatch(r'(?:\.\./)?[a-z][a-z0-9/_-]*\.pdf',b['file']):raise InputError('Reference file must be a relative PDF path')
                if isinstance(b.get('page'),bool) or not isinstance(b.get('page'),int) or b['page']<1:raise InputError('Reference page must be positive')
                if 'page_label' in b:
                    if not isinstance(b['page_label'],str):raise InputError('Reference page_label must be text')
                    text_value(b['page_label'])
        if kind=='equation':
            if not isinstance(b.get('math'),str):raise InputError('Math must be a string')
            math=text_value(b.get('math'))
            if '^^' in math:raise InputError('TeX character-code escapes are forbidden')
            if len(math)>1000 or re.search(r'[^A-Za-z0-9\\{}^_+\-*/=()., :<>|!\[\]]',math):raise InputError('Math contains unsupported characters')
            if set(re.findall(r'\\([A-Za-z]+)',math))-MATH_COMMANDS:raise InputError('Math command outside the safe allowlist')
            if re.search(r'\\[^A-Za-z]',math):raise InputError('Math control symbols are not supported')
    for b in blocks:
        if b.get('kind')=='table':
            h=b.get('headers');rows=b.get('rows')
            if not isinstance(h,list) or len(h)!=2 or any(not isinstance(x,list) or not 1<=len(x)<=5 for x in h) or len(h[0])!=len(h[1]):raise InputError('Table needs two matching header lists, one to five columns')
            if not isinstance(rows,list) or len(rows)!=2 or any(not isinstance(x,list) or not x for x in rows) or len(rows[0])!=len(rows[1]):raise InputError('Table rows must align across languages')
            for side in range(2):
                for cell in h[side]:
                    text_value(cell)
                    if isinstance(cell,dict) and PROFILES[languages[side]]['direction']!='rtl':raise InputError('Directional table cells require an RTL language')
                for row in rows[side]:
                    if not isinstance(row,list) or len(row)!=len(h[side]) or any(not isinstance(x,(str,dict)) for x in row):raise InputError('Table row has wrong columns or non-text cell')
                    for cell in row:
                        text_value(cell)
                        if isinstance(cell,dict) and PROFILES[languages[side]]['direction']!='rtl':raise InputError('Directional table cells require an RTL language')
        if b.get('kind')=='reference' and 'file' not in b and b['target'] not in ids:raise InputError('Unresolved local reference: '+b['target'])
    generated=[]
    for b in blocks:
        if 'chunks' in b:generated.extend(c['id'] for c in b['chunks'])
        if b.get('kind')=='equation':generated.append(b['id']+'.formula')
        if b.get('kind')=='figure' and b.get('placement')=='shared':generated.append(b['id']+'.caption')
        if b.get('kind')=='table':
            generated.extend(b['id']+'.row-'+str(i) for i in range(len(b['rows'][0])+1))
            if 'text' in b:generated.append(b['id']+'.caption')
        if b.get('kind')=='list':generated.extend(b['id']+'.item-'+str(i+1) for i in range(len(b['text'][0])))
    if any(x in ids for x in generated) or len(generated)!=len(set(generated)):raise InputError('Generated list IDs collide with explicit block IDs')
    settings=data.get('layout',{})
    if not isinstance(settings,dict):raise InputError('layout must be an object')
    allowed={'font_size','leading','margin_mm','inner_mm','outer_mm','binding_mm','top_mm','bottom_mm','gap_mm','paper','covers','twoside','profile','divider','page_numbers','paragraph_flow'}
    if set(settings)-allowed:raise InputError('Unknown layout option: '+', '.join(sorted(set(settings)-allowed)))
    if settings.get('paragraph_flow','keep') not in ('keep','breakable'):raise InputError('paragraph_flow must be keep or breakable')
    for key,lo,hi in [('font_size',9,14),('leading',9,24),('margin_mm',8,45),('inner_mm',8,45),('outer_mm',8,45),('binding_mm',0,20),('top_mm',10,40),('bottom_mm',10,40),('gap_mm',4,16)]:
        if key in settings:
            value=settings[key]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not lo<=value<=hi:raise InputError('Invalid layout '+key)
    effective_size=settings.get('font_size',11 if settings.get('profile')=='reading' else 9)
    if settings.get('leading',effective_size*1.2)<effective_size:raise InputError('leading must be at least font_size')
    if settings.get('paper','a4') not in ('a4','letter','a5','legal'):raise InputError('paper must be a4, letter, a5 or legal')
    if settings.get('profile','article') not in ('article','bound','reading'):raise InputError('Unknown layout profile')
    for key in ('covers','twoside'):
        if key in settings and not isinstance(settings[key],bool):raise InputError(key+' must be boolean')
    divider=settings.get('divider',{})
    if not isinstance(divider,dict) or set(divider)-{'enabled','color','width_pt','style'}:raise InputError('Invalid divider options')
    if 'enabled' in divider and not isinstance(divider['enabled'],bool):raise InputError('divider.enabled must be boolean')
    if 'color' in divider and (not isinstance(divider['color'],str) or not re.fullmatch('[0-9A-Fa-f]{6}',divider['color'])):raise InputError('divider.color must be six HTML hex digits')
    if 'width_pt' in divider and (isinstance(divider['width_pt'],bool) or not isinstance(divider['width_pt'],(int,float)) or not 0<divider['width_pt']<=3):raise InputError('Invalid divider.width_pt')
    if divider.get('style','solid') not in ('solid','dashed','dotted','densely dashed','densely dotted'):raise InputError('Invalid divider.style')
    folio=settings.get('page_numbers',{})
    if not isinstance(folio,dict) or set(folio)-{'position','numbering','prefix','suffix'}:raise InputError('Invalid page_numbers options')
    positions={'none'}|{where+'-'+align for where in ('header','footer') for align in ('outer','inner','left','center','right')}
    if not isinstance(folio.get('position','footer-outer'),str) or folio.get('position','footer-outer') not in positions:raise InputError('Invalid page_numbers.position')
    if folio.get('numbering','arabic') not in ('arabic','roman','Roman','alph','Alph','gobble'):raise InputError('Invalid page_numbers.numbering')
    for key in ('prefix','suffix'):
        if key in folio and (not isinstance(folio[key],str) or len(folio[key])>80 or any(ord(c)<32 for c in folio[key])):raise InputError('Invalid page_numbers.'+key)
    return data

def preflight(data):
    missing_python=[p for m,p in [('pymupdf','PyMuPDF'),('PIL','Pillow'),('fontTools','fonttools')] if importlib.util.find_spec(m) is None]
    if missing_python:return {'ok':False,'missing_python_packages':missing_python}
    required=['xelatex','latexmk','fc-match','kpsewhich']
    missing=[x for x in required if not shutil.which(x)]
    if missing:return {'ok':False,'missing_tools':missing}
    package_missing=[]
    packages=['polyglossia.sty','paracol.sty','ragged2e.sty','fontspec.sty','unicode-math.sty','geometry.sty','needspace.sty','tikz.sty','fancyhdr.sty','zref-savepos.sty','amsmath.sty','booktabs.sty','array.sty','tabularx.sty','xcolor.sty','graphicx.sty','enumitem.sty','hyperref.sty','bookmark.sty']
    if any(PROFILES[l]['direction']=='rtl' for l in data['languages']):packages.append('bidi.sty')
    if 'fr' in data['languages']:packages.append('loadhyph-fr.tex')
    # kpsewhich accepts multiple filenames; retain an explicit result for every
    # required basename, including partial-success/missing-package responses.
    q=subprocess.run(['kpsewhich',*packages],capture_output=True,text=True)
    found={Path(line).name for line in q.stdout.splitlines() if line.strip()}
    package_missing=[package for package in packages if package not in found]
    if q.returncode and not package_missing:
        return {'ok':False,'package_lookup_error':'kpsewhich failed despite returning every requested path'}
    fonts=[]
    font_requests=[(language,PROFILES[language]['font']) for language in data['languages']]
    for language in data['languages']:
        body_font=PROFILES[language]['font']
        heading_font=body_font.replace('Serif','Sans') if language.startswith('zh') or language in ('ja','he') else ('Latin Modern Sans' if language in ('en','fr') else body_font)
        font_requests.append((language+':headings',heading_font))
    font_requests += [('math','Latin Modern Math'),('marker','Latin Modern Roman')]
    for language,wanted in font_requests:
        q=subprocess.run(['fc-match','-f','%{family}\n%{file}\n%{index}\n',wanted],capture_output=True,text=True)
        lines=q.stdout.strip().splitlines()
        exact=bool(lines and wanted in lines[0].split(','))
        missing_glyphs=[]
        if exact and language!='math':
            from fontTools.ttLib import TTFont
            font=TTFont(lines[1],fontNumber=int(lines[2]) & 65535,lazy=True)
            cmap=font.getBestCmap();font.close()
            indices=[i for i,l in enumerate(data['languages']) if l==language.split(':')[0]]
            def chars(value,latin=False):
                if isinstance(value,dict):return ''.join(run['text'] for run in value['runs'] if (run['direction']=='ltr')==latin)
                if isinstance(value,list):return ''.join(chars(x,latin) for x in value)
                return '' if latin else value
            if language=='marker':sample='•'+''.join(chars(v,True) for b in data['blocks'] for v in b.get('text',[]))+''.join(chars(b[field],True) for b in data['blocks'] if b.get('kind')=='table' for field in ('headers','rows'))
            else:
                def block_chars(b,i):
                    if ':headings' in language:return chars(b['text'][i]) if b.get('kind')=='heading' else ''
                    value=chars(b['text'][i]) if 'text' in b else ''
                    if b.get('kind')=='table':value+=chars(b['headers'][i])+chars(b['rows'][i])
                    return value
                sample=''.join(data['title'][i]+''.join(block_chars(b,i) for b in data['blocks']) for i in indices)
            missing_glyphs=sorted({f'U+{ord(c):04X}' for c in sample if not c.isspace() and ord(c) not in cmap})
        fonts.append({'language':language,'requested':wanted,'matched':lines[0] if lines else '', 'available':exact,'missing_glyphs':missing_glyphs})
    return {'ok':not package_missing and all(f['available'] and not f['missing_glyphs'] for f in fonts),'missing_packages':package_missing,'fonts':fonts,'engine':subprocess.run(['xelatex','--version'],capture_output=True,text=True).stdout.splitlines()[0]}

NATIVE_LANGUAGES = {'en':'english','fr':'french','zh-Hans':'chinese','zh-Hant':'chinese','ja':'japanese','ar':'arabic','he':'hebrew'}

def language_text(text,language,prefix='',suffix=''):
    if isinstance(text,dict):
        value=''.join((r'\textenglish{'+escape(run['text'])+'}' if run['direction']=='ltr' else escape(run['text'])) for run in text['runs'])
    else:value=escape(text).replace('\n',' ')
    return prefix+value+suffix



# Additive Python API for explicitly source-bound native authoring. This does not
# change the article JSON schema or the study graph-v1 rich-run contract.
BOUND_TEXT_API_VERSION = 1
_SCIENTIFIC_SYMBOLS = {
    '←': r'\ensuremath{\leftarrow}\allowbreak{}',
    '→': r'\ensuremath{\rightarrow}\allowbreak{}',
    '∂': r'\ensuremath{\partial}', '∝': r'\ensuremath{\propto}',
    '≈': r'\ensuremath{\approx}', '⊙': r'\ensuremath{\odot}',
    '≤': r'\ensuremath{\leq}', '≥': r'\ensuremath{\geq}',
    '≠': r'\ensuremath{\ne}',
}


def render_bound_text(text, *, runs=None, references=(), language='en',
                      text_policy='literal', source_sha256=None,
                      trusted_native=False):
    """Render exact-source text/math spans and pre-resolved native references.

    Runs reconstruct the whole text: {kind: text, source: ...} or
    {kind: math, source: ..., tex: ...}. References contain start/end/text/tex.
    Offsets count Unicode code points. Native reference fragments and unrestricted
    math require explicit trusted_native=True AND a matching source_sha256.
    Hash binding detects drift; it does not make native TeX safe.
    """
    if not isinstance(text, str):
        raise InputError('Bound source must be a string')
    text_value('text' + text)  # Permit empty/whitespace-only source spans.
    if language not in PROFILES:
        raise InputError('Unsupported bound-text language')
    if text_policy not in ('literal', 'scientific-breaks'):
        raise InputError('Unknown bound-text policy')
    digest = hashlib.sha256(text.encode()).hexdigest()
    if source_sha256 is not None and source_sha256 != digest:
        raise InputError('Bound source hash drift')
    if trusted_native and source_sha256 != digest:
        raise InputError('Trusted native fragments require an exact source hash')
    if not isinstance(references, (list, tuple)):
        raise InputError('References must be an ordered sequence')
    events = []
    if runs is not None:
        if not isinstance(runs, list):
            raise InputError('Bound runs must be a list')
        offset = 0
        for run in runs:
            if not isinstance(run, dict) or run.get('kind') not in ('text', 'math'):
                raise InputError('Unknown bound run kind')
            fields = {'kind', 'source', 'tex'} if run['kind'] == 'math' else {'kind', 'source'}
            if set(run) != fields or not isinstance(run['source'], str) or not run['source']:
                raise InputError('Invalid bound run fields')
            end = offset + len(run['source'])
            if text[offset:end] != run['source']:
                raise InputError('Bound runs do not reconstruct source')
            if run['kind'] == 'math':
                tex = run['tex']
                if not isinstance(tex, str) or not tex:
                    raise InputError('Bound mathematics must be nonempty TeX')
                if not trusted_native:
                    validate({'languages': ['en', 'en'], 'title': ['Math', 'Math'],
                              'blocks': [{'id': 'formula', 'kind': 'equation',
                                          'text': ['Formula', 'Formula'], 'math': tex}]})
                    depth = 0
                    for char in tex:
                        depth += (char == '{') - (char == '}')
                        if depth < 0:
                            raise InputError('Unbalanced math braces')
                    if depth:
                        raise InputError('Unbalanced math braces')
                events.append((offset, end, r'\(' + tex + r'\)'))
            offset = end
        if offset != len(text):
            raise InputError('Bound runs do not reconstruct source')
    for reference in references:
        if not trusted_native:
            raise InputError('Resolved reference TeX requires trusted_native and source hash')
        if not isinstance(reference, dict) or set(reference) != {'start', 'end', 'text', 'tex'}:
            raise InputError('Invalid bound reference fields')
        start, end = reference['start'], reference['end']
        if (type(start) is not int or type(end) is not int or
                not 0 <= start < end <= len(text) or text[start:end] != reference['text']):
            raise InputError('Bound reference span drift')
        if not isinstance(reference['tex'], str) or not reference['tex']:
            raise InputError('Resolved reference must be nonempty native TeX')
        events.append((start, end, reference['tex']))
    events.sort(key=lambda event: (event[0], event[1]))
    if any(left[1] > right[0] for left, right in zip(events, events[1:])):
        raise InputError('Bound reference/mathematical spans overlap')
    def literal(value):
        if text_policy == 'literal':
            return language_text(value, language)
        return ''.join(_SCIENTIFIC_SYMBOLS.get(char, escape(char)) +
                       (r'\allowbreak{}' if char in '/,;' else '') for char in value)
    output, offset = [], 0
    for start, end, tex in events:
        output.extend((literal(text[offset:start]), tex))
        offset = end
    output.append(literal(text[offset:]))
    return ''.join(output)


def content(b,index,language):
    if b.get('kind')=='table' and 'text' not in b:return ''
    value=b['text'][index];kind=b.get('kind','paragraph')
    if kind=='list':
        return r'\begin{itemize}'+''.join(r'\item '+language_text(x,language) for x in value)+r'\end{itemize}'
    value=language_text(value,language)
    if kind=='reference':
        if 'file' in b:
            return r'\href[page='+str(b['page'])+']{'+b['file']+'}{'+value+r' \textenglish{(p.\,'+escape(b.get('page_label',str(b['page'])))+')}}'
        return r'\ParallelReference{'+b['target']+'}{'+value+'}'
    if kind=='quote':return r'\begin{quote}'+value+r'\end{quote}'
    return value

def tex_parts(data,mode,*,stem="document",image_names=None):
    files=project_filenames(stem)
    image_names=image_names or {}
    settings=data.get('layout',{});size=settings.get('font_size',9);margin=settings.get('margin_mm',18);gap=settings.get('gap_mm',6)
    languages=data['languages'];names=[NATIVE_LANGUAGES[x] for x in languages]
    locale=[]
    for language in dict.fromkeys(languages):
        name=NATIVE_LANGUAGES[language]
        if name!='english':
            options='[numerals=maghrib]' if language=='ar' else ('[variant=traditional]' if language=='zh-Hant' else '')
            locale.append(r'\setotherlanguage'+options+'{'+name+'}')
        options={'ar':'[Script=Arabic]','he':'[Script=Hebrew]'}.get(language,'')
        locale.append(r'\newfontfamily'+chr(92)+name+'font'+options+'{'+PROFILES[language]['font']+'}')
        sans=PROFILES[language]['font'].replace('Serif','Sans') if language.startswith('zh') or language in ('ja','he') else ('Latin Modern Sans' if language in ('en','fr') else PROFILES[language]['font'])
        locale.append(r'\newfontfamily'+chr(92)+name+'fontsf'+options+'{'+sans+'}')
    setup=['mode='+('paired' if mode=='bilingual' else mode)]
    if 'paragraph_flow' in settings:setup.append('paragraph-flow='+settings['paragraph_flow'])
    if settings.get('profile','article')!='article':setup.insert(0,'profile='+settings['profile'])
    if 'font_size' in settings:
        setup+=['body-size='+str(size),'body-leading='+str(settings.get('leading',round(size*1.2,2)))]
    elif 'leading' in settings:setup+=['body-leading='+str(settings['leading'])]
    if 'gap_mm' in settings:setup+=['column-gap='+str(gap)+'mm']
    geometry=[]
    if 'paper' in settings:geometry.append(settings['paper']+'paper')
    if 'twoside' in settings:geometry.append('twoside='+str(settings['twoside']).lower())
    if 'margin_mm' in settings:geometry+=['inner='+str(margin)+'mm','outer='+str(margin)+'mm']
    for key,texkey in [('inner_mm','inner'),('outer_mm','outer'),('binding_mm','bindingoffset'),('top_mm','top'),('bottom_mm','bottom')]:
        if key in settings:geometry.append(texkey+'='+str(settings[key])+'mm')
    if geometry:setup+=['geometry={'+','.join(geometry)+'}']
    divider=settings.get('divider',{})
    if 'color' in divider:
        locale.append(r'\definecolor{parallel.adapter.divider}{HTML}{'+divider['color']+'}')
        setup+=['divider-color=parallel.adapter.divider']
    for key,texkey in [('enabled','divider'),('width_pt','divider-width'),('style','divider-style')]:
        if key in divider:setup+=[texkey+'='+str(divider[key]).lower()+('pt' if key=='width_pt' else '')]
    folio=settings.get('page_numbers',{})
    for key in ('position','numbering'):
        if key in folio:setup+=[('page-numbering' if key=='numbering' else 'page-number-position')+'='+folio[key]]
    if 'prefix' in folio or 'suffix' in folio:
        setup+=['page-number-format={'+escape(folio.get('prefix',''))+r'\thepage{}'+escape(folio.get('suffix',''))+'}']
    locale += [r'\ParallelLanguages{'+names[0]+'}{'+names[1]+'}',r'\ParallelSetup{'+','.join(setup)+'}',r'\hypersetup{pdftitle={'+escape(data['title'][1 if mode=='right' else 0])+r'},pdfauthor={}}']
    body=[];titles=[language_text(t,l) for t,l in zip(data['title'],languages)]
    if settings.get('covers',False):body.append(r'\ParallelFrontCover{'+titles[0]+'}{'+titles[1]+'}')
    body.append(r'\ParallelTitle{'+titles[0]+'}{'+titles[1]+'}')
    for block_index,b in enumerate(data['blocks']):
        if b.get('break_before'):body.append(r'\clearpage')
        ident=b['id'];kind=b.get('kind','paragraph');pair=[content(b,i,l) if kind!='list' else '' for i,l in enumerate(languages)]
        if kind=='heading':
            next_block=data['blocks'][block_index+1] if block_index+1<len(data['blocks']) else {}
            command=r'\ParallelProseSection' if 'chunks' in next_block else r'\ParallelSection'
            body.append(command+'{'+ident+'}{'+pair[0]+'}{'+pair[1]+'}')
        elif kind=='paragraph' and 'chunks' in b:
            if mode=='bilingual':
                lines=[r'\begin{ParallelProseGroup}{'+ident+'}']
                for chunk in b['chunks']:
                    sides=[language_text(x,l) for x,l in zip(chunk['text'],languages)]
                    lines.append(r'\ParallelProseChunk{'+chunk['id']+'}{'+sides[0]+'}{'+sides[1]+'}')
                lines.append(r'\end{ParallelProseGroup}')
                body.append('\n'.join(lines))
            else:
                # Selected output is the exact joined paragraph, with no chunk line breaks.
                body.append(r'\ParallelProse{'+ident+'}{'+pair[0]+'}{'+pair[1]+'}')
        elif kind=='figure':
            names=image_names.get(ident)
            if names is None:names=['figure-'+ident+'/'+side+'.png' for side in ('left','right')] if len(figure_images(b))==2 else ['figure-'+ident+'/image.png']
            if isinstance(names,str):names=[names]
            figure=('\\ParallelWideFigure{' if b.get('placement')=='shared' else '\\ParallelFigure{')+ident+'}{'+names[0]+'}{'+pair[0]+'}{'+pair[1]+'}'+('['+names[1]+']' if len(names)==2 else '')
            if b.get('caption_prefix','automatic')=='none':figure=r'{\renewcommand\ParallelFigureLabel{}'+figure+'}'
            body.append(figure)
        elif kind=='list':
            for i,(left,right) in enumerate(zip(*b['text'])):
                pair=[language_text(left,languages[0]),language_text(right,languages[1])]
                if i==0:pair[0]=r'\phantomsection\label{'+ident+r'}\hypertarget{'+ident+'}{}'+pair[0];pair[1]=r'\ifdefstring{\ParallelMode}{right}{\phantomsection\label{'+ident+r'}\hypertarget{'+ident+r'}{}}{}'+pair[1]
                body.append(r'\ParallelText{'+ident+'.item-'+str(i+1)+'}{'+r'\begin{itemize}\item '+pair[0]+r'\end{itemize}}{'+r'\begin{itemize}\item '+pair[1]+r'\end{itemize}}')
        elif kind=='equation':
            formula=r'\[ '+b['math']+r' \]'
            body.append(r'\begin{ParallelKeep}\ParallelText{'+ident+'}{'+pair[0]+'}{'+pair[1]+'}'+r'\ParallelText{'+ident+'.formula}{'+formula+'}{'+formula+r'}\end{ParallelKeep}')
        elif kind=='table':
            body.append(r'\begin{ParallelKeep}')
            for row_index in range(len(b['rows'][0])+1):
                cells=[]
                for side in range(2):
                    row=b['headers'][side] if row_index==0 else b['rows'][side][row_index-1]
                    align=r'\RaggedLeft' if PROFILES[languages[side]]['direction']=='rtl' else r'\RaggedRight'
                    spec='@{}'+('>{'+align+r'\arraybackslash}X')*len(row)+'@{}'
                    table=r'\begin{tabularx}{\linewidth}{'+spec+'}'
                    if row_index==0:table+=r'\toprule '
                    table+=' & '.join((r'\textbf{'+language_text(x,languages[side])+'}') if row_index==0 else language_text(x,languages[side]) for x in row)+r'\\ '
                    if row_index==0:table+=r'\midrule '
                    if row_index==len(b['rows'][0]):table+=r'\bottomrule '
                    table+=r'\end{tabularx}'
                    if row_index==0:
                        anchor=r'\phantomsection\label{'+ident+r'}\hypertarget{'+ident+'}{}'
                        table=(anchor if side==0 else r'\ifdefstring{\ParallelMode}{right}{'+anchor+'}{}')+table
                    cells.append(table)
                body.append(r'\ParallelText{'+ident+'.row-'+str(row_index)+'}{'+cells[0]+'}{'+cells[1]+'}')
            caption=r'\ParallelText{'+ident+'.caption}{'+pair[0]+'}{'+pair[1]+'}' if 'text' in b else ''
            body.append(caption+r'\end{ParallelKeep}')
        else:
            if kind=='paragraph':
                flow=b.get('flow','default')
                if flow=='atomic':flow='keep'
                body.append('\\ParallelParagraph'+('' if flow=='default' else '[flow='+flow+']')+'{'+ident+'}{'+pair[0]+'}{'+pair[1]+'}')
            else:body.append('\\ParallelText{'+ident+'}{'+pair[0]+'}{'+pair[1]+'}')
    if settings.get('covers',False):body.append(r'\ParallelBackCover{'+titles[0]+'}{'+titles[1]+'}')
    main=r"""\documentclass[10pt,twoside]{article}
\usepackage{paralleltext}
\input{languages.tex}
\begin{document}
\input{content.tex}
\end{document}
"""
    main=main.replace('languages.tex',files['languages']).replace('content.tex',files['content'])
    return main,'\n'.join(locale)+'\n','\n\n'.join(body)+'\n'

def tex_document(data,mode):
    main,locale,body=tex_parts(data,mode)
    return main.replace(r'\input{languages.tex}',locale).replace(r'\input{content.tex}',body)

def project_filenames(stem='document'):
    """Internal names for one document in a portable project directory."""
    if not isinstance(stem,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,49}',stem):raise InputError('Invalid document stem')
    prefix='' if stem=='document' else stem+'-'
    return {'tex':stem+'.tex','languages':prefix+'languages.tex','content':prefix+'content.tex',
            'pdf':stem+'.pdf','log':stem+'.log','compile':prefix+'compile.log','result':prefix+'result.json'}

def write_project(data,input_path,out,mode,*,stem='document',asset_root=None):
    """Write a new named document inside an already-created collection folder.

    Existing document/assets are never overwritten. Shared package/license files
    may be reused only when their bytes match this installed skill exactly.
    """
    files=project_filenames(stem)
    if not out.is_dir():raise InputError('Project directory must already exist')
    figures=[b for b in data['blocks'] if b.get('kind')=='figure']
    prefix=Path() if stem=='document' else Path('images')/stem
    images={b['id']:([(prefix/('figure-'+b['id'])/(side+'.png')).as_posix() for side in ('left','right')] if len(figure_images(b))==2 else [(prefix/('figure-'+b['id'])/'image.png').as_posix()]) for b in figures}
    # Preserve recognized importer provenance only. Root metadata was historically
    # open/ignored, so arbitrary caller-owned "translation" values stay harmless.
    provenance={}
    metadata=data.get('translation')
    if isinstance(metadata,dict) and isinstance(metadata.get('content'),dict):
        master=metadata['content'];version=metadata.get('contract_version')
        prefix='' if stem=='document' else stem+'-'
        if version==2 and isinstance(master.get('document'),dict) and isinstance(master.get('units'),list):
            provenance[prefix+'translation-source.jsonl']=''.join(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n' for record in [master['document']]+master['units'])
        elif version==1:
            provenance[prefix+'translation-source.json']=json.dumps(master,ensure_ascii=False,allow_nan=False,indent=2)+'\n'
        if provenance:
            provenance[prefix+'translation-map.json']=json.dumps({k:v for k,v in metadata.items() if k!='content'},ensure_ascii=False,allow_nan=False,indent=2)+'\n'
    targets=[out/name for name in files.values()]+[out/(stem+suffix) for suffix in ('.aux','.xdv','.fls','.fdb_latexmk','.toc')]+[out/name for names in images.values() for name in names]
    targets += [out/name for name in provenance]
    if any(target.exists() or target.is_symlink() for target in targets):raise InputError('Named document, image or provenance already exists; preserve previous outputs')
    shared={'paralleltext.sty':ROOT/'assets/paralleltext.sty','LICENSE':ROOT/'LICENSE'}
    for name,source in shared.items():
        target=out/name
        if target.is_symlink() or (target.exists() and target.read_bytes()!=source.read_bytes()):raise InputError('Existing shared project resource differs: '+name)
    from PIL import Image
    for block in figures:
        for relative,name in zip(figure_images(block),images[block['id']]):
            source=resolve_image(input_path,relative,asset_root)
            target=out/name
            if not target.resolve().is_relative_to(out.resolve()):raise InputError('Figure output escapes the project directory')
            target.parent.mkdir(parents=True,exist_ok=True)
            with Image.open(source) as im:
                if im.format not in {'PNG','JPEG'}:raise InputError('Unsupported image bytes')
                image=im.convert('RGBA');background=Image.new('RGBA',image.size,'white');background.alpha_composite(image)
                background.convert('RGB').save(target)
    for name,source in shared.items():
        if not (out/name).exists():shutil.copyfile(source,out/name)
    main,locale,body=tex_parts(data,mode,stem=stem,image_names=images)
    for name,text in [(files['tex'],main),(files['languages'],locale),(files['content'],body)]:
        (out/name).write_text(text,encoding='utf-8')
    for name,text in provenance.items():
        (out/name).write_text(text,encoding='utf-8')
    return files

def export_document(data,input_path,out,mode,*,stem='document',asset_root=None):
    if out.exists():raise InputError('Output directory already exists; choose a new directory to preserve previous outputs')
    out.mkdir(parents=True)
    return write_project(data,input_path,out,mode,stem=stem,asset_root=asset_root)

def write_json_atomic(path,value):
    # Publish a complete receipt without exposing partially written JSON.
    fd,name=tempfile.mkstemp(prefix='.bilingual-receipt-',dir=path.parent)
    temporary=Path(name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
        temporary.replace(path)
    finally:
        if temporary.exists():temporary.unlink()


BUILD_MANIFEST = '.bilingual-build.json'
BUILD_LOCK = '.bilingual-build.lock'


def build_document(data,input_path,out,mode,*,asset_root=None,environment=None):
    """Update a renderer-owned project without discarding latexmk dependencies.

    Generate into a sibling temporary directory first. Only generated files in
    the ownership receipt may be replaced, and only if their recorded bytes are
    still present. Native edits belong to export + latexmk, not this JSON route.
    """
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def generated(name):
        return name in {'document.tex','languages.tex','content.tex','paralleltext.sty','LICENSE','translation-map.json','translation-source.jsonl','translation-source.json'} or bool(re.fullmatch(r'figure-[a-z][a-z0-9.-]{0,79}/(?:left|right|image)\.png',name))

    def check_path(name):
        target=out/name
        for part in [target,*target.parents]:
            if part==out:break
            if part.is_symlink():raise InputError('Symlink in managed project path: '+name)
        if target.exists() and not target.is_file():raise InputError('Managed project path is not a file: '+name)
        return target

    fresh=not out.exists()
    if fresh:out.mkdir(parents=True)
    manifest=out/BUILD_MANIFEST
    if not fresh and (manifest.is_symlink() or not manifest.is_file()):
        raise InputError('Build requires a new directory or a project previously created by build; preserve native edits with export and latexmk')
    try:
        lock=os.open(out/BUILD_LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:
        raise InputError('Another build or interrupted build lock exists; verify no build is running before removing '+BUILD_LOCK)
    os.close(lock)
    try:
        for name in ['document'+suffix for suffix in ('.aux','.pdf','.log','.out','.toc','.fls','.fdb_latexmk','.xdv','.synctex.gz')]+['compile.log','result.json']:
            check_path(name)
        previous={};pending={}
        if fresh:write_json_atomic(manifest,{'format':1,'files':{}})
        if not fresh:
            try:
                state=json.loads(manifest.read_text(encoding='utf-8'))
                if state.get('format')!=1:raise ValueError('Unsupported format')
                previous=state['files'];pending=state.get('pending',{})
                for entries in (previous,pending):
                    if not isinstance(entries,dict):raise ValueError('Invalid files')
                    for name,value in entries.items():
                        if not generated(name) or not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid managed file')
            except (ValueError,KeyError,TypeError,AttributeError) as exc:
                raise InputError('Invalid build ownership receipt') from exc
        known=set(previous)|set(pending)
        for name in known:
            target=check_path(name)
            if target.exists() and digest(target) not in {previous.get(name),pending.get(name)}:
                raise InputError('Managed file was edited outside build: '+name+'; preserve the native project and choose a new build directory')
        with tempfile.TemporaryDirectory(prefix='.bilingual-build-',dir=out.parent) as work:
            staged=Path(work)/'project'
            export_document(data,input_path,staged,mode,asset_root=asset_root)
            current={p.relative_to(staged).as_posix():digest(p) for p in staged.rglob('*') if p.is_file()}
            for name in current:
                target=check_path(name)
                if target.exists() and name not in known:
                    raise InputError('Unmanaged file would be overwritten: '+name)
            # The pending receipt makes an interrupted file update recoverable.
            # Every existing byte must match a previously recorded old/new hash.
            old={name:(digest(out/name) if (out/name).exists() else previous.get(name,pending.get(name))) for name in known}
            def receipt(value):
                candidate=Path(work)/'receipt.json'
                candidate.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
                candidate.replace(manifest)
            source_changed=old!=current
            if environment is not None or (source_changed and (out/'result.json').exists()):
                write_json_atomic(out/'result.json',{'ok':False,'stage':'build','error':'Compilation and checks have not completed'})
            receipt({'format':1,'files':old,'pending':current})
            changed=[]
            for name,value in current.items():
                target=out/name
                if not target.exists() or digest(target)!=value:
                    target.parent.mkdir(parents=True,exist_ok=True)
                    (staged/name).replace(target)
                    changed.append(name)
            for name in known-set(current):
                if (out/name).exists():(out/name).unlink()
                changed.append(name)
            receipt({'format':1,'files':current})
        update={'changed_files':sorted(changed),'unchanged_files':len(current)-len(set(changed)&set(current))}
        if environment is None:return update
        # Keep the ownership lock through compilation and QA. A previous PDF
        # may remain after failure, but its old success receipt must not survive.
        result_path=out/'result.json'
        try:
            return compile_project(data,out,mode,environment,update=update)
        except (OSError,RuntimeError,subprocess.TimeoutExpired,ImportError) as exc:
            write_json_atomic(result_path,{'ok':False,'stage':'build','error':str(exc),'update':update})
            raise
    finally:
        (out/BUILD_LOCK).unlink()


def check_pdf(path,covered,paired=False,margin_mm=12):
    import pymupdf as fitz
    from PIL import Image, ImageChops
    pdf=fitz.open(path);errors=[];blanks=[];mm=72/25.4;fonts_checked=set()
    for i,p in enumerate(pdf):
        for font in p.get_fonts():
            xref=font[0]
            if xref not in fonts_checked:
                fonts_checked.add(xref)
                if xref<=0 or not pdf.extract_font(xref)[3]:errors.append(f'Unembedded font on page {i+1}: '+font[3])
        if '\ufffd' in p.get_text():errors.append(f'Replacement glyph on page {i+1}')
        pix=p.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
        image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
        bbox=ImageChops.difference(image,Image.new('RGB',image.size,'white')).getbbox()
        if not bbox:blanks.append(i+1)
        else:
            horizontal=min(bbox[0],pix.width-bbox[2])/mm
            vertical=min(bbox[1],pix.height-bbox[3])/mm
            if horizontal<margin_mm-.8:errors.append(f'Ink enters configured horizontal margin on page {i+1}')
            if vertical<5:errors.append(f'Ink enters 5 mm print exclusion on page {i+1}')
        for link in p.get_links():
            if link.get('kind') in {fitz.LINK_GOTO,fitz.LINK_NAMED} and not 0<=link.get('page',-1)<len(pdf):errors.append(f'Broken internal link on page {i+1}')
            # MuPDF may expose named GoToR actions as LINK_LAUNCH. Inspect the
            # actual PDF action instead of assuming all external links use a page index.
            action=pdf.xref_get_key(link['xref'],'A/S')[1] if link.get('xref') else ''
            if action=='/GoToR':
                file_type,filename=pdf.xref_get_key(link['xref'],'A/F')
                dest_type,destination=pdf.xref_get_key(link['xref'],'A/D')
                companion=(path.parent/filename).resolve()
                if file_type!='string' or not companion.is_relative_to(path.parent.parent.resolve()) or not companion.is_file():errors.append(f'Missing/out-of-bundle companion on page {i+1}');continue
                with fitz.open(companion) as other:
                    if dest_type=='string':
                        target=other.resolve_names().get(destination)
                        if target is None or not 0<=target.get('page',-1)<len(other):errors.append(f'Broken named companion destination on page {i+1}')
                    else:
                        match=re.match(r'\[\s*(\d+)',destination)
                        if not match or not 0<=int(match[1])<len(other):errors.append(f'Broken companion destination on page {i+1}')
    if covered and (len(pdf)%2 or 2 not in blanks or len(pdf)-1 not in blanks):errors.append('Cover or blank-page parity failure')
    count=0
    if paired:
        aux=path.with_suffix('.aux')
        if not aux.exists():errors.append('Pair-position evidence missing')
        else:
            text=aux.read_text()
            positions={m[1]:(int(m[2]),int(m[3])) for m in re.finditer(r'\\zref@newlabel\{pt-internal:([^{}]+)\}\{\\posx\{(\d+)\}\\posy\{(\d+)\}\}',text)}
            pages={m[1]:m[2] for m in re.finditer(r'\\newlabel\{pt-internal:([^{}]+-[LR])\}\{\{[^{}]*\}\{([^{}]+)\}',text)}
            widths={m[1]:int(m[2]) for m in re.finditer(r'\\PairMeasure\{([^{}]+)\}\{(\d+)\}',text)}
            physical={m[1]:int(m[2])-1 for m in re.finditer(r'\\PTPairPage\{([^{}]+)\}\{(\d+)\}',text)}
            geometry={int(m[1])-1:tuple(int(m[i]) for i in range(2,7)) for m in re.finditer(r'\\PTPageGeometry'+r'\{(\d+)\}'*6,text)}
            scale=72/(72.27*65536)
            for key,pos in positions.items():
                if not key.endswith('-L-start'):continue
                ident=key[:-8];right=ident+'-R-start';count+=1
                if right not in positions or positions[right][1]!=pos[1] or pages.get(ident+'-L')!=pages.get(ident+'-R'):errors.append('Pair start/page mismatch: '+ident)
                if ident in widths and right in positions:
                    page=physical.get(ident)
                    if page is None or page not in geometry:
                        errors.append('Live page geometry evidence missing: '+ident);continue
                    left,top,textwidth,textheight,gap=geometry[page]
                    if abs(pos[0]*scale-left*scale)>.2:errors.append('Physical left column slot shifted: '+ident)
                    expected=(left+widths[ident]+gap)*scale
                    if abs(positions[right][0]*scale-expected)>.2:errors.append('Physical column slot shifted: '+ident)
            if not count:errors.append('No paired position records found')
    return {'ok':not errors,'pages':len(pdf),'blank_pages':blanks,'paired_blocks_checked':count,'embedded_fonts_checked':len(fonts_checked),'errors':errors,'visual_review':'required','semantic_review':'caller responsibility'}

def compile_project(data,out,mode,environment,*,stem='document',update=None):
    """Compile and check one named project through the canonical rendering path."""
    files=project_filenames(stem)
    p=subprocess.run(['latexmk','-norc','-xelatex','-interaction=nonstopmode','-halt-on-error','-latexoption=-no-shell-escape',files['tex']],cwd=out,capture_output=True,text=True,timeout=180)
    (out/files['compile']).write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(f"LaTeX failed; inspect {out / files['compile']}")
    log=(out/files['log']).read_text(errors='replace')
    issues=[line for line in log.splitlines() if any(t in line for t in ['Missing character:','Overfull','undefined references','multiply defined','No hyphenation patterns'])]
    result=check_pdf(out/files['pdf'],data.get('layout',{}).get('covers',False),mode=='bilingual',min(data.get('layout',{}).get('inner_mm',data.get('layout',{}).get('margin_mm',16 if data.get('layout',{}).get('profile')=='bound' else 18)),data.get('layout',{}).get('outer_mm',data.get('layout',{}).get('margin_mm',16 if data.get('layout',{}).get('profile')=='bound' else 18))))
    result['environment']=environment
    if update is not None:result['update']=update
    result['renderer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['template_sha256']={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['paralleltext.sty']}
    result['errors']+=issues;result['ok']=not result['errors']
    result.update({'pdf':str(out/files['pdf']),'sha256':hashlib.sha256((out/files['pdf']).read_bytes()).hexdigest(),'languages':data['languages'],'mode':mode})
    write_json_atomic(out/files['result'],result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['preflight','export','render','build','validate'])
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--translation-skill',type=Path,help='Explicit discovered bilingual-translation installation for reviewed JSONL/v1 input')
    parser.add_argument('--source-side',choices=['left','right'],default='left',help='Physical source column for translation input')
    parser.add_argument('--layout',help='Sparse JSON object of global layout overrides; uses the documented layout schema without editing the input manuscript')
    parser.add_argument('--asset-root',type=Path,help='Read figure paths inside this directory only (default: input directory)')
    parser.add_argument('--mode',choices=['bilingual','left','right'],default='bilingual')
    parser.add_argument('--no-covers',action='store_true',help='Compatibility flag: validate assumes no covers by default')
    parser.add_argument('--covers',action='store_true',help='For validate: require booklet cover/blank parity')
    parser.add_argument('--paired',action='store_true',help='For validate: verify paired positions against the matching AUX')
    parser.add_argument('--margin-mm',type=float,default=18,help='For validate: nominal horizontal margin')
    args=parser.parse_args()
    try:
        if args.command=='validate':
            result=check_pdf(args.input,args.covers,args.paired,args.margin_mm)
            log=args.input.with_suffix('.log')
            if log.exists():result['errors'] += [line for line in log.read_text(errors='replace').splitlines() if any(t in line for t in ['Missing character:','Overfull','undefined references','multiply defined','No hyphenation patterns'])]
            result['ok']=not result['errors'];code=0 if result['ok'] else 4
        else:
            if args.translation_skill or args.input.suffix.lower()=='.jsonl':
                if not args.translation_skill:raise InputError('JSONL input requires --translation-skill with the discovered bilingual-translation installation')
                from import_translation import read_translation
                data=read_translation(args.input,args.translation_skill,args.source_side)
            else:data=validate(json.loads(args.input.read_text(encoding='utf-8')))
            if args.layout is not None:
                overrides=json.loads(args.layout)
                if not isinstance(overrides,dict):raise InputError('--layout must be a JSON object')
                data['layout']={**data.get('layout',{}),**overrides}
                validate(data)
            result={'ok':True} if args.command=='export' else preflight(data);code=0 if result['ok'] else 2
            if args.command in ('export','render','build') and result['ok']:
                if not args.output:raise InputError('--output is required')
                out=args.output.resolve()
                if args.command=='build':
                    result=build_document(data,args.input,out,args.mode,asset_root=args.asset_root,environment=result)
                else:
                    export_document(data,args.input,out,args.mode,asset_root=args.asset_root)
                    if args.command=='export':
                        print(json.dumps({'ok':True,'tex':str(out/'document.tex'),'editable_content':str(out/'content.tex'),'build':'latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape document.tex'}));return 0
                    result=compile_project(data,out,args.mode,result)
                code=0 if result['ok'] else 4
    except (InputError,json.JSONDecodeError,UnicodeError) as e:result={'ok':False,'error':str(e),'stage':'input'};code=1
    except (OSError,RuntimeError,subprocess.TimeoutExpired,ImportError) as e:result={'ok':False,'error':str(e),'stage':'runtime'};code=3
    print(json.dumps(result,ensure_ascii=False));return code

if __name__=='__main__':sys.exit(main())
