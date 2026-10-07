# Native graph emission helpers, API 1

Use scripts/graph_emission.py for trusted native adapters that need inline
helper-call prose, precise native references or source-field survival checks.
It is independent of the graph-v1 importer: no new schema, call-group behavior,
branch selection or graph-validation bypass is introduced. Keep graph-v1 inputs
on the documented structured route. This helper is also usable without a graph
JSON file.

Discover installed study-notes and bilingual-pdf separately. Load each script
by its discovered absolute path with importlib.util.spec_from_file_location;
never infer a sibling installation. Check EMISSION_API_VERSION == 1 and the
bilingual renderer's BOUND_TEXT_API_VERSION == 1. Read the installed
bilingual-pdf reference references/bound-text.md for escaping, math, exact
source runs and trusted-native boundaries.

## References and authored call sentences

native_reference(key, step=None) emits StudyGraphReference or
StudyGraphResumeReference. step is a positive integer or completion_check.
The caller verifies target/step existence; this utility validates syntax only.
Generated native references retain canonical native numbers/pages/anchors.

For an existing trusted native shell, pass that shell's already-rendered
reference to labeled_reference(reference, label, template=...). The default
template is "{reference} — {label}". Localized templates must use each named
placeholder exactly once with no conversions or format specifications. Labels
are already-rendered TeX. This does not declare, rename or resolve an anchor.

compose_call(kind, *, target, outputs, resume, condition=None, origin=None,
template=None, separator="; ") returns one sentence. kind is entry or exit;
outputs is a nonempty ordered list/tuple of rendered fragments.

- Entry requires condition, target, outputs and resume.
- Exit requires origin, target, outputs and resume, making the caller explicit.
- Built-in templates are English. Supply a reviewed localized TeX template for
  another language, with each required placeholder exactly once. Double braces
  in literal template TeX, following Python format-string conventions.
- Each supplied fragment is already escaped/rendered by its owner. Templates
  and native fragments are trusted executable TeX, not untrusted source data.
- A call does not choose among other calls, advance a resume step, sort outputs
  or suppress ordinary continuation. Preserve the author's call sequence and
  conditions. A same-step resume remains the same exact reference. The stricter
  graph-v1 importer continues to enforce its own later-step restrictions.
- Translation review and source-to-call mapping remain the caller's job.

## Verify actual formatted fragments

Wrap each source field with EmissionTrace.field(identity, language, source,
rendered), and each complete visible component with
EmissionTrace.unit(category, identity, language, rendered). Put unit markers
inside formatter arguments, so dropping a whole component remains observable
even if its source field also appears elsewhere.

After formatting, call finish(fragments, expected_fields=..., ordered_fields=False). fragments is an
insertion-ordered mapping of output filenames to final TeX strings in document
order. expected_fields maps each selected language to its expected source
identities. The result is (cleaned_fragments, report); write only cleaned output.

```python
import importlib.util
import os
from pathlib import Path

path = Path(os.environ["STUDY_NOTES_SKILL"]) / "scripts/graph_emission.py"
spec = importlib.util.spec_from_file_location("installed_emission", path)
emission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emission)
assert emission.EMISSION_API_VERSION == 1

trace = emission.EmissionTrace()
field = trace.field("/steps/0", "en", "Keep the box.", "Keep the box.")
paragraph = trace.unit("paragraph", "pack", "en", field)
cleaned, report = trace.finish(
    {"body.tex": r"\par " + paragraph},
    expected_fields={"en": ["/steps/0"]},
)
assert cleaned["body.tex"] == r"\par Keep the box."
assert report["fields"][0]["occurrences"] == 1

```

Trace semantics:

- Every wrap call is one expected occurrence. Repeated field identities must
  retain the same exact UTF-8 source hash. Reuse a source through another field()
  call, rather than copying an already-tagged string.
- Unit order is checked independently per category/language against wrap-call
  order. Tag units in intended reader order. Distinct nesting roles need distinct
  categories; wrapping an outer unit after its inner units with the same category
  would intentionally disagree with their final reading order.
- Field occurrences use exact token counts by default: a formatter may construct
  a title after its body but output that title first. Set ordered_fields=True
  when field construction follows reader order and field-order verification is
  also required. This option never relaxes semantic-unit ordering.
- Markers are balanced, occurrence-specific and confined to one output file.
  Missing, duplicated, reordered, crossing, partial and unknown markers fail.
  Reserved U+001C–U+001F source characters fail. No trace marker is delivered.
- Expected inventory catches a never-requested source field. A selected edition
  lists only its selected language(s); paired editions list both. Required
  fields, occurrences and unit order are separate checks.
- Reports contain source hashes/counts and surviving unit identities. They
  prove survival of tagged spans through the formatter, not preservation of
  arbitrary edits inside a marked span, language equivalence, factual validity,
  visible glyphs or actual PDF links. Inspect rendered PDF pixels/text/links
  separately. Do not claim a migration complete from trace coverage alone.
- Use a fresh trace for each document/edition. No global registry, callback
  framework or dependency download is involved.

## Maintainer verification

From a clean checkout with root requirements installed:

```sh
python -m unittest discover -s tests -p 'test_graph_emission.py' -v
python -m unittest discover -s tests -p 'test_*graph*.py' -v
python tools/check_package.py
python tests/graph_emission_render.py --output .local/graph-emission-render

```

Neutral tests cover source/hash/span errors, literal/scientific escaping,
native trust, precise same-step references, ordered independent calls,
caller-qualified exits, paired/selected fields and dropped/duplicated/reordered
units. An isolated Python subprocess loads separately installed skills without
repository import access. These checks do not replace a downstream shell's
visual/link equivalence acceptance.
