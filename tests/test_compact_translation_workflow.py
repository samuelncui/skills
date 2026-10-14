"""Public JSONL protocol regressions; fixture attestations are not semantic review.

Preparation parsing/splitting lives in test_translation_preparation; patch,
todo and atomic batch contract cases live in test_translation_actions.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/bilingual-translation/scripts/workflow.py"
SPEC = importlib.util.spec_from_file_location("compact_workflow", SCRIPT)
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)
C = W.core


class CompactWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.md"
        self.master = self.root / "master.jsonl"

    def act(self, op, **fields):
        return W.execute(self.master, [{"op": op, **fields}])[0]

    def prepare(self, text="First.\n\nSecond.", **fields):
        self.source.write_bytes(text.encode())
        return self.act("prepare init", source=str(self.source), **fields)

    def save_action(self, block, value="Translated."):
        return {"op": "translate save", "ref": block["ref"],
                "targets": {u["id"]: value for u in block["units"]}}

    def translate(self):
        while True:
            block = self.act("translate next")
            if block.get("complete"):
                return
            W.execute(self.master, [self.save_action(block)])

    def finish(self):
        while True:
            block = self.act("review next")
            if block.get("complete"):
                return
            self.act("review accept", ref=block["ref"])

    def cli(self, *args, action=None, raw=None, master=None, script=SCRIPT, cwd=None, check=True):
        command = [sys.executable, "-B", str(script)]
        if master is not False:
            command += ["--master", str(master or self.master)]
        command += list(map(str, args))
        result = subprocess.run(command, input=raw if raw is not None else (
            json.dumps(action) + "\n" if action is not None else ""),
            capture_output=True, text=True, timeout=15, cwd=cwd)
        if not check:
            return result
        self.assertEqual(result.returncode, 0, result.stderr)
        records = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertTrue(records)
        self.assertEqual(records[-1]["record_type"], "receipt")
        return records

    @staticmethod
    def block(records):
        return {**records[-1], "units": [v for v in records if v["record_type"] == "unit"]}

    def test_structural_groups_and_source_cap_in_both_phases(self):
        self.prepare("# Heading\n\nOne.\n\nTwo.\n\n- First\n- Second\n\n"
                     "| Key | Value |\n| --- | --- |\n| A | B |\n\n## Next\n\n"
                     + "中" * 1024 + "\n\n" + "文" * 1024 + "\n\nLast.")
        expected = [1, 2, 2, 4, 1, 2, 1]
        for phase in ("translate", "review"):
            groups = []
            while True:
                block = self.block(self.cli(phase, "next"))
                if block.get("complete"):
                    break
                groups.append(len(block["units"]))
                self.assertLessEqual(sum(len(u["source"]) for u in block["units"]), 2048)
                action = self.save_action(block) if phase == "translate" else {
                    "op": "review accept", "ref": block["ref"]}
                saved = self.cli(*action["op"].split(), action=action)
                self.assertEqual(len(saved), 1)
                self.assertNotIn("next", saved[0])
            self.assertEqual(groups, expected)
        self.act("validate", ready=True)

    def test_normal_three_source_passes_and_one_complete_target_read(self):
        prepared = self.prepare("One.\n\nTwo.", context={"summary": "Whole source"})
        sources = [u["source"] for u in prepared["units"]]
        for phase in ("translate", "review"):
            delivered = []
            # At most one group per source unit, plus the terminal receipt.
            for _ in range(len(sources) + 1):
                block = self.act(phase + " next")
                if block.get("complete"):
                    break
                delivered.extend(u["source"] for u in block["units"])
                if phase == "translate":
                    self.assertTrue(all("target" not in u for u in block["units"]))
                    receipt = W.execute(self.master, [self.save_action(block)])[0]
                else:
                    self.assertTrue(all(u["target"] == "Translated." for u in block["units"]))
                    receipt = self.act("review accept", ref=block["ref"])
                self.assertNotIn("units", receipt)
                self.assertNotIn("next", receipt)
            else:
                self.fail("phase did not reach completion")
            self.assertEqual(delivered, sources)

    def test_context_recovery_does_not_advance_active_work(self):
        context = {"summary": "Whole source background", "audience": "Readers"}
        self.prepare("# Heading\n\nOne.\n\nTwo.", context=context, source_lang="en", target_lang="fr")
        first = self.act("translate next")
        self.assertEqual(first["context"], context)
        W.execute(self.master, [self.save_action(first)])
        following = self.act("translate next")
        self.assertNotIn("context", following)
        recovered = self.act("translate next", context=True)
        self.assertEqual(recovered["ref"], following["ref"])
        self.assertEqual(recovered["units"], following["units"])
        self.assertEqual(recovered["context"], context)
        self.assertEqual(recovered["languages"], first["languages"])
        self.assertEqual(self.act("translate next")["ref"], following["ref"])

    def test_exact_ids_stale_refs_wrong_phase_and_replay(self):
        self.prepare("A.\n\nB.\n\n# Next\n\nC.")
        block = self.act("translate next")
        good = self.save_action(block)
        before = self.master.read_bytes()
        for bad in ({**good, "source": "replacement"}, {**good, "targets": {}},
                    {**good, "targets": {"wrong": "T"}}, {**good, "ref": "wrong"},
                    {**good, "targets": {u["id"]: "" for u in block["units"]}},
                    {"op": "review accept", "ref": block["ref"]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                W.execute(self.master, [bad])
            self.assertEqual(self.master.read_bytes(), before)
        receipt = W.execute(self.master, [good])
        following = self.act("translate next")
        W.execute(self.master, [self.save_action(following)])
        self.assertEqual(W.execute(self.master, [good]), receipt)
        self.assertEqual(self.act("status")["saved"], 3)
        with self.assertRaises(ValueError):
            W.execute(self.master, [self.save_action(block, "Changed retry")])

    def test_progress_small_document_replay_and_review_rollback(self):
        prepared = self.prepare()
        self.assertEqual(prepared["progress"]["percent"], 100)
        block = self.act("translate next")
        packet = self.save_action(block)
        saved = W.execute(self.master, [packet])[0]
        self.assertEqual(saved["progress"], {"phase": "translate", "completed": 2,
            "total": 2, "unit": "units", "percent": 100})
        self.assertEqual(W.execute(self.master, [packet])[0], saved)
        self.finish()
        block = self.act("review next", units=["u000001"])
        response = self.act("review patch", ref=block["ref"],
                            edits=[{"unit": "u000001", "old": "Translated", "new": "Corrected"}])
        self.assertEqual(response["progress"]["percent"], 50)
        self.assertEqual(self.act("status")["reviewed"], 1)
        reread = self.act("review next")
        accepted = self.act("review accept", ref=reread["ref"])
        self.assertEqual(accepted["progress"]["percent"], 100)
        restart = self.act("review next", units=["u000001"])
        self.assertEqual(self.act("review restart", ref=restart["ref"])["progress"]["percent"], 0)

    def test_preparation_continuation_replay_and_changed_source(self):
        text = "\n\n".join(str(i) + "x" * 1499 for i in range(7))
        first = self.prepare(text)
        self.assertEqual(first["characters"], 9000)
        before = self.master.read_bytes()
        with self.assertRaises(ValueError):
            self.act("prepare init", ref="wrong")
        self.assertEqual(self.master.read_bytes(), before)
        last = self.act("prepare init", ref=first["ref"])
        self.assertTrue(last["complete"])
        self.assertEqual(self.act("prepare init", ref=first["ref"]), last)
        self.assertEqual(self.act("prepare init", source=str(self.source)), first)
        self.source.write_text("Changed.")
        with self.assertRaises(ValueError):
            self.act("prepare init", source=str(self.source))

    def test_atomic_failure_and_post_replace_uncertainty(self):
        self.prepare("A.\n\n# Next\n\nB.")
        block = self.act("translate next")
        packet = [self.save_action(block), {"op": "translate next"}]
        before = self.master.read_bytes()
        with patch.object(C.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaises(W.ActionError):
                W.execute(self.master, packet, batch=True)
        self.assertEqual(self.master.read_bytes(), before)
        original = C.os.replace
        def replace_then_fail(*args):
            original(*args)
            raise OSError("response lost after replacement")
        with patch.object(C.os, "replace", side_effect=replace_then_fail):
            committed = W.execute(self.master, packet, batch=True)
        self.assertEqual(W.execute(self.master, packet, batch=True), committed)
        self.assertEqual(self.act("translate next")["ref"], committed[-1]["ref"])
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_real_process_crash_before_and_after_atomic_replace(self):
        self.prepare("A.\n\n# Next\n\nB.")
        block = self.act("translate next")
        packet = [self.save_action(block), {"op": "translate next"}]
        code = """import importlib.util,json,os,signal,sys
