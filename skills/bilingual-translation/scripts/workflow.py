#!/usr/bin/env python3
"""Standalone commands and atomic JSONL packets use one command registry."""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

_SPEC = importlib.util.spec_from_file_location("_translation_actions", Path(__file__).with_name("actions.py"))
actions = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(actions)
core = actions.core
COMMANDS = actions.COMMANDS
ProtocolError = actions.ProtocolError
require = actions.require

class ActionError(ValueError):
    def __init__(self, line, op, error, committed=False):
        self.line, self.op, self.error, self.committed = line, op, error, committed
        super().__init__(str(error))

def _safe_error(error):
    if isinstance(error, ProtocolError):
        return str(error)
    if isinstance(error, OSError):
        return "file operation failed; check storage and retry the identical packet"
    if isinstance(error, (json.JSONDecodeError, UnicodeError)):
        return "invalid JSON or Unicode input"
    message = str(error)
    safe = ("cut anchors", "cuts must", "each child", "split requires", "split all", "source reconstruction",
            "source hash mismatch", "parent reconstruction", "use the current preparation ref",
            "preparation is already complete", "source needs a lossless native route")
    if message.startswith(safe):
        return message
    return "invalid action or saved state; check fields and current references"

def _packet(incoming, batch):
    normalized = []
    for index, item in enumerate(incoming, 1):
        try:
            normalized.append(actions.normalize(item))
        except (ValueError, TypeError, KeyError) as error:
            op = item.get("op") if isinstance(item, dict) else None
            raise ActionError(index, op if isinstance(op, str) and op in COMMANDS else None, error) from error
    require(bool(normalized), "provide at least one action")
    reads = [i for i, item in enumerate(normalized) if COMMANDS[item["op"]].reads]
    if len(reads) > 1 or (reads and reads[0] != len(normalized)-1):
        index = reads[0]
        raise ActionError(index+1, normalized[index]["op"], ProtocolError(
            "at most one body-reading action is allowed, and it must be last"))
    if batch:
        for index, item in enumerate(normalized, 1):
            if COMMANDS[item["op"]].external:
                raise ActionError(index, item["op"], ProtocolError("export is standalone, outside run"))
    else:
        require(len(normalized) == 1, "standalone commands accept exactly one action")
    ops = [a["op"] for a in normalized]
    if "review patch" in ops and "review accept" in ops:
        index = ops.index("review accept")
        raise ActionError(index+1, ops[index], ProtocolError("patch and accept cannot share a packet"))
    return normalized

def execute(master, packet, *, batch=False):
    """Load once, dispatch registry handlers in memory, commit at most once."""
    packet = _packet(packet, batch)
    path = Path(master)
    if packet[0]['op'] == 'export':
        data = core.load_jsonl(path, require_ready=True)
        result = COMMANDS['export'].handler(data, packet[0], {})
        output = Path(result['output'])
        with core._lock(output):
            core._atomic(output, json.dumps(result['exchange'], ensure_ascii=False, indent=2)+'\n', new=True)
        return [{'exported': True}]
    with core._lock(path):
        new = not path.exists()
        source_text = None
        if packet[0]['op'] == 'prepare init' and 'source' in packet[0]:
            source_text = core._source(packet[0]['source'])
        fingerprint = core.digest(core._canonical([packet, core.digest(source_text) if source_text is not None else None]))
        cacheable = any('ref' in action for action in packet) or source_text is not None
        if new:
            require(packet[0]['op'] == 'prepare init' and source_text is not None,
                    'start a new task with prepare init and source')
            require('ref' not in packet[0], 'initial preparation does not take a prior ref')
            preparation = actions.load_module('_translation_preparation', 'preparation.py')
            kwargs = {k: packet[0][k] for k in ('source_lang','target_lang','source_dir','target_dir','context') if k in packet[0]}
            data = preparation.create(source_text, **kwargs)
        else:
            data = core.load_jsonl(path)
            cached = data['document']['workflow']['operations'].get(fingerprint) if cacheable else None
            if cached is not None:
                return copy.deepcopy(cached['receipt']['results'])
        initial = core._canonical(data)
        results = []
        context = {'new': new, 'patched': False}
        for index, action in enumerate(packet, 1):
            context['before'] = {phase: actions.counts(data, phase) for phase in ('prepare', 'translate', 'review')}
            try:
                result = COMMANDS[action['op']].handler(data, action, context)
            except (ValueError, TypeError, KeyError, IndexError) as error:
                raise ActionError(index, action['op'], error) from error
            results.append(result)
        try:
            core.validate(data)
        except (ValueError, TypeError, KeyError) as error:
            raise ActionError(len(packet), packet[-1]['op'], error) from error
        changed = new or core._canonical(data) != initial
        if changed:
            data['document']['revision'] += 1
            if cacheable:
                data['document']['workflow']['operations'][fingerprint] = {
                    'request_hash': fingerprint, 'receipt': {'results': copy.deepcopy(results)}}
            try:
                core._save(path, data, new=new)
            except OSError as error:
                try:
                    persisted = core.load_jsonl(path)
                    if core._canonical(persisted) == core._canonical(data):
                        return results
                except (OSError, ValueError):
                    pass
                raise ActionError(len(packet), packet[-1]['op'], error, committed='unknown') from error
        return results


