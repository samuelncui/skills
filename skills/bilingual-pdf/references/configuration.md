# Native configuration reference

The default design works without `\ParallelSetup`: A4, 18 mm inner/outer margins, 9 pt body on 10.8 pt leading, a 6 mm column gap, a 0.3 pt gray divider and an outside footer folio. All keys below are supported by both package options and `\ParallelSetup{...}`. The latter is preamble-only. Unknown keys and invalid enumerated choices are errors.

Configuration is sparse and ordered. Omitted values retain the current value, including prior profile changes; an empty setup does not reset anything. Apply a profile first and then explicit overrides. Trusted native TeX declarations are allowed in style/content keys. JSON exposes a smaller data-only subset in [input.md](input.md) and [the schema](../schemas/document.schema.json).

Keep language/font choices in `languages.tex`, optional presentation in `layout.tex`, and paired content in the manuscript. Neither a profile nor a page size changes supplied wording.

## Selection, geometry and spacing keys

| Key | Accepted value | Default and behavior |
| --- | --- | --- |
| `profile` | Declared profile name | No preset. Built-ins: `bound`, `reading`. Native `profile=article` is not defined; JSON `article` means omit a preset. |
| `geometry` | Braced geometry key list | `a4paper,inner=18mm,outer=18mm,top=17mm,bottom=14mm,headsep=3mm,footskip=7mm`. One/two-sided behavior otherwise comes from the document class. |
| `mode` | `paired`, `left`, `right` | `paired`; physical side selection, independent of language direction. |
| `left-language`, `right-language` | Declared Polyglossia name | Both `english`; same state as `\ParallelLanguages`. Do not declare languages or fonts by setting these keys alone. |
| `single-columns` | `1`, `2` | `1`. `2` starts standard two-column layout at document start and requires left/right mode. |
| `paragraph-flow` | `keep`, `breakable` | `keep`. Global default for `\ParallelParagraph`; its local flow option can override it. Explicit `\ParallelText`/`\ParallelProse` retain their own behavior. |
| `body-size` | Positive number in points | `9`; native values are not restricted to JSON's 9–14 range. Does not automatically update leading. |
| `body-leading` | Number in points, at least body-size | `10.8`. Set both size and leading when changing native body typography. |
| `column-gap` | Nonnegative TeX length | `6mm`; gap between paired slots, also standard column separation at document start. |
| `pair-gap` | TeX length | `2.5pt`; extra vertical separation after ordinary paired units. |
| `paragraph-skip` | TeX length/glue | Package initially sets `\parskip=2pt`; absent override lets normal language/minipage initialization apply. Explicit value is reapplied inside each side. |
| `paragraph-indent` | TeX length | Package initially sets `\parindent=0pt`; explicit value is reapplied after language/minipage initialization. |
| `paragraph-emergency-stretch` | Nonnegative TeX length | `\linewidth`; `\ParallelParagraphEmergencyStretch`. Evaluated in the current physical column after selecting the paragraph font. Gives TeX its final line-breaking fallback without changing text, font size or column width. |
| `minimum-column-width` | TeX length | `20mm`; structural guard, not a readability certificate. |
| `section-space` | TeX length | `65pt`; minimum reservation before section heading. |
| `subsection-space` | TeX length | `45pt`; minimum reservation for subsection/entry headings. |

`\ParallelParagraph[flow=default]{id}{left}{right}` uses the global choice. `flow=keep` forbids a page break inside that paragraph pair, while `flow=breakable` lets each side continue naturally across pages. The next pair starts after both have finished. Keeping an oversized paragraph does not authorize shrinking or truncation: the build fails and the caller must choose another layout policy or supply smaller units.

Geometry validates actual width/height, not just key syntax. Paired mode cannot run inside standard twocolumn; text height must be at least 30 mm. An atomic pair/group must fit inside the text area, including its safety allowance. A heading stays with the next bounded unit; oversized heading/unit combinations error.

Use geometry's `inner`/`outer`/`bindingoffset` for bound work. `twoside` mirrors inner/outer margins; `asymmetric` deliberately suppresses that swap and should not be used as a synonym. Custom `paperwidth`/`paperheight` are supported natively. The divider follows live text-block geometry on each parity, including offset and binding allowance.

## Typography and declaration hooks

Each style key replaces the corresponding public macro with a declaration list. Sizes below are font size/baseline spacing in pt. Defaults that refer to `\ParallelHeadingFont` keep that hook dynamic.

