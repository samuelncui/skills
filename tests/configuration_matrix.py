#!/usr/bin/env python3
"""Native configuration regressions in isolated installed projects."""
import argparse, concurrent.futures, json, re, shutil, subprocess, sys
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append',help='Run only named cases (repeatable)');a=p.parse_args()
work=a.output.resolve()
if work.exists():raise SystemExit('Choose a fresh output directory')
work.mkdir(parents=True)
shutil.copytree(ROOT/'skills/bilingual-pdf',work/'installed')
sys.path.insert(0,str(work/'installed/scripts'))
from bilingual_pdf import validate,export_document,check_pdf
BUILD=['latexmk','-norc','-xelatex','-interaction=nonstopmode','-halt-on-error','-latexoption=-no-shell-escape']
SCALE=72/(72.27*65536)
body=r'\ParallelText{one}{First page.}{A corresponding sentence.}\clearpage\ParallelText{two}{Second page.}{Another corresponding sentence.}'
cases=[]
def add(name,setup='',content=body,options='',classopts='10pt,twoside',error=None,paired=True,covers=False,margin=5):
 d=work/name;d.mkdir();shutil.copyfile(work/'installed/assets/paralleltext.sty',d/'paralleltext.sty')
 for profile in ['bound','reading']:shutil.copyfile(work/f'installed/assets/{profile}-profile.tex',d/f'{profile}-profile.tex')
 (d/'main.tex').write_text('\\documentclass['+classopts+']{article}\n\\usepackage['+options+']{paralleltext}\n'+setup+'\n\\begin{document}\n'+content+'\n\\end{document}\n')
 cases.append(dict(name=name,project=d,error=error,paired=paired,covers=covers,margin=margin))
add('zero-configuration')
add('mirrored-binding',r'\ParallelSetup{geometry={inner=24mm,outer=16mm,bindingoffset=3mm}}')
add('standard-geometry',r'\geometry{inner=23mm,outer=15mm,bindingoffset=4mm}')
add('oneside-binding',r'\ParallelSetup{geometry={inner=24mm,outer=16mm,bindingoffset=3mm}}',classopts='10pt,oneside')
add('custom-paper',r'\ParallelSetup{geometry={paperwidth=180mm,paperheight=240mm,inner=20mm,outer=14mm},divider-style=densely dotted,divider-width=.6pt}')
add('package-options',options='geometry={letterpaper,inner=25mm,outer=15mm},divider-color=red!60!black,divider-width=.8pt,divider-style=dashed,page-number-position=footer-center')
add('bound-profile',r'\input{bound-profile.tex}')
add('reading-profile',r'\input{reading-profile.tex}')
add('standard-page-style',r'\pagestyle{empty}\renewcommand\thepage{X\arabic{page}}')
add('roman-folio',r'\ParallelSetup{page-number-position=header-inner,page-number-format={\thepage}}\pagenumbering{roman}')
add('selected-two-columns',r'\ParallelSetup{mode=left,single-columns=2}',paired=False)
for n in [1,2]:
 content=r'\ParallelFrontCover{Field notes}{Notebook}\pagenumbering{roman}'+(body if n==2 else r'\ParallelText{one}{Body.}{Content.}')+r'\ParallelBackCover{Back}{End}'
 add('booklet-'+str(n)+'-body-pages',content=content,covers=True)
