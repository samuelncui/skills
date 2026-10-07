"""Deterministic, dependency-free minimum-span ordering of a directed graph.

optimize(keys, entry, edges, exact_limit=9, budget=60000) accepts a nonempty
ordered sequence of unique nonempty string keys and an iterable of directed
(source, target) pairs. Every endpoint, including a self-transition endpoint,
must be declared in keys. Repeated directed pairs are counted once and self
transitions are omitted. Reverse pairs remain distinct, with unit weight each.

The entry is fixed first. The baseline is entry followed by the other keys in
their supplied order; all returned orders contain every key exactly once.
For positions p, the objective is sum(abs(p[u] - p[v])) over the normalized
directed transitions. This measures ordinal span, not page distance or reader
effort. Equal scores are resolved lexicographically by original key rank, never
by key spelling, edge input order, randomness, or hash iteration order.

When len(keys) <= exact_limit, every entry-fixed permutation is evaluated and
the result is certified globally optimal for this objective and entry constraint.
exact_limit must be an integer from 1 through 9 inclusive; the hard bound limits
exact enumeration to at most 8! = 40320 scores. The positive integer budget
applies ONLY to the larger-graph heuristic, including its baseline evaluation.
It does not truncate or invalidate an exact search.

The heuristic repeatedly selects the best rank-tie-broken candidate from one
sweep of non-entry swaps and relocations. It stops on a sweep with no improvement
or budget exhaustion, retaining the best evaluated result including the baseline.
It is deterministic and never worsens the baseline score; it is not a global
optimality certificate, even if the result happens to be optimal.

The JSON-safe report includes baseline/order, normalized directed edges, scores,
evaluation count, method, exact/certified_optimal flags, algorithm_version and
config. Evaluations count objective calls, including repeated candidates in the
heuristic. Exact search takes O((n-1)! * (n+m)) time; the heuristic uses at most
budget calls of O(n+m) each. Search memory is O(n+m), apart from the returned
report and input normalization. There is no I/O, randomness or input mutation.
"""

from collections.abc import Iterable, Sequence
from itertools import permutations

ALGORITHM_VERSION = "1"
MAX_EXACT_LIMIT = 9


def _validated(keys, entry, edges, exact_limit, budget):
    if isinstance(keys, (str, bytes)) or not isinstance(keys, Sequence):
        raise TypeError("keys must be an ordered sequence of unique strings")
    keys = tuple(keys)
    if not keys:
        raise ValueError("keys must not be empty")
    if any(not isinstance(key, str) or not key for key in keys):
        raise ValueError("keys must contain nonempty strings")
    if len(set(keys)) != len(keys):
        raise ValueError("keys must be unique")
    if not isinstance(entry, str) or entry not in keys:
        raise ValueError("entry must be a declared key")
    if isinstance(exact_limit, bool) or not isinstance(exact_limit, int):
        raise TypeError("exact_limit must be an integer")
    if not 1 <= exact_limit <= MAX_EXACT_LIMIT:
        raise ValueError("exact_limit must be between 1 and 9")
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise TypeError("budget must be an integer")
    if budget < 1:
        raise ValueError("budget must be positive")
    if isinstance(edges, (str, bytes, dict)) or not isinstance(edges, Iterable):
        raise TypeError("edges must be an iterable of directed pairs")

    ranks = {key: rank for rank, key in enumerate(keys)}
    normalized = set()
    for edge in edges:
        if (
            isinstance(edge, (str, bytes))
            or not isinstance(edge, Sequence)
            or len(edge) != 2
        ):
            raise ValueError("each edge must be a two-item directed pair")
        source, target = edge
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in ranks
            or target not in ranks
        ):
            raise ValueError("every edge endpoint must be a declared key")
        if source != target:
            normalized.add((ranks[source], ranks[target]))
    return keys, ranks[entry], tuple(sorted(normalized))


def _score(order, edges):
    positions = [0] * len(order)
    for position, rank in enumerate(order):
        positions[rank] = position
    return sum(abs(positions[source] - positions[target]) for source, target in edges)


def _neighbors(order):
    """Yield a bounded-memory, stable sweep; never relocate the entry."""
    for first in range(1, len(order)):
        for second in range(first + 1, len(order)):
            candidate = list(order)
            candidate[first], candidate[second] = candidate[second], candidate[first]
            yield tuple(candidate)
    for source in range(1, len(order)):
        for target in range(1, len(order)):
            if source == target:
                continue
            candidate = list(order)
            candidate.insert(target, candidate.pop(source))
            yield tuple(candidate)


def optimize(keys, entry, edges, exact_limit=9, budget=60000):
    """Return an auditable ordering report; see the module contract for bounds.

    Invalid container/configuration types raise TypeError; malformed key sets,
    edges, unknown endpoints, and out-of-range configuration raise ValueError.
    Only explicit finite input collections/iterables should be supplied.
    """
    keys, entry_rank, edges = _validated(keys, entry, edges, exact_limit, budget)
    baseline = (entry_rank,) + tuple(rank for rank in range(len(keys)) if rank != entry_rank)
    baseline_score = _score(baseline, edges)
    best_order, best_score = baseline, baseline_score
    evaluations = 1
    exact = len(keys) <= exact_limit

    if exact:
        for suffix in permutations(baseline[1:]):
            candidate = (entry_rank,) + suffix
            if candidate == baseline:  # Its score is already counted.
                continue
            score = _score(candidate, edges)
            evaluations += 1
            if (score, candidate) < (best_score, best_order):
                best_order, best_score = candidate, score
    else:
        while evaluations < budget:
            sweep_order, sweep_score = best_order, best_score
            for candidate in _neighbors(best_order):
                if evaluations >= budget:
                    break
                score = _score(candidate, edges)
                evaluations += 1
                if (score, candidate) < (sweep_score, sweep_order):
                    sweep_order, sweep_score = candidate, score
            if sweep_order == best_order:
                break
            best_order, best_score = sweep_order, sweep_score

    return {
        "algorithm_version": ALGORITHM_VERSION,
        "baseline": [keys[rank] for rank in baseline],
        "order": [keys[rank] for rank in best_order],
        "edges": [[keys[source], keys[target]] for source, target in edges],
        "baseline_score": baseline_score,
        "score": best_score,
        "evaluations": evaluations,
        "exact": exact,
        "certified_optimal": exact,
        "method": "exhaustive" if exact else "bounded-local-search",
        "config": {
            "exact_limit": exact_limit,
            "max_exact_limit": MAX_EXACT_LIMIT,
            "budget": budget,
        },
    }