| Key | Public hook | Default |
| --- | --- | --- |
| `heading-font` | `\ParallelHeadingFont` | `\sffamily\bfseries\hyphenpenalty=10000\exhyphenpenalty=10000` |
| `title-style` | `\ParallelTitleStyle` | Heading font, theme color, 17/20.4 |
| `section-style` | `\ParallelSectionStyle` | Heading font, active structure color, 13/15.6 |
| `subsection-style` | `\ParallelSubsectionStyle` | Heading font, 9.5/11.4; subsection command additionally applies its role color |
| `caption-style` | `\ParallelCaptionStyle` | Secondary color; body size inherited |
| `cover-style` | `\ParallelCoverStyle` | Heading font, theme color, 24/30 |
| `note-style` | `\ParallelNoteStyle` | Secondary color; body size inherited |
| `entry-style` | `\ParallelEntryStyle` | Heading font, active structure color, 11/13.2 |
| `semantic-marker-style` | `\ParallelSemanticMarkerStyle` | Heading font for semantic labels |
| `semantic-title-style` | `\ParallelSemanticTitleStyle` | Bold body-colored semantic titles |
| `semantic-destination-prefix` | `\ParallelSemanticDestinationPrefix` | Arrow and space before a choice destination |
| `semantic-destination-indent` | `\ParallelSemanticDestinationIndent` | `1em` choice-destination inset |
| `diagram-style` | `\ParallelDiagramStyle` | 8/10 |
| `header-style` | `\ParallelHeaderStyle` | Sans, 7/8 |
| `footer-style` | `\ParallelFooterStyle` | Sans, 7/8 |
| `page-number-style` | `\ParallelPageNumberStyle` | `\MarkerFont`, 8/9.6 |
| `tab-text-style` | `\ParallelTabTextStyle` | Sans bold, 6/7 |

To retain defaults and append one property, use the loaded etoolbox interface:

```tex
\appto\ParallelTitleStyle{\color{red!60!black}}
\ParallelSetup{body-size=10,body-leading=12,column-gap=7mm}
```

Styles execute within the side's language context. Define the relevant roman and sans font families through fontspec/Polyglossia, including bold faces as needed. Default base families are Latin Modern Roman, Latin Modern Sans and Latin Modern Math; `\MarkerFont` is Latin Modern Roman. See [languages.md](languages.md).

## Palette and divider

| Key | Accepted value | Default |
| --- | --- | --- |
| `theme-color` | xcolor expression | `parallel.theme`, HTML `4C6174`; updates that named color |
| `body-color` | xcolor expression | Body text initially `black`; setting updates body text and `parallel.body` |
| `secondary-color` | xcolor expression | `parallel.secondary`, HTML `50555A` |
| `divider` | Boolean | `true`; only rendered on paired body pages |
| `divider-color` | xcolor expression | `black!35` |
| `divider-width` | Positive TeX length | `.3pt`; must remain positive even if the divider is disabled |
| `divider-style` | TikZ path style/options | `solid`; native trusted lists can include dashes, opacity and other path options |
| `background-color` | xcolor expression | `white`; mask behind shared images, not a whole-page background painter |

Built-in role colors are `parallel.body=161616`, `parallel.concept=0B4F8A`, `parallel.example=006B5B`, `parallel.caution=8A5A00` and `parallel.error=A4262C` (HTML). Role declarations, not theme-color, control role wording/color. `\ParallelStructureColor` initially names `parallel.theme`; an active navigation group replaces its accent until `\ParallelEndNavigation`.

## Running furniture and folios

| Key | Accepted value | Default and behavior |
| --- | --- | --- |
| `furniture-language` | Configured Polyglossia name | `\mainlanguagename`; stable language context at shipout |
| `entry-header-width` | Native TeX length | `.46\headwidth`; bounded box width for first/last entry headers; public hook `\ParallelEntryHeaderWidth` |
| `entry-header-max-lines` | Positive integer | `2`; height budget is active baseline spacing × this value + 1 pt; public hook `\ParallelEntryHeaderMaxLines` |
| `entry-continuation-left` | Trusted native text | Empty; append on later physical pages of a tracked entry in paired/left output; public hook `\ParallelEntryContinuationLeft` |
| `entry-continuation-right` | Trusted native text | Empty; corresponding cue for right output; public hook `\ParallelEntryContinuationRight` |
| `running-title` | Trusted native text | Empty; `\ParallelTitle` does not fill it automatically |
| `header-left` | Trusted native text | `\ParallelRunningTitle` |
| `header-right` | Trusted native text | Empty |
| `footer-left`, `footer-right` | Trusted native text | Both empty |
| `page-style` | Existing native style name | `parallel`; calls `\pagestyle` immediately |
| `page-number-position` | Position listed below | `footer-outer` |
| `page-numbering` | `arabic`, `roman`, `Roman`, `alph`, `Alph`, `gobble` | Ordinary class numbering (arabic in the examples). Calls `\pagenumbering`, including its counter reset. |
| `page-number-format` | Trusted native content | `\thepage`; keep the live page macro rather than a literal number |
| `page-reference-prefix` | Trusted native text | `p.\,` inside the LTR suffix produced by `\ParallelReference` |

