---
name: study-notes
description: Create explanatory study notes, a unified quick reference, a keyword index or a decision tree from authorized learning sources. Use native LaTeX for one or several selected forms. Requires the installed bilingual-pdf skill for rendering.
---

# Study Notes

Turn authorized learning sources into the forms the reader needs. Native LaTeX is the only manuscript input. This skill owns source-to-notes authoring and native lookup/decision components; the installed `bilingual-pdf` skill owns all typography, paired layout and PDF rendering.

## Select forms and resolve the dependency

Offer the relevant forms without requiring the whole set:

- Notes explain concepts, assumptions, mechanisms and worked applications.
- Quick Reference combines substantive canonical entries, aliases and keyword routes in one sorted headword space. This is the default lookup form.
- Keyword Index is a compact standalone pointer view when the user explicitly wants one.
- Decision Tree asks natural questions, offers A/B/C choices plus an unknown/insufficient-information route, and leads by stable ID/page to a usable method.

One form or a combination is valid. Discover `bilingual-pdf` through the host's installed-skill listing and read its `SKILL.md`; never assume a sibling installation or download a dependency automatically. Use the discovered directory as `BILINGUAL_PDF_SKILL`. Read [the human guide](README.md) for build commands, [native study API](references/native-api.md) for declarations and [rendering](references/rendering.md) for independent/combined builds. Canonical layout, language and flow references belong to the installed bilingual skill.

## Map the source and author the selected forms

Read the actual source, including diagrams and worked steps. Preserve originals. Record source locator → concept → notes/lookup/tree coverage and mark unreadable, missing or conflicting material. Keep source claims, derived explanation and original examples distinguishable. Do not invent locators or force an existing useful manuscript into a fixed template.

Read [authoring](references/authoring.md). Explain purpose, meaning, conditions, mechanism and application as needed. Notes and compact entries need the assumptions that make their rules valid. There is no prescribed subject, course count or Meaning/Rule/Checks taxonomy.

Declare canonical concepts and meaningful subentries once. Add direct alias/keyword routes with exact target titles and context labels. Sort one registry. Deliberately shared lookup identities group matching headwords; sort normalization alone must not merge different meanings. Never replace a substantive glossary definition with a merely related pointer. Local and notes section/page references must be generated, and routes must terminate at a canonical concept/subentry rather than another alias.

For a decision tree, start from information the reader can observe. Each question needs distinct choices and a useful unknown route. Leaves contain a method, validation step or specific information-gathering action, not only a topic name. Keep graph IDs and generated pages visible; reject dangling targets and endless cycles.

## Build, inspect and deliver

Adapt the self-hosted example project in `examples/`; it teaches how to choose and build these forms. Retain only requested products. Use the canonical `ParallelParagraph` global/per-block page-breaking choice for long prose. Do not wrap a breakable paragraph inside an indivisible private box. Keep-together units that exceed a page must fail visibly, without truncation or shrinking.

The native `studytools.sty` layer uses the installed `paralleltext.sty`. Do not copy or fork its renderer, geometry, language handling or QA. Downstream projects should pin the tested skill revision and use thin private manuscript/configuration adapters. Keep private names, source text, identifiers and provenance downstream.

Run the [review and delivery checks](references/review-release.md), inspect every final page and exercise actual keyword, alias, subentry and tree lookups. Check coverage separately from layout; disclose unreviewed content and unrun checks. Keep selected PDFs together when they use relative cross-document links. Deliver the selected PDFs, portable native sources and source map. No JSON manuscript adapter is provided.

Native TeX and latexmk configuration execute code; disabled shell escape is not a sandbox. Use trusted inputs or appropriate isolation. Obtain applicable permission for external processing/publication and preserve licenses. Never move personal or private learning material into public examples.
