#!/usr/bin/env python3
"""Crop and rasterize the seven original native tutorial diagrams.

Compile examples/shared/illustrations.tex with XeLaTeX into an ignored directory,
then pass its PDF here. Only diagram ink, labels and a small margin are retained.
"""
import argparse
import json
from pathlib import Path
import pymupdf

NAMES = ("layout-anatomy","pipeline-en","pipeline-fr","pipeline-zh-Hans",
         "pipeline-ja","pipeline-ar","pipeline-he")

def export(pdf_path, output):
    with pymupdf.open(pdf_path) as pdf:
        if len(pdf) != len(NAMES):
            raise ValueError("Expected exactly seven illustration pages")
        clips = []
        for page in pdf:
            rects = [item["rect"] for item in page.get_drawings()]
            rects += [pymupdf.Rect(block[:4]) for block in page.get_text("blocks") if block[4].strip()]
            if not rects:
                raise ValueError("An illustration page is empty")
            bounds = pymupdf.Rect(rects[0])
            for rect in rects[1:]:
                bounds |= rect
            clips.append((bounds+(-8,-8,8,8)) & page.rect)
        output.mkdir(parents=True,exist_ok=True)
        records=[]
        for name,page,clip in zip(NAMES,pdf,clips):
            pix=page.get_pixmap(dpi=180,clip=clip,alpha=False)
            pix.save(output/(name+".png"))
            records.append({"file":name+".png","width":pix.width,"height":pix.height})
        return records

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps({"images":export(args.pdf,args.output)}))

if __name__=="__main__":
    main()