Position choices are `footer-outer`, `footer-inner`, `footer-left`, `footer-center`, `footer-right`, the corresponding five `header-...` choices, and `none`. Outer/inner follow logical page parity for twoside documents; in oneside, outer is right and inner is left.

All matching public content hooks are named by converting the key to CamelCase with `Parallel` prefix, for example `\ParallelHeaderLeft` and `\ParallelPageNumberFormat`. Font hooks are listed above. `\ParallelFirstEntry`/`\ParallelLastEntry` can be used as header content and select their own headword language.

The package defines a dedicated fancyhdr style `parallel`; it does not redefine `plain` or the user's `fancy` style. Head/foot rules default to zero; headheight starts at 25 pt. Ordinary `\fancypagestyle`, `\pagestyle`, `\thispagestyle`, geometry dimensions and LaTeX counters remain available. The package does not overwrite a later author-selected page style at document start.

Entry header title hooks \ParallelEntryHeaderLeft{full title} and \ParallelEntryHeaderRight{full title} are identity functions by default. Redefine them with \renewcommand when the running head needs different wording. The selected hook is expanded/captured when \ParallelEntry begins; the printed title stays unchanged. Keep captured content expansion-safe/robust. First/last entry headers are ragged-right/ragged-left respectively and use the bounded width/height above. Over-height content errors rather than clipping or truncating; increase geometry/header height coherently or supply a shorter header. Continuation cues use multipass physical entry-page records; include a leading space in the cue if wanted. These are native-only interfaces.

A folio and running text placed in the same field are concatenated; design their spacing explicitly. Use configured `\texthebrew`, `\textarabic` or other language commands for mixed-language furniture. Reset logical numbering at a physical recto when parity should agree with duplex order. Back-cover parity is separately based on physical shipped pages.

## Cover keys

| Key | Value | Default and effect |
| --- | --- | --- |
| `cover-top` | TeX length | `20mm` before cover titles |
| `cover-gap` | TeX length | `10mm` between two cover titles in paired mode |
| `cover-bottom` | Trusted native content | Empty; printed after flexible vertical space |
| `blank-verso` | Boolean | `true`; blank reverse after front cover |
| `blank-inside-back` | Boolean | `true`; blank inside-back face |
| `back-parity` | `even`, `odd`, `any` | `even`; physical final cover page |

These keys configure cover commands but do not emit covers. Front/back helpers temporarily enter one-column mode and restore it afterward. Their defaults produce genuinely blank inside faces and an even physical final page. When changing blank/parity policy, review that policy explicitly rather than using the default `validate --covers` assumption.

## Navigation tab keys

| Key | Value | Default |
| --- | --- | --- |
| `tabs` | Boolean | `false` |
| `tab-inset` | Nonnegative TeX length | `6mm` from selected paper edge |
| `tab-width` | Positive TeX length | `5mm` minimum node width |
| `tab-height` | Positive TeX length | `12mm` minimum node height |
| `tab-top` | TeX length | `30mm` to slot 1 |
| `tab-step` | Positive TeX length | `16mm` between slot starts |
| `tab-style` | TikZ node options | `line width=.5pt,inner sep=.25mm` |
| `tab-text-style` | Font declarations | Sans bold 6/7 pt |
| `tab-rotation` | graphicx rotation angle | `0` degrees |
| `tab-side` | `outer`, `inner`, `left`, `right` | `outer` |

Each tab uses its navigation group's color for outline and an 8% tint for fill before applying tab-style. Start position is tab-top + (slot − 1) × tab-step. A bottom edge below paper height errors. Duplicate slots, top/horizontal overflow, text exceeding minimum node size and overlap are not comprehensively validated; inspect the actual page.

## Profiles and direct hooks

`\ParallelDeclareProfile{name}{key list}` creates a preamble-only sparse preset. Built-ins:
- `bound`: `geometry={twoside,inner=24mm,outer=16mm,bindingoffset=3mm}`
- `reading`: `body-size=11,body-leading=14,pair-gap=5pt,paragraph-skip=3pt,divider=false,page-number-position=footer-center`

