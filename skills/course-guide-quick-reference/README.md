# Learning Notes and Quick Reference

Turn authorized learning sources into two complementary tools: explanatory notes that teach and a keyword-and-concept Quick Reference that helps a reader retrieve the right idea. This skill owns the source-to-teaching workflow and collection adapter. Rendering uses the installed `bilingual-pdf` dependency.

Read [SKILL.md](SKILL.md) for the agent workflow, [authoring](references/authoring.md) for source mapping and concept design, and [review and delivery](references/review-release.md) for coverage, language and retrieval checks. There is no mandatory course count, subject list or Meaning/Rule/Checks template.

## Required dependency

Install both `bilingual-pdf` and this skill using your host's supported skill installer, or copy both complete skill directories to supported locations. Discover `bilingual-pdf` through the host's installed-skill listing and use that actual installation directory. The skills may be installed anywhere; do not infer a sibling path or use a repository checkout as a runtime requirement.

For the commands below, set the discovered absolute path:

```sh
export BILINGUAL_PDF_SKILL="/path/reported/by/host/bilingual-pdf"
```

The native Makefile uses `$BILINGUAL_PDF_SKILL/assets/paralleltext.sty`. The collection command accepts `--bilingual-skill "$BILINGUAL_PDF_SKILL"`, or reads `BILINGUAL_PDF_SKILL` when the option is omitted. If the dependency is missing or invalid, resolve it before building. No helper downloads or installs it automatically.

Read the dependency's `README.md` and `references/languages.md` for TeX/fonts and Python prerequisites. Its `references/latex.md`, `references/input.md`, `references/configuration.md` and `references/acceptance.md` are the canonical native API, structured schema, complete layout reference and PDF acceptance contract. Resolve those files under the discovered installed directory. The course skill does not carry a second renderer, template, package or copy of those references.

## Complete learning example

The [three-concept example](examples/) develops an original teaching source into English / Chinese notes and a keyword-and-concept Quick Reference:

- [Teaching source](examples/source.md) and [source/coverage map](examples/source-map.json)
- [Notes PDF](examples/notes.pdf) and [editable notes](examples/notes-content.tex)
- [Quick Reference PDF](examples/quick-reference.pdf) and [editable lookup entries](examples/quick-content.tex)
- [Coverage and review limits](examples/coverage-review.md)

Read the source, one complete notes concept and its lookup routes before adapting the workflow. Average speed, rectangle area and stack behaviour are examples, not required topics. Editable figures are TikZ code in the manuscripts. Both PDFs, editable files and source records remain together, without separate notes/Quick subdirectories.

## Native LaTeX

Copy the complete `examples/` folder to a fresh working directory. Preserve the user's original source, replace `notes-content.tex` and `quick-content.tex` with authored content, and adjust `languages.tex` for the requested language pair or selected side. Build from that copied directory:

```sh
make BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL"
```

The Makefile builds notes before the Quick Reference. Without Make, expose the installed package and run in that order:

```sh
export TEXINPUTS="$BILINGUAL_PDF_SKILL/assets//:${TEXINPUTS:-}"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape notes.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape quick-reference.tex
```

These native builds need XeLaTeX, latexmk, `xr-hyper` and the dependency's documented fonts/packages. They do not need Python or a repository checkout. Native `xr-hyper` / `hyperref` imports generate the Quick Reference's notes section/page pointers. Never type page numbers by hand. Rebuild both PDFs after changing notes, and keep `notes.pdf` and `quick-reference.pdf` together for relative cross-document links. Some browser PDF viewers restrict those links.

For a portable editable handoff, copy the dependency's `assets/paralleltext.sty` beside the `.tex` files, include required images and licenses, and supply the direct latexmk commands above. The recipient can then compile with the package locally rather than resolving your skill installation. This delivery copy is separate from ownership of the installed renderer.

## Structured collection

From this installed course skill's directory:

```sh
python3 scripts/course_documents.py collection.json --bilingual-skill "$BILINGUAL_PDF_SKILL" --output /path/to/new-bundle
```

The environment variable may replace the option. Add `--mode left` or `--mode right` for one language. Choose a new output directory; existing work is not silently overwritten. The adapter builds notes, derives aliases/keyword lookup and generated notes pointers, and passes content through the dependency's renderer. It emits flat `notes.pdf` and `quick-reference.pdf` with named editable sources, the package, staged images and transformation records.

Add `--asset-root path/to/assets` when collection images are stored outside the collection JSON's parent directory. Guide and Quick blocks both accept localized image pairs; shared figures accept one scalar image. The dependency's bounded resolver rejects absolute image paths, traversal and symlink escapes.

The [rendering reference](references/rendering.md) contains the collection contract, a minimal JSON example and exact validation commands. Ordinary paragraph, list, figure, table and equation fields follow the installed dependency's `references/input.md`. Its native and JSON routes share the same layout; the course adapter does not impose a fixed writing structure or create another design engine.

## Review, safety and licensing

Source coverage, faithful explanation, usable lookup and generated links are distinct checks. Read both languages independently, reconcile the pair and inspect every final page. Report limitations and actual review depth; compiling is not evidence that material is exam-complete, translated accurately or independently audited.

Native TeX and latexmk configuration are executable. Disabling shell escape does not isolate file access. Keep private source material, identities, source links and operational logs out of published examples; external translation and publication need applicable authorization. The tools do not install dependencies or fetch course material.

Deliver the notes, Quick Reference, source map and portable editable project, plus structured input when used. Retain the skill-level [MIT license](LICENSE) when redistributing the original example content/code, and retain the dependency's license for its package. Other dependencies and any source figures retain their own rights.

Keep both installed skills on the same repository revision. The course adapter requires renderer API 1 and reports an actionable error for an incompatible dependency before creating its output.
