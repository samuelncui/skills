# Translation exchange v1

This optional plain-text exchange accompanies the source-first workflow in [SKILL.md](../SKILL.md). Native paired TeX and other lossless native formats are equally valid; they do not have to pass through JSON. This reference, [JSON Schema](../schemas/translation.schema.json), and the runtime define version 1.

## Document and units

Required document keys are `schema_version: 1`, `languages`, ordered `units`, and ordered `blocks`. Only `context` and `source_revision` are optional. Unknown fields are errors. `source_revision` is a nonempty caller-supplied snapshot label, not proof of identity.

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

Text is plain text, including strings that resemble HTML, Markdown or TeX. Renderers must escape it, never execute or interpret it. Nested rich-text objects, inline formatting, formulas, footnotes, spans and nested lists are not representable as rich content in v1. Choose an explicit native route when those semantics matter; do not silently strip or flatten them. Control characters other than tabs/newlines/carriage returns, Unicode surrogate code points and bidi embedding/isolate controls are rejected. Ordinary RTL letters and combining characters remain valid. Direction belongs in explicit language metadata.

`context` is optional, with optional nonempty `summary` and `audience` strings, plus an optional `glossary` array (which may be empty). Each glossary entry contains nonempty `source`, `target`, and optional `note`. It is shared translation context, not rendered source content.

## Structural blocks

Blocks define document reading order. Units are an ordered inventory; references, rather than array positions, determine rendering. Every unit must be used exactly once, including captions and alt text.

- Heading: `{"type":"heading","unit":"intro","level":2}`. The referenced kind is heading, or title at level 1. Levels are integers 1–6. A document title is a title unit referenced by a level-1 heading; there is no separate title field. A title is optional, not inferred.
- Paragraph: `{"type":"paragraph","unit":"p1"}`, referencing kind paragraph.
- List: `{"type":"list","ordered":false,"items":["item-a","item-b"]}`. Items are nonempty, ordered references to list_item units; one unit per original list item.
- Table: `{"type":"table","headers":["h-a","h-b"],"rows":[["r1-a","r1-b"]],"caption":"table-caption"}`. Headers and rows are nonempty; all rows have the same width as headers. Each cell is a table_cell unit. Caption is optional and references a caption unit. Merged cells, multi-level headers and nested cell content require a native route.
- Figure: `{"type":"figure","asset":"assets/diagram.png","caption":"figure-caption","alt":"figure-alt"}`. Caption and alt are required references to caption and alt_text units. One shared figure is used for both languages. The relative asset path is portable ASCII: letters, digits, underscores, hyphens, dots and forward slashes, with no empty, dot or parent segments, leading/trailing slash, URL, query or fragment. Runtime validates the path string only; each renderer must enforce its own realpath/symlink containment, file existence, type and resource limits.

Preserve paragraph, list-item, table-cell and caption boundaries. One execution may process successive units, but each receives a reading of its exact complete source text and needed neighbors, its own translation and semantic review, and a save to the paired master before advancing. This does not require rereading the entire article per unit. The contract proves coverage of the inventory only; compare that inventory with the original source to find extraction omissions.

## States and revision safety

- untranslated: target and target_source_hash are both null.
- draft: target is nonempty and target_source_hash equals current source_hash; semantic review remains open.
- reviewed: target is nonempty and target_source_hash equals current source_hash; a caller has recorded a completed semantic review.
- needs_review: target is nonempty, and target_source_hash may be old, current or null. Preserve the existing target until it is deliberately revised.

Every stored source_hash must match source text. A changed source invalidates an existing target even when the text still looks plausible. Run sync after editing source; it recomputes source_hash, preserves source/target/IDs/order exactly, and marks changed or stale targets needs_review. It never changes target_source_hash or records review. Unchanged targets keep their existing state. Use --in-place to atomically save this state in the same working master; use --output NEW for an optional separate checkpoint. Keep original source inputs separate and unchanged.

After reading a current source/target pair and finishing semantic review, the caller may set target_source_hash to source_hash and status to reviewed. Writing these fields is an attestation, not an automated judgment. Edits to target text require a new review; v1 does not hash target text and cannot detect a forged/stale attestation.

## API and command line

Python 3.11+; no third-party packages or network access are needed. Keep the complete skill directory because the script loads its owned schema.

