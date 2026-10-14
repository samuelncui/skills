# Source-first translation workflow

## Agent entry point

Use this installed skill's `scripts/workflow.py` with Python 3.11+ and POSIX locking. Set `TRANSLATION_SKILL` to its discovered installation and run in one dedicated task directory. Commands use `master.jsonl` there by default; select another master with the process-level `--master PATH` before the command. Actions cannot change the master inside a batch.

Return tool-provided references unchanged. A reference belongs to its action and current work; do not invent one or substitute a reference from another task. The commands expose short references while validating their full state bindings internally.

## Output defaults

Output is JSONL: each body record has `record_type: "unit"`; each command ends with a `record_type: "receipt"` record. Omitted unit metadata means `parent_id` equals its `id`, `part_index` is `0`, and `has_more` is `false`. Real parent links, nonzero child indices and `has_more: true` remain explicit; `heading_path` is retained. Omitted receipt `context`, `pending` and `oversize` mean `{}`, `[]` and `[]` respectively. Nonempty context and all references and progress remain explicit. Save and accept receipts report `saved` or `accepted` as a count of the submitted/current group, without repeating its IDs. These output defaults do not alter the stored master or lossless continuation rules.

## Execution boundaries

Run one documented CLI invocation directly per host execution-tool call, then read its complete output. An invocation may be an independent command or the supplied `run` command. Use the execution tool's stdin field for JSONL, or a host-authored input file with ordinary stdin redirection. Read all returned unit records and the final receipt without tool truncation before choosing another action.

- The supplied CLI is the workflow driver. Do not replace it with helper scripts, loops, pipelines, subprocess drivers, wrappers or imports of its internals; leave installed tools unchanged.
- Read and change controlled source, master, receipts, hashes and review/state through documented commands only. Restore context through the workflow rather than scanning controlled files.
- Author documented context, action and translation inputs through host file-writing tools or stdin. Derive them from work already delivered to your context; do not prewrite future translations or automate semantic approval.
- Choose semantic split locations yourself; the tool locates exact anchors and counts codepoints. It does not choose meaningful cuts for you.
- On failure, follow the diagnostic or retry identical inputs when the outcome is uncertain. If the supported route remains blocked, report it and ask for direction; do not bypass it by editing controlled files.

Normal documented steps need no extra confirmation. The actor boundary does not prohibit repository engineering tests from exercising the official CLI programmatically.

## Independent commands and JSONL batches

Each input line is one JSON object with `op` equal to the command name, including its space:

```json
{"op":"translate save","ref":"RETURNED_REF","targets":{"u000001":"Complete target."}}
{"op":"translate next"}
```

