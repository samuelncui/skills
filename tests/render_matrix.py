#!/usr/bin/env python3
"""Render isolated installed-skill fixtures. Mechanical results are not visual sign-off."""
import argparse,copy,json,shutil,sys,hashlib,tempfile,subprocess,os,datetime
from matrix_support import add_matrix_arguments, initialize_output, execute_matrix, run_command, repeat_text, first_sentence
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reuse-rendered',type=Path,help='Reuse verified compiled inputs only within an unchanged TeX/font installation; engine version is checked, external font/package bytes are not; all assertions rerun');add_matrix_arguments(p);args=p.parse_args()
work=initialize_output(args.output,args.resume)
for skill in ['bilingual-pdf']:
 shutil.copytree(ROOT/'skills'/skill,work/skill,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
shutil.copytree(ROOT/'tests/fixtures',work/'fixtures',dirs_exist_ok=True)
base=json.loads((work/'fixtures/garden-en-fr.json').read_text());base['layout']={'covers':True};cases=[];case_sources={}
for name in ['en-fr','en-zh-Hans','en-ar','en-he','zh-Hans-ja']:
 for mode in ['bilingual','left','right']:
  source=work/'bilingual-pdf/examples'/name
  cases.append((name+'-'+mode,json.loads((source/'source.json').read_text()),mode,0));case_sources[name+'-'+mode]=work/'bilingual-pdf/examples/shared'
rtlrefs=json.loads((work/'fixtures/garden-en-ar.json').read_text());rtlrefs['blocks'] += [{'id':'intro-ref','kind':'reference','target':'check','text':['See the introduction','انظر المقدمة']},{'id':'average-ref','kind':'reference','target':'average','text':['See the average','انظر المتوسط']}]
for mode in ['bilingual','left','right']:cases.append(('rtl-references-'+mode,rtlrefs,mode,0))
rev=json.loads((work/'bilingual-pdf/examples/en-ar/source.json').read_text());rev['languages'].reverse();rev['title'].reverse()
for b in rev['blocks']:
 b['text'].reverse()
 if isinstance(b.get('image'),list):b['image'].reverse()
 for field in ('headers','rows'):
  if field in b:b[field].reverse()
cases.append(('ar-en-reversed',rev,'bilingual',0));case_sources['ar-en-reversed']=work/'bilingual-pdf/examples/shared'
no=copy.deepcopy(base);no['layout']={'covers':False,'paper':'letter'};cases.append(('letter-no-covers',no,'bilingual',0))
multi=copy.deepcopy(base);multi['blocks']=[]
for i in range(70):
 multi['blocks'].append({'id':f'block-{i}','text':['Check the length, then record the unit. '*5,'Vérifiez la longueur, puis notez l’unité utilisée. '*7]})
multi['blocks'].insert(0,{'id':'uneven-list','kind':'list','text':[['First step.','Second step.'],['La première étape doit être expliquée assez longuement pour occuper plusieurs lignes dans la colonne de droite.','Deuxième étape.']]})
cases.append(('multipage-uneven',multi,'bilingual',0))
refs=copy.deepcopy(base);refs['blocks'] += [{'id':'list-parent-ref','kind':'reference','target':'steps','text':['See the steps','Voir les étapes']},{'id':'equation-parent-ref','kind':'reference','target':'average','text':['See the average','Voir la moyenne']}]
for mode in ['bilingual','left','right']:cases.append(('parent-references-'+mode,refs,mode,0))
ov=copy.deepcopy(base);ov['blocks']=[{'id':'oversize','text':['A long explanation. '*3000,'Une longue explication. '*3000]}];cases.append(('oversized-block',ov,'bilingual',3))
glyph=copy.deepcopy(base);glyph['blocks'][0]['text'][0]='Missing glyph 🦄';cases.append(('missing-glyph',glyph,'bilingual',2))
for name in ['en-fr','en-zh-Hans','en-ar','en-he','zh-Hans-ja']:
 source=work/'bilingual-pdf/examples'/name;article=json.loads((source/'source.json').read_text())
 passage=next(b['text'] for b in article['blocks'] if b['id']=='continuing-prose')
 flow=copy.deepcopy(article);flow['blocks']=[{'id':'long-prose','kind':'paragraph','flow':'breakable','text':[repeat_text(x) for x in passage]},{'id':'after-flow','text':[first_sentence(x) for x in passage]}]
 cases.append(('flow-'+name,flow,'bilingual',0));case_sources['flow-'+name]=work/'bilingual-pdf/examples/shared'
 captions={'en':'Shared photograph.','fr':'Photographie partagée.','zh-Hans':'共用照片。','ar':'صورة مشتركة.','ja':'共有写真。','he':'תרשים משותף.'}
 wide=copy.deepcopy(article);wide['blocks']=[{'id':'photo','kind':'figure','placement':'shared','image':'layout-anatomy.png','text':[captions[l] for l in article['languages']]},{'id':'after-photo','text':[first_sentence(x) for x in passage]}]
 cases.append(('shared-photo-'+name,wide,'bilingual',0));case_sources['shared-photo-'+name]=work/'bilingual-pdf/examples/shared'

def stage_input(name,data,source):
 directory=work/'generated-inputs'/name;directory.mkdir(parents=True,exist_ok=True)
 blocks=data['blocks']
 for block in blocks:
  if block.get('kind')=='figure':
   for image in (block['image'] if isinstance(block['image'],list) else [block['image']]):
    relative=Path(image);target=directory/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/relative,target)
 ip=directory/'source.json';ip.write_text(json.dumps(data,ensure_ascii=False));return ip

