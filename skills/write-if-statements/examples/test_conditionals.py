"""Executable contracts: explicit outcomes plus observable effect traces."""
import unittest
from contextlib import contextmanager

from conditionals import (
    classify_branch, classify_rules, deliver_guarded, deliver_nested,
    route_branch, route_map, should_retry,
)


class ConditionalContracts(unittest.TestCase):
    def test_guards_preserve_result_and_cleanup(self):
        for impl in (deliver_nested, deliver_guarded):
            for ready_value in (False, True):
                with self.subTest(impl=impl.__name__, ready=ready_value):
                    events = []

                    @contextmanager
                    def channel():
                        events.append("open")
                        try:
                            yield "channel"
                        finally:
                            events.append("close")

                    def ready():
                        events.append("ready")
                        return ready_value

                    def send(target):
                        events.append(("send", target))

                    self.assertEqual(
                        impl(channel, ready, send),
                        "sent" if ready_value else "idle",
                    )
                    expected = ["open", "ready"]
                    if ready_value:
                        expected.append(("send", "channel"))
                    self.assertEqual(events, expected + ["close"])

    def test_guards_preserve_exception_and_cleanup(self):
        for impl in (deliver_nested, deliver_guarded):
            for failing_step in ("ready", "send"):
                with self.subTest(impl=impl.__name__, step=failing_step):
                    events = []
                    failure = RuntimeError("fixture failure")

                    @contextmanager
                    def channel():
                        events.append("open")
                        try:
                            yield "channel"
                        finally:
                            events.append("close")

                    def ready():
                        events.append("ready")
                        if failing_step == "ready":
                            raise failure
                        return True

                    def send(target):
                        events.append("send")
                        raise failure

                    with self.assertRaises(RuntimeError) as caught:
                        impl(channel, ready, send)
                    self.assertIs(caught.exception, failure)
                    self.assertEqual(
                        events,
                        ["open", "ready", "close"] if failing_step == "ready"
                        else ["open", "ready", "send", "close"],
                    )

    def test_ordered_overlap_boundaries_and_no_match(self):
        cases = (
            (-1, "negative", [10, 0]),
            (0, "ordinary", [10, 0]),
            (9, "ordinary", [10, 0]),
            (10, "high", [10]),
            (11, "high", [10]),
        )
        for impl in (classify_branch, classify_rules):
            for value, expected, calls in cases:
                with self.subTest(impl=impl.__name__, value=value):
                    events = []

                    def at_least(number, threshold):
                        events.append(threshold)
                        return number >= threshold

                    self.assertEqual(impl(value, at_least), expected)
                    self.assertEqual(events, calls)

    def test_skipped_predicate_cannot_raise(self):
        for impl in (classify_branch, classify_rules):
            with self.subTest(impl=impl.__name__):
                def at_least(number, threshold):
                    if threshold == 0:
                        raise RuntimeError("must remain unevaluated")
                    return number >= threshold

                self.assertEqual(impl(10, at_least), "high")

    def test_keyed_dispatch_calls_exactly_one_handler(self):
        for impl in (route_branch, route_map):
            for kind, expected in (
                ("text", "text"), ("binary", "binary"), ("unknown", "fallback"),
            ):
                with self.subTest(impl=impl.__name__, kind=kind):
                    events = []
                    token = object()

                    def handler(label):
                        def run():
                            events.append(label)
                            if label != expected:
                                raise AssertionError("unselected handler executed")
                            return token
                        return run

                    result = impl(kind, handler("text"), handler("binary"),
                                  handler("fallback"))
                    self.assertIs(result, token)
                    self.assertEqual(events, [expected])

    def test_dispatch_preserves_selected_exception(self):
        for impl in (route_branch, route_map):
            with self.subTest(impl=impl.__name__):
                failure = ValueError("bad payload")

                def fail():
                    raise failure

                def forbidden():
                    self.fail("fallback or another handler must not run")

                with self.assertRaises(ValueError) as caught:
                    impl("text", fail, forbidden, forbidden)
                self.assertIs(caught.exception, failure)

    def test_simple_if_is_clear_and_short_circuits(self):
        for transient, attempts, expected in (
            (False, 2, False), (True, 0, False),
            (True, -1, False), (True, 1, True),
        ):
            with self.subTest(transient=transient, attempts=attempts):
                self.assertIs(should_retry(transient, attempts), expected)

        class MustNotCompare:
            def __gt__(self, other):
                raise AssertionError("comparison should be skipped")

        self.assertFalse(should_retry(False, MustNotCompare()))


if __name__ == "__main__":
    unittest.main()
