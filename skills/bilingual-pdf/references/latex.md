# Native LaTeX API reference

The native route builds topic-neutral parallel-text documents directly with XeLaTeX. The calling agent supplies the two texts, their order and their corresponding units. The package handles placement, language contexts, typography and print furniture; it does not generate or translate content. Native and JSON routes use the same [paralleltext.sty](../assets/paralleltext.sty).

This reference covers the public commands and environments. The [configuration reference](configuration.md) lists every setup key, default and style hook. [Language setup](languages.md) covers font selection, RTL and CJK. Names beginning `PT` and `pt-internal:` are implementation details, not an authoring API.

## Project and build contract

Use the standard one-column `article` class. The package requires XeLaTeX and a LaTeX kernel dated 2022-06-01 or later. It loads fontspec, unicode-math, amsmath, geometry, needspace, booktabs, array, tabularx, xcolor, TikZ, graphicx, enumitem, ragged2e, etoolbox, paracol, hyperref, bookmark, fancyhdr, zref-savepos and then Polyglossia. Configure these through their normal interfaces; avoid reloading a package with incompatible options.

A portable project includes its manuscript, language/configuration files, `paralleltext.sty`, referenced images and applicable licenses. Installed examples use the canonical package in `assets/` and example-only images in `examples/shared/`; copy the required files when making an independent project. A native project has no Python runtime requirement.

```tex
\documentclass[10pt,twoside]{article}
\usepackage{paralleltext}
\setotherlanguage{french}
\newfontfamily\frenchfont{Latin Modern Roman}
\newfontfamily\frenchfontsf{Latin Modern Sans}
\ParallelLanguages{english}{french}
\begin{document}
\ParallelTitle{A short observation}{Une brève observation}
\ParallelText{opening}{Notice one detail.}{Remarquez un détail.}
\end{document}
```

No setup call is required. For larger projects, keep language/font declarations in `languages.tex`, presentation in `layout.tex` and body commands in `content.tex`. Input the first two in the preamble and the last inside the document.

```sh
latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error \
  -latexoption=-no-shell-escape main.tex
```

Use enough passes to settle references, entry headers and navigation records. latexmk handles these automatically. Native QA may use the installed helper's `validate main.pdf --paired` command with the matching AUX/log files; this does not make Python a requirement for native compilation.

## Signature conventions and IDs

In the signatures below, braces are mandatory arguments and brackets are optional arguments. A body argument accepts ordinary trusted LaTeX; text is not escaped by the package. Long bodies are supported only where the layout permits them. Dimensions are TeX dimensions unless explicitly described as point numbers.

Every paired unit needs a unique, stable label. Native IDs are standard safe LaTeX label keys, for example `route`, `section:route` or `note.scope`; they are not constrained to the JSON identifier grammar. Avoid spaces, expandable macros and TeX-special characters in keys. The package rejects duplicate paired IDs and keys beginning `pt-internal:`. `pt-title` is used by `ParallelTitle`; do not use it yourself. `ParallelWideFigure{photo}` also consumes `photo.caption`. Ordinary user labels can still collide with package labels, so maintain one label namespace for the manuscript.

Package units create a native label and a hyperlink anchor. `pageref{id}` gives the generated printed folio. `\ref{id}` gives a meaningful number only for a counter-bearing helper (section, subsection, equation or figure); an ordinary text label is not a numbered paragraph.

## Setup and selection

| Public command | Arguments, default and effect |
| --- | --- |
| `\ParallelLanguages{left}{right}` | Polyglossia language names, not JSON codes; initially both `english`. Chooses contexts for physical left/right slots; does not declare languages or fonts. Configure in the preamble. |
| `\ParallelSelect{mode}` | `paired` (default), `left` or `right`; other values error. Select before body output. Right-only uses the right text/image; selection never translates or swaps side order. |
| `\ParallelSetup{key=value,...}` | Preamble-only sparse configuration. Same keys as package options. Processed in order; omitted keys retain current values. See the complete [key reference](configuration.md). |
| `\ParallelDeclareProfile{name}{key list}` | Preamble-only named preset, selected with `profile=name`. Built-ins are `bound` and `reading`. Apply a preset before overrides. No implicit full reset. |

