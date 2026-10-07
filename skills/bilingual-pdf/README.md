# Bilingual PDF

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Put corresponding content where readers can compare it: matching paragraph starts, list items and table rows, with a stable divider between physical columns. Choose whether long paragraphs stay together or continue across pages. Native LaTeX and JSON share one canonical layout package.

The calling agent supplies the paired content. This skill renders it; it does not choose translations, rewrite prose or decide which statements correspond.

This skill lays out supplied text pairs. OCR, extracting existing PDF content, automatic translation and preserving an existing PDF’s original page layout are outside its scope.

## What it does

- Aligns each paired paragraph, list item and table row independently of translation length
- Lets a paragraph continue across pages, then resynchronizes the following pair
- Keeps physical left/right column order separate from LTR/RTL language direction
- Renders one shared full-width image with paired captions, or two localized images
- Shares equation/figure counters and generates local page links
- Supports paired, left-only and right-only editions, configurable paper/binding geometry, covers, folios, semantic styles and navigation

[![Paragraph alignment in the English/Chinese usage guide](examples/en-zh-Hans/preview.png)](examples/en-zh-Hans/output.pdf)

[![English/Hebrew example](examples/en-he/preview.png)](examples/en-he/output.pdf)

These are actual output previews. Open the PDFs for all pages; a first-page image is a browsing aid, not complete visual evidence.

## Self-hosted examples

Each edition uses the same usage-guide content to demonstrate paragraphs, a table, figures, references and a small formula. Repeated English/Chinese passages are identical across editions.

| Pair | PDF | Structured source | Native project |
| --- | --- | --- | --- |
| English / French | [output.pdf](examples/en-fr/output.pdf) | [source.json](examples/en-fr/source.json) | [main.tex](examples/en-fr/main.tex) |
| English / Chinese | [output.pdf](examples/en-zh-Hans/output.pdf) | [source.json](examples/en-zh-Hans/source.json) | [main.tex](examples/en-zh-Hans/main.tex) |
| English / Arabic | [output.pdf](examples/en-ar/output.pdf) | [source.json](examples/en-ar/source.json) | [main.tex](examples/en-ar/main.tex) |
| English / Hebrew | [output.pdf](examples/en-he/output.pdf) | [source.json](examples/en-he/source.json) | [main.tex](examples/en-he/main.tex) |
| Chinese / Japanese | [output.pdf](examples/zh-Hans-ja/output.pdf) | [source.json](examples/zh-Hans-ja/source.json) | [main.tex](examples/zh-Hans-ja/main.tex) |

Example-only illustrations live once in `examples/shared/`. Runtime `assets/` contains the reusable package and optional profiles. The native examples do not need Python or repository-maintainer tools to compile.

## Native LaTeX

From this installed skill's directory:

```sh
cd examples/en-fr
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape -jobname=output main.tex
```

For your own work, copy a complete example to a fresh directory. Retain its package/image path relationship, or copy the required package and images into a portable project. Edit `content.tex` and `languages.tex`. The [complete native API](references/latex.md) documents every public command, argument, default and error boundary; it also includes a minimal document.

Set a global paragraph policy in the preamble and override it on individual paragraphs:

```tex
\ParallelSetup{paragraph-flow=breakable}
\ParallelParagraph{explanation}{Left paragraph.}{Right paragraph.}
\ParallelParagraph[flow=keep]{short}{Keep this pair together.}{Keep this pair together.}
```

`ParallelText` is always bounded; `ParallelProse` explicitly permits continuation. An oversized keep-together unit fails visibly. The renderer does not shrink or truncate it.

## Structured JSON

From this installed skill's directory:

```sh
python3 scripts/bilingual_pdf.py export examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-project
python3 scripts/bilingual_pdf.py render examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-build
```

`export` creates portable editable LaTeX. `render` also compiles and checks it. Existing output directories are rejected. Add `--mode left` or `--mode right` for a selected-language edition.

Use the independent [JSON Schema](schemas/document.schema.json) and [field reference](references/input.md). `layout.paragraph_flow` sets `keep` or `breakable`; a paragraph's `flow` overrides it. `atomic` remains a compatibility alias for `keep`. Schema validation is complemented by runtime checks for IDs, dimensions, references, fonts and asset paths.

Image paths resolve inside the input directory or explicit `--asset-root`; absolute paths, traversal and symlink escapes are rejected. The adapter never fetches assets or dependencies.

## Configure without forking the layout

The [configuration reference](references/configuration.md) covers geometry, binding, divider appearance, folios, spacing, styles, semantic roles, covers and navigation. Defaults work without setup. Use sparse overrides or documented native hooks, keeping content, language/font mapping and presentation separate.

The JSON table aligns rows but keeps the complete table and caption together. Native paired rows can be placed outside `ParallelKeep` to permit breaks between rows. Individual rows are bounded; automatic splitting of a row or repeated longtable headers is not provided.

## Dependencies, checks and delivery

Use XeLaTeX, latexmk and the documented TeX packages/fonts. See [language setup](references/languages.md) for French hyphenation, Arabic/Hebrew bidi, CJK fonts and mixed-script runs. Structured import and optional PDF checks use `requirements.txt`, Fontconfig and `kpsewhich`.

Follow [rendering acceptance](references/acceptance.md): inspect actual pages for alignment, continuations, glyphs, RTL shaping, clipping, images, references and print geometry. Mechanical checks do not establish semantic correctness. Report passed, failed and unrun checks separately.

Deliver the PDF, portable native source project and JSON when used. Include required assets/licenses. Native TeX and latexmk configuration execute code; `-no-shell-escape` is not a sandbox. Use trusted source or appropriate isolation. Vertical writing, arbitrary floats/verbatim macro arguments, native Windows font discovery and PDF/UA remain outside the tested contract.

Original code, tutorial text and diagrams use the [MIT license](LICENSE). Third-party dependencies retain their own licenses. No private document content belongs in these public examples.

## Translation before layout

For raw-source translation, use the separately installed bilingual-translation skill to prepare one reviewed paired manuscript. Supplied pairs still render directly. See [translation handoff](references/translation.md) for installed-skill discovery, version pinning and optional exchange-v1 import; native TeX remains equally supported.
