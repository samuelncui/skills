# Agent skills for documents and software workflows

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Eight skills for translation, document layout, learning material, software quality and skill improvement.

## Translation and documents

- [bilingual-translation](skills/bilingual-translation/README.md): Read the full source, save bounded semantic groups and independently review one paired master.
- [bilingual-html](skills/bilingual-html/README.md): Render supplied pairs as portable responsive HTML, with logical pair order, RTL text, real tables and shared figures.
- [bilingual-pdf](skills/bilingual-pdf/README.md): Render side-by-side bilingual articles, reports and handouts from paired text.
- [study-notes](skills/study-notes/README.md): Turn learning sources into explanatory notes, quick references, keyword indexes or decision trees.
- [reader-doc-review](skills/reader-doc-review/README.md): Review and revise one document for its real readers through fresh-context task trials and fix rounds.
## Software and skill quality

- [testing-workflow](skills/testing-workflow/README.md): Design and run cost-aware automated tests and benchmarks for software changes.
- [write-if-statements](skills/write-if-statements/README.md): Write and review readable if statements, and refactor conditional logic without changing behavior.
- [skill-optimization](skills/skill-optimization/README.md): Improve skills through realistic fresh-context trials and focused corrections.

## Install

With the [Skills CLI](https://github.com/vercel-labs/skills) or a compatible installer:

```sh
npx skills add samuelncui/skills --skill bilingual-translation
npx skills add samuelncui/skills --skill bilingual-html
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill reader-doc-review
npx skills add samuelncui/skills --skill testing-workflow
npx skills add samuelncui/skills --skill write-if-statements
npx skills add samuelncui/skills --skill skill-optimization
```

Choose complete skill directories. Supplied pairs need only bilingual-pdf or bilingual-html. reader-doc-review needs only Python 3 for its optional helpers. Raw-source translation needs bilingual-translation; direct reviewed JSONL input is supported by PDF, while HTML uses its own layout JSON or the semantic-exchange importer. study-notes requires bilingual-pdf. The three software/skill-quality guides have no runtime dependency of their own; tested projects supply their toolchains. Dependencies are discovered through the host and never installed automatically. Follow each linked guide for setup and examples.

## Repository conventions

Each skill owns its implementation and documentation. Human guides live in skill READMEs; agent workflows live in SKILL.md. Shared implementations have one owner, and dependent skills resolve installed dependencies through the host rather than assuming neighboring directories. Pin a tested revision in downstream projects.

See [validation](tests/README.md) for reproducible repository checks and the distinction between historical and current results. Curated examples stay with their owning skills. Keep private content out of this public repository; external processing and publication require applicable authorization.

Original code and example content use the [MIT license](LICENSE). Dependencies retain their [own licenses](THIRD_PARTY_NOTICES.md).
