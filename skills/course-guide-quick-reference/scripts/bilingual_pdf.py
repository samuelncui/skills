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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    'en': {'font': 'Latin Modern Roman', 'direction': 'ltr', 'locale': 'en'},
    'fr': {'font': 'Latin Modern Roman', 'direction': 'ltr', 'locale': 'fr'},
    'zh-Hans': {'font': 'Noto Serif CJK SC', 'direction': 'ltr', 'locale': 'zh'},
    'zh-Hant': {'font': 'Noto Serif CJK TC', 'direction': 'ltr', 'locale': 'zh'},
    'ja': {'font': 'Noto Serif CJK JP', 'direction': 'ltr', 'locale': 'ja'},
    'ar': {'font': 'Noto Naskh Arabic', 'direction': 'rtl', 'locale': 'ar'},
}
MATH_COMMANDS = {'frac','sqrt','sum','prod','int','infty','alpha','beta','gamma','theta','sigma','mu','pi','Delta','times','cdot','pm','leq','geq','neq','approx','log','ln','exp','sin','cos','left','right','mathrm','mathbf','text','quad','qquad','overline','hat','bar'}

class InputError(ValueError): pass

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
        if 'flow' in b and (kind!='paragraph' or b['flow'] not in ('atomic','breakable')):raise InputError('flow is atomic or breakable, for paragraph blocks only')
        if 'placement' in b and (kind!='figure' or b['placement'] not in ('paired','shared')):raise InputError('placement is paired or shared, for figures only')
        pair=b.get('text')
        if not isinstance(pair,list) or len(pair)!=2:raise InputError('Each block needs exactly two paired texts')
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
        if kind=='figure':
            image=b.get('image')
            if not isinstance(image,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]*\.(?:png|jpg|jpeg)',image) or '..' in Path(image).parts:raise InputError('Figure image must be a relative PNG/JPEG path')
        if kind=='reference':
            target=b.get('target')
            if not isinstance(target,str) or not re.fullmatch(r'[a-z][a-z0-9.-]{0,79}',target):raise InputError('Reference target must be an identifier')
            if 'file' in b:
                if not isinstance(b['file'],str) or not re.fullmatch(r'(?:\.\./)?[a-z][a-z0-9/_-]*\.pdf',b['file']):raise InputError('Reference file must be a relative PDF path')
                if isinstance(b.get('page'),bool) or not isinstance(b.get('page'),int) or b['page']<1:raise InputError('Reference page must be positive')
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
                    if not isinstance(cell,str):raise InputError('Table header must be plain text')
                    text_value(cell)
                for row in rows[side]:
                    if not isinstance(row,list) or len(row)!=len(h[side]) or any(not isinstance(x,str) for x in row):raise InputError('Table row has wrong columns or non-text cell')
                    for cell in row:text_value(cell)
        if b.get('kind')=='reference' and 'file' not in b and b['target'] not in ids:raise InputError('Unresolved local reference: '+b['target'])
    generated=[]
    for b in blocks:
        if b.get('kind')=='equation':generated.append(b['id']+'.formula')
        if b.get('kind')=='figure' and b.get('placement')=='shared':generated.append(b['id']+'.caption')
        if b.get('kind')=='table':generated.extend([b['id']+'.row-'+str(i) for i in range(len(b['rows'][0])+1)]+[b['id']+'.caption'])
        if b.get('kind')=='list':generated.extend(b['id']+'.item-'+str(i+1) for i in range(len(b['text'][0])))
    if any(x in ids for x in generated) or len(generated)!=len(set(generated)):raise InputError('Generated list IDs collide with explicit block IDs')
    settings=data.get('layout',{})
    if not isinstance(settings,dict):raise InputError('layout must be an object')
    for key,default,lo,hi in [('font_size',10,9,14),('margin_mm',18,12,30),('gap_mm',6,4,12)]:
        value=settings.get(key,default)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not lo<=value<=hi:raise InputError('Invalid layout '+key)
    if not isinstance(settings.get('paper','a4'),str) or settings.get('paper','a4') not in {'a4','letter'}:raise InputError('paper must be a4 or letter')
    if not isinstance(settings.get('covers',True),bool):raise InputError('covers must be boolean')
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
    for package in packages:
        q=subprocess.run(['kpsewhich',package],capture_output=True,text=True)
        if q.returncode or not q.stdout.strip():package_missing.append(package)
    fonts=[]
    font_requests=[(language,PROFILES[language]['font']) for language in data['languages']]
    for language in data['languages']:
        body_font=PROFILES[language]['font']
        heading_font=body_font.replace('Serif','Sans') if language.startswith('zh') or language=='ja' else ('Latin Modern Sans' if language in ('en','fr') else body_font)
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
            if language=='marker':sample='•'+''.join(chars(v,True) for b in data['blocks'] for v in b['text'])
            else:
                def block_chars(b,i):
                    if ':headings' in language:return chars(b['text'][i]) if b.get('kind')=='heading' else ''
                    value=chars(b['text'][i])
                    if b.get('kind')=='table':value+=chars(b['headers'][i])+chars(b['rows'][i])
                    return value
                sample=''.join(data['title'][i]+''.join(block_chars(b,i) for b in data['blocks']) for i in indices)
            missing_glyphs=sorted({f'U+{ord(c):04X}' for c in sample if not c.isspace() and ord(c) not in cmap})
        fonts.append({'language':language,'requested':wanted,'matched':lines[0] if lines else '', 'available':exact,'missing_glyphs':missing_glyphs})
    return {'ok':not package_missing and all(f['available'] and not f['missing_glyphs'] for f in fonts),'missing_packages':package_missing,'fonts':fonts,'engine':subprocess.run(['xelatex','--version'],capture_output=True,text=True).stdout.splitlines()[0]}

