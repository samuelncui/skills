#!/usr/bin/env python3
"""Source-first JSONL v2 workflow. Receipts attest delivery/review, never understanding."""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile

_SPEC = importlib.util.spec_from_file_location(
    "_translation_contract_v1", Path(__file__).with_name("translation_contract.py"))
legacy = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(legacy)

CONTRACT_VERSION = 2
MAX_SOURCE = 2048
MAX_CONTEXT = 1024
READ_PAGE = 8192
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
BAD_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069\ud800-\udfff]")
UNIT_KEYS = {"record_type", "id", "parent_id", "part_index", "has_more", "kind",
             "source", "target", "source_hash", "target_source_hash", "status",
             "order", "heading_path", "review", "target_hash"}
HEADER_KEYS = {"record_type", "contract_version", "document_id", "revision", "languages",
               "source", "blocks", "parents", "source_layout", "context", "workflow",
               "preread"}
PARENT_KEYS = {"id", "kind", "source_hash", "char_count", "heading_path"}
COMMIT_KEYS = {"operation_id", "block_id", "revision", "source_hashes", "targets"}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json(text):
    return json.loads(text, object_pairs_hook=legacy._object, parse_constant=legacy._nonfinite)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _keys(value, expected, label):
    _require(isinstance(value, dict) and set(value) == expected, label + ": wrong/missing fields")


def _text(value, label, empty=False):
    _require(isinstance(value, str) and (empty or bool(value.strip())) and not BAD_TEXT.search(value),
             label + ": expected safe nonempty Unicode text")


def _id(value):
    return isinstance(value, str) and len(value) <= 128 and ID.fullmatch(value)


def _hash(value):
    return isinstance(value, str) and HASH.fullmatch(value)


def _source(path):
    # Decode bytes directly: universal newline conversion would change CRLF.
    value = Path(path).read_bytes().decode("utf-8")
    _text(value, "source")
    return value


@contextmanager
def _lock(path):
    """Stable sidecar inode + OS process lock; never unlink the lock file."""
    path = Path(path).absolute()
    _require(not path.is_symlink(), "refusing symlink destination")
    lock = path.with_name(path.name + ".lock")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock, flags, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        _require(not path.is_symlink(), "refusing symlink destination")
        yield
    finally:
        os.close(fd)


def _atomic(path, text, new=False):
    path = Path(path)
    _require(not path.is_symlink(), "refusing symlink destination")
    _require(not new or not path.exists(), "output already exists")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=path.parent, prefix="." + path.name + ".",
                                         suffix=".tmp", delete=False) as out:
            temporary = Path(out.name)
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        if new:
            # Atomic create without overwriting a concurrently created output.
            os.link(temporary, path)
            temporary.unlink()
        else:
            os.replace(temporary, path)
        temporary = None
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_source(source, receipt, continuation=None):
    """Emit sequential exact pages. Replaying the last continuation replays that page."""
    text = _source(source)
    sha = digest(text)
    with _lock(receipt):
        path = Path(receipt)
        if not path.exists():
            _require(continuation is None, "no receipt exists for this continuation")
            state = {"source_hash": sha, "char_count": len(text), "end": 0,
                     "token": None, "last_request": None, "page": None, "acknowledged": False}
        else:
            state = _json(path.read_text("utf-8"))
            _require(state["source_hash"] == sha, "source changed; create a new preread receipt")
            if continuation == state["last_request"] and state["page"] is not None:
                return state["page"]
            _require(continuation is not None and continuation == state["token"],
                     "use the returned continue token; reread with a new receipt to start over")
            _require(state["end"] < len(text), "all source pages delivered; acknowledge source")
        start = state["end"]
        end = min(start + READ_PAGE, len(text))
        token = secrets.token_hex(16)
        page = {"source_hash": sha, "start": start, "end": end, "char_count": len(text),
                "text": text[start:end], "complete": end == len(text), "token": token,
                "note": "Read this exact page. Acknowledge the version after the final page."}
        state.update(end=end, token=token, last_request=continuation, page=page)
        _atomic(path, _canonical(state) + "\n", new=not path.exists())
        return page


