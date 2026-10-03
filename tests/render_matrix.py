#!/usr/bin/env python3
"""Render isolated installed-skill fixtures. Mechanical results are not visual sign-off."""
import argparse,concurrent.futures,copy,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
work=args.output.resolve()
if work.exists():raise SystemExit('Choose a new test directory')
work.mkdir(parents=True)
shutil.copytree(ROOT/'examples',work/'inputs')
for skill in ['bilingual-pdf','course-guide-quick-reference']:
 shutil.copytree(ROOT/'skills'/skill,work/skill,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(ROOT/'tests/fixtures',work/'fixtures')
base=json.loads((work/'fixtures/garden-en-fr.json').read_text());base['layout']={'covers':True};cases=[];case_sources={}
for name in ['en-fr','en-zh-Hans','en-ar','zh-Hans-ja']:
 for mode in ['bilingual','left','right']:
  source=work/'inputs/bilingual-pdf'/name
  cases.append((name+'-'+mode,json.loads((source/'source.json').read_text()),mode,0));case_sources[name+'-'+mode]=source
rtlrefs=json.loads((work/'fixtures/garden-en-ar.json').read_text());rtlrefs['blocks'] += [{'id':'intro-ref','kind':'reference','target':'check','text':['See the introduction','انظر المقدمة']},{'id':'average-ref','kind':'reference','target':'average','text':['See the average','انظر المتوسط']}]
for mode in ['bilingual','left','right']:cases.append(('rtl-references-'+mode,rtlrefs,mode,0))
rev=json.loads((work/'inputs/bilingual-pdf/en-ar/source.json').read_text());rev['languages'].reverse();rev['title'].reverse()
for b in rev['blocks']:
 b['text'].reverse()
 for field in ('headers','rows'):
  if field in b:b[field].reverse()
cases.append(('ar-en-reversed',rev,'bilingual',0));case_sources['ar-en-reversed']=work/'inputs/bilingual-pdf/en-ar'
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
for name in ['en-fr','en-zh-Hans','en-ar','zh-Hans-ja']:
 source=work/'inputs/bilingual-pdf'/name;article=json.loads((source/'source.json').read_text())
 passage=next(b['text'] for b in article['blocks'] if b['id']=='notebook-prose')
 flow=copy.deepcopy(article);flow['blocks']=[{'id':'long-prose','kind':'paragraph','flow':'breakable','text':[(x+' ')*18 for x in passage]},{'id':'after-flow','text':passage}]
 cases.append(('flow-'+name,flow,'bilingual',0));case_sources['flow-'+name]=source
 captions={'en':'Shared photograph.','fr':'Photographie partagée.','zh-Hans':'共用照片。','ar':'صورة مشتركة.','ja':'共有写真。'}
 wide=copy.deepcopy(article);wide['blocks']=[{'id':'photo','kind':'figure','placement':'shared','image':'images/footpath.png','text':[captions[l] for l in article['languages']]},{'id':'after-photo','text':passage}]
 cases.append(('shared-photo-'+name,wide,'bilingual',0));case_sources['shared-photo-'+name]=work/'inputs/bilingual-pdf/en-zh-Hans'

def stage_input(name,data,source,collection=False):
 directory=work/'generated-inputs'/name;directory.mkdir(parents=True)
 blocks=data['blocks'] if not collection else [b for t in data['topics'] for b in t['guide_blocks']+t['quick'].get('blocks',[])]
 for block in blocks:
  if block.get('kind')=='figure':
   relative=Path(block['image']);target=directory/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/relative,target)
 ip=directory/'source.json';ip.write_text(json.dumps(data,ensure_ascii=False));return ip

def run(c):
 name,data,mode,expected=c;ip=stage_input(name,data,case_sources.get(name,work/'fixtures/course-en-fr'))
 proc=subprocess.run([sys.executable,str(work/'bilingual-pdf/scripts/bilingual_pdf.py'),'render',str(ip),'--output',str(work/name),'--mode',mode],cwd=work,capture_output=True,text=True,timeout=240)
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
 if proc.returncode==0 and name in [x+'-bilingual' for x in ['en-fr','en-zh-Hans','en-ar','zh-Hans-ja']]:
  from layout_checks import quote_geometry
  quote=quote_geometry(work/name/'document.pdf',data['languages']);r['quote_geometry']=quote
  if not quote['ok']:proc.returncode=4
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
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,cases))
course=json.loads((work/'fixtures/course-en-fr/source.json').read_text())
wrapped=copy.deepcopy(course);wrapped['topics'][0]['title']=['Average speed over a complete trip with measured distance and elapsed time','Vitesse moyenne sur un trajet complet avec une distance et une durée mesurées']
arabic={'languages':['en','ar'],'guide_title':['Measurements — Guide','دليل القياسات'],'quick_title':['Measurements — Quick Reference','مرجع سريع للقياسات'],'labels':{'meaning':['Meaning','المعنى'],'rule':['Rule','القاعدة'],'checks':['Checks','التحقق'],'guide':['Guide','الدليل'],'see':['See','انظر']},'topics':[{'id':'mean','title':['Mean','المتوسط'],'guide_blocks':[copy.deepcopy(rtlrefs['blocks'][3])],'quick':{'meaning':['The sum divided by the count.','المجموع مقسوما على العدد.'],'rule':['For two values, add them and divide by two.','اجمع القيمتين ثم اقسم المجموع على اثنين.'],'checks':['Use comparable values and consistent units.','استخدم قيما قابلة للمقارنة ووحدات متسقة.']},'aliases':[{'id':'average','title':['Average','المعدل']}]}],'keywords':[{'id':'measurements','title':['Measurements','القياسات'],'targets':['mean']}]}
flexible=copy.deepcopy(course)
flexible['topics'][0]['quick']={'blocks':[{'id':'speed.quick-summary','text':course['topics'][0]['quick']['meaning']},{'id':'speed.quick-figure','kind':'figure','image':'trip.png','text':['An original trip diagram.','Un schéma original du trajet.']},{'id':'speed.quick-related','kind':'reference','target':'entry.'+course['topics'][1]['id'],'text':['Another concept','Une autre notion']}]}
course_cases=[('flexible-course-blocks',flexible,'bilingual'),('isolated-course',course,'bilingual'),('wrapped-course-links',wrapped,'bilingual'),('rtl-course',arabic,'bilingual'),('rtl-course-right',arabic,'right')]
def run_course(case):
 name,data,mode=case;ip=stage_input(name,data,work/'fixtures/course-en-fr',collection=True)
 proc=subprocess.run([sys.executable,str(work/'course-guide-quick-reference/scripts/course_documents.py'),str(ip),'--output',str(work/name),'--mode',mode],cwd=work,capture_output=True,text=True,timeout=240)
 valid_json=True
 try:result=json.loads(proc.stdout)
 except json.JSONDecodeError:result={'error':proc.stdout+proc.stderr};valid_json=False
 return {'case':name,'expected_exit':0,'actual_exit':proc.returncode,'passed':proc.returncode==0 and valid_json and result.get('ok') is True,'result':result}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results.extend(pool.map(run_course,course_cases))
report={'ok':all(x['passed'] for x in results),'tests':results,'visual_review':'required','language_review':'required'}
(work/'matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'ok':report['ok'],'cases':len(results),'failures':[x for x in results if not x['passed']]},ensure_ascii=False))
sys.exit(0 if report['ok'] else 1)