Run those two lines with:

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" run
```

Pass the JSONL through stdin. For an independent command, pass one matching object through stdin, for example `translate save` with only the first line. The stdin object includes the same matching `op`; choose either flags or one stdin object, not both. Independent flags are generated from the same command configuration; use that command's `--help` for their spelling. No-argument commands such as `translate next` do not require stdin.

Each action carries its own `ref` when required. There is no batch-wide reference. Save and accept produce acknowledgments; neither implicitly retrieves another group. To save and advance in one invocation, explicitly include the two lines shown above.

`run` applies one same-master transaction through the same handlers as independent commands. A failed action does not commit a partial batch. Plan the whole batch using information already read:

- At most one action may return source/target body text; put it last.
- Read the result before constructing another body-dependent action. Do not try to consume a reference that this same batch has not yet returned.
- Never combine `review patch` and `review accept` in the same batch. After a patch, retrieve and read the changed source/target comparison before accepting in a later invocation.
- `export` is standalone and cannot appear in `run`.

The commands are `prepare init`, `prepare split`, `translate next`, `translate save`, `review next`, `review accept`, `review patch`, `review restart`, `todo add`, `todo resolve`, `status`, `validate` and `export`.

## Authorized delegation

Follow the [main-agent default and permission rule](../SKILL.md#keep-one-agent-in-context). For approved work, provide full-source background, concepts/glossary, audience, style decisions, user constraints, relevant source and neighboring passages, and unit boundaries/continuation relationships. The main agent integrates results and remains responsible for whole-document consistency.

Approval does not bypass active-group references, locking or coordinated writes. Do not use parallel writes or direct edits to evade those gates.

## Prepare the complete source

Preserve UTF-8 bytes and line endings. The importer supports ATX/setext headings, plain paragraphs, flat single-line lists and rectangular pipe tables with nonempty cells. It preserves heading ancestry, syntax gaps, blank lines, BOM and CRLF; inline markup remains literal text. Fenced code, blockquotes, HTML, images, nested/multiline lists and complex tables require an explicit lossless native route.

Start preparation with an independent `prepare init` and a single input object:

```json
{"op":"prepare init","source":"source.md","source_lang":"en","target_lang":"fr","source_dir":"ltr","target_dir":"ltr","context":{"audience":"Library volunteers"}}
```

It returns complete source units, not slices at arbitrary character boundaries. Each nonfinal batch contains at least 8192 source codepoints; the final batch may be smaller. A long paragraph remains complete in the output. Ensure the execution tool can deliver all of it without truncation. Read the entire batch and final receipt, verify the extraction, and choose semantic cuts immediately for any unit exceeding 2048 codepoints.

### Split by exact adjacent anchors

```json
{"op":"prepare split","ref":"PREPARATION_REF","unit":"u000004","cuts":[{"left":"The first complete sentence. ","right":"The next sentence begins"}]}
```

Replace these illustrative strings with exact adjacent fragments from the delivered unit. `left` ends exactly at the cut and `right` begins there. Their joint occurrence must identify one unique location. Keep spaces and punctuation exactly: a space included at the end of `left` belongs to the preceding child; one at the beginning of `right` belongs to the next child. Do not normalize or repeat boundary whitespace.

Choose cuts between complete semantic units, preserving sentences, combining sequences and qualifications. The tool locates the anchors, computes offsets and lengths, and verifies exact reconstruction and children of at most 2048 source codepoints. You do not calculate offsets or count 2048 characters manually. Supply enough ordered cuts to make every child fit. Ambiguous anchors need longer exact neighboring fragments; an oversized result needs another meaningful cut. Diagnostics identify the problem without routinely repeating the complete paragraph. If no meaningful split can satisfy the limit, stop for a content decision.

Finish splitting the current batch before continuing preparation. The current preparation reference remains valid for the units in that delivered batch; each split action still carries its own `ref`. Do not use it after advancing to another batch. Advance with:

```json
{"op":"prepare init","ref":"CURRENT_PREPARATION_REF"}
```

Continuation uses `ref`, without resupplying source/language initialization fields. It may include an updated `context` object. Preparation can report complete on the final read or its last required split; before translating, an extra `prepare init` with that current reference may update the final context without rereading source. From this same complete-source reading, form a concise final summary, audience and glossary, and supply the updated context on the appropriate continuation:

```json
{"op":"prepare init","ref":"CURRENT_PREPARATION_REF","context":{"summary":"Community tool-lending procedures and their exceptions.","audience":"Library volunteers","glossary":[{"source":"loan","target":"prêt","note":"Temporary lending, not a financial loan."}]}}
```

`summary` and `audience` are optional nonempty strings. Each glossary entry needs nonempty `source` and `target`, with optional nonempty `note`. Use the actual document's concepts and languages. Keep reading and splitting until preparation reports completion; then translate. Children retain their original parent and order and concatenate losslessly into that original unit.

## Translate bounded groups

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" translate next
```

Read all dispatched units and the receipt. A group totals at most 2048 source codepoints. Preserve IDs, structural positions and split-child continuation boundaries. Use already-read whole-source context and supplied guidance. Keep the language/context metadata returned with the initial phase dispatch available for later groups. After context loss, use `translate next --context` or `review next --context` to return the stored languages and context explicitly with the current work.

Submit translations only for the active IDs:

```json
{"op":"translate save","ref":"TRANSLATION_REF","targets":{"u000001":"First complete target.","u000002":"Second complete target."}}
```

Run this with independent `translate save`, or as the first line of a `run` followed by `{"op":"translate next"}`. Include boundary spaces needed when child targets are concatenated; the renderer adds no separators. Saves are drafts and return an acknowledgment. Request another group explicitly.

Wrong IDs, extra fields, stale references and changed retries fail. Retry an uncertain operation identically, then recover current work rather than treating a historical replay as a fresh dispatch. Preparation is for reading and semantic splitting, not a route to author future targets ahead of the active group.

## Review all pairs separately

