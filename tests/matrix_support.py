"""Single-worker, bounded integration cases with checkpointed outcomes and cleanup.

Exit 0 means every requested case passed; 1 means an assertion/build failed; 75
means requested work remains blocked or unrun. Only complete=True means the
whole suite passed. Resume never retries unchanged assertion failures.
"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_DEADLINE = None

class InfrastructureTimeout(RuntimeError):
    pass

class BlockedCase(RuntimeError):
    pass

def implementation_fingerprint(root=ROOT):
    paths = []
    for directory in (root/'skills/bilingual-pdf', root/'skills/study-notes', root/'tests', root/'tools'):
        for path in directory.rglob('*'):
            if not path.is_file() or any(x in ('__pycache__', '.local') for x in path.parts):
                continue
            if path.name in ('RESULTS.json', 'MANIFEST.json') or path.name.endswith('preview.png'):
                continue
            if path.suffix in ('.py', '.sty', '.tex', '.json', '.png') or path.name in ('Makefile', 'source.md'):
                paths.append(path)
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
    return digest.hexdigest()

def run_command(command, **kwargs):
    """Run one owned process group; retain partial output and reap on timeout."""
    limit = kwargs.pop('timeout', 180)
    if _DEADLINE is not None:
        limit = min(limit, max(.1, _DEADLINE-time.monotonic()))
    kwargs.pop('capture_output', None)
    kwargs.setdefault('text', True)
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True, **kwargs)
    except FileNotFoundError as error:
        raise BlockedCase('Required executable is unavailable: '+str(command[0])) from error
    try:
        stdout, stderr = proc.communicate(timeout=limit)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = proc.communicate()
        directory = Path(kwargs.get('cwd', '.'))
        (directory/'interrupted-command.log').write_text(
            stdout+stderr if kwargs['text'] else (stdout+stderr).decode(errors='replace'))
        if isinstance(error, KeyboardInterrupt):
            raise
        raise InfrastructureTimeout(f'Owned process group exceeded {limit:.1f} seconds; see interrupted-command.log') from error
    return subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)

def add_matrix_arguments(parser):
    parser.add_argument('--resume', action='store_true', help='Resume unchanged fixtures from per-case checkpoints')
    parser.add_argument('--case', action='append', help='Run only a named case; repeatable')
    parser.add_argument('--budget-seconds', type=float, default=0,
                        help='Bound this foreground batch; 0 means the normal full run')

def initialize_output(output, resume):
    output = Path(output).resolve()
    if output.exists() and not resume:
        raise SystemExit('Choose a fresh output directory or explicitly use --resume')
    if resume and not output.exists():
        raise SystemExit('Cannot resume a missing output directory')
    output.mkdir(parents=True, exist_ok=True)
    return output

def _write_json(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)

def execute_matrix(cases, run, work, args, suite, name=lambda case: case[0]):
    global _DEADLINE
    if args.budget_seconds < 0:
        raise ValueError('Budget must not be negative')
    _DEADLINE = time.monotonic()+args.budget_seconds if args.budget_seconds else None
    identities = [name(case) for case in cases]
    if not identities or len(set(identities)) != len(identities):
        raise ValueError('Matrix needs nonempty, unique case names')
    if any(not ident or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in ident) for ident in identities):
        raise ValueError('Case names must be safe checkpoint filenames')
    selected = set(args.case or identities)
    unknown = selected-set(identities)
    if unknown:
        raise ValueError('Unknown cases: '+', '.join(sorted(unknown)))
    checkpoint = work/'case-results'
    checkpoint.mkdir(exist_ok=True)
    fingerprint = implementation_fingerprint()
    marker = work/'execution.json'
    identity = {'suite': suite, 'implementation_sha256': fingerprint, 'cases': identities}
    if marker.exists():
        if json.loads(marker.read_text()) != identity:
            raise ValueError('Implementation, fixtures or suite changed; choose a fresh output directory')
    else:
        _write_json(marker, identity)
    results = {}
    for filename in checkpoint.glob('*.json'):
        result = json.loads(filename.read_text())
        if result['case'] in identities:
            results[result['case']] = result
    executed = 0
    for case in cases:
        ident = name(case)
        if ident not in selected:
            continue
        previous = results.get(ident)
        if previous and previous.get('status') != 'blocked':
            continue
        if _DEADLINE is not None and _DEADLINE-time.monotonic() < 5:
            break
        started = time.monotonic()
        try:
            result = run(case)
            if not isinstance(result, dict) or result.get('case') != ident or not isinstance(result.get('passed'), bool):
                raise ValueError('Case returned no explicit outcome')
            result['status'] = 'passed' if result['passed'] else 'failed'
        except (InfrastructureTimeout, BlockedCase) as error:
            result = {'case': ident, 'passed': False, 'status': 'blocked', 'error': str(error)}
        except Exception as error:
            result = {'case': ident, 'passed': False, 'status': 'failed', 'error': type(error).__name__+': '+str(error)}
        result['elapsed_seconds'] = round(time.monotonic()-started, 3)
        if previous:
            result['previous_attempts'] = previous.get('previous_attempts', [])+[previous]
        results[ident] = result
        _write_json(checkpoint/(ident+'.json'), result)
        executed += 1
        print(json.dumps({'case': ident, 'status': result['status']}, ensure_ascii=False), flush=True)
        if isinstance(result.get('error'), str) and result['status'] == 'blocked':
            break
    pending = [ident for ident in identities if ident in selected and
               (ident not in results or results[ident].get('status') == 'blocked')]
    failed = [ident for ident in selected if results.get(ident, {}).get('status') == 'failed']
    tests = [dict(results[ident], requested=ident in selected) if ident in results else
             {'case': ident, 'passed': None, 'status': 'unrun' if ident in selected else 'not_requested',
              'requested': ident in selected} for ident in identities]
    report = {'suite': suite, 'ok': not pending and not failed,
              'complete': all(results.get(ident, {}).get('status') == 'passed' for ident in identities),
              'total_cases': len(identities), 'requested_cases': len(selected), 'executed_this_run': executed,
              'pending': pending, 'not_requested': [x for x in identities if x not in selected],
              'tests': tests, 'implementation_sha256': fingerprint,
              'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'visual_review': 'not implied by matrix', 'semantic_review': 'not implied by matrix'}
    _write_json(work/'matrix.json', report)
    print(json.dumps({k: report[k] for k in ('suite', 'ok', 'complete', 'total_cases', 'requested_cases',
                                          'executed_this_run', 'pending', 'not_requested')}, ensure_ascii=False))
    _DEADLINE = None
    return 1 if failed else (75 if pending else 0)


def repeat_text(value, count=3):
    """Repeat safe fixture text while preserving explicit mixed-direction runs."""
    if isinstance(value, str):
        return (value+' ')*count
    runs = []
    for _ in range(count):
        part = [dict(run) for run in value['runs']]
        part[-1]['text'] += ' '
        runs.extend(part)
    return {'runs': runs}

def first_sentence(value):
    """Use the first source sentence as a compact following alignment probe."""
    if isinstance(value, dict):
        value = value['runs'][0]['text']
    for punctuation in ('.', '。'):
        if punctuation in value:
            return value.split(punctuation)[0]+punctuation
    return value
