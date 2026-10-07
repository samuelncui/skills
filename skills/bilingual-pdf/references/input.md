# JSON input API reference

The structured route converts caller-supplied paired content into an editable native LaTeX project using the same [paralleltext.sty](../assets/paralleltext.sty) as native authoring. The calling agent chooses both texts and corresponding units; this layout tool does not translate, reconcile sources or impose an editorial workflow.

The machine-readable contract is [document.schema.json](../schemas/document.schema.json), JSON Schema Draft 2020-12. Its descriptions explain every field. This independent Markdown reference explains runtime behavior and semantic checks. Worked TeX/PDF tutorials complement these references; they do not replace them.

## Minimal input

~~~json
{
  "$schema": "../../schemas/document.schema.json",
  "languages": ["en", "he"],
  "title": ["Parallel text", "טקסט מקביל"],
  "layout": {"paragraph_flow": "breakable"},
  "blocks": [
    {"id": "start", "kind": "heading",
     "text": ["Start here", "התחילו כאן"]},
    {"id": "first", "text": ["One aligned paragraph.", "פסקה אחת מיושרת."]},
    {"id": "short", "flow": "keep",
     "text": ["Keep this pair together.", "השאירו את הזוג הזה יחד."]}
  ]
}
~~~

Adjust the optional $schema reference to the input's actual location. Editors/validators can use it; the renderer ignores it. Use schema validation in read-only mode: defaults are annotations, and omitted layout fields inherit profile values. Preserve those omissions when converting or validating input.

## CLI

Run from the installed bilingual skill. For an editable export, compile the generated `document.tex` before validating its PDF:

~~~sh
python3 scripts/bilingual_pdf.py preflight input.json
python3 scripts/bilingual_pdf.py export input.json --output new-project
(cd new-project && latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape document.tex)
python3 scripts/bilingual_pdf.py validate new-project/document.pdf --paired
~~~

Alternatively, `python3 scripts/bilingual_pdf.py render input.json --output another-project` performs export, compilation and mechanical validation together. Choose one route and a fresh output directory; both produce editable native sources.

| Command | Input and behavior |
| --- | --- |
| preflight | JSON. Runs runtime structural/semantic validation, then checks Python packages, XeLaTeX tools/packages, exact font matches and text glyph coverage. Does not export or resolve/decode figure assets. |
| export | JSON; requires --output. Validates, stages local image assets, and writes native source. Does not compile or require TeX preflight. Python/Pillow are needed for export. |
| render | JSON; requires --output. Validates, preflights, exports, compiles through latexmk and runs mechanical PDF checks. Pixel review remains required. |
| build | JSON; requires --output. Creates or safely updates a managed native project, then runs the same preflight, latexmk and mechanical checks. Preserves unchanged files and build dependencies. |
| validate | Existing PDF, not JSON. Checks PDF geometry/fonts/links and any matching log; optionally checks matching AUX alignment records and cover parity. |

| Option | Default and scope |
| --- | --- |
| --output DIRECTORY | Required for export/render/build. Export/render reject existing directories; build accepts only a new directory or one previously created by build. |
| --asset-root DIRECTORY | Input JSON's parent directory. Export/render/build resolve every image relative to this root. For bundled tutorial assets use --asset-root examples/shared from the skill directory. |
| --mode bilingual / left / right | bilingual, exported as native paired. Left/right uses the matching title/text/image. Validation/preflight still examines the supplied two-sided document. |
| --paired | For PDF validate, require paired position evidence from the matching AUX. Off by default. |
| --covers | For PDF validate, require default cover/blank-face/even-final-page policy. Off by default. |
| --margin-mm NUMBER | For PDF validate, nominal horizontal ink exclusion, default 18 mm. Match intentional geometry/furniture. |
| --no-covers | Compatibility flag; default validation already assumes no covers. Does not override JSON layout.covers or undo --covers. |

Exports include document.tex, languages.tex, content.tex, paralleltext.sty, LICENSE and staged images. A build adds PDF/AUX/log files; render writes result.json and compile.log. Portable source delivery includes TeX, package, assets and applicable licenses, not unrelated private inputs or transient logs. Exported native projects need no Python to compile.

Commands emit JSON. Exit codes: 0 success; 1 invalid input; 2 failed dependency/font/glyph preflight; 3 runtime/build/import failure; 4 mechanical acceptance failure. Read error/errors and compile logs. Failed export/build can leave partial output; preserve evidence and use a new output path. Do not suppress a failing check.

## Incremental builds

For repeated structured edits, start with a new managed project:

