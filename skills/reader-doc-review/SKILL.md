---
name: reader-doc-review
description: Review and revise one document for its real readers through fresh-context reader trials, triage and fix cycles until a round finds no new issue. Use for any topic, format or source (proposal, design, guide, README, policy, manual) when the document should work for named readers, not for an isolated wording fix.
---

# Reader-based document review

Make a document work for the people who will read it. Each round gives fresh readers the document and real tasks, triages what they report, fixes the document, verifies the edit, and improves the next round. Stop when a round finds nothing new.

Writing to a shared or published document, uploading files and contacting people require the user's authorization. Delegated readers get only the document copy and their brief, never credentials or private context they do not need.

## 1. Collect facts before reviewing

Draft the fact sheet from the document, its previous version, comments and the conversation. The author is whoever owns the document's decisions: one writer, or a team of maintainers who may also be readers. Ask the author to confirm only items you cannot infer or that are ambiguous, and agree on three working terms: where edits go (a private copy, or the source with write permission), whether readers may run as delegated agents, and a budget in rounds or cost. Use [the templates](references/templates.md).

- Primary readers: the people the document exists to serve. Record role, background, unfamiliar terms, what each must do after reading (decide, implement, integrate, approve, operate, maintain, install, contribute), and which sections that task needs.
- Secondary readers: others who consult it occasionally, and which sections they actually read. Confirm the classification with the author.
- Reading situation: careful pre-read, silent reading in a meeting, skimming, lookup.
- Genre and purpose: what decision or action the document must enable; what it deliberately leaves to other documents.
- Author intent: numbered conclusions every reader must reach (C1, C2, …).
- Constraints: author preferences, templates, content that must not change, such as prototypes or legal text (W1, W2, …).
- Sources of truth: owner of each fact and figure; editable figure sources with content hashes.
- History: prior decisions, unresolved comments, recurring objections.
- Success: per reader type, task questions they must answer and locate in the document.

Keep one private working file, outside the document, with conclusions (C), constraints (W), pending author decisions (D), decided items with their rationale, and out-of-scope follow-ups.

## 2. Prepare the reader copy

Convert the document to plain text or Markdown, keeping code line breaks, table rows and headers, citation titles, links, captions, and every figure as a local image file. Prefer the most structured export available, such as the wiki or editor source over a PDF. When some structure cannot survive conversion, such as a scanned page or a complex table, include that page as an image and tell readers which parts are images. Readers judge the copy, so a lossy copy produces false findings. Spot-check the copy against the source before sending: each code block, citation, table and figure. When the source changes figure identifiers or file names, update the conversion mapping and recheck.

## 3. Brief fresh readers

Use one new agent per reader type and a new agent each round. Give each the copy path, role and background, genre and scope, which figures are prototypes whose text is fixed, task questions, and the recorded-items list. Do not give author intent or earlier findings.

Ask every reader to read before answering, then return:

1. A retelling of the core conclusions and a step-by-step walk through each process diagram.
2. Answers to the task questions with the section where each answer is found, or "not found". Readers must not fill gaps from their own knowledge.
3. A list of issues not already recorded, each quoting the text and naming the type: contradiction, unclear, missing information needed for the reader's task.

Role-specific duties:

- Primary readers read everything their task needs; the consistency reader reads the whole document.
- Secondary readers skim as they really would and report their reading path. Compare the path with the definitions they needed; a needed definition they never reached is a navigation issue.
- One reader performs a consistency check every round: for each named fact, list every statement of it in the text and figures and judge whether they agree. Give this duty to the reader who works most closely with the details (an implementer or maintainer); if no reader type fits, add a dedicated consistency reader. The consistency duty runs every round even when its reader is otherwise secondary. In the first round also check the document's defined terms and any word used in several sections.

The recorded-items list has three parts: decided by the author (with rationale; raise again only with a new argument), pending author decisions, and out of scope. This keeps readers from re-reporting known items.

## 4. Triage every finding

First compare each retelling with the conclusions. A deviation, or a task question answered wrongly or marked not found, must be fixed. Then place each finding in one class:

1. Intent deviation, contradiction, unclear text, failed task question: fix.
2. Structure: make small moves directly; propose larger outlines to the author.
3. Design gap that affects the reader's decision: add to pending decisions; do not invent the answer.
4. Implementation detail: record as a follow-up for a later document.
5. Violates a constraint, outside scope, or caused by a faulty reader copy: decline and record the reason.
6. Polish with no contradiction and no task impact: fix when cheap; it does not count as a new issue.

Readers judge only the document. Before fixing a factual claim, check it against its source of truth yourself: code, command help, configuration, the owning policy or the fact owner. Run a documented command only when it is safe and within the agreed permissions; otherwise record it as unverified. Handle any finding that appears in two or more rounds explicitly: fix it, or record why not. When a fix depends on your reading of existing text, mark it for author confirmation.

## 5. Revise and verify

1. Before editing a fact, list every statement of it with the helper in this skill's `scripts` directory: `python3 <skill>/scripts/sweep.py COPY TERM... --ignore-case` on the current reader copy. Matching is by substring, so pass the word stem and its synonyms ("inspect", "check"). Edit all statements together. Run it again after the edit.
2. Edit where the reader quoted, usually the definition, not in a later sentence.
3. When a paragraph needs its second fix, rewrite the whole paragraph from the fact sheet instead of adding another patch.
4. Write both branches of a conditional definition: "when X …; otherwise …".
5. Treat merging or centralizing definitions as high risk; sweep first.
6. For figures, confirm the editable source matches the published image by content hash (for example SHA-256 of the image file). Regenerate an out-of-date figure from its source, such as a screenshot of the current software, when the author agrees. Without a source, make the smallest pixel edit and check that only the target region changed. Re-uploading a figure to change a caption must keep the image hash.
7. After writing to the agreed location, export the document again with the same method used for BEFORE (for a plain file, BEFORE is the copy saved before editing), so conversion noise cancels out, and compare: `python3 <skill>/scripts/textdiff.py BEFORE AFTER --max-changed N`, where N is the number of lines you planned to change (a rewritten paragraph counts as its lines). `changed` is the larger of removed and added lines; the command exits 1 when it exceeds N. Inspect every removed and added line; any figure reference change needs hash evidence.

## 6. Loop and stop

After each round, review the round itself: which step let an issue through, and what the next round should do differently. Apply that to the next brief or edit procedure and note it in the record.

- Task questions in each round cover every fact changed in the previous round, one question per changed fact; edits are the main source of new issues. For a long document, give each reader only the questions for its role and point to the sections they cover.
- Primary readers and the consistency reader join every round. A secondary reader joins only when their sections changed materially or their task failed last round, and stops after two rounds that raise only class 4 or class 6 findings.
- Pending decisions do not block the loop; present them together at the end.
- Stop when a round has no class 1 finding, no new class 3 finding, and no issue found in it traces back to a gap in the procedure (a missing sweep, a skipped question, a lossy copy, an unclear brief). When the agreed budget runs out first, stop and report what remains.

## 7. Report

State what changed per round, pending decisions ordered by impact, declined findings and reasons, follow-ups, interpretations awaiting confirmation, edits not reviewed by a later reader, and approximate cost. Distinguish verified, unverified and not run.

For a complete small cycle, read [the worked example](references/worked-example.md).
