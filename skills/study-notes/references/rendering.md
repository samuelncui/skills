# Build native study forms

Study-notes renders through native LaTeX. Notes and lookup manuscripts are native; the optional [structured graph importer](structured-graph.md) generates decision fragments for the same native components. `source-map.json` and output manifests are provenance/QA records, not a second document-authoring interface.

## Resolve installed packages

Discover both skills through the host's supported skill listing. Set `BILINGUAL_PDF_SKILL` to the actual bilingual-pdf directory and `STUDY_NOTES_SKILL` to this installed skill. They may be unrelated paths, including paths with spaces. The helpers never fetch a missing dependency.

Use matching tested revisions. `studytools.sty` requires native `ParallelTextAPIVersion` 2 and exposes `StudyToolsAPIVersion` 1. The common renderer owns all typography and layout. See its native, language and configuration references through the discovered installation.

## Build the worked example

Copy `examples/` to a new project and edit the native manuscripts. From that project:

```sh
make BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='notes quick-reference keyword-index decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
```

Default products are `notes quick-reference`. Allowed names are `notes`, `quick-reference`, `keyword-index` and `decision-tree`; an empty selection or unknown name fails. The Makefile creates `.build-products.tex` as generated selection metadata and builds included notes before dependent products. It does not create omitted products or import omitted companions.

The expected outputs are flat `notes.pdf`, `quick-reference.pdf`, `keyword-index.pdf` and `decision-tree.pdf` for the selected forms. Keep selected PDFs together if they have relative cross-document links. Rebuild dependent PDFs after notes pagination changes.

The installed example can find its own study assets through `..`; a copied project should pass the actual `STUDY_NOTES_SKILL` path or carry the required package files in a portable delivery. This is not a sibling-path assumption about the bilingual dependency.

## Direct native compilation

Make is optional. Supply the package search roots and compile the chosen document with latexmk:

```sh
export TEXINPUTS="$STUDY_NOTES_SKILL/assets//:$BILINGUAL_PDF_SKILL/assets//:${TEXINPUTS:-}"
latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape notes.tex
latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape quick-reference.tex
```

For a standalone dependent form, ensure the project's selection metadata or native wrapper omits unbuilt companion imports. A minimal authored project does not need the example Makefile; use the [native API](native-api.md) directly.

`common.tex` separates language/style choices from `notes-content.tex`, `entries.tex` and `decisions.tex`. Record declarations are preamble data; the wrappers choose a product renderer. Native LaTeX can use ordinary supported packages and the canonical layout hooks. Do not maintain another paired-rendering implementation.

## Check the selected outputs

For ordinary default-margin output, run the installed bilingual validator with the matching AUX/LOG evidence:

```sh
python3 "$BILINGUAL_PDF_SKILL/scripts/bilingual_pdf.py" validate notes.pdf --paired
python3 "$BILINGUAL_PDF_SKILL/scripts/bilingual_pdf.py" validate decision-tree.pdf --paired
```

The example's alphabet tabs are intentionally inset 6 mm from the physical edge, inside part of the body margin. Their whole-page minimum ink check is therefore 5 mm:

```sh
python3 "$BILINGUAL_PDF_SKILL/scripts/bilingual_pdf.py" validate quick-reference.pdf --paired --margin-mm 5
python3 "$BILINGUAL_PDF_SKILL/scripts/bilingual_pdf.py" validate keyword-index.pdf --paired --margin-mm 5
```

This is an explicit tab/print contract, not permission to ignore body geometry. Check the AUX-recorded column starts/widths, actual tab rectangles, page-edge clearance, overfull/missing-glyph warnings and actual pixels. For custom geometry, supply its intended minimum physical ink inset and retain body/label checks. Selected-language output omits `--paired`; booklet output adds `--covers` when that lifecycle is used.

Compiler exit alone is not acceptance. Validate local/named external links, generated pages, subentry targets and the full chosen decision graph. Inspect every final page. Record unrun and blocked checks separately.

## Portable delivery and pinned consumers

Include manuscripts, language/configuration files, source map, necessary images, `paralleltext.sty`, `studytools.sty`, `study-tree.tex`, `study-graph-components.tex` and applicable licenses. Include the graph file even when the manuscript selects only lookup/tree forms, because `studytools.sty` loads it. This portable copy does not transfer canonical implementation ownership to the downstream project.

A long-lived consumer records the exact tested public revision and package hashes in its own dependency manifest. Its private content, document identities, publication metadata and compatibility adapters stay downstream. Generic capability fixes belong in the public package and must be tested there before updating the pin. The divider follows the live text-block center: use symmetric paired-page margins for a fixed physical paper center. Asymmetric mirrored binding can shift that center by page parity; selected-language pages can use their own geometry without a second renderer.

Native TeX and latexmk configuration execute code. `-no-shell-escape` is not a filesystem sandbox; use trusted source or appropriate isolation. The helper does not authorize external translation, publication, downloads or access to private material.