In paired mode each slot has width `(\textwidth-\ParallelColumnGap)/2`. In selected-language mode it uses the current text/column width. Standard `twocolumn` cannot contain paired mode; `single-columns=2` is available only with left/right selection. Avoid mid-page mode or geometry changes; deliberately finish the page before changing the output regime.

## Core placement and headings

| Public command/environment | Contract |
| --- | --- |
| `\ParallelParagraph[flow=default]{id}{left body}{right body}` | Configurable paragraph pair. Optional key `flow` accepts `default`, `keep` or `breakable`; omission/default inherits global `paragraph-flow` (initially keep). Keep delegates to `\ParallelText`; breakable delegates to `\ParallelProse`. Local policy overrides the global default. Unknown keys/choices error. |
| `\ParallelText{id}{left body}{right body}` | One bounded pair. Measures each side once in a top-aligned minipage, reserves the larger height, and starts the next unit below both. The selected side alone is executed in single-language output. Default inter-pair gap is 2.5 pt. Paragraphs use the shared `ParallelParagraphEmergencyStretch` policy (the current column linewidth by default), configurable with `paragraph-emergency-stretch`; see the configuration reference. |
| `\ParallelProse{id}{left body}{right body}` | Flowing prose. In paired mode, paracol starts both sides at one vertical position; each can cross pages, and the next unit resumes after the longer side. Internal line/page breaks can differ. In selected output it is ordinary flowing text. |
| `\ParallelTitle{left title}{right title}` | One paired title, using reserved ID `pt-title` and `ParallelTitleStyle`; call once. Stores both title values in `ParallelTitleLeft` / `ParallelTitleRight`. Does not set running-title or PDF title automatically. |
| `\ParallelSection{id}{left title}{right title}` | Advances `section` exactly once, resets subsection, prints the same number on both sides, and creates one TOC/bookmark entry. Uses left wording in paired/left mode and right wording in right mode. |
| `\ParallelSubsection[role]{id}{left title}{right title}` | Advances `subsection` once and produces one TOC entry. Optional role defaults to `body`; its color applies to the heading, while role labels are not inserted. |
| `\begin{ParallelKeep} ... \end{ParallelKeep}` | Boxes several short paired units into one bounded group. No arguments or independent ID. Do not nest it or put breakable prose inside it expecting page flow. |

Atomic pairs and kept groups exceeding `\textheight-8mm` fail rather than shrink or truncate. A heading stays with the following bounded unit; a heading chain plus a unit exceeding the text height also errors. For a long paragraph choose `\ParallelParagraph[flow=breakable]` or explicit `\ParallelProse`. Use `\ParallelSetup{paragraph-flow=breakable}` to make flowing paragraphs the global default, then `[flow=keep]` for a particular short paragraph. `\ParallelText` and `\ParallelProse` always keep their explicit behavior. For lists/tables supply smaller corresponding items/rows as separate units. Layout code does not rewrite their wording.

Plain paragraphs, emphasis, inline citations, `quote`, `itemize`, `enumerate`, unnumbered displays and `tabular`/`tabularx` can be placed in a bounded side. Each list item or table row needs its own paired unit if its start must align separately. Prefer `booktabs` rules to vertical rules. Use ordinary paragraph breaks within a side only when no independent cross-side alignment is needed.

Put shared numbering and anchors in one owning command: use `ParallelEquation` for a shared numbered formula and the figure helpers below for numbered images with paired captions. Keep side bodies for their localized text and unnumbered content. Duplicating a numbered environment, identical `label`, counter mutation, float or other global side effect in both bodies can execute it twice and corrupt references. Footnotes and other page-insertion behavior need deliberate native design and actual rendered testing.