The bundled [bound-profile.tex](../assets/bound-profile.tex) and [reading-profile.tex](../assets/reading-profile.tex) are richer worked configurations, not byte-for-byte aliases for the built-in profiles. The bound file additionally styles the divider/folio and enables tabs; the reading file additionally selects Letter/oneside geometry, black theme, larger title and a header folio. Copy one beside the manuscript and input it after language setup if those choices fit the requested layout.

Most public storage hooks correspond directly to the listed keys, such as `\ParallelParagraphFlow`, `\ParallelBodySize`, `\ParallelBodyLeading`, `\ParallelColumnGap`, `\ParallelMinimumColumnWidth`, `\ParallelDividerColor`, `\ParallelDividerWidth`, `\ParallelDividerStyle`, `\ParallelBackgroundColor`, `\ParallelSectionSpace`, `\ParallelSubsectionSpace`, `\ParallelCoverTop`, `\ParallelCoverGap`, `\ParallelCoverBottom`, `\ParallelBackParity`, `\ParallelSingleColumns` and the `\ParallelTab...` macros. Prefer setup keys; internal booleans, dimensions and measurement records are not extension APIs.

For completeness, the remaining key-backed storage macros are \ParallelBodyColor, \ParallelFurnitureLanguage, \ParallelHeaderRight, \ParallelFooterLeft, \ParallelFooterRight, \ParallelPageStyle, \ParallelPageNumberPosition, \ParallelPageReferencePrefix, \ParallelTabInset, \ParallelTabWidth, \ParallelTabHeight, \ParallelTabTop, \ParallelTabStep, \ParallelTabStyle, \ParallelTabRotation and \ParallelTabSide. Their accepted values and defaults are the corresponding rows above. \ParallelPageNumberFormat is a formatting hook; changing it is distinct from changing the native page-numbering counter representation.

Additional direct public hooks are `\ParallelLocationWidth` (12 mm printed-location column), `\ParallelStructureColor` (active navigation accent) and `\MarkerFont` (Latin marker family). Standard `\setlist`, `\tikzset`, `\hypersetup`, `\definecolor`/`\colorlet`, fontspec and Polyglossia remain the proper APIs for their own domains. The role/entry/navigation/diagram commands are fully specified in [latex.md](latex.md).

## Print and visual verification

The nominal text margin is not a printer-safe ink margin. Tabs intentionally occupy margins; choose a printer-safe clearance and inspect both parities. A shared image masks the divider using background-color, so coordinate it with any custom page background. In selected two-column output a shared figure fills one column; use deliberate `\onecolumn`/`\twocolumn` page transitions for a page-wide figure.

After global layout changes, render actual pages and check alignment, line/page continuations, glyphs, references, clipping, headers/folios, tab overlap and cover parity. QA `--margin-mm` is a horizontal ink exclusion and must reflect intentional furniture. Keep bounded table rows individually intact; row-by-row pagination does not make one oversized row breakable. Configuration acceptance and compiler success do not replace pixel review.
## Independent document version and status

Native `document-version` and `document-status` store separate optional token strings in `\ParallelDocumentVersion` and `\ParallelDocumentStatus`. Both default to empty. The package imposes no version format or status vocabulary and does not automatically join or display them. A project can populate them from its build metadata and use a cover/header hook, for example `\ParallelSetup{document-version={1.2},document-status={Review},cover-bottom={\ParallelDocumentVersion\quad\ParallelDocumentStatus}}`. These are presentation metadata, not the PDF file-format version, and they are outside the JSON layout subset.

The divider follows the center of the live text block, not an independently fixed paper coordinate. With symmetric physical margins and no asymmetric binding offset, text-block and paper centers coincide. With asymmetric mirrored binding geometry, the text-block center and divider can shift between odd and even pages. There is no separate paper-center divider mode; choose symmetric paired-page geometry when a fixed physical middle is required.

Emergency stretch is used only when ordinary paragraph line-breaking cannot meet its tolerance. The width-relative default can admit a legal short ragged line even when a CJK paragraph contains a long Latin identifier; it is not a fixed em threshold tied to one paper or binding width. Normal line-breaking passes still run first. It does not split an intrinsically over-wide token, suppress overflow diagnostics or change the acceptance margin. This key is native configuration; structured documents inherit the same canonical default.

Native cell-content helpers `\ParallelSemanticLabel{role}{label}`, `\ParallelSemanticHeading{role}{label}{title}`, `\ParallelSemanticChoice{role}{ordinal}{condition}{destination}` and `\ParallelSemanticField{role}{label}{text}` use declared semantic roles and these hooks. Place them inside the ordinary paragraph/entry lifecycle; they do not establish layout or graph validity.
