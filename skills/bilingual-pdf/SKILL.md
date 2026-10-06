---
name: bilingual-pdf
description: Render or edit side-by-side bilingual PDFs (parallel text) from supplied source and translation pairs, with aligned paragraphs, table rows, lists and figures. Use native LaTeX or structured JSON for articles, reports and handouts, including LTR, RTL and CJK scripts. Not for OCR, automatic translation or preserving an existing PDF layout.
license: MIT
compatibility: Requires XeLaTeX, latexmk and document fonts. JSON import and optional PDF checks also need Python packages; see requirements.txt and references/languages.md.
---

# Bilingual PDF

This is a layout tool. Accept the text pairs, rows and document structure supplied by the calling agent; render their corresponding units at aligned positions. Content selection, translation and semantic pairing belong to that agent. Before layout, check the supplied ordered language pair, corresponding units and requested edition; return missing or ambiguous pairings to the caller. Preserve the supplied wording and solve fit problems through the layout choices below.

## Select an input route

Resolve paths relative to this installed skill and use a fresh working directory. Preserve supplied inputs. Start with the [human guide and dependency checks](README.md#dependencies-checks-and-delivery).

- Native LaTeX: read [the native API and minimal build](references/latex.md#project-and-build-contract). Adapt a worked project in `examples/` or use the minimal native document. Build with XeLaTeX/latexmk without Python.
- Structured JSON: read [the input contract and minimal input](references/input.md#minimal-input) and [JSON Schema](schemas/document.schema.json). Run `python3 scripts/bilingual_pdf.py export input.json --output new-project`, or use `render` to export, compile and mechanically check. Image paths are relative to the input directory unless `--asset-root` is supplied.

Both routes use the one canonical `assets/paralleltext.sty`. Export produces an editable, portable native project. Choose a new output directory for each export/render attempt; existing directories are rejected to preserve earlier work. Use the installed package and helpers directly, so the project remains buildable without a repository checkout.

## Map structure to layout

Use `ParallelParagraph` with a global `paragraph-flow=keep|breakable` choice and per-block `[flow=keep|breakable]` override. JSON uses `layout.paragraph_flow` and paragraph `flow`. Explicit `ParallelText` stays bounded; `ParallelProse` permits continuation. The next pair resynchronizes after both sides finish. Table rows and list items align independently. A JSON table stays together as a complete group; native authors can allow breaks between bounded rows. Neither route splits a row automatically.

Use `ParallelWideFigure` (`placement: "shared"`) for one shared full-width image with paired captions. Use `ParallelFigure` (JSON `image: [left, right]`) for localized images. Example photographs and diagrams belong to `examples/shared/`; they are not generic runtime assets.

Language direction and physical column position are independent. Read [language setup](references/languages.md) when changing fonts or scripts, especially RTL/CJK and mixed-script expressions. If a font, image or tool is missing, report its exact name/path and the blocked stage; use the authorized environment workflow to install/retrieve it, or ask the caller to approve an alternative if none is already authorized, then resume that stage.

## Configure and validate

Defaults require no setup. Read [configuration](references/configuration.md) for sparse native keys, standard package hooks and the JSON subset. Keep language/font selection, manuscript content and layout settings separate. Fix layout problems in the canonical configuration or implementation rather than changing supplied wording, shrinking individual blocks or duplicating example-specific styles.

Run structured `preflight` when using JSON and the [rendering acceptance checks](references/acceptance.md). Inspect actual PDF pages for aligned starts/rows, continuations, glyphs, RTL shaping, image/caption placement, clipping, references and print geometry. Report passed, failed and unrun checks separately; compiler success alone is insufficient for visual acceptance.

## Deliver and preserve the trust boundary

Deliver the PDF and portable editable native project, plus JSON when used. Include required package/image files and their licenses. The helper does not translate, assess factual correctness or certify accessibility. Supplied native TeX and latexmk configuration execute code; `-no-shell-escape` is not a filesystem sandbox. Use trusted inputs or appropriate isolation. Obtain applicable authorization before external processing or publication, and keep private material out of public examples.
