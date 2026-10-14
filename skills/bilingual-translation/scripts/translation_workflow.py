#!/usr/bin/env python3
"""Source-first JSONL storage and validation. Receipts attest delivery/review, never understanding."""
from __future__ import annotations

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
import tempfile

_SPEC = importlib.util.spec_from_file_location(
    "_translation_semantic_contract", Path(__file__).with_name("translation_contract.py"))
exchange = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(exchange)

MAX_SOURCE = 2048
MAX_CONTEXT = 1024
READ_PAGE = 8192
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
BAD_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069\ud800-\udfff]")
UNIT_KEYS = {"record_type", "id", "parent_id", "part_index", "has_more", "kind",
             "source", "target", "source_hash", "target_source_hash", "status",
             "order", "heading_path", "review", "target_hash"}
HEADER_KEYS = {"record_type", "document_id", "revision", "languages",
               "source", "blocks", "parents", "source_layout", "context", "workflow",
               "preread"}
PARENT_KEYS = {"id", "kind", "source_hash", "char_count", "heading_path"}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# A short confirmation cue, not authentication or evidence of comprehension.
REF_WORDS = tuple("""apple arrow beach bird bloom blue boat book bread bridge bright brook
brown brush cabin calm candle cedar chair cherry clear cloud coast coral crane creek
crown dance dawn deer dream drift dune eagle earth east ember field fire flame
flower forest fox fresh frost garden glass globe gold grape grass green grove harbor
hawk hazel hill honey horse house ice island ivory jade jewel lake leaf lemon
light lily lion maple marsh meadow mint moon moss mountain music night north oak
ocean olive orange owl palm paper park peach pearl pine pink plum pond quiet
rain raven reed ridge river road robin rock rose round ruby sage sand sea
seed shade shell shore silver sky small snow soft south spark spring star stone
storm stream sun sweet swift table tall tea thorn tide tiger trail tree tulip
vale violet warm water wave west wheat white wild willow wind wing winter wood""".split())
REFERENCE = re.compile(r"([1-9][0-9]{0,17})-([a-z]+)\Z")


def reference_number(value):
    match = REFERENCE.fullmatch(value) if isinstance(value, str) else None
    _require(match is not None and match[2] in REF_WORDS, "invalid numbered reference")
    return int(match[1])


def compact_binding(data, phase, units):
    """Full internal binding; the public word is only a low-cost confirmation cue."""
    h = data["document"]
    return digest(_canonical([h["document_id"], h["revision"], phase,
                              [[u["id"], u["source_hash"], u["target_hash"]] for u in units]]))


def compact_reference(data, phase, units):
    binding = compact_binding(data, phase, units)
    return str(data["document"]["revision"]) + "-" + REF_WORDS[int(binding, 16) % len(REF_WORDS)]


