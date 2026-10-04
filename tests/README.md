# Validation and realistic usage tests

The current suites include **94 unit tests**, **38 structured-render cases**, **26 native-LaTeX cases** and **41 configuration cases**. Exact completed results and positive-PDF/page counts are recorded in RESULTS.json. Expected failures are counted as tests, not usable deliverables. Exact case results, source/output hashes and review limits are in [RESULTS.json](RESULTS.json). Remote CI status belongs to the exact commit shown in Actions, not this local record.

## Structured route

- One substantial original article in four pairs: English/French, English/Chinese, English/Arabic and Chinese/Japanese; paired and both single-language outputs. Repeated English/Chinese text and semantic block structure must be identical across editions.
- Reversed Arabic/English physical order; RTL mixed-script runs, bullets and page-reference suffixes.
- Paired headings, prose, list items, quotation, image/captions, individually aligned table rows and native local references.
- Letter paper, optional covers/blank parity, a 12-page unequal-length stress fixture and references to expanded parent blocks.
- Isolated notes/Quick builds, flexible Quick blocks including their own image and cross-concept reference, aliases, secondary keywords and wrapped Guide links.
- Arabic notes/Quick and Arabic-only output.
- Real paragraph flow across pages in all four language pairs, with unequal translation lengths and resynchronized following blocks.
- One full-width shared photograph with paired captions in all four language pairs. These checks also run against each complete curated article, verifying both paragraph continuations and the following section’s resynchronization.
- Rejection of an oversized atomic semantic unit and a missing glyph.

## Native LaTeX route

- Each checked-in article project builds directly with latexmk in an isolated directory. Its pixels match the equivalent structured-route PDF in the same environment.
- Minimal native authoring still works without starter trees. Four installed article examples resolve the one skill-level style/image pool directly. The course example and minimal notes/Quick pair use the explicitly selected installed bilingual dependency.
- Public IDs `foo` and `foo-L` remain distinct; duplicate IDs and the reserved measurement namespace are rejected.
- Shared equation counters advance once. An RTL numbered-math regression checks actual formula baseline equality, not only block-start markers.
- Native missing glyphs and oversized units are caught; a selected-language booklet omits the unselected cover language and preserves blank inner faces.
- Standard `xr-hyper`/`hyperref` named cross-PDF destinations resolve to the actual flat `notes.pdf` target.
- Direct native prose/shared-photo helper fixtures match their structured equivalents pixel-for-pixel in the same environment.

## Native configuration and lifecycle

The configuration matrix exercises zero-setup defaults and sparse native/package-key overrides; A4, Letter and custom paper; mirrored binding and oneside geometry; actual divider endpoints; high-resolution full-height ink clearance; custom folio notation and positions; standard page styles and manual one/two-column transitions; configurable cover blank/parity rules; semantic roles, diagrams, localized entry heads and navigation tabs; paragraph register propagation; heading attachment; and long paired/selected/Arabic continuation furniture. It rejects unknown keys/roles/navigation, impossible geometry, invalid choices and late setup. Independently authored native and structured configuration fixtures must match pixels. The collection matrix also checks Roman printed folios against physical cross-PDF destinations.

The independent API review reproduced and verified corrections for minipage paragraph resets, selected-flow continuation records, cover column-state restoration, heading orphans, and ambient-language leakage into shipped furniture. These are executable regressions, not manuscript-specific page patches. Configuration styles and built-in profiles are documented at skill level; the two native profile files are optional.

## Realistic skill use

Before this dependency refactor, a fresh learning-skill run received the then-self-contained skill and the small original teaching source. It authored three notes pages, two Quick pages and a 32-record source map. A second review found grouped secondary headwords and English action labels in the Chinese trace. Those were corrected: three alias rows and 23 keyword rows now lead to three canonical concepts, including independently findable Overflow, Queue and Removal order. The corrected bundle passed relocation, page inspection and 63 link-annotation checks. Source uncertainty remains explicit. See [the example review record](../skills/course-guide-quick-reference/examples/coverage-review.md).

