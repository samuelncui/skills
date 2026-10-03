# One article, four bilingual editions

All four projects translate the same original article, “A slower walk through a familiar street.” Each includes a full-width shared photograph with paired captions, a schematic route, a quotation, a table, a cross-reference and one continuous long paragraph that flows across pages without manual breaks.

- [English / French](../examples/en-fr/): [PDF](../examples/en-fr/output.pdf), [JSON](../examples/en-fr/source.json)
- [English / Chinese](../examples/en-zh-Hans/): [PDF](../examples/en-zh-Hans/output.pdf), [JSON](../examples/en-zh-Hans/source.json)
- [English / Arabic](../examples/en-ar/): [PDF](../examples/en-ar/output.pdf), [JSON](../examples/en-ar/source.json)
- [Chinese / Japanese](../examples/zh-Hans-ja/): [PDF](../examples/zh-Hans-ja/output.pdf), [JSON](../examples/zh-Hans-ja/source.json)

Choose the nearest language pair and read its `content.tex` alongside the PDF before authoring. Each folder is a complete portable native project: source, images, PDF and first-page preview stay together. The same English and Chinese passages are identical wherever they recur; natural translation length can change pagination. Do not cut or pad a translation to force identical page counts.

## Build or adapt

Copy an entire example folder into a fresh working directory, edit `content.tex` and `languages.tex`, then run there:

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape -jobname=output main.tex
```

The native project builds without Python or a repository checkout. For JSON authoring, run from this installed skill's directory and choose a fresh output destination:

```sh
python3 scripts/bilingual_pdf.py export examples/en-fr/source.json --output /path/to/new-project
python3 scripts/bilingual_pdf.py render examples/en-fr/source.json --output /path/to/new-build
```

Native builds need XeLaTeX, latexmk and the [documented packages/fonts](languages.md). Structured import and optional QA also need this skill's `requirements.txt`. Neither helper installs dependencies. Read the [native API](latex.md), [input contract](input.md) and [acceptance checks](acceptance.md) as needed. TeX is executable input; disabled shell escape is not a filesystem sandbox.

The article and diagram are original MIT-licensed examples. The skill-level [MIT license](../LICENSE) covers original text/code; the photograph has one shared [CC0 attribution](photo-credit.md). Retain these notices when redistributing a copied project. Inspect all pages, reconcile each translation and preserve user-supplied text when adapting. First-page previews are browsing aids, not full-document review evidence.
