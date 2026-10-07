# Rendering contract and review

## Contents
- Embedded-pair layout
- Text and structure
- Styling
- Assets and output
- Optional translation import
- Review boundaries

## Embedded-pair layout

Python 3.11+ is the only runtime dependency. [layout.schema.json](../schemas/layout.schema.json) describes layout version 1; the executable validator reports invalid input before writing. The [complete original English–French tutorial](../examples/tutorial/layout.json) is both documentation and an input you can render.

A document contains `layout_version: 1`, `languages`, optional `config`, and ordered `blocks`. Each language is `{"tag":"en","dir":"ltr"}`. Tags use a conservative hyphenated language-tag subset, such as `en`, `zh-CN`, `fr`, `ar` or `he`; direction must be explicitly `ltr` or `rtl`.

Every text pair is `{"id":"intro","source":"Hello.","target":"Bonjour."}`. Both texts are nonempty literal Unicode. IDs start with an ASCII letter and then use ASCII letters, digits, underscores, periods, colons or hyphens. IDs are unique across the document. No translation status, hash, revision or translation skill is required.

Blocks:
- Heading: `{"type":"heading","level":1,"pair":PAIR}`; levels 1–6.
- Paragraph: `{"type":"paragraph","pair":PAIR}`.
- List: `{"type":"list","ordered":false,"items":[PAIR,PAIR]}`.
- Table: `{"type":"table","headers":[PAIR,PAIR],"rows":[[PAIR,PAIR]],"caption":PAIR}`. Caption is optional. Headers and rows are nonempty; all rows have the header cell count.
- Figure: `{"type":"figure","asset":"images/pairs.png","caption":PAIR,"alt":PAIR}`. Caption and alternative-text pairs are required.

Unknown fields, duplicate JSON keys, duplicate IDs, malformed structures and unresolved texts are errors. Use a unique ID for each structural occurrence, even when its wording repeats. Read the entire original source before choosing paragraph boundaries; a renderer does not repair missing content.

## Text and structure

All text is HTML-escaped. Strings resembling tags, formulas or Markdown remain text. There is no inline HTML, raw TeX, URL embedding, arbitrary CSS or script execution interface. The JSON route is deliberately plain-text v1; it cannot preserve arbitrary rich source markup.

Each pair is one logical DOM container with source followed by target. Headings and paragraphs contain two language spans; list items contain a pair. Real `table`, `thead`, `tbody`, `tr`, `th scope="col"` and `td` elements preserve row/cell semantics. Each cell contains its two texts. Narrow screens stack the two languages within each cell. Cells retain word-based minimum widths instead of squeezing headings, times and numbers into single-character lines. When the table is wider than the page, its own region scrolls horizontally; prose stays within the viewport. The region is keyboard-focusable, has a direction-neutral `↔` cue, visible focus ring and scrollbar styling, and takes its accessible name from the supplied bilingual caption or first header. Focus it and use the arrow keys to reach columns outside the view. Very long unbroken identifiers can require substantial horizontal scrolling; review the actual data at the intended viewport and zoom.

A figure is shared once. Its image has source fallback alt text and an accessible name referencing both language-tagged alternative-text spans in the same hidden pair. Its visible caption is another pair. These choices provide a reviewable semantic foundation, not a screen-reader or accessibility certification.

## Styling

Optional `config` accepts:
- `browser_title`: literal text for the browser tab; otherwise the first heading's source text.
- `desktop_order`: `source-first` (default) or `target-first`. Physical order changes only in desktop CSS. DOM and narrow screens remain source then target.
- `styles`: sparse overrides from the list below. All others are rejected.

The owned `assets/style.css` defines these CSS variables; configuration writes safe overrides into the delivered copy. Snake-case config keys map to hyphenated variable names.

| Config keys | Values | Defaults |
| --- | --- | --- |
| `max_width`, `column_gap`, `block_gap`, `font_size`, `page_padding` | Positive length up to 1000 in rem, em, px or ch | 78rem, 1.6rem, 1.25rem, 1rem, 1.4rem |
| `source_weight`, `target_weight` | Number 0.5–4, rendered as grid fractions | 1, 1 |
| `line_height` | Number 0.5–4 | 1.65 |
| `background`, `foreground`, `muted`, `border`, `accent` | Six-digit hex color | See stylesheet |
| `source_font`, `target_font` | Nonempty arrays of simple font family names | system-ui, sans-serif |

For example, `{"desktop_order":"target-first","styles":{"source_font":["Noto Sans","sans-serif"],"target_font":["Noto Naskh Arabic","serif"],"column_gap":"2rem","source_weight":1,"target_weight":1.25}}`.

Font names select fonts already available on the viewing system. Fonts are neither downloaded nor bundled. A family name does not prove glyph coverage, correct shaping, line breaking or readability. Inspect actual CJK/RTL/combined-script glyphs and wrapping in the delivery environment. Font family names in this v1 interface use ASCII letters, digits, spaces and hyphens. For additional trusted styling, manually edit the delivered CSS and review the result; the JSON schema intentionally does not accept arbitrary CSS.

