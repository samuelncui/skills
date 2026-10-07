#!/usr/bin/env python3
"""Render literal paired text as portable HTML; optionally import translation v1."""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import importlib.util
import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path, PurePosixPath

LAYOUT_VERSION = 1
SKILL_ROOT = Path(__file__).resolve().parent.parent
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*\Z")
LANG = re.compile(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*\Z")
LENGTH = re.compile(r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:rem|em|px|ch)\Z")
COLOR = re.compile(r"#[0-9A-Fa-f]{6}\Z")
FONT = re.compile(r"[A-Za-z0-9][A-Za-z0-9 -]{0,79}\Z")
LENGTH_STYLES = {"max_width", "column_gap", "block_gap", "font_size", "page_padding"}
COLOR_STYLES = {"background", "foreground", "muted", "border", "accent"}
FONT_STYLES = {"source_font", "target_font"}
RATIO_STYLES = {"source_weight", "target_weight"}
STYLE_KEYS = LENGTH_STYLES | COLOR_STYLES | FONT_STYLES | RATIO_STYLES | {"line_height"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class RenderError(ValueError):
    """An actionable, safe input or output error."""


def _plain(value):
    return isinstance(value, str) and bool(value.strip()) and not any(
        ord(char) < 32 and char not in "\n\t\r" for char in value
    ) and not any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def _object(value, allowed, required, where, errors):
    if not isinstance(value, dict):
        errors.append(f"{where}: expected an object")
        return False
    unknown = set(value) - set(allowed)
    missing = set(required) - set(value)
    if unknown:
        errors.append(f"{where}: unsupported fields: {', '.join(sorted(unknown))}")
    if missing:
        errors.append(f"{where}: missing fields: {', '.join(sorted(missing))}")
    return True


def _asset_name(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    parts = value.split("/")
    return (not PurePosixPath(value).is_absolute()
            and all(part not in {"", ".", ".."} for part in parts)
            and all(re.fullmatch(r"[A-Za-z0-9_. -]+", part) for part in parts)
            and PurePosixPath(value).suffix.lower() in {".png", ".jpg", ".jpeg"})


def validate_document(data):
    """Return layout errors without mutation. This is a rendering schema only."""
    errors = []
    if not _object(data, {"layout_version", "languages", "config", "blocks"},
                   {"layout_version", "languages", "blocks"}, "document", errors):
        return errors
    if type(data.get("layout_version")) is not int or data["layout_version"] != LAYOUT_VERSION:
        errors.append("layout_version: expected 1")
    languages = data.get("languages")
    if _object(languages, {"source", "target"}, {"source", "target"}, "languages", errors):
        for role in ("source", "target"):
            language = languages.get(role)
            if _object(language, {"tag", "dir"}, {"tag", "dir"}, f"languages.{role}", errors):
                if not isinstance(language.get("tag"), str) or not LANG.fullmatch(language["tag"]):
                    errors.append(f"languages.{role}.tag: expected a language tag such as en, zh-CN or ar")
                if language.get("dir") not in ("ltr", "rtl"):
                    errors.append(f"languages.{role}.dir: expected ltr or rtl")
    config = data.get("config", {})
    if _object(config, {"browser_title", "desktop_order", "styles"}, set(), "config", errors):
        if "browser_title" in config and not _plain(config["browser_title"]):
            errors.append("config.browser_title: expected nonempty plain text")
        if config.get("desktop_order", "source-first") not in ("source-first", "target-first"):
            errors.append("config.desktop_order: expected source-first or target-first")
        styles = config.get("styles", {})
        if _object(styles, STYLE_KEYS, set(), "config.styles", errors):
            for key, value in styles.items():
                if key in LENGTH_STYLES:
                    if (not isinstance(value, str) or not LENGTH.fullmatch(value)
                            or float(re.match(r"[0-9.]+", value)[0]) <= 0
                            or float(re.match(r"[0-9.]+", value)[0]) > 1000):
                        errors.append(f"config.styles.{key}: use a positive length up to 1000 in rem, em, px or ch")
                elif key in COLOR_STYLES and (not isinstance(value, str) or not COLOR.fullmatch(value)):
                    errors.append(f"config.styles.{key}: expected a six-digit hex color")
                elif key in FONT_STYLES and (not isinstance(value, list) or not value
                                             or not all(isinstance(x, str) and FONT.fullmatch(x) for x in value)):
                    errors.append(f"config.styles.{key}: expected a nonempty list of simple font family names")
                elif key in RATIO_STYLES | {"line_height"}:
                    if type(value) not in (int, float) or not 0.5 <= value <= 4:
                        errors.append(f"config.styles.{key}: expected a number from 0.5 to 4")
    seen = set()

    def pair(value, where):
        if not _object(value, {"id", "source", "target"}, {"id", "source", "target"}, where, errors):
            return
        identifier = value.get("id")
        if not isinstance(identifier, str) or not ID.fullmatch(identifier):
            errors.append(f"{where}.id: expected a stable identifier starting with an ASCII letter")
        elif identifier in seen:
            errors.append(f"{where}.id: duplicate pair ID {identifier}")
        else:
            seen.add(identifier)
        for role in ("source", "target"):
            if not _plain(value.get(role)):
                errors.append(f"{where}.{role}: expected nonempty literal text; finish unresolved pairs before rendering")

    blocks = data.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        errors.append("blocks: expected a nonempty array")
        return errors
    for i, block in enumerate(blocks):
        where = f"blocks[{i}]"
        if not isinstance(block, dict):
            errors.append(f"{where}: expected an object")
            continue
        kind = block.get("type")
        if kind == "heading":
            _object(block, {"type", "pair", "level"}, {"type", "pair", "level"}, where, errors)
            if type(block.get("level")) is not int or not 1 <= block["level"] <= 6:
                errors.append(f"{where}.level: expected an integer from 1 to 6")
            pair(block.get("pair"), where + ".pair")
        elif kind == "paragraph":
            _object(block, {"type", "pair"}, {"type", "pair"}, where, errors)
            pair(block.get("pair"), where + ".pair")
        elif kind == "list":
            _object(block, {"type", "ordered", "items"}, {"type", "ordered", "items"}, where, errors)
            if type(block.get("ordered")) is not bool:
                errors.append(f"{where}.ordered: expected a boolean")
            if not isinstance(block.get("items"), list) or not block["items"]:
                errors.append(f"{where}.items: expected a nonempty array of pairs")
            else:
                for j, item in enumerate(block["items"]):
                    pair(item, f"{where}.items[{j}]")
        elif kind == "table":
            _object(block, {"type", "headers", "rows", "caption"}, {"type", "headers", "rows"}, where, errors)
            headers, rows = block.get("headers"), block.get("rows")
            if not isinstance(headers, list) or not headers:
                errors.append(f"{where}.headers: expected a nonempty array of pairs")
            else:
                for j, cell in enumerate(headers):
                    pair(cell, f"{where}.headers[{j}]")
            if not isinstance(rows, list) or not rows:
                errors.append(f"{where}.rows: expected a nonempty array")
            else:
                for j, row in enumerate(rows):
                    if not isinstance(row, list) or not isinstance(headers, list) or len(row) != len(headers):
                        errors.append(f"{where}.rows[{j}]: expected the same cell count as headers")
                    elif row:
                        for k, cell in enumerate(row):
                            pair(cell, f"{where}.rows[{j}][{k}]")
            if "caption" in block:
                pair(block["caption"], where + ".caption")
        elif kind == "figure":
            _object(block, {"type", "asset", "caption", "alt"}, {"type", "asset", "caption", "alt"}, where, errors)
            if not _asset_name(block.get("asset")):
                errors.append(f"{where}.asset: expected a relative local PNG or JPEG path without traversal, URL, or backslash")
            pair(block.get("caption"), where + ".caption")
            pair(block.get("alt"), where + ".alt")
        else:
            errors.append(f"{where}.type: expected heading, paragraph, list, table or figure")
    return errors


def _require_valid(data):
    errors = validate_document(data)
    if errors:
        raise RenderError("\n".join(errors))


def load_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RenderError(f"JSON contains duplicate key: {key}")
            result[key] = value
        return result
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream, object_pairs_hook=unique_pairs,
                             parse_constant=lambda value: (_ for _ in ()).throw(RenderError(f"Invalid JSON number: {value}")))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RenderError(f"Cannot read JSON input: {error}") from error


def _no_symlinks(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise RenderError(f"Symlink paths are not accepted: {part.name}")
    return path


def _png_bytes(path):
    if path.stat().st_size > 20 * 1024 * 1024:
        raise RenderError("Figure must be a PNG image no larger than 20 MiB")
    data = path.read_bytes()
    if len(data) > 20 * 1024 * 1024 or not data.startswith(PNG_SIGNATURE):
        raise RenderError("Figure must be a PNG image no larger than 20 MiB")
    offset, chunks, width, height = 8, [], 0, 0
    while offset < len(data):
        if offset + 12 > len(data):
            raise RenderError("Truncated PNG figure")
        size = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(data):
            raise RenderError("Truncated PNG chunk")
        body = data[offset + 8:offset + 8 + size]
        crc = struct.unpack(">I", data[end - 4:end])[0]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise RenderError("PNG figure has a damaged chunk checksum")
        if not chunks and (kind != b"IHDR" or size != 13):
            raise RenderError("PNG figure must begin with IHDR")
        if kind == b"IHDR":
            if chunks:
                raise RenderError("PNG figure contains repeated IHDR")
            width, height = struct.unpack(">II", body[:8])
        chunks.append(kind)
        offset = end
        if kind == b"IEND":
            if size or offset != len(data):
                raise RenderError("PNG figure has data after IEND")
            break
    if not chunks or chunks[-1] != b"IEND" or b"IDAT" not in chunks or not 0 < width <= 16000 or not 0 < height <= 16000:
        raise RenderError("PNG figure requires image data, IEND and dimensions up to 16000 pixels")
    return data


def _jpeg_bytes(path):
    """Check bounded baseline/progressive JPEG framing, not compressed pixels."""
    if path.stat().st_size > 20 * 1024 * 1024:
        raise RenderError("Figure must be a JPEG image no larger than 20 MiB")
    data = path.read_bytes()
    if len(data) > 20 * 1024 * 1024 or not data.startswith(b"\xff\xd8"):
        raise RenderError("Figure must be a JPEG image no larger than 20 MiB")
    offset, components, scanned = 2, None, False
    while offset < len(data):
        if data[offset] != 0xff:
            raise RenderError("Invalid JPEG marker framing")
        while offset < len(data) and data[offset] == 0xff:
            offset += 1
        if offset >= len(data):
            raise RenderError("Truncated JPEG marker")
        marker = data[offset]
        offset += 1
        if marker == 0xd9:
            if offset != len(data) or components is None or not scanned:
                raise RenderError("JPEG requires a frame, scan and final EOI with no trailing data")
            return data
        if marker in {0, 0xd8, 0x01} or 0xd0 <= marker <= 0xd7:
            raise RenderError("Unexpected standalone JPEG marker")
        if offset + 2 > len(data):
            raise RenderError("Truncated JPEG segment")
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        if length < 2 or offset + length > len(data):
            raise RenderError("Invalid JPEG segment length")
        body = data[offset + 2:offset + length]
        offset += length
        if marker in {0xc0, 0xc2}:
            if components is not None or len(body) < 6:
                raise RenderError("Invalid or repeated JPEG frame")
            precision, height, width, components = struct.unpack(">BHHB", body[:6])
            if (precision != 8 or components not in {1, 3, 4}
                    or len(body) != 6 + 3 * components
                    or not 0 < width <= 16000 or not 0 < height <= 16000):
                raise RenderError("JPEG requires an 8-bit frame with dimensions up to 16000 pixels")
        elif 0xc0 <= marker <= 0xcf and marker not in {0xc4, 0xc8, 0xcc}:
            raise RenderError("Only baseline and progressive JPEG frames are supported")
        elif marker == 0xda:
            if (components is None or not body or not 1 <= body[0] <= components
                    or len(body) != 4 + 2 * body[0]):
                raise RenderError("Invalid JPEG scan header")
            scanned = True
            while offset < len(data):
                boundary = data.find(b"\xff", offset)
                if boundary < 0:
                    raise RenderError("JPEG scan has no closing marker")
                after = boundary + 1
                while after < len(data) and data[after] == 0xff:
                    after += 1
                if after >= len(data):
                    raise RenderError("Truncated JPEG scan marker")
                if data[after] == 0 or 0xd0 <= data[after] <= 0xd7:
                    offset = after + 1
                    continue
                offset = boundary
                break
    raise RenderError("JPEG figure is missing final EOI")


def _read_assets(data, root):
    assets = {}
    root = _no_symlinks(root)
    for block in data["blocks"]:
        if block["type"] != "figure" or block["asset"] in assets:
            continue
        name = block["asset"]
        if not _asset_name(name):
            raise RenderError("Only relative local PNG or JPEG asset paths are supported")
        path = _no_symlinks(root / name)
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise RenderError(f"Figure asset is missing or outside the input directory: {name}")
        assets[name] = _png_bytes(path) if path.suffix.lower() == ".png" else _jpeg_bytes(path)
    return assets


def _new_output(path):
    path = _no_symlinks(path)
    if path.exists():
        raise RenderError("Output already exists; choose a new directory to preserve previous files")
    if not path.parent.is_dir():
        raise RenderError("Output parent directory must already exist")
    return path


def _write_bundle(output, files):
    output = _new_output(output)
    # All validation and input reads finish before any output is created.
    output.mkdir()
    try:
        for name, value in files.items():
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(value)
    except Exception:
        shutil.rmtree(output)
        raise
    return output


def _css_value(key, value):
    if key in FONT_STYLES:
        generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"}
        return ", ".join(name if name in generic else '"' + name + '"' for name in value)
    if key in RATIO_STYLES:
        return str(value) + "fr"
    return str(value)


def render_html(data):
    """Return escaped HTML. Asset validation/copy is handled by render_document."""
    _require_valid(data)
    languages = data["languages"]

    def text_role(pair, role, suffix=""):
        language = languages[role]
        identifier = f' id="alt-{pair["id"]}-{role}"' if suffix else ""
        return (f'<span class="text {role}" data-role="{role}" lang="{language["tag"]}" '
                f'dir="{language["dir"]}"{identifier}>{html.escape(pair[role])}</span>')

    def pair_html(pair, tag="div", extra=""):
        return (f'<{tag} class="pair{extra}" id="pair-{pair["id"]}" data-pair-id="{pair["id"]}">'
                + text_role(pair, "source", extra) + text_role(pair, "target", extra) + f'</{tag}>')

    config = data.get("config", {})
    first_heading = next((x["pair"]["source"] for x in data["blocks"] if x["type"] == "heading"), "Bilingual document")
    title = config.get("browser_title", first_heading)
    order = config.get("desktop_order", "source-first")
    lines = ['<!doctype html>', f'<html lang="{languages["source"]["tag"]}" dir="ltr">', '<head>',
             '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\'; style-src \'self\'; base-uri \'none\'; form-action \'none\'">',
             f'<title>{html.escape(title)}</title>', '<link rel="stylesheet" href="style.css">', '</head>',
             f'<body class="{order}"><main>']
    for block in data["blocks"]:
        kind = block["type"]
        if kind == "heading":
            lines.append(pair_html(block["pair"], f'h{block["level"]}'))
        elif kind == "paragraph":
            lines.append(pair_html(block["pair"], "p"))
        elif kind == "list":
            tag = "ol" if block["ordered"] else "ul"
            lines.append(f'<{tag}>')
            for item in block["items"]:
                lines.append('<li>' + pair_html(item) + '</li>')
            lines.append(f'</{tag}>')
        elif kind == "table":
            label = block.get("caption", block["headers"][0])["id"]
            lines.append(f'<div class="table-scroll" role="region" tabindex="0" '
                         f'aria-labelledby="pair-{label}">'
                         '<span class="table-scroll-cue" aria-hidden="true">↔</span><table>')
            if "caption" in block:
                lines.append('<caption>' + pair_html(block["caption"]) + '</caption>')
            lines.append('<thead><tr>')
            for cell in block["headers"]:
                lines.append('<th scope="col">' + pair_html(cell) + '</th>')
            lines.append('</tr></thead><tbody>')
            for row in block["rows"]:
                lines.append('<tr>')
                for cell in row:
                    lines.append('<td>' + pair_html(cell) + '</td>')
                lines.append('</tr>')
            lines.append('</tbody></table></div>')
        elif kind == "figure":
            alt = block["alt"]
            lines.append('<figure>')
            lines.append(f'<img src="{html.escape(block["asset"], quote=True)}" alt="{html.escape(alt["source"], quote=True)}" '
                         f'aria-labelledby="alt-{alt["id"]}-source alt-{alt["id"]}-target">')
            lines.append(pair_html(alt, "div", " visually-hidden"))
            lines.append(pair_html(block["caption"], "figcaption"))
            lines.append('</figure>')
    lines += ['</main></body>', '</html>', '']
    return "\n".join(lines)


def render_document(input_path, output):
    input_path = Path(input_path)
    data = load_json(input_path)
    html_text = render_html(data)
    assets = _read_assets(data, input_path.absolute().parent)
    style = (SKILL_ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    overrides = data.get("config", {}).get("styles", {})
    if overrides:
        style += "\n:root {\n" + "".join(
            f"  --{key.replace('_', '-')}: {_css_value(key, value)};\n"
            for key, value in sorted(overrides.items())
        ) + "}\n"
    files = {"index.html": html_text.encode("utf-8"), "style.css": style.encode("utf-8"),
             "LICENSE": (SKILL_ROOT / "LICENSE").read_bytes(), **assets}
    return _write_bundle(output, files)


def import_pairs(input_path, output, translation_skill, contract_version=1,
                 validator_sha256=None, tested_revision=None):
    """Use the installed semantic owner's validator; own only the layout mapping."""
    if not translation_skill:
        raise RenderError("Discover the separately installed bilingual-translation skill and pass --translation-skill PATH; already paired layout JSON needs no dependency")
    validator_path = Path(translation_skill) / "scripts" / "translation_contract.py"
    if not validator_path.is_file():
        raise RenderError("The discovered bilingual-translation skill must provide scripts/translation_contract.py; install it explicitly or supply paired layout JSON")
    validator_hash = hashlib.sha256(validator_path.read_bytes()).hexdigest()
    if validator_sha256 is not None and validator_sha256 != validator_hash:
        raise RenderError("Installed translation validator does not match --validator-sha256; review the dependency revision")
    spec = importlib.util.spec_from_file_location("_installed_translation_contract", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if (type(contract_version) is not int or contract_version != 1
            or type(getattr(module, "CONTRACT_VERSION", None)) is not int
            or module.CONTRACT_VERSION != contract_version):
        raise RenderError("Unsupported translation contract; this adapter supports version 1")
    data = load_json(input_path)
    errors = module.validate_document(data, require_ready=True)
    if errors:
        raise RenderError("Translation content is not ready:\n" + "\n".join(errors))
    pairs = {unit["id"]: {key: unit[key] for key in ("id", "source", "target")} for unit in data["units"]}
    result = {"layout_version": LAYOUT_VERSION, "languages": copy.deepcopy(data["languages"]), "blocks": []}
    for block in data["blocks"]:
        kind = block["type"]
        mapped = {"type": kind}
        if kind in ("heading", "paragraph"):
            mapped["pair"] = copy.deepcopy(pairs[block["unit"]])
            if kind == "heading":
                mapped["level"] = block["level"]
        elif kind == "list":
            mapped.update(ordered=block["ordered"], items=[copy.deepcopy(pairs[x]) for x in block["items"]])
        elif kind == "table":
            mapped.update(headers=[copy.deepcopy(pairs[x]) for x in block["headers"]],
                          rows=[[copy.deepcopy(pairs[x]) for x in row] for row in block["rows"]])
            if "caption" in block:
                mapped["caption"] = copy.deepcopy(pairs[block["caption"]])
        elif kind == "figure":
            mapped.update(asset=block["asset"], caption=copy.deepcopy(pairs[block["caption"]]),
                          alt=copy.deepcopy(pairs[block["alt"]]))
        else:
            raise RenderError(f"Unsupported translation block type: {kind}")
        result["blocks"].append(mapped)
    _require_valid(result)
    assets = _read_assets(result, Path(input_path).absolute().parent)
    record = {"translation_contract": contract_version, "validator_sha256": validator_hash}
    if tested_revision is not None:
        record["tested_revision"] = tested_revision
    files = {"layout.json": (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
             "import-record.json": (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), **assets}
    return _write_bundle(output, files)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="Render ready embedded pairs without translation tooling")
    render.add_argument("input", type=Path)
    render.add_argument("--output", type=Path, required=True, help="New output directory; parent must exist")
    imported = sub.add_parser("import-pairs", help="Import ready semantic v1 pairs using a discovered translation skill")
    imported.add_argument("input", type=Path)
    imported.add_argument("--output", type=Path, required=True, help="New portable layout bundle directory")
    imported.add_argument("--translation-skill", type=Path, required=True)
    imported.add_argument("--contract-version", type=int, default=1)
    imported.add_argument("--validator-sha256")
    imported.add_argument("--tested-revision", help="Project's reviewed dependency revision label")
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            output = render_document(args.input, args.output)
            print(f"Rendered {output / 'index.html'}")
        else:
            output = import_pairs(args.input, args.output, args.translation_skill,
                                  args.contract_version, args.validator_sha256, args.tested_revision)
            print(f"Imported {output / 'layout.json'}")
        return 0
    except (RenderError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
