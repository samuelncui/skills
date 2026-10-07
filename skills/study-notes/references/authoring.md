# Authoring notes, lookup and decision paths

Choose the form from the reader's task, then use the [native study API](native-api.md) to represent it. Native LaTeX is the only manuscript input; a source map is provenance rather than another authoring format. There is no required subject, course count or fixed teaching taxonomy.

## Select the useful forms

- **Notes** explain a concept, its conditions, mechanism and application.
- **Quick Reference** gives compact substantive answers through canonical entries, aliases and keyword routes in one sorted headword sequence.
- **Keyword Index** is an optional standalone pointer view of the same registry. Select it when locations alone meet the reader's need.
- **Decision Tree** turns observable information into a method through observable questions, first-match choices and usable answer approaches.

One form or several is valid. Notes plus the unified Quick Reference are the default pair; neither the index nor the tree is mandatory. A selected form must remain usable without omitted companions. The [build guide](rendering.md) explains product selection and dependency discovery.

## Preserve source coverage

Read the full authorized source inventory, including diagrams and worked steps. Preserve originals. A heading, unexplained symbol or broken OCR token is not enough to reconstruct a claim confidently: mark the gap, consult authorized context or ask a focused question.

Use a lightweight ledger with source identifier, exact page/slide/section, concept ID, location in each selected form and coverage status: covered, partial, missing or deliberately excluded with a reason. Distinguish an unselected form from missing coverage. Reconcile the ledger against the source inventory rather than only the headings chosen for the notes. Give derived explanations and original examples their own labels; do not invent source locators.

Keep provenance in the working project and publish it only when authorized and appropriate. The original [teaching source](../examples/source.md) and [source map](../examples/source-map.json) demonstrate this practice without private material.

## Teach with notes

Use the structure the concept needs. A definition may need a contrast and example; a procedure may need inputs, preconditions, steps and failure cases; a mathematical result may need notation, assumptions, derivation and a worked calculation. Choose the relevant elements for that concept and arrange them in the order a reader needs to understand or apply it.

Explain why the idea matters and what the reader can do after the section. Explain causes, not merely outcomes. Define notation before use and retain the conditions that make each application valid. Work through soundly derivable intermediate steps and identify them as explanation. Check arithmetic and dimensions. Keep source-specific administrative instructions separate from general learning principles.

Make examples self-contained: state inputs, units, assumptions, diagrams and the reasoning needed for the result. Every referenced figure must appear or have an accurate locator in the delivered bundle. Explain what to read in it. An original diagram may replace an authorized source figure only without silently changing its relationships, scale or labels; inspect actual pixels.

Author prose with the common renderer's `ParallelParagraph`. Select its global or per-paragraph flow policy: breakable prose can cross pages, while a kept unit must fit. Place flowing prose outside bounded containers. If a kept unit overflows, choose breakable prose or divide it at meaningful corresponding boundaries while preserving content. The common renderer owns this behavior; the study layer must not fork it.

## Build one unified lookup

Declare one substantive canonical entry per concept with a stable ID. Include only what answers the reader's recall question: meaning, a rule with conditions, a discriminating example, a procedure or an important limitation. Meaningful subentries have their own IDs and generated local pages.

Declare aliases and keyword routes in the same registry as canonical concepts. Every route goes directly to a concept or subentry, never through another alias. A task keyword may have several direct targets with context labels. Include remembered terms, abbreviations and useful localized variants at their own sort positions. Give a useful secondary term its own route and sort key, pointing directly to the canonical entry or subentry.

Choose ordering deliberately. Explicit lookup-group identity controls which records share a headword; a separate sort key controls position. Equal sort keys do not merge records. A keyword that deliberately shares an existing canonical headword belongs in that group, while different senses retain distinct concept IDs and paired sense labels. Do not discard an independent definition merely because a related concept exists. The example uses literal English A–Z keys, not automatic multilingual collation.

Render this registry once with `StudyPrintQuickReference`. Substantive entries and routes are interleaved, so the reader never has to choose between separate concept and keyword sections. The optional `StudyPrintKeywordIndex` uses the same registry in a separate selected PDF: it omits explanatory bodies while retaining canonical and subentry destinations. It is not a second mandatory lookup location.

Keep local and companion references distinct. A local pointer names the exact concept, sense and subentry where applicable, with its generated page. A companion pointer also identifies the notes document, section and printed page. Use native labels and generated destinations, not hand-entered page numbers. Import only included companions, build them first and rebuild dependants after pagination changes. Printed folios need not equal physical PDF page numbers.

## Turn questions into methods

Use the [native graph components](graph-components.md) with the reader profile. Declare internal semantic keys once, in display order, using `StudyDeclareGraphNodeAuto`; the package generates reader numbers N1, N2, … independently of keys. References use the reader number, localized title and generated page. Keep presentation in the common renderer's configuration and semantic roles: question blue, solution green.

Author the path in this order:

1. State the reader's requested result and the observable facts that distinguish solution approaches. Turn those distinctions into natural questions, not a list of method names the reader must already understand.
2. Put prerequisites beside the question: what to inspect, how to recognize it, definitions, units and scope. For example, “For these measurements of the same quantity in the same unit, do all groups contain the same number of observations? Read the group counts first.” This lets a reader decide at the point of use.
3. Write A/B/C conditions in priority order and stop at the first match. When an earlier condition is undecidable and could affect the answer, explain the specific missing fact and how to obtain it. Usually this instruction fits inline; give it a separate route only when it is a substantive source-supported task. An unknown branch is not compulsory for a question whose prerequisites already resolve the uncertainty. A result that is identical under all unresolved possibilities may still be justified explicitly.
4. At the selected solution, explain the reasoning and the operations needed for the answer, including applicability and a check. For unequal group sizes, for example, weight each group mean by its count, sum those products, then divide by the total count: larger groups represent more observations. Check that the result lies between the smallest and largest group means. This is an answer approach a reader can execute; a named technique or blank answer form would leave the reasoning to the reader.
5. Finish at that useful solution when it already answers the task. Add a continuation only for new required work. Shared subprocedures may return to an explicit step. A genuine iterative method may revisit a node: state what changes, what is carried forward and when to stop. Check all targets and whether each realistic route reaches its intended outcome.

The [worked decision manuscript](../examples/decisions.tex) applies these components to the source's task of building study forms. Its prerequisites are inline and its solutions contain the actual authoring approach. Graph declarations remain native TeX; structured adapters are optional downstream implementation choices, not manuscript requirements.

## Review meaning and usability

Read each full paragraph or worked example before translating isolated phrases. Keep a small project terminology list for recurring concepts, symbols, aliases and deliberate variants. Read each language independently, then compare claims, conditions, emphasis, uncertainty and results. Fluent wording can still omit a qualification.

Before delivery:

1. Trace important claims to a source, a labeled derivation or an original example.
2. Start with realistic aliases and remembered tasks; follow exact concept/subentry targets and included notes links without guessing.
3. Exercise every decision path, including any material uncertainty, required continuation or progress-bearing loop.
4. Inspect every final PDF page and generated reference. Review coverage, teaching quality, language and layout separately.

Use the [example coverage exercises](../examples/coverage-review.md) and [review checklist](review-release.md). Keep these independent references readable alongside the worked manuscripts; examples complement the documentation rather than replacing it.
