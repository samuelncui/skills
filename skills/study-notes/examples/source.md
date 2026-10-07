# Choosing and building a study set

Original teaching source for the self-hosted study-notes example. This text and its examples are MIT-licensed. It describes the skill's workflow; it contains no private course material.

## S1. Select the reader's task

Explanatory notes help a reader understand an idea: what it means, when it applies, how it works and how to use it. A worked example must retain the assumptions that make its steps valid. More pages do not automatically mean more complete coverage.

A Quick Reference helps a reader retrieve an answer from a remembered term or task. It contains substantive canonical entries together with aliases and keyword routes in one sorted headword space. The reader should not need to decide whether to search a separate keyword section first.

A standalone Keyword Index is a compact pointer view. It is useful when the reader explicitly wants locations rather than the compact explanations in the Quick Reference. It is optional; do not produce it as an unavoidable second lookup booklet.

A Decision Tree helps a reader choose a method from observable information. Ask a natural question, state its prerequisites inline and test lettered alternatives in first-match order. A leaf should provide an action or method, not merely the name of a topic.

A user may request one form or several. The default pair is notes plus Quick Reference. A tree or index can also be produced alone; absent companions must not leave broken external links.

## S2. Preserve evidence and scope

Read the authorized source, including figures and worked steps. Keep the original unchanged. Record source locator, concept and the place where it is explained or retrieved. Mark unreadable, missing and conflicting information explicitly. Distinguish source claims from derived explanation and original examples. A source map is provenance, not a second manuscript input format.

## S3. Use one native implementation

Native LaTeX is the manuscript format for study-notes. The installed bilingual-pdf skill owns the common paralleltext package; study-notes adds native record/navigation components. Discover both skill directories through the host and pass their real paths to the build. Do not assume sibling installations, download dependencies automatically or create a second layout engine.

A portable delivery contains the required package files, manuscript/configuration files, images and licenses. A downstream project should pin a tested public revision and keep private content and thin adapters in its own repository.

## S4. Make lookup paths direct

A canonical concept has a stable ID and substantive content. A meaningful subentry keeps its own stable ID and page. An alias redirects to that exact concept or subentry. A keyword can have several direct targets with context labels. Do not route an alias through another alias.

Sort one registry. Explicit lookup-group identity decides which records share a headword; the sort key controls order. These are separate choices. Identical punctuation-normalized text does not prove identical meaning. When a keyword matches an existing canonical headword, merge the route into that group instead of creating another lookup section. Preserve a definition when no equivalent canonical entry exists.

Local pointers name the concept and any subentry qualifier, then use the actual target page. Companion pointers also identify the source document and generated section/page. Printed folios may differ from physical PDF page positions. Rebuild linked documents after pagination changes.

## S5. Choose a paragraph-flow policy

The common native ParallelParagraph command supports a global paragraph-flow choice and a per-paragraph override. Use breakable for continuous prose that may span pages, and keep for a unit that must remain on one page. The following pair resynchronizes after both sides finish. Do not wrap flowing prose in a minipage or another indivisible container. Oversized keep-together content must fail visibly rather than be truncated or shrunk.

## S6. Make decision paths explicit

A/B/C choices are tested in order; follow the first matching condition. Keep semantic keys internal and generate reader-facing N numbers and pages from the display order. Put prerequisite inspections beside the question. A separate information-gathering route is useful only when missing facts can change the answer and obtaining them is a substantive task. A solution explains reasoning, executable steps and checks. Continue only for new required work. A genuine loop states the carried information, progress and exit; all targets must exist.

For this example, first ask whether the reader needs explanation, lookup or method selection. If the reader needs lookup, distinguish a compact answer from pointers alone. If the goal is unclear, ask for an example of what the reader will try to do before selecting a form.

## S7. Check and deliver

Check coverage, explanation, lookup usability, decision paths and visual layout separately. Follow real keyword/alias/subentry links, exercise each decision choice and verify generated destinations. Inspect every final page for alignment, continuations, glyphs, clipping, figures and references. A compiler exit or a first-page preview is not complete review evidence.

Deliver only the requested forms, together with their source map and portable native sources. Keep PDFs beside their relative cross-document targets. Native TeX can execute code; disabled shell escape is not a filesystem sandbox. Source rights, external processing and publication remain separate authorization decisions.