def ack_source(source, receipt, source_hash, token):
    text = _source(source)
    with _lock(receipt):
        state = _json(Path(receipt).read_text("utf-8"))
        _require(state["source_hash"] == source_hash == digest(text), "source version mismatch")
        _require(state["end"] == len(text) and token == state["token"],
                 "complete source delivery and its final token are required")
        state["acknowledged"] = True
        _atomic(receipt, _canonical(state) + "\n")
    return {"acknowledged": source_hash,
            "note": "Delivery and caller acknowledgment recorded; understanding is not established."}


def _new_unit(uid, kind, source, heading_path):
    return {"record_type": "unit", "id": uid, "parent_id": uid, "part_index": 0,
            "has_more": False, "kind": kind, "source": source, "target": None,
            "source_hash": digest(source), "target_source_hash": None,
            "target_hash": None, "status": "untranslated", "review": None,
            "order": 0, "heading_path": list(heading_path)}


def import_markdown(text):
    """Conservative structural subset; retain exact source spans and all syntax gaps."""
    lines = text.splitlines(keepends=True)
    starts, cursor = [], 0
    for line in lines:
        starts.append(cursor)
        cursor += len(line)
    if lines and lines[0].startswith("\ufeff"):
        lines[0] = lines[0][1:]
        starts[0] += 1  # Preserve the BOM in the first source-layout syntax gap.
    units, blocks, spans, headings = [], [], [], []
    heading = re.compile(r"^(#{1,6})[ \t]+(.+?)(?:[ \t]+#+[ \t]*)?$")
    item = re.compile(r"^([-+*]|[0-9]+[.)])[ \t]+(.+)$")
    delimiter = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
    def body(index):
        return lines[index].rstrip("\r\n")
    def add(kind, start, end):
        value = text[start:end]
        _text(value, "Markdown unit")
        uid = "u" + str(len(units) + 1).zfill(6)
        units.append(_new_unit(uid, kind, value, [v for _, v in headings]))
        spans.append((start, end, uid))
        return uid
    def cells(index):
        line = body(index)
        _require("\\|" not in line and "`" not in line,
                 "escaped pipes/code in tables need an explicit lossless native route")
        bounds = [m.start() for m in re.finditer(r"\|", line)]
        _require(bounds, "table row requires pipe separators")
        edges = [-1] + bounds + [len(line)]
        result = []
        for a, b in zip(edges, edges[1:]):
            raw = line[a + 1:b]
            if not raw.strip() and (a == -1 or b == len(line)):
                continue
            _require(bool(raw.strip()), "empty table cell needs an explicit source unit")
            lead = len(raw) - len(raw.lstrip())
            trail = len(raw.rstrip())
            result.append(add("table_cell", starts[index] + a + 1 + lead,
                              starts[index] + a + 1 + trail))
        return result
    i = 0
    while i < len(lines):
        line = body(i)
        if not line.strip():
            i += 1
            continue
        _require(not re.match(r"^(?:[ \t]{4}|\t|\s*[`~]{3}|\s*>|\s*<|\s*!\[|\s*\[\^)", line),
                 "unsupported rich/nested Markdown at line " + str(i + 1) +
                 "; retain original and use an explicit lossless native route")
        match = heading.match(line)
        setext = (i + 1 < len(lines) and re.fullmatch(r"\s*(?:=+|-+)\s*", body(i + 1)))
        if match or setext:
            level = len(match[1]) if match else (1 if "=" in body(i + 1) else 2)
            while headings and headings[-1][0] >= level:
                headings.pop()
            start = starts[i] + (match.start(2) if match else 0)
            end = starts[i] + (match.end(2) if match else len(line))
            uid = add("heading", start, end)
            blocks.append({"type": "heading", "level": level, "unit": uid})
            headings.append((level, uid))
            i += 1 if match else 2
        elif i + 1 < len(lines) and delimiter.fullmatch(body(i + 1)):
            headers = cells(i)
            i += 2
            rows = []
            while i < len(lines) and body(i).strip() and "|" in body(i):
                row = cells(i)
                _require(len(row) == len(headers), "ragged Markdown table")
                rows.append(row)
                i += 1
            _require(rows, "table needs a data row")
            blocks.append({"type": "table", "headers": headers, "rows": rows})
        elif item.match(line):
            ordered = item.match(line)[1][0].isdigit()
            ids = []
            while i < len(lines):
                match = item.match(body(i))
                if not match or match[1][0].isdigit() != ordered:
                    break
                ids.append(add("list_item", starts[i] + match.start(2),
                               starts[i] + match.end(2)))
                i += 1
            if i < len(lines) and body(i).strip():
                _require(heading.match(body(i)) or item.match(body(i)),
                         "multiline/nested list item requires an explicit lossless native route")
            blocks.append({"type": "list", "ordered": ordered, "items": ids})
        else:
            start = i
            i += 1
            while i < len(lines) and body(i).strip():
                if heading.match(body(i)) or item.match(body(i)):
                    break
                _require(not re.match(r"^(?:[ \t]{4}|\t|\s*[`~]{3}|\s*>|\s*<)", body(i)),
                         "nested/rich Markdown requires a lossless native route")
                if i + 1 < len(lines) and delimiter.fullmatch(body(i + 1)):
                    break
                i += 1
            uid = add("paragraph", starts[start], starts[i - 1] + len(body(i - 1)))
            blocks.append({"type": "paragraph", "unit": uid})
    _require(units, "source has no translatable units")
    layout, cursor = [], 0
    for start, end, uid in spans:
        if start != cursor:
            layout.append({"text": text[cursor:start]})
        layout.append({"parent": uid})
        cursor = end
    if cursor < len(text):
        layout.append({"text": text[cursor:]})
    return units, blocks, layout


