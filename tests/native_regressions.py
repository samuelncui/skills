#!/usr/bin/env python3
"""Focused real-XeLaTeX regressions, separate from fast unit discovery.

Use --output DIR; the common runner supports bounded batches and --resume.
Fixtures are original public API examples; no private manuscripts are required.
"""
from __future__ import annotations
import argparse
import os
import re
from pathlib import Path
import pymupdf as fitz
from matrix_support import ROOT, add_matrix_arguments, initialize_output, execute_matrix, run_command

PREAMBLE = r"\documentclass{article}\usepackage{studytools}" + "\n"
SMALL = r"\ParallelSetup{geometry={paperwidth=148mm,paperheight=110mm,margin=12mm},body-size=9,body-leading=11}" + "\n"

def document(preamble, body):
    return PREAMBLE + preamble + "\n" + r"\begin{document}" + "\n" + body + "\n" + r"\end{document}" + "\n"

def fixtures():
    sorting = r"""
\StudyDeclareConcept{b}{b}{B}{B}{}{\ParallelText{body-b}{Third.}{Third.}}
\StudyDeclareConcept{ab}{ab}{Ab}{Ab}{}{\ParallelText{body-ab}{Second.}{Second.}}
\StudyDeclareConcept{a}{a}{A}{A}{}{\ParallelText{body-a}{First.}{First.}}
\StudyDeclareAlias{alias}{a}{Alias}{Alias}{a}
\renewcommand\StudyLookupGroupHook[3]{\typeout{REGRESSION-GROUP: #1}}
"""
    punctuation = ["leaf_one", "leaf.two", "leaf:three", "leaf-four"]
    leaves = "\n".join(
        r"\StudyDeclareLeaf{"+ident+r"}{Method}{Method}{\ParallelParagraph{body-"+str(i)+r"}{Do the check.}{Do the check.}}"
        for i, ident in enumerate(punctuation))
    leaves += "\n" + r"\ParallelSetup{header-left=\ParallelFirstEntry,header-right=\ParallelLastEntry}"
    lifecycle = r"\ParallelSection{start}{Flow test}{Flow test}" + "\n"
    sentence = "A bounded paragraph keeps its own pair together while the next independent pair may move to another page. "
    lifecycle += "\n".join(r"\ParallelParagraph{p"+str(i)+"}{"+sentence*2+"}{"+sentence+"}" for i in range(12))
    lifecycle += "\n" + r"\ParallelSubsection*{star}{Unnumbered target}{Unnumbered target}\ParallelParagraph{after-star}{Done.}{Done.}"
    lifecycle += "\n" + r"\ParallelSubsection{numbered}{Numbered target}{Numbered target}\ParallelParagraph{after-numbered}{Done.}{Done.}\typeout{REGRESSION-COUNTER: \thesubsection}"
    prose = "This entry continues with an independently authored explanation, keeping the next semantic start aligned. "
    long_body = r"\ParallelParagraph{long-body}{" + prose*20 + "}{" + prose*13 + "}"
    short_header = SMALL + r"""
\ParallelSetup{paragraph-flow=breakable,header-left=\ParallelFirstEntry,header-right=\ParallelLastEntry,entry-continuation-left={ CONTINUED},document-version={edition-alpha},document-status={reviewed}}
\StudyDeclareConcept[header-left={SHORT},header-right={SHORT}]{entry}{entry}{A complete explanatory title}{A complete explanatory title}{}{""" + long_body + "}\n"
    huge_header = SMALL + r"""
\ParallelSetup{header-left=\ParallelFirstEntry,entry-header-width=12mm,entry-header-max-lines=2}
\StudyDeclareConcept{entry}{entry}{One two three four five six seven eight nine ten eleven twelve}{Title}{}{\ParallelParagraph{body}{A short body.}{A short body.}}
"""
    huge_keep = SMALL + r"\ParallelSetup{paragraph-flow=keep}" + "\n"
    return [
        ("lookup-prefix-order", document(sorting, r"\StudyPrintQuickReference"), None),
        ("decision-id-punctuation", document(leaves, r"\StudyPrintDecisionTree{leaf_one}\ParallelText{refs}{"+r"\StudyDecisionReference{leaf:three}"+r"}{"+r"\StudyDecisionReference{leaf-four}"+r"}"), None),
        ("paragraph-heading-lifecycle", document(SMALL, lifecycle), None),
        ("short-header-continuation", document(short_header, r"\StudyPrintQuickReference\ParallelText{metadata}{\ParallelDocumentVersion}{\ParallelDocumentStatus}"), None),
        ("oversized-header-rejected", document(huge_header, r"\StudyPrintQuickReference"), "Entry header exceeds configured line limit"),
        ("oversized-keep-rejected", document(huge_keep, long_body), "PAIR TOO TALL"),
    ]

