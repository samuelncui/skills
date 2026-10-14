#!/usr/bin/env python3
"""Compact, transactional agent protocol over the canonical JSONL v2 implementation."""
from __future__ import annotations

import argparse
import base64
import copy
import importlib.util
import json
import re
from pathlib import Path
import sys

_SPEC = importlib.util.spec_from_file_location(
    "_translation_workflow_v2", Path(__file__).with_name("translation_workflow.py"))
core = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(core)

MAX_TARGET = 8192
ACTIVE = "_compact_active"
SEEN = "_compact_seen"
class ProtocolError(ValueError):
    """A fixed, agent-facing message with no echoed user data or internal keys."""


def require(ok, message):
    if not ok:
        raise ProtocolError(message)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ProtocolError("invalid arguments; use --help for syntax")


def _public_error(error):
    if isinstance(error, ProtocolError):
        return str(error)
    if isinstance(error, OSError):
        return "file operation failed; check paths, permissions and storage, then retry"
    if isinstance(error, UnicodeError):
        return "invalid Unicode input; use valid UTF-8 without unsupported controls"
    message = str(error)
    if "wrong/missing fields" in message:
        return "invalid fields; follow the command's payload schema"
    if "split plan" in message:
        return "provide a split plan covering exactly the oversized IDs returned by prepare read"
    if "native route" in message:
        return "source needs a lossless native route; this importer supports only its documented Markdown subset"
    if "offset" in message or "2048" in message:
        return "invalid split; use increasing codepoint offsets with nonempty children at most 2048 characters"
    if any(term in message for term in ("source changed", "source version", "acknowledge", "complete source")):
        return "current complete source delivery required; prepare read and use the final ref"
    if "continue token" in message or "continuation" in message:
        return "invalid read continuation; use the last returned ref"
    if "target" in message and "reviewed" in message:
        return "finish reviewing current targets before final export"
    if "target" in message and "Unicode text" in message:
        return "target must be nonempty valid Unicode text"
    if "source" in message and any(term in message for term in ("mismatch", "reconstruction")):
        return "source integrity check failed; restore the preserved source checkpoint"
    if "duplicate JSON" in message or isinstance(error, json.JSONDecodeError):
        return "invalid JSON; use documented fields without duplicate keys"
    return "invalid input or saved state; check the command schema and preserved checkpoint"


def _short(value):
    import hashlib
    return base64.urlsafe_b64encode(
        hashlib.sha256(core._canonical(value).encode("utf-8")).digest()[:12]).decode("ascii")


_ticket = core.compact_reference


def _ops(data):
    return data["document"]["workflow"]["operations"]


def _active(data):
    entry = _ops(data).get(ACTIVE)
    return entry["receipt"] if entry is not None else None


def _set_active(data, active):
    _ops(data)[ACTIVE] = {"request_hash": core.digest(core._canonical(active)), "receipt": active}


def _unit_view(u, review=False, data=None):
    result = {k: u[k] for k in ("id", "kind", "source")}
    if u["id"] != u["parent_id"]:
        result.update({k: u[k] for k in ("parent_id", "part_index", "has_more")})
    if review:
        result["target"] = u["target"]
    if data is not None:
        for index, block in enumerate(data["document"]["blocks"]):
            if u["parent_id"] not in core._structural_order([block]):
                continue
            if block["type"] == "heading":
                result["level"] = block["level"]
            elif block["type"] == "table":
                for row, cells in enumerate([block["headers"]] + block["rows"]):
                    if u["parent_id"] in cells:
                        result["table"] = {"block": index, "row": row,
                                           "column": cells.index(u["parent_id"])}
                        break
            elif block["type"] == "list":
                result["list"] = {"block": index, "item": block["items"].index(u["parent_id"]),
                                  "ordered": block["ordered"]}
            break
    return result


def _shared(data):
    # Shared guidance is sent once, or on explicit recovery. Never truncate the
    # only available copy of a glossary; routine local context remains bounded.
    return {"languages": copy.deepcopy(data["document"]["languages"]),
            "shared": copy.deepcopy(data["document"]["context"])}