NATIVE_LANGUAGES = {'en':'english','fr':'french','zh-Hans':'chinese','zh-Hant':'chinese','ja':'japanese','ar':'arabic'}

def language_text(text,language,prefix='',suffix=''):
    if isinstance(text,dict):
        value=''.join((r'\textenglish{'+escape(run['text'])+'}' if run['direction']=='ltr' else escape(run['text'])) for run in text['runs'])
    else:value=escape(text).replace('\n',' ')
    return prefix+value+suffix

def content(b,index,language):
    value=b['text'][index];kind=b.get('kind','paragraph')
    if kind=='list':
        return r'\begin{itemize}'+''.join(r'\item '+language_text(x,language) for x in value)+r'\end{itemize}'
    value=language_text(value,language)
    if kind=='reference':
        if 'file' in b:
            return r'\href[page='+str(b['page'])+']{'+b['file']+'}{'+value+r' \textenglish{(p.\,'+str(b['page'])+')}}'
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
        options='[Script=Arabic]' if language=='ar' else ''
        locale.append(r'\newfontfamily'+chr(92)+name+'font'+options+'{'+PROFILES[language]['font']+'}')
        sans=PROFILES[language]['font'].replace('Serif','Sans') if language.startswith('zh') or language=='ja' else ('Latin Modern Sans' if language in ('en','fr') else PROFILES[language]['font'])
        locale.append(r'\newfontfamily'+chr(92)+name+'fontsf'+options+'{'+sans+'}')
    locale += [r'\ParallelLanguages{'+names[0]+'}{'+names[1]+'}',r'\ParallelSelect{'+('paired' if mode=='bilingual' else mode)+'}',r'\renewcommand\ParallelBodySize{'+str(size)+'}',r'\renewcommand\ParallelBodyLeading{'+str(round(size*1.2,2))+'}',r'\renewcommand\ParallelColumnGap{'+str(gap)+'mm}',r'\geometry{'+settings.get('paper','a4')+'paper,inner='+str(margin)+'mm,outer='+str(margin)+'mm,top=17mm,bottom=14mm}',r'\hypersetup{pdftitle={'+escape(data['title'][1 if mode=='right' else 0])+r'},pdfauthor={}}']
    body=[];titles=[language_text(t,l) for t,l in zip(data['title'],languages)]
    if settings.get('covers',False):body.append(r'\ParallelFrontCover{'+titles[0]+'}{'+titles[1]+'}')
    body.append(r'\ParallelTitle{'+titles[0]+'}{'+titles[1]+'}')
    for b in data['blocks']:
        if b.get('break_before'):body.append(r'\clearpage')
        ident=b['id'];kind=b.get('kind','paragraph');pair=[content(b,i,l) if kind!='list' else '' for i,l in enumerate(languages)]
        if kind=='heading':body.append(r'\ParallelSection{'+ident+'}{'+pair[0]+'}{'+pair[1]+'}')
        elif kind=='figure':body.append(('\\ParallelWideFigure{' if b.get('placement')=='shared' else '\\ParallelFigure{')+ident+'}{'+image_names.get(ident,'figure-'+ident+'.png')+'}{'+pair[0]+'}{'+pair[1]+'}')
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
                    table+=' & '.join((r'\textbf{'+escape(x)+'}') if row_index==0 else escape(x) for x in row)+r'\\ '
                    if row_index==0:table+=r'\midrule '
                    if row_index==len(b['rows'][0]):table+=r'\bottomrule '
                    table+=r'\end{tabularx}'
                    if row_index==0:
                        anchor=r'\phantomsection\label{'+ident+r'}\hypertarget{'+ident+'}{}'
                        table=(anchor if side==0 else r'\ifdefstring{\ParallelMode}{right}{'+anchor+'}{}')+table
                    cells.append(table)
                body.append(r'\ParallelText{'+ident+'.row-'+str(row_index)+'}{'+cells[0]+'}{'+cells[1]+'}')
            body.append(r'\ParallelText{'+ident+'.caption}{'+pair[0]+'}{'+pair[1]+r'}\end{ParallelKeep}')
        else:body.append(('\\ParallelProse{' if b.get('flow')=='breakable' else '\\ParallelText{')+ident+'}{'+pair[0]+'}{'+pair[1]+'}')
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

