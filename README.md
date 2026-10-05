# Agent skills for bilingual PDFs, study notes and testing

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Skills for bilingual documents, learning material and cost-aware software verification.

- [bilingual-pdf](skills/bilingual-pdf/README.md): Render side-by-side bilingual articles, reports and handouts from paired text.
- [study-notes](skills/study-notes/README.md): Turn learning sources into explanatory notes, quick references, keyword indexes or decision trees.
- [testing-workflow](skills/testing-workflow/SKILL.md): Design and run cost-aware automated tests and benchmarks for software changes.

## Install

With the [Skills CLI](https://github.com/vercel-labs/skills) or a compatible installer:

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
```

Install the complete directories for the skills you need, using the commands above or your host’s supported installation method. `study-notes` also requires `bilingual-pdf`; `testing-workflow` is independent. Follow each skill’s linked guide for its setup, usage and examples.

## Repository conventions

Each skill owns its implementation and documentation. Human guides live in skill READMEs; agent workflows live in SKILL.md. Shared implementations have one owner, and dependent skills resolve installed dependencies through the host rather than assuming neighboring directories. Pin a tested revision in downstream projects.

See [validation](tests/README.md) for reproducible repository checks and the distinction between historical and current results. Curated examples stay with their owning skills. Keep private content out of this public repository; external processing and publication require applicable authorization.

Original code and example content use the [MIT license](LICENSE). Dependencies retain their [own licenses](THIRD_PARTY_NOTICES.md).