_CACHE_ENGINE=None
def reuse_rendered(name,data,mode,ip):
 global _CACHE_ENGINE
 if args.reuse_rendered is None:return None
 previous=args.reuse_rendered.resolve()/name
 evidence=args.reuse_rendered.resolve()/'case-results'/(name+'.json')
 previous_input=args.reuse_rendered.resolve()/'generated-inputs'/name/'source.json'
 if not evidence.is_file() or not previous_input.is_file():return None
 outcome=json.loads(evidence.read_text())
 if outcome.get('status')!='passed' or outcome.get('expected_exit')!=0 or outcome.get('passed') is not True:return None
 if previous_input.read_bytes()!=ip.read_bytes():return None
 if not all((previous/filename).is_file() for filename in ('result.json','document.pdf','document.aux','document.log')):return None
 result=json.loads((previous/'result.json').read_text())
 if not result.get('ok') or result.get('mode')!=mode:return None
 if _CACHE_ENGINE is None:
  _CACHE_ENGINE=run_command(['xelatex','--version'],cwd=work,timeout=10).stdout.splitlines()[0]
 if result.get('environment',{}).get('engine')!=_CACHE_ENGINE:return None
 digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
 if result.get('renderer_sha256')!=digest(work/'bilingual-pdf/scripts/bilingual_pdf.py'):return None
 if result.get('sha256')!=digest(previous/'document.pdf'):return None
 if set(result.get('template_sha256',{}))!={'paralleltext.sty'}:return None
 for filename,wanted in result['template_sha256'].items():
  if wanted!=digest(work/'bilingual-pdf/assets'/filename):return None
 # Re-export all current TeX, language, package, license and image inputs.
 # Only byte-identical exported source trees can reuse a compiled artifact.
 sys.path.insert(0,str(work/'bilingual-pdf/scripts'))
 from bilingual_pdf import validate,export_document,check_pdf
 with tempfile.TemporaryDirectory(prefix='cache-probe-',dir=work) as temporary:
  exported=Path(temporary)/'exported'
  export_document(validate(copy.deepcopy(data)),ip,exported,mode)
  for path in exported.rglob('*'):
   if path.is_file():
    old=previous/path.relative_to(exported)
    if not old.is_file() or old.read_bytes()!=path.read_bytes():return None
 if os.environ.get('FORCE_SOURCE_DATE')=='1' and os.environ.get('SOURCE_DATE_EPOCH'):
  import pymupdf
  wanted=datetime.datetime.fromtimestamp(int(os.environ['SOURCE_DATE_EPOCH']),datetime.timezone.utc).strftime('D:%Y%m%d%H%M%S')
  with pymupdf.open(previous/'document.pdf') as pdf:
   if not pdf.metadata.get('creationDate','').startswith(wanted):return None
 artifacts={filename:digest(previous/filename) for filename in ('document.pdf','document.aux','document.log','result.json')}
 shutil.copytree(previous,work/name)
 if any(digest(work/name/filename)!=wanted for filename,wanted in artifacts.items()):raise AssertionError('Copied cache artifact checksum mismatch')
 layout=data.get('layout',{})
 margin=min(layout.get('inner_mm',layout.get('margin_mm',16 if layout.get('profile')=='bound' else 18)),layout.get('outer_mm',layout.get('margin_mm',16 if layout.get('profile')=='bound' else 18)))
 checked=check_pdf(work/name/'document.pdf',layout.get('covers',False),mode=='bilingual',margin)
 checked['errors'] += [line for line in (work/name/'document.log').read_text().splitlines() if any(token in line for token in ('Missing character:','Overfull','undefined references','multiply defined','No hyphenation patterns'))]
 checked['ok']=not checked['errors']
 result.update(checked,pdf=str(work/name/'document.pdf'),reused_verified_build=True,
               reuse={'source_directory':str(previous),'source_artifact_sha256':artifacts,
                      'source_case_sha256':digest(evidence),'input_sha256':digest(ip),
                      'engine':_CACHE_ENGINE,'current_exported_sources_byte_identical':True,
                      'aux_log_hashes_captured_at':'reuse validation, not original compilation',
                      'toolchain_prerequisite':'unchanged TeX and font installation required; engine version checked; external font/package byte identity not independently verified'})
 (work/name/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 return subprocess.CompletedProcess([],0 if result['ok'] else 4,json.dumps(result), '')

def run(c):
 name,data,mode,expected=c
 if (work/name).exists():
  attempts=work/'interrupted-cases';attempts.mkdir(exist_ok=True)
  index=1
  while (attempts/(name+'-'+str(index))).exists():index+=1
  (work/name).rename(attempts/(name+'-'+str(index)))
 ip=stage_input(name,data,case_sources.get(name,work/'fixtures'))
 proc=reuse_rendered(name,data,mode,ip) if expected==0 else None
 if proc is None:proc=run_command([sys.executable,str(work/'bilingual-pdf/scripts/bilingual_pdf.py'),'render',str(ip),'--output',str(work/name),'--mode',mode],cwd=work,capture_output=True,text=True,timeout=105)
 valid_json=True
 try:r=json.loads(proc.stdout)
 except json.JSONDecodeError:r={'error':proc.stdout+proc.stderr};valid_json=False
 if name.startswith('parent-references-') and proc.returncode==0:
  import re
  aux=(work/name/'document.aux').read_text()
  labels={m[1]:int(m[2]) for m in re.finditer(r'\\newlabel\{([^{}]+)\}\{\{[^{}]*\}\{(\d+)\}',aux)}
  matches=labels.get('steps')==labels.get('pt-internal:steps.item-1-L') and labels.get('average')==labels.get('pt-internal:average-L')
  import pymupdf as fitz
  with fitz.open(work/name/'document.pdf') as pdf:
   links=[link for page in pdf for link in page.get_links()]
   expected_links=4 if mode=='bilingual' else 2
   matches=matches and len(links)==expected_links and all(link.get('page')==labels['steps']-1 for link in links)
  if not matches:r['parent_reference_error']='Parent destinations or first-child page records differ';proc.returncode=4
 if proc.returncode==0 and name in [x+'-bilingual' for x in ['en-fr','en-zh-Hans','en-ar','en-he','zh-Hans-ja']]:
  from layout_checks import quote_geometry, article_features
  quote=quote_geometry(work/name/'document.pdf',data['languages']);r['quote_geometry']=quote
  features=article_features(work/name/'document.pdf');r['article_features']=features
  if not quote['ok'] or not features['ok']:proc.returncode=4
 if proc.returncode==0 and name in [x+'-'+side for x in ['en-fr','en-zh-Hans','en-ar','en-he','zh-Hans-ja'] for side in ['left','right']]:
  import hashlib,pymupdf
  from PIL import Image
  route=next(b for b in data['blocks'] if b['id']=='localized-pipeline')['image']
  wanted=route[0 if mode=='left' else 1];unwanted=route[1 if mode=='left' else 0]
  def image_digest(filename):
   with Image.open(work/'bilingual-pdf/examples/shared'/filename) as image:return hashlib.md5(image.convert('RGB').tobytes()).digest()
  with pymupdf.open(work/name/'document.pdf') as pdf:digests=[image['digest'] for page in pdf for image in page.get_image_info(hashes=True)]
  r['selected_language_uses_its_localized_image']=image_digest(wanted) in digests and image_digest(unwanted) not in digests
  if not r['selected_language_uses_its_localized_image']:proc.returncode=4
 if proc.returncode==0 and name.startswith('flow-'):
  import re
  aux=(work/name/'document.aux').read_text();page_labels={m[1]:int(m[2]) for m in re.finditer(r'\\newlabel\{pt-internal:([^{}]+)\}\{\{[^{}]*\}\{(\d+)\}',aux)}
  crossed=all(page_labels.get('long-prose-'+side+'-finish',0)>page_labels.get('long-prose-'+side,0) for side in ['L','R'])
  r['both_paragraphs_cross_pages']=crossed
  if not crossed:proc.returncode=4
 if proc.returncode==0 and name.startswith('shared-photo-'):
  import pymupdf
  with pymupdf.open(work/name/'document.pdf') as pdf:
   rects=[rect for page in pdf for im in page.get_images() for rect in page.get_image_rects(im[0])]
   shared=len(rects)==1 and rects[0].x0<pdf[0].rect.width/2<rects[0].x1 and rects[0].width>400
  r['one_full_width_image']=shared
  if not shared:proc.returncode=4
 return {'case':name,'expected_exit':expected,'actual_exit':proc.returncode,'passed':proc.returncode==expected and valid_json and (expected!=0 or r.get('ok') is True),'result':r}

raise SystemExit(execute_matrix(cases,run,work,args,'render'))
