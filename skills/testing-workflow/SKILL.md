---
name: testing-workflow
description: Design and run cost-aware automated tests and benchmarks for code changes, bug fixes, and slow verification workflows. Reuse native runners, batch assertions, and maintain tests with implementation; choose evidence proportional to risk.
---

# Testing Workflow

Optimize useful evidence per unit of total verification cost, not merely test count or runtime. Let code execute cases, assert results, and aggregate failures; use agent judgment for scope, diagnosis, and reviews that cannot be automated reliably.

## Choose the smallest sufficient verification plan

1. Inspect repository instructions, changed behavior and callers, existing tests, dependency manifests, runner commands, and CI. Preserve required gates and user exclusions.
2. Name the plausible failures and their consequences. Consider impact, likelihood, blast radius, and how easily a failure escapes or can be reversed. Do not invent numerical risk scores.
3. Select checks that address those failures. Start with affected fast tests; add boundary, integration, or end-to-end evidence where lower-level checks cannot establish the contract. Broaden for shared interfaces, migrations, concurrency, or other wide effects. Use full suites for integration or required release gates, not automatically after every edit. Stop when the selected scope has sufficient evidence; do not expand it without a concrete gap. Neither a universal full-suite rule nor a universal coverage target is appropriate.
4. State scope, approximate cost, required services, and remaining uncertainty briefly. Include setup, execution, flakiness/diagnosis, maintenance, resource/service use, and agent/tool-call overhead. Read [cost and performance guidance](references/cost-and-performance.md) when choosing between expensive checks, changing a suite, or making performance claims.

Default for a small change: assess affected behavior and callers, state the selected checks and approximate cost, then run only the smallest sufficient affected unit/integration checks. Run performance regressions only for relevant performance paths. A full suite needs a concrete broad-impact, uncertain-impact, or release-gate reason; do not repeat a full run without a new change or unresolved evidence question.

A routine small change needs a short decision, not a testing-plan document. Honor explicit required checks even if expensive; report or resolve blockers rather than silently omitting them.

## Maintain executable tests with the change

- Reuse the project's runner and language: for example, Go testing, pytest/unittest, or an existing JavaScript runner. Add dependencies or a new framework only when the existing facilities leave a concrete gap. Use scripts for orchestration, not a second assertion framework.
- Use small table-driven or parameterized fixtures with explicit expected outcomes: ordinary behavior, relevant boundaries, invalid inputs, and important invariants. Avoid duplicating production logic to compute the expected answer or asserting incidental internals.
- Keep tests, benchmarks, safe fixtures, and required dependencies in the implementation repository. Change them in the same patch when the contract changes; review the tests themselves. Do not update snapshots blindly to accept regressions.
- For a bug, preserve a regression that fails for the intended reason before the repair when practical, then passes after it. If the old state cannot be exercised safely, say so. A plausible defect found manually should become a regression when feasible.
- Mock only the dependency or behavior that is deliberately out of scope. Label mock/stub, contract, integration, real-service/model, and end-to-end evidence accurately. A mocked success does not verify the real boundary.
- Retain explicit semantic, factual, language, accessibility, or visual review where deterministic assertions cannot establish correctness. State the reviewed scope; passing scripts are not certification.

## Execute in batches and preserve evidence

Use one runner invocation or a small number of bounded batches. Do not turn a suite into one tool call per case, one subagent per test, or repeated manual requests with agent-scored output. Exploratory commands may diagnose failures; they do not replace maintained regression tests.

- Use documented clean-checkout commands and the same entry points locally and in CI when available.
- Isolate fixtures, temporary files, ports, and mutable state; automate setup/teardown and child-process cleanup. Bound timeouts and workers by memory, CPU, service limits, and test independence. Do not maximize parallelism blindly.
- Separate fast checks from explicit costly/network/real-model profiles. Automated testing grants no extra permission for paid services, data transmission, production changes, or excluded evaluations.
- Preserve the runner's nonzero failure status through wrappers and pipelines. Check collection and completion: zero collected tests, missing dependencies, disabled assertions, timeout, or truncated evidence are not a full pass.
- Diagnose assertion failures and flakiness; do not rerun until green and discard the earlier failure. Retry transient infrastructure only when safe, within a stated bound, retaining attempts.
- Rerun affected checks after the final relevant edit. Identify the tested revision or working-tree state; do not attach an old result to new code.

Report the command/profile, scope and counts when available, result, and unresolved gaps. Distinguish passed, failed, skipped (with reason), not run, blocked, and incomplete. Separate real from mocked checks and automated from manual review.

## Minimal batch example

For a Python project without an existing runner, the standard library can suffice. Read [implementation](examples/tags.py) and [tests](examples/test_tags.py), then run from this installed skill's directory:

```sh
python3 -B -m unittest discover -s examples -p 'test_tags.py' -v
```

This executes three test methods with multiple fixture cases in one command, including a Unicode case-folding regression. Assertions and exit status come from unittest. It is a teaching example, not verification of the user's product; adapt the pattern to the existing project runner rather than copying a new stack.
