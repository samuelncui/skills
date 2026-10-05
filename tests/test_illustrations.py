"""Original diagram export crops ink without losing native labels."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("export_illustrations",ROOT/"tools/export_illustrations.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class IllustrationTests(unittest.TestCase):
    def fixture(self,path,pages=7,empty=False):
        with pymupdf.open() as pdf:
            for index in range(pages):
                page=pdf.new_page(width=400,height=300)
                if not empty:
                    page.draw_rect((80,80,320,170),color=(0,0,0))
                    page.insert_text((100,120),"Label "+str(index))
            pdf.save(path)
    def test_cropped_assets_have_every_expected_name_and_visible_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root/"source.pdf")
            records=module.export(root/"source.pdf",root/"images")
            self.assertEqual([x["file"] for x in records],[x+".png" for x in module.NAMES])
            for item in records:
                self.assertLess(item["width"],1000)
                self.assertLess(item["height"],750)
                pix=pymupdf.Pixmap(root/"images"/item["file"])
                self.assertGreater(pix.width,500)
                self.assertLess(min(pix.samples),50)
    def test_incomplete_and_empty_inputs_fail_before_creating_outputs(self):
        for pages,empty in ((6,False),(7,True)):
            with self.subTest(pages=pages,empty=empty),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);self.fixture(root/"source.pdf",pages,empty)
                with self.assertRaises(ValueError):module.export(root/"source.pdf",root/"images")
                self.assertFalse((root/"images").exists())

if __name__=="__main__":
    unittest.main()
