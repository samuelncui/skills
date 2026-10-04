#!/usr/bin/env python3
"""Build a scoped Guide and alphabetically navigable companion Quick Reference."""
import argparse,copy,importlib.util,json,os,re,subprocess,sys,shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
class InputError(ValueError): pass
_renderer=None

def configure_renderer(skill_path=None):
    """Use an explicitly discovered installed skill; never guess or download it."""
    global _renderer
    _renderer=None
    value=skill_path or os.environ.get('BILINGUAL_PDF_SKILL')
    if not value:
        raise InputError('Install bilingual-pdf alongside this skill, then pass its installed directory with --bilingual-skill or BILINGUAL_PDF_SKILL. No dependency was downloaded.')
    root=Path(value).expanduser().resolve()
    required=[root/'SKILL.md',root/'scripts/bilingual_pdf.py',root/'assets/paralleltext.sty']
    if any(not p.is_file() or not p.resolve().is_relative_to(root) for p in required):
        raise InputError('Invalid bilingual-pdf skill directory: expected SKILL.md, scripts/bilingual_pdf.py and assets/paralleltext.sty')
    if not re.search(r'^name:\s*bilingual-pdf\s*$',required[0].read_text(),re.M):
        raise InputError('The selected dependency must be the bilingual-pdf skill')
    spec=importlib.util.spec_from_file_location('_course_bilingual_pdf',required[1])
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    api=('InputError','validate','preflight','write_project','compile_project','figure_images','resolve_image')
    if getattr(module,'RENDERER_API_VERSION',None)!=1 or any(not callable(getattr(module,name,None)) for name in api):
        raise InputError('Incompatible bilingual-pdf renderer. Update both skills from the same repository revision (renderer API 1 required).')
    _renderer=module
    return root

def renderer_call(name,*args,**kwargs):
    if _renderer is None:configure_renderer()
    try:return getattr(_renderer,name)(*args,**kwargs)
    except _renderer.InputError as error:raise InputError(str(error)) from error

def validate(*args,**kwargs):return renderer_call('validate',*args,**kwargs)
def preflight(*args,**kwargs):return renderer_call('preflight',*args,**kwargs)
def write_project(*args,**kwargs):return renderer_call('write_project',*args,**kwargs)
def compile_project(*args,**kwargs):return renderer_call('compile_project',*args,**kwargs)

def pair(value,name):
    if not isinstance(value,list) or len(value)!=2 or any(not isinstance(x,str) or not x.strip() for x in value):raise InputError(name+' requires two nonempty strings')
    return value

