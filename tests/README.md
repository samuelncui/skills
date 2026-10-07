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

CI always keeps the fast validation job. The PDF render job is skipped only when every changed path is classified as documentation or an explicitly independent skill/check by `tools/classify_ci_changes.py`. Unknown paths, missing/empty diffs, render inputs/code/dependencies, and classifier/workflow changes retain full rendering. Tag pushes and **Run workflow** (`workflow_dispatch`) force full validation. A failed scope job also retains the render gate. Adding or changing the classifier itself therefore requires a full CI integration run; ordinary later documentation changes do not.

Run affected cases first, then the broader profiles needed for the changed interfaces. Each command is single-worker; do not add parallel TeX jobs on constrained hosts.

```sh
export SOURCE_DATE_EPOCH=1767225600 FORCE_SOURCE_DATE=1
.venv/bin/python tests/render_matrix.py --output .local/structured
.venv/bin/python tests/native_matrix.py --output .local/native --structured-matrix .local/structured
.venv/bin/python tests/configuration_matrix.py --output .local/configuration
.venv/bin/python tests/study_matrix.py --output .local/study
.venv/bin/python tests/study_graph_components.py --output .local/graph-components
.venv/bin/python tests/native_regressions.py --output .local/regressions
```

- **Structured:** the same self-hosted usage guide in English/French, English/Chinese, English/Arabic, English/Hebrew and Chinese/Japanese; paired/selected editions, reversed physical RTL order, explicit mixed-script text and table cells, supplied and omitted table captions, paragraph flow, figures, references and expected failures.
- **Native:** directly authored/installed LaTeX, package and image discovery without source-checkout access, native/structured pixel equivalence for matching normalized raster inputs in the same environment, IDs, counters, formulas, covers and direct flowing-prose helpers. Portable comparison fixtures normalize copied PNG metadata because JSON import deliberately flattens/strips image metadata; raw DPI metadata can otherwise cause subpixel dimension rounding. Installed-native example tests retain the original shared assets and independently check layout/ownership. Following paragraphs use the same keep/breakable policy in both compared fixtures.
- **Configuration:** defaults and sparse overrides; paper/binding parity, divider geometry, clearance, folios, covers, roles, navigation, heading attachment and continuation furniture; invalid/late configuration errors.
- **Study:** native-only selected products, clean independent installations, one interleaved lookup registry, direct subentry and companion-document targets, deferred references that survive language/formatting hooks, aliases and multisense groups, typed decision/clarification/continuation edges and actionable invalid-input errors.
- **Graph components:** neutral English/paired graph rendering, native auto-generated N reader numbers and AUX-safe running headers, compact reader profile, opt-in outlined node badges versus indented localized steps, bulleted caution fields, combined uncertainty/fallback wording, configurable style hooks, stable PDF destinations and rejected invalid API inputs. Hierarchy cases compile from separately installed renderer/study assets; the paired fixture exercises a Chinese step label while retaining original neutral content. The curated graph regression additionally checks that semantic keys stay internal, reader numbers appear, the question/solution palette remains and PDF destinations resolve. These fixtures are not a translation or full-language certification.
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

## Cold-context skill validation