add('custom-page-style-with-covers',r'\pagestyle{empty}',r'\ParallelFrontCover{Front}{First}\pagenumbering{arabic}'+body+r'\ParallelBackCover{Back}{Last}',covers=True)
add('custom-cover-policy',r'\ParallelSetup{blank-verso=false,blank-inside-back=false,back-parity=odd}',r'\ParallelFrontCover{Front}{First}\ParallelText{one}{Body.}{Text.}\ParallelBackCover{Back}{Last}')
nav=r'''\ParallelSetup{profile=bound,tabs=true,tab-width=5mm,tab-height=9mm,tab-step=12mm,header-left=\ParallelFirstEntry,header-right=\ParallelLastEntry}
\ParallelDeclareRole{warning}{parallel.caution}{Caution:}{Attention:}
\ParallelDeclareNavigation{a}{1}{A}\ParallelDeclareNavigation[blue!60!black]{b}{2}{B}'''
navbody=r'''\ParallelNavigation{a}\ParallelEntry{alpha}{Alpha}{Alpha}
\ParallelNote[warning]{note}{State the assumptions.}{Explain the valid conditions.}
\ParallelText{diagram}{\begin{ParallelDiagram}\node[parallel fixed](a){\ParallelLocalize{Start}{Begin}};\node[parallel variable,right=8mm of a](b){Finish};\draw[parallel arrow](a)--(b);\end{ParallelDiagram}}{A diagram can also have an independently authored explanation.}
\clearpage\ParallelText{continued}{Alpha continues here.}{The same entry continues.}
\ParallelNavigation{b}\ParallelEntry{beta}{Beta}{Beta}\ParallelText{beta-body}{Another entry.}{A second explanation.}
\ParallelLookup{lookup}{alpha}{Alpha}{Alpha}\ParallelEndEntry\ParallelEndNavigation'''
# Standard TikZ library configuration remains available.
add('semantic-navigation',nav+r'\usetikzlibrary{positioning}',navbody)
flowbody=r'\ParallelNavigation{a}\ParallelEntry{alpha}{Alpha}{Alpha}\ParallelProse{long}{'+('One entry continues naturally across pages. '*450)+r'}{'+('The corresponding paragraph is longer and explains another useful detail. '*350)+r'}\ParallelNavigation{b}\ParallelEntry{beta}{Beta}{Beta}\ParallelText{end}{The next entry.}{The following entry.}'
add('flow-navigation',nav,flowbody)
arlocale=(work/'installed/examples/en-ar/languages.tex').read_text()
add('arabic-entry-headers',arlocale+r'\ParallelSetup{mode=right,header-left=\ParallelFirstEntry,header-right=\ParallelLastEntry}',r'\ParallelEntry{one}{One}{الأول}\ParallelText{body}{Text.}{نص قصير.}\clearpage\ParallelText{continued}{More.}{متابعة.}',paired=False)
add('paragraph-settings',r'\ParallelSetup{paragraph-skip=7pt,paragraph-indent=6pt}',r'\ParallelText{paragraphs}{\typeout{PT-PARAGRAPH-LEFT skip=\the\parskip;indent=\the\parindent}First paragraph.\par Second paragraph.}{\typeout{PT-PARAGRAPH-RIGHT skip=\the\parskip;indent=\the\parindent}First paragraph.\par Second paragraph.}')
add('selected-flow-navigation',nav+r'\ParallelSetup{mode=left}',flowbody,paired=False)
columnprobe=r'\makeatletter\if@twocolumn\typeout{PT-COLUMN-STATE=2}\else\typeout{PT-COLUMN-STATE=1}\fi\makeatother'
add('native-twocolumn-cover',r'\ParallelSetup{mode=left}',r'\twocolumn\ParallelFrontCover{Front}{First}'+columnprobe+body,paired=False)
add('native-onecolumn-cover',r'\ParallelSetup{mode=left,single-columns=2}',r'\onecolumn\ParallelFrontCover{Front}{First}'+columnprobe+body,paired=False)
add('rtl-prose-navigation',arlocale+nav+r'\ParallelSetup{mode=right,header-left={Field notes},footer-left={Archive}}',r'\ParallelNavigation{a}\ParallelEntry{alpha}{Alpha}{الأول}\ParallelProse{long}{Unused left side.}{'+('هذا شرح طويل يستمر على عدة صفحات مع عنوان واضح في أعلى الصفحة. '*250)+r'}',paired=False)
add('public-end-suffix',r'\ParallelSetup{profile=bound}',r'\ParallelText{flow.finish}{An earlier unit.}{An earlier unit.}\clearpage\ParallelProse{flow}{'+('One long paragraph across pages. '*200)+r'}{'+('A corresponding long paragraph. '*250)+r'}')
for name,setup,content,diagnostic in [
 ('unknown-key',r'\ParallelSetup{not-a-key=1}',body,'unknown'),
 ('invalid-position',r'\ParallelSetup{page-number-position=elsewhere}',body,'accepts only'),
 ('negative-gap',r'\ParallelSetup{column-gap=-1mm}',body,'Column gap must not be negative'),
 ('negative-divider',r'\ParallelSetup{divider-width=-1pt}',body,'Divider width must be positive'),
 ('impossible-columns',r'\ParallelSetup{geometry={inner=95mm,outer=95mm}}',body,'Content columns too narrow'),
 ('paired-two-columns',r'\ParallelSetup{single-columns=2}',body,'single-columns=2 requires one selected language'),
 ('late-setup','',r'\ParallelSetup{divider=false}'+body,'Can be used only in preamble'),
 ('unknown-role','',r'\ParallelNote[missing]{a}{One.}{Two.}','Unknown semantic role'),
 ('unknown-navigation','',r'\ParallelNavigation{missing}'+body,'Unknown navigation ID'),
 ('overflow-tab',r'\ParallelSetup{tabs=true,tab-top=290mm,tab-height=20mm}\ParallelDeclareNavigation{x}{1}{X}',r'\ParallelNavigation{x}'+body,'Navigation tab outside page')]:
 add(name,setup,content,error=diagnostic)
