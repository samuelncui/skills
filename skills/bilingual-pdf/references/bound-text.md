# Source-bound native text API 1

Use this additive Python API when a trusted native authoring adapter has exact
source text, reviewed mathematical spans and resolved reference fragments.
Article JSON and graph-v1 retain their existing, separate contracts. This helper
does not translate, infer mathematics or fetch sources.

Discover the installed bilingual-pdf skill through the host and resolve its
directory explicitly. Load its script by that path; no repository or sibling
skill import is needed:

```python
import importlib.util
import os
from pathlib import Path

path = Path(os.environ["BILINGUAL_PDF_SKILL"]) / "scripts/bilingual_pdf.py"
spec = importlib.util.spec_from_file_location("installed_pdf", path)
pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdf)
assert pdf.BOUND_TEXT_API_VERSION == 1

source = "Keep x^2 & y."
tex = pdf.render_bound_text(source, runs=[
    {"kind": "text", "source": "Keep "},
    {"kind": "math", "source": "x^2", "tex": "x^2"},
    {"kind": "text", "source": " & y."},
])
assert tex == r"Keep \(x^2\) \& y."

```

## Inputs and policies

render_bound_text(text, *, runs=None, references=(), language="en",
text_policy="literal", source_sha256=None, trusted_native=False) returns a
rendered TeX string. Escape it only once.

- Source is literal Unicode text, including empty text. Control and embedded
  directional-control restrictions match the renderer. Offsets count Unicode
  code points, not encoded bytes.
- Runs, when supplied, are a list covering the complete source in order.
  Each nonempty text run has exactly kind/source. Each math run additionally
  has tex. The concatenated source strings must reconstruct the source exactly.
- Restricted math uses the renderer's existing equation policy and additionally
  checks brace balance. This API adds no math commands to that policy.
- References have exactly start/end/text/tex. The half-open source span must
  equal text. tex is a pre-resolved native reference, not a source identifier
  to resolve automatically. References may occur within text runs, but no two
  reference/math spans may overlap. Adjacent spans are allowed.
- The default literal policy uses canonical language_text escaping and newline
  handling. The opt-in scientific-breaks policy preserves source whitespace,
  renders ← → ∂ ∝ ≈ ⊙ ≤ ≥ ≠ as fixed native math symbols, permits breaks after
  arrows and adds allowbreak after slash/comma/semicolon. It applies only to
  literal source slices, never to supplied math/reference TeX. Existing renderer
  defaults are unchanged.
- A supplied source_sha256 must match SHA-256 of the exact UTF-8 source.
  Native references or math beyond the restricted policy require
  trusted_native=True and that matching hash. Both are explicit acknowledgments
  of executable native input; hashes detect drift, not malicious TeX. Use
  reviewed native fragments and suitable isolation. This does not relax a
  structured importer or claim to validate graph topology.

For example, compute hashlib.sha256(source.encode()).hexdigest(), then pass it
with trusted_native=True and a reference such as
{"start": 0, "end": 3, "text": "Box", "tex": r"\StudyGraphReference{pack-box}"}.
The graph-owning skill or adapter verifies target existence and constructs the
native reference; bilingual-pdf only merges its exact source span.

The caller retains source identity, translation/context review, and input-file
provenance. There is no source registry, automatic language conversion or
persistent state. Pin the tested skill revision with downstream projects.
