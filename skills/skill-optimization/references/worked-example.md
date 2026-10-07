# Worked example: preserving an activity notice

This is an original illustrative scenario, not an executed test receipt.

## Realistic task

“Using the installed notice-formatting skill, turn the attached plain-text activity notice into an editable handout. Preserve its wording and shared diagram. Then change the afternoon session's seat limit from six to eight without changing the morning session.”

Raw notice:

> Morning session: four seats. Afternoon session: six seats. Return the shared tray after the session. Joining is optional. Diagram labels: A is the entrance; B is the workbench.

Supply an original small diagram containing those labels. Give the agent the notice, diagram, installed skill, normal output requirements, and its permitted working directory. Keep the following evaluator criteria private: exact source preservation, afternoon-only revision, unchanged optional participation and tray referent, correct diagram associations, editable output, and actual rendering readability.

## Observed failure and diagnosis

Suppose the output is readable, but the agent changes both seat limits. An output parser can reproduce the wrong morning value. Reading the draft and action record shows the instruction “update matching quantities” did not identify the affected semantic unit. This supports a scope-selection hypothesis; it does not prove every incorrect edit has that cause.

A useful correction is: “Identify the source unit affected by the requested edit; update that unit and its aligned output, then compare unchanged units with the saved baseline.” Put it in the skill's revision step. Preserve a fixture asserting both changed and unchanged public values, rather than matching the new instruction's wording.

## Fresh comparison

Rerun the reproducing regression and other affected checks, then repeat the user task in a fresh context with the candidate skill. Inspect the complete edited handout, not only the seat limits. If the agent now edits the right unit but introduces needless whole-document regeneration, investigate that cost before adding more rules. A small unrelated numeral elsewhere is a useful neighboring case if accidental global replacement remains a concrete risk.

If the correction fails again, retain the failure evidence and revise or remove that correction. If the selected checks pass and the fresh task reveals no new issue, stop within the stated notice-editing scope. No claim about all document formats follows.

## Compact trial record

Use these fields in the project's existing record, not a mandatory new tracking system:

- Baseline/candidate identity and relevant installed dependencies
- User task and raw input identity; scope and acceptance criteria
- Observed failure; evidence; root-cause hypothesis and confidence
- Small correction and why it should change behavior
- Affected mechanical checks and actual results
- Semantic/visual review scope and remaining uncertainty
- Fresh-context trial outcome; coaching or context limitations, if any
- Tool calls and elapsed time when measured; setup/waiting caveats
- Decision: keep, simplify, revert, continue for a named gap, or stop within tested scope

Review-state timestamps can establish when a file was written, not when a person or model understood its contents. Render success can establish that a file builds, not that its diagram or prose is faithful. Treat those as separate acceptance questions.