## Figures, mathematics and references

| Public command | Contract |
| --- | --- |
| `\ParallelEquation{id}{math}` | Advances `equation` once, repeats one numbered expression in explicit LTR contexts, and provides one native label. Math is trusted native mathematics without the JSON command allowlist. Put explanations in a separate paired unit, optionally kept with it. |
| `\ParallelFigure{id}{left image}{left caption}{right caption}[right image]` | Advances `figure` once. Each image uses its slot's `linewidth`; absent optional final argument reuses the left image. Right-only output chooses the right image/caption. Captions use native localized figure names, one shared counter and `ParallelCaptionStyle`. |
| `\ParallelWideFigure{id}{image}{left caption}{right caption}` | One shared image across the available text area, with paired captions below and the divider masked by `background-color`. Advances figure once; reserves `id.caption`. In a standard two-column selected edition, available width is one column, not the full page. |
| `\ParallelReference{target}{wording}` | Hyperlink containing the supplied wording plus `(p. folio)` by default. Generated folio uses `pageref*` inside LTR `\textenglish`. Change `page-reference-prefix` or use native reference commands for different grammar. |
| `\ParallelLocationRow{title}{location}` | Unpaired two-field printed row; wrapping title and right-aligned location column. No label/counter. Location width defaults to `ParallelLocationWidth=12mm`, separated by 2 mm. |
| `\ParallelLookup{id}{target}{left title}{right title}` | Paired location row with linked titles and generated local page numbers. Own ID is distinct from target. Uses `ParallelLocationRow` and `ParallelText`; no counter increment. |

Both figure helpers are bounded and must fit on the page. Native `includegraphics` paths/formats follow graphicx and the selected engine; JSON's restricted PNG/JPEG path grammar does not constrain trusted native files. Set `graphicspath` normally or stage files in the portable project. Inspect actual captions, image aspect ratios, glyphs and divider masking.

Use native `hyperref`, `\ref`, `pageref` and `href` where appropriate. Cross-document labels can use standard `xr-hyper` with an explicit prefix; compile the companion first and ship it at the referenced relative location. A printed logical folio may differ from a 1-based physical PDF destination. Verify both; do not hardcode a page number to silence unresolved references.

## Optional roles and localized diagrams

These helpers impose no subject-specific workflow or taxonomy.

| Public command/environment | Contract |
| --- | --- |
| `\ParallelDeclareRole{name}{color}{left label}{right label}` | Preamble-only role declaration. Color is an xcolor expression; labels may be empty. Built-in `body`, `concept`, `example`, `caution`, `error` all have empty labels. Redeclaration replaces that role. |
| `\ParallelNote[role]{id}{left body}{right body}` | Bounded pair styled with `ParallelNoteStyle`, prefixed on each side by its role's label/color. Role defaults to `body`; it is not a shaded box. |
| `\ParallelRoleText{role}{content}` | Applies only a declared role color to inline/native content; does not insert role wording or create an ID. Unknown roles error. |
| `\ParallelRoleColor{role}` | Expands to the declared color for use in another native style. Declare/check the role before use; this accessor does not itself validate the name. |
| `\ParallelLocalize{left content}{right content}` | Selects a value using the active package side; useful inside the same diagram input placed in both columns. It does not establish language context. Outside paired-side rendering the initial active side is left. |
| `\begin{ParallelDiagram}[TikZ options] ... \end{ParallelDiagram}` | Ordinary tikzpicture with `font=\ParallelDiagramStyle` (default 8/10 pt) followed by optional TikZ overrides. No own alignment ID or page-break support; put it inside a bounded pair. |

