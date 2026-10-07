"""Batched lookup preserves exact package, font, language and glyph checks."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/bilingual-pdf/scripts'))
import bilingual_pdf as renderer

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.doc={'languages':['en','fr'],'title':['Guide','Guide'],'blocks':[{'id':'start','text':['Read this.','Lire ceci.']}]}
        self.missing=set();self.calls=[];self.fallback=False;self.lookup_error=False

    def run_preflight(self):
        def run(cmd,**kwargs):
            self.calls.append(cmd)
            if cmd[0]=='kpsewhich':
                return SimpleNamespace(returncode=int(bool(self.missing) or self.lookup_error),stdout=''.join('/texmf/'+name+'\n' for name in cmd[1:] if name not in self.missing))
            if cmd[0]=='fc-match':
                return SimpleNamespace(returncode=0,stdout=('Fallback' if self.fallback else cmd[-1])+'\n/fonts/test.otf\n0\n')
            return SimpleNamespace(returncode=0,stdout='XeTeX test\n')
        with patch.object(renderer.importlib.util,'find_spec',return_value=True),patch.object(renderer.shutil,'which',return_value='/bin/tool'),patch.object(renderer.subprocess,'run',side_effect=run),patch('fontTools.ttLib.TTFont') as font:
            font.return_value.getBestCmap.return_value={**{i:'glyph' for i in range(128)},8226:'bullet'}
            return renderer.preflight(renderer.validate(self.doc))

    def test_all_required_packages_are_checked_in_one_process(self):
        result=self.run_preflight();self.assertTrue(result['ok'])
        calls=[c for c in self.calls if c[0]=='kpsewhich'];self.assertEqual(len(calls),1)
        self.assertIn('paracol.sty',calls[0]);self.assertIn('loadhyph-fr.tex',calls[0])
        self.assertEqual(len(result['fonts']),6)

    def test_partial_lookup_reports_each_missing_package(self):
        self.missing={'paracol.sty','fontspec.sty'}
        result=self.run_preflight();self.assertFalse(result['ok'])
        self.assertEqual(set(result['missing_packages']),self.missing)

    def test_lookup_failure_is_not_silently_accepted(self):
        self.lookup_error=True
        result=self.run_preflight();self.assertFalse(result['ok']);self.assertIn('package_lookup_error',result)

    def test_second_preflight_rechecks_environment(self):
        self.assertTrue(self.run_preflight()['ok']);self.missing={'polyglossia.sty'}
        self.assertFalse(self.run_preflight()['ok'])

    def test_fallback_font_is_rejected(self):
        self.fallback=True;result=self.run_preflight()
        self.assertFalse(result['ok']);self.assertTrue(all(not f['available'] for f in result['fonts']))

    def test_current_content_glyphs_are_checked_for_each_language(self):
        self.assertTrue(self.run_preflight()['ok']);self.doc['blocks'][0]['text'][1]='Lire Ω.'
        result=self.run_preflight();self.assertFalse(result['ok'])
        fr=next(f for f in result['fonts'] if f['language']=='fr');self.assertEqual(fr['missing_glyphs'],['U+03A9'])
        en=next(f for f in result['fonts'] if f['language']=='en');self.assertEqual(en['missing_glyphs'],[])

    def test_language_specific_packages_remain_required(self):
        for pair,package in [(['en','fr'],'loadhyph-fr.tex'),(['en','ar'],'bidi.sty'),(['en','he'],'bidi.sty')]:
            with self.subTest(pair=pair):
                self.doc['languages']=pair;self.missing={package};result=self.run_preflight()
                self.assertFalse(result['ok']);self.assertIn(package,result['missing_packages'])

if __name__=='__main__':unittest.main()
