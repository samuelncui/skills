---
name: bilingual-translation
description: Translate source material into one source-first JSONL master. Read the complete source, choose semantic splits, save bounded groups, and review all source/target pairs in a separate pass. Use for new translations and revisions; supplied pairs can go directly to renderers.
---

# Bilingual translation

Preserve original source bytes and supplied translations within the user's scope. Keep language roles separate from physical display order. Discover installed skills through the host; use their actual paths. Use a separate working directory per task. Master-consuming commands default to its `master.jsonl`; explicit paths remain supported. Preparation inputs stay explicit.

## Use the workflow as supplied

During a translation task, directly run one documented `python3 -B .../scripts/workflow.py ...` command per host execution-tool call. Read its complete response before deciding the next step. The supplied Python CLI itself is allowed; helper scripts, loops, pipelines, subprocesses and wrappers must not drive it. Use host file-writing tools for documented context, split and active target/correction inputs. Access controlled source, master, receipts and review/state only through the workflow commands; do not substitute other commands or direct file edits. Keep installed scripts unchanged and perform semantic translation/review yourself. Follow the [execution boundaries](references/workflow.md#execution-boundaries).

## Keep one agent in context

By default, the current main agent completes preparation, translation and review without asking about delegation. Independent review means a separate reading/comparison pass by that same agent, not a second agent.

Before using subagents, including for speed or work with little context dependence, explain that they may lose whole-source context and introduce inconsistent terminology, style or details; ask for and obtain explicit user permission for the proposed scope. Urgency or a general task request is not permission. Specific translation-delegation approval already in the current request suffices: disclose the risk without asking again. Delegate only that scope under the [context and state rules](references/workflow.md#authorized-delegation).

## Prepare

1. Use `scripts/workflow.py` and the [command reference](references/workflow.md). Make `prepare read` the first complete-source reading; follow every page without tool truncation. Verify extraction against the original, including headings, paragraphs, lists, tables, figures, captions and notes; label unreadable material.
2. During that reading, use returned oversized-unit IDs and source spans to choose semantic cuts. Record relative offsets in `splits.json`; reading-page boundaries are not semantic cuts. Each child must fit 2048 Unicode codepoints. Keep sentences, combining sequences and qualifications together; preserve whitespace exactly. If an indivisible semantic unit cannot fit, stop for a content decision.
3. From the same reading, write a concise concept/section summary, relevant audience and terminology into `context.json`, using the reference's context shape. After the complete source is read, call `prepare init` with the final read reference, `--context context.json` and, if needed, `--splits splits.json`. It atomically validates the complete split plan and creates the source-only master. Shared context appears at the first translation/review dispatch; explicit `--context` restores lost context. Apply all chosen splits during initialization.

The importer supports a limited lossless Markdown subset; native paired TeX remains an equal route for richer content.

## Translate

Run `translate next`. Translate only its active units using the already-read whole-source context. A group may contain several units, totaling at most 2048 source codepoints. Preserve IDs and child boundaries; renderers join child targets exactly, so include needed boundary spaces.

Submit `{ref, targets:{ID:TEXT}}` through `translate save --payload FILE`. Its successful response includes the next group: continue from it without another routine `next`. After interruption, `next` recovers pending work. Retry uncertain saves with identical payloads. Return the complete tool-provided `ref` unchanged; never generate or modify it. Saved targets are drafts.

## Review independently

After translation is saved, run `review next`. In one separate complete pass, compare every source/target pair for meaning, omissions, qualifications, numbers, names, negation, conditions, references and natural terminology. Check structural completeness and cross-unit continuity against the preserved source within this pass. Follow any review pagination to its final page before accepting.

Use `review accept` after comparison or `review revise` for corrections. Each response supplies the next work. Re-review changed pairs and affected context; another duplicate whole-document semantic pass is unnecessary. The tool records your attestation, not a judgment of meaning.

## Report progress

After fully reading a preparation page or successfully saving/accepting/revising work, send any returned `progress` to the user as phase, completed/total, counting unit and percent. Updates occur around each 5% boundary and at completion; a group crossing several boundaries needs one current update. Preparation counts source codepoints; translation counts saved units; review counts currently reviewed units, including split children.

Suppress duplicate reports only for retries of the same task, phase and submitted reference (preparation continuation reference). A correction can lower review completion: explain the rollback and review the changed pairs again. A new operation reaching a previously reported count needs a new report. Do not report an old replay as current progress. For translation/review, recover current work with `next`, or `status` for saved/reviewed totals after losing context. For preparation, continue `prepare read` from the current valid reference, not an older replayed page. Translation at 100% still requires the separate review pass and ready validation. See [progress examples](references/workflow.md#progress-updates).

## Hand off

`status` reports remaining work; `validate --ready` requires all current targets reviewed. Keep uncertainty unreviewed.

For PDF, discover `bilingual-pdf`, read its skill and pass reviewed JSONL directly with `--translation-skill` set to this installation. Keep JSONL as the master. PDF acceptance checks actual page pixels, separately from semantic review. See [handoff commands](references/workflow.md#render-or-export).

Native paired TeX remains supported. HTML uses its own layout schema or imports the [semantic exchange](references/semantic-exchange.md), not direct JSONL. Use `export` when a consumer needs semantic exchange JSON; joined children lose child-level layout hints. The [worked example](references/example-guide.md) illustrates exchange structure and pair-review scope.
