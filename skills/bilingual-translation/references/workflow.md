# Source-first translation workflow

## Agent entry point

Use `scripts/workflow.py` in this installed skill with Python 3.11+ and POSIX locking. Return each tool-provided `ref` or `continue` value unchanged; never generate or modify it. Keep each task's directory and returned work together.

## Execution boundaries

Run each documented `python3 -B .../scripts/workflow.py ...` command directly in its own host execution-tool call. Read the complete returned text yourself before the next step. Command blocks show a sequence, not a batch to paste or automate. Calling the supplied Python CLI directly is the intended tool use.

- Do not drive workflow commands through helper scripts, loops, pipelines, subprocesses or wrappers, even when they call the official CLI in order. Do not change the installed tools or import their internals to operate the workflow.
- Use workflow commands for controlled source, master, receipt, hash and review/state access. Scripts, other commands and direct file reads/edits must not replace them. Restore context through documented workflow options instead of scanning files.
- Use host file-writing tools to prepare documented `context.json`, `splits.json` and active target/correction payloads. Author these inputs from the returned work; do not batch future translations or automatically approve review.
- Read-only calculations may count offsets in text already delivered to your context after you choose a semantic cut. They must not reopen source/master files, replace semantic decisions or advance the workflow.
- On failure, use documented recovery or an identical retry. If unresolved, or a needed capability is missing, report the blocker and ask for direction; do not modify the tool or invent a bypass.

Normal documented steps need no extra confirmation.

## Authorized delegation

