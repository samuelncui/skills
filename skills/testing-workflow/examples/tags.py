"""Small teaching implementation; no third-party dependencies."""


def normalize_tag(value):
    """Trim outer whitespace and case-fold a nonempty string.

    Preserve internal whitespace. Reject non-strings with TypeError and empty
    normalized strings with ValueError. This is a text label, not a secure ID.
    """
    if not isinstance(value, str):
        raise TypeError("tag must be a string")
    normalized = value.strip().casefold()
    if not normalized:
        raise ValueError("tag must not be empty")
    return normalized
