# Configure the native LaTeX design

The default design works without `\ParallelSetup`: A4, equal 18 mm side margins, 9 pt body on 10.8 pt leading, a 6 mm column gap, a thin gray divider, and an outside footer folio. Start there. Omitted settings inherit their current values; an adjustment never requires a full configuration object or editing `paralleltext.sty`.

Keep manuscript content in `content.tex`, language/font declarations in `languages.tex`, and optional presentation choices in a short `layout.tex`. Input configuration after `\usepackage{paralleltext}` and before `\begin{document}`. `\ParallelSetup{...}` and package options use the same LaTeX kernel key-value interface. Unknown keys and invalid choices are errors. Setup/profile/role/navigation declarations are preamble-only; semantic commands belong in the body. Native TeX keys intentionally accept trusted LaTeX, not untrusted text.

## Intent → configuration

| Change | Native interface |
| --- | --- |
| Paper, one-/two-sided pages, margins, binding allowance | `geometry={letterpaper,twoside,inner=24mm,outer=16mm,bindingoffset=3mm}`; ordinary `\geometry` is also supported |
| Show one language | `mode=left` or `mode=right`; `paired` is the default |
| Selected language in two ordinary newspaper columns | `mode=left,single-columns=2`; paired mode requires one standard document column |
| Languages, fonts, shaping/direction | Standard Polyglossia/fontspec declarations, plus `left-language` / `right-language` or `\ParallelLanguages` |
| Body size/leading | `body-size=10,body-leading=12` (numbers in pt); no automatic shrinking |
| Column/block/paragraph spacing | `column-gap=7mm,pair-gap=3pt,paragraph-skip=2pt,paragraph-indent=0pt` |
| Divider | `divider=true,divider-color=black!40,divider-width=.4pt,divider-style=dashed`; `divider=false` hides it |
| Heading/body palette | `theme-color`, `body-color`, `secondary-color` take xcolor expressions; semantic role colors use `\ParallelDeclareRole` |
| Heading, caption, note, entry, diagram or cover type | `title-style`, `section-style`, `subsection-style`, `caption-style`, `note-style`, `entry-style`, `diagram-style`, `cover-style` are declaration hooks |
| Shared heading family | `heading-font={\sffamily\bfseries}`; language-specific font families remain in fontspec |
| Minimum space reserved before a heading | `section-space=65pt,subsection-space=45pt` |
| Running text | `running-title={Short title}`; `header-left`, `header-right`, `footer-left`, `footer-right` |
| Running text typography | `header-style`, `footer-style`, `page-number-style` |
| Folio position | `page-number-position=footer-outer`, `footer-inner`, `footer-left`, `footer-center`, `footer-right`, the five corresponding `header-...` choices, or `none` |
| Folio notation | `page-numbering=roman` or native `\pagenumbering{roman}`; choices are `arabic`, `roman`, `Roman`, `alph`, `Alph`, `gobble` |
| Folio appearance | `page-number-format={\textendash\enspace\thepage\enspace\textendash}`; keep `\thepage` dynamic |
| Native page-style control | `page-style=empty` or ordinary `\pagestyle` / `\thispagestyle`; the package's named style is `parallel` |
| Printed reference suffix | `page-reference-prefix={p.\,}`; use native localized `\hyperref`/`\pageref` for other grammar |
| Cover appearance | `cover-top=20mm,cover-gap=10mm`, `cover-style`, `cover-bottom={...}` |
| Cover blank faces and last physical side | `blank-verso=true,blank-inside-back=true,back-parity=even`; parity also accepts `odd` or `any` |
| Navigation tabs | `tabs=true`; dimensions/style keys below, with explicit navigation declarations |

Font/leading values are numeric points; spacing/dimension values use normal TeX lengths and expressions. Explicit paragraph spacing/indentation keys are reapplied after language and minipage initialization; omitted keys preserve the normal environment defaults. A `...-style` key replaces that role’s declaration hook. To preserve its defaults and change just one property, append a declaration with the already loaded etoolbox interface, for example `\appto\ParallelTitleStyle{\color{red!60!black}}`. Keys are deliberately finite. Standard `\setlist`, `\tikzset`, `\hypersetup`, `\setmainfont`, `\setsansfont`, `\setmathfont`, `\newfontfamily`, `\colorlet`, `\definecolor`, `\fancypagestyle` and LaTeX counters remain the appropriate interfaces for their own domains. A package configuration is not another document language.

