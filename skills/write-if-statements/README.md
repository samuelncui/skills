# How to Write an If Statement

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Use this skill to write new conditional logic, review a branch-heavy function, or simplify existing code without changing its behavior. The goal is readable decisions, not fewer `if` statements.

## Install and use

Install with the Skills CLI or your host's compatible installer:

```sh
npx skills add samuelncui/skills --skill write-if-statements
```

Keep the complete skill directory, including its license, references, and examples. No other skill or Python installation is needed to read the guidance; Python 3 is needed only to run the included examples.

Ask your coding assistant to use `$write-if-statements` (or select it through your host). Supply the relevant code, callers, expected behavior, and available test command. Useful requests include:

- “Write the retry decision for this client. Retry only transient failures while attempts remain. Keep it simple and test the boundaries.”
- “Review this routing function. Explain whether a lookup table would preserve first-match priority and skipped work. Don't edit yet.”
- “Flatten this nested handler without changing return values, exceptions, or cleanup. Add regression tests and run the affected suite.”

Expect a scoped review or patch, reasons for the chosen structure, and test results with remaining gaps. A simple branch may stay unchanged. A suspected bug should be distinguished from a behavior-preserving refactor.

## Try the examples

Read the [implementation](examples/conditionals.py) beside its [tests](examples/test_conditionals.py). From this skill directory, run:

```sh
python3 -B -m unittest discover -s examples -p 'test_conditionals.py' -v
```

Seven test methods check guard-clause results and cleanup, exception propagation, overlapping ordered rules, skipped predicates, selected dispatch handlers, and a clear conjunction worth keeping. They use only the standard library and verify these teaching examples, not your application.

## Boundaries and further reading

An ordered condition chain is not automatically equivalent to a dictionary. Moving a decision can change when work runs, when errors occur, and which state is observed. Read the [semantic traps and primary references](references/semantic-traps.md) for those tradeoffs; [SKILL.md](SKILL.md) contains the agent workflow.

The independently written material and examples carry the included [MIT license](LICENSE). Linked external works retain their own rights.
