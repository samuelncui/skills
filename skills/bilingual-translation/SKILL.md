---
name: bilingual-translation
description: Translate source material into aligned source/target content while preserving exact source text, stable units and review progress. Use for new translations or revisions of paired content; already-paired PDF/HTML layout can use its renderer directly.
---

# Bilingual translation

Produce one canonical paired manuscript from the preserved source. Keep source and target language roles separate from physical display order. Retain supplied translations; revise them only within the user's request.

## Establish the source and master

1. Preserve original input bytes. Read the complete relevant source before translating, streaming through all of it if large. For an excerpt request, read the requested excerpt and needed context. Verify extraction against the original, including lists, tables, figures, captions and footnotes; label unreadable portions.
2. Choose a lossless manuscript route. Native paired TeX and other appropriate native formats are first-class choices. Use the optional [v1 JSON exchange](references/contract-v1.md) when its plain-text types preserve the requested content. Rich formulas, nested structures and formatting require an explicit native route when v1 cannot represent them.
3. Establish one canonical paired master with exact source text, stable IDs, target slots and review progress. Keep full paragraphs, semantic list items, table cells and captions as separate units. Record a concise section map, audience and recurring terms with the master; keep the full source available. Summaries aid orientation; exact source governs translation and checking.
4. Assign IDs before translation and retain them on edits/reordering. Record source snapshot identity and unit locations to reconcile coverage. Execute the source-only preparation now: save the master with exact source units and empty target slots, then read that saved file back and check its source coverage. For JSON, `validate --untranslated` checks this persisted checkpoint. Begin target authoring after this execution and readback have finished. In native TeX, save and inspect the paired source commands with explicitly empty target arguments first.

## Translate and save one coherent working block

Stable alignment IDs describe what stays paired; they do not require one remote write for every small cell or item. Resume from the persisted source-only master and choose the next working block:

- Prose: one complete paragraph, translated, reviewed and saved before the next paragraph.
- Short structured content: one coherent table row (read with its headers), a short header row, or one small coherent list. Retain each cell/item's own ID and target slot while reviewing the complete row/list together. A paragraph-length cell or item is its own working block.

Make the active ID or small ID set explicit. Read its complete source plus only the neighboring context needed. Reuse the already-read section map and glossary. The optional `view --unit ID` gives one complete pair and table-row context; request global context once on entry/resume.

Compare the active source and target for:
- Complete meaning, omissions, qualifications and cross-references
- Numbers, dates, quantities, units, names and labels, including which header belongs to each cell
- Negation, conditions, exceptions and causal relationships
- Consistent terminology and natural target-language expression

Correct discrepancies and persist the active block once into the same paired master. Confirm that scoped write before authoring the next block. For one pair, `record-review` records the caller's review and returns the next source. For a reviewed row/list, compose the existing `record_review` calls in memory and call `save_document` once; the [worked example](references/example-guide.md#one-short-row-one-atomic-save) preserves each ID and checks all source hashes before saving.

Reuse one agent session, source access, glossary and editor/interactive stream. Read back the affected block or a concise save receipt rather than the complete manuscript after every small field. Batch deterministic whole-document validation after useful progress; keep semantic review with each working block. Adjacent prose paragraphs remain separate working blocks.

On a source edit, preserve the existing target and mark it for renewed review. Read the current pair before acknowledging it. Native manuscripts can use stable comments or a concise progress record; JSON offers hash-based invalidation and a single-unit review-record helper.

## Reconcile and render

Compare the complete master with the preserved source for missing, duplicated or misplaced units, table cells, figures and captions. Read cross-unit transitions and recurring terms. Keep unresolved uncertainty visible and unreviewed.

The [optional validator](scripts/translation_contract.py) checks structure, source hashes, review currency and per-ID coverage. It cannot judge semantic accuracy or prove extraction completeness. Check image labels separately, preserving a shared figure unless localization is requested.

Pass the already-paired master to an installed renderer discovered through the host, or deliver the native paired manuscript as requested. Native TeX goes directly to its renderer. Existing pairs do not require this skill; translation and rendering have separate owners. Report translation/review scope separately from objective checks and visual inspection.

## Resources

- [Contract and commands](references/contract-v1.md): optional JSON schema, states and Python API
- [Complete original English–French example](examples/guide/translation.json): all unit types, real table cells and a shared figure
- [Executed preparation and single-unit example](references/example-guide.md): source-only readback first, later one-pair update, and native TeX equivalent
- [Design provenance](references/design-provenance.md): consulted concepts and implementation ownership

The optional helper needs Python 3.11+ and its bundled schema only. No dependency installation or translation service is involved.
