# Translation CLI acceptance — 2026-10-14

This scoped record covers the shared command registry, per-action JSONL input, atomic batches, paragraph preparation and anchor splitting, explicit translation/review steps, exact local patches, review restart, todos and compact stdout metadata. It supplements, rather than replaces, the historical `RESULTS.json` snapshot. Local raw traces and private review material are not published.

## Engineering checks

- Pre-progress-string fast discovery: 312 tests, with 311 passing and one optional browser profile skipped in that invocation. That browser test was then enabled separately and passed: four language/order fixtures at desktop and narrow widths, eight actual Chromium scenarios. Local fixture execution used an explicitly authorized browser-only sandbox exception; host isolation was unchanged.
- After the later stdout progress-string projection, all 105 translation tests passed, including rollback and identical-packet replay. The earlier full-suite count is not presented as a rerun after that projection.
- Earlier translation-only discovery: 101 tests passed before the final three stdout-default regressions were added. This is an earlier subset, not another 101 tests to add to the final total.
- Independent installed translation → PDF and semantic-exchange → HTML consumers passed, including source preservation, child ordering and review/readiness rejection.
- Six real PDF cases passed: reviewed English/Chinese, unequal multipage content, left selection, right selection, continuation reserve and heading continuation. Representative reviewed and unequal-length pages were visually inspected. The later stdout-only projection did not change stored masters or renderer inputs, so this render evidence was reused.
- Package ownership, native example parity, nine PDF/nine preview manifest checks and whitespace checks passed.
- Initial aggregate/browser attempts exposed missing environment activation (`make` and Chromium shared libraries). Loading the existing toolchain fixed those environment failures; no dependency installation or validation relaxation was needed.

Reproduce with the repository's documented dependencies and the commands in [README.md](README.md):

```sh
.venv/bin/python -B -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python tools/check_package.py
.venv/bin/python tools/export_native_examples.py --check
.venv/bin/python tools/collect_example_outputs.py --check --output .
.venv/bin/python tests/translation_pdf_matrix.py --output /path/to/fresh-evidence
```

Enable the separate HTML browser profile using an existing Playwright/Chromium installation as documented in the README. Tests do not authorize disabling browser isolation.

## Live translation and semantic limits

A cold-context model trial processed a 6,942-word source through all 88 units to machine-ready status. Independent semantic review nevertheless found substantive meaning errors, including negation and responsibility attribution. Machine readiness establishes workflow completion, not translation correctness. The trial also exposed incomplete forwarding of progress events.

Review guidance was then strengthened to check proposition polarity, roles, conditions and the meaning of an entire patched sentence, and to inspect every receipt in a batch for progress. A separate 1,226-word cold-context trial subsequently reached 22/22 ready. Its completed independent check covered all 32 defined facts without finding a substantive error, including the earlier error categories. The follow-up still omitted five of 26 expected progress notifications. Stronger prose alone did not resolve that mechanical reporting failure. A subsequent stdout-only change renders each progress value as a directly copyable string. Its separate 266-word cold-context regression passed: all 25 emitted progress strings matched the received reports (one preparation, twelve translation, twelve review); all 52 official CLI calls succeeded, all twelve units were delivered once per normal stage, and the final master was reviewed and ready. The observer found unchanged source/installation hashes and no script-driven workflow or unexplained state drift. This verifies reporting on that small fixture, not zero missed updates on arbitrary long documents.

The shorter follow-up is targeted evidence; it is not a zero-error rerun of the complete long source under the final guidance. Neither these trials nor fixed benchmark translations establish general language quality, elapsed-time savings or reliability across arbitrary documents.

## Measured protocol costs

The same four original fixtures were replayed with `tiktoken 0.12.0`, `o200k_base`. Tokens count actual request argv plus authored stdin and actual stdout; they exclude transport/file-writing framing, hidden reasoning, billing and rendering. Each run asserted three normal source-body exposures, one target write and one complete target review, exact source reconstruction and readiness. Random short references can cause small token variation.

All entries below are **calls / protocol tokens**. The old baseline is commit `14a9113`; candidate measurements are actual runs, not sums of offline estimates.

| Fixture | Old protocol | New run, before stdout compaction | Compact run, before progress text | Final progress-text run | Final standalone commands |
| --- | ---: | ---: | ---: | ---: | ---: |
| guide_short | 8 / 1773 | 7 / 2565 | 7 / 2176 | 7 / 2145 | 9 / 2203 |
| long_semantic_split | 12 / 5080 | 12 / 5394 | 12 / 5311 | 12 / 5234 | 18 / 5400 |
| zh_en_structure | 14 / 2139 | 13 / 2702 | 13 / 2424 | 13 / 2330 | 21 / 2540 |
| shared_context | 10 / 1145 | 9 / 1360 | 9 / 1282 | 9 / 1227 | 13 / 1338 |

Final progress-text run costs remain 20.98%, 3.03%, 8.93% and 7.16% above the old protocol. Relative to the new uncompressed run, actual savings were 420, 160, 372 and 133 tokens. Metadata/ack compaction alone saved 389, 83, 278 and 78 tokens; the subsequent progress-string runs saved a further 31, 77, 94 and 55. Batching reduced final standalone calls by 2, 6, 8 and 4 respectively. These are protocol costs and call counts, not measured model-time or translation-quality gains.

Before compaction, prepare-phase increases accounted for 537/135/497/82 of the total 792/314/563/215 token increases over the old protocol. Short structured fixtures repeatedly emitted default unit metadata. Translation-phase increases were 114/72/13/52, review-phase increases 117/83/29/57, and final reconciliation added 24 per fixture. No additional full-source pass was observed. Final compaction omits documented default parent/index/continuation values and empty receipt fields, and replaces repeated save/accept ID arrays with counts; actual continuation, heading paths, references, record tags and progress remain explicit.

Progress objects cost 64/150/190/106 tokens in the earlier compact fixtures. Final progress strings cost 34/80/100/56 tokens and are already included in protocol totals. Counting a field with its surrounding JSON delimiters produces a different allocation; token ablation estimates are not independently additive.

Fixed instruction loading is separate: old 4304 tokens; new pre-compaction 4580; compact-output benchmark snapshot 4749. After the semantic/progress guidance changes, that instruction snapshot totaled **5106 tokens** (SKILL 1460, workflow reference 3646). The subsequent concise copyable-progress guidance totals **4984 tokens** (SKILL 1394, workflow 3590). The eight final progress-text protocol runs used the 4984-token instruction snapshot; earlier traces retain their original instruction hashes.

Use `tests/benchmark_translation_tokens.py --help` and a fresh output directory to reproduce both standalone and batched fixture measurements. Preserve previous evidence directories. Fixed fixture replay is not a substitute for live semantic review.