def _local(data, unit):
    # Do not repeatedly serialize the whole-document glossary into local context.
    h = data["document"]
    by_parent = {}
    for u in data["units"]:
        if u["kind"] == "heading" or u["kind"] == "table_cell":
            by_parent[u["parent_id"]] = by_parent.get(u["parent_id"], "") + u["source"]
    context = {"headings": [by_parent.get(pid, "") for pid in unit["heading_path"]]}
    for block in h["blocks"]:
        if block["type"] == "table" and unit["parent_id"] in core._structural_order([block]):
            context["table_headers"] = [by_parent.get(pid, "") for pid in block["headers"]]
            break
    raw = core._canonical(context)
    if not any(context.values()):
        return None
    return {"text": raw[:core.MAX_CONTEXT], "truncated": len(raw) > core.MAX_CONTEXT,
            "character_limit": core.MAX_CONTEXT}


def _oversize(data, references=True):
    # Locate units in the already-delivered exact source, including syntax gaps,
    # BOM and CRLF. No extra source text needs to be emitted to choose splits.
    if not any(len(u["source"]) > core.MAX_SOURCE for u in data["units"]):
        return []
    parents = {p["id"]: p for p in data["document"]["parents"]}
    starts, cursor = {}, 0
    for piece in data["document"]["source_layout"]:
        if "text" in piece:
            cursor += len(piece["text"])
        else:
            starts[piece["parent"]] = cursor
            cursor += parents[piece["parent"]]["char_count"]
    result = []
    for unit in data["units"]:
        start = starts[unit["parent_id"]]
        end = start + len(unit["source"])
        starts[unit["parent_id"]] = end
        if len(unit["source"]) > core.MAX_SOURCE:
            item = {"id": unit["id"], "characters": len(unit["source"]), "source_span": [start, end]}
            if references:
                item["ref"] = _ticket(data, "split", [unit])
            result.append(item)
    return result


def _recovery_context(data):
    result = _shared(data)
    active = _active(data)
    if active:
        unit = next(u for u in data["units"] if u["id"] == active["ids"][0])
        local = _local(data, unit)
        if local:
            result["context"] = local
    return result


def _load(path):
    # The canonical reader validates both legacy and compact journal records.
    return core.load_jsonl(path)


def _scope(data, unit):
    # Do not cross headings, list containers or table containers in a batch.
    if unit["kind"] in ("heading", "list_item", "table_cell"):
        for index, block in enumerate(data["document"]["blocks"]):
            if unit["parent_id"] in core._structural_order([block]):
                return (unit["kind"], index, tuple(unit["heading_path"]))
    return (unit["kind"], tuple(unit["heading_path"]))


def _group(data, phase, unit_id=None):
    units = data["units"]
    if phase == "translate":
        require(not _oversize(data), "prepare split required for oversized source units")
        candidates = [u for u in units if u["target"] is None]
    else:
        require(all(u["target"] is not None for u in units),
                "finish translate before starting the separate review pass")
        require(not _oversize(data), "prepare split required for oversized source units")
        if unit_id:
            candidates = [u for u in units if u["id"] == unit_id]
            require(candidates, "unknown review unit")
        else:
            candidates = [u for u in units if u["status"] != "reviewed"]
    if not candidates:
        return []
    return _bounded_group(data, candidates, phase, unit_id)


def _bounded_group(data, candidates, phase, unit_id=None):
    first = candidates[0]
    selected, source_count, target_count = [], 0, 0
    for u in candidates:
        if selected and (u["order"] != selected[-1]["order"] + 1
                         or _scope(data, u) != _scope(data, first)):
            break
        src, tgt = len(u["source"]), len(u["target"] or "")
        if selected and (source_count + src > core.MAX_SOURCE
                         or phase == "review" and target_count + tgt > MAX_TARGET):
            break
        selected.append(u)
        source_count += src
        target_count += tgt
        if unit_id or phase == "review" and target_count >= MAX_TARGET:
            break
    return selected


