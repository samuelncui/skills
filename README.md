# Skills

Two independently installable agent skills for aligned, same-page bilingual documents. Both use one shared LaTeX design, with native LaTeX and structured content as equal authoring routes.

| Skill | Purpose |
| --- | --- |
| [bilingual-pdf](skills/bilingual-pdf/SKILL.md) | Parallel-text articles, reports, instructions and travel writing |
| [course-guide-quick-reference](skills/course-guide-quick-reference/SKILL.md) | Authorized learning sources → explanatory notes and a keyword/concept Quick Reference |

## Open a complete example

Examples are installed inside their owning skill. All four article editions translate the same original text and demonstrate a full-width shared photograph, paired captions and a continuous paragraph flowing across pages. Each folder keeps its source, editable LaTeX, images, PDF and preview together:

- [English / French article](skills/bilingual-pdf/examples/en-fr/): [PDF](skills/bilingual-pdf/examples/en-fr/output.pdf)
- [English / Chinese article](skills/bilingual-pdf/examples/en-zh-Hans/): [PDF](skills/bilingual-pdf/examples/en-zh-Hans/output.pdf)
- [English / Arabic article](skills/bilingual-pdf/examples/en-ar/): [PDF](skills/bilingual-pdf/examples/en-ar/output.pdf)
- [Chinese / Japanese article](skills/bilingual-pdf/examples/zh-Hans-ja/): [PDF](skills/bilingual-pdf/examples/zh-Hans-ja/output.pdf)
- [Three-concept learning set](skills/course-guide-quick-reference/examples/): [notes](skills/course-guide-quick-reference/examples/notes.pdf), [Quick Reference](skills/course-guide-quick-reference/examples/quick-reference.pdf), [original source](skills/course-guide-quick-reference/examples/source.md)

The [article example guide](skills/bilingual-pdf/references/examples.md) and [learning example guide](skills/course-guide-quick-reference/references/examples.md) include build commands and adaptation instructions. These are directly browsable public examples; no Actions artifact download is needed. The compact structured-course compatibility fixture lives under `tests/fixtures/`, separate from the public learning example.

## Install

With the [Skills CLI](https://github.com/vercel-labs/skills) or a compatible Agent Skills installer:

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill course-guide-quick-reference
```

Or copy one complete skill directory into the location supported by your agent. Each contains its runtime, templates, references, complete worked examples and licenses. Neither needs the sibling skill or repository maintainer tools. Installation does not install TeX/fonts or authorize processing or publishing private material.

## Two authoring routes

Native LaTeX projects use ordinary `article` documents, separate content/language files and `paralleltext.sty`. Copy a complete example folder, edit its `.tex` sources, then build it directly:

```sh
cd skills/bilingual-pdf/examples/en-zh-Hans
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape -jobname=output main.tex
```

Structured input can be exported to the same editable LaTeX or rendered and checked in one command:

```sh
python3 skills/bilingual-pdf/scripts/bilingual_pdf.py export skills/bilingual-pdf/examples/en-zh-Hans/source.json --output .local/article-project
python3 skills/bilingual-pdf/scripts/bilingual_pdf.py render skills/bilingual-pdf/examples/en-zh-Hans/source.json --output .local/article-build
```

Choose fresh output directories. Existing projects are never silently overwritten. JSON is the implemented interchange reader; other structured formats need an explicit mapping to the same semantic fields.

The learning skill adds source reading, explanatory notes, independently findable lookup terms and generated notes pointers. Its native starter builds `notes.pdf` and `quick-reference.pdf` together. The structured collection adapter produces the same flat PDF arrangement with named editable sources; it does not require a fixed Meaning/Rule/Checks writing structure.

## Adjust the design

No setup is required for the default style. Add sparse `\ParallelSetup{...}` overrides only when needed: mirrored binding geometry, divider color/dash/width, folio position/format, heading styles, spacing or optional tabs. Ordinary geometry, fontspec, Polyglossia, fancyhdr, enumitem and TikZ commands remain available. See the [intent-to-option guide](skills/bilingual-pdf/references/configuration.md), including two ready-to-use profile files. The structured adapter emits the same settings.

## Dependencies and limits

Use a coherent TeX Live or MiKTeX setup with XeLaTeX, latexmk, Polyglossia, paracol and the documented packages. French needs its hyphenation patterns; Arabic needs matching bidi support. Examples use Latin Modern Roman/Sans/Math, Noto Serif/Sans CJK and Noto Naskh Arabic. See [language and font prerequisites](skills/bilingual-pdf/references/languages.md).

Structured import and optional PDF QA need Python 3.10+, PyMuPDF, Pillow, fonttools, Fontconfig and `kpsewhich`. Linux is CI-tested; native Windows font discovery is not claimed. The helpers do not install software, download fonts, translate through an external service or enable TeX shell escape.

Use bounded paired units for headings, lists, quotations, tables and other content that must stay together. Opt-in flowing prose can cross pages while preserving the two language columns; shared figures place one image above paired captions. Read the [native API and safety contract](skills/bilingual-pdf/references/latex.md) before adapting these behaviors. Raw floats, arbitrary verbatim macro arguments, vertical writing and PDF/UA are outside the documented contract. Disabled shell escape is not a filesystem sandbox.

## Validation and maintenance

[Tests](tests/README.md) describe the tested language/layout combinations and review limits. Mechanical checks do not replace reading the content, reconciling translations and inspecting PDF pages.

The canonical implementation lives in `skills/bilingual-pdf`. Repository-only tools maintain self-contained distribution copies and examples:

- `tools/check_package.py`: audit each independently installable skill package
- `tools/sync_renderer.py`: synchronize the package, runtime and shared references
- `tools/export_native_examples.py`: refresh native article sources from co-located JSON and images
- `tools/collect_example_outputs.py`: collect only approved PDFs/previews and record provenance in each skill's `examples/MANIFEST.json`

The [test guide](tests/README.md#regenerate-curated-outputs) gives the complete regeneration sequence. Installed skills do not import or execute these maintainer tools.

## Privacy and licensing

The existing [MIT attribution](LICENSE) is retained. Public teaching texts and diagrams are original generic material; the shared photograph in every article edition has its own [CC0 attribution](skills/bilingual-pdf/references/photo-credit.md). No private learning sources or personal provenance belong in published artifacts. Fonts, TeX packages and Python libraries retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).

Rendering is local. Any translation performed by the host agent is a separate data-processing step. Translation accuracy, domain suitability and error-free output are not guaranteed.