The mobile breakpoint is 48rem. Source/target language directions are independent of the left-to-right layout wrapper. Any new color palette, text size or column ratio needs visual and contrast review. Print rules are basic browser-print assistance, not a paginated PDF renderer.

## Assets and output

Figures accept local PNG and 8-bit baseline/progressive JPEG files in v1. For a trusted original SVG, follow [faithful derivative checks](#faithful-derivatives-of-trusted-svg-originals), preserving the original and its paired caption/alternative text. SVG itself is not accepted by this renderer because it can contain active or remote content. Paths are relative to the JSON file's directory, use forward slashes, and may contain ASCII letters, digits, spaces, underscores, periods or hyphens. Absolute paths, URLs, traversal, empty path components and symlinks are rejected. Raster images are limited to 20 MiB and 16000 pixels per dimension. PNG chunk integrity and JPEG marker/frame/scan boundaries are checked; compressed pixels are not fully decoded. These are bounded structural checks, not a full image-decoder audit. Open every delivered image in the intended browser.

Rendering copies checked image bytes and the owned stylesheet into a new directory; no network access is performed. Keep original source images separate and unchanged. The output directory must not exist, its parent must exist, and symlinked output paths are rejected. A write failure removes only the newly created output directory. Choose another directory for each revision and compare before replacing a previously delivered version.

The output consists of `index.html`, `style.css`, `LICENSE` and required PNG/JPEG assets. Preserve their relative paths and share the whole directory. Source JSON remains unchanged. Rebuilds from identical input/style/assets produce identical output bytes.

## Optional translation import

Discover the installed `bilingual-translation` skill using the host's installed-skill discovery. Set `TRANSLATION_SKILL` to that verified directory; no sibling path is assumed. The path selects trusted installed executable code and should never come from untrusted document text.

```sh
python3 scripts/bilingual_html.py import-pairs reviewed.json \
  --translation-skill "$TRANSLATION_SKILL" \
  --contract-version 1 --output imported
python3 scripts/bilingual_html.py render imported/layout.json --output page
```

Both destination parents must already exist. Import produces `layout.json`, copied PNG/JPEG assets and `import-record.json`. It loads `scripts/translation_contract.py` from the selected skill and calls `validate_document(data, require_ready=True)`. Only reviewed, current, nonempty targets pass. Stale, draft and unresolved units must be resolved through the translation owner before publication. Nothing is silently omitted or retranslated.

Mapping preserves exact source and target strings, pair IDs and block/row/cell ordering. It converts unit references into embedded rendering pairs. Translation history and hashes remain in the original semantic master, not the layout schema. Table captions and figure alternative text retain their pair identities.

Pin `--contract-version 1`. For reproducible projects, record the tested skill release or commit and the validator SHA-256; `--tested-revision LABEL` records the supplied revision label and `--validator-sha256 HEX` verifies an expected validator hash before loading it. The importer always records the actual hash. A supplied label is a project assertion, not independently verified Git history. Keep these records with the project's source master and renderer version, without public machine-specific paths.

The adapter needs only the semantic owner's public validator and owns only HTML mapping. It carries no copy of the translation SOP or validator. It does not install a missing dependency. Already paired layout JSON uses `render` directly.

## Review boundaries

Objective checks can establish parsing, escaping, pair order, DOM structure, copied-asset bounds, reproducibility and dependency separation. They cannot establish factual equivalence, completeness relative to unseen sources, translation quality, readable glyphs, assistive-technology behavior or visual quality. Review those separately at the requested scope.

Open the page offline at desktop and mobile widths, including a target-first desktop variant and an RTL pair. Check intact short headings and times (for example `14:30`), long cells, browser zoom, visible horizontal-scroll affordance and keyboard scrolling, images and captions, actual font rendering, and whether both alternative descriptions express the same image. Do not describe a small sample as all-language support or accessibility certification.

## Faithful derivatives of trusted SVG originals

Keep the original SVG unchanged and record the derivative's source, converter/version, fonts and dimensions. Use an already-installed full SVG renderer where available, for example `rsvg-convert --width 2160 --keep-aspect-ratio --output figure.png original.svg`, or a supported browser's element screenshot at a declared viewport/scale. The [upstream rsvg-convert reference](https://gnome.pages.gitlab.gnome.org/librsvg/Rsvg-2.0/rsvg-convert.html) documents sizing and format options. Verify that executable/browser is actually available. A conversion library's ability to open SVG is not evidence that it supports every SVG feature.

Open the original in a standards-capable viewer and compare it with the raster at readable size. Check dashed versus solid strokes, marker/arrow direction, line joins, clipping, opacity, text/font metrics, numbers and labels, and overall geometry. A numerical diagram needs both visual and semantic comparison. Retain the paired caption and alternative text; update only the asset path to the verified derivative. Review browser decoding separately from the helper's bounded image-header checks.

If the available converter changes a meaningful feature, retain the original and try an already-authorized capable converter or request the missing tool. Describe the unresolved fidelity difference precisely. A successful command or valid PNG header is not a faithful-conversion pass. Native workflows may preserve the trusted vector where their supported toolchain can render it correctly.