## Geometry and printing

The divider is centered on the actual text block. At shipout it reads `\oddsidemargin` or `\evensidemargin`, `\hoffset`, `\textwidth`, `\topmargin`, `\headheight`, `\headsep` and `\textheight`. Unequal inner/outer margins and `bindingoffset` therefore move the divider and columns together on both parities. `oneside` keeps the same margins; `twoside` mirrors them as documented by geometry. Do not use geometry's separate `asymmetric` option when you mean ordinary mirrored margins: that option deliberately suppresses their swap.

Choose paper sizes through geometry, including `a4paper`, `letterpaper`, `a5paper`, `legalpaper` or `paperwidth`/`paperheight`. Native authoring is not limited to the adapter's paper list. The validator rejects an impossibly narrow column; the minimum is configurable with `minimum-column-width` and is only a structural safeguard, not a readability promise. Changing paper size can still require a different figure or table design.

The page rule runs along the text block and appears only on paired body pages. `divider-style` is a TikZ path style list, so native authors can use `densely dotted`, `dash pattern=on 2pt off 1pt`, opacity, or other appropriate path options. A shared image masks the rule using `background-color=white`; set this to the actual page background if customizing it.

A two-column selected-language edition uses the standard LaTeX column mechanism. Bounded blocks fill one column. A `ParallelWideFigure` spans the current text area: in this edition that means one column. For a true page-wide figure, change to `\onecolumn` and restore `\twocolumn` at deliberate page boundaries. Covers do that automatically. Paired mode is not nestable inside `twocolumn`.

Folios use the current `\thepage`. `\pagenumbering` retains its standard behavior, including resetting the logical counter. Mirrored layout and outer/inner furniture follow the standard logical page parity; reset numbering at the appropriate recto so that it agrees with physical print order. The back-cover helper separately counts actual shipped PDF pages, so Roman folios or a body-number reset do not break its final physical parity. With both blank switches on, front reverse and inside back are genuinely blank. When deliberately choosing another blank/parity policy, validate that policy rather than using the default `--covers` check.

`parallel` is a dedicated fancyhdr style; the package does not redefine `plain` or the user's `fancy` style. Configuration initializes the default style at package load and does not reapply it over later author commands. For a custom header/folio composition use `\fancypagestyle{my-layout}{...}` and `\pagestyle{my-layout}`. Running fields and tab labels use the document’s main Polyglossia language as a stable base context at shipout, independent of the active body language. Override it with `furniture-language` when needed; use explicit `\textarabic{...}`, `\textchinese{...}` or another configured Polyglossia command for other label text. Entry-head helpers select their own headword language. Do not put a long running title and a folio in the same field without designing their spacing. Head/foot rules and header dimensions use ordinary fancyhdr/geometry commands.

A heading stays with the next bounded semantic unit; if it cannot fit, both move together with their labels. A heading plus an atomic unit that exceeds one page is rejected; use a shorter semantic unit or flowing prose. `section-space` and `subsection-space` are minimum reservations, not substitutes for that keep rule.

The nominal text margin is not the printer's safe ink margin. Tabs intentionally occupy the outer margin. Render every page after a style change, inspect both parities, and choose an explicit printer-safe clearance. The QA command accepts `--margin-mm` for a full-page horizontal ink exclusion; use a value consistent with intentional furniture. Never assume a nominal binding margin proves a minimum glyph clearance.

## Optional semantic roles, entries and navigation

A general article needs none of these commands. A learning guide, dictionary or field manual may use them selectively:

```tex
\ParallelDeclareRole{warning}{parallel.caution}{Caution:}{注意：}
\ParallelDeclareNavigation{methods}{1}{M}
\ParallelDeclareNavigation{lookup}{2}{A–Z}
\ParallelSetup{tabs=true,header-left=\ParallelFirstEntry,
  header-right=\ParallelLastEntry}
% In the document:
\ParallelNavigation{methods}
\ParallelEntry{entry:method}{Method}{方法}
\ParallelNote[warning]{note:scope}{State the valid conditions.}{说明适用条件。}
\ParallelText{explanation}{Explain the method.}{解释方法。}
\ParallelLookup{alias:method}{entry:method}{Method}{方法}
\ParallelEndEntry
\ParallelEndNavigation
```

