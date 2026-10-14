# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Create one source-first, aligned translation master. By default, the current main agent reads the complete source, chooses semantic splits, saves bounded groups, then reviews all saved pairs in a separate pass. Independent review is a separate stage by the same agent.

Subagents may lose context and introduce inconsistent terminology, style or details. Delegation requires explaining this risk and your explicit approval for its scope; urgency alone does not authorize it. Specific approval in your current request need not be repeated.

Install this complete skill directory. The JSONL helper requires Python 3.11+ and POSIX file locking, with no external packages or network service. Native paired TeX remains an equal route for rich content outside the Markdown importer.

Try: “Translate this guide into French with bilingual-translation, preserving paragraphs and table cells in one reviewed master.” Supply the source, target language, audience and terminology.

Agent entry: scripts/workflow.py. prepare reads and initializes the source, translate dispatches groups totaling at most 2048 source codepoints, and review records an independent complete comparison. Save/accept returns the next group; complete confirmation codes such as 17-maple are copied back unchanged instead of hashes and are not security credentials. Revision/hash/retry checks stay inside the tool. Only changed pairs need review again.

[Agent workflow](SKILL.md) · [Commands and boundaries](references/workflow-v2.md)

Reviewed JSONL goes directly to the separately discovered bilingual-pdf skill. HTML uses its own layout JSON or a legacy v1 import; it does not directly consume JSONL. Existing supplied pairs need no new translation.

## Legacy v1 compatibility

The original [v1 contract](references/contract-v1.md), [worked English–French example](references/example-guide.md) and translation_contract.py APIs remain supported. They are separate from the gated JSONL workflow. Use workflow.py export only when a consumer needs v1 JSON; keep JSONL as the master.

Validation checks structure and recorded review currency. Meaning is reviewed by the agent; PDF appearance is checked separately on actual rendered pages.

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
