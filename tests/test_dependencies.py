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
        self.doc={'languages':['en','fr'],'title':['Map','Carte'],'blocks':[{'id':'map','kind':'figure','image':['route-en.png','route-fr.png'],'text':['English map.','Carte française.']}]}
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
            export_document(validate(self.doc),Path(td)/'source.json',out,'bilingual',asset_root=ROOT/'skills/bilingual-pdf/assets')
            self.assertTrue((out/'paralleltext.sty').is_file())
            self.assertEqual(sorted(p.relative_to(out).as_posix() for p in out.rglob('*.png')),['figure-map/left.png','figure-map/right.png'])
            self.assertNotEqual((out/'figure-map/left.png').read_bytes(),(out/'figure-map/right.png').read_bytes())
    def test_pair_image_names_cannot_collide_with_other_ids(self):
        doc=copy.deepcopy(self.doc)
        doc['blocks'].append({'id':'map-1','kind':'figure','image':'route-ja.png','text':['Another','Autre']})
        doc['blocks'].append({'id':'map-1.png','kind':'figure','image':['route-zh-Hans.png','route-ar.png'],'text':['Pair','Paire']})
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'portable'
            export_document(validate(doc),Path(td)/'source.json',out,'bilingual',asset_root=ROOT/'skills/bilingual-pdf/assets')
            self.assertEqual(len([p for p in out.rglob('*.png') if p.is_file()]),5)
            self.assertNotEqual((out/'figure-map/left.png').read_bytes(),(out/'figure-map-1/image.png').read_bytes())
    def test_one_asset_root_does_not_enable_absolute_paths(self):
        with self.assertRaises(InputError):resolve_image(ROOT/'source.json',str(ROOT/'skills/bilingual-pdf/assets/footpath.png'),ROOT)

class DependencyTests(unittest.TestCase):
    def load_course(self,path):
        spec=importlib.util.spec_from_file_location('isolated_course_test',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def test_missing_dependency_is_actionable_and_creates_no_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);course=root/'workflow';shutil.copytree(ROOT/'skills/course-guide-quick-reference',course)
            out=root/'result';env=dict(os.environ);env.pop('BILINGUAL_PDF_SKILL',None)
            result=subprocess.run([sys.executable,str(course/'scripts/course_documents.py'),str(ROOT/'tests/fixtures/course-en-fr/source.json'),'--output',str(out)],cwd=root,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,1);self.assertIn('--bilingual-skill',json.loads(result.stdout)['error']);self.assertFalse(out.exists())
    def test_unrelated_install_paths_and_environment_override(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);engine=root/'engines with spaces'/'chosen';course=root/'workflows'/'lesson'
            shutil.copytree(ROOT/'skills/bilingual-pdf',engine);shutil.copytree(ROOT/'skills/course-guide-quick-reference',course)
            module=self.load_course(course/'scripts/course_documents.py')
            with patch.dict(os.environ,{'BILINGUAL_PDF_SKILL':str(root/'wrong')}):
                self.assertEqual(module.configure_renderer(engine),engine)
            self.assertEqual(module._renderer.ROOT,engine)
            guide,quick,topics=module.prepare(json.loads((ROOT/'tests/fixtures/course-en-fr/source.json').read_text()))
            self.assertEqual(len(topics),3)
            with patch.dict(os.environ,{'BILINGUAL_PDF_SKILL':str(engine)}):self.assertEqual(module.configure_renderer(),engine)
    def test_invalid_dependency_and_escaped_script_are_rejected(self):
        module=self.load_course(ROOT/'skills/course-guide-quick-reference/scripts/course_documents.py')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaises(module.InputError):module.configure_renderer(root)
            engine=root/'engine';shutil.copytree(ROOT/'skills/bilingual-pdf',engine)
            script=engine/'scripts/bilingual_pdf.py';script.unlink();script.symlink_to(ROOT/'skills/bilingual-pdf/scripts/bilingual_pdf.py')
            with self.assertRaises(module.InputError):module.configure_renderer(engine)
    def test_course_does_not_vendor_renderer_or_template(self):
        course=ROOT/'skills/course-guide-quick-reference'
        self.assertFalse(list(course.rglob('paralleltext.sty')))
        self.assertFalse(list(course.rglob('bilingual_pdf.py')))
        self.assertFalse((ROOT/'tools/sync_renderer.py').exists())
    def test_incompatible_dependency_is_actionable(self):
        module=self.load_course(ROOT/'skills/course-guide-quick-reference/scripts/course_documents.py')
        with tempfile.TemporaryDirectory() as td:
            engine=Path(td)/'engine';shutil.copytree(ROOT/'skills/bilingual-pdf',engine)
            script=engine/'scripts/bilingual_pdf.py'
            script.write_text(script.read_text().replace('RENDERER_API_VERSION = 1','RENDERER_API_VERSION = 0'))
            with self.assertRaisesRegex(module.InputError,'Update both skills'):module.configure_renderer(engine)
            self.assertIsNone(module._renderer)
    def test_native_dependency_path_is_not_shell_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            shutil.copyfile(ROOT/'skills/course-guide-quick-reference/examples/Makefile',root/'Makefile')
            for basename in ('engine`touch injection-marker`','engine$(shell touch injection-marker)','engine$Dollar'):
                engine=root/basename;(engine/'assets').mkdir(parents=True)
                (engine/'assets/paralleltext.sty').write_text('test')
                for args in ([],['BILINGUAL_PDF_SKILL='+str(engine)]):
                    with self.subTest(basename=basename,args=args):
                        proc=subprocess.run(['make','check-dependency']+args,cwd=root,env={**os.environ,'BILINGUAL_PDF_SKILL':str(engine)},capture_output=True,text=True)
                        self.assertEqual(proc.returncode,0,proc.stderr)
                        self.assertFalse((root/'injection-marker').exists())

if __name__=='__main__':unittest.main()