def _envelope(data):
    active = _active(data)
    require(active is not None, "no active compact block")
    units = [u for u in data["units"] if u["id"] in active["ids"]]
    phase = active["phase"]
    result = {"phase": phase, "ref": active["ref"],
              "units": [_unit_view(u, phase == "review", data) for u in units]}
    if active["initial"] and active["page"] == 0:
        result.update(_shared(data))
    # A rare huge target is delivered losslessly in explicit bounded pages.
    # Only the final page provides the mutation reference.
    if phase == "review" and len(units) == 1 and len(units[0]["target"]) > MAX_TARGET:
        target = units[0]["target"]
        start = active["page"] * MAX_TARGET
        end = min(start + MAX_TARGET, len(target))
        require(start < len(target), "invalid review page")
        result["units"][0]["target"] = target[start:end]
        if active["page"] > 0:
            result["units"][0].pop("source")
        result["target_page"] = {"start": start, "end": end, "total": len(target),
                                 "complete": end == len(target)}
        if end < len(target):
            result.pop("ref")
            result["continue"] = "p" + _short([active["ref"], active["page"]])
    return result


def _dispatch(data, phase, unit_id=None):
    require(data["document"]["workflow"]["active"] is None,
            "legacy block pending; finish it with translation_workflow.py")
    active = _active(data)
    if active is not None:
        require(active["phase"] == phase, "finish the active " + active["phase"] + " block first")
        require(unit_id is None or active["ids"] == [unit_id], "finish the active review group first")
        return _envelope(data)
    units = _group(data, phase, unit_id)
    if not units:
        return {"phase": phase, "complete": True,
                "next_action": "review next" if phase == "translate" else "validate --ready"}
    seen_entry = _ops(data).setdefault(SEEN, {"request_hash": core.digest("phases"),
                                             "receipt": {"phases": []}})
    seen = seen_entry["receipt"]["phases"]
    initial = phase not in seen
    if initial:
        seen.append(phase)
    data["document"]["revision"] += 1
    _set_active(data, {"phase": phase, "ids": [u["id"] for u in units],
                       "ref": _ticket(data, phase, units), "page": 0,
                       "last_continue": None, "initial": initial})
    return _envelope(data)


def next_block(path, phase="translate", include_context=False, unit_id=None, continuation=None, restart=False):
    with core._lock(path):
        data = _load(path)
        before = core._canonical(data)
        result = _dispatch(data, phase, unit_id)
        if restart:
            require(phase == "review" and continuation is None and not result.get("complete"),
                    "restart requires an active review and cannot be combined with continue")
            active = _active(data)
            active.update(page=0, last_continue=None)
            _set_active(data, active)
            result = _envelope(data)
        if continuation is not None:
            require(phase == "review" and not result.get("complete"), "no review page to continue")
            active = _active(data)
            if continuation != active["last_continue"]:
                require(result.get("continue") == continuation, "stale/wrong review continuation")
                active["last_continue"] = continuation
                active["page"] += 1
                _set_active(data, active)
            result = _envelope(data)
        if include_context:
            result.update(_recovery_context(data))
            if result.get("target_page", {}).get("start", 0) > 0:
                unit = next(u for u in data["units"] if u["id"] == result["units"][0]["id"])
                result["units"][0]["source"] = unit["source"]
        if core._canonical(data) != before:
            core._save(path, data)
        return result


