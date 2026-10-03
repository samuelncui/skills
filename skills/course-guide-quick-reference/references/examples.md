# Complete learning example

[Three concepts](../examples/) is an original English / Chinese teaching source developed into explanatory notes and a keyword-and-concept Quick Reference:

- [Teaching source](../examples/source.md) and [source/coverage map](../examples/source-map.json)
- [Notes PDF](../examples/notes.pdf) and [editable notes](../examples/notes-content.tex)
- [Quick Reference PDF](../examples/quick-reference.pdf) and [editable lookup entries](../examples/quick-content.tex)
- [Coverage and review limits](../examples/coverage-review.md)

Read the source, one complete notes concept and its lookup routes before adapting the workflow. The example teaches average speed, rectangle area and stack behaviour; these are examples, not a required subject list or writing template.

Copy the complete `examples/` folder to a fresh working directory and run `make` there. Both PDFs, all `.tex` files and source records remain together, with no separate notes/Quick subdirectories. Editable figures are TikZ code inside the manuscripts. Without Make, run `latexmk -xelatex notes.tex`, then `latexmk -xelatex quick-reference.tex`. Retain the skill-level [MIT license](../LICENSE) when redistributing copied original content/code.

Native builds require XeLaTeX, latexmk, `xr-hyper` and the [documented fonts/packages](languages.md). They do not need Python, another skill or a repository checkout. Build notes first so native labels generate the Quick Reference's section/page pointers; keep both PDFs together for relative links. Some browser PDF viewers restrict cross-document navigation.

For structured learning input, see [rendering](rendering.md). For content and page review, see [review and delivery](review-release.md). Do not mistake compilation for source coverage, translation review or usable printed lookup routes.
