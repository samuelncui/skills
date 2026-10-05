# Agent skills for bilingual PDFs, study notes and testing

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Skills for bilingual documents, learning material and cost-aware software verification.

- [bilingual-pdf](skills/bilingual-pdf/README.md): align paragraph starts, table rows and list items in fixed physical columns. Choose whether long paragraphs can continue across pages; the following pair resynchronizes. Native LaTeX and JSON use one renderer, with LTR, RTL and CJK language profiles.
- [study-notes](skills/study-notes/README.md): create explanatory notes, one unified quick reference, a keyword index or a decision tree. Select one form or several. Native LaTeX records reuse the installed bilingual renderer.
- [testing-workflow](skills/testing-workflow/SKILL.md): design and maintain automated tests and benchmarks with the project's native runner. Batch execution and choose evidence proportional to risk and cost.

[![A bilingual usage guide](skills/bilingual-pdf/examples/en-zh-Hans/preview.png)](skills/bilingual-pdf/examples/en-zh-Hans/output.pdf)

The examples explain how to use the skills while demonstrating their output. Source files, PDFs and previews stay together. Human usage guides, native API references, configuration documentation and the JSON Schema remain independent, readable text.

## Start from your task

- Have paired text for a side-by-side bilingual article, report or handout? Use `bilingual-pdf`: [minimal native LaTeX and build command](skills/bilingual-pdf/references/latex.md#project-and-build-contract), or [minimal JSON, preflight and render commands](skills/bilingual-pdf/references/input.md#minimal-input). Both deliver editable source; check the [fonts and language requirements](skills/bilingual-pdf/references/languages.md) first.
- Need to turn learning sources into explanations or navigable reference material? Start with [study-notes](skills/study-notes/README.md), then use its explicitly installed rendering dependency.
- Need a test plan, regression tests or benchmarks for software? Start with [testing-workflow](skills/testing-workflow/SKILL.md).

The PDF route lays out supplied text pairs. OCR, extracting existing PDF content, automatic translation and preserving an existing PDF’s original page layout are outside its scope.

## Install

With the [Skills CLI](https://github.com/vercel-labs/skills) or a compatible installer:

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
```

Install only `bilingual-pdf` for ordinary parallel-text documents. `study-notes` requires it. Alternatively, copy the complete required skill directories to locations supported by your host. `testing-workflow` is independent and needs neither PDF skill.

Discover the actual installed `bilingual-pdf` directory through the host and supply it as `BILINGUAL_PDF_SKILL` when building study documents. The skills do not assume adjacent installations and never download dependencies automatically. TeX/fonts and optional Python QA dependencies are described in the individual guides.

## One implementation, explicit boundaries

`bilingual-pdf` owns `paralleltext.sty`, structured import, layout and rendering checks. `study-notes` adds a small native record/navigation layer and a learning authoring workflow; it does not carry a second renderer. Downstream document projects should pin a tested revision and keep their own content/configuration separate.

The calling agent supplies content and semantic pairings. The layout tool controls their rendered positions. Native TeX is executable; disabled shell escape is not a filesystem sandbox. Publication, external processing and source rights remain separate authorization decisions.

See [validation](tests/README.md) for reproducible tests and the distinction between historical and current results. Curated example PDFs are tracked beside their sources; Actions checks the repository rather than serving as the example-delivery channel.

Original code and example content use the [MIT license](LICENSE). Dependencies retain their [own licenses](THIRD_PARTY_NOTICES.md). No universal language, printer or accessibility certification is claimed.
