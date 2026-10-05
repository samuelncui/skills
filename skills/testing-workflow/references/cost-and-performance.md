# Cost and Performance Decisions

Read this for expensive scope choices, suite optimization, or benchmark work.

## Budget evidence before optimizing machinery

Begin qualitatively: what could break, what evidence would catch it, and which checks are cheap or costly here? Favor checks with distinct failure-detection value. Do not trade away critical boundary evidence merely because mocks are faster.

Include:
- Setup and teardown: dependency installs, compilation, environment creation, fixture/model loading, and cleanup.
- Execution: elapsed and compute time, memory, storage, network, paid requests, and resource contention.
- Feedback overhead: agent/tool round trips, log volume, and time to a diagnosable result.
- Repeat costs: flakiness, investigation, fixture drift, and maintenance when behavior changes.

Measure only when the choice depends on it. Use observed runner timings and representative runs; distinguish cold setup from warm execution. Do not invent precise estimates, probabilities, or a universal cost equation. A short note such as “affected unit tests first; one real boundary check because serialization changed; broader suite deferred with explicit uncertainty” is often enough.

Examples:
- Pure parser fix: parameterized valid/invalid/boundary cases and a reproducing regression, plus affected callers.
- Client/server schema change: both sides' contract tests and a representative actual integration path; isolated mocks alone are insufficient.
- Shared storage or concurrency change: failure/rollback, isolation, and relevant concurrent behavior, with wider checks proportional to blast radius.
- Text-only documentation change: appropriate link/example checks; no automatic unrelated performance experiment.

Retain repository-required release gates. Document excluded or blocked evidence and what would trigger broader checks. Maintain an explicit map of coverage boundaries. Remove obsolete cases and consolidate duplicates only when they test the same contract; fill real gaps. Fewer tests are not inherently better. For UI changes, test existing user interactions, list behavior, and virtualization when affected, rather than inventing unrelated workflows.

## Improve a slow verification loop

Profile where time goes before replacing tools. Prefer batching cases, selecting affected suites, reusing safe setup, small representative fixtures, and concise structured reports over manual per-case operation. Cache immutable inputs with explicit keys and invalidation; prevent shared mutable fixtures or stale outputs from creating false passes.

Parallelize independent work only. Bound workers for the actual CPU, memory, external quotas, and shared resources; serialize stateful tests unless isolation is proven. Expose slow integration/end-to-end profiles explicitly, keeping meaningful real-boundary coverage.

Treat coverage as a gap-finding aid. High line coverage says little about assertion quality, failure paths, or important contracts. Review whether an intentionally broken behavior would fail a relevant test.

## Reproducible benchmarks

Use the project's native benchmark facilities when available; benchmark only when performance matters to the change or claim. Define before running:
- The operation and timed boundary, including whether setup, I/O, and teardown count.
- Representative input sizes/distributions and fixed safe fixtures; record seed and fixture/model hashes when relevant.
- The relevant cold-start or warmed steady-state behavior, framework calibration, concurrency, runtime/dependency versions, hardware, and important machine conditions. Do not add warm-up or repeated whole runs by default.
- The pre-change revision/configuration as the initial baseline, then an agreed stable baseline for later comparisons. Do not require arbitrary historical versions. Define any acceptance threshold from an actual requirement, not an invented statistical rule.

Keep correctness assertions separate from timed work while verifying the measured operation produces meaningful results. Prevent dead-code elimination and account for allocation, memory, or I/O metrics where relevant. Preserve the benchmark alongside implementation.

Start with the native runner's normal measurement and calibration. For ordinary Go benchmark work, one `go test -run '^$' -bench '<affected-pattern>' -count=1` invocation per source version can be sufficient; Go calibrates internal iterations. This is a starting workflow, not a prohibition on statistical experiments or a universal requirement for other languages. Diagnose anomalies first, preserve the original result, and rerun only affected cases when justified. Do not invent a fixed ten-sample rule or describe an agent-chosen budget as a repository requirement.

Compare baseline and candidate under matching conditions. Report units, measured boundaries, and the evidence actually collected, including calibration or sample count when available. A single runner result supports a limited observation, not a confidence interval. If repeated measurements are necessary for the decision, explain why, choose a proportionate budget, and report variation or distributions; interleave baseline/candidate runs where useful to reduce drift. Use tail percentiles only with enough samples to support them. Preserve raw results and explain outlier handling rather than discarding inconvenient values.

If observed noise overlaps the claimed change, report an inconclusive result or improve the measurement; do not claim “no regression” from insufficient evidence. Shared-machine timings and total test-suite duration alone are poor performance gates. Choose longer or more controlled runs only when their decision value justifies the cost.

## Primary references

- [Google code-review guidance: tests](https://google.github.io/eng-practices/review/reviewer/looking-for.html#tests): co-maintenance, appropriate scope, and test validity.
- [Go test flags](https://pkg.go.dev/cmd/go#hdr-Testing_flags): `-count` controls whole test/benchmark repetitions (default one); duration-based `-benchtime` lets the runner choose enough internal iterations. The one-run starting budget above is workflow guidance, not a statistical guarantee.
- [Go testing](https://pkg.go.dev/testing#hdr-Benchmarks): native benchmark loops and measurement boundaries; use APIs supported by the project's Go version.
- [Python unittest](https://docs.python.org/3/library/unittest.html): discovery, subtests, assertions, and runner results used by the included example.

These references explain supporting mechanisms; they do not impose a universal runner or testing target.