~~~sh
python3 scripts/bilingual_pdf.py build input.json --output managed-project
# Edit input.json or its source images, then run the same command again.
python3 scripts/bilingual_pdf.py build input.json --output managed-project
~~~

`build` regenerates into an isolated temporary staging directory and compares bytes before updating its owned files. Unchanged TeX, package and image files keep their timestamps. latexmk decides which dependencies need rebuilding and how many passes settle references. Content, language, configuration, mode, same-filename image and installed package changes are detected. Every invocation still validates the JSON, checks the current toolchain/fonts/glyphs and mechanically checks the resulting PDF. A no-op avoids TeX work, not acceptance checks. Batch related content edits when practical.

The `.bilingual-build.json` receipt tracks generated inputs; preserve it with the working directory. Existing arbitrary/native projects are not adopted. Manual edits to owned TeX/package/image files, colliding user files and symlinked managed paths are rejected before updates. Use JSON as the editing source for this route. If you prefer native editing, continue with latexmk and `validate`, or choose a new directory for later JSON builds. Unrelated files remain untouched. Removed generated images are removed; current image bytes are decoded and staged on every build.

An interrupted source update records old/new hashes so a later build can reconcile only known bytes. A failed compilation preserves source and dependency files for diagnosis and retry, and marks result.json unsuccessful even if the previous PDF remains. The exclusive `.bilingual-build.lock` prevents simultaneous writers; after an interrupted process, verify no build is running before removing only that stale lock. Ownership receipts and locks are not a sandbox against hostile native TeX or a hostile directory owner. Preserve prior deliverable PDFs separately when their exact historical revision is needed.

## Document fields

| Field | Required/type | Purpose and default |
| --- | --- | --- |
| languages | Required array of two profile IDs | Physical [left,right] order. en, fr, zh-Hans, zh-Hant, ja, ar, he. Duplicate IDs permitted. Mixed zh-Hans/zh-Hant rejected. No default. |
| title | Required array of two nonempty plain strings | Paired printed title. Left title becomes PDF title in bilingual/left mode; right title in right mode. No rich runs. No default. |
| blocks | Required nonempty array of block objects | Ordered layout units. No default. |
| layout | Optional object | Sparse presentation overrides; missing means package defaults. Unknown layout/nested style keys are rejected. |
| $schema | Optional editor annotation | Ignored by renderer; use the bundled schema location in schema-aware tools. |

Root and block objects accept unrecognized fields for compatibility; rendering ignores these fields. Kind-specific fields on unrelated kinds are also ignored, except flow and placement, whose presence is restricted. The schema mirrors this open-object behavior. Prefer documented fields: accepting a key does not mean it does anything. Layout, divider, page_numbers, rich-text and run objects are closed.

## Text and direction

Plain text must contain a non-whitespace character. Newline/tab are permitted; other C0 controls and U+202A–U+202E/U+2066–U+2069 direction controls are rejected. Text is escaped literally, not evaluated as TeX. A newline does not create a new aligned paragraph; use another block for a new alignment boundary.

An RTL-side text value may instead be:

~~~json
{"runs": [
  {"text": "בשעה: ", "direction": "rtl"},
  {"text": "09:30", "direction": "ltr"}
]}
~~~

The object has exactly one key, runs, with a nonempty array. Every run has exactly text (nonempty plain string) and direction (ltr or rtl); neither has a default. Runs concatenate without invented spaces. LTR uses native \textenglish; RTL inherits the enclosing Arabic/Hebrew language. Runs are permitted in paired block text, list items, table headers and table body cells, but only on an Arabic/Hebrew (RTL-profile) side. Non-RTL sides require plain strings in all these positions; document titles require plain strings on both sides. More complex per-run language/font control belongs in trusted native TeX.

A table without a supplied caption omits `text`; no caption or caption spacing is generated. If a caption is supplied, both sides must remain nonempty. Other block kinds still require `text`.

## Common block fields

| Field | Constraint | Meaning |
| --- | --- | --- |
| id | Required; [a-z][a-z0-9.-]{0,79} | Unique stable ID/link target. pt-title is reserved. IDs are not page numbers. |
| kind | Optional enumerated string | Default paragraph; kinds below determine shape/operation. |
| text | Required except for uncaptioned tables; exactly two sides when provided | For lists, two nonempty equal-length item arrays. For other kinds, two text values. |
| break_before | Optional boolean | Default false; emits \clearpage before this unit. |
| flow | Optional, paragraph only | keep, breakable, or atomic (compatibility alias for keep). Omitted inherits layout.paragraph_flow, default keep. |
| placement | Optional, figure only | paired (default) or shared. |

