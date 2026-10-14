# Translation protocol token benchmark

This is an actual-CLI protocol benchmark with fixed translations, not a live translation-quality evaluation or a bill estimate. Run it explicitly; the installed translation skill still needs only Python's standard library. Its optional benchmark dependency is `tiktoken==0.12.0`, using `o200k_base`.

## Reproduce

From a clean repository checkout, use a private new output directory:

```sh
WORK=$(mktemp -d)
python3 -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install tiktoken==0.12.0
# The tokenizer may download its encoding on first use.
mkdir "$WORK/baseline"
git archive 25fb7db96bc86be93e91abb3c3b6979596901a02 skills/bilingual-translation | tar -x -C "$WORK/baseline"
BASE="$WORK/baseline/skills/bilingual-translation"
"$WORK/venv/bin/python" tests/benchmark_translation_tokens.py \
  --skill "$BASE" --fixtures-skill "$BASE" --mode legacy \
  --output "$WORK/before"
"$WORK/venv/bin/python" tests/benchmark_translation_tokens.py \
  --skill skills/bilingual-translation --fixtures-skill "$BASE" --mode compact \
  --output "$WORK/after" --baseline-summary "$WORK/before/summary.json"
```

Keep both output directories for inspection. They contain exact fixtures, copied implementation snapshots, saved masters, raw command/payload/stdout traces, byte/token counts and SHA-256 identities. The tool refuses to overwrite an output directory. Do not publish private fixtures or raw operational logs. A differing implementation hash requires new evidence for the affected scope. Random references are not fixed or mocked, so reruns can differ by a small number of tokens.

## Measured boundary

- Input: JSON serialization of the executed portable argv, plus each authored target payload, context JSON and split-plan JSON exactly once. Payload JSON is compact UTF-8 in both modes.
- Output: actual CLI stdout, including full-source delivery, preparation, translation, a separate complete review pass, readiness validation and optional legacy export.
- Calls: logical workflow CLI invocations. Separate payload-file writes and outer orchestration calls are excluded.
- Excluded: MCP/shell transport framing, other session instructions, repeated billing of conversation history, hidden reasoning, cached-input treatment, price, rendering and paid/model services. These counts must not be presented as exact account usage or total end-to-end agent tokens.
- Fixed loading: `SKILL.md` plus the mandatory `references/workflow-v2.md`, reported separately. Human README translations are not loaded.
- Body reference: source text and fixed target strings tokenized independently once. These are reference costs, not an additive decomposition of serialized protocol tokens; BPE boundaries and repeated text matter.
- Both modes use the same fixture hashes, targets and review note. The first three fixtures have no optional context; a fourth independently tests a supplied summary, audience and glossary. The benchmark checks complete source delivery, translation/review ID coverage in order, source reconstruction, unchanged fixed translations, reviewed status and default export readiness. It does not merely trust a successful process exit.

## Historical measured result (2026-10-14)

The measurements below identify earlier implementation and instruction snapshots, before the numbered confirmation codes and direct-tool execution rules. The new protocol and fixed-loading totals have not yet been measured; these historical percentages are not claims about the current revision.

Python 3.13.5, tiktoken 0.12.0, o200k_base. Original baseline commit: `25fb7db96bc86be93e91abb3c3b6979596901a02`. Original three baseline workloads were reused unchanged; only the new shared-context fixture required an additional baseline run. No timing or statistical significance claim.

Directly measured implementation SHA-256:
- `scripts/workflow.py`: `80d3809a9e5ea1bbdc50f9a3691b0cd20892f358204a1aafba7892f0cedd98e6`
- `scripts/translation_workflow.py`: `447ad6c9eee22e82ac4d5aa74ca8084ea25605f61d25fd60c4254b3098004b1d`

| Workload | Source characters / units | Protocol tokens before → after | Reduction | CLI calls before → after |
| --- | ---: | ---: | ---: | ---: |
| guide_short | 515 / 15 | 15,913 → 1,757 | 88.96% | 67 → 8 |
| long_semantic_split | 3519 / 3 | 9,256 → 5,018 | 45.79% | 21 → 12 |
| zh_en_structure | 164 / 11 | 12,048 → 2,087 | 82.68% | 51 → 14 |
| shared_context | 176 / 3 | 3,985 → 1,105 | 72.27% | 19 → 10 |

| Workload | Input tokens before → after | Output tokens before → after | Input bytes before → after | Output bytes before → after | Body reference: source + target tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| guide_short | 5,089 → 480 | 10,824 → 1,277 | 15,429 → 1,681 | 28,462 → 4,708 | 119 + 157 |
| long_semantic_split | 2,198 → 1,288 | 7,058 → 3,730 | 7,098 → 4,605 | 24,934 → 15,381 | 775 + 813 |
| zh_en_structure | 3,763 → 670 | 8,285 → 1,417 | 11,485 → 2,378 | 21,597 → 4,560 | 109 + 82 |
| shared_context | 1,286 → 465 | 2,699 → 640 | 4,090 → 1,682 | 7,649 → 2,381 | 37 + 50 |

