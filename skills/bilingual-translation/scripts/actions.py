"""Shared command definitions and in-memory handlers for JSONL action packets."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

core = load_module("_translation_storage", "translation_workflow.py")

class ProtocolError(ValueError):
    def __init__(self, message, **details):
        self.details = details
        super().__init__(message)

def require(condition, message):
    if not condition:
        raise ProtocolError(message)

class Field:
    def __init__(self, kind, required=False, default=None):
        self.kind, self.required, self.default = kind, required, default

class Command:
    def __init__(self, name, handler, fields, reads=False, external=False):
        self.name, self.handler, self.fields = name, handler, fields
        self.reads, self.external = reads, external

    def normalize(self, action):
        require(isinstance(action, dict) and action.get("op") == self.name, "op must match selected command")
        require(set(action) <= {"op", *self.fields}, "unknown action field")
        result = {"op": self.name}
        for key, field in self.fields.items():
            if key not in action:
                require(not field.required, "missing required field: " + key)
                if field.default is not None:
                    result[key] = copy.deepcopy(field.default)
                continue
            value = action[key]
            require(type(value) is field.kind, "invalid field type: " + key)
            if field.kind is str and field.default != '':
                require(bool(value.strip()), "empty field: " + key)
            result[key] = value
        return result

COMMANDS = {}

def command(name, fields=None, *, reads=False, external=False):
    def decorate(handler):
        COMMANDS[name] = Command(name, handler, fields or {}, reads, external)
        return handler
    return decorate

def normalize(action):
    require(isinstance(action, dict) and isinstance(action.get("op"), str), "each action needs op")
    require(action["op"] in COMMANDS, "unknown command")
    return COMMANDS[action["op"]].normalize(action)

def units(data, ids):
    selected = [u for u in data["units"] if u["id"] in ids]
    require([u["id"] for u in selected] == ids, "unknown or unordered unit IDs")
    return selected

def binding(data, phase, selected):
    return core.workflow_binding(data, phase, selected)


def active(data, phase=None, ref=None):
    block = data["document"]["workflow"]["active"]
    require(block is not None, "read the next block first")
    if phase:
        require(block["phase"] == phase, "wrong active phase")
    selected = units(data, block["ids"])
    require(block["binding"] == binding(data, block["phase"], selected), "active text changed; read again")
    if ref is not None:
        require(ref == block["ref"], "stale or invalid ref")
        require(block["delivered"], "read changed pairs before accepting or editing")
    return block, selected

def new_active(data, phase, selected, delivered=False):
    workflow = data["document"]["workflow"]
    workflow["sequence"] += 1
    digest = binding(data, phase, selected)
    ref = str(workflow["sequence"]) + "-" + core.REF_WORDS[int(digest, 16) % len(core.REF_WORDS)]
    result = {"phase": phase, "ids": [u["id"] for u in selected], "ref": ref,
              "sequence": workflow["sequence"], "binding": digest, "delivered": delivered}
    workflow["active"] = result
    return result

def scope(data, unit):
    if unit['kind'] in ('heading', 'list_item', 'table_cell'):
        for index, block in enumerate(data['document']['blocks']):
            if unit['parent_id'] in core._structural_order([block]):
                return (unit['kind'], index, tuple(unit['heading_path']))
    return (unit['kind'], tuple(unit['heading_path']))


def group(data, phase, requested=None):
    candidates = [u for u in data['units'] if (u['target'] is None if phase == 'translate'
                                              else u['status'] != 'reviewed')]
    if requested is not None:
        require(phase == 'review' and requested, 'nonempty units selection is only for review')
        candidates = units(data, requested)
    result, size, previous_scope = [], 0, None
    for unit in candidates:
        current_scope = scope(data, unit)
        if result and (size + len(unit['source']) > core.MAX_SOURCE or current_scope != previous_scope
                       or unit['order'] != result[-1]['order'] + 1):
            break
        require(len(unit['source']) <= core.MAX_SOURCE, 'finish required preparation splits')
        result.append(unit)
        previous_scope, size = current_scope, size + len(unit['source'])
    if requested is not None:
        require([u['id'] for u in result] == requested, 'requested review units must fit one structural group')
    return result


def view(data, block, include_context=False):
    selected = units(data, block['ids'])
    records = []
    for unit in selected:
        item = {k: unit[k] for k in ('id', 'kind', 'source')}
        if unit['id'] != unit['parent_id']:
            item.update({k: unit[k] for k in ('parent_id', 'part_index', 'has_more')})
        if block['phase'] == 'review':
            item['target'] = unit['target']
        records.append(item)
    block['delivered'] = True
    result = {'phase': block['phase'], 'ref': block['ref'], 'units': records}
    relevant = [t for t in data['document']['workflow']['todos'] if not t['resolved']
                and (not t['units'] or set(t['units']) & set(block['ids']))]
    if relevant:
        result['todos'] = copy.deepcopy(relevant)
    seen = data['document']['workflow']['seen']
    if include_context or block['phase'] not in seen:
        if block['phase'] not in seen:
            seen.append(block['phase'])
        result.update(languages=copy.deepcopy(data['document']['languages']),
                      context=copy.deepcopy(data['document']['context']))
    return result


def counts(data, phase):
    if phase == 'prepare':
        parents = data['document']['parents']
        count = sum(p['char_count'] for p in parents[:data['document']['preparation']['cursor']])
        return count, sum(p['char_count'] for p in parents), 'codepoints'
    return sum(u['target'] is not None if phase == 'translate' else u['status'] == 'reviewed'
               for u in data['units']), len(data['units']), 'units'


def progress(before, data, phase):
    completed, total, unit = counts(data, phase)
    previous = before[phase][0] if before else 0
    percent = completed * 100 // total if total else 100
    old_percent = previous * 100 // total if total else 100
    if percent // 5 != old_percent // 5 or completed < previous:
        return {'phase': phase, 'completed': completed, 'total': total, 'unit': unit, 'percent': percent}
    return None


def ready_to_translate(data):
    require(data['document']['preparation']['complete'], 'finish complete preparation and splits first')


def ready_to_review(data):
    ready_to_translate(data)
    require(all(u['target'] is not None for u in data['units']), 'finish all translations first')


@command('prepare init', {'source': Field(str), 'source_lang': Field(str), 'target_lang': Field(str),
         'source_dir': Field(str), 'target_dir': Field(str), 'context': Field(dict), 'ref': Field(str)}, reads=True)
def prepare_init(data, action, context):
    preparation = load_module('_translation_preparation', 'preparation.py')
    schema = core.exchange._SCHEMA
    require(not core.exchange._schema_errors(data['document']['languages'], schema['properties']['languages']),
            'invalid source/target language metadata')
    if 'context' in action:
        require(not core.exchange._schema_errors(action['context'], schema['$defs']['context']), 'invalid context fields')
    if not context.get('new'):
        require('source' not in action and not any(k in action for k in ('source_lang','target_lang','source_dir','target_dir')),
                'continuation uses ref, not source or language fields')
        require(action.get('ref') == data['document']['preparation']['ref'], 'use the current preparation ref')
    if 'context' in action:
        require(not any(u['target'] is not None for u in data['units']), 'set whole-source context before translation')
        data['document']['context'] = copy.deepcopy(action['context'])
    if data['document']['preparation']['complete']:
        return {'phase': 'prepare', 'complete': True, 'ref': data['document']['preparation']['ref']}
    result = preparation.deliver(data)
    update = progress(context['before'], data, 'prepare')
    if update:
        result['progress'] = update
    return result


@command('prepare split', {'ref': Field(str, True), 'unit': Field(str, True), 'cuts': Field(list, True)})
def prepare_split(data, action, context):
    preparation = load_module('_translation_preparation', 'preparation.py')
    return preparation.split(data, action['ref'], action['unit'], action['cuts'])


def next_handler(data, action, context):
    phase = action['op'].split()[0]
    ready_to_translate(data) if phase == 'translate' else ready_to_review(data)
    block = data['document']['workflow']['active']
    if block is not None:
        require(block['phase'] == phase, 'finish the current active phase first')
        require('units' not in action or action['units'] == block['ids'], 'finish current active group first')
    else:
        selected = group(data, phase, action.get('units'))
        if not selected:
            return {'phase': phase, 'complete': True}
        block = new_active(data, phase, selected)
    return view(data, block, action.get('context', False))

command('translate next', {'context': Field(bool, default=False)}, reads=True)(next_handler)
command('review next', {'units': Field(list), 'context': Field(bool, default=False)}, reads=True)(next_handler)


@command('translate save', {'ref': Field(str, True), 'targets': Field(dict, True)})
def translate_save(data, action, context):
    block, selected = active(data, 'translate', action['ref'])
    require(set(action['targets']) == set(block['ids']), 'targets must match exact active IDs')
    for value in action['targets'].values():
        core._text(value, 'target')
    for unit in selected:
        target = action['targets'][unit['id']]
        unit.update(target=target, target_hash=core.digest(target), target_source_hash=unit['source_hash'],
                    status='draft', review=None)
    data['document']['workflow']['active'] = None
    result = {'saved': block['ids']}
    update = progress(context['before'], data, 'translate')
    if update:
        result['progress'] = update
    return result


@command('review accept', {'ref': Field(str, True), 'reviewer': Field(str, default='translator'),
                           'note': Field(str, default='')})
def review_accept(data, action, context):
    block, selected = active(data, 'review', action['ref'])
    core._text(action['reviewer'], 'reviewer')
    core._text(action['note'], 'review note', empty=True)
    for unit in selected:
        unit['status'] = 'reviewed'
        unit['review'] = {'source_hash': unit['source_hash'], 'target_hash': unit['target_hash'],
                          'reviewer': action['reviewer'], 'note': action['note']}
    data['document']['workflow']['active'] = None
    result = {'accepted': block['ids']}
    update = progress(context['before'], data, 'review')
    if update:
        result['progress'] = update
    return result


@command('review patch', {'ref': Field(str, True), 'edits': Field(list, True)})
def review_patch(data, action, context):
    block, selected = active(data, 'review', action['ref'])
    require(action['edits'], 'edits must not be empty')
    originals = {u['id']: u['target'] for u in selected}
    ranges = {}
    for edit in action['edits']:
        require(isinstance(edit, dict) and set(edit) == {'unit', 'old', 'new'}, 'patch edits need unit, old and new')
        uid, old, new = edit['unit'], edit['old'], edit['new']
        require(isinstance(uid, str) and uid in originals and isinstance(old, str) and old
                and isinstance(new, str), 'patch must address a read unit with nonempty exact old text')
        target = originals[uid]
        starts, at = [], target.find(old)
        while at >= 0:
            starts.append(at)
            at = target.find(old, at + 1)
        if len(starts) != 1:
            raise ProtocolError('patch old text must have exactly one match', unit=uid,
                                match_count=len(starts), contexts=[target[max(0,n-24):min(len(target),n+len(old)+24)][:96] for n in starts[:3]])
        start, end = starts[0], starts[0] + len(old)
        prior = ranges.setdefault(uid, [])
        require(all(end <= a or start >= b for a, b, _ in prior), 'patch edits overlap')
        prior.append((start, end, new))
    replacements = {}
    for uid, spans in ranges.items():
        target = originals[uid]
        for start, end, new in sorted(spans, reverse=True):
            target = target[:start] + new + target[end:]
        core._text(target, 'target')
        replacements[uid] = target
    changed = []
    for unit in selected:
        if unit['id'] in replacements and replacements[unit['id']] != unit['target']:
            target = replacements[unit['id']]
            unit.update(target=target, target_hash=core.digest(target), status='needs_review', review=None)
            changed.append(unit)
    require(changed, 'patch does not change target text')
    # Only changed pairs are re-read; untouched drafts remain pending, never implicitly accepted.
    new_active(data, 'review', changed, delivered=False)
    context['patched'] = True
    result = {'patched': [u['id'] for u in changed], 'needs_review': True}
    update = progress(context['before'], data, 'review')
    if update:
        result['progress'] = update
    return result

@command('review restart', {'ref': Field(str, True)})
def review_restart(data, action, context):
    ready_to_review(data)
    active(data, 'review', action['ref'])
    data['document']['workflow']['active'] = None
    data['document']['workflow']['review_round'] += 1
    for unit in data['units']:
        unit.update(status='needs_review', review=None)
    result = {'review_restarted': True, 'units': len(data['units'])}
    update = progress(context['before'], data, 'review')
    if update:
        result['progress'] = update
    return result


@command('todo add', {'ref': Field(str, True), 'text': Field(str, True), 'units': Field(list)})
def todo_add(data, action, context):
    block, selected = active(data, ref=action['ref'])
    requested = action.get('units', [])
    require(all(isinstance(uid, str) for uid in requested) and len(set(requested)) == len(requested),
            'todo units must be unique IDs')
    require(set(requested) <= set(block['ids']), 'todo can name only currently read units')
    core._text(action['text'], 'todo text')
    todos = data['document']['workflow']['todos']
    item = {'id': 'todo-' + str(len(todos) + 1), 'text': action['text'], 'units': requested,
            'resolved': False}
    todos.append(item)
    return {'todo': item['id'], 'scope': requested or 'global', 'open': True}


@command('todo resolve', {'ref': Field(str, True), 'id': Field(str, True)})
def todo_resolve(data, action, context):
    block, selected = active(data, ref=action['ref'])
    item = next((t for t in data['document']['workflow']['todos'] if t['id'] == action['id']), None)
    require(item is not None and not item['resolved'], 'unknown or already resolved todo')
    require(not item['units'] or set(item['units']) <= set(block['ids']), 'read the todo units before resolving')
    item['resolved'] = True
    return {'resolved': item['id']}


@command('status')
def status(data, action, context):
    total = len(data['units'])
    saved = sum(u['target'] is not None for u in data['units'])
    reviewed = sum(u['status'] == 'reviewed' for u in data['units'])
    todos = [t for t in data['document']['workflow']['todos'] if not t['resolved']]
    return {'prepared': data['document']['preparation']['complete'], 'total': total,
            'saved': saved, 'reviewed': reviewed, 'open_todos': len(todos),
            'active': data['document']['workflow']['active'] is not None,
            'blockers': [label for label, yes in [('preparation', not data['document']['preparation']['complete']),
                ('translation', saved != total), ('review', reviewed != total), ('todos', bool(todos)),
                ('active', data['document']['workflow']['active'] is not None)] if yes]}


@command('validate', {'ready': Field(bool, default=False)})
def validate(data, action, context):
    core.validate(data, require_ready=action['ready'])
    return {'valid': True, 'ready': action['ready']}


@command('export', {'output': Field(str, True)}, external=True)
def export(data, action, context):
    # External output is handled after registry validation, outside run packets.
    core.validate(data, require_ready=True)
    return {'exchange': core.to_exchange_document(data), 'output': action['output']}
