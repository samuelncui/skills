#!/usr/bin/env python3
"""Stage curated outputs at installed-skill paths, with one local manifest per skill."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ('en-fr', 'en-zh-Hans', 'en-ar', 'zh-Hans-ja')
EXAMPLE_ROOTS = ('skills/bilingual-pdf/examples', 'skills/course-guide-quick-reference/examples')
ARTICLE_ROOT, COURSE_ROOT = EXAMPLE_ROOTS
COURSE = COURSE_ROOT + '/three-concepts'
PDFS = {**{f'{ARTICLE_ROOT}/{name}/document.pdf': f'{name}-bilingual/document.pdf' for name in ARTICLES},
        f'{COURSE}/notes.pdf': 'native-course-example/notes.pdf',
        f'{COURSE}/quick-reference.pdf': 'native-course-example/quick-reference.pdf'}
INPUTS = [f'{ARTICLE_ROOT}/{name}/source.json' for name in ARTICLES] + [f'{COURSE}/source.md', f'{COURSE}/source-map.json']
PREVIEWS = {**{f'{ARTICLE_ROOT}/{name}/preview.png': (f'{name}-bilingual/document.pdf', 0) for name in ARTICLES},
            f'{COURSE}/notes-preview.png': ('native-course-example/notes.pdf', 0),
            f'{COURSE}/quick-reference-preview.png': ('native-course-example/quick-reference.pdf', 0)}
TRANSIENT = {'.aux', '.log', '.out', '.toc', '.xdv', '.fls', '.fdb_latexmk', '.synctex.gz'}


def bounded_file(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError('Missing or out-of-bundle example: ' + relative)
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_names(source_root, example_root):
    generated = set(PDFS) | set(PREVIEWS)
    for required in INPUTS:
        if required.startswith(example_root + '/'):
            bounded_file(source_root, required)
    names = []
    for p in sorted((source_root / example_root).rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(source_root).as_posix()
        if rel in generated or p.name == 'MANIFEST.json' or any(p.name.endswith(x) for x in TRANSIENT) or p.suffix == '.pdf':
            continue
        if any(x.startswith('.') or x == '__pycache__' for x in Path(rel).parts):
            continue
        if p.suffix not in {'.json', '.md', '.tex', '.sty', '.png', '.jpg', '.jpeg'} and p.name not in {'LICENSE', 'Makefile'}:
            continue
        names.append(p.relative_to(source_root / example_root).as_posix())
    return names


def collect_examples(matrix, output, source_root=ROOT, native_matrix=None):
    if output.exists():
        raise ValueError('Choose a new example output directory')
    for result in [matrix] + ([native_matrix] if native_matrix is not None else []):
        if json.loads((result / 'matrix.json').read_text()).get('ok') is not True:
            raise ValueError('Only a passing matrix can produce curated examples')
    copies = [(bounded_file(native_matrix if target.startswith(COURSE + '/') and native_matrix is not None else matrix, source), Path(target)) for target, source in PDFS.items()]
    output.mkdir(parents=True)
    records = []
    for source, relative in copies:
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({'path': relative.as_posix(), 'sha256': digest(target)})
    for example_root in EXAMPLE_ROOTS:
        base = source_root / example_root
        manifest = {
            'source_hashes': {name: digest(bounded_file(base, name)) for name in source_names(source_root, example_root)},
            'files': [{**x, 'path': str(Path(x['path']).relative_to(example_root))} for x in records if x['path'].startswith(example_root + '/')],
            'previews': [],
            'regeneration': 'See the repository tests/README.md. Sources and outputs are bundled in this skill; byte identity requires the same toolchain and fixed clock.'}
        (output / example_root / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return records


def check_examples(output, source_root=ROOT):
    count = 0
    for example_root in EXAMPLE_ROOTS:
        base = output / example_root
        manifest = json.loads((base / 'MANIFEST.json').read_text())
        expected_pdfs = {str(Path(x).relative_to(example_root)) for x in PDFS if x.startswith(example_root + '/')}
        expected_previews = {str(Path(x).relative_to(example_root)) for x in PREVIEWS if x.startswith(example_root + '/')}
        if {x['path'] for x in manifest['files']} != expected_pdfs:
            raise ValueError('Example manifest inventory mismatch')
        previews = manifest.get('previews', [])
        if previews and {x['path'] for x in previews} != expected_previews:
            raise ValueError('Example preview inventory mismatch')
        expected = expected_pdfs | {x['path'] for x in previews} | set(manifest['source_hashes']) | {'MANIFEST.json'}
        actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        if actual - expected:
            raise ValueError('Unexpected file in curated examples: ' + ', '.join(sorted(actual - expected)))
        for record in manifest['files'] + previews:
            if digest(bounded_file(base, record['path'])) != record['sha256']:
                raise ValueError('Example output hash mismatch: ' + record['path'])
        if set(manifest['source_hashes']) != set(source_names(source_root, example_root)):
            raise ValueError('Example source inventory changed; regenerate curated outputs')
        for name, expected_hash in manifest['source_hashes'].items():
            if digest(bounded_file(source_root / example_root, name)) != expected_hash:
                raise ValueError('Example source changed; regenerate curated outputs: ' + name)
        count += len(manifest['files'])
    return count


def make_previews(matrix, output, native_matrix=None):
    if output.exists():
        raise ValueError('Choose a new preview directory')
    import pymupdf
    output.mkdir(parents=True)
    records = []
    for target, (relative, page_number) in PREVIEWS.items():
        base = native_matrix if target.startswith(COURSE + '/') and native_matrix is not None else matrix
        destination = output / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(bounded_file(base, relative)) as pdf:
            pdf[page_number].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False).save(destination)
        records.append({'path': target, 'sha256': digest(destination)})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path)
    parser.add_argument('--native-matrix', type=Path)
    parser.add_argument('--output', required=True, type=Path, help='Repository root to check, or a fresh staging root')
    parser.add_argument('--previews', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        count = check_examples(args.output)
    else:
        if args.matrix is None:
            parser.error('--matrix is required unless --check is set')
        count = len(collect_examples(args.matrix, args.output, native_matrix=args.native_matrix))
        if args.previews:
            records = make_previews(args.matrix, args.previews, args.native_matrix)
            for example_root in EXAMPLE_ROOTS:
                path = args.output / example_root / 'MANIFEST.json'
                manifest = json.loads(path.read_text())
                manifest['previews'] = [{**x, 'path': str(Path(x['path']).relative_to(example_root))} for x in records if x['path'].startswith(example_root + '/')]
                path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'ok': True, 'pdfs': count, 'preview_images': len(PREVIEWS) if args.previews and not args.check else 0}))


if __name__ == '__main__':
    main()