def initialize(source, receipt, output, source_lang="en", target_lang="fr",
               source_dir="ltr", target_dir="ltr", context=None):
    text = _source(source)
    state = _json(Path(receipt).read_text("utf-8"))
    _require(state.get("acknowledged") is True and state.get("source_hash") == digest(text)
             and state.get("end") == len(text), "acknowledge complete current source before init")
    units, blocks, layout = import_markdown(text)
    parents = [{k: u[k] for k in ("id", "kind", "source_hash", "heading_path")} |
               {"char_count": len(u["source"])} for u in units]
    for i, u in enumerate(units):
        u["order"] = i
    document = {"record_type": "document", "contract_version": 2,
                "document_id": "d" + secrets.token_hex(12), "revision": 0,
                "languages": {"source": {"tag": source_lang, "dir": source_dir},
                              "target": {"tag": target_lang, "dir": target_dir}},
                "source": {"sha256": digest(text), "char_count": len(text), "format": "markdown"},
                "blocks": blocks, "parents": parents, "source_layout": layout,
                "context": context or {}, "workflow": {"active": None, "operations": {}},
                "preread": {"source_hash": digest(text), "acknowledged": True}}
    data = {"document": document, "units": units}
    with _lock(output):
        _save(output, data, new=True)
    # Readback is part of init, before any target authoring.
    checked = load_jsonl(output)
    return {"initialized": True, "revision": 0, "document_id": document["document_id"],
            "source_hash": document["source"]["sha256"], "units": len(checked["units"]),
            "oversize": oversized(checked), "preparation_readback": True}


def _joined(data):
    h, units = data["document"], data["units"]
    result = []
    for parent in h["parents"]:
        children = [u for u in units if u["parent_id"] == parent["id"]]
        source = "".join(u["source"] for u in children)
        target = None if any(u["target"] is None for u in children) else "".join(u["target"] for u in children)
        status = ("untranslated" if target is None else
                  "reviewed" if all(u["status"] == "reviewed" for u in children) else
                  "needs_review" if any(u["status"] == "needs_review" for u in children) else "draft")
        result.append({"id": parent["id"], "kind": parent["kind"], "source": source,
                       "source_hash": digest(source), "target": target, "status": status,
                       "target_source_hash": None if target is None else digest(source)})
    return {"schema_version": 1, "languages": copy.deepcopy(h["languages"]),
            "source_revision": h["source"]["sha256"], "context": copy.deepcopy(h["context"]),
            "units": result, "blocks": copy.deepcopy(h["blocks"])}


