#!/usr/bin/env python3
"""Maintain editable LaTeX beside the four article sources and their assets."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import validate,tex_parts,figure_images,resolve_image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check',action='store_true')
args=parser.parse_args()
errors=[]
for name in ('en-fr','en-zh-Hans','en-ar','zh-Hans-ja'):
    directory=ROOT/'skills/bilingual-pdf/examples'/name
    data=validate(json.loads((directory/'source.json').read_text()))
    images={}
    expected={}
    for block in data['blocks']:
        if block.get('kind')!='figure':continue
        # Shared assets belong to the owning skill, not each language edition.
        images[block['id']]=figure_images(block)
        for image in images[block['id']]:
            resolve_image(directory/'source.json',image,ROOT/'skills/bilingual-pdf/assets')
    main,locale,body=tex_parts(data,'bilingual',image_names=images)
    main=main.replace(r'\usepackage{paralleltext}',r'\makeatletter\def\input@path{{../../assets/}}\makeatother'+'\n'+r'\usepackage{paralleltext}'+'\n'+r'\graphicspath{{../../assets/}}')
    expected.update({'main.tex':main.encode(),'languages.tex':locale.encode(),'content.tex':body.encode()})
    for filename,content in expected.items():
        target=directory/filename
        if args.check:
            if not target.exists() or target.read_bytes()!=content:errors.append(str(target.relative_to(ROOT)))
        elif not target.exists() or target.read_bytes()!=content:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
print(json.dumps({'ok':not errors,'stale':errors}))
raise SystemExit(bool(errors))