spec=importlib.util.spec_from_file_location('crash',sys.argv[1])
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
original=w.core.os.replace
def crash(*args):
    if sys.argv[3]=='after': original(*args)
    os.kill(os.getpid(),signal.SIGKILL)
w.core.os.replace=crash
w.execute(sys.argv[2],json.loads(sys.stdin.read()),batch=True)
"""
        before = self.master.read_bytes()
        for mode in ("before", "after"):
            result = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPT),
                str(self.master), mode], input=json.dumps(packet), text=True, timeout=15)
            self.assertEqual(result.returncode, -9)
            if mode == "before":
                self.assertEqual(self.master.read_bytes(), before)
        receipt = W.execute(self.master, packet, batch=True)
        self.assertEqual(self.act("translate next")["ref"], receipt[-1]["ref"])
        self.assertEqual(self.act("status")["saved"], 1)

    def test_parallel_identical_and_competing_packets(self):
        self.prepare("A.\n\n# Next\n\nB.")
        def race(packets):
            args = [sys.executable, "-B", str(SCRIPT), "--master", str(self.master), "run"]
            processes = [subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True) for _ in packets]
            try:
                for process, packet in zip(processes, packets):
                    process.stdin.write("\n".join(json.dumps(a) for a in packet) + "\n")
                    process.stdin.close()
                    process.stdin = None
                results = [p.communicate(timeout=15) for p in processes]
                return [p.returncode for p in processes], results
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
        block = self.act("translate next")
        packet = [self.save_action(block), {"op": "translate next"}]
        codes, results = race([packet, packet])
        self.assertEqual(codes, [0, 0], results)
        self.assertEqual(results[0][0], results[1][0])
        block = self.act("translate next")
        codes, results = race([[self.save_action(block, value), {"op": "translate next"}]
                              for value in ("Winner A", "Winner B")])
        self.assertEqual(sorted(codes), [0, 1], results)
        data = C.load_jsonl(self.master)
        self.assertIn(data["units"][1]["target"], ("Winner A", "Winner B"))
        self.assertEqual(self.act("status")["saved"], 2)

    def test_all_success_records_hide_machine_metadata(self):
        forbidden = {"source_hash", "target_hash", "target_source_hash", "request_hash",
                     "sha256", "revision", "document_id", "binding", "output"}
        def check(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden & value.keys())
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
        self.source.write_text("One.")
        transcript = []
        def call(op, **fields):
            records = self.cli(*op.split(), action={"op": op, **fields})
            check(records)
            transcript.extend(records)
            return self.block(records)
        call("prepare init", source=str(self.source))
        call("status"); call("validate")
        block = call("translate next")
        call("todo add", ref=block["ref"], text="Check", units=["u000001"])
        call("todo resolve", ref=block["ref"], id="todo-1")
        call("translate save", ref=block["ref"], targets={"u000001": "Translation."})
        block = call("review next", context=True)
        call("review patch", ref=block["ref"],
             edits=[{"unit": "u000001", "old": "Translation", "new": "Correction"}])
        block = call("review next")
        call("review accept", ref=block["ref"])
        block = call("review next", units=["u000001"])
        call("review restart", ref=block["ref"])
        block = call("review next"); call("review accept", ref=block["ref"])
        call("validate", ready=True); call("export", output=str(self.root / "out.json"))
        raw = json.dumps(transcript)
        self.assertNotIn(str(self.root), raw)
        for unit in C.load_jsonl(self.master)["units"]:
            self.assertNotIn(unit["source_hash"], raw)
            self.assertNotIn(unit["target_hash"], raw)

    def test_cli_errors_hide_paths_hashes_and_tracebacks(self):
        self.prepare()
        sha = C.load_jsonl(self.master)["units"][0]["source_hash"]
        cases = [
            (["status", "--" + sha], None, None),
            (["translate", "save"], '{"op":"translate save","ref":"' + sha + '","targets":{}}', None),
            (["status"], '{"' + sha + '":1,"' + sha + '":2}', None),
            (["status"], None, self.root / sha),
            (["prepare", "read"], None, None),
            (["translate", "save", "--payload", str(self.root / sha)], None, None)]
        for args, raw, master in cases:
            with self.subTest(args=args):
                result = self.cli(*args, raw=raw, master=master, check=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                for hidden in (sha, str(self.root), "Traceback", "source_hash", "target_hash"):
                    self.assertNotIn(hidden, result.stderr)
                self.assertFalse(json.loads(result.stderr)["ok"])

    def test_literal_hex_content_is_preserved(self):
        literal = "0123456789abcdef" * 4
        self.prepare("Published identifier: " + literal)
        block = self.block(self.cli("translate", "next"))
        self.assertIn(literal, block["units"][0]["source"])
        W.execute(self.master, [self.save_action(block, literal)])
        self.assertEqual(self.block(self.cli("review", "next"))["units"][0]["target"], literal)

    def test_clean_install_default_master_and_independent_directories(self):
        installation = self.root / "independent installed skill"
        shutil.copytree(SCRIPT.parents[1], installation)
        script = installation / "scripts/workflow.py"
        work = self.root / "task"
        work.mkdir()
        (work / "source.md").write_text("One.")
        def call(op, cwd=work, **fields):
            return self.block(self.cli(*op.split(), action={"op": op, **fields},
                script=script, master=False, cwd=cwd))
        call("prepare init", source="source.md")
        block = call("translate next")
        call("translate save", ref=block["ref"], targets={"u000001": "Target."})
        nested = work / "nested"; nested.mkdir()
        missing = self.cli("status", script=script, master=False, cwd=nested, check=False)
        self.assertEqual(missing.returncode, 1)
        self.assertFalse((nested / "master.jsonl").exists())
        other = self.root / "other"; other.mkdir()
        (other / "source.md").write_text("Other.")
        call("prepare init", cwd=other, source="source.md")
        self.assertEqual(call("status", cwd=other)["saved"], 0)
        self.assertEqual(call("status")["saved"], 1)
        block = call("review next")
        call("review accept", ref=block["ref"])
        call("validate", ready=True)
        call("export", output="exchange.json")
        self.assertTrue((work / "exchange.json").exists())
        self.assertFalse((other / "exchange.json").exists())


if __name__ == "__main__":
    unittest.main()