def mutate(path, action, payload):
    if action == "accept":
        core._keys(payload, {"ref", "reviewer", "note"}, "review acceptance")
        core._text(payload["reviewer"], "reviewer")
        core._text(payload["note"], "review note", empty=True)
    else:
        core._keys(payload, {"ref", "targets"}, "target-only payload")
    require(isinstance(payload["ref"], str), "expected ref")
    fingerprint = core.digest(core._canonical([action, payload]))
    key = "_compact_receipt:" + payload["ref"]
    with core._lock(path):
        data = _load(path)
        old = _ops(data).get(key)
        if old is not None:
            require(old["request_hash"] == fingerprint, "reference reused with different content/action")
            return copy.deepcopy(old["receipt"])
        active = _active(data)
        phase = "translate" if action == "save" else "review"
        require(active is not None and active["phase"] == phase, "wrong phase or no active block")
        require(payload["ref"] == active["ref"], "stale/wrong reference or document")
        envelope = _envelope(data)
        require("ref" in envelope, "read every review page before accepting or revising")
        units = [u for u in data["units"] if u["id"] in active["ids"]]
        if action != "accept":
            targets = payload["targets"]
            require(isinstance(targets, dict) and targets, "targets must be a nonempty object")
            ids = set(active["ids"])
            require(set(targets) == ids if action == "save" else set(targets) <= ids,
                    "targets must match exact active IDs (revise permits a nonempty subset)")
            for value in targets.values():
                core._text(value, "target")
            changed = []
            for u in units:
                if u["id"] in targets:
                    target = targets[u["id"]]
                    u.update(target=target, target_hash=core.digest(target),
                             target_source_hash=u["source_hash"], status="draft", review=None)
                    changed.append(u["id"])
        else:
            changed = active["ids"][:]
            for u in units:
                u["review"] = {"source_hash": u["source_hash"], "target_hash": u["target_hash"],
                               "reviewer": payload["reviewer"], "note": payload["note"]}
                u["status"] = "reviewed"
        _ops(data).pop(ACTIVE)
        data["document"]["revision"] += 1
        # Revise presents the same complete group again. No automatic approval.
        if action == "revise":
            units = _bounded_group(data, units, "review")
            _set_active(data, dict(active, ids=[u["id"] for u in units],
                                   ref=_ticket(data, phase, units),
                                   page=0, last_continue=None, initial=False))
            following = _envelope(data)
        else:
            following = _dispatch(data, phase)
        result = {{"save": "saved", "accept": "reviewed", "revise": "revised"}[action]: changed,
                  "next": following}
        _ops(data)[key] = {"request_hash": fingerprint, "receipt": copy.deepcopy(result)}
        core._save(path, data)
        return result


def _read_ref(token):
    # Existing legacy preread receipts can contain hex tokens. Keep their stored
    # protocol untouched, but never expose those tokens through this interface.
    if isinstance(token, str) and re.fullmatch(r"[a-f0-9]{32}", token):
        return "p" + _short(["read", token])
    require(isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9_-]{12}", token),
            "invalid read receipt; create a new receipt and reread the source")
    return "p" + token


def read_source(source, receipt, continuation=None):
    if continuation is not None and Path(receipt).exists():
        state = core._json(Path(receipt).read_text("utf-8"))
        tokens = [state["token"], state["last_request"]]
        matched = next((token for token in tokens
                        if token is not None and _read_ref(token) == continuation), None)
        require(matched is not None, "invalid read continuation; use the last returned ref")
        continuation = matched
    page = core.read_source(source, receipt, continuation)
    text = core._source(source)
    require(core.digest(text) == page["source_hash"], "source changed; reread with a new receipt")
    units, _, layout = core.import_markdown(text)
    preparation = {"units": units, "document": {
        "parents": [{"id": u["id"], "char_count": len(u["source"])} for u in units],
        "source_layout": layout}}
    result = {k: page[k] for k in ("start", "end", "text", "complete")} | {"ref": _read_ref(page["token"])}
    oversized = [u for u in _oversize(preparation, references=False)
                 if page["start"] <= u["source_span"][0] < page["end"]]
    if oversized:
        result["oversize"] = oversized
    return result


def initialize(source, receipt, output, read_ref, source_lang="en", target_lang="fr",
               source_dir="ltr", target_dir="ltr", context=None, splits=None):
    # The final delivery reference explicitly acknowledges the emitted source.
    # The initial replay record is part of the same atomic creation as the master.
    require(splits is None or isinstance(splits, dict), "split plan must be an ID-to-offsets object")
    kwargs = dict(source_lang=source_lang, target_lang=target_lang,
                  source_dir=source_dir, target_dir=target_dir, context=context,
                  source_splits={} if splits is None else splits)
    source_text = core._source(source)
    fingerprint = core.digest(core._canonical([read_ref, core.digest(source_text), kwargs]))
    def replay():
        old = _ops(_load(output)).get("_compact_init")
        require(old is not None and old["request_hash"] == fingerprint,
                "output already exists with a different initialization")
        return copy.deepcopy(old["receipt"])
    if Path(output).exists():
        return replay()
    state = core._json(Path(receipt).read_text("utf-8"))
    require(read_ref == _read_ref(state["token"]), "use the final prepare read ref to initialize")
    core.ack_source(source, receipt, state["source_hash"], state["token"])
    def initial_operations(data):
        result = {"initialized": True, "units": len(data["units"]), "oversize": _oversize(data)}
        return {"_compact_init": {"request_hash": fingerprint, "receipt": result}}
    try:
        core.initialize(source, receipt, output, initial_operations=initial_operations, **kwargs)
    except (FileExistsError, ValueError):
        if Path(output).exists():
            return replay()
        raise
    return replay()


