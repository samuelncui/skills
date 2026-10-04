# Skills

Agent skills for aligned, same-page bilingual documents, with native LaTeX and structured content as equal authoring routes.

| Skill | Purpose | Dependency |
| --- | --- | --- |
| [bilingual-pdf](skills/bilingual-pdf/README.md) | Parallel-text articles, reports, instructions and travel writing | TeX/fonts; Python for structured import and optional QA |
| [course-guide-quick-reference](skills/course-guide-quick-reference/README.md) | Authorized learning sources → explanatory notes and a keyword/concept Quick Reference | Installed `bilingual-pdf` |

Each skill's README is its human use guide; `SKILL.md` is its agent workflow. Worked examples, PDFs and previews live inside the owning skill. `bilingual-pdf` is the sole owner of the renderer, LaTeX package, layout references and reusable article assets. The course skill adds teaching and retrieval authoring, using that installed dependency.

## Install

With the [Skills CLI](https://github.com/vercel-labs/skills) or a compatible Agent Skills installer:

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
# For learning notes and Quick Reference, also install:
npx skills add samuelncui/skills --skill course-guide-quick-reference
```

Or copy the complete required skill directories to the locations supported by your host. Installing the course skill alone does not install its dependency. Resolve `bilingual-pdf` from the host's installed-skill discovery, then provide its actual directory as `--bilingual-skill` or `BILINGUAL_PDF_SKILL`; do not assume adjacent directories. See the [course dependency and build guide](skills/course-guide-quick-reference/README.md#required-dependency).

The helpers never download or install missing skills, TeX, fonts or Python packages. Installation does not authorize processing, translating externally or publishing private material.

## Review, maintenance and licensing

See each skill's guide for prerequisites, authoring, examples and review limits. [Tests](tests/README.md) documents validation and curated-output regeneration. Mechanical checks do not replace source, translation and actual-page review. Maintainer tools are repository-only; installed workflows do not import them.

Original code and teaching content retain the [MIT license](LICENSE). The shared article photograph has [CC0 attribution](skills/bilingual-pdf/references/photo-credit.md); dependencies retain their [own licenses](THIRD_PARTY_NOTICES.md). Rendering is local. Translation accuracy, domain suitability, error-free output and PDF/UA conformance are not guaranteed.