# Full manuscript regressions preserve scripts and flow under asymmetric geometry.
for pair in ['en-fr','en-zh-Hans','en-ar','zh-Hans-ja']:
 d=work/('bound-'+pair);shutil.copytree(work/'installed/examples'/pair,d,ignore=shutil.ignore_patterns('*.pdf','preview.png'))
 for asset in (work/'installed/assets').iterdir():
  if asset.suffix in ('.sty','.png'):shutil.copyfile(asset,d/asset.name)
 main=d/'main.tex';main.write_text(main.read_text().replace(r'\begin{document}',r'\ParallelSetup{profile=bound,divider-style={dash pattern=on 2pt off 1pt,line cap=round}}'+'\n'+r'\begin{document}'))
 cases.append(dict(name='bound-'+pair,project=d,error=None,paired=True,covers=False,margin=15))

# Two independently written documents use the same settings API through different routes.
layout={'paper':'letter','twoside':True,'inner_mm':25,'outer_mm':15,'binding_mm':2,'gap_mm':7,'font_size':10,'leading':12,'divider':{'color':'315A71','width_pt':.5,'style':'dashed'},'page_numbers':{'position':'footer-inner','numbering':'roman','prefix':'[','suffix':']'}}
data={'languages':['en','en'],'title':['A small example','A small example'],'layout':layout,'blocks':[{'id':'one','text':['First page.','A corresponding sentence.']},{'id':'two','break_before':True,'text':['Second page.','Another corresponding sentence.']}]}
export_document(validate(data),work/'source.json',work/'structured-equivalent','bilingual')
(work/'structured-equivalent/document.tex').rename(work/'structured-equivalent/main.tex')
cases.append(dict(name='structured-equivalent',project=work/'structured-equivalent',error=None,paired=True,covers=False,margin=5))
setup=r'''\newfontfamily\englishfont{Latin Modern Roman}\newfontfamily\englishfontsf{Latin Modern Sans}
\ParallelLanguages{english}{english}\definecolor{parallel.adapter.divider}{HTML}{315A71}
\ParallelSetup{mode=paired,geometry={letterpaper,twoside,inner=25mm,outer=15mm,bindingoffset=2mm},body-size=10,body-leading=12,column-gap=7mm,divider-color=parallel.adapter.divider,divider-width=.5pt,divider-style=dashed,page-number-position=footer-inner,page-numbering=roman,page-number-format={[\thepage{}]}}'''
add('native-equivalent',setup,r'\ParallelTitle{A small example}{A small example}'+body)