def _validate_operation_journal(data):
    h, units = data["document"], data["units"]
    operations = h["workflow"]["operations"]
    for record in operations.values():
        _keys(record, {"request_hash", "receipt"}, "operation journal record")
        _require(_hash(record["request_hash"]) and isinstance(record["receipt"], dict),
                 "invalid operation journal record")
    if "_compact_seen" in operations:
        record = operations["_compact_seen"]
        _keys(record["receipt"], {"phases"}, "compact phases")
        phases = record["receipt"]["phases"]
        _require(isinstance(phases, list) and all(p in ("translate", "review") for p in phases)
                 and len(set(phases)) == len(phases) and record["request_hash"] == digest("phases"),
                 "invalid compact phases")
    if "_compact_active" not in operations:
        return
    record = operations["_compact_active"]
    a = record["receipt"]
    _keys(a, {"phase", "ids", "ref", "page", "last_continue", "initial", "binding"}, "compact active")
    _require(record["request_hash"] == digest(_canonical(a)), "invalid compact journal checksum")
    _require(a["phase"] in ("translate", "review") and isinstance(a["ids"], list)
             and a["ids"] and all(_id(uid) for uid in a["ids"]), "invalid compact phase/IDs")
    selected = [u for u in units if u["id"] in a["ids"]]
    _require([u["id"] for u in selected] == a["ids"]
             and all(b["order"] == a0["order"] + 1 for a0, b in zip(selected, selected[1:])),
             "invalid compact selection order")
    _require(a["ref"] == compact_reference(data, a["phase"], selected)
             and a["binding"] == compact_binding(data, a["phase"], selected), "stale compact reference")
    _require(type(a["page"]) is int and a["page"] >= 0 and type(a["initial"]) is bool
             and (a["last_continue"] is None or isinstance(a["last_continue"], str)),
             "invalid compact page metadata")
    _require(sum(len(u["source"]) for u in selected) <= MAX_SOURCE,
             "oversized active source")
    if a["phase"] == "translate":
        remaining = [u for u in units if u["target"] is None]
        _require(a["ids"] == [u["id"] for u in remaining[:len(selected)]]
                 and a["page"] == 0 and a["last_continue"] is None, "invalid compact translation block")
    else:
        _require(all(u["target"] is not None for u in units), "review requires all saved targets")
        # This budget is part of the compact protocol, independent of source cap.
        target_chars = sum(len(u["target"]) for u in selected)
        _require((len(selected) == 1 or target_chars <= 8192)
                 and a["page"] <= (target_chars - 1) // 8192, "invalid compact review page/budget")


def _json(text):
    return json.loads(text, object_pairs_hook=exchange._object, parse_constant=exchange._nonfinite)


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
            _require(reference_number(state["token"]) == (state["end"] + READ_PAGE - 1) // READ_PAGE,
                     "invalid read receipt; create a new receipt and reread the source")
            if continuation == state["last_request"] and state["page"] is not None:
                return state["page"]
            _require(continuation is not None and continuation == state["token"],
                     "use the returned continue token; reread with a new receipt to start over")
            _require(state["end"] < len(text), "all source pages delivered; acknowledge source")
        start = state["end"]
        end = min(start + READ_PAGE, len(text))
        token = str(start // READ_PAGE + 1) + "-" + secrets.choice(REF_WORDS)
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
               source_dir="ltr", target_dir="ltr", context=None, initial_operations=None, source_splits=None):
    text = _source(source)
    state = _json(Path(receipt).read_text("utf-8"))
    _require(state.get("acknowledged") is True and state.get("source_hash") == digest(text)
             and state.get("end") == len(text), "acknowledge complete current source before init")
    units, blocks, layout = import_markdown(text)
    parents = [{k: u[k] for k in ("id", "kind", "source_hash", "heading_path")} |
               {"char_count": len(u["source"])} for u in units]
    for i, u in enumerate(units):
        u["order"] = i
    document = {"record_type": "document",
                "document_id": "d" + secrets.token_hex(12), "revision": 0,
                "languages": {"source": {"tag": source_lang, "dir": source_dir},
                              "target": {"tag": target_lang, "dir": target_dir}},
                "source": {"sha256": digest(text), "char_count": len(text), "format": "markdown"},
                "blocks": blocks, "parents": parents, "source_layout": layout,
                "context": context or {}, "workflow": {
                    "operations": {} if callable(initial_operations) else initial_operations or {}},
                "preread": {"source_hash": digest(text), "acknowledged": True}}
    data = {"document": document, "units": units}
    if source_splits is not None:
        _require(isinstance(source_splits, dict), "split plan must be an ID-to-offsets object")
        _require(set(source_splits) == {u["id"] for u in units if len(u["source"]) > MAX_SOURCE},
                 "split plan must cover exactly all oversized source units")
        for unit in list(units):
            if unit["id"] in source_splits:
                _split_data(data, unit["id"], source_splits[unit["id"]],
                            unit["source_hash"], document["revision"])
    if callable(initial_operations):
        # Build protocol receipts after stable document IDs exist, within the
        # same initial transaction.
        document["workflow"]["operations"] = initial_operations(data)
    with _lock(output):
        _save(output, data, new=True)
    # Readback is part of init, before any target authoring.
    checked = load_jsonl(output)
    return {"initialized": True, "revision": document["revision"], "document_id": document["document_id"],
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
    return {"languages": copy.deepcopy(h["languages"]),
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
    _require(h["record_type"] == "document", "expected JSONL document record")
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
    errors = exchange.validate_document(_joined(data))
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
    _keys(h["workflow"], {"operations"}, "workflow")
    _require(isinstance(h["workflow"]["operations"], dict), "invalid operations")
    _validate_operation_journal(data)
    if require_ready:
        _require(not oversized(data)
                 and h["workflow"]["operations"].get("_compact_active") is None, "master not ready")
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


def to_exchange_document(data, require_ready=True):
    validate(data, require_ready)
    return _joined(data)


def _save(path, data, new=False):
    validate(data)
    _atomic(path, "\n".join(_canonical(v) for v in [data["document"]] + data["units"]) + "\n", new)


def oversized(data):
    return [{"id": u["id"], "parent_id": u["parent_id"], "characters": len(u["source"]),
             "source_hash": u["source_hash"]} for u in data["units"] if len(u["source"]) > MAX_SOURCE]


def _split_data(data, unit_id, offsets, source_hash, revision):
    """Apply a checked source split inside the initialization transaction."""
    h = data["document"]
    _require(h["revision"] == revision, "stale revision")
    _require(h["workflow"]["operations"].get("_compact_active") is None,
             "finish active work before changing segmentation")
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
    return {"split": unit_id, "revision": h["revision"], "children": [
        {"id": u["id"], "characters": len(u["source"]), "source_hash": u["source_hash"],
         "part_index": u["part_index"], "has_more": u["has_more"]} for u in children],
            "reconstruction_hash": digest("".join(texts))}