def prepare(data):
    if not isinstance(data,dict):raise InputError('Collection must be an object')
    base={'languages':data.get('languages'),'layout':data.get('layout',{})}
    guide={**base,'title':pair(data.get('guide_title'),'guide_title'),'blocks':[]}
    quick={**base,'title':pair(data.get('quick_title'),'quick_title'),'blocks':[]}
    topics=data.get('topics');ids=set();aliases=set()
    if not isinstance(topics,list) or not topics:raise InputError('topics must be nonempty')
    labels=data.get('labels')
    if not isinstance(labels,dict):raise InputError('Provide localized labels')
    for field in ['guide','see']:pair(labels.get(field),'labels '+field)
    for t in topics:
        if not isinstance(t,dict):raise InputError('Topic must be an object')
        ident=t.get('id')
        if not isinstance(ident,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,49}',ident) or ident in ids:raise InputError('Topic IDs must be unique')
        ids.add(ident);pair(t.get('title'),'topic title')
        if 'sort_key' in t and not isinstance(t['sort_key'],str):raise InputError('sort_key must be a string')
        if not isinstance(t.get('aliases',[]),list):raise InputError('aliases must be a list')
        if not isinstance(t.get('see_also',[]),list) or any(not isinstance(x,str) for x in t.get('see_also',[])):raise InputError('see_also must be a list of IDs')
        guide['blocks'].append({'id':'topic.'+ident,'kind':'heading','text':t['title']})
        blocks=t.get('guide_blocks')
        if not isinstance(blocks,list) or not blocks:raise InputError('Each topic needs authored guide_blocks')
        guide['blocks'].extend(copy.deepcopy(blocks))
        q=t.get('quick')
        if not isinstance(q,dict):raise InputError('Each topic needs quick sections')
        if 'blocks' in q:
            if not isinstance(q['blocks'],list) or not q['blocks']:raise InputError('quick.blocks must be nonempty')
        else:
            for field in ['meaning','rule','checks']:
                pair(q.get(field),'quick '+field);pair(labels.get(field),'labels '+field)
        for alias in t.get('aliases',[]):
            if not isinstance(alias,dict):raise InputError('Alias must be an object')
            aid=alias.get('id')
            if not isinstance(aid,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,49}',aid) or aid in aliases or aid in ids:raise InputError('Invalid alias ID')
            aliases.add(aid);pair(alias.get('title'),'alias title')
            if 'sort_key' in alias and not isinstance(alias['sort_key'],str):raise InputError('Alias sort_key must be a string')
    if ids & aliases:raise InputError('Alias ID collides with a topic')
    for t in topics:
        if any(x not in ids for x in t.get('see_also',[])):raise InputError('Unknown see_also topic')
        if len(set(t.get('see_also',[])))!=len(t.get('see_also',[])):raise InputError('Duplicate see_also topic')
    keywords=data.get('keywords',[])
    if not isinstance(keywords,list):raise InputError('keywords must be a list')
    seen=set()
    for keyword in keywords:
        if not isinstance(keyword,dict):raise InputError('Keyword must be an object')
        kid=keyword.get('id')
        if not isinstance(kid,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,29}',kid) or kid in seen:raise InputError('Invalid or duplicate keyword ID')
        seen.add(kid);pair(keyword.get('title'),'keyword title')
        targets=keyword.get('targets')
        if not isinstance(targets,list) or not targets or any(not isinstance(x,str) or x not in ids for x in targets):raise InputError('Keyword targets must name existing topics')
        if len(set(targets))!=len(targets):raise InputError('Duplicate keyword target')
        if 'sort_key' in keyword and not isinstance(keyword['sort_key'],str):raise InputError('Keyword sort_key must be text')
    if any(t.get('see_also') for t in topics):pair(labels.get('see_also'),'labels see_also')
    probe=[]
    for t in topics:
        probe.append({'id':'entry.'+t['id'],'text':t['title']})
        probe.append({'id':'entry.'+t['id']+'.guide','text':t['title']})
        probe.extend(copy.deepcopy(t['quick'].get('blocks',[])))
        for alias in t.get('aliases',[]):probe.append({'id':'alias.'+alias['id'],'text':alias['title']})
    for keyword in keywords:probe.append({'id':'keyword.'+keyword['id'],'text':keyword['title']})
    validate({**base,'title':quick['title'],'blocks':probe})
    validate(guide)
    if base['layout'].get('page_numbers',{}).get('numbering')=='gobble':raise InputError('Printed course references need page labels; use page_numbers.position=none to hide running folios')
    return guide,quick,topics

def build(input_path,output,mode,stem):
    data=validate(json.loads(input_path.read_text(encoding='utf-8')))
    environment=preflight(data)
    if not environment.get('ok'):raise RuntimeError(json.dumps(environment))
    write_project(data,input_path,output,mode,stem=stem)
    result=compile_project(data,output,mode,environment,stem=stem)
    if not result.get('ok'):raise RuntimeError(json.dumps(result))
    return result

def stage_figures(guide,input_path,out,prefix="guide",asset_root=None):
    """Keep editable inputs portable without occupying reserved output folders."""
    for block in guide['blocks']:
        if block.get('kind')=='figure':
            staged=[]
            images=renderer_call('figure_images',block)
            for index,image in enumerate(images):
                source=renderer_call('resolve_image',input_path,image,asset_root)
                relative=Path('input-assets')/prefix/(Path(block['id'])/(('left' if index==0 else 'right')+source.suffix.lower()) if len(images)==2 else Path(block['id'])/('image'+source.suffix.lower()))
                target=out/relative
                if not target.resolve().is_relative_to(out.resolve()):raise InputError('Figure output escapes collection directory')
                if target.exists() or target.is_symlink():raise InputError('Figure staging would overwrite an existing file')
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,target);staged.append(relative.as_posix())
            block['image']=staged if isinstance(block['image'],list) else staged[0]


