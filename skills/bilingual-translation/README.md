# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Create one source-first, aligned translation master. By default, the current main agent reads the complete source, chooses semantic splits, saves bounded groups, then reviews all saved pairs in a separate pass. Independent review is a separate stage by the same agent.

Progress updates report actual completed/total counts by phase about every 5%, including completion and review rollback after corrections.

Subagents may lose context and introduce inconsistent terminology, style or details. Delegation requires explaining this risk and your explicit approval for its scope; urgency alone does not authorize it. Specific approval in your current request need not be repeated.

Install this complete skill directory. The JSONL helper requires Python 3.11+ and POSIX file locking, with no external packages or network service. Native paired TeX remains an equal route for rich content outside the Markdown importer.

Try: “Translate this guide into French with bilingual-translation, preserving paragraphs and table cells in one reviewed master.” Supply the source, target language, audience and terminology.

Agent entry: scripts/workflow.py. prepare reads and initializes the source, translate dispatches groups totaling at most 2048 source codepoints, and review records a separate complete comparison. Save/accept returns the next group. Return tool-provided references unchanged. Only changed pairs need review again.

[Agent workflow](SKILL.md) · [Commands and boundaries](references/workflow.md)

Reviewed JSONL goes directly to the separately discovered bilingual-pdf skill. HTML uses its own layout JSON or imports the semantic exchange; it does not directly consume JSONL. Existing supplied pairs need no new translation.

## Semantic exchange

The [semantic exchange](references/semantic-exchange.md) and [worked English–French example](references/example-guide.md) describe the renderer handoff. Use workflow.py export when a consumer needs semantic exchange JSON; keep JSONL as the master. Consumers validate exchange documents with translation_contract.py’s read-only validate_document API.

Validation checks structure and recorded review currency. Meaning is reviewed by the agent; PDF appearance is checked separately on actual rendered pages.

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
