# Testing workflow

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Use this skill to choose and maintain useful tests for a code change, investigate a regression, or reduce a slow verification loop. It favors the project's existing runner and checks proportional to the risk, while preserving required release gates.

## Use it

Install `testing-workflow` with your host's skill installer, or copy its complete directory. It is independent of the PDF skills. Then ask, for example:

- “Use testing-workflow to test this parser fix. Preserve a regression and check affected callers.”
- “Review why this suite is slow and propose cheaper checks without losing meaningful coverage.”

Provide the change or repository, known failures, required checks, and any excluded services or cost limits. Expect a short verification scope, maintained executable tests where needed, and a report separating passed, failed, skipped, blocked, and unrun checks. The [agent workflow](SKILL.md) and [cost/performance reference](references/cost-and-performance.md) contain the detailed method.

Across an iteration, previous verification evidence remains usable only while its relevant inputs and assumptions still match. After a change or interruption, refresh the affected checks or failed stages instead of restarting everything. Keep required final gates, avoid unjustified local/CI duplication, and explain further benchmark runs by an unresolved question and stopping condition. Details stay in the cost/performance reference.

## Try the example

Read the [tag normalizer](examples/tags.py) and [tests](examples/test_tags.py). From this installed skill's directory, with Python 3.11+ and no third-party packages, run:

```sh
python3 -B -m unittest discover -s examples -p 'test_tags.py' -v
```

Three test methods cover normal inputs, idempotence, Unicode case folding, and rejected inputs. The command uses unittest's assertions and failure exit status. These are teaching fixtures, not tests of your product; adapt the pattern to its existing runner.

Automated results do not establish factual, language, visual, or accessibility correctness. External services, paid runs, publication, and excluded evaluations still need applicable authorization. [MIT license](LICENSE).
