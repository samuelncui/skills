---
name: study-notes
description: Create explanatory study notes, a unified quick reference, a keyword index or a decision tree from authorized learning sources. Use native LaTeX for selected forms or import a structured decision graph. Requires the installed bilingual-pdf skill for rendering.
---

# Study Notes

Turn authorized learning sources into the forms the reader needs. Use native LaTeX for notes, quick references and indexes. Decision graphs may also use the optional versioned structured import route. This skill owns source-to-notes authoring and native lookup/decision components; the installed `bilingual-pdf` skill owns all typography, paired layout and PDF rendering.

## Select forms and resolve the dependency

Offer the relevant forms without requiring the whole set:

- Notes explain concepts, assumptions, mechanisms and worked applications.
- Quick Reference combines substantive canonical entries, aliases and keyword routes in one sorted headword space. This is the default lookup form.
- Keyword Index is a compact standalone pointer view when the user explicitly wants one.
- Decision Tree asks natural questions, tests A/B/C choices in first-match order and leads by generated reader number/page to a usable answer approach.

One form or a combination is valid. Discover `bilingual-pdf` through the host's installed-skill listing and read its `SKILL.md`; never assume a sibling installation or download a dependency automatically. Use the discovered directory as `BILINGUAL_PDF_SKILL`. If discovery finds no compatible installation, report the required dependency/version and continue source mapping while its installation is resolved through the authorized host workflow. Read [the human guide](README.md) for build commands, [native study API](references/native-api.md) for declarations and [rendering](references/rendering.md) for independent/combined builds. Canonical layout, language and flow references belong to the installed bilingual skill.

## Import a structured decision graph

When the input is structured graph data, use the single primary [graph-v1 import workflow](references/structured-graph.md): validate the standard schema and semantics, retain supplied language pairs, generate deterministic Nx order and existing native fragments, then compile with the discovered bilingual-pdf dependency and the trusted native layout. Read that reference before adapting data; unknown fields fail instead of being discarded. Keep one authoritative JSON graph, with source-bound rich fields and explicit helper calls where needed. Do not create a parallel reader graph or make uncertainty/inspection routes mandatory. Native graph authoring remains compatible. The importer requires Python 3.10+, its owned requirements and bilingual-pdf renderer API 1; native-only authoring remains Python-free.

For trusted native adapters, use the [native emission helpers](references/native-emission.md) for localized inline call sentences, precise references and source-field survival checks. These additive helpers preserve authored routes; the structured importer retains its own graph-v1 limits.

## Map the source and author the selected forms

Read the actual source, including diagrams and worked steps. Preserve originals. Record source locator → concept → notes/lookup/tree coverage and mark unreadable, missing or conflicting material. Keep source claims, derived explanation and original examples distinguishable. Use verified page/section identifiers; mark unavailable locators as unknown. Retain useful existing organization and add the context or coverage that the selected form needs.

Read [authoring](references/authoring.md). Explain purpose, meaning, conditions, mechanism and application as needed. Notes and compact entries need the assumptions that make their rules valid. There is no prescribed subject, course count or Meaning/Rule/Checks taxonomy.

Declare canonical concepts and meaningful subentries once. Add direct alias/keyword routes with exact target titles and context labels. Sort one registry. Deliberately shared lookup identities group matching headwords; sort normalization alone must not merge different meanings. Keep an independently useful definition as a canonical entry; use a direct pointer for a genuine synonym or a task route whose answer lives in another entry. Local and notes section/page references must be generated, and routes must terminate at a canonical concept/subentry rather than another alias.

For a decision tree, use the [native graph components](references/graph-components.md) and their reader profile. Keep stable semantic keys internal; generate N1, N2, … from one display order. Put the facts to inspect and definitions needed to answer directly with each natural question. Test uniformly lettered choices in first-match order. Provide an information-gathering branch only when unresolved information can change the answer and cannot be obtained in that question. Each solution explains how and why to reach the requested answer, with applicable conditions and checks. A route may converge or repeat when its carried state, progress and exit are clear. Review these semantics separately from target/link checks.

## Build, inspect and deliver

Adapt the self-hosted example project in `examples/`; it teaches how to choose and build these forms. Retain only requested products. Use the canonical `ParallelParagraph` global/per-block page-breaking choice for long prose. Place breakable paragraphs directly in the flowing manuscript; reserve bounded containers for short units that fit together on a page. Keep-together units that exceed a page must fail visibly, without truncation or shrinking.

The native `studytools.sty` layer uses the installed `paralleltext.sty`. Do not copy or fork its renderer, geometry, language handling or QA. Downstream projects should pin the tested skill revision and use thin private manuscript/configuration adapters. Keep private names, source text, identifiers and provenance downstream.

Run the [review and delivery checks](references/review-release.md), inspect every final page and exercise actual keyword, alias, subentry and tree lookups. Check coverage separately from layout; disclose unreviewed content and unrun checks. Keep selected PDFs together when they use relative cross-document links. Deliver the selected PDFs, portable native sources and source map. For imported decision graphs, keep the versioned JSON as the sole content/edge source and regenerate derived TeX.

Native TeX and latexmk configuration execute code; disabled shell escape is not a sandbox. Use trusted inputs or appropriate isolation. Obtain applicable permission for external processing/publication and preserve licenses. Never move personal or private learning material into public examples.
