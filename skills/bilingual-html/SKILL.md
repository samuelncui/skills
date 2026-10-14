---
name: bilingual-html
description: Render supplied bilingual text pairs as portable offline HTML with responsive per-pair alignment, native tables, figures, and independent language directions. Use for bilingual web documents; route raw-source translation to separately installed bilingual-translation.
---

# Bilingual HTML

Use this skill alone when the user already supplies paired text. Start with the [human guide, installation and examples](README.md), then read [the rendering contract](references/rendering.md) and turn those pairs into layout version 1. Preserve supplied text and pair identities; ask about actual omissions instead of inventing translations.

1. Inspect the whole input and identify its logical headings, paragraphs, list items, table cells, captions and alternative text. Keep both languages of each item together.
2. Use the embedded-pair format illustrated by [the complete tutorial](examples/tutorial/layout.json). Select each language's tag and direction independently from physical desktop order. Configure supported styles only when needed.
3. Render with Python 3.11+: `python3 scripts/bilingual_html.py render INPUT.json --output NEW_DIRECTORY`. Run this from the installed skill directory or use the script's discovered absolute path. The output parent must exist; use a fresh output directory.
4. Open the generated `index.html` in a browser. Read paired content, inspect desktop and narrow-screen order, actual glyphs, RTL text, table relationships, shared images and alternative text. Test source-first mobile order even when desktop order is reversed. Structural tests do not establish translation quality or accessibility conformance.
5. Deliver the entire output directory, including `style.css`, images and `LICENSE`. It works offline and needs no JavaScript or translation dependency.

## When translation is needed

For raw source or unresolved translation, discover the separately installed `bilingual-translation` skill through the host's skill discovery and follow its workflow. If absent, explain that translation requires that skill to be installed explicitly, or ask the user to supply completed pairs. Do not implement a second translation workflow here.

For its reviewed JSONL master, first run that skill's `scripts/workflow.py export master.jsonl --output reviewed.json`, then use `import-pairs reviewed.json` with an explicit discovered `--translation-skill PATH --contract-version 1`, and render the resulting `layout.json`. Existing reviewed exchange-v1 JSON can enter at `import-pairs`. HTML does not accept JSONL directly. Export joins split children into parent pairs; keep the master for child-level records and review history. Read [the adapter instructions](references/rendering.md#optional-translation-import) for exact commands, asset staging and version/revision recording. The adapter calls the semantic owner's validator; it neither installs dependencies nor rewrites translations.

## Scope and authoring

Version 1 accepts literal plain text, not raw HTML, Markdown rendering, TeX or scripts. Mathematical markup is displayed literally. For trusted manually authored rich HTML, follow the [minimal native page and per-pair DOM rules](references/rendering.md#native-html-authoring), reuse the owned CSS and author outside this JSON renderer; review markup, assets, behavior and security separately. Choose JSON or native HTML as the editing source: manual native edits are not imported or checked by this renderer. Re-render JSON into a fresh output directory for each revision; the CLI has no incremental build or overwrite mode. Keep actual language roles stable when changing desktop columns.

The complete tutorial includes its original PNG and generated [portable HTML](examples/tutorial/site/index.html). [Styling, asset constraints and review boundaries](references/rendering.md) belong to this renderer. Translation judgments belong to the separately discovered translation skill.
