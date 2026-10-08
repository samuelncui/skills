# Source-first JSONL workflow v2

Use `scripts/translation_workflow.py` from this installed skill directory. Python 3.11+ and POSIX file locking are required. No network service or dependency installation is involved.

## 1. Deliver and acknowledge the complete source

Preserve the UTF-8 source and its line endings. The importer supports ATX/setext headings, plain paragraphs, flat single-line bullet/numbered list items, and rectangular pipe tables with nonempty cells. Heading levels and ancestry are retained. Markdown syntax gaps, blank lines, BOM and CRLF stay in the lossless source layout. Inline markup is literal plain text, not a rich-formatting representation. Fenced code, blockquotes, HTML, images, nested/multiline lists and complex tables require an explicit lossless native route.

```sh
python3 -B scripts/translation_workflow.py read-source source.md --receipt source-read.json
# If complete is false, read the next page with the exact returned token:
python3 -B scripts/translation_workflow.py read-source source.md --receipt source-read.json --continue PREVIOUS_TOKEN
# After reading every page, use the final page's token and source_hash:
python3 -B scripts/translation_workflow.py ack-source source.md --receipt source-read.json --source-hash SOURCE_SHA256 --token FINAL_TOKEN
python3 -B scripts/translation_workflow.py init source.md --receipt source-read.json --output master.jsonl --source-lang en --target-lang fr
```

Uppercase values here are placeholders for actual returned values. Each read page gives exact `text`, codepoint `start/end`, total length, hash and continuation token. Keep the tool's output allowance large enough for the complete returned JSON; confirm it is not truncated. A page replay with the same continuation is idempotent. A source change requires a new read receipt. Init requires the current complete acknowledgment, creates a new master without overwriting an existing file, and reads the source-only checkpoint back.

The receipt records which text the tool emitted and the caller's explicit acknowledgment. It is not an authentication boundary or proof that a model read, understood or semantically reviewed the text. If a tool truncates or loses output, reread the page before acknowledgment.

Optional `--source-dir rtl` / `--target-dir rtl` controls language direction. Optional `--context context.json` accepts the v1 context shape: summary, audience and glossary. Keep context concise; it helps orientation but never replaces the source.

## 2. Choose semantic splits

```sh
python3 -B scripts/translation_workflow.py oversize master.jsonl
python3 -B scripts/translation_workflow.py inspect master.jsonl --unit u000004
# Choose offsets yourself after reading the original paragraph:
python3 -B scripts/translation_workflow.py split master.jsonl --unit u000004 --offsets 1450,2870 --source-hash UNIT_SHA256 --revision 0
```

Those numbers illustrate syntax only. Use offsets computed for the actual source. Offsets are Python Unicode codepoint indices strictly inside the original string, in increasing order with no duplicates. Booleans, empty/whitespace-only children and children over 2048 codepoints are rejected. The helper slices exact substrings and verifies their concatenation against the original parent hash and length. It never chooses offsets, trims whitespace or claims semantic boundary detection.

Finish preparation splits before requesting the first translation block. Every resulting piece must end at an agent-verified semantic boundary. If an indivisible sentence/semantic unit itself exceeds the cap, keep the workflow blocked and obtain a content decision rather than cutting it arbitrarily. Split returns child IDs, lengths, hashes and continuation fields; the parent remains one structural paragraph.

## 3. Dispatch and save one target

```sh
python3 -B scripts/translation_workflow.py next master.jsonl
```

Read its one complete source block. A pending block is sticky: another `next` returns the identical block ID, revision and source. It does not move forward until the target is saved. Core source text is at most 2048 Unicode codepoints. Context is a separately labeled serialized text excerpt capped at 1024 codepoints, with an explicit truncation flag. There is no neighbor-count or batch-size override.

Construct `target.json` from the returned fields. Example shape (copy real IDs/hashes/revision):

```json
{
  "operation_id": "save-u000001-v1",
  "block_id": "bRETURNED_BLOCK_ID",
  "revision": 1,
  "source_hashes": {"u000001": "RETURNED_SOURCE_SHA256"},
  "targets": {"u000001": "The complete target for this active source."}
}
```

```sh
python3 -B scripts/translation_workflow.py commit master.jsonl --payload target.json
# Only after successful save/readback:
python3 -B scripts/translation_workflow.py next master.jsonl
```

Only the exact active target IDs may be supplied. The payload cannot contain source text, structure, status or replacement document fields. The commit checks the active block ID, exact source hashes and current revision under a stable advisory file lock, writes an fsynced temporary file, atomically replaces the master, and fsyncs its directory. Source, target and dispatcher state live in that same transaction. A killed process leaves either the old pending state or the completed commit; retry the same payload and operation ID to resolve uncertainty. An identical replay returns its original receipt even after later blocks were dispatched; reuse of that operation ID with changed content fails. Competing different commits cannot both win.

The `.lock` sidecar is intentionally retained and unlocked automatically on process exit. Keep all cooperating writers on this protocol. Direct edits/legacy helpers do not participate in locks/CAS, so they are not a concurrent authoring route. Local filesystem atomic replacement and POSIX lock semantics are assumed; other storage backends need their own verified implementation.

A successful save is `draft`, not semantic review. There is no automatic translation service.

## 4. Record review and apply the export gate

Use `inspect` on the saved unit, read its source/target, and review meaning yourself. The response includes current document revision and source/target hashes. Save a pending block before recording review.

