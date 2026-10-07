#!/usr/bin/env python3
"""Serial, one-observation PDF performance probes with unittest correctness checks.
Example from a checkout with dependencies already installed:
    .venv/bin/python tests/benchmark_bilingual.py --work .local/benchmark --case en-zh-Hans --conditions clean noop edit

Runs serially using unittest correctness assertions, with one observation per
condition and a 105-second per-observation foreground budget. Use a fresh work
directory for a new source comparison; receipts cannot be overwritten.
Dependencies match tests/README.md. Timings exclude installation, translation,
visual/semantic review, upload, and remote tool/queue latency. Clean means new
document build state, not a cold OS cache. Font-cache probes additionally require
a self-contained FONTCONFIG_FILE with one cachedir and no includes. Environment
and source manifests, raw logs, and PDFs are private local evidence, not public
artifacts or portable performance guarantees.
"""
import argparse, copy, hashlib, importlib.util, json, os, platform, re, shutil, signal, subprocess, sys, time, unittest
from pathlib import Path
from datetime import datetime, timezone
P = argparse.ArgumentParser()
P.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
P.add_argument('--work', type=Path, required=True)
P.add_argument('--case', default='en-zh-Hans', choices=['en-zh-Hans', 'en-fr', 'multipage-en-fr'])
P.add_argument('--condition', default='clean', choices=['clean', 'noop', 'edit', 'asset', 'layout', 'preflight', 'font-cold', 'font-warm'])
P.add_argument('--pipeline', default='native', choices=['native','render','build'], help='native reuse, repeated fresh render, or managed incremental JSON build')
P.add_argument('--worker', action='store_true')
P.add_argument('--compare-to', type=Path, help='Assert identical inputs and page text/pixels against this prior observation directory')
P.add_argument('--conditions', nargs='+', choices=['clean', 'noop', 'edit', 'asset', 'layout', 'preflight', 'font-cold', 'font-warm'], help='One serial observation per listed condition, e.g. clean noop edit')
A = P.parse_args()
requested=A.conditions or [A.condition]
if A.compare_to and A.pipeline=='native' and any(c!='preflight' for c in requested):
    P.error('--compare-to requires render/build pipelines, except for preflight-only comparisons')
if A.case=='multipage-en-fr' and any(c in ('edit','asset') for c in requested):
    P.error('edit/asset observations require a full article fixture')
if A.pipeline=='native' and any(c in ('asset','layout') for c in requested):
    P.error('asset/layout observations require a render/build pipeline')
A.work = A.work.resolve()
A.repo = A.repo.resolve()

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

