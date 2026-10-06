---
name: write-if-statements
description: Write and review readable if statements, choose appropriate conditional structures, and refactor nested branches or repeated policy checks while preserving behavior. Use for new conditional logic and conditional-heavy code review or cleanup, not to eliminate every if statement.
---

# How to Write an If Statement

Make decisions easier to understand and change. Branch count is not the goal: a clear `if` is often the best design. Preserve the user's requested scope and existing language idioms.

## Establish the contract

Read the relevant callers, repository instructions, and existing tests before editing. For new code, establish the expected outcomes, invalid-input behavior, and decision priority before choosing a structure. For review or refactoring, identify the actual difficulty: nesting, unnamed policy, repeated dispatch, flag combinations, or behavior scattered across states.

Record the behavior that must remain stable: first-match priority versus independent actions; return values and types; errors; evaluation order and count; effects; and cleanup. If the code has a suspected bug, separate an intended behavior change from the refactor and confirm uncertain requirements rather than silently fixing both.

## Choose the smallest useful change

- **Keep the branch** when a short condition or a few local alternatives express the rule clearly. Keep readable conjunctions together; do not mechanically turn every Boolean operand into a return.
- **Use guard clauses** for exceptional or terminal cases that obscure the main path. Verify the exit belongs to the same function or loop and does not bypass a required suffix, transaction, audit event, or resource release. Preserve `finally`, context-manager, defer, or RAII behavior.
- **Name a predicate** when its domain meaning is clearer than its expression or one policy genuinely has multiple callers. Preserve laziness: extracting `a() and b()` into `eligible(a(), b())` evaluates both arguments before the call. Keep I/O, mutation and authorization inputs visible in the function name/signature or at the caller, so readers can see when evaluation has effects or depends on trust context.
- **Use keyed dispatch** for discrete, mutually exclusive keys with the same call contract. Keep unknown-key behavior explicit and call only the selected handler. An ordered predicate chain is not a dictionary of Boolean results; retain it or use lazy ordered rules when overlap and precedence matter. Read [semantic traps](references/semantic-traps.md) before changing dispatch or evaluation structure.
- **Use polymorphism or a strategy** when several operations repeatedly vary along the same meaningful type or state axis. Reuse an existing interface when possible; functions may suffice for one varying operation. For two simple local branches, retain the conditional unless an existing interface or repeated variation makes a strategy useful. For mutable state, preserve transition timing and handler lifetime instead of freezing a construction-time decision.
- **Compose at the caller** when separate callers already know which operations they need, instead of encoding that knowledge into interacting mode flags. Preserve shared invariants and meaningful API compatibility. An independent Boolean option is not automatically a design defect.
- **Centralize policy definitions**, not every evaluation. Consolidate genuinely identical domain rules with explicit inputs. Keep checks at independent trust boundaries and after relevant state changes; reusing a stale authorization or availability decision changes behavior. Similar-looking expressions can represent different policies.

Prefer a short exceptional branch first when it improves the reading order. Keep the normal branch first when that matches the domain story; choose order and names together so readers can follow the rule without mentally undoing negations.

## Verify behavior, then stop

Use the project's native runner and existing test style. Add or retain independent expected outcomes for normal, boundary, invalid, overlapping, and no-match cases relevant to the change. Trace observable calls when order, skipped work, mutations, or exceptions matter. Before/after comparison helps, but both implementations agreeing is not a sufficient oracle by itself.

Run affected tests in one invocation or a small resource-bounded batch. Broaden only for a concrete integration risk or a required repository gate. Keep regression tests with the change and rerun them after the final relevant edit. Report changed decisions, commands/results, intentionally unchanged branches, and untested boundaries. Do not claim faster code without a representative measurement.

The standalone [example implementation](examples/conditionals.py) and [native tests](examples/test_conditionals.py) demonstrate guard clauses, lazy dispatch, ordered rules, cleanup, and a branch worth keeping. Run from this skill directory:

```sh
python3 -B -m unittest discover -s examples -p 'test_conditionals.py' -v
```

Python's standard library is sufficient for these teaching examples; they do not verify the user's application. No other skill is required.
