"""Run all fixtures with: python3 -B -m unittest discover -s examples -v."""
import unittest

from tags import normalize_tag


class NormalizeTagTests(unittest.TestCase):
    def test_normalization_and_idempotence(self):
        cases = (
            ("  Alpha  ", "alpha"),
            ("A B", "a b"),
            ("\tMixed\n", "mixed"),
        )
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_tag(raw), expected)
                self.assertEqual(normalize_tag(expected), expected)

    def test_unicode_casefold_regression(self):
        # Replacing casefold() with lower() reproduces this defect.
        self.assertEqual(normalize_tag("  Straße  "), "strasse")

    def test_rejected_inputs(self):
        cases = (
            ("", ValueError),
            (" \t\n", ValueError),
            (None, TypeError),
            (7, TypeError),
        )
        for raw, error in cases:
            with self.subTest(raw=raw):
                with self.assertRaises(error):
                    normalize_tag(raw)


if __name__ == "__main__":
    unittest.main()
