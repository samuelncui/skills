#!/usr/bin/env python3
"""JSONL handoff, multipage paired chunks, and native continuation regressions."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import pymupdf
from matrix_support import add_matrix_arguments, initialize_output, execute_matrix, run_command
from test_translation_pdf_jsonl import make_master, PDF, TRANSLATION
import bilingual_pdf as pdf

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
add_matrix_arguments(parser)
args = parser.parse_args()
work = initialize_output(args.output, args.resume)
cases = ["reviewed-en-zh", "unequal-multipage", "selected-left", "selected-right", "continuation-reserve", "heading-continuation"]
BUILD = ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error",
         "-latexoption=-no-shell-escape"]


def compact(text):
    return "".join(text.split()).replace("\u00ad", "")


def heading_case(directory):
    shutil.copyfile(PDF / "assets/paralleltext.sty", directory / "paralleltext.sty")
    data={"languages":["en","zh-Hans"],"title":["Test","测试"],
          "layout":{"font_size":10.5,"leading":14},
          "blocks":[{"id":"one","text":["Text","文字"]}]}
    locale=pdf.tex_parts(data,"bilingual")[1]
    native=r"\documentclass[10pt,twoside]{article}"+"\n"+r"\usepackage{paralleltext}"+"\n"+locale+r"""
\begin{document}
\noindent Near-bottom fixture.\par
\vspace*{\dimexpr\textheight-60pt\relax}
\ParallelProseSection{section}{FLOWHEADING}{流动标题}
\begin{ParallelProseGroup}{parent}
\ParallelProseChunk{first}{LEFTFIRST This paragraph should start with its heading. It continues with enough ordinary text to cross several lines and exercise widow and club protection in both physical columns.}{开始中文。这一段应当跟随标题开始。它包含足够多的文字，能够在窄栏中排成多行，并检验两种文字在页面底部能否同时开始。下一位读者应当在标题后立即看到正文，而不是在下一页寻找。}
\end{ParallelProseGroup}
\typeout{HEADING-AFTER=\ifPTAfterHeading true\else false\fi}
\ParallelProse{after}{AFTERLEFT}{后续段落。}
\end{document}
"""
    (directory/"document.tex").write_text(native)
    result=run_command(BUILD+["document.tex"],cwd=directory,timeout=60)
    (directory/"compile.log").write_text(result.stdout)
    if result.returncode:return {"case":"heading-continuation","passed":False,"error":result.stdout[-5000:]}
    qa=pdf.check_pdf(directory/"document.pdf",False,True,12)
    checks={"heading_state_consumed":"HEADING-AFTER=false" in (directory/"document.log").read_text()}
    found={}
    with pymupdf.open(directory/"document.pdf") as doc:
        for i,page in enumerate(doc):
            for marker in ("FLOWHEADING","LEFTFIRST","开始中文"):
                rects=page.search_for(marker)
                if rects:found[marker]=(i,rects[0])
            page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(directory/("page-"+str(i+1)+".png"))
        checks["heading_and_actual_glyphs_same_page"]=len(found)==3 and len({v[0] for v in found.values()})==1
        checks["near_bottom_heading_moves_with_both_sides"]=len(found)==3 and found["FLOWHEADING"][0]==1
    return {"case":"heading-continuation","passed":qa["ok"] and all(checks.values()),"checks":checks,"result":qa}


def run(name):
    directory = work / name
    directory.mkdir(exist_ok=True)
    if name == "heading-continuation":
        return heading_case(directory)
    if name == "continuation-reserve":
        shutil.copyfile(PDF / "assets/paralleltext.sty", directory / "paralleltext.sty")
        native = r"""\documentclass[10pt,twoside]{article}