def _structural_order(blocks):
    ids = []
    for block in blocks:
        kind = block["type"]
        if kind in ("heading", "paragraph"):
            ids.append(block["unit"])
        elif kind == "list":
            ids.extend(block["items"])
        elif kind == "table":
            ids.extend(block["headers"])
            for row in block["rows"]:
                ids.extend(row)
            if "caption" in block:
                ids.append(block["caption"])
        elif kind == "figure":
            ids.extend([block["caption"], block["alt"]])
    return ids


def _validate(data, require_ready=False):
    _keys(data, {"document", "units"}, "master")
    h, units = data["document"], data["units"]
    _keys(h, HEADER_KEYS, "document")
    _require(h["record_type"] == "document" and type(h["contract_version"]) is int
             and h["contract_version"] == 2, "expected JSONL contract_version 2")
    _require(_id(h["document_id"]), "invalid document_id")
    _require(type(h["revision"]) is int and h["revision"] >= 0, "invalid revision")
    _keys(h["source"], {"sha256", "char_count", "format"}, "source metadata")
    _require(_hash(h["source"]["sha256"]) and type(h["source"]["char_count"]) is int
             and h["source"]["char_count"] > 0 and h["source"]["format"] == "markdown",
             "invalid source metadata")
    _keys(h["preread"], {"source_hash", "acknowledged"}, "preread")
    _require(h["preread"]["acknowledged"] is True and
             h["preread"]["source_hash"] == h["source"]["sha256"],
             "missing current preread acknowledgment")
    _require(isinstance(units, list) and units, "units must be a nonempty array")
    _require(isinstance(h["parents"], list) and h["parents"], "parents must be nonempty")
    parents, ids = {}, set()
    for p in h["parents"]:
        _keys(p, PARENT_KEYS, "parent")
        _require(_id(p["id"]) and p["id"] not in parents and _hash(p["source_hash"]),
                 "invalid or duplicate parent ID/hash")
        _require(type(p["char_count"]) is int and p["char_count"] > 0, "invalid parent length")
        _require(isinstance(p["heading_path"], list) and len(p["heading_path"]) <= 6
                 and all(_id(x) for x in p["heading_path"]), "invalid heading_path")
        parents[p["id"]] = p
    for i, u in enumerate(units):
        _keys(u, UNIT_KEYS, "unit")
        _require(u["record_type"] == "unit" and _id(u["id"]) and u["id"] not in ids,
                 "invalid/duplicate unit ID")
        ids.add(u["id"])
        _require(type(u["order"]) is int and u["order"] == i, "unit order changed")
        _require(u["parent_id"] in parents, "unknown parent ID")
        p = parents[u["parent_id"]]
        _require(u["kind"] == p["kind"] and u["heading_path"] == p["heading_path"],
                 "child kind/heading_path differs from parent")
        _text(u["source"], "unit source")
        _require(u["source_hash"] == digest(u["source"]), "unit source hash mismatch")
        _require(type(u["part_index"]) is int and type(u["has_more"]) is bool,
                 "invalid continuation fields")
        if u["target"] is None:
            _require(u["status"] == "untranslated" and u["target_source_hash"] is None
                     and u["target_hash"] is None and u["review"] is None,
                     "empty target must be untranslated")
        else:
            _text(u["target"], "target")
            _require(u["target_source_hash"] == u["source_hash"]
                     and u["target_hash"] == digest(u["target"]), "stale target/source hash")
            _require(u["status"] in ("draft", "reviewed", "needs_review"), "invalid saved status")
            if u["status"] == "reviewed":
                _keys(u["review"], {"source_hash", "target_hash", "reviewer", "note"}, "review")
                _require(u["review"]["source_hash"] == u["source_hash"]
                         and u["review"]["target_hash"] == u["target_hash"], "stale review")
                _text(u["review"]["reviewer"], "reviewer")
                _text(u["review"]["note"], "review note", empty=True)
            else:
                _require(u["review"] is None, "unreviewed target cannot carry current review")
        if require_ready:
            _require(u["status"] == "reviewed", "export requires reviewed current targets")
    flat, parent_text = [], {}
    for p in h["parents"]:
        group = [u for u in units if u["parent_id"] == p["id"]]
        _require(group, "parent has no children")
        for j, u in enumerate(group):
            expected = p["id"] if len(group) == 1 else p["id"] + ".part" + str(j + 1).zfill(4)
            _require(u["id"] == expected and u["part_index"] == j
                     and u["has_more"] == (j < len(group) - 1), "invalid child IDs/order/has_more")
        joined = "".join(u["source"] for u in group)
        _require(len(joined) == p["char_count"] and digest(joined) == p["source_hash"],
                 "parent reconstruction mismatch")
        parent_text[p["id"]] = joined
        flat.extend(u["id"] for u in group)
    _require(flat == [u["id"] for u in units], "children must follow contiguous parent order")
    reconstructed, covered = [], []
    _require(isinstance(h["source_layout"], list), "invalid source layout")
    for piece in h["source_layout"]:
        _require(isinstance(piece, dict) and len(piece) == 1, "invalid source layout piece")
        if "text" in piece:
            _text(piece["text"], "syntax gap", empty=True)
            reconstructed.append(piece["text"])
        else:
            _require(set(piece) == {"parent"} and piece["parent"] in parent_text, "unknown source parent")
            covered.append(piece["parent"])
            reconstructed.append(parent_text[piece["parent"]])
    _require(covered == list(parents), "source layout order/coverage mismatch")
    source = "".join(reconstructed)
    _require(digest(source) == h["source"]["sha256"] and len(source) == h["source"]["char_count"],
             "complete source reconstruction mismatch")
    _require(all(isinstance(h["languages"].get(role), dict) and
                 isinstance(h["languages"][role].get("tag"), str) and
                 len(h["languages"][role]["tag"]) <= 64 for role in ("source", "target")),
             "language metadata must use bounded tags")
    errors = legacy.validate_document(_joined(data))
    _require(not errors, "\n".join(errors))
    _require(_structural_order(h["blocks"]) == list(parents), "structural reading order differs from parents")
    # Heading metadata must identify the actual preceding structural ancestry.
    headings = []
    for block in h["blocks"]:
        for pid in _structural_order([block]):
            if block["type"] == "heading":
                while headings and headings[-1][0] >= block["level"]:
                    headings.pop()
            _require(parents[pid]["heading_path"] == [v for _, v in headings], "heading ancestry mismatch")
            if block["type"] == "heading":
                headings.append((block["level"], pid))
    _keys(h["workflow"], {"active", "operations"}, "workflow")
    _require(isinstance(h["workflow"]["operations"], dict), "invalid operations")
    active = h["workflow"]["active"]
    if active is not None:
        _keys(active, {"block_id", "revision", "ids", "source_hashes"}, "active block")
        remaining = [u for u in units if u["target"] is None]
        _require(remaining and active["ids"] == [remaining[0]["id"]], "active is not next unsaved block")
        _require(type(active["revision"]) is int and active["revision"] == h["revision"]
                 and _id(active["block_id"]),
                 "stale active revision/ID")
        _require(active["source_hashes"] == {remaining[0]["id"]: remaining[0]["source_hash"]},
                 "active source hash mismatch")
        _require(len(remaining[0]["source"]) <= MAX_SOURCE, "active source exceeds limit")
    if require_ready:
        _require(active is None and not oversized(data), "master not ready")
    return data