def inspect(path, unit_id):
    data = _load(path)
    require(_active(data) is None and data["document"]["workflow"]["active"] is None,
            "finish active block before preparation")
    require(all(u["target"] is None for u in data["units"]), "preparation is source-only")
    unit = next((u for u in data["units"] if u["id"] == unit_id), None)
    require(unit is not None, "unknown unit")
    return {"ref": _ticket(data, "split", [unit]), "unit": _unit_view(unit, data=data)}


def split(path, ref, offsets):
    payload_hash = core.digest(core._canonical(["split", ref, offsets]))
    key = "_compact_receipt:" + str(ref)
    with core._lock(path):
        data = _load(path)
        old = _ops(data).get(key)
        if old is not None:
            require(old["request_hash"] == payload_hash, "reference reused with different split")
            return copy.deepcopy(old["receipt"])
        require(_active(data) is None, "finish active block before preparation")
        require(all(u["target"] is None for u in data["units"]), "preparation is source-only")
        unit = next((u for u in data["units"] if _ticket(data, "split", [u]) == ref), None)
        require(unit is not None, "stale/wrong split reference or document")
        result = core._split_data(data, unit["id"], offsets, unit["source_hash"], data["document"]["revision"])
        result = {"split": result["split"],
                  "children": [{k: u[k] for k in ("id", "characters", "part_index", "has_more")}
                               for u in result["children"]],
                  "oversize": _oversize(data)}
        _ops(data)[key] = {"request_hash": payload_hash, "receipt": copy.deepcopy(result)}
        core._save(path, data)
        return result