After all targets are saved:

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" review next
```

Review uses at most 2048 source codepoints per group; target length does not reduce that budget. Complete targets are returned without target pagination. Read the entire response and compare meaning, omissions/duplication, qualifications, numbers, names, negation, conditions, terminology and cross-unit continuity independently from translation. A tool receipt proves delivery/state, not comprehension.

Within this comparison pass, match each source clause to its target proposition: who does what, to whom, under which condition, with what polarity and degree of certainty. For negation and modal expressions, identify exactly which proposition they modify and check that the target preserves that scope; a fluent sentence can still reverse or strengthen a claim. Resolve pronouns and implicit actors using the source and relevant surrounding passages. When the source remains ambiguous, retain that ambiguity or record a todo rather than inventing a more specific actor.

After reading the comparison, acknowledge it with:

```json
{"op":"review accept","ref":"REVIEW_REF"}
```

Acceptance records your attestation against current content. It returns an acknowledgment, not another group. Request `review next` explicitly, or put that action last after acceptance in `run`.

### Exact local corrections

```json
{"op":"review patch","ref":"REVIEW_REF","edits":[{"unit":"u000001","old":"an incorrect phrase","new":"the corrected phrase"}]}
```

Before proposing a patch, identify the specific defect and the source/context evidence that establishes the intended meaning or referent. Change only what that evidence supports. On the required post-patch read, compare the revised target back to the source proposition, negation/modal scope, conditions and actor/reference; improved fluency is not sufficient evidence of a correct repair. This is part of the existing local re-review, not an additional full-document pass.

Use exact substrings from the displayed target. Each `old` must match exactly once; multiple edits are located against the same current target and must not overlap. Avoid repeating the unchanged whole target. The tool checks the old text against current content and leaves changed units requiring review. Retrieve and read their changed source/target comparison, then accept in a later invocation; patching is never itself approval.

For a local issue, recheck the affected pairs and needed surrounding context. Unchanged accepted content need not be redundantly reviewed. For widespread errors, a global terminology/style change or loss of confidence in the complete review, use `review restart` and perform a new whole-document comparison. Restart requires the `ref` from a currently delivered review group. It can discard that active group without accepting it and marks every pair for a new review round; call `review next` afterward. It does not resolve open todos. Do not label a global problem as a local correction to keep an old completion count.

To restart and explicitly retrieve the first group in one invocation, pass these two lines to `run`:

```json
{"op":"review restart","ref":"CURRENT_REVIEW_REF"}
{"op":"review next"}
```

If the full review is already complete, first call `review next` with `{"op":"review next","units":["UNIT_ID"]}` for an existing unit, read that comparison and use its returned `ref` for restart. Retrying the identical restart-and-next packet replays its original receipt and reference without opening another review round. `status` does not supply a replacement reference.

### Track unresolved issues

```json
{"op":"todo add","ref":"CURRENT_REF","text":"Verify the exception against the source.","units":["u000001"]}
```

Use the active read group’s `ref`. Optional `units` must name units in that group; omitting it records a global issue. Resolve a scoped issue only after reading all its units together and checking the outcome:

```json
{"op":"todo resolve","ref":"CURRENT_REF","id":"RETURNED_TODO_ID"}
```

To revisit a saved or reviewed pair, use `review next` with `{"op":"review next","units":["u000001"]}` when no other group is active. The returned group supplies the current review reference; use that reference to patch or resolve a todo. A scoped todo requires all its named units in the active group.

Open todos block ready validation and export. They do not prevent accepting other pairs that you have actually read and checked. Resolving a todo does not replace required review of changed text.

## Progress updates

Read each JSONL receipt in the tool response. If its `progress` is nonempty, send that exact string to the user before making the next tool call. Forward each new progress string in receipt order; the tool has already selected the reporting point and computed the counts.

For example, a receipt containing `"progress":"review 5/22 units (22%)"` means: send “review 5/22 units (22%)” to the user, then continue the workflow.

An identical operation retry returns the same progress; suppress it only if that operation's update was already reported. A correction or restart can lower the count, for example `review 0/22 units (0%)`; this is a new update to forward. Preparation uses `codepoints`, and translation/review use `units`. Translation at 100% still requires the separate review and ready validation. After losing reporting context, use `status` for current totals rather than treating an old replay as new progress.

## Render or export

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" status
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" validate --ready
```

Validation checks exact source reconstruction, identities, ordering, hashes, current review and unresolved todos; it does not judge translation meaning. Keep the master as source evidence.

For PDF, discover both installed skills and use their actual, potentially unrelated paths:

```sh
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" preflight master.jsonl --translation-skill "$TRANSLATION_SKILL"
python3 -B "$PDF_SKILL/scripts/bilingual_pdf.py" render master.jsonl --translation-skill "$TRANSLATION_SKILL" --output new-pdf-project
```

PDF directly consumes reviewed JSONL, preserves full records and aligns children within their original paragraph. Follow its language, structure and font limits and inspect actual pages. Its own `export` creates portable native source without compiling; `build` handles repeated managed builds. Native paired TeX remains equally supported.

When another consumer needs semantic exchange JSON, use standalone:

```sh
python3 -B "$TRANSLATION_SKILL/scripts/workflow.py" export --output reviewed-exchange.json
```

Export creates a new file and retains the JSONL master. It requires current complete review and resolved todos; no draft-export bypass exists. Joined children lose child-level layout hints. HTML consumes its own layout JSON or imports this [semantic exchange](semantic-exchange.md), not direct JSONL. See the [worked exchange example](example-guide.md).
