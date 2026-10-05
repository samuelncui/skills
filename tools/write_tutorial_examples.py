#!/usr/bin/env python3
"""Maintain the self-hosted usage-guide sources; no build or network side effects."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
texts=json.loads((ROOT/'tools/tutorial-content.json').read_text())
PAIRS=[('en','fr'),('en','zh-Hans'),('en','ar'),('en','he'),('zh-Hans','ja')]
def rich(text,language):
    if language not in ('ar','he'):return text
    pieces=[];last=0
    pattern=r'[A-Za-z][A-Za-z0-9_./=:-]*(?:[ ]+[A-Za-z0-9_./=:-]+)*|[0-9]+(?:[.][0-9]+)*(?:[ ]*mm)?'
    for match in re.finditer(pattern,text):
        if match.start()>last:pieces.append({'text':text[last:match.start()],'direction':'rtl'})
        pieces.append({'text':match.group(),'direction':'ltr'});last=match.end()
    if last<len(text):pieces.append({'text':text[last:],'direction':'rtl'})
    if not any(x['direction']=='ltr' for x in pieces):return text
    # Whitespace is retained beside a substantive run, never emitted as an empty text value.
    out=[]
    for piece in pieces:
        if not piece['text'].strip():
            if out:out[-1]['text']+=piece['text']
            else:continue
        else:out.append(piece)
    return {'runs':out}
for languages in PAIRS:
    left,right=languages
    def pair(key):return [rich(texts[l][key],l) for l in languages]
    blocks=[
      {'id':'choose-route','kind':'heading','text':pair('choose')},
      {'id':'opening','text':pair('intro')},
      {'id':'routes-table','kind':'table','text':pair('tableCaption'),
       'headers':[[rich(x,l) for x in texts[l]['headers']] for l in languages],'rows':[[[rich(x,l) for x in row] for row in texts[l]['rows']] for l in languages]},
      {'id':'page-flow','kind':'heading','text':pair('flowHeading')},
      {'id':'flow-options','text':pair('flowIntro')},
      {'id':'continuing-prose','flow':'breakable','text':pair('long')},
      {'id':'figures-and-references','kind':'heading','text':pair('imagesHeading')},
      {'id':'shared-layout','kind':'figure','placement':'shared','image':'layout-anatomy.png','text':pair('wideCaption')},
      {'id':'localized-pipeline','kind':'figure','image':['pipeline-'+l+'.png' for l in languages],'text':pair('localCaption')},
      {'id':'quotation','kind':'quote','text':pair('quote')},
      {'id':'column-width','kind':'equation','math':r'w=\frac{W-g}{2}','text':pair('equationText')},
      {'id':'check-and-deliver','kind':'heading','text':pair('checkHeading')},
      {'id':'checks','kind':'list','text':[[rich(x,l) for x in texts[l]['checks']] for l in languages]},
      {'id':'back-to-flow','kind':'reference','target':'page-flow','text':pair('back')}
    ]
    doc={'languages':list(languages),'title':[texts[l]['title'] for l in languages],
         'layout':{'covers':False,'font_size':10,'paragraph_flow':'breakable'},'blocks':blocks}
    p=ROOT/'skills/bilingual-pdf/examples'/('-'.join(languages));p.mkdir(parents=True,exist_ok=True)
    (p/'source.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
print('Wrote five self-hosted JSON examples.')
