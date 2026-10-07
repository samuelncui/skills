"""Fast ownership, invalidation and recovery checks for the public JSON build API."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
import bilingual_pdf as renderer

class IncrementalBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'source.json'
        self.out=self.root/'build'
        self.doc={'languages':['en','fr'],'title':['Guide','Guide'],'blocks':[{'id':'first','text':['A short text.','Un texte court.']}]}
        self.source.write_text(json.dumps(self.doc))

    def build(self):
        return renderer.build_document(renderer.validate(self.doc),self.source,self.out,'bilingual')

    def state(self):
        return {p.relative_to(self.out).as_posix():(p.read_bytes(),p.stat().st_mtime_ns) for p in self.out.rglob('*') if p.is_file() and p.name!=renderer.BUILD_MANIFEST}

    def figure(self):
        Image.new('RGB',(30,20),'red').save(self.root/'image.png')
        self.doc['blocks'].append({'id':'photo','kind':'figure','image':'image.png','text':['Photo','Photo']})

    def test_unchanged_build_preserves_generated_bytes_and_mtimes(self):
        self.build();before=self.state();result=self.build()
        self.assertEqual(result['changed_files'],[])
        self.assertEqual(self.state(),before)

    def test_content_edit_only_rewrites_content(self):
        self.build();before=self.state();self.doc['blocks'][0]['text'][0]='An edited sentence.'
        self.assertEqual(self.build()['changed_files'],['content.tex'])
        self.assertIn('An edited sentence.',(self.out/'content.tex').read_text())
        for name,value in before.items():
            if name!='content.tex':self.assertEqual(self.state()[name],value)

    def test_config_and_language_edits_rewrite_dependencies(self):
        self.build();self.doc['layout']={'margin_mm':19}
        self.assertIn('languages.tex',self.build()['changed_files'])
        self.doc['languages']=['en','he']
        self.assertIn('languages.tex',self.build()['changed_files'])

    def test_same_filename_asset_change_is_detected(self):
        self.figure();self.build();before=(self.out/'figure-photo/image.png').read_bytes()
        Image.new('RGB',(30,20),'blue').save(self.root/'image.png')
        self.assertEqual(self.build()['changed_files'],['figure-photo/image.png'])
        self.assertNotEqual((self.out/'figure-photo/image.png').read_bytes(),before)

    def test_removed_asset_removed_but_unrelated_file_preserved(self):
        self.figure();self.build();(self.out/'notes.txt').write_text('Keep this note')
        self.doc['blocks'].pop();self.build()
        self.assertFalse((self.out/'figure-photo/image.png').exists())
        self.assertEqual((self.out/'notes.txt').read_text(),'Keep this note')

    def test_missing_generated_file_is_recreated(self):
        self.build();(self.out/'content.tex').unlink()
        self.assertEqual(self.build()['changed_files'],['content.tex'])

    def test_native_project_and_existing_empty_directory_are_rejected(self):
        for populated in (False,True):
            with self.subTest(populated=populated):
                self.out.mkdir(exist_ok=True)
                if populated:(self.out/'content.tex').write_text('My manuscript')
                with self.assertRaisesRegex(renderer.InputError,'previously created by build'):self.build()
        self.assertEqual((self.out/'content.tex').read_text(),'My manuscript')

    def test_native_edit_is_preserved_and_rejected(self):
        self.build();(self.out/'content.tex').write_text('My manual edit')
        before=self.state()
        with self.assertRaisesRegex(renderer.InputError,'edited outside build'):self.build()
        self.assertEqual(self.state(),before)

    def test_new_asset_collision_is_preserved(self):
        self.build();self.figure();(self.out/'figure-photo').mkdir();(self.out/'figure-photo/image.png').write_bytes(b'User asset')
        before=self.state()
        with self.assertRaisesRegex(renderer.InputError,'Unmanaged file'):self.build()
        self.assertEqual(self.state(),before)

    def test_symlinked_managed_paths_and_build_outputs_are_rejected(self):
        self.build()
        for name in ('content.tex','document.pdf','figure-photo'):
            with self.subTest(name=name):
                path=self.out/name
                old=path.read_bytes() if path.is_file() else None
                if path.exists():path.unlink()
                outside=self.root/('outside-'+name.replace('/','-'))
                if name=='figure-photo':outside.mkdir();self.figure()
                else:outside.write_bytes(b'Untouched')
                path.symlink_to(outside)
                with self.assertRaisesRegex(renderer.InputError,'Symlink'):self.build()
                if outside.is_file():self.assertEqual(outside.read_bytes(),b'Untouched')
                path.unlink()
                if old is not None:path.write_bytes(old)

    def test_failed_first_staging_can_retry_same_directory(self):
        self.figure();(self.root/'image.png').write_text('invalid image bytes')
        with self.assertRaises(OSError):self.build()
        self.assertTrue((self.out/renderer.BUILD_MANIFEST).exists())
        Image.new('RGB',(30,20),'blue').save(self.root/'image.png')
        self.build();self.assertTrue((self.out/'figure-photo/image.png').is_file())

    def test_failed_update_invalidates_success_before_replacing_sources(self):
        self.build();(self.out/'result.json').write_text('{"ok":true}')
        self.doc['blocks'][0]['text'][0]='A changed sentence.'
        original=Path.replace
        def fail_content(path,target):
            if Path(target)==self.out/'content.tex':raise OSError('Interrupted content replacement')
            return original(path,target)
        with patch.object(Path,'replace',fail_content):
            with self.assertRaisesRegex(OSError,'Interrupted content'):
                renderer.build_document(self.doc,self.source,self.out,'bilingual',environment={'ok':True})
        self.assertFalse(json.loads((self.out/'result.json').read_text())['ok'])
        self.build();self.assertIn('A changed sentence.',(self.out/'content.tex').read_text())

    def test_failed_staging_preserves_existing_project(self):
        self.build();before=self.state();self.figure();(self.root/'image.png').write_text('invalid image bytes')
        with self.assertRaises(OSError):self.build()
        self.assertEqual(self.state(),before)

    def test_ownership_receipt_rejects_arbitrary_paths(self):
        self.build();outside=self.root/'outside';outside.write_text('Untouched')
        (self.out/renderer.BUILD_MANIFEST).write_text(json.dumps({'format':1,'files':{'../outside':hashlib.sha256(b'Untouched').hexdigest()}}))
        with self.assertRaisesRegex(renderer.InputError,'Invalid build ownership'):self.build()
        self.assertEqual(outside.read_text(),'Untouched')

    def test_existing_lock_is_not_removed(self):
        self.build();lock=self.out/renderer.BUILD_LOCK;lock.write_text('Other build')
        with self.assertRaisesRegex(renderer.InputError,'lock exists'):self.build()
        self.assertEqual(lock.read_text(),'Other build')

    def test_pending_update_recovers_only_recorded_bytes(self):
        self.build();manifest=self.out/renderer.BUILD_MANIFEST;state=json.loads(manifest.read_text())
        changed=b'A partially applied generated content file'
        state['pending']={'content.tex':hashlib.sha256(changed).hexdigest()}
        manifest.write_text(json.dumps(state));(self.out/'content.tex').write_bytes(changed)
        self.build();self.assertNotIn('pending',json.loads(manifest.read_text()))
        self.assertIn('A short text.',(self.out/'content.tex').read_text())

    def test_package_change_is_not_stale(self):
        self.build();installed=self.root/'installed';(installed/'assets').mkdir(parents=True)
        for name in ('assets/paralleltext.sty','LICENSE'):(installed/name).write_bytes((renderer.ROOT/name).read_bytes())
        with (installed/'assets/paralleltext.sty').open('a') as f:f.write('\n% New installed revision\n')
        with patch.object(renderer,'ROOT',installed):self.assertEqual(self.build()['changed_files'],['paralleltext.sty'])

    def test_cli_holds_lock_through_compilation_and_qa(self):
        def compile_under_lock(*args,**kwargs):
            self.assertTrue((self.out/renderer.BUILD_LOCK).exists())
            with self.assertRaisesRegex(renderer.InputError,'lock exists'):self.build()
            return {'ok':True}
        with patch.object(sys,'argv',['bilingual_pdf.py','build',str(self.source),'--output',str(self.out)]),patch.object(renderer,'preflight',return_value={'ok':True}),patch.object(renderer,'compile_project',side_effect=compile_under_lock):
            self.assertEqual(renderer.main(),0)
        self.assertFalse((self.out/renderer.BUILD_LOCK).exists())

    def test_source_only_update_invalidates_earlier_qa_on_change(self):
        self.build();(self.out/'result.json').write_text('{"ok":true}')
        self.doc['blocks'][0]['text'][0]='Another source revision.';self.build()
        self.assertFalse(json.loads((self.out/'result.json').read_text())['ok'])

    def test_failed_compile_invalidates_previous_success_receipt(self):
        self.build();(self.out/'result.json').write_text('{"ok":true}')
        (self.out/'document.pdf').write_bytes(b'previous PDF')
        with patch.object(sys,'argv',['bilingual_pdf.py','build',str(self.source),'--output',str(self.out)]),patch.object(renderer,'preflight',return_value={'ok':True}),patch.object(renderer,'compile_project',side_effect=RuntimeError('Compile failed')):
            self.assertEqual(renderer.main(),3)
        result=json.loads((self.out/'result.json').read_text())
        self.assertFalse(result['ok']);self.assertEqual(result['error'],'Compile failed')
        self.assertEqual((self.out/'document.pdf').read_bytes(),b'previous PDF')
        self.assertFalse((self.out/renderer.BUILD_LOCK).exists())

    def test_cli_build_keeps_validation_preflight_and_qa(self):
        with patch.object(sys,'argv',['bilingual_pdf.py','build',str(self.source),'--output',str(self.out)]),patch.object(renderer,'preflight',return_value={'ok':True}) as preflight,patch.object(renderer,'compile_project',return_value={'ok':True}) as compile_project:
            self.assertEqual(renderer.main(),0)
        preflight.assert_called_once();compile_project.assert_called_once()
        self.assertTrue((self.out/renderer.BUILD_MANIFEST).exists())

if __name__=='__main__':unittest.main()