def write_project(data,input_path,out,mode,*,stem='document'):
    """Write a new named document inside an already-created collection folder.

    Existing document/assets are never overwritten. Shared package/license files
    may be reused only when their bytes match this installed skill exactly.
    """
    files=project_filenames(stem)
    if not out.is_dir():raise InputError('Project directory must already exist')
    figures=[b for b in data['blocks'] if b.get('kind')=='figure']
    prefix=Path() if stem=='document' else Path('images')/stem
    images={b['id']:(prefix/('figure-'+b['id']+'.png')).as_posix() for b in figures}
    targets=[out/name for name in files.values()]+[out/(stem+suffix) for suffix in ('.aux','.xdv','.fls','.fdb_latexmk','.toc')]+[out/name for name in images.values()]
    if any(target.exists() or target.is_symlink() for target in targets):raise InputError('Named document or image already exists; preserve previous outputs')
    shared={'paralleltext.sty':ROOT/'assets/paralleltext.sty','LICENSE':ROOT/'LICENSE'}
    for name,source in shared.items():
        target=out/name
        if target.is_symlink() or (target.exists() and target.read_bytes()!=source.read_bytes()):raise InputError('Existing shared project resource differs: '+name)
    from PIL import Image
    for block in figures:
        source=(input_path.resolve().parent/block['image']).resolve()
        if not source.is_relative_to(input_path.resolve().parent):raise InputError('Figure escapes the input directory')
        target=out/images[block['id']]
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
    return files

def export_document(data,input_path,out,mode,*,stem='document'):
    if out.exists():raise InputError('Output directory already exists; choose a new directory to preserve previous outputs')
    out.mkdir(parents=True)
    return write_project(data,input_path,out,mode,stem=stem)

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
            scale=72/(72.27*65536)
            for key,pos in positions.items():
                if not key.endswith('-L-start'):continue
                ident=key[:-8];right=ident+'-R-start';count+=1
                if right not in positions or positions[right][1]!=pos[1] or pages.get(ident+'-L')!=pages.get(ident+'-R'):errors.append('Pair start/page mismatch: '+ident)
                if ident in widths and right in positions:
                    page=int(pages.get(ident+'-L','1'))-1
                    expected=pdf[page].rect.width-pos[0]*scale-widths[ident]*scale
                    if abs(positions[right][0]*scale-expected)>.2:errors.append('Physical column slot shifted: '+ident)
            if not count:errors.append('No paired position records found')
    return {'ok':not errors,'pages':len(pdf),'blank_pages':blanks,'paired_blocks_checked':count,'embedded_fonts_checked':len(fonts_checked),'errors':errors,'visual_review':'required','translation_review':'required'}

def compile_project(data,out,mode,environment,*,stem='document'):
    """Compile and check one named project through the canonical rendering path."""
    files=project_filenames(stem)
    p=subprocess.run(['latexmk','-norc','-xelatex','-interaction=nonstopmode','-halt-on-error','-latexoption=-no-shell-escape',files['tex']],cwd=out,capture_output=True,text=True,timeout=180)
    (out/files['compile']).write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(f"LaTeX failed; inspect {out / files['compile']}")
    log=(out/files['log']).read_text(errors='replace')
    issues=[line for line in log.splitlines() if any(t in line for t in ['Missing character:','Overfull','undefined references','multiply defined','No hyphenation patterns'])]
    result=check_pdf(out/files['pdf'],data.get('layout',{}).get('covers',False),mode=='bilingual',data.get('layout',{}).get('margin_mm',18))
    result['environment']=environment
    result['renderer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['template_sha256']={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['paralleltext.sty']}
    result['errors']+=issues;result['ok']=not result['errors']
    result.update({'pdf':str(out/files['pdf']),'sha256':hashlib.sha256((out/files['pdf']).read_bytes()).hexdigest(),'languages':data['languages'],'mode':mode})
    (out/files['result']).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['preflight','export','render','validate'])
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path)
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
            data=validate(json.loads(args.input.read_text(encoding='utf-8')))
            result={'ok':True} if args.command=='export' else preflight(data);code=0 if result['ok'] else 2
            if args.command in ('export','render') and result['ok']:
                if not args.output:raise InputError('--output is required')
                out=args.output.resolve();export_document(data,args.input,out,args.mode)
                if args.command=='export':
                    print(json.dumps({'ok':True,'tex':str(out/'document.tex'),'editable_content':str(out/'content.tex'),'build':'latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape document.tex'}));return 0
                result=compile_project(data,out,args.mode,result)
                code=0 if result['ok'] else 4
    except (InputError,json.JSONDecodeError,UnicodeError) as e:result={'ok':False,'error':str(e),'stage':'input'};code=1
    except (OSError,RuntimeError,subprocess.TimeoutExpired,ImportError) as e:result={'ok':False,'error':str(e),'stage':'runtime'};code=3
    print(json.dumps(result,ensure_ascii=False));return code

if __name__=='__main__':sys.exit(main())