def unit_pages(aux):
    """Return absolute PDF pages and native printed folios as separate values."""
    physical={m[1]:int(m[2]) for m in re.finditer(r'\\PTPairPage\{([^{}]+)\}\{(\d+)\}',aux)}
    folios={m[1]:m[2] for m in re.finditer(r'\\newlabel\{pt-internal:([^{}]+)-L\}\{\{[^{}]*\}\{([^{}]*)\}',aux)}
    return physical,folios

def verify_guide_links(aux,page_heights,remote,destinations,mode):
    """Check logical blocks; a wrapped PDF link may have several annotations."""
    positions={m[1]:(int(m[2]),int(m[3])) for m in re.finditer(r'\\zref@newlabel\{pt-internal:([^{}]+)\}\{\\posx\{(\d+)\}\\posy\{(\d+)\}\}',aux)}
    physical,_=unit_pages(aux)
    pages={ident+'-'+side:page-1 for ident,page in physical.items() for side in ['L','R']}
    widths={m[1]:int(m[2]) for m in re.finditer(r'\\PairMeasure\{([^{}]+)\}\{(\d+)\}',aux)}
    # XeTeX positions use scaled TeX points; PDF coordinates use 72 points/inch.
    scale=72/(72.27*65536);used=set();logical=0
    for topic,destination in destinations.items():
        ident='entry.'+topic+'.guide'
        for side in (['L','R'] if mode=='bilingual' else ['L']):
            key=ident+'-'+side
            if key not in pages or key+'-start' not in positions or key+'-end' not in positions or ident not in widths:raise RuntimeError('Missing Guide-link position evidence: '+key)
            source_page=pages[key]
            if not 0<=source_page<len(page_heights):raise RuntimeError('Invalid Guide-link source page: '+key)
            x,y=positions[key+'-start'];end=positions[key+'-end'][1]
            left=x*scale;right=(x+widths[ident])*scale
            top=page_heights[source_page]-y*scale;bottom=page_heights[source_page]-end*scale
            found=[]
            for i,link in enumerate(remote):
                rect=link['rect'];cx=(rect[0]+rect[2])/2;cy=(rect[1]+rect[3])/2
                if link['source_page']==source_page and left-2<=cx<=right+2 and top-6<=cy<=bottom+6:found.append(i)
            if not found:raise RuntimeError('Missing logical Guide link: '+key)
            if any(remote[i]['file']!='notes.pdf' or remote[i]['page']!=destination-1 for i in found):raise RuntimeError('Wrong logical Guide destination: '+key)
            if used.intersection(found):raise RuntimeError('Ambiguous overlapping Guide-link blocks: '+key)
            used.update(found);logical+=1
    if len(used)!=len(remote):raise RuntimeError('Unexpected remote link outside generated Guide blocks')
    return logical

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--mode',choices=['bilingual','left','right'],default='bilingual')
    parser.add_argument('--bilingual-skill',type=Path,help='Installed bilingual-pdf directory; defaults to BILINGUAL_PDF_SKILL')
    parser.add_argument('--asset-root',type=Path,help='Bounded image directory (default: input directory)')
    args=parser.parse_args()
    try:
        configure_renderer(args.bilingual_skill)
        data=json.loads(args.input.read_text());guide,quick,topics=prepare(data)
        out=args.output.resolve()
        if out.exists():raise InputError('Choose a new output directory')
        out.mkdir(parents=True)
        stage_figures(guide,args.input,out,prefix='notes',asset_root=args.asset_root)
        gi=out/'notes-input.json';gi.write_text(json.dumps(guide,ensure_ascii=False,indent=2)+'\n')
        gr=build(gi,out,args.mode,'notes')
        aux=(out/'notes.aux').read_text()
        pages,folios=unit_pages(aux)
        by_id={t['id']:t for t in topics};entries=[]
        for t in topics:
            entries.append((t.get('sort_key',t['title'][0]).casefold(),'topic',t))
            for a in t.get('aliases',[]):entries.append((a.get('sort_key',a['title'][0]).casefold(),'alias',{**a,'target':t['id']}))
        for k in data.get('keywords',[]):entries.append((k.get('sort_key',k['title'][0]).casefold(),'keyword',k))
        labels=data.get('labels')
        if not isinstance(labels,dict):raise InputError('Provide localized labels for meaning, rule, checks, guide and see')
        for field in ['guide','see']:pair(labels.get(field),'labels '+field)
        for _,kind,t in sorted(entries,key=lambda x:(x[0],x[1],x[2]['id'])):
            ident={'topic':'entry.','alias':'alias.','keyword':'keyword.'}[kind]+t['id']
            quick['blocks'].append({'id':ident,'kind':'heading','text':t['title']})
            if kind=='keyword':
                for i,target_id in enumerate(t['targets']):
                    target=by_id[target_id];quick['blocks'].append({'id':ident+'.target-'+str(i+1),'kind':'reference','target':'entry.'+target_id,'text':[target['title'][j] for j in range(2)]})
                continue
            if kind=='alias':
                target=by_id[t['target']];quick['blocks'].append({'id':ident+'.see','kind':'reference','target':'entry.'+target['id'],'text':[labels['see'][i]+': '+target['title'][i] for i in range(2)]});continue
            if 'blocks' in t['quick']:
                quick['blocks'].extend(copy.deepcopy(t['quick']['blocks']))
            else:
                for field in ['meaning','rule','checks']:
                    quick['blocks'].append({'id':ident+'.'+field,'text':[labels[field][i]+': '+t['quick'][field][i] for i in range(2)]})
            page=pages.get('topic.'+t['id'])
            if not page:raise RuntimeError('Missing generated Guide page for '+t['id'])
            quick['blocks'].append({'id':ident+'.guide','kind':'reference','target':'topic.'+t['id'],'file':'notes.pdf','page':page,'page_label':folios['topic.'+t['id']],'text':[labels['guide'][i]+': '+t['title'][i] for i in range(2)]})
            for index,target_id in enumerate(t.get('see_also',[]),1):
                target=by_id[target_id];quick['blocks'].append({'id':ident+'.related-'+str(index),'kind':'reference','target':'entry.'+target_id,'text':[labels['see_also'][i]+': '+target['title'][i] for i in range(2)]})
        validate(quick);stage_figures(quick,args.input,out,prefix='quick-reference',asset_root=args.asset_root);qi=out/'quick-reference-input.json';qi.write_text(json.dumps(quick,ensure_ascii=False,indent=2)+'\n')
        qr=build(qi,out,args.mode,'quick-reference')
        import pymupdf as fitz
        qpdf=fitz.open(out/'quick-reference.pdf');remote=[]
        for index,page in enumerate(qpdf):
            for link in page.get_links():
                if link.get('kind')==fitz.LINK_GOTOR:
                    remote.append({'source_page':index,'file':link.get('file'),'page':link.get('page',-1),'rect':tuple(link['from'])})
        logical=verify_guide_links((out/'quick-reference.aux').read_text(),[p.rect.height for p in qpdf],remote,{t['id']:pages['topic.'+t['id']] for t in topics},args.mode)
        result={'ok':True,'stage':'review-candidate','guide':gr,'quick':qr,'guide_links':logical,'guide_link_annotations':len(remote),'factual_review':'pending','language_review':'pending','visual_review':'required'}
        (out/'collection-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));return 0
    except (InputError,ValueError,OSError,RuntimeError,subprocess.TimeoutExpired,ImportError) as e:print(json.dumps({'ok':False,'error':str(e)}));return 1

if __name__=='__main__':sys.exit(main())