def output_records(results):
    for result in results:
        receipt = dict(result)
        body = receipt.pop('units', None)
        if isinstance(body, list) and (not body or isinstance(body[0], dict)):
            for unit in body:
                emitted = dict(unit)
                if emitted.get('parent_id') == emitted.get('id'):
                    emitted.pop('parent_id', None)
                if emitted.get('part_index') == 0:
                    emitted.pop('part_index')
                if emitted.get('has_more') is False:
                    emitted.pop('has_more')
                yield {'record_type': 'unit', **emitted}
        elif body is not None:
            receipt['units'] = body
        for key, empty in (('context', {}), ('pending', []), ('oversize', [])):
            if receipt.get(key) == empty:
                receipt.pop(key)
        for key in ('saved', 'accepted'):
            if isinstance(receipt.get(key), list):
                receipt[key] = len(receipt[key])
        progress = receipt.get('progress')
        if isinstance(progress, dict):
            receipt['progress'] = (f"{progress['phase']} {progress['completed']}/{progress['total']} "
                                   f"{progress['unit']} ({progress['percent']}%)")
        yield {'record_type': 'receipt', **receipt}


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ProtocolError('invalid CLI arguments; use --help')


def parser():
    result = ArgumentParser(description=__doc__)
    result.add_argument('--master', type=Path, default=Path('master.jsonl'))
    groups = result.add_subparsers(dest='group', required=True)
    parents = {}
    for name, spec in COMMANDS.items():
        parts = name.split()
        if len(parts) == 2:
            if parts[0] not in parents:
                parents[parts[0]] = groups.add_parser(parts[0]).add_subparsers(dest='verb', required=True)
            selected = parents[parts[0]].add_parser(parts[1])
        else:
            selected = groups.add_parser(name)
        selected.set_defaults(selected_op=name)
        for key, field in spec.fields.items():
            flag = '--' + key.replace('_', '-')
            if field.kind is bool:
                selected.add_argument(flag, action='store_true', default=None)
            else:
                selected.add_argument(flag)
    groups.add_parser('run').set_defaults(selected_op='run')
    return result


def input_actions(text):
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            raise ActionError(number, None, ProtocolError('each JSONL line must contain one action'))
        try:
            result.append(core._json(line))
        except (ValueError, TypeError) as error:
            raise ActionError(number, None, error) from error
    return result


def main(argv=None, stdin=None):
    try:
        args = parser().parse_args(argv)
        name = args.selected_op
        raw = sys.stdin.read() if stdin is None and not sys.stdin.isatty() else (stdin or '')
        incoming = input_actions(raw)
        if name == 'run':
            results = execute(args.master, incoming, batch=True)
        else:
            spec = COMMANDS[name]
            cli = {'op': name}
            for key, field in spec.fields.items():
                value = getattr(args, key, None)
                if value is not None:
                    if field.kind in (dict, list, int):
                        value = core._json(value)
                    cli[key] = value
            if incoming:
                require(len(incoming) == 1, 'standalone command accepts one JSONL action')
                require(set(cli) == {'op'}, 'choose flags or one stdin object, not both')
                require(isinstance(incoming[0], dict) and incoming[0].get('op') == name,
                        'stdin op conflicts with selected command')
                cli = incoming[0]
            results = execute(args.master, [cli])
        for record in output_records(results):
            print(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
        return 0
    except ActionError as error:
        print(json.dumps({'ok': False, 'line': error.line, 'op': error.op,
                          'committed': error.committed, 'error': _safe_error(error.error),
                          **getattr(error.error, 'details', {})},
                         ensure_ascii=False, separators=(',', ':')), file=sys.stderr)
        return 1
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(json.dumps({'ok': False, 'committed': False, 'error': _safe_error(error)},
                         ensure_ascii=False, separators=(',', ':')), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
