# Study Notes

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Create the learning tools a reader actually needs. Choose explanatory notes, one unified quick reference, a compact keyword index or a decision tree, individually or together. Manuscripts use native LaTeX; rendering comes from the installed `bilingual-pdf` skill.

## Four optional forms

| Form | Reader's question | Output |
| --- | --- | --- |
| Notes | “What does this mean, and how does it work?” | `notes.pdf` |
| Unified Quick Reference | “I remember a term or task. What is the relevant idea?” | `quick-reference.pdf` |
| Keyword Index | “Where are the relevant concepts?” | `keyword-index.pdf` |
| Decision Tree | “Given what I know, what should I do next?” | `decision-tree.pdf` |

The default pair is notes plus Quick Reference. The Quick Reference interleaves canonical concepts, aliases and keyword routes in one sorted headword space. Readers do not have to choose between a keyword section and a concept section. A separate keyword booklet is optional, not a compulsory second place to search.

[![Unified lookup example](examples/quick-reference-preview.png)](examples/quick-reference.pdf)

[![Question-to-method decision example](examples/decision-tree-preview.png)](examples/decision-tree.pdf)

## A self-hosted learning example

The [original teaching source](examples/source.md) explains how to select and build these four forms. Its [source map](examples/source-map.json), native manuscripts, PDFs and previews remain together under `examples/`:

- [Notes](examples/notes.pdf): explanation and worked choices
- [Unified Quick Reference](examples/quick-reference.pdf): one interleaved lookup space
- [Keyword Index](examples/keyword-index.pdf): compact generated pointers
- [Decision Tree](examples/decision-tree.pdf): natural questions, alternatives, clarification and methods

These examples demonstrate the skill using its own subject matter. Independent human usage, [authoring guidance](references/authoring.md), [native API](references/native-api.md), [build guide](references/rendering.md) and [review checklist](references/review-release.md) remain readable Markdown.

## Install and discover the renderer

Install both `study-notes` and `bilingual-pdf` through your host. Discover their actual installed directories; they may be unrelated paths. Do not assume a sibling installation.

```sh
export BILINGUAL_PDF_SKILL="/path/reported/by/host/bilingual-pdf"
export STUDY_NOTES_SKILL="/path/reported/by/host/study-notes"
```

`bilingual-pdf/assets/paralleltext.sty` owns geometry, fonts, paragraph alignment, continuation, figures, roles, covers and rendering checks. This skill's `studytools.sty` adds native records and navigation. It never downloads dependencies or carries a second renderer.

Use the bilingual skill's independent native/language/configuration references for the common layout API. Native builds require XeLaTeX, latexmk and the documented fonts/packages. Python is optional for native-manuscript QA and required for the optional structured decision-graph importer. Notes and lookup forms remain native.

## Build only the forms you want

Copy `examples/` into a fresh project, retain the discovered skill paths and replace the teaching manuscripts with your authorized content. From that project:

```sh
make BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='notes quick-reference keyword-index decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
```

The first command selects notes and Quick Reference. Build selected companion notes before documents that refer to them. Omitted companions must not leave broken external links. Keep PDFs together when they use relative cross-document links; viewer support for those links varies.

For a portable native handoff, include the required `paralleltext.sty`, `studytools.sty`, `study-tree.tex`, `study-graph-components.tex`, manuscript/configuration files and licenses. A delivery copy is distinct from maintaining another installed renderer. The [build guide](references/rendering.md) gives direct latexmk commands and dependency checks.

## One lookup registry

Declare canonical concepts once, including meaningful subentries. Route remembered words, aliases and acronyms directly to the exact concept or subentry. Generated references include the relevant title/context and the actual target page, with companion-document identity and section/page when available.

Lookup identity is explicit and separate from the sort key. Records deliberately sharing a headword group appear together; punctuation normalization alone must not merge different meanings. A glossary definition without an equivalent canonical explanation remains substantive content rather than being discarded as a “related” link.

The same native registry produces the unified Quick Reference or a compact index. See [native declarations](references/native-api.md) for grouping, aliases, multi-target routes, subentries, short running heads and navigation hooks.

## Questions that lead to methods

Use the [native graph components](references/graph-components.md) to ask natural questions with prerequisites at the point of use. Test A/B/C in order and take the first match. Generated N1, N2, … references keep semantic keys internal. Each solution explains the reasoning, operations and checks needed to answer the task.

Resolve missing facts beside the question where possible. A separate information-gathering branch is useful when that work is substantive; it is not required for every question. Genuine loops are valid when their carried state, progress and exit are clear. The shared renderer preserves question-blue and solution-green roles.

## Long paragraphs and reusable presentation

Use `ParallelSetup{paragraph-flow=breakable}` with `ParallelParagraph`, and override individual paragraphs with `[flow=keep]` when appropriate. Do not enclose flowing prose in an indivisible private box. The canonical renderer supports paired and selected-language continuation, then restores alignment before the next unit. An oversized keep-together block fails without truncating or shrinking content.

Downstream projects should pin a tested skill revision and keep private content, metadata and thin compatibility adapters in their own project. Add missing generic capabilities to the shared renderer instead of maintaining a private layout fork.

## Review and delivery

Check source coverage, explanation quality, realistic lookup routes, decision paths, links and actual PDF pages separately. Do not claim completeness or an independent audit without evidence. Deliver the selected PDFs, source map and portable editable project; report passed, failed and unrun checks.

Native TeX and latexmk configuration execute code. Disabled shell escape does not isolate file access. Keep private sources, names, identifiers and provenance out of public examples, and obtain applicable authorization before external processing or publication. Original code/content use the [MIT license](LICENSE); dependencies retain their own licenses.

## Structured graph input

Notes and lookup forms stay native LaTeX. For a structured decision graph, follow the [graph-v1 workflow](references/structured-graph.md) and the [paired example](examples/structured-graph.json). One versioned JSON source defines content and edges; the importer validates it, generates deterministic N identities and emits the existing native semantic components. Supplied language pairs need no translation dependency. Rendering and typography remain owned by the installed bilingual-pdf skill.