The earlier bilingual-skill authoring check built the English/Chinese structured article, copied only six portable source files into a fresh project, and built it directly with latexmk. Its two PDFs were pixel-identical at 1273 × 1800; all four page images were inspected. Input hashes stayed unchanged, package bytes matched, and recorder evidence showed no JSON, Python generation or sibling-skill input in the native build. This tested export followed by native compilation; current minimal authoring and installed-source checks are separate.

Current relocation checks install bilingual independently and exercise course with an explicitly supplied renderer in unrelated paths containing spaces. Missing or incompatible dependencies report actionable errors before output creation. TeX recorder files verify that installed examples consume the selected skill assets rather than source-checkout files. Manifests record portable local source paths and the named renderer/shared-asset hashes.

The [official skill structure](https://developers.openai.com/plugins/build/skills) manifest checks also passed. The important evidence is executable behavior and the reviewed output, not frontmatter validity alone.

## Reproduce

After installing the documented dependencies:

```sh
python3 tools/export_native_examples.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/check_package.py
python3 tests/render_matrix.py --output .local/new-structured-matrix
python3 tests/native_matrix.py --output .local/new-native-matrix --structured-matrix .local/new-structured-matrix
python3 tests/configuration_matrix.py --output .local/new-configuration-matrix
python3 tools/collect_example_outputs.py --check --output .
```

Unit tests cover localized image schemas, bounded asset roots, traversal/symlink escapes, collision-free exported names, renderer API compatibility and literal dependency paths through Make. Matrices copy complete skills into fresh directories. The native tests compile authored `.tex` without using the JSON adapter to generate their bodies. GitHub Actions runs the same checks with public Ubuntu dependencies; it does not deliver example artifacts.

## Review limits

The previous release received contact-sheet inspection but missed a real quote-slot defect; the rebuilt tests now measure actual quote glyph bounds and physical column positions in all four language pairs. See RESULTS.json for the current review coverage. Curated article pages, notes/Quick pages and targeted RTL/reference/equation pages receive readable-resolution inspection before publication. All 12 current article pages and all five learning pages were reviewed; final unchanged pages were compared pixel-for-pixel with their reviewed versions. The four article translations received separate author-level reading and source reconciliation, including corrected Arabic/Japanese nuances. These checks are not external human linguistic certification or universal domain validation. Synchronized column endings and wrapped titles may produce underfull-box warnings; whitespace is reviewed as part of the documented layout contract. No overfull box or missing glyph is accepted.

The stress fixture deliberately repeats text a different number of times in its two columns; it is a placement test, not a translation-quality example. Traditional Chinese, other language combinations, vertical writing, native Windows font discovery, printer-specific production and PDF/UA remain unverified. Native TeX is executable; the checks do not turn it into a sandbox.

Working logs and operational evidence stay out of the public repository. Only original inputs, portable example sources, sanitized summaries and six curated PDFs are published.

## Regenerate curated outputs

Repository-only maintenance commands; installed skills do not execute these tools. Use fresh ignored build directories:

```sh
python3 tools/export_native_examples.py
export SOURCE_DATE_EPOCH=1767225600 FORCE_SOURCE_DATE=1
python3 tests/render_matrix.py --output .local/new-structured-matrix
python3 tests/native_matrix.py --output .local/new-native-matrix --structured-matrix .local/new-structured-matrix
python3 tests/configuration_matrix.py --output .local/new-configuration-matrix
python3 tools/collect_example_outputs.py --matrix .local/new-structured-matrix --native-matrix .local/new-native-matrix --output .local/new-pdfs --previews .local/new-previews
```

Inspect every final page, then overlay the `skills/` subtrees from `.local/new-pdfs/` and `.local/new-previews/` into the repository's `skills/`. Only six PDFs, six first-page previews and the two local manifests are staged. Sources remain beside their outputs; article images live once under the bilingual skill assets. Skill READMEs hold usage guidance, references hold photo attribution, and each skill carries its license. Verify with `python3 tools/collect_example_outputs.py --check --output .`. Example paths are local to their installed examples folder; renderer dependency hashes use paths relative to the named bilingual-pdf skill. Build tools remain repository-only. Exact byte reproduction requires the same TeX engine, packages, fonts and fixed clock.
