---
name: course-guide-quick-reference
description: Turn authorized courseware, textbooks or other learning sources into understandable notes and a companion keyword-and-concept Quick Reference. Use for creating or revising these paired learning tools, not document-format conversion alone.
---

# Learning Notes and Quick Reference

Create two complementary products: notes that teach, and a Quick Reference that helps a reader retrieve the right concept. The reusable workflow matters more than any particular subject or field list.

## Understand the source before summarizing

Identify the audience, prerequisites, requested source scope, language editions and output needs. Read the actual slides/pages, including diagrams and worked examples. Preserve an existing useful manuscript rather than restarting it.

Create a compact source map: source locator → concept → planned notes section. Record missing explanations, conflicting claims and unreadable material. Separate what the source says from your own derived examples or explanations. Never invent a source page, attribution or conclusion to fill a gap. Use only material the user is authorized to process; publication of textbook excerpts or figures requires separate rights review.

## Author notes that teach

Organize by the reader's learning dependencies, not necessarily the slide order. Explain the purpose, meaning, assumptions, mechanism and application that each concept actually needs. Work through calculations completely; use concrete examples for non-numerical material. Label limitations and pitfalls accurately. “Checks” should contain actionable validation, not every property of a topic.

Read [authoring](references/authoring.md) for source handling and concept design. There is no required number of courses, chapters or concepts, and no mandatory Meaning/Rule/Checks template for every entry. Preserve the requested scope; do not silently combine unrelated courses.

## Derive the keyword-and-concept Quick Reference

Give each concept one canonical entry. Use concise definitions, formulas, decision rules, procedures, examples or caveats as appropriate. Keep enough assumptions to make a shortcut usable; move extended teaching to the notes.

Provide lookup routes from the words a reader is likely to remember:

- **Canonical concept:** the substantive entry, with a stable label and a notes section/page pointer.
- **Alias or acronym:** a redirect to that concept, not a second copy of its explanation.
- **Secondary keyword/task:** an inverted lookup to one or more relevant concepts.
- **Related concept:** a useful explicit cross-reference, not an arbitrary link added just to populate a field.

Choose a useful ordering and document it. If the lookup claims A–Z ordering, give every advertised alias/keyword its own findable position; grouping several words under only the first word is not a complete alphabetical lookup. Native LaTeX references must generate page numbers; never type page pointers by hand. Recheck every alias, keyword and notes link after pagination changes.

## Produce portable documents

Use the complete `assets/learning-starter/` project for ordinary `.tex` authoring, shared `paralleltext.sty`, and native `xr-hyper`/`hyperref` links. Build `notes.tex` before `quick-reference.tex`; the resulting `notes.pdf` and `quick-reference.pdf` stay together in one folder. Both documents may be bilingual, or export one selected side. The structured collection route is also available and uses the same paired template, not another layout engine.

For a worked source-to-deliverable pattern, read the [bundled three-concept example](references/examples.md): source map, full teaching notes and independently findable lookup routes, with both PDFs and all editable files together.

Read [rendering](references/rendering.md) for the actual commands, structured contract and executable examples; read [layout](references/layout.md) only when adapting the design. Resolve paths relative to this installed skill. The skill is self-contained and does not require the sibling bilingual skill.

## Check the result, not only the build

Compare the notes with the source map for coverage and factual fidelity. Check units, assumptions, worked steps, definitions, language equivalence and unsupported claims. Then use the Quick Reference to answer realistic lookup questions; confirm that the links land at the promised explanation.

Render and personally inspect every final PDF page for paired correspondence, readable figures/tables, glyphs, clipping and page references. Use an independent reviewer when the scope or risk warrants one and the environment permits it; otherwise disclose that review was sequential. Follow [review and delivery](references/review-release.md) for larger projects. A small sample does not require a full production-release process.

Deliver the notes, Quick Reference, editable sources, source map and concise coverage/review limits. Do not claim the material is exam-complete or independently audited unless that was established. Native TeX is executable; `-no-shell-escape` is not a sandbox. Keep private sources and source locators out of public examples, and obtain applicable authorization before publishing or uploading.

## Adjust the presentation only when needed

The default style is usable without configuration. For a requested change, consult the [intent-to-option reference](references/configuration.md), add only the needed native setup keys or standard package commands, and rebuild and inspect all affected pages. Content, language/font mapping and presentation remain separate.