def validate(data, require_ready=False):
    """Validate JSON-shaped data with predictable ValueError failures."""
    try:
        return _validate(data, require_ready)
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValueError("malformed JSONL structure: " + str(exc)) from exc


def load_jsonl(path, require_ready=False):
    records = [_json(line) for line in Path(path).read_text("utf-8").splitlines() if line.strip()]
    _require(records, "empty JSONL master")
    data = {"document": records[0], "units": records[1:]}
    try:
        return validate(data, require_ready)
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError("malformed JSONL structure: " + str(exc)) from exc


def to_legacy_document(data, require_ready=True):
    validate(data, require_ready)
    return _joined(data)


def _save(path, data, new=False):
    validate(data)
    _atomic(path, "\n".join(_canonical(v) for v in [data["document"]] + data["units"]) + "\n", new)


def oversized(data):
    return [{"id": u["id"], "parent_id": u["parent_id"], "characters": len(u["source"]),
             "source_hash": u["source_hash"]} for u in data["units"] if len(u["source"]) > MAX_SOURCE]


def split_unit(path, unit_id, offsets, source_hash, revision):
    with _lock(path):
        data = load_jsonl(path)
        h = data["document"]
        _require(h["revision"] == revision, "stale revision")
        _require(h["workflow"]["active"] is None, "save active block before changing segmentation")
        unit = next((u for u in data["units"] if u["id"] == unit_id), None)
        _require(unit is not None and unit["parent_id"] == unit_id, "split requires an unsplit parent ID")
        _require(unit["source_hash"] == source_hash, "stale source hash")
        _require(unit["target"] is None, "split source-only units before translating")
        _require(isinstance(offsets, list) and offsets and all(type(n) is int for n in offsets)
                 and offsets == sorted(set(offsets)) and 0 < offsets[0]
                 and offsets[-1] < len(unit["source"]), "invalid Unicode codepoint offsets")
        edges = [0] + offsets + [len(unit["source"])]
        texts = [unit["source"][a:b] for a, b in zip(edges, edges[1:])]
        _require(all(0 < len(v) <= MAX_SOURCE and v.strip() for v in texts),
                 "each semantic child must contain text and be at most 2048 codepoints")
        children = []
        for i, value in enumerate(texts):
            child = _new_unit(unit_id + ".part" + str(i + 1).zfill(4), unit["kind"], value, unit["heading_path"])
            child.update(parent_id=unit_id, part_index=i, has_more=i < len(texts) - 1)
            children.append(child)
        index = data["units"].index(unit)
        data["units"][index:index + 1] = children
        for i, u in enumerate(data["units"]):
            u["order"] = i
        h["revision"] += 1
        _save(path, data)
        return {"split": unit_id, "revision": h["revision"], "children": [
            {"id": u["id"], "characters": len(u["source"]), "source_hash": u["source_hash"],
             "part_index": u["part_index"], "has_more": u["has_more"]} for u in children],
                "reconstruction_hash": digest("".join(texts))}


