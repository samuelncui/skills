"""Native graph prose and source-emission accounting, independent of graph-v1.

Inputs are already-rendered trusted TeX. This module neither escapes text nor
validates graph topology; use the discovered bilingual-pdf skill for text/math.
"""
import hashlib
import re
from collections import Counter, defaultdict
from string import Formatter

EMISSION_API_VERSION = 1
_RESERVED = "\x1c\x1d\x1e\x1f"
_MARKER = re.compile("\x1e([0-9]+):([oc])\x1f")
CALL_TEMPLATES = {
    "entry": "When needed: {condition} Go to {target}. Bring back {outputs}, then continue at {resume}.",
    "exit": "If you reached this result from {origin} through {target}, bring back {outputs} and continue at {resume}.",
}


def compose_call(kind, *, target, outputs, resume, condition=None, origin=None,
                 template=None, separator="; "):
    """Compose one authored call, preserving output order and exact resume text.

    Supply a localized trusted TeX template with every required placeholder
    exactly once. Calls are independent; this function selects no branch and
    never advances, merges, or deduplicates a resume or output.
    """
    if kind not in CALL_TEMPLATES:
        raise ValueError("Call kind must be entry or exit")
    if not isinstance(outputs, (list, tuple)) or not outputs:
        raise ValueError("Call outputs must be a nonempty ordered sequence")
    fields = {"target": target, "outputs": outputs, "resume": resume}
    fields["condition" if kind == "entry" else "origin"] = condition if kind == "entry" else origin
    if any(not isinstance(value, str) or not value for value in
           [target, resume, separator, *outputs, fields["condition" if kind == "entry" else "origin"]]):
        raise ValueError("Call fragments must be nonempty rendered strings")
    if (kind == "entry" and origin is not None) or (kind == "exit" and condition is not None):
        raise ValueError("Unexpected call fragment")
    template = CALL_TEMPLATES[kind] if template is None else template
    parsed = list(Formatter().parse(template))
    names = [name for _, name, _, _ in parsed if name is not None]
    if Counter(names) != Counter(fields.keys()) or any(spec or conversion for _, _, spec, conversion in parsed):
        raise ValueError("Template must contain each call placeholder exactly once")
    fields["outputs"] = separator.join(outputs)
    return template.format_map(fields)


def native_reference(key, step=None):
    """Emit canonical native node/resume references; existence is caller-validated."""
    if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", key):
        raise ValueError("Invalid native graph key")
    if step is None:
        return r"\StudyGraphReference{" + key + "}"
    if step != "completion_check" and (type(step) is not int or step < 1):
        raise ValueError("Step must be a positive integer or completion_check")
    return r"\StudyGraphResumeReference{" + key + "}{" + str(step) + "}"


def labeled_reference(reference, label, *, template="{reference} — {label}"):
    """Attach an already-rendered localized label without changing its anchor."""
    names = [name for _, name, spec, conversion in Formatter().parse(template)
             if name is not None]
    if Counter(names) != Counter(["reference", "label"]):
        raise ValueError("Reference template needs reference and label exactly once")
    if any(spec or conversion for _, _, spec, conversion in Formatter().parse(template)):
        raise ValueError("Reference template formatting is unsupported")
    return template.format_map({"reference": reference, "label": label})


class EmissionTrace:
    """Tag fields/units before formatting, then verify survival in final fragments.

    This is a one-document accounting helper, not a renderer. Each wrap call is
    one expected occurrence. Supply final fragments in intended document order.
    Use a fresh instance for each language edition or build.
    """

    def __init__(self):
        self._records = []
        self._fields = {}

    def _wrap(self, category, identity, language, rendered):
        if not all(isinstance(value, str) and value for value in (category, identity, language)):
            raise ValueError("Trace identity, category and language must be nonempty strings")
        if not isinstance(rendered, str):
            raise ValueError("Rendered trace content must be a string")
        token = str(len(self._records))
        self._records.append((category, identity, language))
        return "\x1e" + token + ":o\x1f" + rendered + "\x1e" + token + ":c\x1f"

    def field(self, identity, language, source, rendered):
        """Bind one source field to rendered content; repeat uses must match."""
        if not isinstance(source, str) or any(char in source for char in _RESERVED):
            raise ValueError("Invalid source text or reserved trace character")
        digest = hashlib.sha256(source.encode()).hexdigest()
        key = (identity, language)
        if key in self._fields and self._fields[key] != digest:
            raise ValueError("Source changed between emissions of the same field")
        self._fields[key] = digest
        return self._wrap("field", identity, language, rendered)

    def unit(self, category, identity, language, rendered):
        """Wrap a complete semantic unit inside its formatter's arguments."""
        if category == "field":
            raise ValueError("Use field() for source-bound fields")
        return self._wrap(category, identity, language, rendered)

    def finish(self, fragments, *, expected_fields, ordered_fields=False):
        """Return (cleaned fragments, report), rejecting lost/reordered emissions.

        expected_fields maps language IDs to source identities expected in this
        edition. Unit order is checked per category/language. Field occurrence tokens are
        counted; opt into field order only when construction follows reader order. No marker may cross a file.
        """
        expected = defaultdict(list)
        for token, (category, identity, language) in enumerate(self._records):
            expected[(category, language)].append(token)
        seen = defaultdict(list)
        cleaned = {}
        for name, content in fragments.items():
            stack = []
            def remove(match):
                token, boundary = int(match[1]), match[2]
                if token >= len(self._records):
                    raise ValueError("Unknown emission marker")
                category, identity, language = self._records[token]
                if boundary == "o":
                    stack.append(token)
                    seen[(category, language)].append(token)
                elif not stack or stack.pop() != token:
                    raise ValueError("Partial or crossing emission markers")
                return ""
            cleaned[name] = _MARKER.sub(remove, content)
            if stack or any(char in cleaned[name] for char in _RESERVED):
                raise ValueError("Partial or invalid emission marker")
        for key in expected.keys() | seen.keys():
            wanted, actual = expected[key], seen[key]
            if key[0] == "field" and not ordered_fields:
                matches = Counter(wanted) == Counter(actual)
            else:
                matches = wanted == actual
            if not matches:
                raise ValueError("Emission multiplicity/order differs")
        inventories = defaultdict(set)
        counts = Counter()
        for category, identity, language in self._records:
            if category == "field":
                inventories[language].add(identity)
                counts[(identity, language)] += 1
        requested = {lang: set(identities) for lang, identities in expected_fields.items()}
        actual = {lang: identities for lang, identities in inventories.items()}
        if {lang: ids for lang, ids in requested.items() if ids} != actual:
            raise ValueError("Source field coverage differs")
        report = {
            "fields": [{"identity": identity, "language": language, "source_sha256": digest,
                        "occurrences": counts[(identity, language)]}
                       for (identity, language), digest in self._fields.items()],
            "units": [{"category": category, "language": language, "identities":
                       [self._records[token][1] for token in tokens]}
                      for (category, language), tokens in seen.items() if category != "field"],
        }
        return cleaned, report
