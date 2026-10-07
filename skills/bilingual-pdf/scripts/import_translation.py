#!/usr/bin/env python3
"""Map reviewed translation-contract v1 pairs into the existing PDF layout API."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

# Renderer ownership stays here. Translation validation stays in its installed skill.
import bilingual_pdf as pdf


def load_contract(skill_path):
    root = Path(skill_path).expanduser().resolve()
    path = root / "scripts" / "translation_contract.py"
    if not (root / "SKILL.md").is_file() or not path.is_file():
        raise pdf.InputError("Discover the installed bilingual-translation skill and pass its directory with --translation-skill.")
    spec = importlib.util.spec_from_file_location("bilingual_translation_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "CONTRACT_VERSION", None) != 1:
        raise pdf.InputError("This adapter requires bilingual-translation contract version 1; use a tested compatible installation.")
    return module


def convert_pairs(data, contract, source_side="left"):
    errors = contract.validate_document(data, require_ready=True)
    if errors:
        raise pdf.InputError("Translation pairs are not ready: " + "; ".join(errors))
    if source_side not in {"left", "right"}:
        raise pdf.InputError("source_side must be left or right")
    roles = ["source", "target"] if source_side == "left" else ["target", "source"]
    languages = [data["languages"][role]["tag"] for role in roles]
    for role, tag in zip(roles, languages):
        if tag not in pdf.PROFILES:
            raise pdf.InputError("Unsupported PDF profile for " + role + ": " + tag + ". Use a separately verified native language/font setup; the translation contract itself remains language-neutral.")
        if data["languages"][role]["dir"] != pdf.PROFILES[tag]["direction"]:
            raise pdf.InputError("PDF profile direction differs from the declared " + role + " direction")
    units = {unit["id"]: unit for unit in data["units"]}
    def pair(ident):
        unit = units[ident]
        return [unit[role] for role in roles]
    blocks = data["blocks"]
    if not blocks or blocks[0]["type"] != "heading" or units[blocks[0]["unit"]]["kind"] != "title":
        raise pdf.InputError("PDF import needs a first heading block whose unit kind is title; supply a reviewed paired title or use native authoring.")
    title_id = blocks[0]["unit"]
    result = {"languages": languages, "title": pair(title_id), "blocks": []}
    mapping = {title_id: "pt-title"}
    # Semantic IDs remain intact in the preserved contract and mapping. Safe
    # physical anchors are generated independently, avoiding PDF-specific ID rules.
    for index, block in enumerate(blocks[1:], 1):
        ident = "pair-" + str(index)
        kind = block["type"]
        item = {"id": ident, "kind": kind}
        if kind in {"heading", "paragraph"}:
            if kind == "heading" and block["level"] != 2:
                raise pdf.InputError("The PDF JSON route maps level-2 headings to sections. Use native LaTeX for deeper headings rather than flattening them.")
            item["text"] = pair(block["unit"])
            mapping[block["unit"]] = ident
        elif kind == "list":
            if block["ordered"]:
                raise pdf.InputError("The existing PDF JSON list route is unordered. Use native enumerate item pairs to preserve an ordered list.")
            item["text"] = [[units[x][role] for x in block["items"]] for role in roles]
            for n, unit_id in enumerate(block["items"], 1):
                mapping[unit_id] = ident + ".item-" + str(n)
        elif kind == "table":
            item["headers"] = [[units[x][role] for x in block["headers"]] for role in roles]
            item["rows"] = [[[units[x][role] for x in row] for row in block["rows"]] for role in roles]
            for row_index, row in enumerate([block["headers"]] + block["rows"]):
                for cell_index, unit_id in enumerate(row):
                    mapping[unit_id] = {"anchor": ident + ".row-" + str(row_index), "cell": cell_index}
            if "caption" in block:
                item["text"] = pair(block["caption"])
                mapping[block["caption"]] = ident + ".caption"
        elif kind == "figure":
            item.update(image=block["asset"], placement="shared", caption_prefix="none", text=pair(block["caption"]))
            mapping[block["caption"]] = ident + ".caption"
            mapping[block["alt"]] = {"asset": block["asset"], "use": "retained-description", "pdf_alt_encoded": False}
        else:
            raise pdf.InputError("Unsupported block for PDF import: " + str(kind))
        result["blocks"].append(item)
    if not result["blocks"]:
        raise pdf.InputError("PDF import needs at least one content block after the title")
    # The existing PDF API accepts metadata and ignores it during layout. This
    # keeps every source/target unit, locator and review hash available for edits.
    result["translation"] = {"contract_version": 1, "column_roles": roles, "unit_mapping": mapping, "content": data}
    pdf.validate(result)
    return result


def read_json(path):
    def unique_object(items):
        result = {}
        for key, value in items:
            if key in result:
                raise pdf.InputError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise pdf.InputError("Non-finite JSON value: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--translation-skill", required=True, type=Path)
    parser.add_argument("--source-side", choices=["left", "right"], default="left")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        data = read_json(args.input)
        result = convert_pairs(data, load_contract(args.translation_skill), args.source_side)
        if args.output.exists() or args.output.is_symlink():
            raise pdf.InputError("Output already exists; choose a new file to preserve previous inputs")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
        print(json.dumps({"ok": True, "output": str(args.output), "asset_root": str(args.input.resolve().parent), "note": "Use the original input directory as --asset-root when exporting. Figure descriptions are retained as metadata; this does not create a tagged accessible PDF."}))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
