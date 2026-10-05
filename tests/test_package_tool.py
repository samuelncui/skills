"""Behavioral package checks, including frontmatter and actual Markdown-link failures."""
import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class PackageToolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'tools').mkdir()
        shutil.copyfile(ROOT/'tools/check_package.py',self.root/'tools/check_package.py')
        self.skill=self.root/'skills/bilingual-pdf'
        (self.skill/'assets').mkdir(parents=True);(self.skill/'scripts').mkdir()
        (self.skill/'assets/paralleltext.sty').write_text('')
        (self.skill/'scripts/bilingual_pdf.py').write_text('')
        (self.skill/'SKILL.md').write_text('---\nname: bilingual-pdf\ndescription: A valid isolated package.\n---\n\n# Example\n')
    def check(self):
        result=subprocess.run([sys.executable,str(self.root/'tools/check_package.py')],capture_output=True,text=True)
        return result.returncode,json.loads(result.stdout)
    def test_valid_frontmatter_passes(self):
        code,result=self.check();self.assertEqual(code,0,result);self.assertTrue(result['ok'])
    def test_mismatched_name_fails(self):
        p=self.skill/'SKILL.md';p.write_text(p.read_text().replace('name: bilingual-pdf','name: other'))
        code,result=self.check();self.assertNotEqual(code,0);self.assertTrue(any('name/description' in x for x in result['errors']))
    def test_actual_missing_local_link_fails(self):
        (self.skill/'README.md').write_text('[Missing](missing.md)\n')
        code,result=self.check();self.assertNotEqual(code,0);self.assertTrue(any('missing.md' in x for x in result['errors']))
    def test_existing_local_link_passes(self):
        (self.skill/'guide.md').write_text('# Guide\n')
        (self.skill/'README.md').write_text('[Guide](guide.md#guide)\n[Web](https://example.org/)\n')
        code,result=self.check();self.assertEqual(code,0,result)
    def test_external_sibling_link_fails(self):
        other=self.root/'skills/other';other.mkdir();(other/'SKILL.md').write_text('---\nname: other\ndescription: Other.\n---\n')
        (self.skill/'README.md').write_text('[Sibling](../other/SKILL.md)\n')
        code,result=self.check();self.assertNotEqual(code,0);self.assertTrue(any('external local link' in x for x in result['errors']))
    def test_duplicate_renderer_owner_fails(self):
        (self.skill/'examples').mkdir();(self.skill/'examples/paralleltext.sty').write_text('duplicate')
        code,result=self.check();self.assertNotEqual(code,0);self.assertTrue(any('one owner' in x for x in result['errors']))
    def test_symlink_is_not_a_self_contained_package(self):
        (self.skill/'linked.md').symlink_to(self.skill/'SKILL.md')
        code,result=self.check();self.assertNotEqual(code,0);self.assertTrue(any('symlink' in x for x in result['errors']))

if __name__=='__main__':unittest.main()
