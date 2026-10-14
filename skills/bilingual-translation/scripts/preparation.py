"""In-memory, source-order preparation. The caller owns persistence and revisions."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import secrets

_SPEC = importlib.util.spec_from_file_location(
    "_preparation_core", Path(__file__).with_name("translation_workflow.py"))
core = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(core)

PAGE_SOURCE = 8192
CONTEXT_SIDE = 24


class PreparationError(ValueError):
    """A concise correction hint with bounded, already-delivered source excerpts."""

    def __init__(self, message, details):
        super().__init__(message)
        self.details = details


def _boundary_context(source, offset):
    return {"left": source[max(0, offset - CONTEXT_SIDE):offset],
            "right": source[offset:offset + CONTEXT_SIDE]}


def create(source_text, source_lang="en", target_lang="fr",
           source_dir="ltr", target_dir="ltr", context=None):
    core._text(source_text, "source")
    units, blocks, layout = core.import_markdown(source_text)
    parents = [{k: u[k] for k in ("id", "kind", "source_hash", "heading_path")} |
               {"char_count": len(u["source"])} for u in units]
    for index, unit in enumerate(units):
        unit["order"] = index
    return {"document": {
        "record_type": "document", "document_id": "d" + secrets.token_hex(12),
        "revision": 0,
        "languages": {"source": {"tag": source_lang, "dir": source_dir},
                      "target": {"tag": target_lang, "dir": target_dir}},
        "source": {"sha256": core.digest(source_text), "char_count": len(source_text),
                   "format": "markdown"},
        "blocks": blocks, "parents": parents, "source_layout": layout,
        "context": copy.deepcopy(context) if context is not None else {},
        "workflow": {"active": None, "operations": {}, "review_round": 0,
                     "sequence": 0, "todos": [], "seen": []},
        "preparation": {"cursor": 0, "delivered": [], "pending": [],
                        "complete": False, "ref": None}},
        "units": units}


def batch_reference(data):
    """Bind the current original-parent batch independently of later revisions."""
    h = data["document"]
    p = h["preparation"]
    selected = set(p["delivered"])
    binding = core.digest(core._canonical([
        h["document_id"], h["source"]["sha256"], "prepare", p["cursor"],
        [[v["id"], v["source_hash"]] for v in h["parents"] if v["id"] in selected]]))
    return str(p["cursor"]) + "-" + core.REF_WORDS[int(binding, 16) % len(core.REF_WORDS)]


def _metadata(data):
    result = {}
    for block in data["document"]["blocks"]:
        kind = block["type"]
        if kind == "heading":
            result[block["unit"]] = {"level": block["level"]}
        elif kind == "list":
            for index, uid in enumerate(block["items"]):
                result[uid] = {"list_index": index, "ordered": block["ordered"]}
        elif kind == "table":
            for column, uid in enumerate(block["headers"]):
                result[uid] = {"table_row": -1, "table_column": column}
            for row, cells in enumerate(block["rows"]):
                for column, uid in enumerate(cells):
                    result[uid] = {"table_row": row, "table_column": column}
    return result


def deliver(data):
    h = data["document"]
    p = h["preparation"]
    core._require(not p["pending"], "split all pending oversized units before continuing preparation")
    core._require(not p["complete"], "preparation is already complete")
    parents = h["parents"]
    start = p["cursor"]
    end, characters = start, 0
    while end < len(parents) and characters < PAGE_SOURCE:
        characters += parents[end]["char_count"]
        end += 1
    ids = [v["id"] for v in parents[start:end]]
    selected = set(ids)
    metadata = _metadata(data)
    units = []
    for unit in data["units"]:
        if unit["parent_id"] in selected:
            out = {key: copy.deepcopy(unit[key]) for key in
                   ("id", "parent_id", "part_index", "has_more", "kind", "source", "heading_path")}
            out.update(metadata.get(unit["parent_id"], {}))
            units.append(out)
    oversized = [{"id": u["id"], "characters": len(u["source"]),
                  "minimum_parts": (len(u["source"]) + core.MAX_SOURCE - 1) // core.MAX_SOURCE}
                 for u in units if len(u["source"]) > core.MAX_SOURCE]
    p.update(cursor=end, delivered=ids, pending=[v["id"] for v in oversized],
             complete=end == len(parents) and not oversized)
    p["ref"] = batch_reference(data)
    total = sum(v["char_count"] for v in parents)
    completed = sum(v["char_count"] for v in parents[:end])
    previous = sum(v["char_count"] for v in parents[:start])
    response = {"phase": "prepare", "units": units, "ref": p["ref"],
                "complete": p["complete"], "oversize": oversized,
                "pending": list(p["pending"]), "characters": characters}
    if completed == total or completed * 20 // total > previous * 20 // total:
        response["progress"] = {"phase": "prepare", "completed": completed,
                                "total": total, "unit": "codepoints",
                                "percent": completed * 100 // total}
    return response


def _cut_offsets(source, cuts):
    core._require(isinstance(cuts, list) and cuts, "provide nonempty cuts with exact left/right anchors")
    offsets = []
    for cut_index, cut in enumerate(cuts):
        core._keys(cut, {"left", "right"}, "cut")
        left, right = cut["left"], cut["right"]
        core._require(isinstance(left, str) and bool(left) and
                      isinstance(right, str) and bool(right),
                      "cut anchors must be nonempty exact strings")
        needle = left + right
        index = source.find(needle)
        first, match_count, contexts = index, 0, []
        while index >= 0:
            match_count += 1
            if len(contexts) < 3:
                contexts.append(_boundary_context(source, index + len(left)))
            index = source.find(needle, index + 1)
        if match_count != 1:
            message = ("cut anchors do not match adjacent source text" if match_count == 0 else
                       "cut anchors are ambiguous; include more surrounding text")
            raise PreparationError(message, {"cut_index": cut_index,
                                             "match_count": match_count,
                                             "contexts": contexts})
        offsets.append(first + len(left))
    core._require(offsets == sorted(set(offsets)) and
                  0 < offsets[0] and offsets[-1] < len(source),
                  "cuts must identify distinct interior boundaries in source order")
    return offsets


def split(data, ref, unit, cuts):
    h = data["document"]
    p = h["preparation"]
    core._require(ref == p["ref"] == batch_reference(data), "use the current preparation ref")
    core._require(unit in p["pending"], "split requires a pending oversized unit")
    old = next((v for v in data["units"] if v["id"] == unit), None)
    core._require(old is not None and old["parent_id"] == unit and old["target"] is None,
                  "split requires an untranslated original parent")
    source = old["source"]
    core._require(core.digest(source) == old["source_hash"], "source hash mismatch")
    parent = next(v for v in h["parents"] if v["id"] == unit)
    core._require(parent["source_hash"] == old["source_hash"] and
                  parent["char_count"] == len(source), "parent reconstruction mismatch")
    offsets = _cut_offsets(source, cuts)
    edges = [0] + offsets + [len(source)]
    texts = [source[a:b] for a, b in zip(edges, edges[1:])]
    bad_children = []
    for index, value in enumerate(texts):
        if not value.strip() or len(value) > core.MAX_SOURCE:
            bad_children.append({
                "part_index": index, "characters": len(value),
                "excess": max(0, len(value) - core.MAX_SOURCE),
                "blank": not bool(value.strip()),
                "start": _boundary_context(source, edges[index]),
                "end": _boundary_context(source, edges[index + 1])})
    if bad_children:
        raise PreparationError("each child must contain text and be at most 2048 codepoints",
                               {"children": bad_children})
    core._require("".join(texts) == source, "source reconstruction mismatch")
    children = []
    for index, value in enumerate(texts):
        child = core._new_unit(unit + ".part" + str(index + 1).zfill(4),
                               old["kind"], value, old["heading_path"])
        child.update(parent_id=unit, part_index=index, has_more=index < len(texts) - 1)
        children.append(child)
    index = data["units"].index(old)
    data["units"][index:index + 1] = children
    for index, value in enumerate(data["units"]):
        value["order"] = index
    p["pending"].remove(unit)
    p["complete"] = p["cursor"] == len(h["parents"]) and not p["pending"]
    return {"split": unit, "children": [v["id"] for v in children],
            "ref": p["ref"], "complete": p["complete"], "pending": list(p["pending"])}
