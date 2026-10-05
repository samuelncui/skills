"""Explicit renderer dependencies and bounded shared/localized figure inputs."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
from bilingual_pdf import InputError,validate,figure_images,resolve_image,tex_parts,export_document

class FigureAssetTests(unittest.TestCase):
    def setUp(self):
        self.doc={'languages':['en','fr'],'title':['Map','Carte'],'blocks':[{'id':'map','kind':'figure','image':['pipeline-en.png','pipeline-fr.png'],'text':['English map.','Carte française.']}]}
    def test_native_uses_two_localized_images(self):
        body=tex_parts(validate(self.doc),'bilingual')[2]
        self.assertIn(r'\ParallelFigure{map}{figure-map/left.png}{English map.}{Carte française.}[figure-map/right.png]',body)
    def test_shared_image_remains_scalar(self):
        self.doc['blocks'][0].update(image='photo.png',placement='shared')
        self.assertIn(r'\ParallelWideFigure{map}{figure-map/image.png}',tex_parts(validate(self.doc),'bilingual')[2])
    def test_shared_image_pair_is_rejected(self):
        self.doc['blocks'][0]['placement']='shared'
        with self.assertRaises(InputError):validate(self.doc)
    def test_invalid_pairs_and_paths_are_rejected(self):
        for value in [[],['a.png'],['a.png','b.png','c.png'],['a.png',{}],['a.png','../b.png'],['a.png','/b.png'],['a.png','b[1].png']]:
            with self.subTest(value=value),self.assertRaises(InputError):figure_images({'image':value})
    def test_legacy_scalar_pair_remains_supported(self):
        self.doc['blocks'][0]['image']='same.png'
        self.assertEqual(figure_images(validate(self.doc)['blocks'][0]),['same.png'])
    def test_explicit_root_and_default_root_are_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);inputs=root/'inputs';assets=root/'shared';inputs.mkdir();assets.mkdir()
            (assets/'map.png').write_bytes(b'image')
            with self.assertRaises(InputError):resolve_image(inputs/'source.json','map.png')
            self.assertEqual(resolve_image(inputs/'source.json','map.png',assets),assets/'map.png')
    def test_traversal_and_symlink_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);assets=root/'shared';assets.mkdir();outside=root/'private.png';outside.write_bytes(b'private')
            (assets/'linked.png').symlink_to(outside)
            for relative in ['../private.png','linked.png','/private.png']:
                with self.subTest(relative=relative),self.assertRaises(InputError):resolve_image(root/'source.json',relative,assets)
    def test_export_materializes_only_used_assets(self):
        # A repository asset is exported to a portable delivery project, not duplicated in checked-in examples.
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'portable'
            export_document(validate(self.doc),Path(td)/'source.json',out,'bilingual',asset_root=ROOT/'skills/bilingual-pdf/examples/shared')
            self.assertTrue((out/'paralleltext.sty').is_file())
            self.assertEqual(sorted(p.relative_to(out).as_posix() for p in out.rglob('*.png')),['figure-map/left.png','figure-map/right.png'])
            self.assertNotEqual((out/'figure-map/left.png').read_bytes(),(out/'figure-map/right.png').read_bytes())
    def test_pair_image_names_cannot_collide_with_other_ids(self):
        doc=copy.deepcopy(self.doc)
        doc['blocks'].append({'id':'map-1','kind':'figure','image':'pipeline-ja.png','text':['Another','Autre']})
        doc['blocks'].append({'id':'map-1.png','kind':'figure','image':['pipeline-zh-Hans.png','pipeline-ar.png'],'text':['Pair','Paire']})
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'portable'
            export_document(validate(doc),Path(td)/'source.json',out,'bilingual',asset_root=ROOT/'skills/bilingual-pdf/examples/shared')
            self.assertEqual(len([p for p in out.rglob('*.png') if p.is_file()]),5)
            self.assertNotEqual((out/'figure-map/left.png').read_bytes(),(out/'figure-map-1/image.png').read_bytes())
    def test_one_asset_root_does_not_enable_absolute_paths(self):
        with self.assertRaises(InputError):resolve_image(ROOT/'source.json',str(ROOT/'skills/bilingual-pdf/examples/shared/layout-anatomy.png'),ROOT)

class NativeDependencyTests(unittest.TestCase):
    def make_fixture(self,root):
        shutil.copyfile(ROOT/'skills/study-notes/examples/Makefile',root/'Makefile')
        study=root/'workflow with spaces';(study/'assets').mkdir(parents=True)
        for name in ('studytools.sty','study-tree.tex'):(study/'assets'/name).write_text('fixture')
        return study
    def test_missing_dependency_is_actionable_and_creates_no_products(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);study=self.make_fixture(root)
            env={**os.environ,'STUDY_NOTES_SKILL':str(study)};env.pop('BILINGUAL_PDF_SKILL',None)
            proc=subprocess.run(['make'],cwd=root,env=env,capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0);self.assertIn('BILINGUAL_PDF_SKILL',proc.stderr)
            self.assertFalse((root/'.build-products.tex').exists());self.assertFalse(list(root.glob('*.pdf')))
    def test_literal_dependency_paths_from_environment_and_make_arguments(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);study=self.make_fixture(root)
            for basename in ('engine with spaces','engine`touch injection-marker`','engine$(shell touch injection-marker)','engine$Dollar'):
                engine=root/basename;(engine/'assets').mkdir(parents=True)
                (engine/'assets/paralleltext.sty').write_text('fixture');(engine/'SKILL.md').write_text('fixture')
                for args in ([],['BILINGUAL_PDF_SKILL='+str(engine),'STUDY_NOTES_SKILL='+str(study)]):
                    with self.subTest(basename=basename,args=args):
                        proc=subprocess.run(['make','check-dependency']+args,cwd=root,env={**os.environ,'BILINGUAL_PDF_SKILL':str(engine),'STUDY_NOTES_SKILL':str(study)},capture_output=True,text=True)
                        self.assertEqual(proc.returncode,0,proc.stderr);self.assertFalse((root/'injection-marker').exists())
    def test_native_only_package_has_one_renderer_owner(self):
        study=ROOT/'skills/study-notes'
        self.assertFalse(list(study.rglob('paralleltext.sty')))
        self.assertFalse(list(study.rglob('bilingual_pdf.py')))
        self.assertFalse((study/'scripts/course_documents.py').exists())
        self.assertFalse((ROOT/'skills/course-guide-quick-reference').exists())
        self.assertTrue((study/'assets/studytools.sty').is_file())

if __name__=='__main__':unittest.main()
