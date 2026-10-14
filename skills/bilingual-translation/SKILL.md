---
name: bilingual-translation
description: Translate source material into one source-first JSONL master. Read complete paragraphs, choose semantic splits, save bounded groups, and review all source/target pairs in a separate pass. Use for new translations and corrections; supplied pairs can go directly to renderers.
---

# Bilingual translation

Preserve original source bytes and supplied translations within the user's scope. Keep language roles separate from display order. Discover installed skills through the host and use their actual paths. Use one working directory per task; commands default to its `master.jsonl` or use the process-level `--master` path.

## Use the supplied commands

Run `python3 -B .../scripts/workflow.py ...` directly through the host execution tool. Read its complete output before choosing the next action. Independent commands and `run` use the same action names and inputs; `run` reads one action object per stdin JSONL line. Each action carries its own tool-provided `ref` when required. See the [command reference](references/workflow.md) for exact inputs.

A batch may include at most one action that returns source/target body text, placed last. Save and next are separate actions: combine them only as explicit JSONL lines. A patch must be followed by reading the changed comparison before acceptance; never patch and accept in the same batch. Export runs separately.

Use the supplied CLI, not helper scripts, loops, pipelines, subprocess drivers or wrappers. Author documented inputs through host file-writing tools or the execution tool's stdin field. Access controlled source, master and workflow state only through documented commands; leave installed tools unchanged. Perform translation and semantic review yourself. See [execution boundaries](references/workflow.md#execution-boundaries).

## Keep one agent in context

By default, the current main agent completes preparation, translation and review. Independent review is a separate comparison pass by that same agent.

Before delegating translation or review, explain the risk of losing whole-source context and introducing inconsistent terminology, style or details; obtain explicit user permission for the proposed scope. Urgency is not permission. Specific approval already in the current request suffices: disclose the risk without asking again. Follow the [context and state rules](references/workflow.md#authorized-delegation).

## Prepare

1. Start with `prepare init`. Read every returned complete paragraph/unit and the final receipt without truncation. Each nonfinal preparation batch contains at least 8192 source codepoints; the final batch may be smaller. Verify extraction against the original, including headings, lists and table cells, and identify unreadable or unsupported material.
2. During that same reading, choose semantic cuts for each unit over 2048 codepoints. Submit exact adjacent `left`/`right` source anchors with `prepare split` before requesting the next preparation batch; the tool locates cuts and checks lengths, so do not calculate offsets manually. Keep sentences, combining sequences and qualifications together; preserve exact whitespace. Every resulting child must fit 2048 codepoints. If an indivisible semantic unit cannot fit, stop for a content decision.
3. Continue preparation with the returned reference until the entire source is read and all required splits are complete. Form concise whole-source context, audience and terminology from that reading using the documented context input. Translation begins only after preparation finishes.

The Markdown importer supports a limited lossless subset. Use an explicit lossless native route for richer content.

## Translate

Run `translate next`. Translate only the active units using the already-read whole-source context. A group contains at most 2048 source codepoints. Preserve IDs and child boundaries; renderers concatenate child targets exactly, so retain needed boundary spaces.

Use `translate save` with the current `ref` and `targets` keyed by active IDs. Saving returns an acknowledgment, not another group. Request `translate next` separately, or supply explicit save and next lines to `run`. Return references unchanged and use identical inputs for an uncertain retry. Saved targets are drafts.

## Review and correct

After all translations are saved, use `review next` for a separate complete comparison of every source/target pair. Its 2048-codepoint grouping budget counts only the source. Read all returned target text without truncation. Check meaning, omissions, qualifications, numbers, names, terminology and cross-unit continuity. For each negation, modal or condition, match the source proposition, its scope and degree of certainty to the target. Resolve who acts or is referred to from the source and surrounding context; preserve uncertainty where the source leaves it open.

Use `review accept` only after comparison. Before correcting, identify the meaning error and its source/context evidence; clearer wording alone does not justify a more specific actor or claim. Use `review patch` with exact `old`/`new` substrings and unit IDs, then read the changed comparison for preserved meaning, scope and reference before accepting in a later call. Leave unchanged target text out of the patch. Recheck locally affected pairs and context for a local issue; use `review restart` with the current delivered review group’s `ref` for widespread or global issues requiring a new complete pass. If review is already complete, first retrieve an existing pair with `review next --units` to obtain that reference. The tool records an attestation, not a judgment of meaning.

Record unresolved issues with `todo add`, scoped to relevant units when possible. Resolve them explicitly with `todo resolve` after checking the repair. Leave uncertainty unapproved; all required current review and todo gates must pass before export.

## Report progress

Read every returned JSONL receipt. For each nonempty `progress` string, send that string to the user before the next tool call. The tool has already chosen the reporting point and formatted the counts; forward all such strings in a response, in order. An identical retry already reported needs no duplicate message. A correction or restart can report a lower review count; forward it too. See the [one-step example](references/workflow.md#progress-updates).

## Hand off

Use `status` to inspect remaining work and `validate --ready` to check current review readiness. Export has a strict review gate; there is no draft-export bypass.

For PDF, discover `bilingual-pdf`, read its skill and pass reviewed JSONL directly with `--translation-skill` set to this installation. Keep JSONL as the master and check actual PDF pages separately from semantic review. See [handoff commands](references/workflow.md#render-or-export).

Native paired TeX remains supported. HTML uses its own layout schema or imports the [semantic exchange](references/semantic-exchange.md), not direct JSONL. Use standalone `export` only when a consumer needs exchange JSON; joined children lose child-level layout hints. The [worked example](references/example-guide.md) illustrates exchange structure and review scope.