def _envelope(data, unit):
    # Fixed, bounded context. No neighbor/count option can enlarge a dispatched block.
    parents = {p["id"]: p for p in data["document"]["parents"]}
    sources = {pid: "".join(u["source"] for u in data["units"] if u["parent_id"] == pid) for pid in parents}
    context = {"heading_path": [sources[p] for p in unit["heading_path"]],
               "shared": data["document"]["context"]}
    for block in data["document"]["blocks"]:
        if block["type"] == "table" and unit["parent_id"] in _structural_order([block]):
            context["table_headers"] = [sources[pid] for pid in block["headers"]]
            break
    # A single serialized text excerpt is explicitly context, never source-to-translate.
    raw = _canonical(context)
    return {"text": raw[:MAX_CONTEXT], "truncated": len(raw) > MAX_CONTEXT,
            "character_limit": MAX_CONTEXT}


def next_block(path):
    with _lock(path):
        data = load_jsonl(path)
        h = data["document"]
        blocked = oversized(data)
        _require(not blocked, "oversized sources require agent-selected semantic splits: " + _canonical(blocked))
        active = h["workflow"]["active"]
        remaining = [u for u in data["units"] if u["target"] is None]
        if not remaining:
            return {"complete": True, "saved": len(data["units"]),
                    "reviewed": sum(u["status"] == "reviewed" for u in data["units"]),
                    "note": "Saved is distinct from reviewed; export defaults to reviewed."}
        unit = remaining[0]
        if active is None:
            h["revision"] += 1
            active = {"block_id": "b" + secrets.token_hex(16), "revision": h["revision"],
                      "ids": [unit["id"]], "source_hashes": {unit["id"]: unit["source_hash"]}}
            h["workflow"]["active"] = active
            _save(path, data)
        return {"complete": False, **copy.deepcopy(active), "document_id": h["document_id"],
                "units": [{k: unit[k] for k in ("id", "parent_id", "part_index", "has_more",
                                               "kind", "source", "source_hash")}],
                "source_characters": len(unit["source"]), "context": _envelope(data, unit),
                "languages": h["languages"]}


