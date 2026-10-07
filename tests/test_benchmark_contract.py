"""Invalid expensive benchmark combinations fail before preparing observations."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class BenchmarkArgumentsTests(unittest.TestCase):
    def test_unsupported_comparisons_fail_before_creating_work(self):
        cases=[['--compare-to','prior'],['--case','multipage-en-fr','--condition','edit'],['--condition','asset']]
        for flags in cases:
            with self.subTest(flags=flags),tempfile.TemporaryDirectory() as td:
                work=Path(td)/'must-not-exist'
                result=subprocess.run([sys.executable,str(ROOT/'tests/benchmark_bilingual.py'),'--work',str(work),*flags],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,2,result.stdout+result.stderr)
                self.assertFalse(work.exists())

if __name__=='__main__':unittest.main()
