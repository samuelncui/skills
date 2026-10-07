#!/usr/bin/env python3
"""Optional v1 exchange validation. Checks structure/currency, never meaning."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
import re
import sys

CONTRACT_VERSION = 1
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
            errors.append(f"unit {uid}: source_hash does not match exact source; run sync")
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


def sync_document(data) -> dict:
    """Refresh source hashes, preserving target bytes and never recording review."""
    errors = _schema_errors(data, _SCHEMA)
    if errors:
        raise ValueError("\n".join(errors))
    result = copy.deepcopy(data)
    for unit in result["units"]:
        current = source_digest(unit["source"])
        if unit["target"] is not None and (
                unit["source_hash"] != current or unit["target_source_hash"] != current):
            unit["status"] = "needs_review"
        unit["source_hash"] = current
    errors = validate_document(result)
    if errors:
        raise ValueError("\n".join(errors))
    return result


def record_review(data, unit_id: str, target: str, *, reviewed_source_hash: str) -> dict:
    """Record a caller's completed review for one exact source; never judge meaning."""
    errors = validate_document(data)
    if errors:
        raise ValueError("\n".join(errors))
    result = copy.deepcopy(data)
    unit = next((u for u in result["units"] if u["id"] == unit_id), None)
    if unit is None:
        raise ValueError(f"missing unit {unit_id!r}")
    if reviewed_source_hash != source_digest(unit["source"]):
        raise ValueError(f"unit {unit_id}: reviewed source changed; read and review current source")
    unit["target"] = target
    unit["target_source_hash"] = reviewed_source_hash
    unit["status"] = "reviewed"
    errors = validate_document(result)
    if errors:
        raise ValueError("\n".join(errors))
    return result



def save_document(path, data) -> None:
    """Atomically persist a valid working master. Caller coordinates a single writer."""
    errors = validate_document(data)
    if errors:
        raise ValueError("\n".join(errors))
    path = Path(path)
    if path.is_symlink():
        raise ValueError("refusing to replace a symlink; select the actual working master")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp",
                                         delete=False) as output:
            temporary = Path(output.name)
            json.dump(data, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError(f"non-finite JSON value {value}")


def untranslated_errors(data) -> list[str]:
    """Check a saved preparation checkpoint; no judgment of source completeness."""
    errors = validate_document(data)
    if errors:
        return errors
    for unit in data["units"]:
        if unit["target"] is not None or unit["target_source_hash"] is not None or unit["status"] != "untranslated":
            errors.append(f"unit {unit['id']}: preparation checkpoint requires an empty untranslated target")
    return errors


def unit_view(data, unit_id=None, *, include_context=False, neighbors=0) -> dict:
    """Read one complete pair from the current master, with requested context."""
    errors = validate_document(data)
    if errors:
        raise ValueError("\n".join(errors))
    if type(neighbors) is not int or neighbors < 0:
        raise ValueError("neighbors must be a nonnegative integer")
    units = data["units"]
    selected = next((u for u in units if u["id"] == unit_id), None) if unit_id is not None else next(
        (u for u in units if u["status"] != "reviewed"), None)
    if selected is None:
        if unit_id is not None:
            raise ValueError(f"missing unit {unit_id!r}")
        return {"complete": True, "note": "All units have current review records; semantic accuracy is not checked."}
    result = {"complete": False, "unit": copy.deepcopy(selected)}
    if include_context:
        result["context"] = copy.deepcopy(data.get("context", {}))
        result["languages"] = copy.deepcopy(data["languages"])
    if neighbors:
        index = units.index(selected)
        result["neighbor_sources"] = [
            {key: unit[key] for key in ("id", "kind", "source")}
            for unit in units[max(0, index-neighbors):index+neighbors+1]
            if unit["id"] != selected["id"]]
    for block in data["blocks"]:
        if block["type"] == "table":
            rows = [block["headers"]] + block["rows"]
            row = next((row for row in rows if selected["id"] in row), None)
            if row is not None:
                by_id = {u["id"]: u for u in units}
                result["table_context"] = {
                    "headers": [by_id[x]["source"] for x in block["headers"]],
                    "row": [by_id[x]["source"] for x in row]}
                break
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="check structure, source hashes and currency")
    validate.add_argument("data", type=Path)
    stage = validate.add_mutually_exclusive_group()
    stage.add_argument("--ready", action="store_true", help="require recorded current reviews")
    stage.add_argument("--untranslated", action="store_true", help="read back an executed source-only preparation checkpoint")
    view = commands.add_parser("view", help="show one complete current source/target pair")
    view.add_argument("data", type=Path)
    selected = view.add_mutually_exclusive_group(required=True)
    selected.add_argument("--unit")
    selected.add_argument("--next", action="store_true", help="first unit without a completed review record")
    view.add_argument("--context", action="store_true", help="include shared context once when entering/resuming the master")
    view.add_argument("--neighbors", type=int, default=0, help="complete neighboring source units on each side, when needed")
    review = commands.add_parser("record-review", help="persist the caller's already-reviewed target for one exact source")
    review.add_argument("data", type=Path)
    review.add_argument("--unit", required=True)
    review.add_argument("--source-hash", required=True)
    review.add_argument("--target", required=True, help="one complete target already reviewed by the caller")
    sync = commands.add_parser("sync", help="refresh source hashes; invalidate existing targets")
    sync.add_argument("data", type=Path)
    output = sync.add_mutually_exclusive_group(required=True)
    output.add_argument("--output", type=Path, help="a new checkpoint; input is untouched")
    output.add_argument("--in-place", action="store_true", help="atomically update the working master")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.data.read_text(encoding="utf-8"),
                          object_pairs_hook=_object, parse_constant=_nonfinite)
        if args.command == "validate":
            errors = untranslated_errors(data) if args.untranslated else validate_document(data, args.ready)
            if errors:
                raise ValueError("\n".join(errors))
            if args.untranslated:
                print(json.dumps({"preparation_readback": True, "units": len(data["units"]),
                                  "master_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
                                  "note": "Empty target slots and exact source hashes checked. Compare source coverage with the original before authoring targets."}))
            else:
                print("Valid structure and current review records." if args.ready else
                      "Valid structure and source/target state.")
            print("Semantic accuracy is not checked by this command.")
        elif args.command == "view":
            print(json.dumps(unit_view(data, args.unit, include_context=args.context, neighbors=args.neighbors),
                             ensure_ascii=False, indent=2))
        elif args.command == "record-review":
            result = record_review(data, args.unit, args.target, reviewed_source_hash=args.source_hash)
            save_document(args.data, result)
            print(json.dumps({"recorded_unit": args.unit,
                              "note": "Caller review recorded; this command does not evaluate translation meaning.",
                              "next": unit_view(result)}, ensure_ascii=False, indent=2))
        else:
            result = sync_document(data)
            if args.in_place:
                save_document(args.data, result)
            else:
                if args.output.resolve() == args.data.resolve():
                    raise ValueError("use --in-place to update the working master")
                with args.output.open("x", encoding="utf-8") as output:
                    json.dump(result, output, ensure_ascii=False, indent=2, allow_nan=False)
                    output.write("\n")
            print("Source hashes refreshed; targets preserved. Semantic review remains manual.")
        return 0
    except (OSError, ValueError, TypeError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