def query(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {'command': cmd, 'exit': p.returncode, 'output': (p.stdout + p.stderr).strip()}

def initialize():
    root = A.work
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'snapshot.json').exists():
        frozen = json.loads((root / 'snapshot.json').read_text())
        for name, digest in frozen['hashes'].items():
            if sha(root / name) != digest:
                raise RuntimeError('Frozen benchmark input changed: ' + name)
        return
    assert A.repo and A.repo.is_dir()
    source = A.repo / 'skills/bilingual-pdf'
    frozen = root / 'snapshot/bilingual-pdf'
    for d in ['assets', 'scripts']:
        shutil.copytree(source / d, frozen / d, ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(source / 'LICENSE', frozen / 'LICENSE')
    for case in ['en-zh-Hans', 'en-fr']:
        target = root / 'fixtures' / case
        target.mkdir(parents=True)
        shutil.copyfile(source / 'examples' / case / 'source.json', target / 'source.json')
    shutil.copytree(source / 'examples/shared', root / 'fixtures/shared')
    if A.case == 'multipage-en-fr':
        # Scale the existing render_matrix multipage-uneven workload, without
        # introducing private content or another renderer/test framework.
        fixture = json.loads((A.repo / 'tests/fixtures/garden-en-fr.json').read_text())
        fixture['layout'] = {'covers': True}
        fixture['blocks'] = [{'id': f'block-{i}', 'text': ['Check the length, then record the unit. ' * 5, 'Vérifiez la longueur, puis notez l’unité utilisée. ' * 7]} for i in range(140)]
        fixture['blocks'].insert(0, {'id': 'uneven-list', 'kind': 'list', 'text': [['First step.', 'Second step.'], ['La première étape doit être expliquée assez longuement pour occuper plusieurs lignes dans la colonne de droite.', 'Deuxième étape.']]})
        target = root / 'fixtures/multipage-en-fr'
        target.mkdir(parents=True)
        write(target / 'source.json', fixture)
    files = {str(p.relative_to(root)): sha(p) for group in ['snapshot', 'fixtures'] for p in (root / group).rglob('*') if p.is_file()}
    versions = {n: query(cmd) for n, cmd in {'python': [sys.executable, '--version'], 'xelatex': ['xelatex', '--version'], 'latexmk': ['latexmk', '-v'], 'fc-match': ['fc-match', '--version'], 'kpsewhich': ['kpsewhich', '--version']}.items()}
    from importlib.metadata import version
    versions['python_packages'] = {n: version(n) for n in ['PyMuPDF', 'Pillow', 'fonttools']}
    env = {'timestamp': datetime.now(timezone.utc).isoformat(), 'python': sys.executable, 'platform': platform.platform(), 'cpu_model': platform.processor(), 'visible_cpus': os.cpu_count(), 'affinity_cpus': len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None, 'host_meminfo': Path('/proc/meminfo').read_text().splitlines()[:3] if Path('/proc/meminfo').exists() else None, 'loadavg': os.getloadavg() if hasattr(os, 'getloadavg') else None, 'resource_note': 'Visible host CPU/memory figures are not necessarily container allocation; cgroup values are recorded separately when readable', 'versions': versions}
    for n in ['cpu.max', 'memory.max']:
        p = Path('/sys/fs/cgroup') / n
        if p.exists():
            env[n] = p.read_text().strip()
    write(root / 'environment.json', env)
    write(root / 'snapshot.json', {'repository': str(A.repo), 'head': query(['git', '-C', str(A.repo), 'rev-parse', 'HEAD']), 'status': query(['git', '-C', str(A.repo), 'status', '--short']), 'hashes': files, 'state': 'Chosen checkout HEAD plus any listed working-tree changes, frozen before timing', 'cold_definition': 'new document build directory; existing OS and font caches unless isolated font condition'})

def worker():
    root = A.work
    case = A.case
    condition = A.condition
    result = {'case': case, 'condition': condition, 'pipeline': A.pipeline, 'status': 'running', 'started_at': datetime.now(timezone.utc).isoformat(), 'benchmark_sha256':sha(Path(__file__)), 'commands': [], 'phases': {}, 'cache': 'shared installed font cache' if not condition.startswith('font-') else 'isolated fontconfig cache; OS page cache not reset'}
    dest = root / 'results' / case
    dest.mkdir(parents=True, exist_ok=True)
    receipt = dest / (condition + '.json')
    if receipt.exists():
        raise RuntimeError('Receipt already exists; do not overwrite an observation')
    project = root / 'documents' / case / ('font-cache' if condition.startswith('font-') else 'normal')
    if A.pipeline=='render' and not condition.startswith('font-'):
        project=project.parent/condition
    if condition == 'font-warm':
        project = root / 'documents' / case / 'font-cache-warm'
    if condition.startswith('font-'):
        config_path = os.environ.get('FONTCONFIG_FILE')
        if not config_path:
            raise RuntimeError('Isolated cache tests require FONTCONFIG_FILE naming a self-contained config with one cachedir and no includes')
        config = Path(config_path).read_text()
        if '<include' in config or len(re.findall('<cachedir>.*?</cachedir>', config)) != 1:
            raise RuntimeError('Cannot prove isolated font cache: require exactly one cachedir and no includes')
        cache = root / 'font-cache' / case
        if condition == 'font-cold' and cache.exists():
            raise RuntimeError('Font-cold requires a new isolated cache; use a new work directory')
        if condition == 'font-warm' and (not cache.exists() or not any(cache.iterdir())):
            raise RuntimeError('Font-warm requires the populated cache from font-cold')
        cache.mkdir(parents=True, exist_ok=True)
        config = re.sub('<cachedir>.*?</cachedir>', '<cachedir>' + str(cache) + '</cachedir>', config)
        conf = root / ('fonts-' + case + '.conf')
        conf.write_text(config)
        os.environ['FONTCONFIG_FILE'] = str(conf)
        result['cache_files_before'] = len(list(cache.rglob('*')))
    start = time.perf_counter()
    spec = importlib.util.spec_from_file_location('bilingual_benchmark', root / 'snapshot/bilingual-pdf/scripts/bilingual_pdf.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result['phases']['renderer_import'] = time.perf_counter() - start

    def timed(name, fn):

        def wrap(*a, **kw):
            t = time.perf_counter()
            try:
                return fn(*a, **kw)
            finally:
                result['phases'][name] = result['phases'].get(name, 0) + time.perf_counter() - t
        return wrap
    for name in ['validate', 'preflight', 'export_document', 'check_pdf']+(['build_document'] if hasattr(mod,'build_document') else []):
        setattr(mod, name, timed(name, getattr(mod, name)))
    oldrun = subprocess.run

    def tracked(cmd, *a, **kw):
        t = time.perf_counter()
        p = oldrun(cmd, *a, **kw)
        elapsed = time.perf_counter() - t
        if cmd[0] == 'latexmk':
            result['phases']['latexmk'] = elapsed
            result['commands'].append({'argv': cmd, 'cwd': str(kw.get('cwd')), 'exit': p.returncode, 'seconds': elapsed})
            out = (p.stdout or '') + (p.stderr or '')
            result['tex_passes'] = len(re.findall("Run number \\d+ of rule 'xelatex'", out))
            result['xdvipdfmx_passes'] = len(re.findall("Run number \\d+ of rule 'xdvipdfmx'", out))
            (dest / (condition + '-latexmk.log')).write_text(out)
        return p
    mod.subprocess.run = tracked
    try:
        if condition=='preflight':
            result['output']=mod.preflight(mod.validate(json.loads((root/'fixtures'/case/'source.json').read_text())))
            status=0 if result['output']['ok'] else 2
        elif A.pipeline!='native':
            if condition.startswith('font-'):raise ValueError('Font-cache observations use the native pipeline')
            inputs=root/'working-inputs'/case
            if condition=='clean':
                if inputs.exists():raise RuntimeError('Working inputs already exist')
                shutil.copytree(root/'fixtures'/case,inputs)
                shutil.copytree(root/'fixtures/shared',inputs/'assets')
            if not inputs.is_dir():raise RuntimeError('Run clean before update conditions')
            source=inputs/'source.json'
            data=json.loads(source.read_text())
            if condition=='edit':
                old='A short translation does not have to be padded to match a longer one.'
                body=source.read_text()
                if body.count(old)!=1:raise RuntimeError('Edit sentence must occur exactly once')
                source.write_text(body.replace(old,'A short translation can remain concise even when its counterpart needs more words.'))
            elif condition=='asset':
                from PIL import Image,ImageDraw
                figure=next(b for b in data['blocks'] if b.get('kind')=='figure')
                relative=mod.figure_images(figure)[0]
                asset=inputs/'assets'/relative
                with Image.open(asset) as im:
                    changed=im.convert('RGB');ImageDraw.Draw(changed).rectangle((0,0,25,25),fill='red');changed.save(asset)
            elif condition=='layout':
                data.setdefault('layout',{})['gap_mm']=7
                source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
            result['input_hashes']={str(p.relative_to(inputs)):sha(p) for p in inputs.rglob('*') if p.is_file()}
            project.parent.mkdir(parents=True,exist_ok=True)
            sys.argv=[str(root/'snapshot/bilingual-pdf/scripts/bilingual_pdf.py'), A.pipeline, str(source), '--output', str(project), '--asset-root', str(inputs/'assets')]
            status=mod.main()
        elif condition in ['clean', 'font-cold', 'font-warm']:
            project.parent.mkdir(parents=True, exist_ok=True)
            sys.argv = [str(root / 'snapshot/bilingual-pdf/scripts/bilingual_pdf.py'), 'render', str(root / 'fixtures' / case / 'source.json'), '--output', str(project), '--asset-root', str(root / 'fixtures/shared')]
            status = mod.main()
        else:
            if condition not in ['noop','edit']:raise ValueError('Asset/layout conditions require render or build pipeline')
            assert project.is_dir(), 'Clean case must complete first'
            if condition == 'edit':
                content = project / 'content.tex'
                body = content.read_text()
                old = 'A short translation does not have to be padded to match a longer one.'
                assert body.count(old) == 1
                content.write_text(body.replace(old, 'A short translation can remain concise even when its counterpart needs more words.'))
                result['edit'] = 'One English paragraph sentence changed only in copied native content.tex'
            data = json.loads((root / 'fixtures' / case / 'source.json').read_text())
            r = mod.compile_project(data, project, 'bilingual', {'benchmark': 'toolchain preflight already passed for unchanged environment'})
            status = 0 if r['ok'] else 4
        result['status'] = 'passed' if status == 0 else 'failed'
        result['exit_code'] = status
        if condition!='preflight' and (project / 'result.json').exists():
            result['output'] = json.loads((project / 'result.json').read_text())
            result['pdf_bytes'] = (project / 'document.pdf').stat().st_size
            for suffix in ['.pdf', '.aux', '.log']:
                shutil.copyfile(project / ('document' + suffix), dest / (condition + suffix))
            result['preserved_pdf'] = str(dest / (condition + '.pdf'))
            import pymupdf
            with pymupdf.open(project/'document.pdf') as pdf:
                result['page_evidence']=[{'text':p.get_text(),'pixels_sha256':hashlib.sha256(p.get_pixmap(alpha=False).samples).hexdigest()} for p in pdf]
        if condition.startswith('font-'):
            result['cache_files_after'] = len(list(cache.rglob('*')))
    except Exception as e:
        result['status'] = 'failed'
        result['exception'] = repr(e)
        status = 1
    finally:
        result['worker_seconds'] = time.perf_counter() - start
        result['ended_at'] = datetime.now(timezone.utc).isoformat()
        result['loadavg_after'] = os.getloadavg() if hasattr(os, 'getloadavg') else None
        write(receipt, result)
    return status

class BenchmarkCorrectness(unittest.TestCase):

    def test_requested_observations(self):
        for condition in A.conditions or [A.condition]:
            with self.subTest(case=A.case, condition=condition):
                A.condition = condition
                self.observe_condition()

    def observe_condition(self):
        initialize()
        receipt = A.work / 'results' / A.case / (A.condition + '.json')
        self.assertFalse(receipt.exists(), 'Receipt already exists; choose a new work directory rather than overwrite an observation')
        cmd = [sys.executable, str(Path(__file__).resolve()), '--work', str(A.work), '--case', A.case, '--condition', A.condition, '--pipeline', A.pipeline, '--worker']
        t = time.perf_counter()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, stderr = proc.communicate(timeout=105)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                stdout, stderr = proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                stdout, stderr = proc.communicate()
            d = A.work / 'results' / A.case
            d.mkdir(parents=True, exist_ok=True)
            (d / (A.condition + '-timeout.log')).write_text(stdout + stderr)
            write(d / (A.condition + '-incomplete.json'), {'status': 'incomplete', 'reason': '105-second foreground budget exhausted; owned process group terminated', 'command': cmd})
            self.fail('Benchmark incomplete: timeout; see preserved evidence')
        p = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
        elapsed = time.perf_counter() - t
        d = A.work / 'results' / A.case
        d.mkdir(parents=True, exist_ok=True)
        (d / (A.condition + '-worker.log')).write_text(p.stdout + p.stderr)
        receipt = d / (A.condition + '.json')
        self.assertTrue(receipt.exists(), p.stdout + p.stderr)
        r = json.loads(receipt.read_text())
        r['complete_process_seconds'] = elapsed
        r['process_command'] = cmd
        write(receipt, r)
        print(json.dumps({k: r.get(k) for k in ['case', 'condition', 'status', 'complete_process_seconds', 'phases', 'tex_passes', 'xdvipdfmx_passes']}), flush=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(r['status'], 'passed')
        if A.condition=='preflight':
            self.assertTrue(r['output']['ok'])
            if A.compare_to:
                baseline=json.loads((A.compare_to/'results'/A.case/(A.condition+'.json')).read_text())
                self.assertEqual(r['output'],baseline['output'])
            return
        self.assertGreater(r['output']['pages'], 0)
        self.assertTrue(r['output']['ok'])
        self.assertFalse(r['output']['errors'])
        self.assertGreater(r['output']['paired_blocks_checked'], 0)
        if A.compare_to:
            baseline=json.loads((A.compare_to/'results'/A.case/(A.condition+'.json')).read_text())
            self.assertEqual(r['input_hashes'],baseline['input_hashes'],'Benchmark inputs differ')
            self.assertEqual(r['page_evidence'],baseline['page_evidence'],'Page text or pixels differ from fresh baseline')
        if A.condition == 'noop' and A.pipeline!='render':
            self.assertEqual(r['tex_passes'], 0, 'No-op unexpectedly invoked XeLaTeX')
if __name__ == '__main__':
    if A.worker:
        sys.exit(worker())
    unittest.main(argv=[sys.argv[0]], verbosity=2)
