# Structured interchange: JSON to the shared LaTeX template

The structured route is an equal entry point, not a separate layout engine. `export` normalizes validated content into an ordinary editable project; `render` performs that export and then runs latexmk and PDF checks. Native LaTeX uses the same `paralleltext.sty` without parsing JSON.

## Commands

From the installed skill directory, with an input path and a new output path:

```sh
python3 scripts/bilingual_pdf.py preflight input.json
python3 scripts/bilingual_pdf.py export input.json --output new-project
cd new-project
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape document.tex
```

Or run `python3 scripts/bilingual_pdf.py render input.json --output new-project`. Use `--asset-root path/to/assets` for images stored outside the input file's parent directory; for bundled articles, run from the skill directory with `--asset-root assets`. `--mode left` and `--mode right` export only the selected language. `export` needs Python and Pillow for safe image staging; `preflight`/`render` also need the documented QA and TeX dependencies. A native build of the exported project needs no Python.

Outputs: `document.tex`, `languages.tex`, `content.tex`, `paralleltext.sty`, staged figure files, and (after building) `document.pdf` plus ordinary TeX auxiliaries. `render` additionally writes `result.json`. Preserve input files; choose a new output directory for each export. The final portable source project consists of authored/generated `.tex`, the package and images, not logs or private inputs.

## Document

```json
{
  "languages": ["en", "zh-Hans"],
  "title": ["A familiar street", "熟悉的街道"],
  "layout": {"covers": false, "font_size": 10},
  "blocks": [
    {"id": "opening", "kind": "heading", "text": ["Look closely", "仔细观察"]},
    {"id": "detail", "text": ["Notice one detail.", "留意一个细节。"]}
  ]
}
```

`languages` and every paired field have exactly two ordered sides. IDs are unique lowercase letters/digits/dots/hyphens, starting with a letter, at most 80 characters. These are stable semantic identities and link targets, not page numbers. Keep source and translation in matching units; list items and table rows also correspond by index.

Optional layout fields are data-only inputs to the [same native configuration](configuration.md):

- `paper`: `a4`, `letter`, `a5`, `legal`; `twoside`: boolean
- `font_size`: 9–14 pt; `leading`: 9–24 pt and at least the selected body size
- `margin_mm`: equal side margins, or independent `inner_mm` / `outer_mm` (8–45 mm); `binding_mm`: 0–20 mm; `top_mm` / `bottom_mm`: 10–40 mm; `gap_mm`: 4–16 mm
- `covers`: boolean, default false; `profile`: `article` (defaults), `bound`, or `reading`. A profile is applied before explicit overrides; omitted fields retain profile/default values.
- `divider`: optional object with `enabled` (boolean), `color` (six HTML hex digits), `width_pt` (positive, at most 3), and `style` (`solid`, `dashed`, `dotted`, `densely dashed`, `densely dotted`)
- `page_numbers`: optional `position` (the native named positions, including `none`), `numbering` (`arabic`, `roman`, `Roman`, `alph`, `Alph`, `gobble`), and plain-text `prefix` / `suffix` (at most 80 characters each, escaped as text)

Unknown keys, out-of-range numbers, raw TeX styles and invalid choices are rejected. Native authoring offers the full documented style hooks, standard packages and custom paper dimensions. This subset does not promise arbitrary fonts, roles, tabs or executable styling through JSON. `break_before: true` on a block requests an explicit page break before that semantic unit, useful for an editorial section boundary. It is not a requirement to divide all content into page-sized chunks.

## Block meanings

