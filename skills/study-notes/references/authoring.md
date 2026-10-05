# Authoring notes, lookup and decision paths

Choose the form from the reader's task, then use the [native study API](native-api.md) to represent it. Native LaTeX is the only manuscript input; a source map is provenance rather than another authoring format. There is no required subject, course count or fixed teaching taxonomy.

## Select the useful forms

- **Notes** explain a concept, its conditions, mechanism and application.
- **Quick Reference** gives compact substantive answers through canonical entries, aliases and keyword routes in one sorted headword sequence.
- **Keyword Index** is an optional standalone pointer view of the same registry. Select it when locations alone meet the reader's need.
- **Decision Tree** turns observable information into a method through explicit questions, choices and unknown-information routes.

One form or several is valid. Notes plus the unified Quick Reference are the default pair; neither the index nor the tree is mandatory. A selected form must remain usable without omitted companions. The [build guide](rendering.md) explains product selection and dependency discovery.

## Preserve source coverage

Read the full authorized source inventory, including diagrams and worked steps. Preserve originals. A heading, unexplained symbol or broken OCR token is not enough to reconstruct a claim confidently: mark the gap, consult authorized context or ask a focused question.

Use a lightweight ledger with source identifier, exact page/slide/section, concept ID, location in each selected form and coverage status: covered, partial, missing or deliberately excluded with a reason. Distinguish an unselected form from missing coverage. Reconcile the ledger against the source inventory rather than only the headings chosen for the notes. Give derived explanations and original examples their own labels; do not invent source locators.

Keep provenance in the working project and publish it only when authorized and appropriate. The original [teaching source](../examples/source.md) and [source map](../examples/source-map.json) demonstrate this practice without private material.

## Teach with notes

Use the structure the concept needs. A definition may need a contrast and example; a procedure may need inputs, preconditions, steps and failure cases; a mathematical result may need notation, assumptions, derivation and a worked calculation. Do not force these into identical fields.

Explain why the idea matters and what the reader can do after the section. Explain causes, not merely outcomes. Define notation before use and retain the conditions that make each application valid. Work through soundly derivable intermediate steps and identify them as explanation. Check arithmetic and dimensions. Keep source-specific administrative instructions separate from general learning principles.

Make examples self-contained: state inputs, units, assumptions, diagrams and the reasoning needed for the result. Every referenced figure must appear or have an accurate locator in the delivered bundle. Explain what to read in it. An original diagram may replace an authorized source figure only without silently changing its relationships, scale or labels; inspect actual pixels.

Author prose with the common renderer's `ParallelParagraph`. Select its global or per-paragraph flow policy: breakable prose can cross pages, while a kept unit must fit. Do not enclose flowing prose in an indivisible box, truncate it or silently shrink it. The common renderer owns this behavior; the study layer must not fork it.

## Build one unified lookup

Declare one substantive canonical entry per concept with a stable ID. Include only what answers the reader's recall question: meaning, a rule with conditions, a discriminating example, a procedure or an important limitation. Meaningful subentries have their own IDs and generated local pages.

Declare aliases and keyword routes in the same registry as canonical concepts. Every route goes directly to a concept or subentry, never through another alias. A task keyword may have several direct targets with context labels. Include remembered terms, abbreviations and useful localized variants at their own sort positions. Do not hide a useful secondary term inside another headword's title.

Choose ordering deliberately. Explicit lookup-group identity controls which records share a headword; a separate sort key controls position. Equal sort keys do not merge records. A keyword that deliberately shares an existing canonical headword belongs in that group, while different senses retain distinct concept IDs and paired sense labels. Do not discard an independent definition merely because a related concept exists. The example uses literal English A–Z keys, not automatic multilingual collation.

Render this registry once with `StudyPrintQuickReference`. Substantive entries and routes are interleaved, so the reader never has to choose between separate concept and keyword sections. The optional `StudyPrintKeywordIndex` uses the same registry in a separate selected PDF: it omits explanatory bodies while retaining canonical and subentry destinations. It is not a second mandatory lookup location.

Keep local and companion references distinct. A local pointer names the exact concept, sense and subentry where applicable, with its generated page. A companion pointer also identifies the notes document, section and printed page. Use native labels and generated destinations, not hand-entered page numbers. Import only included companions, build them first and rebuild dependants after pagination changes. Printed folios need not equal physical PDF page numbers.

## Turn questions into methods

Start from information the reader can observe. Use natural questions with distinct alternatives and visible stable node IDs. Each question needs at least two ordinary lettered choices and one explicit unknown/insufficient-information route.

A method leaf must contain usable instructions, checks or a specific action, not merely a topic name. A required next step is a forward continuation; a terminal leaf has no such continuation. A clarification says exactly what information to obtain before a conditional return to a question. Keep this typed return distinct from an unconditional loop.

Check every choice, unknown route, continuation and clarification return. Ordinary forward paths must terminate and all targets must exist. Structural validation cannot establish that alternatives are sensible, observable or sufficiently complete. Test realistic reader situations, including a reader who does not yet know an answer.

The original [decision declarations](../examples/decisions.tex) ask whether the reader needs explanation, lookup or method selection, then distinguish compact answers from pointers alone. They demonstrate conditional clarification returns and a shared required review step.

## Review meaning and usability

Read each full paragraph or worked example before translating isolated phrases. Keep a small project terminology list for recurring concepts, symbols, aliases and deliberate variants. Read each language independently, then compare claims, conditions, emphasis, uncertainty and results. Fluent wording can still omit a qualification.

Before delivery:

1. Trace important claims to a source, a labeled derivation or an original example.
2. Start with realistic aliases and remembered tasks; follow exact concept/subentry targets and included notes links without guessing.
3. Exercise every decision path, including unknown information and its return condition.
4. Inspect every final PDF page and generated reference. Review coverage, teaching quality, language and layout separately.

Use the [example coverage exercises](../examples/coverage-review.md) and [review checklist](review-release.md). Keep these independent references readable alongside the worked manuscripts; examples complement the documentation rather than replacing it.