def status(path, include_context=False):
    data = _load(path)
    units = data["units"]
    saved = sum(u["target"] is not None for u in units)
    reviewed = sum(u["status"] == "reviewed" for u in units)
    blocked = _oversize(data)
    active = _active(data)
    if data["document"]["workflow"]["active"]:
        action = "legacy commit"
    elif active:
        action = active["phase"] + (" save" if active["phase"] == "translate" else " next")
    elif blocked:
        action = "prepare split"
    elif saved != len(units):
        action = "translate next"
    elif reviewed != len(units):
        action = "review next"
    else:
        action = "validate --ready"
    result = {"units": len(units), "saved": saved, "reviewed": reviewed, "next_action": action}
    if blocked:
        result["oversize"] = blocked
    if include_context:
        result.update(_recovery_context(data))
    return result


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="phase", required=True)
    prepare = commands.add_parser("prepare").add_subparsers(dest="action", required=True)
    read = prepare.add_parser("read")
    read.add_argument("source", type=Path)
    read.add_argument("--receipt", type=Path, required=True)
    read.add_argument("--continue", dest="continuation")
    init = prepare.add_parser("init")
    init.add_argument("source", type=Path)
    init.add_argument("--receipt", type=Path, required=True)
    init.add_argument("--read-ref", required=True)
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--source-lang", required=True)
    init.add_argument("--target-lang", required=True)
    init.add_argument("--source-dir", choices=["ltr", "rtl"], default="ltr")
    init.add_argument("--target-dir", choices=["ltr", "rtl"], default="ltr")
    init.add_argument("--context", type=Path)
    init.add_argument("--splits", type=Path)
    ins = prepare.add_parser("inspect")
    ins.add_argument("data", type=Path, nargs="?", default=Path("master.jsonl"), help="JSONL master (default: ./master.jsonl)")
    ins.add_argument("--unit", required=True)
    spl = prepare.add_parser("split")
    spl.add_argument("data", type=Path, nargs="?", default=Path("master.jsonl"), help="JSONL master (default: ./master.jsonl)")
    spl.add_argument("--ref", required=True)
    spl.add_argument("--offsets", required=True)
    for phase, actions in (("translate", ("next", "save")), ("review", ("next", "accept", "revise"))):
        sub = commands.add_parser(phase).add_subparsers(dest="action", required=True)
        for action in actions:
            cmd = sub.add_parser(action)
            cmd.add_argument("data", type=Path, nargs="?", default=Path("master.jsonl"), help="JSONL master (default: ./master.jsonl)")
            if action == "next":
                cmd.add_argument("--context", action="store_true")
                if phase == "review":
                    cmd.add_argument("--unit")
                    cmd.add_argument("--continue", dest="continuation")
                    cmd.add_argument("--restart", action="store_true")
            elif action == "accept":
                cmd.add_argument("--ref", required=True)
                cmd.add_argument("--reviewer", default="translation-agent")
                cmd.add_argument("--note", default="")
            else:
                cmd.add_argument("--payload", type=Path, required=True)
    stat = commands.add_parser("status")
    stat.add_argument("data", type=Path, nargs="?", default=Path("master.jsonl"), help="JSONL master (default: ./master.jsonl)")
    stat.add_argument("--context", action="store_true")
    val = commands.add_parser("validate")
    val.add_argument("data", type=Path, nargs="?", default=Path("master.jsonl"), help="JSONL master (default: ./master.jsonl)")
    val.add_argument("--ready", action="store_true")
    exp = commands.add_parser("export")
    exp.add_argument("data", type=Path, nargs="?", default=Path("master.jsonl"), help="JSONL master (default: ./master.jsonl)")
    exp.add_argument("--output", type=Path, required=True)
    exp.add_argument("--allow-draft", action="store_true")
    try:
        args = parser.parse_args(argv)
        if args.phase == "prepare":
            if args.action == "read":
                result = read_source(args.source, args.receipt, args.continuation)
            elif args.action == "init":
                context = core._json(args.context.read_text("utf-8")) if args.context else None
                splits = core._json(args.splits.read_text("utf-8")) if args.splits else None
                result = initialize(args.source, args.receipt, args.output, args.read_ref,
                                    source_lang=args.source_lang, target_lang=args.target_lang,
                                    source_dir=args.source_dir, target_dir=args.target_dir, context=context, splits=splits)
            elif args.action == "inspect":
                result = inspect(args.data, args.unit)
            else:
                try:
                    offsets = [int(x) for x in args.offsets.split(",")]
                except ValueError:
                    raise ProtocolError("offsets must be comma-separated integer codepoint boundaries") from None
                result = split(args.data, args.ref, offsets)
        elif args.phase in ("translate", "review"):
            if args.action == "next":
                result = next_block(args.data, args.phase, args.context,
                                    getattr(args, "unit", None), getattr(args, "continuation", None),
                                    getattr(args, "restart", False))
            else:
                payload = ({"ref": args.ref, "reviewer": args.reviewer, "note": args.note}
                           if args.action == "accept" else core._json(args.payload.read_text("utf-8")))
                result = mutate(args.data, args.action, payload)
        elif args.phase == "status":
            result = status(args.data, args.context)
        else:
            data = _load(args.data)
            if args.phase == "validate":
                core.validate(data, args.ready)
                require(not args.ready or _active(data) is None, "finish active review")
                result = {"valid": True, "ready": args.ready}
            else:
                require(all(u["target"] is not None for u in data["units"]), "export requires all targets saved")
                require(args.allow_draft or _active(data) is None, "finish active review")
                legacy = core.to_legacy_document(data, not args.allow_draft)
                with core._lock(args.output):
                    core._atomic(args.output, json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", new=True)
                result = {"exported": str(args.output), "review_gate": not args.allow_draft}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 0
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as error:
        print(json.dumps({"error": _public_error(error)}, ensure_ascii=False, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
