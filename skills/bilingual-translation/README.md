# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Create one aligned source/target manuscript. Read the full relevant source first, then translate and review each complete paragraph or semantic unit, saving it in the same master before advancing. Stable IDs preserve alignment; source edits reopen the corresponding target for review.

Install the complete directory with your host's skill installer. Native paired TeX is an equal route. Optional plain-text JSON and its Python 3.11+ standard-library validator work independently of PDF/HTML renderers.

Try: “Use bilingual-translation to translate this guide into French, preserving each paragraph and table cell in one paired manuscript.” Provide the source, target language, audience and terminology. Existing pairs can go directly to a renderer.

Read the [workflow](SKILL.md), [optional contract](references/contract-v1.md) and [complete original English–French example](references/example-guide.md), including its source, table and shared figure. From the skill directory:

```sh
python3 -B scripts/translation_contract.py validate examples/guide/translation.json --ready
```

Checks cover structure, source hashes and recorded review currency. Semantic accuracy still requires reading source and target.

[Design provenance](references/design-provenance.md) · [MIT license](LICENSE)
