"""Pixel-coordinate checks for the actual rendered example geometry."""
import re
from pathlib import Path
import pymupdf

SCALE=72/(72.27*65536)

def quote_geometry(pdf_path,languages,ident='quotation'):
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
            edge=max(c['bbox'][2] for c in chars) if language in ('ar','he') else min(c['bbox'][0] for c in chars)
            # Standard article 10pt quote has a 25 TeX-point inset on both edges.
            inset=(slot+width-edge) if language in ('ar','he') else edge-slot
            ok=abs(start[0]-slot)<.2 and abs(inset-25*72/72.27)<1
            result.append({'side':side,'language':language,'slot_x':slot,'measured_slot_x':start[0],'quote_start_inset':inset,'ok':ok})
    return {'ok':all(x['ok'] for x in result),'sides':result}

def article_features(pdf_path):
    """Check the actual complete article, not only isolated helper fixtures."""
    path = Path(pdf_path)
    aux = path.with_suffix('.aux').read_text()
    pages = {m[1]: int(m[2]) for m in re.finditer(r'\\newlabel\{pt-internal:([^{}]+)\}\{\{[^{}]*\}\{(\d+)\}', aux)}
    crossed = all(pages.get('continuing-prose-' + side + '-finish', 0) > pages.get('continuing-prose-' + side, 0) for side in ('L', 'R'))
    resumed = pages.get('figures-and-references-L') == pages.get('figures-and-references-R') and pages.get('figures-and-references-L', 0) >= max(pages.get('continuing-prose-' + side + '-finish', 0) for side in ('L', 'R'))
    captions = pages.get('shared-layout.caption-L') == pages.get('shared-layout.caption-R') and pages.get('shared-layout.caption-L', 0) > 0
    with pymupdf.open(path) as pdf:
        wide = [(i + 1, rect) for i, page in enumerate(pdf) for image in page.get_images() for rect in page.get_image_rects(image[0]) if rect.width > 400]
        shared = len(wide) == 1 and wide[0][1].x0 < pdf[0].rect.width / 2 < wide[0][1].x1
        captions = captions and bool(wide) and pages.get('shared-layout.caption-L') == wide[0][0]
        narrow=[(i,image) for i,page in enumerate(pdf) for image in page.get_image_info(hashes=True) if 100<image['bbox'][2]-image['bbox'][0]<300]
        narrow.sort(key=lambda item:item[1]['bbox'][0])
        localized=len(narrow)==2 and narrow[0][0]==narrow[1][0] and narrow[0][1]['digest']!=narrow[1][1]['digest']
        if localized:
            left,right=narrow[0][1]['bbox'],narrow[1][1]['bbox'];center=pdf[narrow[0][0]].rect.width/2
            localized=left[2]<center<right[0] and abs(left[1]-right[1])<.2
    return {'ok': crossed and resumed and captions and shared and localized, 'both_paragraphs_cross_pages': crossed,
            'following_pair_resynchronizes': resumed, 'paired_captions_with_photo': captions, 'one_full_width_photo': shared,
            'distinct_localized_images_in_aligned_columns':localized}