At the host-discovered installed skill path, import `scripts/translation_contract.py` using a filesystem module loader. Do not assume a sibling installation or repository checkout. Public API:
- `CONTRACT_VERSION = 1`
- `source_digest(text: str) -> str`: exact UTF-8 digest; non-string or invalid Unicode input raises TypeError/UnicodeEncodeError.
- `validate_document(data, require_ready=False) -> list[str]`: no mutation; empty means accepted. Malformed JSON-shaped values return actionable errors. The default permits valid untranslated/draft/needs_review work. `require_ready=True` also requires every target reviewed against the current source.
- `sync_document(data) -> dict`: returns a deep copy or raises ValueError for invalid structure/coverage/state unrelated to source invalidation.
- `record_review(data, unit_id, target, *, reviewed_source_hash) -> dict`: records the caller's completed semantic review for exactly one unit, rejects a changed source hash, and preserves every other unit and exact source text. Returns a deep copy or raises ValueError. It does not translate or judge meaning.
- `save_document(path, data) -> None`: validates and atomically replaces the working master using a temporary file in the same directory, or raises ValueError/OSError. Persist each reviewed unit before advancing. Coordinate a single writer; no concurrent merge is performed. Final-path symlinks are rejected.

From this installed skill directory:

```sh
python3 -B scripts/translation_contract.py validate examples/guide/translation.json --ready
python3 -B scripts/translation_contract.py sync working.json --in-place
# Optional separate checkpoint:
python3 -B scripts/translation_contract.py sync working.json --output updated.json
```

CLI input rejects duplicate object keys and non-finite JSON values. Success exits 0, validation or I/O error exits 1; command-usage errors exit 2. Sync with --output refuses the input path and any existing output path; explicit --in-place atomically updates the working master. Validation checks structure, exact source hashes, target currency and ID coverage. It does not compare input file bytes, inspect assets, certify translation quality, prove factual accuracy, or audit visual rendering.

The schema handles field shape and text constraints; runtime adds unique IDs, reference/kind/coverage checks, rectangular tables and hash/state checks. Use both in repository tests. A schema-only pass is insufficient for readiness.

## Preparation checkpoint and focused authoring helpers

These optional helpers leave exchange version 1 unchanged. First execute source-only preparation and inspect the saved master; only then start writing target content.

```sh
python3 -B scripts/translation_contract.py validate master.json --untranslated
python3 -B scripts/translation_contract.py view master.json --next --context
```

`--untranslated` is mutually exclusive with `--ready`. It checks valid source hashes and that every target/review slot is empty, then reports the exact saved-file hash and unit count. This proves file state at readback, not completeness against the original or what the author previously thought.

`view` takes `--unit ID` or `--next`. It returns the complete current pair without truncation or mutation. The next unit is the first non-reviewed unit in the master's declared unit order. `--context` includes global context/languages; reuse them after the first read. `--neighbors N` adds complete adjacent sources when required. Table cells automatically include source headers and their row. Sources remain authoritative.

After personally reviewing one full pair, `record-review master.json --unit ID --source-hash HASH --target TEXT` updates only that unit through the existing hash-checked API and atomic save, then returns the next unit. It never evaluates meaning or assigns a review score. A changed source is rejected before the file is written. Target text is supplied only for the current reviewed unit. Use direct scoped edits in a native manuscript where more suitable.

Public optional functions: `untranslated_errors(data) -> list[str]`; `unit_view(data, unit_id=None, include_context=False, neighbors=0) -> dict`. The existing `record_review` and `save_document` API remains compatible. A complete/passed record is a caller attestation plus structural checks, not proof of semantic review.

## Alignment units and atomic working blocks

Each paragraph, list item and table cell keeps its own stable ID and target slot. Authoring/persistence can group a short coherent table row with header context, a short header row, or a small coherent list. This is a semantic working block, not a change to the exchange structure. Prose paragraphs stay separate translate/review/save cycles.

The existing API supports one atomic save: load the current master, review the block's exact source/target pairs, compose `record_review` for those IDs in memory, and call `save_document` once after every source-hash check succeeds. Each call returns a copy, so a later stale hash leaves the on-disk master unchanged when saving is deferred until the end. `record-review` CLI remains a single-pair convenience; it is not a requirement to perform one remote operation per cell. See the [row example](example-guide.md#one-short-row-one-atomic-save).

Keep only the active block in the update payload and use a concise readback of its IDs/targets. Whole-document deterministic checks can be batched. Group coherence and translation quality remain caller judgments; the helpers validate recorded states and exact source hashes, not meaning.
