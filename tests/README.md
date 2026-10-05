# Validation and realistic usage tests

These checks belong to the implementation and run through Python's native unittest runner plus serial integration scripts. [RESULTS.json](RESULTS.json) records the last completed, sanitized acceptance scope; it is evidence for its source hashes, not an automatic claim about later edits. CI status belongs to the exact commit checked by Actions.

## Setup and fast checks

Use Python 3.11+, Make and the skill's documented XeLaTeX/latexmk/fonts. Python dependencies are isolated:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/export_native_examples.py --check
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python tools/check_package.py
.venv/bin/python tools/collect_example_outputs.py --check --output .
```

On Debian/Ubuntu the rendering profile needs latexmk, texlive-xetex, texlive-latex-extra, texlive-science, texlive-lang-arabic, texlive-lang-french, fonts-lmodern, fonts-noto-core, fonts-noto-cjk and fonts-dejavu-core. Do not install unrelated dependencies or modify host security limits to make a check pass.

Fast tests cover schema/runtime agreement, field constraints, explicit RTL text runs, bounded asset paths and symlink/traversal protection, literal installed dependency paths, Make product selection, package ownership, portable manifests, example parity and bounded-runner outcomes. Expected errors are tests, not usable deliverables.

The separate testing-workflow skill also carries its own standard-library regression command:

```sh
python3 -m unittest discover -s skills/testing-workflow/examples -p 'test_tags.py' -v
```

## Integration profiles

Run affected cases first, then the broader profiles needed for the changed interfaces. Each command is single-worker; do not add parallel TeX jobs on constrained hosts.

```sh
export SOURCE_DATE_EPOCH=1767225600 FORCE_SOURCE_DATE=1
.venv/bin/python tests/render_matrix.py --output .local/structured
.venv/bin/python tests/native_matrix.py --output .local/native --structured-matrix .local/structured
.venv/bin/python tests/configuration_matrix.py --output .local/configuration
.venv/bin/python tests/study_matrix.py --output .local/study
.venv/bin/python tests/native_regressions.py --output .local/regressions
```

- **Structured:** the same self-hosted usage guide in English/French, English/Chinese, English/Arabic, English/Hebrew and Chinese/Japanese; paired/selected editions, reversed physical RTL order, explicit mixed-script text and table cells, paragraph flow, figures, references and expected failures.
- **Native:** directly authored/installed LaTeX, package and image discovery without source-checkout access, native/structured pixel equivalence for matching normalized raster inputs in the same environment, IDs, counters, formulas, covers and direct flowing-prose helpers. Portable comparison fixtures normalize copied PNG metadata because JSON import deliberately flattens/strips image metadata; raw DPI metadata can otherwise cause subpixel dimension rounding. Installed-native example tests retain the original shared assets and independently check layout/ownership. Following paragraphs use the same keep/breakable policy in both compared fixtures.
- **Configuration:** defaults and sparse overrides; paper/binding parity, divider geometry, clearance, folios, covers, roles, navigation, heading attachment and continuation furniture; invalid/late configuration errors.
- **Study:** native-only selected products, clean independent installations, one interleaved lookup registry, direct subentry and companion-document targets, deferred references that survive language/formatting hooks, aliases and multisense groups, typed decision/clarification/continuation edges and actionable invalid-input errors.
- **Focused native regressions:** prefix-key ordering; all documented decision-ID punctuation; paragraph/heading lifecycle and starred subentries; short and continued headers; separate version/status values; explicit oversized keep/header failures.

The registry and decision fixtures are original generic examples. Private learning material is not a fixture source. The [self-hosted source review](../skills/study-notes/examples/coverage-review.md) maps selected source sections to the four study forms; automated link checks complement source reading.

### Bounded foreground execution

Failed or blocked cases print their full structured diagnostic record, including failed checks and document errors, while successful cases stay concise. CI retains only synthetic matrix and per-case JSON reports for seven days with an always-run artifact step; it does not publish generated deliverable PDFs, raw environment variables or credentials.

Every integration script accepts --case, --budget-seconds and --resume. A tool/runtime time limit is an infrastructure boundary, not evidence of a rendering defect. For example:

```sh
.venv/bin/python tests/render_matrix.py --output .local/structured --budget-seconds 95
.venv/bin/python tests/render_matrix.py --output .local/structured --resume --budget-seconds 95
```

The budget is a wall-clock ceiling for the current foreground batch, not a benchmark or a reason to repeat the suite. Pick a ceiling below the host's invocation limit, leaving cleanup time. The runner checkpoints each case, terminates and reaps its own process group on timeout, and resumes pending/infrastructure-blocked work. It never retries an unchanged assertion failure until it happens to pass.

Each directory contains matrix.json and per-case results. Exit 0 means all **requested** cases passed; exit 1 means a real case failed; exit 75 means requested work remains blocked/unrun. Only complete=true means every case in that profile passed. Not-requested cases, expected failures, semantic review and visual review remain explicit. Zero completed cases cannot become a complete pass.

Runtime, fixtures, installed-source inputs and test implementation are fingerprinted. Do not change them during a resumable run. After a fix, choose a new output directory and rerun the affected scope; do not relabel old PDFs as evidence for changed inputs.

The structured profile alone supports optional `--reuse-rendered PRIOR_MATRIX` for unchanged successful positive renders. It freshly exports and byte-compares current native source/package/license/image files, verifies the original PDF checksum, rejects detected engine/fixed-date changes, then reruns canonical QA and every case assertion. Failed, blocked and expected-error cases are not reused. The caller must keep the TeX/font installation unchanged: this feature does not prove external font/package byte identity. Reuse metadata distinguishes original recorded checksums from AUX/LOG hashes captured during verified copying. If any prerequisite is missing or differs, rebuild that case. Reuse is an optimization with explicit provenance, not a way to bypass a failure.

## Regenerate curated examples

Repository-maintainer commands are not dependencies of installed skills. The nine curated PDFs remain beside their sources: five bilingual output.pdf files and the selected study notes.pdf, quick-reference.pdf, keyword-index.pdf and decision-tree.pdf. Actions validates them; it does not generate the deliverable copies.

When tutorial content changes, regenerate the native route and check parity:

```sh
.venv/bin/python tools/write_tutorial_examples.py
.venv/bin/python tools/export_native_examples.py
```

The original native illustrations are shared once under examples/shared. If illustrations.tex changes, compile it into an ignored directory and crop/render its seven pages:

```sh
mkdir -p .local/illustrations
cp skills/bilingual-pdf/examples/shared/illustrations.tex .local/illustrations/main.tex
(cd .local/illustrations && latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape main.tex)
.venv/bin/python tools/export_illustrations.py --pdf .local/illustrations/main.pdf --output skills/bilingual-pdf/examples/shared
```

Run the current-source structured and study profiles above. For a focused artifact refresh, request all five named *-bilingual cases and study-example-all; other unrequested checks remain explicitly unrun. Then collect only passed, matching-source outputs:

```sh
.venv/bin/python tools/collect_example_outputs.py --matrix .local/structured --study-matrix .local/study --output .local/curated --previews .local/previews
```

Inspect every final PDF page and its text, links, fonts and metadata. Copy only the collected skills subtrees into the repository after that review, then rerun the manifest --check command. Sources and shared example images stay adjacent to their owning skill; runtime assets contain only reusable package/profile files. Manifests use portable relative paths and dependency identities, never host paths or build logs. Exact byte reproduction requires matching fonts, engine/packages and fixed time.

## Review limits

Compiler success is not semantic, factual, translation, privacy or visual approval. The calling model owns paired content. Review readable-resolution pixels and the authored source, especially Arabic/Hebrew direction, actual table cells, uneven multi-page paragraphs, next-block resynchronization, subentry page destinations, continued headers and tab clearance. Sparse whitespace or underfull boxes can be valid; clipping, overfull boxes, missing glyphs and unresolved references are not accepted silently.

Tests distinguish a bounded JSON table from paragraph continuation: each table row aligns independently, but the complete structured table remains together. Native authors may permit page breaks between bounded rows; row splitting and repeated longtable headers are not implemented.

Traditional Chinese, arbitrary language combinations, vertical writing, native Windows font discovery, printer-specific production and PDF/UA are outside current acceptance. Native TeX remains executable input; disabling shell escape is not a sandbox. Keep review evidence private and publish only original fixtures, authorized examples and sanitized results. Test elapsed time on a shared machine is not a performance benchmark.