Built-in TikZ styles are ordinary, overridable `\tikzset` styles:
- `parallel node`: secondary-colored outline, 1 pt rounded corners, centered text, 2 pt inner padding, 26 mm text width and 9 mm minimum height
- `parallel fixed`: base node with `black!3` fill
- `parallel variable`: base node with example-colored outline
- `parallel arrow`: directed secondary-colored line, 0.45 pt
- `parallel annotation`: secondary-colored centered text, 1 pt padding

Roles/colors do not replace text labels. Diagram topology and labels come from the manuscript.

## Optional entries and margin navigation

| Public command | Contract |
| --- | --- |
| `\ParallelEntry{id}{left headword}{right headword}` | Non-numbered paired heading with `ParallelEntryStyle`. Starts entry tracking until another entry or end command. ID is a paired label. Keeps with the next bounded unit. |
| `\ParallelEntryHeaderLeft{full title}` / `\ParallelEntryHeaderRight{full title}` | One-argument formatting/content hooks, both identity by default. Redefine with `\renewcommand` to supply a shorter running head. `\ParallelEntry` captures the selected hook's expansion at entry start; the printed heading remains the original full title. Left applies in paired/left output; right in right output. Use expansion-safe/robust header content. |
| `\ParallelEndEntry` | Stops entry tracking; no arguments and no visible output. |
| `\ParallelFirstEntry` / `\ParallelLastEntry` | Header content helpers resolving the first/last active headword recorded on the current physical page. Empty without a record; need later TeX passes. Use the left language in paired/left editions and right language in right editions. |
| `\ParallelDeclareNavigation[color]{id}{slot}{label}` | Preamble-only declaration. Color defaults to `parallel.theme`; ID must be unique among navigation declarations; slot is a positive integer starting at 1. Labels are authored text. Slot uniqueness is not enforced, so avoid unintended overlap. |
| `\ParallelNavigation{id}` | Activates a declared group for following units, also setting their structural section/entry accent. Unknown ID errors. A page containing multiple groups can show multiple tabs. |
| `\ParallelEndNavigation` | Stops tab tracking and restores structural accent to `parallel.theme`. No visible output. |

Tabs are off until `tabs=true`. Slot positions are stable and independent of section numbering or language; this API does not generate an index. Tab geometry/font defaults are in [configuration](configuration.md). Lower-page overflow errors; horizontal clearance, label fit and inter-slot overlap still require visual QA. Flowing paragraphs record continuation endpoints for entry/tab page coverage. Entry headers are bounded boxes: `entry-header-width` defaults to `.46\headwidth` and `entry-header-max-lines` to 2. The first-entry helper is ragged-right; the last-entry helper is ragged-left. If measured box height plus depth exceeds the active baseline spacing times the configured line count plus 1 pt, the package errors. This is a height limit, not a truncation or exact line-count algorithm. Supply a shorter header through the hooks or explicitly redesign width/font/header height; the package never shortens the printed heading.

`entry-continuation-left` and `entry-continuation-right` default to empty. A configured cue is appended when the current physical page is later than that entry's first recorded physical page, using left wording in paired/left output and right wording in right output. Include any desired leading space in the cue. The decision uses multipass page records, not logical folios; first/last helpers can each show a cue for their own recorded entry. Rebuild until auxiliary records settle. These header hooks and keys are native-only, with no JSON field.

```tex
% Preamble:
\ParallelDeclareRole{notice}{parallel.caution}{Note:}{Remarque :}
\ParallelDeclareNavigation{route}{1}{R}
\ParallelSetup{tabs=true,
  header-left=\ParallelFirstEntry,header-right=\ParallelLastEntry}
% Body:
\ParallelNavigation{route}
\ParallelEntry{entry:route}{Route}{Itinéraire}
\ParallelNote[notice]{scope}{A short note.}{Une courte remarque.}
\ParallelEndEntry
\ParallelEndNavigation
```

## Optional cover lifecycle

