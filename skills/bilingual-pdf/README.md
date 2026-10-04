# Bilingual PDF

Create same-page parallel-text articles, reports, instructions and travel writing. Source and translation occupy fixed physical columns; language direction is independent of their order. Native LaTeX and JSON use the same `assets/paralleltext.sty` and produce editable source projects.

For the agent workflow, read [SKILL.md](SKILL.md). This skill owns the renderer, templates, layout/language references and shared article assets. The separately installed `course-guide-quick-reference` skill uses it for rendering learning documents.

## One article, four bilingual editions

All four projects translate the same complete original article, “A slower walk through a familiar street.” Each demonstrates a full-width shared photograph with paired captions, language-specific route diagrams, a quotation, a table, a cross-reference and a continuous paragraph flowing across pages:

- [English / French](examples/en-fr/): [PDF](examples/en-fr/output.pdf), [JSON](examples/en-fr/source.json)
- [English / Chinese](examples/en-zh-Hans/): [PDF](examples/en-zh-Hans/output.pdf), [JSON](examples/en-zh-Hans/source.json)
- [English / Arabic](examples/en-ar/): [PDF](examples/en-ar/output.pdf), [JSON](examples/en-ar/source.json)
- [Chinese / Japanese](examples/zh-Hans-ja/): [PDF](examples/zh-Hans-ja/output.pdf), [JSON](examples/zh-Hans-ja/source.json)

Read `content.tex` beside its PDF before choosing an authoring pattern. The same English and Chinese passages remain text-identical wherever they recur. Natural translation length can change pagination; never cut or pad a translation to force identical page counts. First-page previews are browsing aids, not full-document review evidence.

Each language-pair folder holds its JSON, editable LaTeX, PDF and preview. Reusable images live once in `assets/`: `footpath.png`, `route-en.png`, `route-fr.png`, `route-zh-Hans.png`, `route-ar.png` and `route-ja.png`. The shared photograph spans both columns; the paired route figure uses the appropriate localized image on each side. The image pool and renderer are not copied into every installed example.

## Native LaTeX

From this installed skill's directory:

```sh
cd examples/en-fr
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape -jobname=output main.tex
```

The checked-in native project finds the package and images through its relative `../../assets` fallback. It builds without Python or a repository checkout. Choose the nearest language pair, then work in a fresh copy rather than overwriting supplied examples. Either retain the `examples/<pair>/` and `assets/` relationship, or place the needed package and images beside the copied `.tex` files and update explicit image paths if needed. Retain the license and photograph credit with redistributed material.

Edit `content.tex` for meaning and `languages.tex` for fonts/languages. The [native reference](references/latex.md) also supplies a minimal document when a full worked article is unnecessary. Use ordinary LaTeX lists, mathematics, tables, quotations and labels inside the documented paired commands. For handoff, include all required `.tex`, package and image files; no recipient should need your installation paths.

## Structured content

Run from this installed skill's directory, selecting a fresh output directory:

```sh
python3 scripts/bilingual_pdf.py export examples/en-fr/source.json --asset-root assets --output /path/to/new-project
python3 scripts/bilingual_pdf.py render examples/en-fr/source.json --asset-root assets --output /path/to/new-build
```

`export` creates a self-contained editable project. Build its `document.tex` directly with the native latexmk command, without Python. `render` exports, compiles and mechanically checks it in one step. Existing output directories are never silently overwritten. Add `--mode left` or `--mode right` for a selected-language edition.

The [input contract](references/input.md) defines semantic fields and validation. JSON is the implemented interchange reader; another format needs an explicit mapping to those fields. Image paths are relative to `--asset-root`, which defaults to the input file's parent directory. Absolute paths, traversal and symlink escapes are rejected. A paired figure accepts one image or `[left, right]` images; a shared figure accepts one image. Export stages the required images into its portable output.

## Adjust the design

No setup is needed for the default style. Add sparse `\ParallelSetup{...}` settings only when requested: geometry and mirrored binding allowance, divider color/dash/width, folio position/format, heading styles, spacing, semantic roles or optional navigation tabs. Ordinary geometry, fontspec, Polyglossia, fancyhdr, enumitem and TikZ commands remain available.

The [configuration guide](references/configuration.md) preserves the full native option reference and two optional profile files. The JSON adapter exposes a smaller validated data-only subset of the same settings. Keep content, language mapping and presentation separate; do not edit individual paragraphs to hide a global layout problem.

Use bounded paired units for headings, lists, quotations and tables that must stay together. Opt-in `ParallelProse` / `flow: "breakable"` allows continuous prose across pages, then resynchronizes the next unit. `ParallelWideFigure` / `placement: "shared"` prints one full-width image above paired captions; `ParallelFigure` supports localized images. Read the [native API and safety contract](references/latex.md) before adapting these features.

## Dependencies and limits

Use a coherent TeX Live or MiKTeX installation with XeLaTeX, latexmk, Polyglossia, paracol and the documented packages. French requires hyphenation patterns; Arabic requires matching bidi support. The examples use Latin Modern Roman/Sans/Math, Noto Serif/Sans CJK and Noto Naskh Arabic. See [language and font prerequisites](references/languages.md), including RTL, mixed-script and CJK requirements.

Structured import needs Python 3.10+ and Pillow. Preflight, rendering and optional PDF QA also use the packages in `requirements.txt`, Fontconfig and `kpsewhich`. Linux is CI-tested; native Windows font discovery is not claimed. Helpers never download fonts, install software, translate through an external service or enable TeX shell escape.

Raw floats, arbitrary verbatim macro arguments, vertical writing and PDF/UA are outside the documented contract. Native TeX and latexmk configuration are executable inputs; disabled shell escape is not a filesystem sandbox. Use trusted sources or an appropriately isolated environment.

## Review and delivery

Run the [acceptance checks](references/acceptance.md), read both languages, reconcile claims and inspect every actual PDF page. Check RTL shaping, CJK punctuation, mixed-script numbers, image labels, references and both print parities. Compiler success is not a semantic or visual review.

Deliver the PDF, portable editable source project and structured source when used. Preserve supplied text and translations; report passed, failed and unrun checks separately. Rendering is local, but any host-agent translation is a separate data-processing step. No private source material or provenance belongs in public examples.

The article text and localized diagrams are original [MIT-licensed](LICENSE) material. The shared photograph has one [CC0 attribution](references/photo-credit.md). Retain applicable notices when redistributing a project; fonts, TeX packages and Python libraries retain their own licenses.
