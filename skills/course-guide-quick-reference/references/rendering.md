# Executable rendering routes

## Native LaTeX notes and Quick Reference

Copy the complete `assets/learning-starter/` directory to a new project. Read its small example, then replace `notes-content.tex` and `quick-content.tex` with authored material from the source map. `languages.tex` configures the language pair and `ParallelSelect` mode. The shared package is bundled, so this project builds without a sibling skill or Python body generation.

From that copied directory:

```sh
make
```

Without Make, run the two commands in order:

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape notes.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape quick-reference.tex
```

Expected PDFs: `notes.pdf` and `quick-reference.pdf`. Reserve the `notes-` label prefix for imported notes labels; use a distinct local prefix such as `qr-` for Quick IDs. LaTeX reports collisions as multiply defined references. The Quick imports `notes.aux` with native `xr-hyper` and uses relative PDF links to `notes.pdf`. It combines keyword/alias rows, canonical concept entries and generated notes section/page pointers. Keep the two PDFs together when distributing them. Rebuild both after changing notes; do not hand-edit page numbers.

Use normal LaTeX within the paired commands. The bundled [native API](latex.md) explains headings, text, figures, groups and references; [language setup](languages.md) covers fonts and direction. Native compilation needs XeLaTeX, latexmk and the documented packages/fonts; `xr-hyper` is included in the reference distribution. Python is optional for this authoring route and is used only by the QA command:

```sh
python3 scripts/bilingual_pdf.py validate new-project/notes.pdf --paired
python3 scripts/bilingual_pdf.py validate new-project/quick-reference.pdf --paired
```

Native TeX and latexmk configuration are executable. Shell escape being disabled does not isolate file access; use trusted projects or a suitable sandbox for untrusted source.

## Structured collection

```sh
python3 scripts/course_documents.py collection.json --output new-output-directory
```

Add `--mode left` or `--mode right` for one language. This builds the Guide first, derives keyword/concept lookup and generated Guide pointers, then exports/builds Quick content through the same `paralleltext.sty`. One output folder contains `notes.pdf`, `quick-reference.pdf`, the matching named `.tex` entrypoints/content/language files, one package and staged images. `notes-input.json`, `quick-reference-input.json` and `collection-result.json` record the transformation and mechanical result. Python does not write a second layout implementation.

A collection has `languages`, `guide_title`, `quick_title`, optional `layout`, localized `labels` for `guide` and `see`, and nonempty `topics`. Each topic has a unique `id`, paired `title`, authored `guide_blocks`, and `quick.blocks`. Blocks use the shared [input contract](input.md), allowing the topic's actual explanation structure rather than fixed slots.

```json
{
  "languages":["en","fr"],
  "guide_title":["Learning notes","Notes d’apprentissage"],
  "quick_title":["Keywords and concepts","Mots-clés et notions"],
  "labels":{"guide":["Notes","Notes"],"see":["See","Voir"]},
  "topics":[{
    "id":"stack","title":["Stack","Pile"],
    "guide_blocks":[{"id":"stack.explanation","text":["A stack removes the most recently added item first.","Une pile retire d’abord le dernier élément ajouté."]}],
    "quick":{"blocks":[{"id":"stack.recall","text":["Last in, first out (LIFO).","Dernier entré, premier sorti (LIFO)."]}]},
    "aliases":[{"id":"lifo","title":["LIFO","LIFO"]}]
  }],
  "keywords":[{"id":"removal","title":["Removal order","Ordre de retrait"],"targets":["stack"]}]
}
```

- `aliases` redirect to their containing canonical topic. `keywords` can target one or more concept IDs. Optional `see_also` lists related topic IDs and requires localized `labels.see_also`.
- Topic, alias and keyword `sort_key` values can override source-language title ordering. The default is case-folded source-title order, not locale-aware dictionary collation.
- Older collections using `quick.meaning`, `quick.rule`, `quick.checks` remain readable when the corresponding localized labels are provided. They are optional compatibility fields, not the authoring model required for new notes.
- The implementation builds one notes/Quick bundle for the explicitly supplied collection. It does not infer textbook content, translate, OCR, verify pedagogy, combine courses or install software. Larger collections should be divided by an explicit authoring decision, not an invisible fixed course count.

Success means implemented mechanical checks passed. Perform source coverage, factual, language, retrieval and full-page visual review before claiming a finished learning tool. Choose a new output directory; errors are JSON and must be fixed rather than ignored.

Physical PDF destinations and printed folios are separate: Roman/letter page numbering uses native logical labels for visible pointers while links still target absolute PDF pages. The structured collection rejects `numbering: "gobble"` because its printed lookup requires page labels; use `position: "none"` to hide running folios while retaining meaningful printed references. Native LaTeX retains the normal `\pageref` semantics if deliberately using empty page labels.
