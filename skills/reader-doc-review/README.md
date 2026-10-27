# Reader-based document review

Review and revise one document for the people who will actually read it. Collect the facts first: readers, their tasks, the document's purpose, scope and the author's intent. Then give fresh-context readers real task questions, triage what they report, fix the document and verify each edit. Repeat until a round finds nothing new. Works for any topic, format or source: proposals, designs, guides, READMEs, policies and manuals.

Install this folder as a skill using your host's supported discovery mechanism. Python 3 runs the two optional helpers: `scripts/sweep.py` lists every statement of a fact before you edit it, and `scripts/textdiff.py` compares two exports of the document. Reading and writing the document use whatever access you already have to its source; this skill does not grant publishing rights.

Try: “Use reader-doc-review on this design proposal. The readers are the approving manager and the engineers who will build it. Confirm the facts with me first, then run review and fix rounds until nothing new comes up, and list the decisions I still need to make.”

See the [agent workflow](SKILL.md), the [templates](references/templates.md) and the [original worked example](references/worked-example.md). Reader trials show whether the tested readers could use the document; they do not prove the design is right. Licensed under [MIT](LICENSE).
