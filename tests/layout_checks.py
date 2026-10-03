"""Pixel-coordinate checks for the actual rendered example geometry."""
import re
from pathlib import Path
import pymupdf

SCALE=72/(72.27*65536)

def quote_geometry(pdf_path,languages,ident='prompt'):
    path=Path(pdf_path);text=path.with_suffix('.aux').read_text()
    positions={m[1]:(int(m[2])*SCALE,int(m[3])*SCALE) for m in re.finditer(r'\\zref@newlabel\{pt-internal:([^{}]+)\}\{\\posx\{(\d+)\}\\posy\{(\d+)\}\}',text)}
    pages={m[1]:int(m[2])-1 for m in re.finditer(r'\\newlabel\{pt-internal:([^{}]+-[LR])\}\{\{[^{}]*\}\{(\d+)\}',text)}
    widths={m[1]:int(m[2])*SCALE for m in re.finditer(r'\\PairMeasure\{([^{}]+)\}\{(\d+)\}',text)}
    result=[]
    with pymupdf.open(path) as pdf:
        left=positions[ident+'-L-start'][0];width=widths[ident]
        for side,language in zip(['L','R'],languages):
            key=ident+'-'+side;page=pdf[pages[key]];start=positions[key+'-start'];end=positions[key+'-end']
            slot=left if side=='L' else page.rect.width-left-width
            top=page.rect.height-start[1];bottom=page.rect.height-end[1]
            chars=[c for block in page.get_text('rawdict')['blocks'] if block['type']==0 for line in block['lines'] for span in line['spans'] for c in span['chars'] if c['c'].strip() and top-2<c['origin'][1]<bottom+2 and slot-2<c['origin'][0]<slot+width+2]
            if not chars:raise AssertionError('No quote glyphs found: '+key)
            edge=max(c['bbox'][2] for c in chars) if language=='ar' else min(c['bbox'][0] for c in chars)
            # Standard article 10pt quote has a 25 TeX-point inset on both edges.
            inset=(slot+width-edge) if language=='ar' else edge-slot
            ok=abs(start[0]-slot)<.2 and abs(inset-25*72/72.27)<1
            result.append({'side':side,'language':language,'slot_x':slot,'measured_slot_x':start[0],'quote_start_inset':inset,'ok':ok})
    return {'ok':all(x['ok'] for x in result),'sides':result}

def article_features(pdf_path):
    """Check the actual complete article, not only isolated helper fixtures."""
    path = Path(pdf_path)
    aux = path.with_suffix('.aux').read_text()
    pages = {m[1]: int(m[2]) for m in re.finditer(r'\\newlabel\{pt-internal:([^{}]+)\}\{\{[^{}]*\}\{(\d+)\}', aux)}
    crossed = all(pages.get('long-prose-' + side + '-finish', 0) > pages.get('long-prose-' + side, 0) for side in ('L', 'R'))
    resumed = pages.get('notebook-L') == pages.get('notebook-R') and pages.get('notebook-L', 0) >= max(pages.get('long-prose-' + side + '-finish', 0) for side in ('L', 'R'))
    captions = pages.get('shared-photo.caption-L') == pages.get('shared-photo.caption-R') and pages.get('shared-photo.caption-L', 0) > 0
    with pymupdf.open(path) as pdf:
        wide = [(i + 1, rect) for i, page in enumerate(pdf) for image in page.get_images() for rect in page.get_image_rects(image[0]) if rect.width > 400]
        shared = len(wide) == 1 and wide[0][1].x0 < pdf[0].rect.width / 2 < wide[0][1].x1
        captions = captions and bool(wide) and pages.get('shared-photo.caption-L') == wide[0][0]
    return {'ok': crossed and resumed and captions and shared, 'both_paragraphs_cross_pages': crossed,
            'following_pair_resynchronizes': resumed, 'paired_captions_with_photo': captions, 'one_full_width_photo': shared}
