# Native LaTeX authoring

Use the complete starter project named by the skill entrypoint (`assets/starter/` for a general article, `assets/learning-starter/` for notes and Quick Reference). Each document uses the standard `article` class, `\usepackage{paralleltext}`, a language configuration, and `\input{content.tex}`. Content supplies meaning; the package owns paired placement, typography and optional print furniture. No custom class or Python body generator is required.

## Small public API

```tex
\ParallelLanguages{english}{chinese} % Polyglossia language names
\ParallelSelect{paired}             % paired, left or right
\ParallelTitle{A familiar street}{熟悉的街道}
\ParallelSection{route}{Choose a route}{选择路线}
\ParallelSubsection[example]{pause}{An unhurried stop}{从容停留}
\ParallelText{first-stop}
  {An ordinary paragraph with \emph{emphasis} and $x+y$.}
  {一段普通正文，可以包含\emph{强调}以及公式 $x+y$。}
\ParallelFigure{route-image}{route.png}{A schematic route.}{路线示意图。}
\ParallelWideFigure{shared-photo}{path.png}{A shared photograph.}{共用照片。}
\ParallelProse{long-observation}
  {A long ordinary paragraph may continue across pages here.}
  {这里的长段落可以自然跨页。}
\ParallelText{back-link}
  {See \ParallelReference{route}{the route discussion}.}
  {参见\ParallelReference{route}{路线说明}。}
```

- `ParallelText` accepts ordinary, bounded LaTeX bodies. It anchors the supplied ID; `\pageref{first-stop}` and `\hyperref[first-stop]{...}` work normally.
- Sections/subsections increment their native LaTeX counter once, then display its value in both languages. They write one source-title table-of-contents/bookmark entry per logical heading. `\ref{route}` is the section number. `ParallelSubsection` optionally selects `body`, `concept`, `example`, `caution` or `error` color; put an accurate textual label in the heading so meaning never depends on color alone.
- `\ParallelEquation{eq:balance}{a+b=c}` advances `equation` once, repeats the expression and its number in an explicit left-to-right math context, and supplies one standard label. Keep localized explanatory prose in a separate paired unit. Use it for shared numbered mathematics; `\ref{eq:balance}` returns that number.
- `ParallelFigure` repeats the same image once in each column with localized captions; it increments `figure` once and creates a standard label. `ParallelWideFigure` instead prints the image once across the full text width, masks the center rule behind the image, and keeps two localized captions below it. The next paired unit resumes the normal columns. It also reserves `<id>.caption` for the caption pair. For genuinely different localized images, put ordinary `\includegraphics` and captions in a `ParallelText` unit instead.
- `ParallelReference` is a convenience around native `\hyperref` and `\pageref`; it isolates its Latin page suffix in RTL text. Authors may use localized native reference wording instead.
- `\begin{ParallelKeep} ... \end{ParallelKeep}` keeps several short paired units together, for example an equation and its explanation.
- IDs are unique, stable labels. The package rejects duplicate paired IDs. `pt-title` is reserved for `ParallelTitle`; automatic measurement labels use the reserved `pt-internal:` namespace. Public IDs beginning with that prefix are rejected; labels such as `foo` and `foo-L` otherwise remain distinct.

## Ordinary LaTeX inside each side

Do not duplicate a numbered `equation` environment or the same manual `\label` in both sides: ordinary LaTeX would increment that counter twice or define the label twice. Use the shared equation helper or unnumbered displays.

Paragraphs, `itemize`, `enumerate`, `quote`, display mathematics, `tabular`/`tabularx`, inline citations, and native labels/references work inside the side's language context. Keep individual list items in separate paired units when each item needs its own alignment boundary. `booktabs` rules work in tables; do not use vertical rules by default.

`ParallelText` measures two top-aligned minipages once, then moves them as a unit. Each physical column slot retains its configured width even when an indented quote/list produces a narrower natural box. An atomic unit may not exceed a page: use meaningful shorter units for lists/tables, or choose flowing prose rather than shrinking or dropping content.

`ParallelProse{id}{left}{right}` uses the standard `paracol` package. Both versions start at the same vertical position, each can continue across page boundaries, and the next paired unit begins below the longer version. This is actual paragraph flow: authors do not insert manual page breaks or split the paragraph into arbitrary fragments. Unequal translations can end on different pages and leave whitespace below the shorter version. Individual lines and within-paragraph page breaks are not synchronized. Use ordinary prose, lists or quotes inside each side; do not nest the paired helpers inside a flowing body. Standard labels and links still work. The `left`/`right` edition flows as normal full-width prose.

Floats (`figure`, `table`), `longtable`, cross-column footnotes and raw `verbatim` are not supported directly inside these paired macro arguments. Use the figure helper, bounded ordinary tables, inline `\texttt` or an externally prepared listing, and explicit paired notes. Choose the flow helper explicitly when the correspondence contract permits different continuation lengths.

## Fonts, language and design

Use Polyglossia/fontspec normally in `languages.tex`; see [languages.md](languages.md). Language switches restore the appropriate line-breaking rules; the package does not leave Chinese rules active for Latin or Arabic text or disable all hyphenation. A modest emergency stretch permits ordinary narrow-column line breaking without reducing the font size. Defaults reproduce the compact paired design: 9 pt body, 10.8 pt leading, A4, equal 18 mm side margins, a 6 mm column gap, and a physical center divider. These are nominal geometry, not a guarantee about a printer's ink-safe area.

Document-level changes belong in configuration, for example `\geometry{letterpaper,inner=18mm,outer=18mm}` or `\renewcommand\ParallelBodySize{10}` and the matching leading. Keep equal side margins for a fixed page-center divider. An asymmetric mirrored binding profile is not implemented by this package; it requires adapting the divider and physical-slot checks as well as geometry. Choose it explicitly and validate both parities rather than assuming the defaults suit every binding. Do not place per-paragraph font/spacing tweaks in the manuscript to hide layout failures. `\ParallelRunningTitle` is optional and should be short. PDF author defaults to empty; choose public metadata deliberately.

## Optional booklets

Call `\ParallelFrontCover{left title}{right title}` before the body and `\ParallelBackCover{left title}{right title}` after it. The first inner face and final inside-back face remain blank; physical page numbering does not reset. The back cover is the final even physical page; inspect actual rendered blank faces and page parity before duplex printing. Covers are full-width and are the intentional exception to paired body text. Omit them for short articles.

## Build and trust boundary

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape main.tex
```

LaTeX source, packages and `.latexmkrc` files are executable inputs. `-no-shell-escape` only disables one execution route; it does not prevent TeX from reading or writing accessible files, nor does it sandbox latexmk configuration. Review trusted projects or compile untrusted projects in an isolated environment without sensitive files or credentials. The JSON adapter escapes text and allowlists mathematics, but a later hand-edited `.tex` file must be treated as native executable source.

## Design references

The package separates manuscript content from presentation using the [standard LaTeX package model](https://www.latex-project.org/help/documentation/clsguide.pdf). Breakable columns use [paracol’s documented synchronization and page handling](https://ctan.org/pkg/paracol); multipass builds use [latexmk](https://ctan.org/pkg/latexmk).
