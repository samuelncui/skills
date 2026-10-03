# Three concepts: notes and Quick Reference

A beginner English / Chinese learning set covering average speed, rectangle area and stack behaviour.

- [Notes PDF](notes.pdf)
- [Quick Reference PDF](quick-reference.pdf)
- [Original teaching source](source.md) and [claim-to-notes map](source-map.json)

Keep both PDFs in this directory so relative notes links work. Some PDF viewers restrict opening other local files.

## Edit and build

Copy the complete folder. Edit `notes-content.tex` and `quick-content.tex`; language and font settings are in `languages.tex`. Original editable diagrams are included as TikZ in the manuscripts.

```sh
make
```

Or run, in order:

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape notes.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape quick-reference.tex
```

Outputs are `notes.pdf` and `quick-reference.pdf` beside these sources. The second build imports `notes.aux` using `xr-hyper`; section and page pointers update automatically. Neither build needs Python or another repository directory. The `notes-` prefix is reserved for imported labels.

Install a coherent XeLaTeX distribution with latexmk, Polyglossia, paracol and xr-hyper, plus Latin Modern and Noto CJK fonts. See [language and font prerequisites](../../references/languages.md). For one language, change `ParallelSelect` in `languages.tex` to `left` or `right`, rebuild both documents and review that edition separately.

## Scope and review

The original source has stable P1–P3 locators. The map distinguishes supplied claims, derived explanations, original diagrams and retrieval terms. [Coverage review](coverage-review.md) records the review scope. Source gaps, including uncertainty methods and stack implementation choices, remain explicit. This is a short learning aid, not a completeness or certification claim.

[MIT license](LICENSE). Native TeX is executable input; disabled shell escape is not a filesystem sandbox.