Historical fixed loading: 4,216 → 3,703 tokens (12.17% reduction). Only instruction text was recounted after the delegation-policy edit; the actual-CLI protocol measurements above are unchanged and were not rerun.
- `SKILL.md`: 972 tokens; SHA-256 `f3f75d6ff30c7267990c7e801eaddcdf0620343fa1d05626289584b72675becd`.
- `references/workflow-v2.md`: 2,731 tokens; SHA-256 `342b1c1941fe525d0d2bd12c165bc24e1da6be3924a80c59c7bd1fb4c55fe7eb`.

## Three-pass body exposure

All candidate units appear once in preparation, once in translation, once in independent review. Targets are authored once and displayed once for review. Normal-path inspections and repeated local source context are zero. Counts below are Unicode codepoints, not tokens. Original syntax/spacing is read once separately.

| Workload | Prepare including syntax | Extra inspection | Translate body | Review body | Target written / read | Syntax read once |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| guide_short | 515 | 0 | 486 | 486 | 573 / 573 | 29 |
| long_semantic_split | 3519 | 0 | 3519 | 3519 | 1089 / 1089 | 0 |
| zh_en_structure | 164 | 0 | 111 | 111 | 383 / 383 | 53 |
| shared_context | 176 | 0 | 169 | 169 | 59 / 59 | 7 |

The guide is its existing plain-text extraction with 15 paragraphs; the Chinese fixture separately exercises actual headings, lists and a table. The long paragraph has 18 station instructions, split after complete instructions 6 and 12. Oversize IDs and source spans arrive with the first reading. Offsets are chosen from retained source text and supplied once through init --splits, which validates and applies all splits atomically. Normal preparation has no separate split or inspect call. Chained next responses are consumed without duplicate standalone next calls.

The shared-context fixture supplies a semantic summary, audience and two terminology entries, not a copy of the manuscript. Its full compact context JSON is 222 characters, emitted exactly twice (444 characters), checked for exact equality at first translation and first review. The authored context is also counted once in input. Repeated terminology guidance is disclosed separately from full body appearances; no later normal block repeats shared context. The other three fixtures use empty shared objects.

Errors, uncertain retries, corrections, explicit recovery and huge-target pagination are not exercised by these normal-path benchmarks. They belong to separate regression evidence. A correction requires renewed review and must not be hidden inside a three-pass normal-path claim.

## Incremental evidence

The final normal path reduces the long workload from 6,013 to 5,018 tokens and 14 to 12 calls by avoiding a repeated paragraph inspection and merging split application into initialization. Removing automatic source-bearing local context reduces the structured workload from 2,307 to 2,087 tokens. Random-reference variation affects differences between runs; savings attributable to individual argument removals are measured separately below. No affected workload has a measured net loss requiring rollback.

Earlier redundant-field removals also had isolated positive savings on identical frozen stdout serialization: unused receipt scalars saved 30/91/116 tokens, default unsplit continuation fields 510/17/374, and duplicate initialization context 28/30/30 for guide/long/structured fixtures. Those attribution measurements are distinct from the actual final CLI totals. Exact content, split-child alignment, shared/recovery context, transaction retries and independent review remain.

All four candidate workloads passed complete prereading, ordered per-unit translation/review exposure, exact fixed targets, source reconstruction and readiness/export assertions. Fixed pairs were reviewed for numbers, dates, conditions, negation, labels and semantic boundaries. Automatic replay measures protocol cost, not fresh-model translation quality, general multilingual quality, accessibility, layout or exact billing.

## Default task directory boundary

The final candidate above was actually executed with the optional data argument omitted, in a separate working directory for every workload. Initial source reads, initialization output, context and split-plan inputs remain explicit. The baseline continues to use its original required data argument.

Removing only the data argument from the same frozen argv saves exactly 4 input tokens per affected call: 24, 40, 48 and 32 tokens for guide, long, structured and shared-context workloads. This is a small convenience improvement, not a reduction in calls or output. Actual run-to-run totals also vary with random references, so their entire difference is not attributed to the default argument.

The table uses an executed portable relative script path. It excludes the longer discovered installation path that a real host may need, the NAS wrapper's repeated working-directory field, and all outer MCP framing. A host that repeats its full task directory has not eliminated that directory cost by moving it outside the CLI. Keep one task directory per manuscript; no global active-project state or persistent shell is assumed.

## Context-shape instruction locality

At the context-shape-only revision, adding the minimal context JSON and field constraints added 94 tokens to the two-file entry load (3,321 to 3,415). The separate legacy `contract-v1.md` is 2,506 tokens. For a cold reader that previously opened that whole legacy reference only to learn the context shape, this avoids a net 2,412 tokens of instruction text: 3,321 + 2,506 versus 3,415. This conditional comparison is not an actual account bill or a measurement of every reference a cold agent might read.

The main fixed-loading table has always counted only SKILL plus workflow-v2, excluding contract-v1. Do not add this conditional avoidance again to the main baseline reduction. Legacy consumers may still need contract-v1; the optimization removes that dependency only from the normal v2 context-authoring path. No code or protocol measurement was rerun for this documentation-only change.

## Delegation instruction boundary

The main-agent default, explicit delegation consent and context/state handoff guidance add 288 instruction tokens to the preceding 3,415-token revision. The historical fixed-loading count above includes this addition; human README translations remain excluded. That documentation-only revision left scripts, schemas, fixtures and CLI protocol unchanged, so its original executed evidence was retained. This documentation-only recount does not test fresh-agent compliance or translation quality.
