---
name: skill-optimization
description: Improve an agent skill through realistic blank-context use, observed failure diagnosis, small corrections, and fresh trials. Use when a skill's reliability, clarity, or execution cost needs evidence-based improvement.
---

# Skill optimization

Make the correct workflow easier to execute. Improve a skill from observed use, with the smallest change that addresses the cause and preserves working behavior.

## Establish the trial

1. Read the skill, relevant references, repository rules, and current changes. Identify the permitted edits, required guides/licenses/localizations, and release gates. Keep other owners' work intact; use an isolated candidate. Preserve the baseline and identify each tested skill/dependency snapshot.
2. Choose a realistic user task and raw, rights-cleared inputs that exercise the behavior in question. Include the relevant ordinary case and boundary or follow-up edit. Define observable acceptance criteria before seeing the output. Keep evaluator expectations separate from the task given to the trial agent.
3. Start a fresh context with only the user task, installed skill, declared dependencies, raw inputs, and actual environment/permission constraints. Discover dependencies as a user would; exclude repository helpers, prior conclusions, worked answers, and proposed fixes. Blank context means no previous task reasoning, not missing necessary user information. Obtain any required permission for agent execution, services, or cost first. If fresh execution is unavailable, label the substitute and its limits.

## Observe and diagnose

Let the agent complete the task without coaching toward the expected answer. Retain useful actions, failures, outputs, and input identities in the existing private project record. Review the actual artifacts, not only the agent's summary or completion flags.

Separate two kinds of evidence:
- Mechanical checks establish contracts such as parseability, coverage, stable IDs, preserved inputs, build success, dependency isolation, and observable action order. Use maintained executable assertions in the project's native runner, batched into bounded invocations.
- Semantic, factual, language, visual, and usability review establishes qualities the mechanical checks cannot prove. Inspect the relevant source/output pairs or actual rendered pixels. State what was reviewed and what remains uncertain. A recorded review flag proves a recorded state, not the quality or timing of the reasoning.

For each failure, record expected versus observed behavior and supporting evidence. Distinguish a skill defect from an implementation, fixture, evaluator, installation, environment, or task ambiguity. Name a root-cause hypothesis and a discriminating check; a single symptom does not establish its cause. Keep blocked infrastructure separate from product failures.

## Make one useful correction

Describe the correct action, its inputs, and the next observable checkpoint in concise, positive instructions. Place it at the decision that went wrong. Prefer a small change to the owning instruction, helper, or example over repeated warnings and unrelated requirements. Generalize only as far as the evidence supports.

Preserve permission boundaries and existing quality checks. Where sequencing matters, specify the executed checkpoint rather than relying on a script's textual order or self-reported flags. Where overhead matters, batch deterministic work and use coherent semantic units without weakening review. Add a maintained reproducing regression when feasible; establish that the baseline fails for the intended reason.

## Retest and decide

Run the affected regressions after the final relevant edit, then give a fresh agent the same realistic task with the candidate snapshot and no diagnostic hints. Compare outcome, review quality, and relevant execution cost with the baseline. Extend to a neighboring case only for a concrete uncovered risk. Preserve evidence that remains valid for unchanged inputs; broaden to integration/release gates when required.

Keep an effective correction. Revert or simplify ineffective additions, redundant cautions, and overhead that does not improve the intended behavior. Diagnose regressions before continuing; never weaken an acceptance check just to obtain a pass. Repeat the focused cycle only while an observed failure or explicit coverage gap remains.

Stop when the agreed representative scope passes its required checks and fresh trials reveal no new actionable issue in that scope. This is a scoped result, not a guarantee for every task, language, environment, or future model. Report unresolved or blocked checks; do not silently shrink the scope to call it complete.

## Report evidence and cost

Use a short existing-project note: tested snapshot; task/coverage; observed issue and cause confidence; correction; mechanical results; semantic/visual review; fresh-trial result; cost; remaining limits. Distinguish passed, failed, skipped, blocked, incomplete, and not run, and reused evidence from new runs.

Select trial breadth for distinct risks rather than a fixed sample count. Include preparation, tool round trips, waiting, execution, diagnosis, and rework where material. Measured task wall time is not pure model time or a controlled benchmark. Repeat a costly run for changed relevant inputs or a stated unresolved question, not to accumulate favorable results.

For an illustrated cycle and a compact record, read [the worked example](references/worked-example.md). Keep private raw trials separate from published skill files; publish only authorized, sanitized examples and summaries. This workflow does not authorize commit, publication, or new execution environments.