\usepackage{paralleltext}
\ParallelSetup{body-size=10,body-leading=12,paragraph-indent=8mm,paragraph-skip=7pt}
\let\SavedReserve\PTReserveSpace
\renewcommand\PTReserveSpace[1]{\typeout{CHUNK-RESERVE=\the\dimexpr#1\relax}\SavedReserve{#1}}
\let\SavedEnsure\ensurevspace
\renewcommand\ensurevspace[1]{\typeout{CHUNK-ENSURE=\the\dimexpr#1\relax}\SavedEnsure{#1}}
\begin{document}
\noindent Top.\par\vspace*{.70\textheight}
\begin{ParallelProseGroup}{parent}
\ParallelProseChunk{first}{LONE\newline LTWO\newline LTHREE}{RONE}
\ParallelProseChunk{next}{LFOUR}{RFOUR}
\end{ParallelProseGroup}
\ParallelProse{after}{LAFTER}{RAFTER}
\end{document}
"""
        (directory / "document.tex").write_text(native)
        result = run_command(BUILD + ["document.tex"], cwd=directory, timeout=60)
        (directory / "compile.log").write_text(result.stdout)
        if result.returncode:
            return {"case": name, "passed": False, "error": result.stdout[-5000:]}
        log = (directory / "document.log").read_text()
        qa = pdf.check_pdf(directory / "document.pdf", False, True, 12)
        checks = {"actual_two_line_reserve": "CHUNK-RESERVE=24.0pt" in log,
                  "actual_sync_reserve": "CHUNK-ENSURE=24.0pt" in log}
        with pymupdf.open(directory / "document.pdf") as doc:
            found = {}
            for i, page in enumerate(doc):
                for marker in ("LONE", "LTHREE", "LFOUR", "LAFTER", "RONE", "RFOUR", "RAFTER"):
                    rects = page.search_for(marker)
                    if rects:
                        found[marker] = (i, rects[0])
                page.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3)).save(directory / ("page-" + str(i+1) + ".png"))
            checks["all_markers_once"] = len(found) == 7 and all(sum(len(p.search_for(m)) for p in doc) == 1 for m in found)
            checks["available_page_space_used"] = all(value[0] == 0 for value in found.values())
            if len(found) == 7:
                checks["no_continuation_paragraph_gap"] = 10 < found["LFOUR"][1].y0 - found["LTHREE"][1].y0 < 14
                checks["continuation_indent_removed"] = 21 < found["LONE"][1].x0 - found["LFOUR"][1].x0 < 24
                checks["normal_indent_restored"] = abs(found["LONE"][1].x0 - found["LAFTER"][1].x0) < .1
                checks["paired_start_same_page_y"] = all(found[l][0] == found[r][0] and abs(found[l][1].y0 - found[r][1].y0) < .1
                    for l, r in (("LONE", "RONE"), ("LFOUR", "RFOUR"), ("LAFTER", "RAFTER")))
        return {"case": name, "passed": qa["ok"] and all(checks.values()), "checks": checks, "result": qa}

    master, data = make_master(directory, stress=name == "unequal-multipage")
    mode = name.removeprefix("selected-") if name.startswith("selected-") else "bilingual"
    out = directory / "project"
    command = [sys.executable, str(PDF / "scripts/bilingual_pdf.py"), "render", str(master),
               "--translation-skill", str(TRANSLATION), "--output", str(out), "--mode", mode]
    result = run_command(command, cwd=directory, timeout=90)
    (directory / "render-command.log").write_text(result.stdout)
    if result.returncode:
        return {"case": name, "passed": False, "error": result.stdout[-5000:]}
    qa = json.loads(result.stdout)
    preserved = [json.loads(line) for line in (out / "translation-source.jsonl").read_text().splitlines()]
    checks = {"full_master_preserved": preserved == [data["document"]] + data["units"]}
    with pymupdf.open(out / "document.pdf") as doc:
        checks["multiple_pages"] = len(doc) >= 2 if name == "unequal-multipage" else True
        for i, page in enumerate(doc):
            page.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3)).save(out / ("page-" + str(i+1) + ".png"))
        # Source English can hyphenate at line wraps. Chinese is compared exactly
        # after whitespace normalization, across pages and independent of line wraps.
        chinese = "".join(u["target"] for u in data["units"])
        extracted = "".join(p.get_text() for p in doc)
        if mode != "left":
            expected = "".join(c for c in chinese if "\u4e00" <= c <= "\u9fff")
            actual = "".join(c for c in extracted if "\u4e00" <= c <= "\u9fff")
            checks["all_chinese_text_in_order"] = actual == expected
        if mode != "right":
            expected = "".join(u["source"] for u in data["units"])
            words = [word for unit in data["units"] for word in re.findall(r"[A-Za-z]+", unit["source"])]
            actual = re.findall(r"[A-Za-z]+", re.sub(r"-\s*\n\s*", "", extracted))
            checks["all_english_words_in_order"] = actual == words
        if name == "unequal-multipage":
            aux = (out / "document.aux").read_text()
            # At least one child must really flow across a page, not just whole
            # chunks moved together. The canonical QA independently checks starts.
            positions = {}
            for ident, body in re.findall(r"\\newlabel\{(pt-internal:[^}]+)\}\{([^\n]+)", aux):
                match = re.search(r"\{[^{}]*\}\{(\d+)\}", body)
                if match:
                    positions[ident] = int(match[1])
            checks["natural_break_inside_chunk"] = any(
                positions.get("pt-internal:pair-1.chunk-" + str(i) + "-" + side) !=
                positions.get("pt-internal:pair-1.chunk-" + str(i) + "-" + side + "-finish")
                for i in range(1, 4) for side in ("L", "R"))
    return {"case": name, "passed": qa["ok"] and all(checks.values()), "checks": checks, "result": qa}


raise SystemExit(execute_matrix(cases, run, work, args, "translation-pdf", name=lambda case: case))