Follow the [main-agent default and permission rule](../SKILL.md#keep-one-agent-in-context). For approved work, hand over the full-source background, concepts/glossary, audience, style decisions, user constraints, relevant source text and neighboring passages, and unit boundaries/continuation relationships. The main agent integrates results and remains responsible for whole-document consistency during the required review.

Approval does not change dispatch or concurrency rules: keep writes coordinated through the active group, current references and existing locks; never bypass these gates with parallel work or direct/legacy edits.

## Task directory

Run commands in one dedicated task directory, with `TRANSLATION_SKILL` set to the discovered installed skill path. Use `source.md`, `context.json`, optional `splits.json`, `source-read.json`, `master.jsonl`, and `output/` as a simple convention. Only the default master filename is enforced: master-consuming commands may omit their data argument and use the current directory's `master.jsonl`. An explicit data path still works. No parent-directory search, remembered last task, automatic context/split loading, or file relocation occurs. Keep the execution tool's working directory explicit when it does not persist between calls.

## Prepare the complete source

Preserve UTF-8 bytes and line endings. The importer supports ATX/setext headings, plain paragraphs, flat single-line lists and rectangular pipe tables with nonempty cells. It retains heading ancestry, syntax gaps, blank lines, BOM and CRLF. Inline markup remains literal text. Fenced code, blockquotes, HTML, images, nested/multiline lists and complex tables need an explicit lossless native route.

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" prepare read source.md --receipt source-read.json
# When complete is false, continue with the previous ref:
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" prepare read source.md --receipt source-read.json --continue READ_REF
# While reading, choose semantic splits; form summary/audience/glossary from that reading.
# After the final page, initialize once with context and the split plan:
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" prepare init source.md --receipt source-read.json --read-ref FINAL_REF --output master.jsonl --source-lang en --target-lang fr --context context.json --splits splits.json
```

Uppercase values are placeholders. Read returns exact `text`, `start`, `end`, `complete` and `ref`. An oversized unit is identified on the page where it starts by `oversize` metadata: `id`, `characters`, and `source_span: [start,end]` in the complete original source (end exclusive). Its text may continue on later reading pages; do not treat page boundaries as semantic cuts. Ensure all pages reach you without truncation before initialization. Receipts record delivery and acknowledgment, not comprehension; changed sources need new receipts.

### Choose splits during the first reading

Write `splits.json` as an object mapping every oversized ID to increasing offsets relative to that unit, for example:

```json
{"u000004":[1450,2870]}
```

Choose actual semantic boundaries, not these example positions. Python string indices count Unicode codepoints, not bytes, UTF-16 units or graphemes. Keep complete sentences, combining sequences and qualifications together. Offsets must be strictly increasing and interior; every child must be nonblank and at most 2048 codepoints. Whitespace belongs to exact slices. If an indivisible semantic unit cannot fit, stop for a content decision. Omit `--splits` when no units are oversized.

From the same initial reading, write substantive context in `context.json`:

```json
{"summary":"Community tool-lending procedures and their exceptions.","audience":"Library volunteers","glossary":[{"source":"loan","target":"prêt","note":"Temporary lending, not a financial loan."}]}
```

`summary` and `audience` are optional nonempty strings. `glossary` is optional; each entry needs nonempty `source` and `target`, with optional nonempty `note`. Use the document's actual concepts and languages; no v1 document is needed to supply context. `--context` stores this guidance for translation and review. Language directions optionally use `--source-dir rtl` and `--target-dir rtl`.

Init acknowledges complete reading, validates exact split-plan coverage and lossless reconstruction, and creates the fully split source-only master in one atomic operation. Missing, extra or invalid plans leave no partial master. It never chooses semantic cuts or normalizes text. Children retain parent ID, order, part index and continuation fields as parts of one original paragraph. Init reports `initialized`, the final unit count and an empty `oversize` list. Identical retries replay the original response; changed plans or context cannot overwrite an existing master.

## Translate bounded groups

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" translate next
```

The normal work envelope has `phase`, confirmation-code `ref` and `units`. Each unit includes `id`, `kind` and complete `source`. Split children also include `parent_id`, `part_index` and `has_more`; unsplit units imply parent=id, index=0 and no continuation. Heading levels and list/table positions are included where applicable. Group source totals at most 2048 codepoints. Source is never truncated. Initial phase dispatch includes languages and complete `shared` context. Routine groups do not repeat local headings/table headers; explicit `--context` restores shared guidance and, when available, a local excerpt capped at 1024 codepoints with a truncation flag.

Translate the displayed units, then write a target-only payload:

```json
{"ref":"RETURNED_REF","targets":{"u000001":"First complete target.","u000002":"Second complete target."}}
```

Use the actual reference and all active IDs. Include needed boundary spaces because child strings concatenate without added separators.

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" translate save --payload targets.json
```

Save returns `saved` IDs and `next`. Continue from that envelope; call `next` separately only initially or to resume. Pending work is sticky until saved. A finished phase returns `complete: true` and `next_action`.

Extra fields, wrong IDs, stale references and changed retries fail. Identical replay returns the original response even after later work advances. After resolving an old retry, recover current work with `next` rather than acting on its historical envelope. Preparation reads establish context and splits, not an alternative route to author future targets. Saves create drafts.

## Review all pairs separately

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" review next
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" review accept --ref REVIEW_REF
```

Start after all translation is saved. Compare every source/target pair independently from generation, including meaning, missing/duplicated content, qualifications, terminology and cross-unit continuity. Ordinary review groups contain complete pairs, at most 2048 source and 8192 target codepoints.

An individual target above 8192 codepoints is paginated explicitly: `units[0].target` is the current slice; top-level `target_page` gives start/end/total/complete. The complete source appears on the first page; later pages retain unit identity and page metadata without repeating source or shared context. Explicit `review next --context` can recover source context. Follow `review next --continue TOKEN` using the returned `continue` until the final page supplies an actionable `ref`. Read and compare every page; earlier pages cannot be accepted. Pagination never silently drops target text. If an interrupted review loses earlier page context, use `review next --restart` to reread from page zero; it is mutually exclusive with `--continue` and unnecessary during normal sequential review.

Accept records your attestation against current hashes. Optional `--reviewer NAME` defaults to `translation-agent`; `--note TEXT` describes the review. For corrections use a nonempty subset of displayed IDs:

```json
{"ref":"REVIEW_REF","targets":{"UNIT_ID":"Corrected target."}}
```

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" review revise --payload corrections.json
```

For paginated targets, a correction contains the complete replacement target, not only the displayed slice. Revision preserves source and clears changed review to draft. Accept/revise returns affected IDs (`reviewed` or `revised`) and `next`. Review changed pairs again; unchanged accepted pairs remain reviewed. Revisit a specific saved/reviewed pair with `review next --unit ID`. Another whole-document semantic pass is unnecessary; rendering acceptance is separate.

## Progress updates

Preparation reads and successful save/accept/revise responses may include:

```json
{"progress":{"phase":"translate","completed":42,"total":800,"unit":"units","percent":5}}
```

After reading the complete preparation page or completing the successful mutation, report the phase, completed/total, counting unit and percentage to the user, for example: “Translation: 42/800 units (5%).” Preparation uses `phase: "prepare"` and `unit: "codepoints"`; translation and review use `translate` / `review` and `units`. Split children count separately.

An update appears at roughly each 5% boundary, including 100%, or when correction lowers review completion. Several boundaries crossed by one group need only one report of the actual current count. Small documents may finish in one group. Percent is rounded down; 999/1000 is 99%. `next`, target pagination and errors do not advance completion. Report review decreases explicitly, for example: “Review: 799/800 units (99%). A correction needs review again.” Translation at 100% still needs the separate review pass and `validate --ready`.

Identical retries return the original response, including historical progress. Suppress a repeated user report only for the same task, phase and submitted operation reference (the continuation reference for preparation; none on its first page). Do not deduplicate by completed count: a new correction/re-review can revisit that count. Do not report an old replay as current progress. For translation/review, recover current work with `next`; use `status` for saved/reviewed counts after losing reporting context. For preparation, continue `prepare read` from the current valid reference, not the older replayed page. Do not claim a user update was delivered merely because the tool emitted progress.

## Render or export

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" status
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" validate --ready
```

Status restores shared metadata with `--context`. Validation checks exact source reconstruction, IDs, order, hashes and state, not meaning.

For PDF, discover both installed skills and read the PDF workflow. Set PDF_SKILL and TRANSLATION_SKILL to their actual, potentially unrelated directories:

```sh
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" preflight master.jsonl --translation-skill "$TRANSLATION_SKILL"
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" render master.jsonl --translation-skill "$TRANSLATION_SKILL" --output new-pdf-project
```

PDF directly consumes reviewed JSONL, retains full records and aligns children within their original paragraph. Inspect actual pages through PDF acceptance. Its `export` creates portable native source without compiling; `build` handles repeated managed builds. Follow its structure, language and font limits. Native paired TeX is equally supported.

Only for consumers needing v1 JSON:

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" export --output reviewed-v1.json
```

Export creates a new file and retains the master. Joined children lose child-level layout hints. Default export requires current reviews; explicit `--allow-draft` is only for a requested draft and still rejects empty targets. HTML consumes its own layout JSON or legacy v1 import, not direct JSONL.

## Data access

Keep the JSONL master and use the workflow commands to read or change it. Do not edit controlled source/master/state files directly. After an interrupted write, retry the identical payload, then use `next` to recover current work. Do not mix legacy mutable helpers with this workflow.

Use `export` for consumers requiring legacy v1 JSON. Existing v1 inputs use the separate [v1 APIs](contract-v1.md) and [example](example-guide.md).
