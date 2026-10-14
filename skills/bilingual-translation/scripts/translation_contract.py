#!/usr/bin/env python3
"""Semantic exchange validation. Checks structure/currency, never meaning."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

_SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas" /
                      "translation.schema.json").read_text(encoding="utf-8"))


def source_digest(text: str) -> str:
    """Hash exact source UTF-8 bytes without normalization."""
    if not isinstance(text, str):
        raise TypeError("source must be a string")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _schema_errors(value, schema, path="$"):
    """Evaluate only the documented, bundled schema keyword subset (stdlib)."""
    if "$ref" in schema:
        schema = _SCHEMA["$defs"][schema["$ref"].removeprefix("#/$defs/")]
    errors = []
    for mode in ("anyOf", "oneOf"):
        if mode in schema:
            branches = [_schema_errors(value, branch, path) for branch in schema[mode]]
            matches = sum(not branch for branch in branches)
            if matches == 0:
                best = min(branches, key=len)
                return [f"{path}: no supported {mode} shape; " + "; ".join(best)]
            if mode == "oneOf" and matches != 1:
                return [f"{path}: ambiguous oneOf shape"]
            return []
    if "type" in schema:
        checks = {"object": isinstance(value, dict), "array": isinstance(value, list),
                  "string": isinstance(value, str), "integer": type(value) is int,
                  "boolean": type(value) is bool, "null": value is None}
        if not checks[schema["type"]]:
            return [f"{path}: expected {schema['type']}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: text must not be empty")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: invalid text or identifier")
    if type(value) is int:
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            errors.append(f"{path}: value outside supported range")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: too few items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(_schema_errors(item, schema["items"], f"{path}[{index}]"))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: missing required field")
        for key, item in value.items():
            if key not in props:
                if schema.get("additionalProperties") is False:
                    errors.append(f"{path}.{key}: unsupported field")
            else:
                errors.extend(_schema_errors(item, props[key], f"{path}.{key}"))
    return errors


def validate_document(data, require_ready=False) -> list[str]:
    """Return structural, hash, state and coverage errors; do not mutate input."""
    errors = _schema_errors(data, _SCHEMA)
    if errors:
        return errors
    units = {}
    for index, unit in enumerate(data["units"]):
        uid = unit["id"]
        if uid in units:
            errors.append(f"units[{index}].id: duplicate ID {uid!r}")
        units[uid] = unit
        current = source_digest(unit["source"])
        if current != unit["source_hash"]:
            errors.append(f"unit {uid}: source_hash does not match exact source; regenerate the exchange from the current master")
        target, status, previous = unit["target"], unit["status"], unit["target_source_hash"]
        if target is None:
            if status != "untranslated" or previous is not None:
                errors.append(f"unit {uid}: null target requires untranslated and null target_source_hash")
        else:
            if status == "untranslated":
                errors.append(f"unit {uid}: nonempty target cannot be untranslated")
            if status in ("draft", "reviewed") and previous != current:
                errors.append(f"unit {uid}: target is stale; status must be needs_review")
        if require_ready and (target is None or status != "reviewed" or previous != current):
            errors.append(f"unit {uid}: not ready; current target requires completed review")

    uses = {uid: 0 for uid in units}

    def use(uid, kinds, location):
        if uid not in units:
            errors.append(f"{location}: missing unit {uid!r}")
            return
        uses[uid] += 1
        if units[uid]["kind"] not in kinds:
            errors.append(f"{location}: unit {uid!r} requires kind {' or '.join(kinds)}")

    for index, block in enumerate(data["blocks"]):
        path, kind = f"blocks[{index}]", block["type"]
        if kind == "heading":
            kinds = ("heading", "title") if block["level"] == 1 else ("heading",)
            use(block["unit"], kinds, path)
        elif kind == "paragraph":
            use(block["unit"], ("paragraph",), path)
        elif kind == "list":
            for item, uid in enumerate(block["items"]):
                use(uid, ("list_item",), f"{path}.items[{item}]")
        elif kind == "table":
            width = len(block["headers"])
            for column, uid in enumerate(block["headers"]):
                use(uid, ("table_cell",), f"{path}.headers[{column}]")
            for rownum, row in enumerate(block["rows"]):
                if len(row) != width:
                    errors.append(f"{path}.rows[{rownum}]: expected {width} cells")
                for column, uid in enumerate(row):
                    use(uid, ("table_cell",), f"{path}.rows[{rownum}][{column}]")
            if "caption" in block:
                use(block["caption"], ("caption",), f"{path}.caption")
        elif kind == "figure":
            use(block["caption"], ("caption",), f"{path}.caption")
            use(block["alt"], ("alt_text",), f"{path}.alt")
    for uid, count in uses.items():
        if count != 1:
            errors.append(f"unit {uid}: expected exactly one structural use, found {count}")
    return errors


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError(f"non-finite JSON value {value}")



def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="check structure, source hashes and currency")
    validate.add_argument("data", type=Path)
    validate.add_argument("--ready", action="store_true", help="require recorded current reviews")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.data.read_text(encoding="utf-8"),
                          object_pairs_hook=_object, parse_constant=_nonfinite)
        errors = validate_document(data, args.ready)
        if errors:
            raise ValueError("\n".join(errors))
        print("Valid structure and current review records." if args.ready else
              "Valid structure and source/target state.")
        print("Semantic accuracy is not checked by this command.")
        return 0
    except (OSError, ValueError, TypeError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
