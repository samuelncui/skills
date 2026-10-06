# Cost and Performance Decisions

Read this for expensive scope choices, suite optimization, or benchmark work.

## Budget evidence before optimizing machinery

Begin qualitatively: what could break, what evidence would catch it, and which checks are cheap or costly here? Favor checks with distinct failure-detection value. Do not trade away critical boundary evidence merely because mocks are faster.

Include:
- Setup and teardown: dependency installs, compilation, environment creation, fixture/model loading, and cleanup.
- Execution: elapsed and compute time, memory, storage, network, paid requests, and resource contention.
- Feedback overhead: agent/tool round trips, log volume, and time to a diagnosable result.
- Repeat costs: flakiness, investigation, fixture drift, and maintenance when behavior changes.

Measure only when the choice depends on it. Use observed runner timings and representative runs; distinguish cold setup from warm execution. When measurements are unavailable, give a qualitative cost estimate and identify the uncertainty that could change the plan. A short note such as “affected unit tests first; one real boundary check because serialization changed; broader suite deferred with explicit uncertainty” is often enough.

Examples:
- Pure parser fix: parameterized valid/invalid/boundary cases and a reproducing regression, plus affected callers.
- Client/server schema change: both sides' contract tests and a representative actual integration path; isolated mocks alone are insufficient.
- Shared storage or concurrency change: failure/rollback, isolation, and relevant concurrent behavior, with wider checks proportional to blast radius.
- Text-only documentation change: appropriate link/example checks; no automatic unrelated performance experiment.

For a small modification, map the affected behavior and callers before selecting checks. Do not automatically run the full regression suite or unrelated performance benchmarks. State approximate cost and any concrete reason for broader scope; uncertain impact may justify widening checks. Repeat only for a changed state or a specific unresolved question, preserving earlier evidence.

Retain repository-required release gates. Document excluded or blocked evidence and what would trigger broader checks. Maintain an explicit map of coverage boundaries. Remove obsolete cases and consolidate duplicates only when they test the same contract; fill real gaps. Fewer tests are not inherently better. For UI changes, test existing user interactions, list behavior, and virtualization when affected, rather than inventing unrelated workflows.

## Preserve valid evidence across an iteration

For each costly check, retain its scope, outcome, tested input identities, and evidence location in the project's existing record. Reuse a prior result only when its relevant source/dependency/configuration identities, toolchain, environment assumptions, and fixtures still match. A matching command or branch name alone is insufficient; a new commit alone does not invalidate results for unchanged, independent inputs. This is evidence validity, not a prescribed build-cache implementation or an automatic impact-analysis oracle.

- A change invalidates checks whose inputs or assumptions it affects. Recheck those boundaries and callers; keep unrelated evidence. If impact or identity cannot be established, broaden checks or report the uncertainty rather than silently assuming reuse.
- An assertion failure needs diagnosis and a targeted regression rerun after repair, followed by newly affected checks. A setup/tool failure needs recovery of that failed stage and dependent stages. A successful prerequisite remains usable only if its outputs and assumptions are intact; incomplete execution never counts as a pass.
- Select the authoritative final full gate in advance when one is required. Local targeted checks and the existing CI full gate can serve different purposes; repeating the same full suite in both places needs an explicit repository requirement or a distinct environment/integration risk. Do not waive a required gate merely because similar local checks passed.
- Preserve the original result when resuming or rerunning. State which evidence was reused, which was refreshed, and what remains unknown. A short note is enough for a small change; do not add a universal ledger or new tooling merely to manage this decision.

## Measure the whole verification loop

Use end-to-end wall time for the iteration and identify preparation, queue/wait, build, test/benchmark execution, diagnosis, and rework where they affect the decision. Overlapping phases and nested command durations are not additive: do not sum them into a fictitious elapsed total. Report resource totals separately and qualify incomplete timing data.

Batch related remote operations into bounded stages with executable assertions and useful summaries. Preserve completed-stage evidence across tool interruptions. Observe running work at a cadence justified by expected progress or a decision deadline; polling is not new test evidence and should not trigger another run. Transport, build reuse, and toolchain-specific mechanisms belong in the target project's implementation, not a mandatory common recipe.

## Improve a slow verification loop

Profile where time goes before replacing tools. Prefer batching cases, selecting affected suites, reusing safe setup, small representative fixtures, and concise structured reports over manual per-case operation. Reuse preparation only when its relevant inputs and outputs remain valid; prevent shared mutable fixtures or stale outputs from creating false passes.

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

Before an additional benchmark run, state the unresolved decision question, the comparison it will test, and a stopping condition. Reuse an unchanged baseline/candidate comparison when its relevant conditions still apply. A new run is justified by changed relevant inputs or a specific uncertainty, not an arbitrary repetition quota, candidate count, or desire for a favorable result. Stop when the decision has sufficient evidence; otherwise report the remaining uncertainty and the justified next measurement.

If observed noise overlaps the claimed change, report an inconclusive result or improve the measurement; do not claim “no regression” from insufficient evidence. Shared-machine timings and total test-suite duration alone are poor performance gates. Choose longer or more controlled runs only when their decision value justifies the cost.

## Primary references

- [Google code-review guidance: tests](https://google.github.io/eng-practices/review/reviewer/looking-for.html#tests): co-maintenance, appropriate scope, and test validity.
- [Go test flags](https://pkg.go.dev/cmd/go#hdr-Testing_flags): `-count` controls whole test/benchmark repetitions (default one); duration-based `-benchtime` lets the runner choose enough internal iterations. The one-run starting budget above is workflow guidance, not a statistical guarantee.
- [Go testing](https://pkg.go.dev/testing#hdr-Benchmarks): native benchmark loops and measurement boundaries; use APIs supported by the project's Go version.
- [Python unittest](https://docs.python.org/3/library/unittest.html): discovery, subtests, assertions, and runner results used by the included example.

These references explain supporting mechanisms; they do not impose a universal runner or testing target.