```json
{
  "operation_id": "review-u000001-v1",
  "revision": 2,
  "unit": "u000001",
  "source_hash": "CURRENT_SOURCE_SHA256",
  "target_hash": "CURRENT_TARGET_SHA256",
  "reviewer": "translation-agent",
  "note": "Compared meaning, numbers, qualifications and terminology."
}
```

```sh
python3 -B scripts/translation_workflow.py review master.jsonl --payload review.json
python3 -B scripts/translation_workflow.py validate master.jsonl --ready
```

Copy actual revision/hashes rather than those placeholders. `review` changes only the selected review/status, uses the same locking/revision/idempotency discipline, and pins both source and target hashes. Future target edits invalidate this attestation. Recording the review is not automated semantic judgment.

To correct a saved target, call `revise master.jsonl --payload correction.json` with exactly `operation_id`, current `revision`, `unit`, current `source_hash`, current `target_hash`, and the new `target`. Read the current pair first. This target-only CAS change requires no pending block, preserves the source, and clears the prior review to draft. Review the corrected pair again.

## 5. Render the reviewed JSONL directly

For a PDF request, use host skill discovery to locate `bilingual-pdf` and this translation skill, then read the PDF skill's workflow. Set `PDF_SKILL` and `TRANSLATION_SKILL` to their actual installed directories, which may be unrelated. Keep `master.jsonl` as the single translation input:

```sh
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" preflight master.jsonl --translation-skill "$TRANSLATION_SKILL"
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" render master.jsonl --translation-skill "$TRANSLATION_SKILL" --output new-pdf-project
```

The renderer takes JSONL directly and requires current reviewed targets. Its portable project retains the full translation records and aligns paragraph children without creating separate visual paragraphs. Inspect the rendered PDF through the PDF skill's acceptance workflow. Its `export` command can instead create a portable native project without compiling. Follow its explicit supported-language/structure limits and font requirements.

### Optional v1 compatibility export

Only use this when the chosen consumer needs v1 JSON:

```sh
python3 -B scripts/translation_workflow.py export master.jsonl --output reviewed-v1.json
```

Default translation export requires all units currently reviewed. Explicit `--allow-draft` permits saved drafts for a requested draft deliverable but still rejects any empty target. Export creates a new v1 JSON file and leaves the JSONL master intact. It joins children per original parent, losing child-level layout hints; it is therefore not the normal JSONL-to-PDF handoff.

## JSONL representation and public API

The first line is a document record; each remaining line is a unit record. Blank lines may be ignored; duplicate JSON keys, unknown fields, nonfinite numbers and malformed state are errors. [The aggregate JSON schema](../schemas/translation-workflow.schema.json) describes the in-memory shape `{"document": HEADER, "units": [...]}`; JSONL puts HEADER and each unit on their own line. Runtime validation adds cross-record/state/hash checks.

Document fields:
- `record_type: document`, `contract_version: 2`, stable `document_id`, monotonically increasing `revision`
- v1 `languages`, `context` and structural `blocks`; block references identify original parent units in reading order
- `source`: complete original UTF-8 SHA-256, codepoint count and `format: markdown`
- `parents`: ordered original IDs, kind, exact source hash/length and heading ancestry
- `source_layout`: ordered original syntax gaps (`text`) and parent references (`parent`); joins reproduce the entire original source including whitespace
- `preread`: source hash and acknowledgment; `workflow`: active block and idempotent operation receipts

Each unit has:
- `record_type: unit`, `id`, `parent_id`, `part_index` (zero-based), `has_more`, `order`, `kind`, `heading_path`
- exact `source`, `source_hash`, `target` (initially null), `target_hash`, `target_source_hash`
- `status`: untranslated, draft, reviewed or needs_review; `review` null or current source/target hashes, reviewer and note

An unsplit unit has `id == parent_id`, index 0 and false `has_more`. Split children are `PARENT.part0001`, `PARENT.part0002`, etc., contiguous in source order, with true `has_more` except the final child. Concatenate both source and target strings exactly with no inserted separators. Parent source length/hash, child indices, ancestry, structural reading order and whole-source reconstruction are validated. Original parent IDs remain stable; split child IDs are assigned once during source-only preparation.

Load this script by filesystem module loader at the discovered installed skill path:
- `load_jsonl(path, require_ready=False)` returns `{"document": header, "units": records}` or raises ValueError/OSError.
- `validate(data, require_ready=False)` returns valid data or raises ValueError.
- `to_legacy_document(data, require_ready=True)` returns v1 JSON with children joined per original parent. Original source text, parent IDs, kinds, structural order, language roles and aggregate review status survive; child continuation/review metadata remains in the JSONL master.
- CLI helpers `read_source`, `ack_source`, `initialize`, `split_unit`, `next_block`, `commit`, `review` and `revise` implement the documented state transitions.

Do not call the v1 mutable helpers on JSONL. V1 JSON remains usable through its unchanged `translation_contract.py` API, examples and renderers. Its free-selection view/review helpers are legacy compatibility, not the gated workflow.

## Maintained verification

From the repository checkout:

```sh
python3 -B -m unittest discover -s tests -p 'test_translation_workflow.py' -v
```

Tests cover full-source delivery/ack/version gates, structural Markdown import, source-only init, exact Unicode/CRLF reconstruction, explicit split boundaries, 2048 cap, sticky dispatch/restart, target-only exact IDs/hashes/revision, interruption rollback, concurrent commits, idempotency and saved-versus-reviewed gating. These are objective protocol checks; sentence boundaries, translation quality and final PDF pixels require separate agent review.