`ParallelDeclareRole{name}{xcolor expression}{left label}{right label}` keeps semantic color and optional wording separate from topic/theme color. Built-in `body`, `concept`, `example`, `caution`, `error` roles have no imposed wording; authors supply accurate labels or declare new ones. `ParallelNote[role]{id}{left}{right}` is an ordinary paired note, not a shaded box. `ParallelRoleText{role}{content}` applies the role color inline. Colors never replace meaningful text.

`ParallelEntry` prints a non-numbered heading with a stable native label, then tracks that entry until the next entry or `ParallelEndEntry`. First/last headwords and navigation IDs are recorded at actual output positions. Flow start/end records extend the active entry across continuation pages. Headers resolve on subsequent LaTeX runs; use latexmk. Keep headwords short. Entry headwords use the selected side’s language/font mapping, while the configurable header style controls size and family; custom mixed-language running text can use ordinary Polyglossia commands. Native `xr-hyper` with a prefix and `\hyperref`/`\ref`/`\pageref` remains the cross-document reference interface. `ParallelLookup` uses a generated local page; `ParallelLocationRow{title}{location}` also supports a native companion reference and a wrap-safe location column. Its width can be changed with `\renewcommand\ParallelLocationWidth{...}`.

Navigation declarations assign stable slots independently of section numbers or language. An optional xcolor expression, such as `\ParallelDeclareNavigation[blue!60!black]{methods}{1}{M}`, gives that group its own structural accent for section/entry headings and tabs; semantic role colors remain unchanged. `ParallelNavigation{id}` selects a declared ID for following blocks; a page containing two navigation groups receives both tabs. Declare A–Z slots yourself when that ordering suits the source; the package does not invent an index or require Latin letters. Keys: `tab-inset`, `tab-width`, `tab-height`, `tab-top`, `tab-step`, `tab-rotation`, `tab-side=outer|inner|left|right`, `tab-style` (TikZ node options), and `tab-text-style` (font declarations). Positions that extend below the paper are rejected. Check label fit, slot overlap and the intended ink clearance visually.

For reusable diagrams, `ParallelDiagram` is a TikZ environment with configurable `diagram-style` and optional standard TikZ options. `parallel node`, `parallel fixed`, `parallel variable`, `parallel arrow` and `parallel annotation` are ordinary `\tikzset` styles. `\ParallelLocalize{left text}{right text}` selects labels inside a diagram input reused on both sides. Topology, equations and explanations remain manuscript data; this is not an automatic chart translator.

## Optional profiles, not separate templates

`profile=bound` adjusts only geometry to a mirrored 24 mm inner / 16 mm outer text margin plus a 3 mm binding allowance. `profile=reading` adjusts only body/paragraph spacing, hides the divider and centers the footer folio. These are examples, not universal print requirements. Apply the profile first, then sparse overrides. Define a project profile with `\ParallelDeclareProfile{name}{key list}` in the preamble.

Two directly usable configuration files are bundled: [bound-profile.tex](../assets/bound-profile.tex) and [reading-profile.tex](../assets/reading-profile.tex). Copy either beside an example, add `\input{bound-profile.tex}` or `\input{reading-profile.tex}` after its language settings, rebuild, and review. Both are exercised by the isolated configuration tests. Do not modify a manuscript paragraph to compensate for a global layout choice.

## Documented foundations

This design uses the [LaTeX kernel's package/key-value interface](https://www.latex-project.org/help/documentation/clsguide.pdf), [geometry's inner/outer and bindingoffset semantics](https://mirrors.ibiblio.org/CTAN/macros/latex/contrib/geometry/geometry.pdf), [fancyhdr's named page styles](https://mirrors.ibiblio.org/CTAN/macros/latex/contrib/fancyhdr/fancyhdr.pdf), and the existing fontspec/Polyglossia and TikZ interfaces. The JSON adapter supports a deliberately smaller validated data-only subset; it emits these same native settings.
