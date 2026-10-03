# Complete learning example

[Three concepts](three-concepts/) is an original English / Chinese teaching source developed into explanatory notes and a keyword-and-concept Quick Reference:

- [Teaching source](three-concepts/source.md) and [source/coverage map](three-concepts/source-map.json)
- [Notes PDF](three-concepts/notes.pdf) and [editable notes](three-concepts/notes-content.tex)
- [Quick Reference PDF](three-concepts/quick-reference.pdf) and [editable lookup entries](three-concepts/quick-content.tex)
- [Coverage and review limits](three-concepts/coverage-review.md)

Read the source, one complete notes concept and its lookup routes before adapting the workflow. The example teaches average speed, rectangle area and stack behaviour; these are examples, not a required subject list or writing template.

Copy the complete `three-concepts/` folder to a fresh working directory and run `make` there. Both PDFs, all `.tex` files and source records remain together, with no separate notes/Quick subdirectories. Editable figures are TikZ code inside the manuscripts. The [project README](three-concepts/README.md) also gives commands without Make.

Native builds require XeLaTeX, latexmk, `xr-hyper` and the [documented fonts/packages](../references/languages.md). They do not need Python, another skill or a repository checkout. Build notes first so native labels generate the Quick Reference's section/page pointers; keep both PDFs together for relative links. Some browser PDF viewers restrict cross-document navigation.

For structured learning input, see [rendering](../references/rendering.md). For content and page review, see [review and delivery](../references/review-release.md). Do not mistake compilation for source coverage, translation review or usable printed lookup routes.
