# Templates

Copy these into the private working file. Replace bracketed text.

## Fact sheet

| Fact | Content |
|---|---|
| Primary readers | [R1 role: background; must do after reading] |
| Secondary readers | [R3 role: sections they read] |
| Reading situation | [pre-read / silent meeting read / skim / lookup] |
| Genre and purpose | [proposal / design / guide / reference; decision or action it enables] |
| Scope | [covers …; leaves … to …] |
| Author intent | C1 … C2 … |
| Constraints | W1 … W2 … |
| Sources of truth | [fact or figure → owner, source file, hash] |
| History | [prior decisions, open comments, recurring objections] |
| Success | [each reader answers their task questions and locates the section] |

## Task questions

Write questions a reader of that role must answer to do their job, not questions about wording. Keep the answer key private to the main agent.

| Reader | Question | Expected answer and section |
|---|---|---|
| R1 | [Can I approve this, and what is still missing?] | [C3; section "…"] |
| R2 | [What does step 2 check, and does the figure agree?] | [C6; section "…"] |

Add a question for every sentence changed in the previous round.

## Reader brief

```text
You are a reader of a [genre]. Read only the file below and the images it lists; do not search elsewhere or modify files.

Document: [reader copy path]

Genre: [purpose; what is left to later documents]. [Which figures are prototypes whose text is part of the interface; which are diagrams.]

Recorded items (do not report again; report a related but different issue):
- Decided by the author: [item — rationale]
- Pending author decision: [items]
- Out of scope: [items]

Your role: [role, background, what you must do after reading]. [Read everything. | Skim as you really would and report your reading path.]

Read the whole document and all figures before answering. Output, within [N] words:
1. Retelling: [problem, core mechanism, each diagram step by step].
2. Task questions, each with the section where you found the answer, or "not found": [questions]
3. [Consistency check: for each fact below, list every statement of it in text and figures and say whether they agree: …]
4. Issues not in the recorded items, each quoting the text and naming the type: contradiction, unclear, or missing information needed for your task. Write "none" if there are none.
```

## Round record

| Round | Readers | Class 1 fixed | New pending decisions | Process change |
|---|---|---|---|---|
| 1 | [R1, R2, R3, R4] | [n] | [n] | [what changes next round] |
