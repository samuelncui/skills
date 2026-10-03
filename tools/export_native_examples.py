#!/usr/bin/env python3
"""Maintain editable LaTeX beside the four article sources and their assets."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import validate,tex_parts
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check',action='store_true')
args=parser.parse_args()
errors=[]
for name in ('en-fr','en-zh-Hans','en-ar','zh-Hans-ja'):
    directory=ROOT/'examples/bilingual-pdf'/name
    data=validate(json.loads((directory/'source.json').read_text()))
    images={}
    expected={}
    for block in data['blocks']:
        if block.get('kind')!='figure':continue
        source=(directory/block['image']).resolve()
        if not source.is_relative_to(directory.resolve()) or not source.is_file():
            raise ValueError('Missing or out-of-project figure: '+block['image'])
        # These are reviewed public source assets, not arbitrary user uploads.
        # Runtime export separately strips image metadata in its fresh project.
        relative=Path(block['image'])
        if relative.parts[0]!='images':relative=Path('images')/relative
        images[block['id']]=relative.as_posix()
        expected[relative.as_posix()]=source.read_bytes()
    main,locale,body=tex_parts(data,'bilingual',image_names=images)
    expected.update({'main.tex':main.encode(),'languages.tex':locale.encode(),'content.tex':body.encode()})
    for filename,content in expected.items():
        target=directory/filename
        if args.check:
            if not target.exists() or target.read_bytes()!=content:errors.append(str(target.relative_to(ROOT)))
        elif not target.exists() or target.read_bytes()!=content:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
print(json.dumps({'ok':not errors,'stale':errors}))
raise SystemExit(bool(errors))
