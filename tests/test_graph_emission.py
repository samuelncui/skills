"""Neutral public contracts for bound native graph emission."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pdf = load("bound_pdf", ROOT / "skills/bilingual-pdf/scripts/bilingual_pdf.py")
emission = load("graph_emission", ROOT / "skills/study-notes/scripts/graph_emission.py")


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class BoundTextTests(unittest.TestCase):
    def test_source_reconstruction_and_literal_escaping(self):
        text = "Price $2 & x^2."
        runs = [{"kind": "text", "source": "Price $2 & "},
                {"kind": "math", "source": "x^2", "tex": "x^2"},
                {"kind": "text", "source": "."}]
        original = copy.deepcopy(runs)
        self.assertEqual(pdf.render_bound_text(text, runs=runs, source_sha256=sha(text)),
                         r"Price \$2 &".replace("&", r"\&") + r" \(x^2\).")
        self.assertEqual(runs, original)
        self.assertEqual(pdf.render_bound_text(""), "")
        self.assertEqual(pdf.render_bound_text("A\nB"), "A B")

    def test_scientific_policy_is_explicit_and_keeps_existing_defaults(self):
        text = "a→b/c, d; x≤y & z"
        self.assertEqual(pdf.render_bound_text(text), "a→b/c, d; x≤y \\& z")
        self.assertEqual(pdf.render_bound_text(text, text_policy="scientific-breaks"),
                         r"a\ensuremath{\rightarrow}\allowbreak{}b/\allowbreak{}c,\allowbreak{} d;\allowbreak{} x\ensuremath{\leq}y \& z")
        self.assertEqual(pdf.language_text(text, "en"), "a→b/c, d; x≤y \\& z")
        for value in ("invented", None):
            with self.assertRaises(ValueError):
                pdf.render_bound_text(text, text_policy=value)

    def test_resolved_reference_and_adjacent_math_keep_unicode_offsets(self):
        text = "Go ✓x."
        runs = [{"kind": "text", "source": "Go ✓"},
                {"kind": "math", "source": "x", "tex": "x"},
                {"kind": "text", "source": "."}]
        refs = [{"start": 3, "end": 4, "text": "✓", "tex": r"\StudyGraphReference{finish}"}]
        self.assertEqual(pdf.render_bound_text(text, runs=runs, references=refs,
                         trusted_native=True, source_sha256=sha(text)),
                         r"Go \StudyGraphReference{finish}\(x\).")
        self.assertEqual(text, "Go ✓x.")

    def test_stale_hash_reconstruction_and_span_errors(self):
        for kwargs in (
            {"source_sha256": "0" * 64},
            {"runs": [{"kind": "text", "source": "wrong"}]},
            {"runs": [{"kind": "text", "source": "a"}]},
            {"runs": [{"kind": "text", "source": "ab", "unknown": True}]},
            {"runs": [{"kind": "text", "source": ""}]},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                pdf.render_bound_text("ab", **kwargs)
        for reference in (
            {"start": True, "end": 1, "text": "a", "tex": "A"},
            {"start": 0, "end": 2, "text": "a", "tex": "A"},
            {"start": -1, "end": 1, "text": "a", "tex": "A"},
            {"start": 0, "end": 1, "text": "a", "tex": ""},
        ):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                pdf.render_bound_text("ab", references=[reference], trusted_native=True,
                                      source_sha256=sha("ab"))

    def test_reference_overlap_with_math_or_reference(self):
        ref = {"start": 0, "end": 1, "text": "x", "tex": "REF"}
        for runs, refs in (([{"kind": "math", "source": "x", "tex": "x"}], [ref]),
                           (None, [ref, ref])):
            with self.assertRaisesRegex(ValueError, "overlap"):
                pdf.render_bound_text("x", runs=runs, references=refs,
                                      trusted_native=True, source_sha256=sha("x"))

    def test_native_trust_is_explicit_hash_bound_and_not_a_sanitizer(self):
        ref = {"start": 0, "end": 1, "text": "x", "tex": r"\Reference{x}"}
        with self.assertRaisesRegex(ValueError, "trusted_native"):
            pdf.render_bound_text("x", references=[ref])
        with self.assertRaisesRegex(ValueError, "exact source hash"):
            pdf.render_bound_text("x", trusted_native=True)
        run = [{"kind": "math", "source": "x", "tex": r"\operatorname{value}(x)"}]
        with self.assertRaisesRegex(ValueError, "allowlist"):
            pdf.render_bound_text("x", runs=run)
        self.assertEqual(pdf.render_bound_text("x", runs=run, trusted_native=True,
                         source_sha256=sha("x")), r"\(\operatorname{value}(x)\)")
        for tex in (r"\input{secret}", r"\frac{1}{2", "x}"):
            with self.subTest(tex=tex), self.assertRaises(ValueError):
                pdf.render_bound_text("x", runs=[{"kind": "math", "source": "x", "tex": tex}])

    def test_controls_and_directions_are_rejected(self):
        for text in ("a\x1eb", "a\u202eb"):
            with self.assertRaises(ValueError):
                pdf.render_bound_text(text)


class GraphEmissionTests(unittest.TestCase):
    def test_native_references_and_labeled_custom_shell_reference(self):
        self.assertEqual(emission.native_reference("pack-box"), r"\StudyGraphReference{pack-box}")
        self.assertEqual(emission.native_reference("pack-box", 2),
                         r"\StudyGraphResumeReference{pack-box}{2}")
        self.assertEqual(emission.native_reference("pack-box", "completion_check"),
                         r"\StudyGraphResumeReference{pack-box}{completion_check}")
        self.assertEqual(emission.labeled_reference(r"\Anchor{box:2}{N3}", "2. Check"),
                         r"\Anchor{box:2}{N3} — 2. Check")
        for key, step in (("a}bad", None), ("box", True), ("box", 0), ("box", "next")):
            with self.assertRaises(ValueError):
                emission.native_reference(key, step)

    def test_calls_preserve_order_and_exact_same_step_resume(self):
        resume = emission.native_reference("pack-box", 2)
        first = emission.compose_call("entry", condition="If material is missing.",
                    target="N4", outputs=["paper", "padding"], resume=resume)
        second = emission.compose_call("entry", condition="If a label is missing.",
                    target="N5", outputs=["label"], resume=resume)
        self.assertEqual(first, "When needed: If material is missing. Go to N4. Bring back paper; padding, then continue at " + resume + ".")
        self.assertLess((first + second).index("paper; padding"), (first + second).index("label"))
        self.assertEqual(first.count(resume), 1)
        self.assertEqual(second.count(resume), 1)
        output = emission.compose_call("exit", origin="N3 step 2", target="N4",
                                      outputs=["paper", "padding"], resume=resume)
        self.assertEqual(output, "If you reached this result from N3 step 2 through N4, bring back paper; padding and continue at " + resume + ".")

    def test_localized_template_and_invalid_placeholders(self):
        self.assertEqual(emission.compose_call("entry", condition="Ready", target="N2",
                         outputs=["A", "B"], resume="N1 step 1", separator=" / ",
                         template="{condition}: {target}; {outputs}; {resume}"),
                         "Ready: N2; A / B; N1 step 1")
        for template in ("{target}", "{condition} {target} {outputs} {resume} {resume}",
                         "{condition} {target.x} {outputs} {resume}",
                         "{condition} {target!r} {outputs} {resume}"):
            with self.assertRaises(ValueError):
                emission.compose_call("entry", condition="Ready", target="N2",
                                      outputs=["A"], resume="N1", template=template)

    def trace_fixture(self):
        trace = emission.EmissionTrace()
        one = trace.unit("paragraph", "first", "en",
                        trace.field("/first", "en", "A", "A"))
        two = trace.unit("paragraph", "second", "en",
                        trace.field("/second", "en", "B", "B"))
        return trace, one, two

    def test_field_and_unit_survival_in_final_fragments(self):
        trace, one, two = self.trace_fixture()
        clean, report = trace.finish({"front": one, "body": two},
                                    expected_fields={"en": ["/first", "/second"]})
        self.assertEqual(clean, {"front": "A", "body": "B"})
        self.assertEqual(report["fields"][0], {"identity": "/first", "language": "en",
                         "source_sha256": sha("A"), "occurrences": 1})
        self.assertEqual(report["units"][0]["identities"], ["first", "second"])

    def test_deleted_duplicated_reordered_partial_units_fail(self):
        for operation in ("drop", "duplicate", "reorder", "partial", "cross-file"):
            trace, one, two = self.trace_fixture()
            content = {"drop": one, "duplicate": one + two + two,
                       "reorder": two + one, "partial": (one + two)[:-1]}
            fragments = {"body": content.get(operation, one + two)}
            if operation == "cross-file":
                fragments = {"a": one[:10], "b": one[10:] + two}
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                trace.finish(fragments, expected_fields={"en": ["/first", "/second"]})

    def test_same_field_elsewhere_does_not_hide_dropped_semantic_unit(self):
        trace = emission.EmissionTrace()
        first = trace.unit("paragraph", "first", "en", trace.field("/x", "en", "X", "X"))
        second = trace.unit("paragraph", "second", "en", trace.field("/x", "en", "X", "X"))
        with self.assertRaises(ValueError):
            trace.finish({"body": first}, expected_fields={"en": ["/x"]})
        clean, report = trace.finish({"body": first + second}, expected_fields={"en": ["/x"]})
        self.assertEqual(clean["body"], "XX")
        self.assertEqual(report["fields"][0]["occurrences"], 2)

    def test_field_construction_order_can_differ_from_reader_order(self):
        trace = emission.EmissionTrace()
        body = trace.field("/body", "en", "Body", "Body")
        title = trace.field("/title", "en", "Title", "Title")
        content = trace.unit("paragraph", "one", "en", title + body)
        clean, report = trace.finish({"body": content},
                                    expected_fields={"en": ["/title", "/body"]})
        self.assertEqual(clean["body"], "TitleBody")
        self.assertEqual(len(report["fields"]), 2)
        with self.assertRaisesRegex(ValueError, "order"):
            trace.finish({"body": content}, expected_fields={"en": ["/title", "/body"]},
                         ordered_fields=True)

    def test_paired_and_selected_edition_coverage(self):
        trace = emission.EmissionTrace()
        en = trace.field("/x", "en", "Box", "Box")
        fr = trace.field("/x", "fr", "Boîte", "Boîte")
        clean, report = trace.finish({"body": en + fr}, expected_fields={"en": ["/x"], "fr": ["/x"]})
        self.assertEqual(len(report["fields"]), 2)
        self.assertEqual(clean["body"], "BoxBoîte")
        for inventories in ({"en": ["/x"]}, {"en": ["/x", "/y"], "fr": ["/x"]}):
            with self.assertRaisesRegex(ValueError, "coverage"):
                trace.finish({"body": en + fr}, expected_fields=inventories)
        with self.assertRaisesRegex(ValueError, "changed"):
            trace.field("/x", "en", "Changed", "Changed")
        with self.assertRaisesRegex(ValueError, "reserved"):
            trace.field("/bad", "en", "\x1f", "bad")

    def test_independent_installed_skills_without_repository_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = root / "render-kit", root / "other" / "learning-kit"
            shutil.copytree(ROOT / "skills/bilingual-pdf", a, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT / "skills/study-notes", b, ignore=shutil.ignore_patterns("__pycache__"))
            script = """
import importlib.util, json, sys
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
pdf = load('renderer', sys.argv[1])
graph = load('emission', sys.argv[2])
source = 'Keep A & B'
rendered = pdf.render_bound_text(source)
trace = graph.EmissionTrace()
text = trace.field('/action', 'en', source, rendered)
clean, report = trace.finish({'body': text}, expected_fields={'en': ['/action']})
assert clean['body'] == r'Keep A \\& B'
assert graph.native_reference('pack-box', 1) == r'\\StudyGraphResumeReference{pack-box}{1}'
print(json.dumps({'fields': len(report['fields']), 'bound_api': pdf.BOUND_TEXT_API_VERSION}))
"""
            result = subprocess.run([sys.executable, "-I", "-c", script,
                        str(a / "scripts/bilingual_pdf.py"), str(b / "scripts/graph_emission.py")],
                        cwd=root, text=True, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"fields": 1, "bound_api": 1})


if __name__ == "__main__":
    unittest.main()