Paragraph flow is explicitly selectable. A kept pair starts together and cannot split internally; an oversized pair fails without shrinking or truncation. Breakable prose starts together, permits independent line/page breaks, then resynchronizes the next unit below the longer side. It does not force identical line breaks.

## Block kinds

### paragraph, heading, quote

- paragraph: paired body content with the chosen paragraph-flow policy
- heading: emits one numbered native section and one TOC/bookmark entry
- quote: bounded paired quote environments, a layout style only

No additional fields are required. Heading/quote reject flow.

### list

Text is [left_items,right_items], with nonempty arrays of equal length. Each corresponding item becomes a bounded paired bullet-list unit. Pagination can occur between items, not inside an oversized item. Generated IDs are <id>.item-1, <id>.item-2, etc.; the block anchor attaches to the first item.

~~~json
{"id":"steps","kind":"list",
 "text":[["Choose a layout.","Build the PDF."],
         ["Choisissez une mise en page.","Compilez le PDF."]]}
~~~

### figure

Required image is a relative PNG/JPEG path or exactly two paths [left,right]. With default paired placement, a scalar repeats on both sides; a pair selects localized images. Shared placement requires a scalar and prints one image across the text area with paired captions below. Text supplies captions.

~~~json
{"id":"layout","kind":"figure","placement":"shared",
 "image":"layout-diagram.png",
 "text":["One shared diagram.","Un schéma commun."]}
~~~

Figure-only `caption_prefix` is `automatic` (default) or `none`. Choose `none` when the supplied caption should be printed exactly, including any source-authored figure label. The figure counter and anchors remain; only the generated localized label is omitted. Native authors use the public `\ParallelFigureLabel` hook.

Shared figures reserve <id>.caption. Both forms are bounded; image plus captions must fit. JSON provides no arbitrary graphicx option string or remote URL.

