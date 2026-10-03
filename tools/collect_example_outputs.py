#!/usr/bin/env python3
"""Stage the six curated PDFs and previews using their co-located example paths."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARTICLES=('en-fr','en-zh-Hans','en-ar','zh-Hans-ja')
COURSE='course-guide-quick-reference/three-concepts'
PDFS={**{f'bilingual-pdf/{name}/document.pdf':f'{name}-bilingual/document.pdf' for name in ARTICLES},
      f'{COURSE}/notes.pdf':'native-course-example/notes.pdf',
      f'{COURSE}/quick-reference.pdf':'native-course-example/quick-reference.pdf'}
INPUTS=[f'bilingual-pdf/{name}/source.json' for name in ARTICLES]+[f'{COURSE}/source.md',f'{COURSE}/source-map.json']
PREVIEWS={**{f'bilingual-pdf/{name}/preview.png':(f'{name}-bilingual/document.pdf',0) for name in ARTICLES},
          f'{COURSE}/notes-preview.png':('native-course-example/notes.pdf',0),
          f'{COURSE}/quick-reference-preview.png':('native-course-example/quick-reference.pdf',0)}
TRANSIENT={'.aux','.log','.out','.toc','.xdv','.fls','.fdb_latexmk','.synctex.gz'}
RUNTIME=['skills/bilingual-pdf/scripts/bilingual_pdf.py','skills/bilingual-pdf/assets/paralleltext.sty',
         'skills/bilingual-pdf/requirements.txt','skills/course-guide-quick-reference/scripts/course_documents.py']

def bounded_file(base,relative):
    path=(base/relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():raise ValueError('Missing or out-of-bundle example: '+relative)
    return path

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def source_names(source_root):
    # The co-located project is the source; generated outputs and transient builds
    # never feed their own provenance hash or leak into the public allowlist.
    required=['examples/'+name for name in INPUTS]+RUNTIME
    generated=set(PDFS)|set(PREVIEWS)|{'MANIFEST.json'}
    for p in sorted((source_root/'examples').rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(source_root/'examples').as_posix()
        if rel in generated or any(p.name.endswith(x) for x in TRANSIENT) or p.suffix=='.pdf':continue
        if any(x.startswith('.') or x=='__pycache__' for x in Path(rel).parts):continue
        if p.suffix not in {'.json','.md','.tex','.sty','.png','.jpg','.jpeg'} and p.name not in {'LICENSE','Makefile'}:continue
        required.append('examples/'+rel)
    return sorted(set(required))

def collect_examples(matrix,output,source_root=ROOT,native_matrix=None):
    if output.exists():raise ValueError('Choose a new example output directory')
    if json.loads((matrix/'matrix.json').read_text()).get('ok') is not True:raise ValueError('Only a passing matrix can produce curated examples')
    if native_matrix is not None and json.loads((native_matrix/'matrix.json').read_text()).get('ok') is not True:raise ValueError('Only a passing native matrix can produce curated examples')
    copies=[(bounded_file(native_matrix if target.startswith(COURSE+'/') and native_matrix is not None else matrix,source),Path(target)) for target,source in PDFS.items()]
    hashes={name:digest(bounded_file(source_root,name)) for name in source_names(source_root)}
    output.mkdir(parents=True);records=[]
    for source,relative in copies:
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        records.append({'path':relative.as_posix(),'sha256':digest(target)})
    manifest={'source_hashes':hashes,'files':records,'previews':[],
              'regeneration':'See examples/README.md. Source, PDF and preview files share each example folder; byte identity requires the same toolchain and fixed clock.'}
    (output/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return records

def check_examples(output,source_root=ROOT):
    manifest=json.loads((output/'MANIFEST.json').read_text())
    if {x['path'] for x in manifest['files']}!=set(PDFS):raise ValueError('Example manifest inventory mismatch')
    preview_records=manifest.get('previews',[])
    if preview_records and {x['path'] for x in preview_records}!=set(PREVIEWS):raise ValueError('Example preview inventory mismatch')
    source_paths={name.removeprefix('examples/') for name in manifest['source_hashes'] if name.startswith('examples/')}
    expected=set(PDFS)|{x['path'] for x in preview_records}|source_paths|{'MANIFEST.json'}
    actual={p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    if actual-expected:raise ValueError('Unexpected file in curated examples: '+', '.join(sorted(actual-expected)))
    for record in manifest['files']+preview_records:
        if digest(bounded_file(output,record['path']))!=record['sha256']:raise ValueError('Example output hash mismatch: '+record['path'])
    if set(manifest['source_hashes'])!=set(source_names(source_root)):raise ValueError('Example source inventory changed; regenerate curated outputs')
    for name,expected_hash in manifest['source_hashes'].items():
        if digest(bounded_file(source_root,name))!=expected_hash:raise ValueError('Example source changed; regenerate curated outputs: '+name)
    return len(manifest['files'])

def make_previews(matrix,output,native_matrix=None):
    if output.exists():raise ValueError('Choose a new preview directory')
    import pymupdf
    output.mkdir(parents=True);records=[]
    for target,(relative,page_number) in PREVIEWS.items():
        base=native_matrix if target.startswith(COURSE+'/') and native_matrix is not None else matrix
        destination=output/target;destination.parent.mkdir(parents=True,exist_ok=True)
        with pymupdf.open(bounded_file(base,relative)) as pdf:
            pdf[page_number].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(destination)
        records.append({'path':target,'sha256':digest(destination)})
    return records

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',type=Path);parser.add_argument('--native-matrix',type=Path)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--previews',type=Path)
    parser.add_argument('--check',action='store_true',help='Verify the co-located outputs, sources and optional preview records')
    args=parser.parse_args()
    if args.check:count=check_examples(args.output)
    else:
        if args.matrix is None:parser.error('--matrix is required unless --check is set')
        count=len(collect_examples(args.matrix,args.output,native_matrix=args.native_matrix))
        if args.previews:
            records=make_previews(args.matrix,args.previews,args.native_matrix)
            path=args.output/'MANIFEST.json';manifest=json.loads(path.read_text());manifest['previews']=records;path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'ok':True,'pdfs':count,'preview_images':len(PREVIEWS) if args.previews and not args.check else 0}))

if __name__=='__main__':main()
