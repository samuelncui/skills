---
name: course-guide-quick-reference
description: Turn authorized courseware, textbooks or other learning sources into understandable notes and a companion keyword-and-concept Quick Reference. Use for creating or revising these paired learning tools, not document-format conversion alone. Requires the installed bilingual-pdf skill for rendering.
---

# Learning Notes and Quick Reference

Create notes that teach and a Quick Reference that retrieves the right concept. This skill owns the teaching workflow and collection adapter; `bilingual-pdf` owns all rendering and layout behavior.

## Resolve the required dependency

Discover `bilingual-pdf` through the host's installed-skill listing and read its `SKILL.md`. Use the reported installation directory, never a hardcoded sibling path. Pass it as `--bilingual-skill` or `BILINGUAL_PDF_SKILL` for `scripts/course_documents.py`; the native example Makefile uses `BILINGUAL_PDF_SKILL` too. If absent, tell the user it must be installed through the host's supported process. Do not download or install it automatically.

Read the [human guide](README.md) for build commands and the dependency's canonical references for native API, structured input, languages, configuration and acceptance. Resolve those references under that installed directory; do not recreate copies in this skill.

## Understand and map the source

Establish audience, prerequisites, source scope, languages and output needs. Read actual slides/pages, including diagrams and worked examples; preserve an existing useful manuscript. Create a source map: exact source locator → concept → planned notes section and coverage status. Record gaps, conflicts and unreadable material. Distinguish source claims from derived explanation or original examples; never invent a locator or attribution. Use authorized material and review publication rights separately.

## Author explanatory notes

Organize by learning dependencies rather than blindly following slide order. Explain each concept's purpose, meaning, assumptions, mechanism and application as needed. Work through calculations; make non-numerical examples concrete. Label limitations and pitfalls accurately. “Checks” should be actionable validation, not a list of properties.

Read [authoring](references/authoring.md). There is no fixed course count or mandatory Meaning/Rule/Checks structure. Preserve requested scope and do not combine unrelated courses silently.

## Derive findable lookup routes

Give each concept one canonical entry with a stable label and generated notes section/page pointer. Use concise definitions, formulas, decision rules, procedures, examples or caveats as appropriate. Keep the assumptions that make a shortcut valid.

- Aliases and acronyms redirect to the canonical concept.
- Secondary keywords/tasks point to one or more concepts.
- Related concepts receive meaningful explicit cross-references.

State the ordering. Every advertised A–Z alias/keyword needs its own findable position; grouping several words under only the first is insufficient. Generate page numbers from native references, never by hand. Recheck lookup routes after pagination changes.

## Build and review

Adapt the complete `examples/` learning project or use the collection contract in [rendering](references/rendering.md). Native LaTeX and structured input use the dependency's same package. Build notes before Quick Reference; keep the flat `notes.pdf` and `quick-reference.pdf` together. Either document may be bilingual or use one selected side.

Compare notes with the source map, checking coverage, claims, units, assumptions, worked steps and language equivalence. Test realistic keyword/alias lookups and generated notes links. Render and inspect every final PDF page for pairing, figures, glyphs, clipping and references. Use independent review when warranted and available; otherwise disclose sequential review. Follow [review and delivery](references/review-release.md) at a depth appropriate to the assignment.

Deliver both PDFs, portable editable sources, source map and concise coverage/review limits. Do not claim exam completeness or an independent audit without evidence. Native TeX executes code; disabled shell escape is not a sandbox. Keep private sources and locators out of public examples and obtain applicable authorization before publishing or uploading.
