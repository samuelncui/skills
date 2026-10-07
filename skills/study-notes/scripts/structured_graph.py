#!/usr/bin/env python3
"""Validate one authoritative graph and emit derived native studytools fragments.

No compilation, dependency download, or translation is performed. The caller explicitly
selects an installed bilingual-pdf skill; its API owns escaping, math and asset policy.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

from jsonschema import Draft202012Validator
from graph_ordering import optimize

ROOT = Path(__file__).resolve().parents[1]
IMPORTER_API_VERSION = 1

class GraphError(ValueError):
    pass

def load_graph(text):
    """Reject duplicate members and non-finite constants before schema/coverage."""
    def members(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise GraphError('Duplicate JSON member: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise GraphError('Non-finite JSON number: ' + value)
    return json.loads(text, object_pairs_hook=members, parse_constant=constant)

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()

def load_renderer(path):
    path = Path(path).resolve()
    module_path = path / 'scripts' / 'bilingual_pdf.py'
    if not module_path.is_file() or not (path / 'assets' / 'paralleltext.sty').is_file():
        raise GraphError('Select an installed bilingual-pdf skill directory')
    spec = importlib.util.spec_from_file_location('study_graph_bilingual_pdf', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, 'RENDERER_API_VERSION', None) != 1:
        raise GraphError('bilingual-pdf renderer API 1 is required')
    return module

def content_fields(graph):
    """Complete inventory of paired reader content, excluding source catalog metadata."""
    yield '/title', graph['title']
    for i, node in enumerate(graph['nodes']):
        base = f'/nodes/{i}'
        for name in ('title', 'prerequisites', 'completion_check', 'stop'):
            if name in node:
                yield base + '/' + name, node[name]
        for j, field in enumerate(node.get('fields', [])):
            yield f'{base}/fields/{j}/text', field['text']
        for j, step in enumerate(node.get('steps', [])):
            yield f'{base}/steps/{j}/text', step['text']
            if 'call' in step:
                for name in ('when', 'outputs'):
                    yield f'{base}/steps/{j}/call/{name}', step['call'][name]
        for j, choice in enumerate(node.get('choices', [])):
            yield f'{base}/choices/{j}/condition', choice['condition']
        for name, value in node.get('loop', {}).items():
            yield f'{base}/loop/{name}', value
        for j, figure in enumerate(node.get('figures', [])):
            yield f'{base}/figures/{j}/caption', figure['caption']

def validate(graph, renderer, *, trusted_native=False, asset_root=None):
    schema = json.loads((ROOT / 'schemas' / 'graph-v1.schema.json').read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(graph), key=lambda x: str(list(x.path)))
    if errors:
        error = errors[0]
        raise GraphError('/' + '/'.join(map(str, error.path)) + ': ' + error.message)
    if any(lang not in renderer.PROFILES for lang in graph['languages']):
        raise GraphError('Unsupported language profile')
    if set(graph['languages']) == {'zh-Hans', 'zh-Hant'}:
        raise GraphError('Mixed simplified/traditional Chinese requires a native project')
    nodes = {node['key']: node for node in graph['nodes']}
    if len(nodes) != len(graph['nodes']):
        raise GraphError('Duplicate node key')
    if set(graph['seed_order']) != set(nodes) or len(graph['seed_order']) != len(nodes):
        raise GraphError('seed_order must contain every node exactly once')
    if graph['entry'] not in nodes:
        raise GraphError('Unknown entry')
    sources = {source['key']: source for source in graph.get('sources', [])}
    if len(sources) != len(graph.get('sources', [])):
        raise GraphError('Duplicate source key')
    for source in sources.values():
        for title in source['title']:
            renderer.text_value(title)
    assets = {}
    def target(key):
        if key not in nodes:
            raise GraphError('Unknown node target: ' + key)
    for pointer, pair in content_fields(graph):
        for field in pair:
            if isinstance(field, str):
                renderer.text_value(field)
                continue
            if not any(run.get('text', '').strip() or run['kind'] in ('reference', 'node') for run in field['runs']):
                raise GraphError('Rich field must contain nonblank content')
            for run in field['runs']:
                kind = run['kind']
                if kind in ('text', 'native', 'math'):
                    renderer.text_value('text' + run['text'] if kind == 'text' else run['text'])
                if kind == 'native' and not trusted_native:
                    raise GraphError(pointer + ': native TeX requires --trusted-native')
                if kind == 'math':
                    renderer.validate({'languages':['en','en'], 'title':['Math','Math'],
                        'blocks':[{'id':'formula','kind':'equation','text':['Formula','Formula'], 'math':run['text']}]})
                    depth = 0
                    for char in run['text']:
                        depth += (char == '{') - (char == '}')
                        if depth < 0:
                            raise GraphError('Unbalanced math braces')
                    if depth:
                        raise GraphError('Unbalanced math braces')
                if kind == 'reference':
                    source = sources.get(run['source'])
                    if not source or source['sha256'] != run['sha256']:
                        raise GraphError('Stale or unknown source binding at ' + pointer)
                    renderer.text_value(run['locator'])
                if kind == 'node':
                    target(run['target'])
    ordinary = set()
    calls = []
    for node in nodes.values():
        key = node['key']
        fields = [f['key'] for f in node.get('fields', [])]
        if len(fields) != len(set(fields)):
            raise GraphError('Duplicate field key in ' + key)
        if node['kind'] == 'decision':
            if not node.get('choices') or 'steps' in node or 'next' in node or 'stop' in node:
                raise GraphError('Decision needs ordered choices, without procedure flow')
        elif 'choices' in node:
            raise GraphError('Procedure cannot contain decision choices')
        if 'next' in node and 'stop' in node:
            raise GraphError('Choose next or stop, not both')
        for choice in node.get('choices', []):
            target(choice['target']); ordinary.add((key, choice['target']))
        if 'next' in node:
            target(node['next']); ordinary.add((key, node['next']))
        for index, step in enumerate(node.get('steps', []), 1):
            if 'call' not in step:
                continue
            call = step['call']; target(call['target']); target(call['resume']['node'])
            resume = nodes[call['resume']['node']]
            if resume['kind'] != 'procedure':
                raise GraphError('Call resume must be a procedure')
            if call['resume']['node'] != key:
                raise GraphError('Graph v1 calls must resume within their owning procedure')
            point = call['resume']['step']
            if point != 'completion_check':
                point = int(point)
            if isinstance(point, int) and point <= index:
                raise GraphError('Call resume must follow the owning step')
            if point == 'completion_check':
                if 'completion_check' not in resume:
                    raise GraphError('Missing resume completion_check')
            elif point > len(resume.get('steps', [])):
                raise GraphError('Resume step does not exist')
            for exit_key in call['return_exits']:
                target(exit_key)
                if nodes[exit_key]['kind'] != 'procedure':
                    raise GraphError('Return exit must be a procedure')
            calls.append((key, call))
        for figure in node.get('figures', []):
            if asset_root is None:
                raise GraphError('Figures require an explicit asset root')
            path = renderer.resolve_image(Path(asset_root) / 'graph.json', figure['path'], asset_root)
            if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
                raise GraphError('Image must be a regular file no larger than 10 MiB')
            from PIL import Image
            with Image.open(path) as image:
                if image.width * image.height > 40_000_000:
                    raise GraphError('Image exceeds 40 million pixels')
                image.verify()
            assets[figure['path']] = path
    adjacency = {key:set() for key in nodes}
    for a, b in ordinary:
        adjacency[a].add(b)
    def reachable(start, stops=frozenset()):
        seen = set(); todo = [start]
        while todo:
            key = todo.pop()
            if key in seen:
                continue
            seen.add(key)
            if key not in stops:
                todo.extend(adjacency[key])
        return seen
    # A declared loop node must intersect every ordinary-flow cycle. This is a
    # structural annotation check, not a proof of progress or termination.
    unmarked = {key for key in nodes if 'loop' not in nodes[key]}
    indegree = {key:0 for key in unmarked}
    for a, b in ordinary:
        if a in unmarked and b in unmarked:
            indegree[b] += 1
    todo = [key for key, degree in indegree.items() if degree == 0]
    removed = 0
    while todo:
        key = todo.pop(); removed += 1
        for child in adjacency[key] & unmarked:
            indegree[child] -= 1
            if indegree[child] == 0:
                todo.append(child)
    if removed != len(unmarked):
        raise GraphError('Cycle needs an explicit loop annotation')
    executable = set(ordinary)
    return_exits = set()
    call_regions = []
    for owner, call in calls:
        exits = set(call['return_exits'])
        region = reachable(call['target'], exits)
        if not exits <= region:
            raise GraphError('Call has an unreachable return exit')
        if owner in region:
            raise GraphError('Recursive calls are unsupported')
        if any(any('call' in step for step in nodes[key].get('steps', [])) for key in region):
            raise GraphError('Nested helper calls are unsupported in graph v1')
        can_return = set(exits)
        while True:
            expanded = can_return | {a for a in region - exits if adjacency[a] & can_return}
            if expanded == can_return:
                break
            can_return = expanded
        if not region <= can_return:
            raise GraphError('Call region has a closed route without a return exit')
        call_regions.append((region, exits))
        executable.add((owner, call['target']))
        executable.update((key, call['resume']['node']) for key in exits)
        return_exits.update(exits)
    for region, exits in call_regions:
        if region & return_exits != exits:
            raise GraphError('Overlapping call regions disagree on return exits')
    for node in nodes.values():
        if node['kind'] == 'procedure' and not any(x in node for x in ('next','stop')) and node['key'] not in return_exits:
            raise GraphError('Procedure needs next, stop, or a declared call return exit')
        if node['key'] in return_exits and 'stop' in node:
            raise GraphError('A return exit cannot also stop; use next for its ordinary route')
    ordinary_reached = reachable(graph['entry'])
    if any(key in ordinary_reached and 'next' not in nodes[key] for key in return_exits):
        raise GraphError('Return-only exits require a call context; ordinary access needs next')
    reached = set(ordinary_reached)
    for (owner, call), (region, exits) in zip(calls, call_regions):
        if owner in ordinary_reached:
            reached.update(region)
    if reached != set(nodes):
        raise GraphError('Unreachable nodes: ' + ', '.join(sorted(set(nodes)-reached)))
    return {'nodes':nodes, 'sources':sources, 'edges':sorted(executable),
            'return_exits':return_exits, 'assets':assets}

def render(graph, renderer, *, trusted_native=False, asset_root=None):
    model = validate(graph, renderer, trusted_native=trusted_native, asset_root=asset_root)
    config = {key:int(value) for key,value in graph.get('ordering', {}).items()}
    ordering = optimize(graph['seed_order'], graph['entry'], model['edges'], **config)
    used = set()
    def value(field, side):
        if isinstance(field, str):
            return renderer.language_text(field, graph['languages'][side])
        chunks = []
        for run in field['runs']:
            kind = run['kind']
            if kind == 'text':
                chunks.append(renderer.language_text(run['text'], graph['languages'][side]))
            elif kind == 'math':
                chunks.append(r'\(' + run['text'] + r'\)')
            elif kind == 'native':
                chunks.append(run['text'])
            elif kind == 'node':
                chunks.append(r'\StudyGraphReference{' + run['target'] + '}')
            else:
                source = model['sources'][run['source']]
                chunks.append(renderer.language_text(source['title'][side] + ', ' + run['locator'], graph['languages'][side]))
        return ''.join(chunks)
    def pair_at(pointer, pair):
        used.add(pointer)
        return [value(field, side) for side, field in enumerate(pair)]
    def macro(name, *args):
        return '\\' + name + ''.join('{' + str(x) + '}' for x in args)
    def paired(identity, parts):
        return macro('ParallelParagraph', identity, parts[0], parts[1])
    indices = {node['key']:i for i,node in enumerate(graph['nodes'])}
    declarations = ['% Derived from structured graph; edit the JSON source.']
    body = [paired('graph-introduction', [macro('StudyGraphInstruction', text) for text in pair_at('/title', graph['title'])])]
    crosswalk = []
    staged_assets = {}
    for number, key in enumerate(ordering['order'], 1):
        node = model['nodes'][key]; base = f'/nodes/{indices[key]}'
        titles = pair_at(base+'/title', node['title'])
        declarations.append(macro('StudyDeclareGraphNode', key, number, node['kind'], node['function'], *titles))
        crosswalk.append({'key':key, 'number':number, 'reader_id':f'N{number}', 'anchor':'graph:'+key})
        parts = ['', '']
        def add_pair(command, pointer, pair, prefix=()):
            texts = pair_at(pointer, pair)
            for side in range(2):
                parts[side] += '\n' + macro(command, *prefix, texts[side])
        if 'prerequisites' in node:
            add_pair('StudyGraphField', base+'/prerequisites', node['prerequisites'], ('context',))
        for j, field in enumerate(node.get('fields', [])):
            add_pair('StudyGraphField', f'{base}/fields/{j}/text', field['text'], (field['role'],))
        for j, step in enumerate(node.get('steps', [])):
            add_pair('StudyGraphStep', f'{base}/steps/{j}/text', step['text'], (j+1,))
            if 'call' in step:
                call = step['call']
                when = pair_at(f'{base}/steps/{j}/call/when', call['when'])
                outputs = pair_at(f'{base}/steps/{j}/call/outputs', call['outputs'])
                command = 'StudyGraphHelperCall' if model['nodes'][call['target']]['kind']=='decision' else 'StudyGraphCall'
                for side in range(2):
                    parts[side] += '\n' + macro(command, call['target'], when[side], outputs[side], call['resume']['node'], call['resume']['step'] if call['resume']['step']=='completion_check' else int(call['resume']['step']))
        for j, choice in enumerate(node.get('choices', [])):
            texts = pair_at(f'{base}/choices/{j}/condition', choice['condition'])
            for side in range(2):
                parts[side] += '\n' + macro('StudyGraphChoice', j+1, texts[side], choice['target'])
        if 'completion_check' in node:
            add_pair('StudyGraphCompletionCheck', base+'/completion_check', node['completion_check'])
        if 'loop' in node:
            values = [pair_at(base+'/loop/'+name, node['loop'][name]) for name in ('carried','progress','continue_when','exit_when')]
            for side in range(2):
                parts[side] += '\n' + macro('StudyGraphLoop', *(p[side] for p in values))
        if key in model['return_exits']:
            command = macro('StudyGraphCalleeExit', node['next']) if 'next' in node else r'\StudyGraphReturnExit'
            parts = [part+'\n'+command for part in parts]
        elif 'next' in node:
            parts = [part+'\n'+macro('StudyGraphJump', node['next']) for part in parts]
        if 'stop' in node:
            add_pair('StudyGraphField', base+'/stop', node['stop'], ('result',))
        body.append(macro('StudyGraphNode', key))
        body.append(paired('graph-' + key + '-body', parts))
        for j, figure in enumerate(node.get('figures', [])):
            source = model['assets'][figure['path']]
            image_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            name = 'assets/graph-' + image_hash + source.suffix.lower()
            staged_assets[name] = source
            captions = pair_at(f'{base}/figures/{j}/caption', figure['caption'])
            body.append(macro('ParallelFigure', f'graph-{key}-figure-{j+1}', name, *captions))
    expected = {pointer for pointer, _ in content_fields(graph)}
    if expected != used:
        raise GraphError('Internal field coverage mismatch')
    declarations = '\n'.join(declarations) + '\n'
    body = '\n\n'.join(body) + '\n'
    report = {'schema_version':1, 'importer_api_version':1, 'renderer_api_version':1,
        'source_sha256':digest(graph), 'seed_order':list(graph['seed_order']),
        'ordering':ordering, 'crosswalk':crosswalk,
        'fields':[{'pointer':pointer,'sha256':digest(pair),'emitted':True} for pointer,pair in content_fields(graph)],
        'outputs':{'graph-declarations.tex':hashlib.sha256(declarations.encode()).hexdigest(),
                   'graph-body.tex':hashlib.sha256(body.encode()).hexdigest()},
        'trusted_native':trusted_native,
        'source_bindings':[{'key':s['key'],'sha256':s['sha256']} for s in graph.get('sources', [])]}
    return declarations, body, report, staged_assets

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--bilingual-pdf-skill', required=True, type=Path)
    parser.add_argument('--output', type=Path, help='New directory for derived fragments and report; omit to validate')
    parser.add_argument('--asset-root', type=Path)
    parser.add_argument('--trusted-native', action='store_true', help='Allow executable trusted native TeX runs; use isolation')
    args = parser.parse_args()
    try:
        graph = load_graph(args.input.read_text(encoding='utf-8'))
        renderer = load_renderer(args.bilingual_pdf_skill)
        declarations, body, report, assets = render(graph, renderer, trusted_native=args.trusted_native, asset_root=args.asset_root)
        if args.output:
            args.output.mkdir(parents=True, exist_ok=False)
            for name, content in [('graph-declarations.tex', declarations), ('graph-body.tex', body), ('graph-report.json', json.dumps(report, indent=2, ensure_ascii=False)+'\n')]:
                (args.output/name).write_text(content, encoding='utf-8')
            for name, source in assets.items():
                destination = args.output/name
                destination.parent.mkdir(exist_ok=True)
                shutil.copyfile(source, destination)
        print(json.dumps({'ok':True, 'nodes':len(graph['nodes']), 'source_sha256':report['source_sha256'], 'exact':report['ordering']['exact']}))
        return 0
    except (ValueError, OSError, RecursionError) as error:
        print(str(error), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