- **paragraph** (default): two nonempty strings. Line breaks in a string are spaces; use separate blocks for separately aligned paragraphs.
- **heading**: two titles; emits one numbered paired section.
- **list**: `text` contains two equally sized nonempty arrays of item text. Each matching item is a separate aligned unit with an ordinary LaTeX bullet list.
- **quote**: two strings in a paired `quote` environment. This is formatting, not a claim that a quotation is licensed or accurately attributed.
- **figure**: `image` is one relative PNG/JPEG path or exactly two ordered paths `[left, right]`; `text` supplies two captions. Default `placement: "paired"` supports localized images, while a scalar repeats one image. `placement: "shared"` accepts a scalar only and prints it once across both columns. Images are resolved under the configured asset root, decoded and re-encoded to staged PNGs. Selected-language output uses its matching image. See the asset boundary below.
- **table**: `headers` contains two equally sized arrays of plain strings, one to five columns. `rows` contains two equally sized arrays of rows; each row has the matching column count. `text` supplies paired captions. Header/row pairs align independently and are kept together with the caption. Split a table that is too tall at an explicit corresponding boundary.
- **equation**: `math` contains a bounded LaTeX math expression; `text` explains it in both languages. The expression is shared and kept with its explanation. Only documented mathematical commands are allowed; arbitrary TeX, file access and character-code escapes are rejected. Use native `.tex` for trusted authored mathematics outside this limited importer.
- **reference**: `target` names an existing block; `text` supplies the displayed link wording. Native `\hyperref`/`\pageref` generate the destination and page. Collection-generated references can additionally carry a bounded relative PDF `file`, positive physical `page`, and plain-text printed `page_label` (for example `iii`). The collection build derives both the absolute destination and logical folio from native output; they are not typed into a notes manuscript.

A table example:

```json
{"id":"notes","kind":"table","text":["Example notes.","示例笔记。"],
 "headers":[["Observation","Question"],["观察","问题"]],
 "rows":[[["An empty bench","Used at another time?"]],[["一张空长椅","换个时间会有人坐吗？"]]]}
```

Arabic strings are logical Unicode text. An RTL text value may instead be `{"runs":[{"text":"الموعد: ","direction":"rtl"},{"text":"09:30","direction":"ltr"}]}` to isolate a Latin/date/number run using native `\textenglish`. Do not insert bidi control characters. Titles and table cells currently require plain strings; complex mixed-direction title/table content belongs in native LaTeX.

Plain text is escaped, never treated as raw TeX. In contrast, native `.tex` is executable and needs a trusted source or an isolated environment. The converter does not translate, OCR, fetch sources, infer missing partners or install dependencies.

## Format scope and diagnostics

JSON is the implemented file reader. YAML, JSONL or CSV can represent equivalent meanings only after an explicit mapping to the same ordered fields, IDs and relationships. There are no format-specific renderers, and arbitrary flat CSV is not assumed to contain nested figures/tables or translation relationships. Convert such input explicitly or ask when the mapping is ambiguous.

Commands emit JSON. Exit codes: 1 invalid input, 2 missing dependency/font/glyph, 3 runtime/build failure, 4 mechanical acceptance failure. Read the `error` or `errors` field and the referenced local compile log; repair the source/dependency and export to a new directory. Do not suppress a failing gate to claim success.

## Flowing prose and one shared image

An ordinary paragraph may add `"flow": "breakable"`. It maps to `\ParallelProse`: both texts start together, each can cross pages naturally, and the next block resynchronizes below the longer text. No arbitrary text splitting or font shrinking is performed. Line breaks and within-paragraph page breaks may differ. The default `"atomic"` remains a bounded pair. `flow` is rejected on non-paragraph blocks.

A figure may add `"placement": "shared"` to print one image across the full text width, with two localized captions and the divider hidden behind it. Use a scalar image path for this placement; a pair is rejected. Default `"paired"` places the selected images in their columns, repeating a scalar image for backward compatibility. Both map to the same native package helpers. A shared figure reserves `<id>.caption`; figures remain bounded units that must fit on a page.

```json
{"id":"photo","kind":"figure","image":"footpath.png","placement":"shared",
 "text":["A shared path photograph.","Une photographie de sentier commune."]}
```

```json
{"id":"route","kind":"figure","image":["route-en.png","route-fr.png"],
 "text":["A schematic route.","Un itinéraire schématique."]}
```

## Image asset boundary

The asset root is `--asset-root DIRECTORY`, or the input JSON file's parent directory when omitted. The root option is a filesystem path supplied by the caller; every JSON image value is relative to that root. Bundled article JSON uses simple names such as `footpath.png` and `route-en.png`, and the example commands supply the skill's `assets/` directory explicitly.

Absolute image paths, traversal such as `../`, and symlinks resolving outside the root are rejected. Each image must exist as a supported local PNG/JPEG file inside the resolved root. The exporter safely stages images in the output, so an exported project does not depend on the original asset pool. The option does not authorize arbitrary file reads or relax source/image rights. The converter never downloads remote images.
