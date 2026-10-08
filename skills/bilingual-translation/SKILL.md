---
name: bilingual-translation
description: Translate source material into a source-first JSONL master with full-source acknowledgment, agent-selected semantic splits, one saved block at a time, stable alignment and separate review. Use for new translations and revisions; supplied pairs can go directly to PDF/HTML renderers.
---

# Bilingual translation

Produce one canonical paired manuscript from preserved source bytes. Keep source and target language roles separate from physical display order. Retain supplied translations within the user's requested scope.

## Prepare the complete source

1. Preserve the original input. Verify extraction against it, including headings, paragraphs, lists, table cells, figures, captions and footnotes. For an excerpt, preserve and read the requested excerpt plus needed context. Label unreadable material.
2. Discover this installed skill through the host. Read [the JSONL workflow and command examples](references/workflow-v2.md). Its helper requires Python 3.11+ on POSIX, without packages or network access.
3. Use `read-source` to receive the complete Markdown source through the tool. Read every returned page in sequence; if `complete` is false, call again with the returned token. Keep the source available. Confirm that tool output is not truncated.
4. After reading all pages, call `ack-source` with the final token and exact source hash. This records delivery and the agent's acknowledgment of this document version; it does not prove understanding.
5. Call `init` to import headings, plain paragraphs, flat list items and simple table cells into source-first JSONL. This saves exact source text, stable IDs and empty target slots, then validates its readback. Record a concise section map, audience and glossary through the optional context file. Rich or nested content that this subset cannot preserve needs an explicit lossless native route; keep original input intact and make that boundary clear.

Use JSONL v2 for the gated workflow. Native paired TeX remains a first-class route when the exchange cannot represent the content. Existing v1 JSON and its original APIs remain supported for compatibility, but do not provide the v2 dispatcher guarantees.

## Resolve oversized source units before dispatch

Call `oversize` after initialization. It lists all source units above 2048 Unicode codepoints; Python string indices count codepoints, not bytes, UTF-16 units or grapheme clusters.

For each oversized unit:
- Read its complete original paragraph through `inspect` as source preparation, using the section context already read.
- Choose semantic split positions yourself, between complete sentences or other complete meaningful units. Keep a sentence, word, combining sequence and its qualifications together. The helper verifies numeric boundaries and lossless reconstruction; semantic boundaries remain the agent's responsibility.
- Pass those explicit offsets, unit ID, source hash and current revision to `split`. Each resulting child must be at most 2048 codepoints. Include all necessary offsets in one call.
- Verify the returned child lengths and reconstructed parent hash. Whitespace belongs to an exact child slice; no text is trimmed, duplicated, normalized or inserted.

Children retain the original parent ID, sequential part index and `has_more`. They remain one original paragraph for rendering. If a complete semantic unit cannot fit the hard limit, leave it blocked and explain what decision is needed; never raise the limit or silently slice it.

## Translate and save the active block

1. Call `next`. It returns exactly one active source unit, at most 2048 codepoints, plus a separately bounded context excerpt (at most 1024 codepoints) and language/ID metadata. Prose children, list items and table cells retain their structural IDs. The source is complete; only the clearly labeled context excerpt may be truncated.
2. Translate only that active unit. Read the exact source, retained whole-document context and needed terminology. For split paragraphs, preserve natural target continuity and put any required boundary whitespace in the target strings themselves: renderers concatenate children without inventing separators.
3. Write a target-only commit payload using the exact block ID, revision, complete source-hash map and active target ID returned by `next`; choose a stable operation ID for retries. Call `commit` and inspect the successful save receipt before authoring the next unit.
4. A repeated `next`, interrupted session or restart returns the same pending block until its target is successfully saved. On an uncertain commit result, retry the identical payload and operation ID. A stale revision, changed hash, malformed or extra ID, or changed retry payload is rejected without advancement.

The dispatcher owns source order and active state. Continue through it rather than preparing future targets with unrestricted file reads or legacy helpers. Preparation inspections and full-source prereading are for comprehension and semantic splitting, not an alternative translation batch.

## Review the saved work separately

Saving a target records `draft`, never `reviewed`. Read the current source/target pair with `inspect`, compare complete meaning, omissions, qualifications, numbers, dates, quantities, units, names, labels, negation, conditions, exceptions and cross-references, and check natural target expression and terminology.

Record a completed review with `review`, using both current source and target hashes. The command records the caller's attestation; it cannot evaluate meaning. Save any pending translation before recording review. For needed corrections, call target-only `revise` with the current revision and both hashes; it preserves the source and resets review to draft. Review the corrected pair again before exporting.

## Reconcile and render

Compare the entire paired master against the preserved original for missing, duplicated or misplaced content. Review cross-child and cross-paragraph transitions and recurring terms. Keep unresolved uncertainty unreviewed.

`validate --ready` and default `export` require all targets saved and currently reviewed. `export --allow-draft` is an explicit review bypass for a requested draft, not a final-quality assertion. Objective validation checks IDs, exact source reconstruction, hashes, state and structural order; semantic, factual, extraction and visual checks stay explicit.

When PDF is requested, discover the installed `bilingual-pdf` and this translation skill through the host, read the PDF skill, and pass the reviewed JSONL master directly to its canonical renderer. Set `PDF_SKILL` and `TRANSLATION_SKILL` to those actual installed directories, which may be unrelated:

```sh
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" preflight master.jsonl --translation-skill "$TRANSLATION_SKILL"
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" render master.jsonl --translation-skill "$TRANSLATION_SKILL" --output new-pdf-project
```

This route preserves aligned children within the same original paragraph and carries the complete translation/review records into the PDF project. Continue the PDF skill's actual-pixel acceptance checks. `export` in the PDF renderer creates an editable native project without compiling if that is the requested deliverable.

Use the translation helper's v1 `export` only for a consumer that needs legacy v1 JSON. It joins each parent's exact child strings, so it omits child-level layout hints; keep JSONL as the canonical master. Existing supplied pairs do not require a new translation. Other renderer choices still follow installed-skill discovery.

## Resources

- [JSONL v2 workflow, schema and commands](references/workflow-v2.md)
- [Legacy v1 exchange](references/contract-v1.md) and [original English–French example](examples/guide/translation.json)
- [Legacy preparation example](references/example-guide.md)
- [Design provenance](references/design-provenance.md)
