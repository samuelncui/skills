# Validation and realistic usage tests

The current suites include **59 unit tests**, **36 structured-render cases** and **22 native-LaTeX cases**. Exact completed results and positive-PDF/page counts are recorded in RESULTS.json. Expected failures are counted as tests, not usable deliverables. Exact case results, source/output hashes and review limits are in [RESULTS.json](RESULTS.json). Remote CI status belongs to the exact commit shown in Actions, not this local record.

## Structured route

- Four substantial original article pairs: English/French, English/Chinese, English/Arabic and Chinese/Japanese; paired and both single-language outputs.
- Reversed Arabic/English physical order; RTL mixed-script runs, bullets and page-reference suffixes.
- Paired headings, prose, list items, quotation, image/captions, individually aligned table rows and native local references.
- Letter paper, optional covers/blank parity, a 12-page unequal-length stress fixture and references to expanded parent blocks.
- Isolated notes/Quick builds, flexible Quick blocks including their own image and cross-concept reference, aliases, secondary keywords and wrapped Guide links.
- Arabic notes/Quick and Arabic-only output.
- Real paragraph flow across pages in all four language pairs, with unequal translation lengths and resynchronized following blocks.
- One full-width shared photograph with paired captions in all four language pairs.
- Rejection of an oversized atomic semantic unit and a missing glyph.

## Native LaTeX route

- Each checked-in article project builds directly with latexmk in an isolated directory. Its pixels match the equivalent structured-route PDF in the same environment.
- Both installed starters build without a sibling skill; the full notes/Quick example rebuilds from ordinary `.tex`.
- Public IDs `foo` and `foo-L` remain distinct; duplicate IDs and the reserved measurement namespace are rejected.
- Shared equation counters advance once. An RTL numbered-math regression checks actual formula baseline equality, not only block-start markers.
- Native missing glyphs and oversized units are caught; a selected-language booklet omits the unselected cover language and preserves blank inner faces.
- Standard `xr-hyper`/`hyperref` named cross-PDF destinations resolve to the actual flat `notes.pdf` target.
- Direct native prose/shared-photo helper fixtures match their structured equivalents pixel-for-pixel in the same environment.

## Realistic skill use

A fresh learning-skill run received only the complete installed skill and the small original teaching source. It authored three notes pages, two Quick pages and a 32-record source map. A second review found grouped secondary headwords and English action labels in the Chinese trace. Those were corrected: three alias rows and 23 keyword rows now lead to three canonical concepts, including independently findable Overflow, Queue and Removal order. The corrected bundle passed relocation, page inspection and 63 link-annotation checks. Source uncertainty remains explicit. See [the example review record](../examples/course-guide-quick-reference/three-concepts/coverage-review.md).

A separate bilingual-skill run built the English/Chinese structured article, copied only six portable source files into a fresh project, and built it directly with latexmk. Its two PDFs were pixel-identical at 1273 × 1800; all four page images were inspected. Input hashes stayed unchanged, package bytes matched, and recorder evidence showed no JSON, Python generation or sibling-skill input in the native build. This tests export followed by native compilation, not independent starter-based authorship.

The [skill-creator](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) manifest checks also passed. The important evidence is executable behavior and the reviewed output, not frontmatter validity alone.

## Reproduce

After installing the documented dependencies:

```sh
python3 tools/export_native_examples.py --check
python3 tools/sync_renderer.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/check_package.py
python3 tests/render_matrix.py --output .local/new-structured-matrix
python3 tests/native_matrix.py --output .local/new-native-matrix --structured-matrix .local/new-structured-matrix
python3 tools/collect_example_outputs.py --check --output examples
```

Matrices copy complete skills into fresh directories. The native tests compile authored `.tex` without using the JSON adapter to generate their bodies. GitHub Actions runs the same checks with public Ubuntu dependencies; it does not deliver example artifacts.

## Review limits

The previous release received contact-sheet inspection but missed a real quote-slot defect; the rebuilt tests now measure actual quote glyph bounds and physical column positions in all four language pairs. See RESULTS.json for the current review coverage. Curated article pages, notes/Quick pages and targeted RTL/reference/equation pages receive readable-resolution inspection before publication. Final unchanged rebuilds were compared with reviewed pixels or hashes. The four article translations received separate author-level reading and source reconciliation, including corrected Arabic/Japanese nuances. These checks are not external human linguistic certification or universal domain validation. Synchronized column endings and wrapped titles may produce underfull-box warnings; whitespace is reviewed as part of the documented layout contract. No overfull box or missing glyph is accepted.

The stress fixture deliberately repeats text a different number of times in its two columns; it is a placement test, not a translation-quality example. Traditional Chinese, other language combinations, vertical writing, native Windows font discovery, printer-specific production and PDF/UA remain unverified. Native TeX is executable; the checks do not turn it into a sandbox.

Working logs and operational evidence stay out of the public repository. Only original inputs, portable example sources, sanitized summaries and six curated PDFs are published.
