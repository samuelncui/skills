# Rendering contract and review

## Contents
- [Commands and output lifecycle](#commands-and-output-lifecycle)
- [Minimal structured example](#minimal-structured-example)
- [Native HTML authoring](#native-html-authoring)
- [Embedded-pair layout](#embedded-pair-layout)
- [Text and structure](#text-and-structure)
- [Styling](#styling)
- [Assets and output](#assets-and-output)
- [Optional translation import](#optional-translation-import)
- [Review boundaries](#review-boundaries)
- [Faithful derivatives of trusted SVG originals](#faithful-derivatives-of-trusted-svg-originals)

## Commands and output lifecycle

Run commands from this installed skill's directory, or use the script's discovered absolute path from a writable project directory. Shell examples use a POSIX-style shell. Install the whole skill; the renderer locates its own `assets/style.css` and `LICENSE` relative to its script, without a repository checkout or sibling installation.

| Command | Input | Output |
| --- | --- | --- |
| `render INPUT.json --output NEW_DIRECTORY` | This skill's embedded-pair layout and local images | `index.html`, `style.css`, `LICENSE`, required images |
| `import-pairs INPUT.json --translation-skill PATH --output NEW_DIRECTORY` | Reviewed semantic translation exchange and local images | `layout.json`, `import-record.json`, required images; render it in a second step |

Both commands accept `--help`. These are the only CLI subcommands: there is no direct JSONL/HTML input, independent `preflight`, incremental `build` or overwrite switch. `render` checks layout and assets before writing. Handled input/output errors exit with status 2 and an `error:` diagnostic; success exits 0 and prints the output path. Successful generation establishes neither linguistic approval nor visual acceptance.

Use a new output directory with an existing, non-symlinked parent for every attempt. For a revised JSON manuscript, change the input and render to a fresh sibling output. For manually edited native HTML, keep the HTML/CSS as the editing source and reopen it in the browser; the JSON renderer does not preserve those edits or import them back. Keep originals and previous deliverables until the replacement has passed review.

## Minimal structured example

From the installed skill directory, this creates a complete two-block input and output in a new working directory:

```sh
set -eu
mkdir minimal-project
cat > minimal-project/layout.json <<'JSON'
{
  "languages": {
    "source": {"tag": "en", "dir": "ltr"},
    "target": {"tag": "fr", "dir": "ltr"}
  },
  "blocks": [
    {"type": "heading", "level": 1,
     "pair": {"id": "title", "source": "A shared guide", "target": "Un guide commun"}},
    {"type": "paragraph",
     "pair": {"id": "intro", "source": "Read both versions together.",
              "target": "Lisez les deux versions ensemble."}}
  ]
}
JSON
python3 scripts/bilingual_html.py render minimal-project/layout.json --output minimal-project/page
```

Open `minimal-project/page/index.html` in a browser. This example needs only Python 3.11+ and its standard library. For tables, figures and lists, adapt the [complete tutorial](../examples/tutorial/layout.json), copying its `images/` folder beside your JSON. Save all source files as UTF-8.

## Native HTML authoring

For trusted hand-authored HTML, use the same owned CSS and per-pair DOM as the renderer. An existing [complete example bundle](../examples/tutorial/site/index.html) can be copied and edited without running Python. The following is a complete minimal page; run it from this skill's installed directory:

```sh
set -eu
mkdir native-minimal
cp assets/style.css LICENSE native-minimal/
cat > native-minimal/index.html <<'HTML'
<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'self'; base-uri 'none'; form-action 'none'">
<title>A shared guide</title>
<link rel="stylesheet" href="style.css">
</head>
<body class="source-first">
<main>
<h1 class="pair" id="pair-title" data-pair-id="title">
  <span class="text source" data-role="source" lang="en" dir="ltr">A shared guide</span>
  <span class="text target" data-role="target" lang="fr" dir="ltr">Un guide commun</span>
</h1>
<p class="pair" id="pair-intro" data-pair-id="intro">
  <span class="text source" data-role="source" lang="en" dir="ltr">Read both versions together.</span>
  <span class="text target" data-role="target" lang="fr" dir="ltr">Lisez les deux versions ensemble.</span>
</p>
</main>
</body>
</html>
HTML
```

Open `native-minimal/index.html` directly. No compilation or Python runtime is needed. Keep the HTML wrapper and pair grid LTR; set each text child's actual `lang` and `dir` independently. Each logical occurrence has a unique `data-pair-id` and `pair-` DOM ID. Source precedes target in DOM order. Change the body's class to `target-first` only to reverse desktop presentation; preserve language roles and source-first mobile order.

For lists, tables and figures, retain the complete example's native elements, scoped table headers, scroll region, caption relationships and paired alternative descriptions. Extra inline markup belongs to this manually reviewed route, not the JSON contract. Escape literal `&`, `<`, `>` and attribute quotes when authoring HTML. Keep assets local if offline delivery is required; review any links or added behavior and inspect the final DOM and rendered result.

The supplied content-security policy restricts scripts and remote resources. It is not an HTML sanitizer or a sandbox for arbitrary edits, and the renderer does not validate a modified native page. Use trusted authoring inputs or suitable isolation. Keep the entire folder and licenses together.

## Embedded-pair layout

Python 3.11+ is the only runtime dependency. [layout.schema.json](../schemas/layout.schema.json) describes the embedded-pair layout; the executable validator reports invalid input before writing. The [complete original English–French tutorial](../examples/tutorial/layout.json) is both documentation and an input you can render.

A document contains `languages`, optional `config`, and ordered `blocks`. Each language is `{"tag":"en","dir":"ltr"}`. Tags use a conservative hyphenated language-tag subset, such as `en`, `zh-CN`, `fr`, `ar` or `he`; direction must be explicitly `ltr` or `rtl`.

Every text pair is `{"id":"intro","source":"Hello.","target":"Bonjour."}`. Both texts are nonempty literal Unicode. IDs start with an ASCII letter and then use ASCII letters, digits, underscores, periods, colons or hyphens. IDs are unique across the document. No translation status, hash, revision or translation skill is required.

Blocks:
- Heading: `{"type":"heading","level":1,"pair":PAIR}`; levels 1–6.
- Paragraph: `{"type":"paragraph","pair":PAIR}`.
- List: `{"type":"list","ordered":false,"items":[PAIR,PAIR]}`.
- Table: `{"type":"table","headers":[PAIR,PAIR],"rows":[[PAIR,PAIR]],"caption":PAIR}`. Caption is optional. Headers and rows are nonempty; all rows have the header cell count.
- Figure: `{"type":"figure","asset":"images/pairs.png","caption":PAIR,"alt":PAIR}`. Caption and alternative-text pairs are required.

Unknown fields, duplicate JSON keys, duplicate IDs, malformed structures and unresolved texts are errors. Use a unique ID for each structural occurrence, even when its wording repeats. Read the entire original source before choosing paragraph boundaries; a renderer does not repair missing content.

## Text and structure

All text is HTML-escaped. Strings resembling tags, formulas or Markdown remain text. There is no inline HTML, raw TeX, URL embedding, arbitrary CSS or script execution interface. The JSON route is deliberately plain-text; it cannot preserve arbitrary rich source markup.

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

Font names select fonts already available on the viewing system. Fonts are neither downloaded nor bundled. A family name does not prove glyph coverage, correct shaping, line breaking or readability. Inspect actual CJK/RTL/combined-script glyphs and wrapping in the delivery environment. Font family names in this interface use ASCII letters, digits, spaces and hyphens. For additional trusted styling, manually edit the delivered CSS and review the result; the JSON schema intentionally does not accept arbitrary CSS.

The mobile breakpoint is 48rem. Source/target language directions are independent of the left-to-right layout wrapper. Any new color palette, text size or column ratio needs visual and contrast review. Print rules are basic browser-print assistance, not a paginated PDF renderer.

## Assets and output

Figures accept local PNG and 8-bit baseline/progressive JPEG files. For a trusted original SVG, follow [faithful derivative checks](#faithful-derivatives-of-trusted-svg-originals), preserving the original and its paired caption/alternative text. SVG itself is not accepted by this renderer because it can contain active or remote content. Paths are relative to the JSON file's directory, use forward slashes, and may contain ASCII letters, digits, spaces, underscores, periods or hyphens. Absolute paths, URLs, traversal, empty path components and symlinks are rejected. Raster images are limited to 20 MiB and 16000 pixels per dimension. PNG chunk integrity and JPEG marker/frame/scan boundaries are checked; compressed pixels are not fully decoded. These are bounded structural checks, not a full image-decoder audit. Open every delivered image in the intended browser.

Rendering copies checked image bytes and the owned stylesheet into a new directory; no network access is performed. Keep original source images separate and unchanged. The output directory must not exist, its parent must exist, and symlinked output paths are rejected. A write failure removes only the newly created output directory. Choose another directory for each revision and compare before replacing a previously delivered version.

The output consists of `index.html`, `style.css`, `LICENSE` and required PNG/JPEG assets. Preserve their relative paths and share the whole directory. Source JSON remains unchanged. Rebuilds from identical input/style/assets produce identical output bytes.

## Optional translation import

Discover the installed `bilingual-translation` skill using the host's installed-skill discovery. Set `TRANSLATION_SKILL` to that verified directory; no sibling path is assumed. The path selects trusted installed executable code and should never come from untrusted document text.

For the current reviewed JSONL master, export through that skill's public workflow first:

```sh
set -eu
python3 "$TRANSLATION_SKILL/scripts/workflow.py" export master.jsonl --output reviewed.json
python3 scripts/bilingual_html.py import-pairs reviewed.json \
  --translation-skill "$TRANSLATION_SKILL" \
  --output imported
python3 scripts/bilingual_html.py render imported/layout.json --output page
```

HTML accepts semantic translation exchange through `import-pairs`, not direct JSONL. The semantic exchange and embedded-pair layout have different structures; use the adapter to convert between them. For an existing reviewed semantic exchange JSON, start at the second command. Use the discovered translation skill's own instructions to finish review; a draft export is not a publication workaround.

The translation export rejoins split children into their parent units. HTML therefore aligns the resulting parent pairs, not the JSONL child starts, and does not retain the JSONL review history or child records. Preserve the reviewed master and exchange file as source/provenance; regenerate the layout derivative after translation changes instead of maintaining another independent translation copy.

Export writes the exchange JSON only. For semantic exchange documents containing figures, put the JSON where each supported PNG/JPEG asset is available at its declared relative path, or explicitly stage those unchanged assets into that directory. `import-pairs` copies them into its new bundle; `render` copies them into the final page. Neither step downloads missing files or converts SVG. The current compact Markdown preparation route does not accept image/figure syntax; it is not an automatic figure extractor.

All destination parents must already exist; the export file and both output directories must be new. Import produces `layout.json`, copied PNG/JPEG assets and `import-record.json`. It loads `scripts/translation_contract.py` from the selected skill and calls `validate_document(data, require_ready=True)`. Only reviewed, current, nonempty targets pass. Stale, draft and unresolved units must be resolved through the translation owner before publication. Nothing is silently omitted or retranslated.

Mapping preserves exact source and target strings, pair IDs and block/row/cell ordering. It converts unit references into embedded rendering pairs. Translation history and hashes remain in the original semantic master, not the layout schema. Table captions and figure alternative text retain their pair identities.

For reproducible projects, record the tested skill release or commit and the validator SHA-256; `--tested-revision LABEL` records the supplied revision label and `--validator-sha256 HEX` verifies an expected validator hash before loading it. The importer always records the actual hash. A supplied label is a project assertion, not independently verified Git history. Keep these records with the project's source master and renderer version, without public machine-specific paths.

The adapter needs only the semantic owner's public validator and owns only HTML mapping. It carries no copy of the translation SOP or validator. It does not install a missing dependency. Already paired layout JSON uses `render` directly.

## Review boundaries

Objective checks can establish parsing, escaping, pair order, DOM structure, copied-asset bounds, reproducibility and dependency separation. They cannot establish factual equivalence, completeness relative to unseen sources, translation quality, readable glyphs, assistive-technology behavior or visual quality. Review those separately at the requested scope.

Open the page offline at desktop and mobile widths, including a target-first desktop variant and an RTL pair. Check intact short headings and times (for example `14:30`), long cells, browser zoom, visible horizontal-scroll affordance and keyboard scrolling, images and captions, actual font rendering, and whether both alternative descriptions express the same image. Do not describe a small sample as all-language support or accessibility certification.

## Faithful derivatives of trusted SVG originals

Keep the original SVG unchanged and record the derivative's source, converter/version, fonts and dimensions. Use an already-installed full SVG renderer where available, for example `rsvg-convert --width 2160 --keep-aspect-ratio --output figure.png original.svg`, or a supported browser's element screenshot at a declared viewport/scale. The [upstream rsvg-convert reference](https://gnome.pages.gitlab.gnome.org/librsvg/Rsvg-2.0/rsvg-convert.html) documents sizing and format options. Verify that executable/browser is actually available. A conversion library's ability to open SVG is not evidence that it supports every SVG feature.

Open the original in a standards-capable viewer and compare it with the raster at readable size. Check dashed versus solid strokes, marker/arrow direction, line joins, clipping, opacity, text/font metrics, numbers and labels, and overall geometry. A numerical diagram needs both visual and semantic comparison. Retain the paired caption and alternative text; update only the asset path to the verified derivative. Review browser decoding separately from the helper's bounded image-header checks.

If the available converter changes a meaningful feature, retain the original and try an already-authorized capable converter or request the missing tool. Describe the unresolved fidelity difference precisely. A successful command or valid PNG header is not a faithful-conversion pass. Native workflows may preserve the trusted vector where their supported toolchain can render it correctly.
