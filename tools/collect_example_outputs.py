#!/usr/bin/env python3
"""Stage nine curated PDFs and previews; never publish build logs or absolute paths."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tests'))
from matrix_support import implementation_fingerprint
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ('en-fr', 'en-zh-Hans', 'en-ar', 'en-he', 'zh-Hans-ja')
FORMS = ('notes', 'quick-reference', 'keyword-index', 'decision-tree')
ARTICLE_ROOT = 'skills/bilingual-pdf/examples'
STUDY_ROOT = 'skills/study-notes/examples'
EXAMPLE_ROOTS = (ARTICLE_ROOT, STUDY_ROOT)
PDFS = {**{f'{ARTICLE_ROOT}/{pair}/output.pdf': f'{pair}-bilingual/document.pdf' for pair in ARTICLES},
        **{f'{STUDY_ROOT}/{form}.pdf': f'study-example-all/{form}.pdf' for form in FORMS}}
PREVIEWS = {**{f'{ARTICLE_ROOT}/{pair}/preview.png': (f'{pair}-bilingual/document.pdf', 0) for pair in ARTICLES},
            **{f'{STUDY_ROOT}/{form}-preview.png': (f'study-example-all/{form}.pdf', 0) for form in FORMS}}
PACKAGE_INPUTS = {
    'bilingual-pdf': ('scripts/bilingual_pdf.py', 'assets/paralleltext.sty',
                      'assets/bound-profile.tex', 'assets/reading-profile.tex'),
    'study-notes': ('assets/studytools.sty', 'assets/study-tree.tex', 'assets/study-graph-components.tex'),
}
SHARED_IMAGES = ('layout-anatomy.png',)+tuple('pipeline-'+language+'.png'
                                            for language in ('en', 'fr', 'zh-Hans', 'ar', 'he', 'ja'))
INPUTS = ([f'{ARTICLE_ROOT}/{pair}/{name}' for pair in ARTICLES
           for name in ('source.json', 'main.tex', 'languages.tex', 'content.tex')]
          + [f'{ARTICLE_ROOT}/shared/{name}' for name in SHARED_IMAGES]
          + [f'{STUDY_ROOT}/{name}' for name in
             ('source.md', 'source-map.json', 'Makefile', 'common.tex', 'languages.tex',
              'entries.tex', 'decisions.tex', 'notes-content.tex',
              'notes.tex', 'quick-reference.tex', 'keyword-index.tex', 'decision-tree.tex')]
          + [f'skills/{skill}/{name}' for skill, names in PACKAGE_INPUTS.items() for name in names])
TRANSIENT = {'.aux', '.log', '.out', '.toc', '.xdv', '.fls', '.fdb_latexmk', '.synctex.gz'}

def bounded_file(base, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Nonportable example path: '+str(relative))
    path = (base/relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError('Missing or out-of-bundle example: '+str(relative))
    return path

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def package_hashes(source_root, example_root):
    skills = ('bilingual-pdf', 'study-notes') if example_root == STUDY_ROOT else ('bilingual-pdf',)
    return {skill: {name: digest(bounded_file(source_root/'skills'/skill, name))
                    for name in PACKAGE_INPUTS[skill]} for skill in skills}

def source_names(source_root, example_root):
    for required in INPUTS:
        if required.startswith(example_root+'/'):
            bounded_file(source_root, required)
    generated = set(PDFS)|set(PREVIEWS)
    names = []
    for path in sorted((source_root/example_root).rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(source_root).as_posix()
        if relative in generated or path.name == 'MANIFEST.json' or path.suffix == '.pdf':
            continue
        if any(path.name.endswith(x) for x in TRANSIENT) or any(x.startswith('.') or x == '__pycache__' for x in Path(relative).parts):
            continue
        if path.suffix not in {'.json', '.md', '.tex', '.png', '.jpg', '.jpeg'} and path.name not in {'LICENSE', 'Makefile'}:
            raise ValueError('Unexpected source file in curated examples: '+relative)
        names.append(path.relative_to(source_root/example_root).as_posix())
    return names

def _required_cases(matrix, names, source_root):
    report = json.loads(bounded_file(matrix, 'matrix.json').read_text())
    if report.get('implementation_sha256') != implementation_fingerprint(source_root):
        raise ValueError('Matrix evidence is stale for the current sources or fixtures')
    outcomes = {result['case']: result for result in report.get('tests', [])}
    if report.get('ok') is not True or any(
            outcomes.get(name, {}).get('status') != 'passed' or outcomes[name].get('passed') is not True
            for name in names):
        raise ValueError('Curated outputs require passing case evidence: '+', '.join(names))

def _validate_pdf(path):
    import pymupdf
    with pymupdf.open(path) as pdf:
        if not len(pdf):
            raise ValueError('Empty curated PDF')
        text = json.dumps(pdf.metadata, ensure_ascii=False)+'\n'+''.join(page.get_text() for page in pdf)
        if any(token in text for token in ('/workspace/', '/Users/', '/home/', 'file://')):
            raise ValueError('Machine-specific path found in curated PDF: '+path.name)

def make_previews(matrix, output, native_matrix=None):
    """Create previews in a fresh directory; retained for separate review workflows."""
    if output.exists():
        raise ValueError('Choose a new preview directory')
    import pymupdf
    output.mkdir(parents=True)
    records = []
    for target, (relative, page_number) in PREVIEWS.items():
        base = native_matrix if target.startswith(STUDY_ROOT+'/') and native_matrix else matrix
        destination = output/target
        destination.parent.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(bounded_file(base, relative)) as pdf:
            pdf[page_number].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False).save(destination)
        records.append({'path': target, 'sha256': digest(destination)})
    return records

def collect_examples(matrix, output, source_root=ROOT, native_matrix=None):
    if output.exists():
        raise ValueError('Choose a new example output directory')
    study_matrix = native_matrix or matrix
    _required_cases(matrix, [pair+'-bilingual' for pair in ARTICLES], source_root)
    _required_cases(study_matrix, ['study-example-all'], source_root)
    copies = []
    for target, source in PDFS.items():
        path = bounded_file(study_matrix if target.startswith(STUDY_ROOT+'/') else matrix, source)
        _validate_pdf(path)
        copies.append((path, Path(target)))
    # Resolve and hash every dependency before creating a partial output bundle.
    manifests = {}
    for example_root in EXAMPLE_ROOTS:
        manifests[example_root] = {
            'source_hashes': {name: digest(bounded_file(source_root/example_root, name))
                              for name in source_names(source_root, example_root)},
            'package_dependencies': package_hashes(source_root, example_root),
            'files': [], 'previews': [],
            'regeneration': 'See tests/README.md. Source paths are relative to this examples directory; package paths are relative to the named installed skill. Exact bytes require the same toolchain and fixed clock.',
        }
    output.mkdir(parents=True)
    records = []
    import pymupdf
    for source, relative in copies:
        target = output/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({'path': relative.as_posix(), 'sha256': digest(target)})
    for example_root, manifest in manifests.items():
        base = output/example_root
        manifest['files'] = [{**record, 'path': str(Path(record['path']).relative_to(example_root))}
                             for record in records if record['path'].startswith(example_root+'/')]
        for preview, (relative, page_number) in PREVIEWS.items():
            if not preview.startswith(example_root+'/'):
                continue
            source = bounded_file(study_matrix if example_root == STUDY_ROOT else matrix, relative)
            destination = output/preview
            with pymupdf.open(source) as pdf:
                pdf[page_number].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False).save(destination)
            manifest['previews'].append({'path': str(Path(preview).relative_to(example_root)), 'sha256': digest(destination)})
        if example_root == ARTICLE_ROOT:
            for image in SHARED_IMAGES:
                destination = base/'shared'/image
                destination.parent.mkdir(exist_ok=True)
                shutil.copyfile(bounded_file(source_root/example_root, 'shared/'+image), destination)
        (base/'MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return records

def check_examples(output, source_root=ROOT):
    count = 0
    for example_root in EXAMPLE_ROOTS:
        base = output/example_root
        manifest = json.loads(bounded_file(base, 'MANIFEST.json').read_text())
        if manifest.get('package_dependencies') != package_hashes(source_root, example_root):
            raise ValueError('Named package dependencies changed; regenerate curated outputs')
        pdfs = {str(Path(x).relative_to(example_root)) for x in PDFS if x.startswith(example_root+'/')}
        previews = {str(Path(x).relative_to(example_root)) for x in PREVIEWS if x.startswith(example_root+'/')}
        if len(manifest['files']) != len(pdfs) or {x['path'] for x in manifest['files']} != pdfs:
            raise ValueError('Example manifest inventory mismatch')
        if len(manifest['previews']) != len(previews) or {x['path'] for x in manifest['previews']} != previews:
            raise ValueError('Example preview inventory mismatch')
        if set(manifest['source_hashes']) != set(source_names(source_root, example_root)):
            raise ValueError('Example source inventory changed; regenerate curated outputs')
        expected = pdfs|previews|set(manifest['source_hashes'])|{'MANIFEST.json'}
        actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        if actual-expected:
            raise ValueError('Unexpected file in curated examples: '+', '.join(sorted(actual-expected)))
        for record in manifest['files']+manifest['previews']:
            if digest(bounded_file(base, record['path'])) != record['sha256']:
                raise ValueError('Example output hash mismatch: '+record['path'])
        for name, expected_hash in manifest['source_hashes'].items():
            if digest(bounded_file(source_root/example_root, name)) != expected_hash:
                raise ValueError('Example source or shared assets changed; regenerate: '+name)
            # Staged shared assets and checked-in sources must agree too.
            if (base/name).exists() and digest(bounded_file(base, name)) != expected_hash:
                raise ValueError('Staged example source changed: '+name)
        count += len(manifest['files'])
    return count

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path)
    parser.add_argument('--study-matrix', '--native-matrix', dest='study_matrix', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--previews', type=Path, help='Optional additional review-only preview directory')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        count = check_examples(args.output)
    else:
        if args.matrix is None:
            parser.error('--matrix is required unless --check is set')
        count = len(collect_examples(args.matrix, args.output, native_matrix=args.study_matrix))
        if args.previews:
            make_previews(args.matrix, args.previews, args.study_matrix)
    print(json.dumps({'ok': True, 'pdfs': count, 'preview_images': len(PREVIEWS)}))

if __name__ == '__main__':
    main()