def commit(path, payload):
    _keys(payload, COMMIT_KEYS, "commit payload (target-only)")
    _require(_id(payload["operation_id"]), "invalid operation_id")
    fingerprint = digest(_canonical(payload))
    with _lock(path):
        data = load_jsonl(path)
        h = data["document"]
        old = h["workflow"]["operations"].get(payload["operation_id"])
        if old is not None:
            _require(old["request_hash"] == fingerprint, "operation_id reused with different content")
            return copy.deepcopy(old["receipt"])
        active = h["workflow"]["active"]
        _require(active is not None, "request next before committing")
        _require(type(payload["revision"]) is int and payload["revision"] == h["revision"]
                 and payload["revision"] == active["revision"], "stale revision")
        _require(payload["block_id"] == active["block_id"], "wrong active block ID")
        _require(payload["source_hashes"] == active["source_hashes"], "stale or extra source IDs/hashes")
        _require(isinstance(payload["targets"], dict) and set(payload["targets"]) == set(active["ids"]),
                 "targets must match exact active IDs")
        for u in data["units"]:
            if u["id"] in active["ids"]:
                target = payload["targets"][u["id"]]
                _text(target, "target")
                u.update(target=target, target_hash=digest(target), target_source_hash=u["source_hash"],
                         status="draft", review=None)
        h["revision"] += 1
        receipt = {"saved": active["ids"], "revision": h["revision"],
                   "block_id": active["block_id"], "operation_id": payload["operation_id"],
                   "reviewed": False}
        h["workflow"]["operations"][payload["operation_id"]] = {
            "request_hash": fingerprint, "receipt": receipt}
        h["workflow"]["active"] = None
        _save(path, data)
        return receipt


def review(path, payload):
    _keys(payload, {"operation_id", "revision", "unit", "source_hash", "target_hash",
                    "reviewer", "note"}, "review payload")
    _require(_id(payload["operation_id"]), "invalid operation_id")
    fingerprint = digest(_canonical(payload))
    with _lock(path):
        data = load_jsonl(path)
        h = data["document"]
        old = h["workflow"]["operations"].get(payload["operation_id"])
        if old is not None:
            _require(old["request_hash"] == fingerprint, "operation_id reused with different content")
            return copy.deepcopy(old["receipt"])
        _require(h["workflow"]["active"] is None, "save active block before recording review")
        _require(type(payload["revision"]) is int and payload["revision"] == h["revision"], "stale revision")
        unit = next((u for u in data["units"] if u["id"] == payload["unit"]), None)
        _require(unit is not None and unit["target"] is not None, "review requires a saved target")
        _require(payload["source_hash"] == unit["source_hash"]
                 and payload["target_hash"] == unit["target_hash"], "stale source/target review hash")
        _text(payload["reviewer"], "reviewer")
        _text(payload["note"], "review note", empty=True)
        unit["review"] = {k: payload[k] for k in ("source_hash", "target_hash", "reviewer", "note")}
        unit["status"] = "reviewed"
        h["revision"] += 1
        receipt = {"reviewed": unit["id"], "revision": h["revision"],
                   "note": "Caller review attestation recorded; meaning was not evaluated."}
        h["workflow"]["operations"][payload["operation_id"]] = {
            "request_hash": fingerprint, "receipt": receipt}
        _save(path, data)
        return receipt