| Public command | Contract |
| --- | --- |
| `\ParallelFrontCover{left title}{right title}` | Clears the page, temporarily uses one column and empty furniture, prints selected/paired cover titles, then adds a blank verso by default. Restores prior column mode. |
| `\ParallelBackCover{left title}{right title}` | Clears the page, inserts blanks according to `blank-inside-back` and `back-parity`, then prints a full-width final cover. Defaults yield a blank inside back and an even final physical page. |
| `\ParallelBlankPage` | Clears current content and inserts one empty page without body divider/tabs/furniture or a PDF page anchor. No arguments. |

Covers do not create semantic IDs or reset page numbering. The front/back helpers suspend PDF page anchors on their cover/blank pages and restore prior settings afterward. Physical back-cover parity uses shipped pages, independent of Roman numbering or a logical counter reset. Cover style/top/gap/bottom and blank policies are documented configuration. Omit all cover commands for an ordinary article.

## Public state, hooks and standard interfaces

`\ParallelLeftLanguage`, `\ParallelRightLanguage` and `\ParallelMode` expose configured selection. `\ParallelParagraphFlow` exposes the global paragraph policy (`keep` or `breakable`). `\ParallelTitleLeft` and `\ParallelTitleRight` expose the most recently supplied title. Use the public setup commands to change selection rather than modifying private state.

Every named typography/furniture/layout hook, including `ParallelHeadingFont`, is listed with its default in [configuration](configuration.md). Setup keys replace declaration hooks; use standard etoolbox `appto` to append a small change without discarding defaults. `ParallelStructureColor` is the active navigation accent; `ParallelLocationWidth` is an additional direct hook. `MarkerFont` is the Latin font family used for list markers/folios. Prefer normal fontspec, Polyglossia, geometry, enumitem, TikZ, xcolor, hyperref, fancyhdr, counters and LaTeX hooks for their own features.

## Language and safety requirements

Configure Polyglossia names and matching roman/sans font families before use. The package starts with English, Latin Modern Roman/Sans/Math. Right-to-left context does not reverse physical slot order. Use explicit native `\textenglish{...}` for LTR subruns within Hebrew/Arabic and language commands for other embedded runs. CJK requires appropriate language configuration as well as a covering font. See the complete [language reference](languages.md).

Native TeX, packages and latexmk configuration are executable inputs. `-norc` avoids loading latexmk rc files in the shown command; `-no-shell-escape` disables one execution route. Neither makes TeX a filesystem sandbox. Compile trusted sources, or isolate untrusted projects from sensitive files, credentials and unwanted network access. A generated project becomes native executable input once edited. Native image/file references can access files allowed to the process; JSON's asset-root containment is not automatically enforced on authored TeX.

After compilation, inspect actual PDF pixels and run [layout acceptance checks](acceptance.md): paired starts, flowing continuations, rows/items, fonts/glyphs, RTL shaping, image/caption placement, clipping, internal/companion references, metadata, paper geometry and both print parities. Do not claim a language combination or accessibility conformance solely because compilation succeeds.
## Independent publication metadata

`\ParallelDocumentVersion` and `\ParallelDocumentStatus` expand to independently configured token strings, empty by default. Set them with the native preamble keys `document-version` and `document-status`. No numbering scheme or status vocabulary is imposed. Display either or both through ordinary cover/header content; the package does not automatically concatenate them. These values describe the document, not the technical PDF format version.

## Unnumbered subheadings and native API compatibility

`\ParallelSubsection*[role]{id}{left}{right}` is the unnumbered variant of `\ParallelSubsection`. It retains a stable named destination, aligned heading treatment, the role style and attachment to the following unit, but does not increment the subsection counter or add a numbered contents entry. Its page can be referenced normally. The existing unstarred form remains numbered.

`\ParallelTextAPIVersion` expands to the integer `2` for this native interface. Dependent native packages may verify it before document output. This is an interface-compatibility number, separate from `document-version` publication metadata and the Python renderer API number.