def run_case(case, work):
    name, source, expected_error = case
    path = work/name
    path.mkdir(exist_ok=True)
    (path/"main.tex").write_text(source)
    env = dict(os.environ)
    env["TEXINPUTS"] = str(ROOT/"skills/study-notes/assets")+"//:"+str(ROOT/"skills/bilingual-pdf/assets")+"//:"+env.get("TEXINPUTS","")+":"
    outputs = []
    for turn in (1,2):
        proc = run_command(["xelatex","-no-shell-escape","-interaction=nonstopmode","-halt-on-error","main.tex"],
                           cwd=path, env=env, timeout=50)
        outputs.append(proc.stdout+proc.stderr)
        (path/f"compile-{turn}.log").write_text(outputs[-1])
        if proc.returncode:
            if expected_error and expected_error in outputs[-1]:
                return {"case":name,"passed":True,"expected_error":expected_error,"passes":turn}
            return {"case":name,"passed":False,"errors":["Unexpected compiler failure"],"log":f"{name}/compile-{turn}.log"}
    if expected_error:
        return {"case":name,"passed":False,"errors":["Expected error was not raised: "+expected_error]}
    errors = []
    log = outputs[-1]
    if re.search(r"Overfull \\[hv]box|Missing character:|undefined references", log):
        errors.append("Layout, glyph, or reference diagnostic")
    pdf = fitz.open(path/"main.pdf")
    text = "\n".join(page.get_text() for page in pdf)
    if name == "lookup-prefix-order":
        if re.findall(r"REGRESSION-GROUP: ([A-Za-z]+)",log) != ["a","alias","ab","b"]:
            errors.append("Prefix/equal-key ordering does not respect sort key then group")
    elif name == "decision-id-punctuation":
        for ident in ("leaf_one","leaf.two","leaf:three","leaf-four"):
            if ident not in text:
                errors.append("Documented ID not preserved: "+ident)
    elif name == "paragraph-heading-lifecycle":
        if len(pdf)<2 or "REGRESSION-COUNTER: 1.1" not in log:
            errors.append("Independent paragraphs failed to paginate, or starred subsection changed numbering")
        if "Unnumbered target" not in text or "Numbered target" not in text:
            errors.append("Subsection text is missing")
    elif name == "short-header-continuation":
        if len(pdf)<2 or "CONTINUED" not in text:
            errors.append("Continuation header is missing")
        if "edition-alpha" not in text or "reviewed" not in text:
            errors.append("Independent document version/status was not retained")
        if "A complete explanatory title" not in text or "SHORT" not in text:
            errors.append("Short header replaced or lost full body title")
        if "CONTINUED" in pdf[0].get_text():
            errors.append("First page incorrectly marked continued")
    result = {"case":name,"passed":not errors,"errors":errors,"pages":len(pdf),"passes":2}
    pdf.close()
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    add_matrix_arguments(parser)
    args=parser.parse_args()
    work=initialize_output(args.output,args.resume)
    return execute_matrix(fixtures(),lambda case:run_case(case,work),work,args,"native-regressions")

if __name__=="__main__":
    raise SystemExit(main())
