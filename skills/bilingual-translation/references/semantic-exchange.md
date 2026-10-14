# Semantic translation exchange

Use the [source-first JSONL workflow](workflow.md) for translation and review. Export the reviewed master when a consumer needs this plain-text semantic exchange. Keep the JSONL master as source evidence; the export is a renderer handoff, not a second mutable translation workflow.

Native paired TeX and other lossless native formats are equally valid and do not have to pass through JSON. This reference, the [JSON Schema](../schemas/translation.schema.json), and the runtime define the exchange structure.

## Document and units

Required document keys are `languages`, ordered `units`, and ordered `blocks`. Only `context` and `source_revision` are optional. Unknown fields are errors. `source_revision` is a nonempty caller-supplied snapshot label, not proof of identity.

`languages.source` and `languages.target` each contain `tag` (a BCP47-like tag, e.g. en, fr-CA, zh-Hant) and `dir` (ltr or rtl). Tags are syntax-checked, not checked against the IANA registry. Source/target are translation roles, independent of a renderer's left/right or top/bottom order.

Every unit has:
- `id`: unique stable ASCII identifier matching `[A-Za-z][A-Za-z0-9_.:-]*`. Assign it before translation; retain it on edits and reorderings. Do not derive identity from mutable text or array position.
- `kind`: title, heading, paragraph, list_item, table_cell, caption, or alt_text.
- `source`: nonempty exact Unicode source text.
- `target`: nonempty Unicode translation, or null before translation.
- `source_hash`: lowercase SHA-256 of exact source UTF-8 bytes, without whitespace or Unicode normalization.
- `target_source_hash`: the source hash used when producing or reviewing this target, or null if unknown.
- `status`: untranslated, draft, reviewed, or needs_review.
- Optional `locator` and `section`: nonempty descriptive strings locating the unit in the preserved input and its section.

Text is plain text, including strings that resemble HTML, Markdown or TeX. Renderers must escape it, never execute or interpret it. Nested rich-text objects, inline formatting, formulas, footnotes, spans and nested lists are not representable as rich content in this exchange. Choose an explicit native route when those semantics matter; do not silently strip or flatten them. Control characters other than tabs/newlines/carriage returns, Unicode surrogate code points and bidi embedding/isolate controls are rejected. Ordinary RTL letters and combining characters remain valid. Direction belongs in explicit language metadata.

`context` is optional, with optional nonempty `summary` and `audience` strings, plus an optional `glossary` array (which may be empty). Each glossary entry contains nonempty `source`, `target`, and optional `note`. It is shared translation context, not rendered source content.

## Structural blocks

Blocks define document reading order. Units are an ordered inventory; references, rather than array positions, determine rendering. Every unit must be used exactly once, including captions and alt text.

- Heading: `{"type":"heading","unit":"intro","level":2}`. The referenced kind is heading, or title at level 1. Levels are integers 1–6. A document title is a title unit referenced by a level-1 heading; there is no separate title field. A title is optional, not inferred.
- Paragraph: `{"type":"paragraph","unit":"p1"}`, referencing kind paragraph.
- List: `{"type":"list","ordered":false,"items":["item-a","item-b"]}`. Items are nonempty, ordered references to list_item units; one unit per original list item.
- Table: `{"type":"table","headers":["h-a","h-b"],"rows":[["r1-a","r1-b"]],"caption":"table-caption"}`. Headers and rows are nonempty; all rows have the same width as headers. Each cell is a table_cell unit. Caption is optional and references a caption unit. Merged cells, multi-level headers and nested cell content require a native route.
- Figure: `{"type":"figure","asset":"assets/diagram.png","caption":"figure-caption","alt":"figure-alt"}`. Caption and alt are required references to caption and alt_text units. One shared figure is used for both languages. The relative asset path is portable ASCII: letters, digits, underscores, hyphens, dots and forward slashes, with no empty, dot or parent segments, leading/trailing slash, URL, query or fragment. Runtime validates the path string only; each renderer must enforce its own realpath/symlink containment, file existence, type and resource limits.

Preserve paragraph, list-item, table-cell and caption boundaries. The workflow keeps bounded active groups and a separate review pass. The exchange proves coverage of its declared inventory only; compare that inventory with the original source to find extraction omissions.

## States and revision safety

- untranslated: target and target_source_hash are both null.
- draft: target is nonempty and target_source_hash equals current source_hash; semantic review remains open.
- reviewed: target is nonempty and target_source_hash equals current source_hash; a caller has recorded a completed semantic review.
- needs_review: target is nonempty, and target_source_hash may be old, current or null. Preserve the existing target until it is deliberately revised.

Every stored source_hash must match source text. A changed source invalidates an existing target even when the text still looks plausible. Preserve the previous target as evidence until deliberately revised and reviewed. Keep original source inputs separate and unchanged; use the documented workflow for authoring rather than editing exported records to make them appear ready.

A reviewed state is a caller attestation, not an automated judgment. Edits to target text require a new review. This exchange does not hash target text and cannot detect a forged or stale attestation; retain the reviewed JSONL master and its stronger workflow state.

## Read-only consumer API

Python 3.11+; no third-party packages or network access are needed. Keep the complete skill directory because the validator loads its owned schema.

At the host-discovered installed skill path, load `scripts/translation_contract.py` with a filesystem module loader. Do not assume a sibling installation or repository checkout. Consumer entry point:

- `validate_document(data, require_ready=False) -> list[str]`: no mutation; an empty list means accepted. Malformed JSON-shaped values return actionable errors. The default permits valid untranslated, draft and needs_review records. `require_ready=True` also requires every target reviewed against the current source.

Renderer integrations must parse JSON strictly, rejecting duplicate object keys and non-finite values, then call this validator with the readiness required by their documented input policy. This module is not an agent command-line entry point. Translation commands, review and export use `scripts/workflow.py` as documented in the [workflow reference](workflow.md).

Validation checks structure, exact source hashes, target currency and ID coverage. It does not compare input file bytes, inspect assets, certify translation quality, prove factual accuracy or audit visual rendering. The schema handles field shape and text constraints; runtime adds unique IDs, reference/kind/coverage checks, rectangular tables and hash/state checks. Use both in repository tests. A schema-only pass is insufficient for readiness.