For a trusted vector original, prepare and compare a supported raster derivative using the [image-fidelity procedure](latex.md#faithful-image-derivatives). Preserve the original and supplied captions; verify strokes, fonts and labels before embedding the PNG/JPEG.

### table

Required headers is [left_headers,right_headers], with matching 1–5-cell arrays. Required rows contains two nonempty arrays of body rows with equal counts. Each row must match its header width. Header and body cells accept nonempty plain strings; on an Arabic/Hebrew side they also accept the directional-run objects described under Text and direction. Non-RTL cells require plain strings. Text contains paired captions.

~~~json
{"id":"settings","kind":"table",
 "text":["Two layout choices.","Deux choix de mise en page."],
 "headers":[["Setting","Value"],["Réglage","Valeur"]],
 "rows":[[["Flow","Breakable"]],[["Flux","Sécable"]]]}
~~~

Directional cells use the same escaping, nonempty-run and control-character checks as other text. LTR runs use the declared English/Latin font, allowing identifiers such as LaTeX, JSON, left and right within Arabic/Hebrew cells. This does not enable arbitrary TeX or automatic font fallback.

Header/body rows align independently, but the adapter wraps the entire table and captions in ParallelKeep. The complete unit must fit on one page. The JSON table API does not paginate between rows, split oversized rows or repeat continuation headers. Generated IDs: <id>.row-0 for the header, .row-1 onward for data, and <id>.caption.

### equation

Required math is one nonempty shared LaTeX math string of at most 1,000 characters. Text supplies explanations. The adapter keeps an explanation pair and a repeated unnumbered display together; it reserves <id>.formula. For a numbered equation with \ref, use native \ParallelEquation.

Allowed ASCII characters: letters, digits, backslash, braces, caret, underscore, + - * / = ( ) . , space, colon, < > | ! and square brackets. Allowed commands:

~~~text
frac sqrt sum prod int infty alpha beta gamma theta sigma mu pi Delta
times cdot pm leq geq neq approx log ln exp sin cos left right
mathrm mathbf text quad qquad overline hat bar
~~~

Character-code escapes (^^) and backslash control symbols are rejected. The allowlist is not a math grammar; balanced braces/valid TeX still require compilation. Use trusted native authoring for mathematics outside this subset.

### reference

Required target follows the identifier grammar. Without file it must name an explicit block ID in this document; forward references are permitted. Text provides link wording, and native references generate the printed page.

External-reference fields:
- file: relative PDF matching (?:\.\./)?[a-z][a-z0-9/_-]*\.pdf, such as notes.pdf or ../notes/notes.pdf
- page: required with file; positive 1-based physical PDF page with integer JSON representation
- page_label: optional nonempty plain printed folio such as iii; defaults to decimal page for display

For an external reference, target remains syntactically required but file/page determine the link. Page labels do not change destinations. Without file, page/page_label are ignored. Export does not fetch/copy companion PDFs; provide them at the authorized relative destination and verify actual pages/links.

## Layout fields

Numeric limits include endpoints unless marked positive. Booleans are not numbers. Unknown keys are errors.

| Field | Valid values | Default / application |
| --- | --- | --- |
| profile | article, bound, reading | article means no native preset; apply before other fields |
| paper | a4, letter, a5, legal | a4 |
| twoside | Boolean | true in generated article; mirrors logical page geometry |
| paragraph_flow | keep, breakable | keep; block flow overrides |
| font_size | 9–14 pt | 9; reading 11 |
| leading | 9–24 pt; at least body size | 10.8; reading 14. Explicit font_size without leading emits size × 1.2 rounded to two decimals. |
| margin_mm | 8–45 mm | Omitted preserves profile; sets both side margins before individual overrides |
| inner_mm | 8–45 mm | 18; bound 24; overrides margin_mm inside |
| outer_mm | 8–45 mm | 18; bound 16; overrides margin_mm outside |
| binding_mm | 0–20 mm | 0; bound 3, additional to inner margin |
| top_mm | 10–40 mm | 17 |
| bottom_mm | 10–40 mm | 14 |
| gap_mm | 4–16 mm | 6 |
| covers | Boolean | false; true emits default front/back covers |
| divider | Closed object | Sparse profile/package overrides below |
| page_numbers | Closed object | Sparse profile/package overrides below |

Divider members:
- enabled: boolean; default true, reading false
- color: exactly six HTML hexadecimal digits without #, e.g. 708090; omission retains native black!35
- width_pt: greater than zero, at most 3; default 0.3
- style: solid (default), dashed, dotted, densely dashed or densely dotted

Page-number members:
- position: footer-outer (default; reading footer-center), footer-inner/left/center/right, corresponding five header positions, or none
- numbering: arabic (default), roman, Roman, alph, Alph or gobble
- prefix/suffix: literal strings, empty by default, at most 80 characters each, no C0 controls. Unlike body text, blank strings and bidi controls are currently accepted here; use logical text and native language-aware formatting for complex RTL furniture.

Native authoring additionally exposes roles, entries, tabs, typography declarations, trusted colors/styles, custom paper dimensions and cover policies. These are not executable JSON options.

## Checks beyond JSON Schema

Use schema validation and the renderer. Standard Draft 2020-12 does not compare arbitrary data values or inspect files. Runtime checks additionally enforce:

1. Unique explicit IDs and no explicit/generated child-ID collisions.
2. Local reference targets exist among explicit block IDs.
3. Both list sides have equal item counts; table sides have equal header widths/row counts; each row matches its header width.
4. Leading is at least effective font_size after profile selection.
5. External page parsing representation: Python requires an int and rejects 1.0/booleans, whereas JSON Schema's mathematical integer type may accept 1.0.
6. Asset-root existence, real-file/symlink containment, supported image decoding and safe staging.
7. Exact font families, glyph coverage, TeX packages and tools.
8. Compilation, bounded-unit fit, references, PDF geometry/alignment and actual page appearance.

The schema encodes RTL-run restrictions, plain-text controls, supported profiles and prohibited mixed Chinese pair, kind-specific requirements, path syntax, math alphabet/command allowlist and numeric limits. It does not prove math syntax; the validator may accept a trailing/incomplete command and compilation must still succeed.

## Assets and trust boundary

Image paths start with an ASCII letter/digit, use only letters/digits/underscore/dot/slash/hyphen and end in lowercase png, jpg or jpeg. Absolute paths, traversal components, spaces, URLs and backslashes are rejected. Symlinks must resolve inside the selected root. Images are decoded/re-encoded as staged PNGs. The converter never downloads them; an asset-root option does not authorize unrelated file access.

Plain JSON text is escaped and mathematics allowlisted. Native TeX, packages and latexmk configuration execute code; editing exported TeX crosses into that native trust model. Use trusted inputs or suitable isolation. No-shell-escape is not a filesystem sandbox.

JSON is the implemented file format. CSV, YAML and JSONL need explicit conversion into this structure; paired cells, missing partners and nested blocks are not inferred. The tool does not OCR, install dependencies, fetch sources or certify accessibility. Finish with [layout acceptance checks](acceptance.md), including actual PDF pixels; report passed, failed and unrun checks separately.
