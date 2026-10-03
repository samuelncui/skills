# Coverage and review

## Delivered scope

- Three notes pages covering all substantive material on P1-P3.
- Two Quick Reference pages, with one canonical entry per independent topic.
- English on the left and Simplified Chinese on the right throughout.
- Original editable route and unit-square diagrams; complete trip calculation, unit conversion and stack trace.
- Three independently listed alias/acronym routes and twenty-three independently listed keyword/task routes, including the multi-target keyword “Units”.
- A source map containing 32 claim and authored-explanation records, with stable native LaTeX labels.

## Review-driven iteration

Review of the first rendered version found two retrieval/localization weaknesses. Secondary terms such as Overflow, Queue and Removal order were grouped under other words and were not independently findable at their alphabetical positions. The Chinese stack trace also retained the English action label “push”.

The revised edition gives every advertised alias and keyword its own sorted redirect row, preserves one canonical body per concept, retains the multi-target Units entry, and uses 入栈 in the Chinese trace. Both revised Quick pages were re-rendered and inspected at the unchanged 10 pt body size. Notes source and PDF checksums remained unchanged. These corrections are iteration findings; the initial pass was not flawless.

## Passed checks

- Notes and Quick Reference compiled in order using XeLaTeX and latexmk with shell escape disabled.
- A portable bundle without build-cache files was extracted to a new directory and rebuilt from scratch. Both rebuilt PDFs passed paired validation and were pixel-identical to the reviewed originals at the comparison resolution.
- Paired-layout validator passed: notes 39 paired blocks and 11 embedded fonts; Quick Reference 45 paired blocks and 10 embedded fonts. No blank pages or reported mechanical errors.
- Every final PDF page was rendered at 140 dpi and inspected. English/Chinese unit alignment, figure geometry, mathematical notation, table columns, folios, glyphs and clipping were checked. No visible defects remained.
- English and Chinese were read sequentially and reconciled for numbers, definitions, scope, negation and caveats.
- All 32 mapped records have corresponding notes targets. Arithmetic and dimensions were checked against the source: 180 m / 12 s = 15 m/s; 200 cm = 2 m; 3 m × 2 m = 6 m²; perimeter = 10 m; doubled-area examples = 12 m² and 24 m².
- All local PDF link annotations resolve. All six bilingual cross-document Notes link annotations use the relative file `../notes.pdf` and resolve to the correct native notes destinations.
- Notes links, section numbers and page numbers are native references, with no manually typed page pointers.
- The final LaTeX logs contain no undefined-reference, multiply-defined-label, missing-character, overfull-box or underfull-box warnings.

## Retrieval exercises

These were answered by beginning with the Quick Reference lookup vocabulary, following the canonical entry and then verifying its fuller notes target:

1. “Mean speed: should pauses count?” → Average speed → yes; elapsed time includes pauses.
2. “Units: can 3 m and 200 cm give 600 m²?” → Rectangle area → convert 200 cm to 2 m; area is 6 m². The same Units row also reaches the distance/time example.
3. “Doubling: will the covering material double?” → Rectangle area → one dimension doubled gives twice the area; both doubled gives four times the area.
4. “LIFO: which item returns after pushing A and B?” → Stack behaviour → B first, with A remaining.
5. “Empty collection: what must pop return?” → Stack behaviour → no stored item exists; the interface must define its response. The source does not choose one.
6. “Uncertainty: how accurate is 15 m/s?” → Average speed → the supplied source gives no uncertainty-estimation method; no numerical uncertainty is inferred.
7. “Capacity: what happens if the stack is full?” → Stack behaviour → fixed-capacity overflow needs a separate test under the actual interface contract; no particular response is prescribed.
8. Direct “Overflow” lookup → its own O row → Stack behaviour → Notes stack section. Fixed-capacity overflow needs a separate test; the source does not prescribe the response.
9. Direct “Queue” lookup → its own Q row → Stack behaviour comparison → Notes stack section. FIFO returns A before B after the same two inputs.
10. Direct “Removal order” lookup → its own R row → Stack behaviour → Notes stack section. A stack returns B first, leaving A; check the returned value and remaining state.

## Review limits

Review was sequential and author-performed, not an independent domain or translation audit. The source is only the supplied small P1-P3 teaching text; no surrounding course content, examination coverage, measurement data, or implementation details are inferred. The delivered paired edition was reviewed; single-language exports and printer-specific production were not tested. Cross-document destinations were inspected structurally; viewer-specific permission prompts or restrictions on opening another local PDF were not tested.