Use this workflow when checking whether an agent can apply an installed skill from its shipped instructions. Follow the [positive-first guidance](../AGENTS.md#positive-first-skill-guidance); run agent trials only within the user's existing authorization.

1. Define a realistic task with generic source inputs, applicable constraints and observable expected outputs. Give a fresh agent the task and installed skills with their declared dependencies; keep earlier conversations, the author's explanation and repository-only tools outside its context. Record the tested skill revision, prompt, inputs and available tools in private review evidence.
2. Compare the agent's output and decisions with the intended contract. Separate missing tools or inputs, implementation defects and instruction gaps. For an instruction gap, identify the first missing or ambiguous step, required input, output criterion or applicability condition that prevented the correct procedure from being followed.
3. Improve the owning skill's explanation at that point: state when the procedure applies, what to read or supply, what action to take, and what the result should contain. Add a compact worked example where needed. For example, teach an optional-label procedure as: “Use the supplied label verbatim; when the input omits it, render the item without a label.” An input/output example for each case gives a fresh agent a complete choice.
4. Reserve a negative rule for an error or risk that generalizes beyond the observed instance. Explain its scope and reason, and pair it with the safe or correct procedure. For example, a general privacy boundary can direct the agent to use original generic fixtures in public examples and keep private source material in private review evidence, because publication exposes it to unrelated readers.
5. Retest the failed task with a fresh agent, then a nearby variation that distinguishes understanding from avoiding the original mistake. For the optional-label example, test both a supplied label and an omitted label. Check the complete intended result and whether a different error has appeared. Remove or revise attempted fixes that prove ineffective; retain only guidance supported by the retest or an independently justified general risk.
6. Report the observed failure, diagnosed cause, changed guidance, tested cases and remaining uncertainty. Keep deterministic checks separate from semantic review. A prose review alone is not evidence that a fresh-agent trial passed.

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

## Source-first translation and HTML

The translation skill's optional exchange v1 keeps exact source text, stable semantic IDs and reviewed target slots in one master. The independent HTML layout API renders supplied pairs without translation tooling. Its optional importer and the PDF importer use the separately discovered installed translation validator. Both preserve source/target roles independently of display order.

Affected deterministic checks run in one native-runner batch:

```sh
PYTHONPATH=tests .venv/bin/python -m unittest test_translation_contract test_translation_pdf test_bilingual_html -v
```

These cover schema/runtime constraints, source hashes and edit invalidation, successive single-unit master updates, exact adapter mapping, installed-package separation, HTML escaping/DOM/table structure, local image paths and output preservation. They do not establish extraction completeness, translation equivalence, browser rendering, font coverage or accessibility. Review exact source/target units and actual PDF/desktop/mobile HTML output separately. Held-out fresh-context authoring trials keep prompts, source identities, outputs and scoped observations as private evidence; file/tool counts are workflow observations, not measured token usage.

## Optional PDF performance profile

With the setup dependencies above installed:

```sh
.venv/bin/python tests/benchmark_bilingual.py --work .local/benchmark-en-zh --case en-zh-Hans --conditions clean noop edit
```

Use a fresh work directory for each source comparison. This performs one serial observation per condition and checks the resulting PDF; it records environment, frozen source/fixture hashes, full logs, phase timings and TeX pass counts locally. Clean means an empty document build directory with the installed toolchain, not a cold OS cache. Timings exclude installation, translation, semantic/visual review, uploads and remote queue/transport. The optional longer text-only workload uses --case multipage-en-fr --condition clean with a separate work directory. Optional --conditions font-cold font-warm requires FONTCONFIG_FILE naming a self-contained configuration with exactly one cachedir and no include directives; only a benchmark-owned cache is changed. These shared-machine observations are not CI performance thresholds or broad scalability guarantees. Keep all generated evidence ignored.

### Incremental rendering comparisons

`test_incremental_build.py` checks managed ownership, no-op timestamps, changed content/configuration/languages/assets/package dependencies, collision/symlink rejection, unrelated-file preservation, locking and interrupted-update recovery. `test_preflight.py` covers batched package discovery without weakening missing-package/font/glyph checks. Run these with the ordinary unittest runner.

For an explicit real-TeX comparison, use two fresh evidence directories and frozen checkout states. Run once per requested condition; choose additional observations only to answer a stated uncertainty. The `render` pipeline repeats fresh builds; `build` uses the managed JSON entry. `native` remains the original export/native-edit baseline.

~~~sh
.venv/bin/python tests/benchmark_bilingual.py --repo /path/to/baseline-checkout --work .local/fresh-baseline --case en-zh-Hans --pipeline render --conditions clean noop edit asset layout
.venv/bin/python tests/benchmark_bilingual.py --work .local/incremental-candidate --case en-zh-Hans --pipeline build --conditions clean noop edit asset layout --compare-to .local/fresh-baseline
.venv/bin/python tests/benchmark_bilingual.py --work .local/preflight-candidate --case en-fr --condition preflight
~~~

`--compare-to` asserts matching source/asset hashes and every page's extracted text and raster bytes, alongside the usual embedded-font, geometry, reference/link and alignment checks. Asset edits replace image bytes at the same path; layout edits change the column gap. Source-edit cases use the full article fixtures, not the text-only long fixture. Preflight-only comparisons assert identical dependency/font/glyph reports. Pixel equality to a baseline does not certify the baseline's factual, language, semantic or accessibility quality; inspect representative actual output as required.


### Optional bilingual HTML browser regression

The fast `test_bilingual_html.py` profile uses only Python. The separately opted-in `test_bilingual_html_browser.py` profile drives an already-installed Playwright Node module and Chromium, testing actual short-heading/time wrapping, paired order, RTL metadata, focus and keyboard table scrolling at desktop and narrow widths. It does not download tools or contact external pages.

```sh
BILINGUAL_HTML_BROWSER_TESTS=1 \
PLAYWRIGHT_NODE_MODULE=/path/to/installed/playwright-core \
CHROMIUM_EXECUTABLE=/path/to/chromium \
python3 -B -m unittest discover -s tests -p 'test_bilingual_html_browser.py' -v
```

`NODE_BINARY` optionally selects Node. The browser sandbox is enabled by default. `BILINGUAL_HTML_ALLOW_NO_SANDBOX=1` is an explicit test-only exception for an independently authorized isolated environment and local generated fixtures; the test neither grants that permission nor changes host isolation. Ordinary discovery reports this profile as skipped unless enabled; a missing browser/module in an enabled profile is a failure. Preserve before/after failure evidence and inspect screenshots of the actual documents as well as running the regression. These checks are not an accessibility or all-language certification.

## Structured decision-graph import

Install root requirements, then run the affected maintained checks:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*graph*.py' -v
.venv/bin/python tests/structured_graph_render.py --output .local/structured-graph-render
```

The unit suite covers the standard schema and semantic validator, strict source parsing, escaped text/restricted math/trusted-native boundaries, source bindings, image containment, call-context regressions, field coverage, a tiny independent ordering oracle and deterministic bounded larger graphs. The render profile uses separately installed skills for paired/left/right editions of the neutral parcel graph, checks Nx identities and actual helper/resume destinations, and compares a separately handwritten native manuscript's visible language columns and semantic AUX labels/pages against the importer. Source-level string equivalence alone is insufficient to establish native API correctness. Existing `study_graph_components.py` retains native compatibility and helper negative cases. Use the existing matrix `--case`, `--budget-seconds`, and `--resume` options for affected reruns; preserve failed evidence.

For practical cold-context validation, give a fresh worker an ordinary graph-authoring task, separately installed skills and available toolchain paths. It should use only owned SKILL.md/references/examples, author neutral source material, preserve one authoritative graph and inspect generated PDF pixels and reader paths. Retain the original failed attempt when updating a candidate, then restage changed skills and retry the unchanged authored graph. Record source/install/output identities privately. This tests authoring usability separately from automated conformance; it does not certify every language or private downstream adapter.