def revise(path, payload):
    """Correct one saved target with CAS; preserve source and invalidate old review."""
    _keys(payload, {"operation_id", "revision", "unit", "source_hash", "target_hash", "target"},
          "revision payload (target-only)")
    _require(_id(payload["operation_id"]), "invalid operation_id")
    fingerprint = digest(_canonical(payload))
    with _lock(path):
        data = load_jsonl(path)
        h = data["document"]
        old = h["workflow"]["operations"].get(payload["operation_id"])
        if old is not None:
            _require(old["request_hash"] == fingerprint, "operation_id reused with different content")
            return copy.deepcopy(old["receipt"])
        _require(h["workflow"]["active"] is None, "save active block before revising a saved target")
        _require(type(payload["revision"]) is int and payload["revision"] == h["revision"], "stale revision")
        unit = next((u for u in data["units"] if u["id"] == payload["unit"]), None)
        _require(unit is not None and unit["target"] is not None, "revision requires a saved target")
        _require(payload["source_hash"] == unit["source_hash"]
                 and payload["target_hash"] == unit["target_hash"], "stale source/target revision hash")
        _text(payload["target"], "target")
        unit.update(target=payload["target"], target_hash=digest(payload["target"]),
                    status="draft", review=None)
        h["revision"] += 1
        receipt = {"revised": unit["id"], "revision": h["revision"], "reviewed": False}
        h["workflow"]["operations"][payload["operation_id"]] = {
            "request_hash": fingerprint, "receipt": receipt}
        _save(path, data)
        return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    read = commands.add_parser("read-source")
    read.add_argument("source", type=Path)
    read.add_argument("--receipt", type=Path, required=True)
    read.add_argument("--continue", dest="continuation")
    ack = commands.add_parser("ack-source")
    ack.add_argument("source", type=Path)
    ack.add_argument("--receipt", type=Path, required=True)
    ack.add_argument("--source-hash", required=True)
    ack.add_argument("--token", required=True)
    init = commands.add_parser("init")
    init.add_argument("source", type=Path)
    init.add_argument("--receipt", type=Path, required=True)
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--source-lang", required=True)
    init.add_argument("--target-lang", required=True)
    init.add_argument("--source-dir", choices=["ltr", "rtl"], default="ltr")
    init.add_argument("--target-dir", choices=["ltr", "rtl"], default="ltr")
    init.add_argument("--context", type=Path)
    for name in ("oversize", "next", "validate", "split", "commit", "review", "revise", "export", "inspect"):
        cmd = commands.add_parser(name)
        cmd.add_argument("data", type=Path)
        if name == "validate":
            cmd.add_argument("--ready", action="store_true")
        if name in ("commit", "review", "revise"):
            cmd.add_argument("--payload", type=Path, required=True)
        if name == "split":
            cmd.add_argument("--unit", required=True)
            cmd.add_argument("--offsets", required=True)
            cmd.add_argument("--source-hash", required=True)
            cmd.add_argument("--revision", type=int, required=True)
        if name == "export":
            cmd.add_argument("--output", type=Path, required=True)
            cmd.add_argument("--allow-draft", action="store_true")
        if name == "inspect":
            cmd.add_argument("--unit", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "read-source":
            result = read_source(args.source, args.receipt, args.continuation)
        elif args.command == "ack-source":
            result = ack_source(args.source, args.receipt, args.source_hash, args.token)
        elif args.command == "init":
            context = _json(args.context.read_text("utf-8")) if args.context else None
            result = initialize(args.source, args.receipt, args.output, args.source_lang,
                                args.target_lang, args.source_dir, args.target_dir, context)
        elif args.command == "next":
            result = next_block(args.data)
        elif args.command == "split":
            result = split_unit(args.data, args.unit, [int(x) for x in args.offsets.split(",")],
                                args.source_hash, args.revision)
        elif args.command in ("commit", "review", "revise"):
            result = globals()[args.command](args.data, _json(args.payload.read_text("utf-8")))
        else:
            data = load_jsonl(args.data, require_ready=getattr(args, "ready", False))
            if args.command == "oversize":
                result = {"revision": data["document"]["revision"], "oversize": oversized(data)}
            elif args.command == "validate":
                result = {"valid": True, "revision": data["document"]["revision"],
                          "ready": bool(args.ready), "note": "Structure/state only; semantic review is manual."}
            elif args.command == "inspect":
                unit = next((u for u in data["units"] if u["id"] == args.unit), None)
                _require(unit is not None, "unknown unit")
                result = {"revision": data["document"]["revision"], "unit": unit}
            else:
                _require(all(u["target"] is not None for u in data["units"]), "export requires all targets saved")
                legacy_data = to_legacy_document(data, require_ready=not args.allow_draft)
                with _lock(args.output):
                    _atomic(args.output, json.dumps(legacy_data, ensure_ascii=False, indent=2) + "\n", new=True)
                result = {"exported": str(args.output), "review_gate": not args.allow_draft}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