def geometry_check(pdf,aux):
 records={int(m[1]):tuple(int(m[i])*SCALE for i in range(2,7)) for m in re.finditer(r'\\PTPageGeometry'+r'\{(\d+)\}'*6,aux)}
 checks=[]
 for i,page in enumerate(pdf):
  lines=[d for d in page.get_drawings() if any(item[0]=='l' and abs(item[1].x-item[2].x)<.02 and abs(item[1].y-item[2].y)>100 for item in d['items'])]
  for d in lines:
   line=next(item for item in d['items'] if item[0]=='l')
   left,top,width,height,gap=records[i+1]
   checks.append(abs(line[1].x-(left+width/2))<.05 and abs(min(line[1].y,line[2].y)-top)<.05 and abs(max(line[1].y,line[2].y)-(top+height))<.05)
 return records,checks

def run(c):
 d=c['project'];proc=subprocess.run(BUILD+['main.tex'],cwd=d,capture_output=True,text=True,timeout=240)
 (d/'build.stdout').write_text(proc.stdout+proc.stderr)
 result={'case':c['name'],'compile_exit':proc.returncode}
 if c['error']:
  result.update(passed=proc.returncode!=0 and c['error'].lower() in (proc.stdout+proc.stderr).lower(),expected_error=c['error']);return result
 if proc.returncode:result.update(passed=False,error=proc.stdout[-1500:]);return result
 report=check_pdf(d/'main.pdf',c['covers'],c['paired'],c['margin'])
 warnings=[x for x in (d/'main.log').read_text().splitlines() if any(t in x for t in ('Overfull','Missing character:','undefined references','multiply defined','No hyphenation patterns'))]
 report['errors']+=warnings
 with pymupdf.open(d/'main.pdf') as pdf:
  records,lines=geometry_check(pdf,(d/'main.aux').read_text())
  report['divider_aligned_with_live_textblock']=all(lines)
  if c['name'] in ('mirrored-binding','standard-geometry','bound-profile'):
   report['odd_even_margins_mirror']=len(pdf)==2 and abs(records[1][0]-(pdf[1].rect.width-records[2][0]-records[2][2]))<.05 and abs(records[1][0]-records[2][0])>10
  if c['name'] in ('mirrored-binding','standard-geometry'):
   from PIL import Image, ImageChops
   safe=[]
   for i,page in enumerate(pdf):
    pix=page.get_pixmap(matrix=pymupdf.Matrix(8,8),alpha=False)
    im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
    box=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
    left,top,width,height,gap=records[i+1]
    safe.append(box is not None and box[0]/8>=left-.5*72/25.4 and (pix.width-box[2])/8>=page.rect.width-left-width-.5*72/25.4)
   report['full_height_binding_ink_at_8x']=all(safe)
  if c['name']=='roman-folio':
   valid=[]
   for i,page in enumerate(pdf):
    words=[w for w in page.get_text('words') if w[4]==('i' if i==0 else 'ii')]
    valid.append(len(words)==1 and words[0][1]<records[i+1][1] and ((words[0][0]<page.rect.width/2)==(i==0)))
   report['roman_folios_in_alternating_inner_header']=all(valid)
  if c['name']=='oneside-binding':report['oneside_margins_unchanged']=abs(records[1][0]-records[2][0])<.05
  if c['name']=='reading-profile':report['divider_disabled']=not lines
  if c['name']=='custom-cover-policy':report['custom_physical_parity']=len(pdf)%2==1 and len(pdf)==3
  if c['name'] in ('flow-navigation','selected-flow-navigation'):
   report['continuation_pages_keep_entry_heads']=len(pdf)>2 and all('Alpha' in page.get_text() for page in pdf[:-1])
   report['continuation_pages_keep_tabs']=all(any(w[4]=='A' and (w[0]<25 or w[0]>page.rect.width-30) for w in page.get_text('words')) for page in pdf[:-1])
  if c['name']=='paragraph-settings':
   log=(d/'main.log').read_text()
   report['paragraph_settings_reach_both_bodies']=all('PT-PARAGRAPH-'+side+' skip=7.0pt;indent=6.0pt' in log for side in ['LEFT','RIGHT'])
  if c['name'] in ('native-twocolumn-cover','native-onecolumn-cover'):
   report['actual_author_column_state_restored']=('PT-COLUMN-STATE='+('2' if c['name']=='native-twocolumn-cover' else '1')) in (d/'main.log').read_text()
  if c['name']=='rtl-prose-navigation':
   report['furniture_font_context_stable_on_rtl_continuations']=len(pdf)>2 and all('Field notes' in page.get_text() and 'Archive' in page.get_text() and any(w[4]=='A' for w in page.get_text('words')) for page in pdf)
  if c['name'] in ('bound-en-fr','bound-en-zh-Hans','bound-en-ar','bound-zh-Hans-ja'):
   source=json.loads((d/'source.json').read_text())
   physical={m[1]:int(m[2]) for m in re.finditer(r'\\PTPairPage\{([^{}]+)\}\{(\d+)\}',(d/'main.aux').read_text())}
   attached=[]
   for index,block in enumerate(source['blocks'][:-1]):
    if block.get('kind')!='heading':continue
    following=source['blocks'][index+1]
    if following.get('break_before'):continue
    suffix='.item-1' if following.get('kind')=='list' else ('.row-0' if following.get('kind')=='table' else ('.caption' if following.get('placement')=='shared' else ''))
    attached.append(physical.get(block['id'])==physical.get(following['id']+suffix) and physical.get(block['id']) is not None)
   report['headings_keep_their_following_unit']=bool(attached) and all(attached)
  if c['name']=='public-end-suffix':
   records={m[1]:int(m[2]) for m in re.finditer(r'\\PTPairPage\{([^{}]+)\}\{(\d+)\}',(d/'main.aux').read_text())}
   report['public_id_not_overwritten_by_flow_end']=records.get('flow.finish')==1
  if c['name']=='semantic-navigation':
   text=[p.get_text() for p in pdf]
   report['actual_entry_headers']=text[0].startswith('A\nAlpha\nAlpha\n') and 'A\nB\nAlpha\nBeta\n' in text[1]
  if c['name'] in ('standard-page-style','custom-page-style-with-covers'):report['author_page_style_preserved']=all(not re.search(r'^(?:X?[12])$',p.get_text(),re.M) for p in pdf)
 report['ok']=not report['errors'] and all(v for k,v in report.items() if isinstance(v,bool))
 result.update(passed=report['ok'],result=report);return result
if a.case:
 selected=set(a.case)
 unknown=selected-{c['name'] for c in cases}
 if unknown:raise SystemExit('Unknown cases: '+', '.join(sorted(unknown)))
 cases=[c for c in cases if c['name'] in selected]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,cases))
if {'structured-equivalent','native-equivalent'} <= {c['name'] for c in cases}:
 with pymupdf.open(work/'structured-equivalent/main.pdf') as x,pymupdf.open(work/'native-equivalent/main.pdf') as y:
  equal=len(x)==len(y) and all(x[i].get_pixmap().samples==y[i].get_pixmap().samples for i in range(len(x)))
 results.append({'case':'native-structured-configuration-equivalence','passed':equal})
report={'ok':all(x['passed'] for x in results),'tests':results,'visual_review':'required'}
(work/'matrix.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'ok':report['ok'],'cases':len(results),'failures':[x for x in results if not x['passed']]}))
raise SystemExit(not report['ok'])
