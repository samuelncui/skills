#!/usr/bin/env python3
"""Execute the example's source-only checkpoint before authoring target text."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parents[1]
spec = importlib.util.spec_from_file_location("translation_contract", SKILL / "scripts/translation_contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def prepare(output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("Choose a new master; the example never overwrites an existing manuscript")
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    original = (ROOT / manifest["source"]["path"]).read_bytes()
    if hashlib.sha256(original).hexdigest() != manifest["source"]["sha256"]:
        raise ValueError("Original source differs from the example manifest")
    kinds = ["title", "heading", "paragraph", "list_item", "list_item",
             "table_cell", "table_cell", "table_cell", "table_cell",
             "table_cell", "table_cell", "caption", "paragraph", "caption", "alt_text"]
    units = []
    for entry, kind in zip(manifest["units"], kinds, strict=True):
        source = original[entry["start"]:entry["end"]].decode("utf-8")
        units.append({"id": entry["id"], "kind": kind, "source": source,
                      "target": None, "source_hash": contract.source_digest(source),
                      "target_source_hash": None, "status": "untranslated",
                      "locator": f"source.txt bytes {entry['start']}:{entry['end']}"})
    master = {"schema_version": 1,
              "languages": {"source": {"tag": "en", "dir": "ltr"},
                            "target": {"tag": "fr", "dir": "ltr"}},
              "source_revision": "sha256:" + manifest["source"]["sha256"],
              "context": {"summary": "Shared seed shelf: packet preparation, register, damp-packet condition and shared figure.",
                          "audience": "Community visitors"},
              "units": units, "blocks": [
                  {"type": "heading", "unit": "title", "level": 1},
                  {"type": "heading", "unit": "preparing", "level": 2},
                  {"type": "paragraph", "unit": "intro"},
                  {"type": "list", "ordered": False, "items": ["dry", "label"]},
                  {"type": "table", "headers": ["crop-header", "count-header"],
                   "rows": [["bean-name", "bean-count"], ["pea-name", "pea-count"]],
                   "caption": "table-caption"},
                  {"type": "paragraph", "unit": "condition"},
                  {"type": "figure", "asset": "assets/shelf.png",
                   "caption": "figure-caption", "alt": "figure-alt"}]}
    contract.save_document(output, master)
    # This readback is an executed boundary, not a promise inside a translator.
    saved = json.loads(output.read_text())
    errors = contract.untranslated_errors(saved)
    if errors:
        raise ValueError("\n".join(errors))
    print(json.dumps({"preparation_readback": True, "units": len(saved["units"]),
                      "master_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                      "next": contract.unit_view(saved, include_context=True)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.output)
