# Semantic traps in conditional refactoring

Read when changing evaluation structure, dispatch, or the placement of a decision.

## First match is not key lookup

`if p(): ... elif q(): ...` tests `q` only if `p` is false. Both can be true, with the first winning. Constructing `{p(): first, q(): second}` evaluates both predicates and collapses equal Boolean keys; dictionary insertion order does not restore the original semantics.

Use a map for actual discrete identifiers, with compatible hashing/equality and missing-key behavior. Preserve `if` chains for ranges and precedence. A lazy ordered sequence of predicate/handler callables can express an extensible rule list; stop at the first match. Independent `if` statements may execute multiple actions, so replacing them with first-match dispatch also changes behavior.

The example's overlapping thresholds use ordered callables to illustrate this distinction. For just those two thresholds, the original branch chain is simpler and can stay.

## Selecting work must not execute all work

Store handlers, not handler results. `handlers.get(key, fallback())` executes the fallback before the lookup even when the key exists. Prefer selecting a callable and then invoking it. Match the existing unknown-key contract explicitly: select the default handler when a default is intended, or preserve the specified exception when an unknown key is an error. Test a known key and a missing key, including whether fallback work is skipped.

Keep input validation and key normalization at their original point unless the contract permits moving them. Equality chains can accept unhashable inputs or compare differently from dictionary keys; a map is not automatically a drop-in replacement for arbitrary values.

## Boolean equivalence is not execution equivalence

Truth tables apply to pure stable Boolean values. Predicates can mutate, throw, perform I/O, or observe changing state. Preserve their order, number of calls, and short-circuiting. In Python, `and` and `or` return an operand, not necessarily a Boolean; adding `bool` may change a public result. Extracting a predicate can also accidentally evaluate arguments that the original branch skipped.

A repeated policy implementation can be centralized in a function while still being evaluated at each required boundary. Removing repeated checks requires evidence that their inputs and trust context cannot change. Caching an authorization result is a separate security decision, not routine cleanup.

## Early exits and state-dependent behavior

A return can skip success bookkeeping or cleanup placed after the branch. Keep cleanup structurally guaranteed and preserve success/error events separately; do not move success-only work into `finally`. In loops, `continue`, `break`, and `return` have distinct effects. In async code, preserve cancellation and awaited cleanup behavior.

Strategy extraction must preserve state transitions, shared mutable data, and object lifetime. A handler chosen once is wrong if the old implementation read the current state before each operation. Keep state selection local unless a stable lifecycle or explicit transition mechanism justifies moving it.

## Primary references

- [Python compound statements](https://docs.python.org/3/reference/compound_stmts.html): first-match conditional execution and cleanup constructs.
- [Python expressions](https://docs.python.org/3/reference/expressions.html): Boolean operands, evaluation order, and dictionary construction.
- [Replace Conditional with Polymorphism](https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html): a refactoring option for meaningful behavioral variants, not a requirement to replace every branch.

The guidance and examples here are independently written. These links explain language semantics and established techniques; they are not bundled source material or a grant to redistribute linked works.
