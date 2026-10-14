# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Create one source-first, aligned translation master. By default, the current main agent reads the complete source, chooses semantic splits, saves bounded groups, then reviews all saved pairs in a separate pass. Independent review is a separate stage by the same agent.

Progress updates report actual completed/total counts by phase about every 5%, including completion and review rollback after corrections.

Subagents may lose context and introduce inconsistent terminology, style or details. Delegation requires explaining this risk and your explicit approval for its scope; urgency alone does not authorize it. Specific approval in your current request need not be repeated.

Install this complete skill directory. The JSONL helper requires Python 3.11+ and POSIX file locking, with no external packages or network service. Native paired TeX remains an equal route for rich content outside the Markdown importer.

Try: “Translate this guide into French with bilingual-translation, preserving paragraphs and table cells in one reviewed master.” Supply the source, target language, audience and terminology.

Agent entry: scripts/workflow.py. Preparation returns complete units totaling at least 8192 source codepoints, except the final batch; split each unit over 2048 before advancing. Translation and review groups each fit 2048 source codepoints; review does not count target length. Save and next are separate actions. Run an independent command or submit stdin JSONL to run, with one action and its own reference per line. At most one body-reading action may appear in a batch, last. Return tool-provided references unchanged. For splits, the agent chooses exact adjacent source anchors; the tool locates the cut and checks lengths, without manual offset arithmetic.

Apply corrections with exact old/new patches, read the changed comparison, then accept separately. Recheck local issues locally; restart the full review for widespread or global issues. Track unresolved issues as todos. Export requires current completed review and resolved todos; it has no draft bypass.

[Agent workflow](SKILL.md) · [Commands and boundaries](references/workflow.md)

Reviewed JSONL goes directly to the separately discovered bilingual-pdf skill. HTML uses its own layout JSON or imports the semantic exchange; it does not directly consume JSONL. Existing supplied pairs need no new translation.

## Semantic exchange

The [semantic exchange](references/semantic-exchange.md) and [worked English–French example](references/example-guide.md) describe the renderer handoff. Use workflow.py export when a consumer needs semantic exchange JSON; keep JSONL as the master. Consumers validate exchange documents with translation_contract.py’s read-only validate_document API.

Validation checks structure and recorded review currency. Meaning is reviewed by the agent; PDF appearance is checked separately on actual rendered pages.

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
