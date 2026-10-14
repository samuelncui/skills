---
name: bilingual-translation
description: Translate source material into one source-first JSONL master. Read the complete source, choose semantic splits, save bounded groups, and review all source/target pairs in a separate pass. Use for new translations and revisions; supplied pairs can go directly to renderers.
---

# Bilingual translation

Preserve original source bytes and supplied translations within the user's scope. Keep language roles separate from physical display order. Discover installed skills through the host; use their actual paths. Use a separate working directory per task. Master-consuming commands default to its `master.jsonl`; explicit paths remain supported. Preparation inputs stay explicit.

## Keep one agent in context

By default, the current main agent completes preparation, translation and review without asking about delegation. Independent review means a separate reading/comparison pass by that same agent, not a second agent.

Before using subagents, including for speed or work with little context dependence, explain that they may lose whole-source context and introduce inconsistent terminology, style or details; ask for and obtain explicit user permission for the proposed scope. Urgency or a general task request is not permission. Specific translation-delegation approval already in the current request suffices: disclose the risk without asking again. Delegate only that scope under the [context and state rules](references/workflow-v2.md#authorized-delegation).

## Prepare

1. Use `scripts/workflow.py` and the [command reference](references/workflow-v2.md). Make `prepare read` the first complete-source reading; follow every page without tool truncation. Verify extraction against the original, including headings, paragraphs, lists, tables, figures, captions and notes; label unreadable material.
2. During that reading, use returned oversized-unit IDs and source spans to choose semantic cuts. Record relative offsets in `splits.json`; reading-page boundaries are not semantic cuts. Each child must fit 2048 Unicode codepoints. Keep sentences, combining sequences and qualifications together; preserve whitespace exactly. If an indivisible semantic unit cannot fit, stop for a content decision.
3. From the same reading, write a concise concept/section summary, relevant audience and terminology into `context.json`, using the reference's context shape. After the complete source is read, call `prepare init` with the final read reference, `--context context.json` and, if needed, `--splits splits.json`. It atomically validates the complete split plan and creates the source-only master. Shared context appears at the first translation/review dispatch; explicit `--context` restores lost context. Normal preparation needs no separate inspect/split calls.

The importer supports a limited lossless Markdown subset; native paired TeX remains an equal route for richer content.

## Translate

Run `translate next`. Translate only its active units using the already-read whole-source context. A group may contain several units, totaling at most 2048 source codepoints. Preserve IDs and child boundaries; renderers join child targets exactly, so include needed boundary spaces.

Submit `{ref, targets:{ID:TEXT}}` through `translate save --payload FILE`. Its successful response includes the next group: continue from it without another routine `next`. After interruption, `next` recovers pending work. Retry uncertain saves with identical payloads. Short references bind internal revision, IDs and hashes; validation remains intact. Saved targets are drafts.

## Review independently

After translation is saved, run `review next`. In one separate complete pass, compare every source/target pair for meaning, omissions, qualifications, numbers, names, negation, conditions, references and natural terminology. Check structural completeness and cross-unit continuity against the preserved source within this pass. Follow any review pagination to its final page before accepting.

Use `review accept` after comparison or `review revise` for corrections. Each response supplies the next work. Re-review changed pairs and affected context; another duplicate whole-document semantic pass is unnecessary. The tool records your attestation, not a judgment of meaning.

## Hand off

`status` reports remaining work; `validate --ready` requires all current targets reviewed. Keep uncertainty unreviewed.

For PDF, discover `bilingual-pdf`, read its skill and pass reviewed JSONL directly with `--translation-skill` set to this installation. Keep JSONL as the master. PDF acceptance checks actual page pixels, separately from semantic review. See [handoff commands](references/workflow-v2.md#render-or-export).

Native paired TeX remains supported. HTML uses its own layout schema or legacy v1 import, not direct JSONL. Use `export` only for consumers needing v1 JSON; joined children lose child-level layout hints. Existing [v1 APIs and example](references/contract-v1.md) are compatibility routes separate from the gated workflow.
