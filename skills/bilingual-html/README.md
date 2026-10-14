# Bilingual HTML

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Turn supplied bilingual text pairs into a portable offline document. Each passage stays together: two columns on desktop, source then target on narrow screens. Use it for parallel-reading articles, instructions and handouts that readers open in a browser.

The caller supplies the corresponding text. This skill preserves it and lays it out; source extraction, translation and deciding which statements correspond belong to the calling workflow.

## What it does

- Aligns the starts of paired headings, paragraphs and list items
- Keeps real table rows and cells, with both languages inside each cell and keyboard-accessible horizontal scrolling for wide tables
- Displays one shared image per figure, with paired captions and alternative descriptions
- Separates each language's LTR/RTL direction from physical desktop column order
- Provides configurable widths, spacing, colors and per-language font families
- Produces HTML, CSS and local assets without JavaScript, remote fonts or a runtime server

## Complete example and preview

The original English/French tutorial explains this skill while demonstrating headings, prose, ordered/unordered lists, a table and a figure:

- [Editable layout JSON](examples/tutorial/layout.json)
- [Complete generated HTML](examples/tutorial/site/index.html), viewable after downloading the whole `site/` directory
- [Original figure](examples/tutorial/images/pairs.png) and [example manifest](examples/MANIFEST.json)

From this installed skill's directory, run:

```sh
set -eu
python3 --version
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

Use Python 3.11+. The output directory `page` must be new and its parent must exist. Open `page/index.html` directly in a browser. No server or build tool is needed to view it; a repository website may show the HTML source instead of rendering it.

## Structured JSON: supplied pairs

Author layout version 1 using the [minimal runnable input](references/rendering.md#minimal-structured-example), [field contract](references/rendering.md#embedded-pair-layout) and [JSON Schema](schemas/layout.schema.json). To adapt the complete tutorial while preserving the supplied example:

```sh
set -eu
mkdir html-work
cp examples/tutorial/layout.json html-work/layout.json
cp -R examples/tutorial/images html-work/images
python3 scripts/bilingual_html.py render html-work/layout.json --output html-work/page
```

Edit the copied `layout.json`, keeping a unique ID for every heading, paragraph, list item, table cell, caption and alternative-text pair. Keep source and target roles stable; change language tags and directions explicitly. Image paths are relative to this JSON file's directory.

`render` validates the document and assets before writing `index.html`, `style.css`, `LICENSE` and the required image files. It leaves the input unchanged. For later edits, render to another new directory such as `html-work/page-v2`; there is no incremental `build` or separate `preflight` command. See the [CLI and output contract](references/rendering.md#commands-and-output-lifecycle).

## Native HTML: trusted manual authoring

The generated page is ordinary editable HTML. To start from the complete example without Python:

```sh
set -eu
test ! -e native-page && cp -R examples/tutorial/site native-page
```

Edit `native-page/index.html` and `native-page/style.css`, then reopen the page. The [minimal native page and DOM rules](references/rendering.md#native-html-authoring) show how to retain one `.pair` container with language-tagged source and target children. Reuse the owned stylesheet, real table structure and paired figure descriptions.

This is a manually reviewed HTML/CSS route. The JSON renderer does not import HTML or validate manual edits, and it cannot round-trip rich markup into JSON. Keep either the JSON or the edited native page as the authoring source. Review any added markup, links, assets and behavior separately; untrusted HTML can execute code or access the network.

## Translation before layout

For raw source, first discover the separately installed `bilingual-translation` skill through your host and follow its translation/review workflow. Set `TRANSLATION_SKILL` to that verified installation path. Given its current, reviewed `master.jsonl`, use:

```sh
set -eu
python3 "$TRANSLATION_SKILL/scripts/workflow.py" export master.jsonl --output reviewed.json
python3 scripts/bilingual_html.py import-pairs reviewed.json \
  --translation-skill "$TRANSLATION_SKILL" --contract-version 1 --output imported
python3 scripts/bilingual_html.py render imported/layout.json --output translated-page
```

Use project input paths as needed and fresh destinations. The first command exports translation exchange v1; the second maps it to HTML's independent layout v1. HTML does not consume JSONL directly. Existing reviewed exchange-v1 JSON can start at `import-pairs`.

Import invokes the selected translation validator, rejects unfinished/stale targets and preserves paired strings, IDs and order. It creates `layout.json`, copied supported assets and `import-record.json`. Keep the JSONL master and exported exchange file for translation history; layout JSON is a rendering derivative. Export rejoins split chunks into parent pairs, so HTML does not retain child-level alignment or review records. See [asset staging, version/hash pinning and handoff limits](references/rendering.md#optional-translation-import). Supplied layout pairs need no translation dependency, and missing skills are never installed automatically.

## Configure and review

Defaults work without setup. Optional `config` controls `browser_title`, `desktop_order` and sparse `styles`. For example:

```json
{"desktop_order":"target-first","styles":{"column_gap":"2rem","source_weight":1,"target_weight":1.25,"source_font":["Noto Sans","sans-serif"],"target_font":["Noto Naskh Arabic","serif"]}}
```

Place this object under `config`, adapting fonts to the declared languages. [All keys, units and defaults](references/rendering.md#styling) are documented in one reference. Desktop order changes CSS presentation only; DOM and mobile order remain source then target at the 48rem breakpoint. Fonts must already be available on the viewing device; the skill does not download or bundle them.

Before delivery, follow the [review checklist](references/rendering.md#review-boundaries):

1. Read both languages against the supplied material for completeness and meaning.
2. Open the actual page offline at desktop and narrow widths, including reversed desktop order and relevant RTL/CJK text. Inspect glyphs, shaping, wrapping, long cells, numbers and browser zoom.
3. Use the keyboard to focus and scroll wide tables; inspect images, captions and both alternative descriptions. Review contrast and assistive-technology behavior for the intended audience.
4. Report structural checks, language review and visual/accessibility review separately, including failures and checks not run. A successful render is not translation approval or accessibility certification.

## Independent installation, dependencies and delivery

Install the complete `bilingual-html` directory through your host's skill installation flow, preserving `SKILL.md`, scripts, assets, schemas, references, examples and `LICENSE`. It works without the repository checkout, maintainer tools, `bilingual-pdf` or `bilingual-translation`. Use the discovered script path when running outside the installed directory; work in a writable project directory if the installation is read-only.

Rendering and importing require Python 3.11+ with its standard library. Viewing or manually editing an existing native bundle needs only a browser/text editor and suitable local fonts. Only translation import additionally requires an explicitly discovered compatible translation skill.

Deliver the entire output directory, preserving relative paths, with the editable JSON/native source as appropriate. Keep import provenance and the translation master with the project when used. Do not deliver `index.html` alone when it depends on the accompanying CSS or images.

## Limits and safety

Layout v1 accepts literal Unicode text and local PNG/JPEG figures. It displays HTML, Markdown and TeX literally; there is no rich-text, equation, hyperlink or script syntax in JSON. It is not an OCR tool, translator or existing-page layout extractor. Browser print rules provide basic assistance, not controlled PDF pagination.

Raster paths, sizes and structure are bounded; remote URLs, traversal, symlinks and SVG input are rejected. See [asset constraints](references/rendering.md#assets-and-output) and [faithful raster derivatives of trusted SVG](references/rendering.md#faithful-derivatives-of-trusted-svg-originals). Header checks do not fully decode images. Review actual browser output; a small language sample does not establish universal language or accessibility support.

The [agent workflow](SKILL.md) gives the concise procedure. Code, documentation and original example assets use the [MIT license](LICENSE); retain licenses for any added assets and keep private material out of public examples.
