#!/usr/bin/env python3
"""One installed native-emission PDF case; no source graph or private fixture."""
import argparse
import hashlib
import importlib.util
import json

from matrix_support import ROOT, add_matrix_arguments, execute_matrix, initialize_output
from structured_graph_render import (
    compile_pdf, install, normalized, require_destinations, require_link, save_pages,
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_case(case, work):
    directory = work / case[0]
    directory.mkdir()
    study, renderer, env = install(directory)
    pdf = load("installed_pdf", renderer / "scripts/bilingual_pdf.py")
    api = load("installed_emission", study / "scripts/graph_emission.py")
    source = "Keep x^2 & y; return to the measurement."
    runs = [{"kind": "text", "source": "Keep "},
            {"kind": "math", "source": "x^2", "tex": "x^2"},
            {"kind": "text", "source": " & y; return to the measurement."}]
    resume, target = api.native_reference("measure-strip", 1), api.native_reference("find-material")
    start = source.index("the measurement")
    rendered = pdf.render_bound_text(source, runs=runs, text_policy="scientific-breaks",
        references=[{"start": start, "end": start + len("the measurement"),
                     "text": "the measurement", "tex": resume}],
        trusted_native=True, source_sha256=hashlib.sha256(source.encode()).hexdigest())
    calls = [api.compose_call("entry", condition="If padding is missing.", target=target,
                             outputs=["paper", "padding"], resume=resume),
             api.compose_call("entry", condition="If a label is missing.", target=target,
                             outputs=["label"], resume=resume)]
    returned = api.compose_call("exit", origin=resume, target=target,
                                outputs=["paper", "padding"], resume=resume)
    trace, paragraphs = api.EmissionTrace(), []
    for index, text in enumerate([rendered, *calls, returned,
                                "Ordinary continuation: keep all returned materials."]):
        identity = "/units/" + str(index)
        field = trace.field(identity, "en", source if index == 0 else text, text)
        paragraphs.append(trace.unit("paragraph", identity, "en",
            r"\ParallelParagraph{unit-" + str(index) + "}{" + field + "}{}"))
    body = (r"\StudyGraphNode{measure-strip}"
            r"\ParallelParagraph{step}{\StudyGraphStep{1}{Measure the strip.}}{}"
            + "".join(paragraphs[:3]) + r"\StudyGraphNode{find-material}"
            + "".join(paragraphs[3:]))
    clean, report = trace.finish({"graph-body.tex": body},
        expected_fields={"en": ["/units/" + str(index) for index in range(5)]})
    (directory / "graph-body.tex").write_text(clean["graph-body.tex"])
    (directory / "emission-report.json").write_text(json.dumps(report, indent=2))
    (directory / "graph-declarations.tex").write_text(
        r"\StudyDeclareGraphNode{measure-strip}{1}{procedure}{action}{Measure the strip}{Measure the strip}"
        r"\StudyDeclareGraphNode{find-material}{2}{procedure}{result}{Find material}{Find material}")
    template = (study / "examples/structured-graph.tex").read_text() if (study / "examples").exists() else (
        ROOT / "skills/study-notes/examples/structured-graph.tex").read_text()
    template = template.replace(r"\ParallelSelect{paired}", r"\ParallelSelect{left}")
    with compile_pdf(directory, template, env)[0] as document:
        text = normalized(" ".join(page.get_text() for page in document))
        for phrase in ("paper; padding", "If padding is missing.", "If a label is missing.",
                       "If you reached this result from",
                       "Ordinary continuation: keep all returned materials."):
            if phrase not in text:
                raise AssertionError("Missing native call prose: " + phrase)
        if text.index("If padding is missing.") >= text.index("If a label is missing."):
            raise AssertionError("Independent calls changed authored order")
        if "Step 2" in text or text.count("Step 1") < 4:
            raise AssertionError("Same-step resume was changed")
        anchors = require_destinations(document, (directory / "main.aux").read_text(),
            ("graph:measure-strip", "graph:measure-strip:step:1", "graph:find-material"))
        for key in ("graph:measure-strip:step:1", "graph:find-material"):
            require_link(document, anchors[key][2])
        save_pages(document, directory)
        return {"case": case[0], "passed": True, "errors": [], "pages": len(document)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    from pathlib import Path
    parser.add_argument("--output", type=Path, required=True)
    add_matrix_arguments(parser)
    args = parser.parse_args()
    work = initialize_output(args.output, args.resume)
    return execute_matrix([("bound-native",)], lambda case: run_case(case, work),
                          work, args, "graph-emission-render")


if __name__ == "__main__":
    raise SystemExit(main())
