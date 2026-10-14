"""Compact protocol tests. Fixture review attestations do not certify semantics."""
import copy
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
        self.root = Path(self.temp.name)
        self.source = self.root / "source.md"
        self.receipt = self.root / "read.json"
        self.master = self.root / "master.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self, text="First.\n\nSecond.\n", **kwargs):
        self.source.write_bytes(text.encode("utf-8"))
        page = W.read_source(self.source, self.receipt)
        delivered = page["text"]
        while not page["complete"]:
            page = W.read_source(self.source, self.receipt, page["ref"])
            delivered += page["text"]
        self.assertEqual(delivered, text)
        self.final_ref = page["ref"]
        return W.initialize(self.source, self.receipt, self.master, page["ref"], **kwargs)

    def targets(self, block, value="Translated."):
        return {"ref": block["ref"], "targets": {u["id"]: value for u in block["units"]}}

    def accept(self, block):
        return W.mutate(self.master, "accept", {"ref": block["ref"], "reviewer": "fixture", "note": ""})

    def translate(self, value="Translated."):
        block = W.next_block(self.master)
        while not block.get("complete"):
            block = W.mutate(self.master, "save", self.targets(block, value))["next"]
        return block

    def finish(self):
        block = W.next_block(self.master, "review")
        while not block.get("complete"):
            block = self.accept(block)["next"]
        C.load_jsonl(self.master, require_ready=True)

    def cli(self, *args, check=True, script=SCRIPT, cwd=None):
        result = subprocess.run([sys.executable, "-B", str(script), *map(str, args)],
                                capture_output=True, text=True, timeout=15, cwd=cwd)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        return result

    def test_full_read_final_ack_and_idempotent_init(self):
        self.source.write_text("A" * (C.READ_PAGE + 1))
        first = W.read_source(self.source, self.receipt)
        self.assertFalse(first["complete"])
        self.assertEqual(first["oversize"][0]["source_span"], [0, C.READ_PAGE + 1])
        self.assertNotIn("ref", first["oversize"][0])
        plan = {"u000001": [2048, 4096, 6144, 8192]}
        with self.assertRaisesRegex(ValueError, "complete"):
            W.initialize(self.source, self.receipt, self.master, first["ref"], splits=plan)
        last = W.read_source(self.source, self.receipt, first["ref"])
        self.assertEqual(W.read_source(self.source, self.receipt, first["ref"]), last)
        self.assertNotIn("oversize", last)
        with self.assertRaises(ValueError):
            W.initialize(self.source, self.receipt, self.master, "wrong", splits=plan)
        with self.assertRaisesRegex(ValueError, "split plan"):
            W.initialize(self.source, self.receipt, self.master, last["ref"])
        self.assertFalse(self.master.exists())
        initialized = W.initialize(self.source, self.receipt, self.master, last["ref"], splits=plan)
        self.assertEqual(initialized, {"initialized": True, "units": 5, "oversize": []})
        self.assertEqual(W.initialize(self.source, self.receipt, self.master, last["ref"], splits=plan), initialized)
        with self.assertRaisesRegex(ValueError, "different initialization"):
            W.initialize(self.source, self.receipt, self.master, last["ref"], target_lang="de", splits=plan)
        self.source.write_text("Changed.")
        with self.assertRaises(ValueError):
            W.initialize(self.source, self.receipt, self.master, last["ref"], splits=plan)

    def test_aggregate_boundaries_sticky_restart_and_shared_recovery(self):
        self.prepare("# Heading\n\nOne.\n\nTwo.\n\n## Next\n\nThree.",
                     context={"summary": "S" * 1500})
        heading = W.next_block(self.master)
        self.assertEqual(len(heading["units"]), 1)
        self.assertEqual(heading["units"][0]["level"], 1)
        self.assertEqual(len(heading["shared"]["summary"]), 1500)
        self.assertEqual(self.cli("translate", "next", self.master), heading)
        self.assertEqual(W.next_block(self.master), heading)
        following = W.mutate(self.master, "save", self.targets(heading))["next"]
        self.assertEqual([u["source"] for u in following["units"]], ["One.", "Two."])
        self.assertNotIn("shared", following)
        self.assertNotIn("languages", following)
        self.assertNotIn("context", following)
        restored = W.next_block(self.master, include_context=True)
        self.assertEqual(restored["ref"], following["ref"])
        self.assertEqual(restored["shared"], heading["shared"])
        self.assertIn("Heading", restored["context"]["text"])
        self.assertLessEqual(len(restored["context"]["text"]), 1024)
        self.assertEqual(W.status(self.master, True)["shared"], heading["shared"])
        after = W.mutate(self.master, "save", self.targets(following))["next"]
        self.assertEqual([u["source"] for u in after["units"]], ["Next"])

    def test_cap_unicode_semantic_split_and_source_integrity(self):
        parts = ["😀" * 1000 + ".  ", "e\u0301" * 600 + ".\r\n", "尾" * 500 + "."]
        source = "\ufeff# 标题\r\n\r\n" + "".join(parts) + "\r\n"
        offsets = [len(parts[0]), len(parts[0]) + len(parts[1])]
        initial = self.prepare(source, splits={"u000002": offsets})
        self.assertEqual(initial["oversize"], [])
        self.assertEqual([u["source"] for u in C.load_jsonl(self.master)["units"][1:]], parts)
        block = W.next_block(self.master)
        while not block.get("complete"):
            self.assertLessEqual(sum(len(u["source"]) for u in block["units"]), 2048)
            block = W.mutate(self.master, "save", self.targets(block))["next"]
        data = C.load_jsonl(self.master)
        self.assertEqual(data["document"]["source"]["sha256"], C.digest(source))
        self.finish()

    def test_exact_2048_and_adjacent_units_do_not_exceed_cap(self):
        self.prepare("中" * 1024 + "\n\n" + "文" * 1024 + "\n\nLast.")
        block = W.next_block(self.master)
        self.assertEqual(len(block["units"]), 2)
        self.assertEqual(sum(len(u["source"]) for u in block["units"]), 2048)
        following = W.mutate(self.master, "save", self.targets(block))["next"]
        self.assertEqual([u["source"] for u in following["units"]], ["Last."])

    def test_table_list_structure_survives_batching_and_context(self):
        self.prepare("# 标题\n\n- One\n- Two\n\n| 名称 | 数量 |\n| --- | --- |\n| 苹果 | 二 |\n")
        block = W.next_block(self.master)
        block = W.mutate(self.master, "save", self.targets(block))["next"]
        self.assertEqual([u["list"]["item"] for u in block["units"]], [0, 1])
        block = W.mutate(self.master, "save", self.targets(block))["next"]
        self.assertEqual([(u["table"]["row"], u["table"]["column"]) for u in block["units"]],
                         [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertNotIn("context", block)
        recovered = W.next_block(self.master, include_context=True)
        self.assertIn("名称", recovered["context"]["text"])
        self.assertEqual(W.status(self.master, True)["context"], recovered["context"])
        self.assertEqual(len({u["id"] for u in block["units"]}), 4)

    def test_save_exact_ids_invalid_payload_and_stable_replay(self):
        self.prepare("A.\n\nB.\n\n# Next\n\nC.")
        block = W.next_block(self.master)
        good = self.targets(block)
        before = self.master.read_bytes()
        for bad in (dict(good, source="replacement"), dict(good, targets={}),
                    dict(good, targets={"u999999": "wrong"}), dict(good, ref="wrong"),
                    dict(good, targets={u["id"]: "" for u in block["units"]})):
            with self.subTest(payload=bad), self.assertRaises(ValueError):
                W.mutate(self.master, "save", bad)
            self.assertEqual(self.master.read_bytes(), before)
        receipt = W.mutate(self.master, "save", good)
        self.assertEqual(W.mutate(self.master, "save", good), receipt)
        later = W.mutate(self.master, "save", self.targets(receipt["next"]))
        self.assertEqual(W.mutate(self.master, "save", good), receipt)
        self.assertEqual(W.next_block(self.master), later["next"])
        with self.assertRaisesRegex(ValueError, "reused"):
            W.mutate(self.master, "save", self.targets(block, "Different."))

    def test_task_local_numbers_phase_stale_and_legacy_writer_guards(self):
        self.prepare()
        block = W.next_block(self.master)
        with self.assertRaises(ValueError):
            self.accept(block)
        with self.assertRaisesRegex(ValueError, "compact block"):
            C.next_block(self.master)
        other = self.root / "other.jsonl"
        W.initialize(self.source, self.receipt, other, self.final_ref)
        other_block = W.next_block(other)
        # Numbers are task-local; no cross-document identity guarantee is claimed.
        self.assertEqual(C.reference_number(other_block["ref"]), C.reference_number(block["ref"]))
        other_before = other.read_bytes()
        with self.assertRaisesRegex(ValueError, "active translate"):
            W.next_block(self.master, "review")
        W.mutate(self.master, "save", self.targets(block))
        self.assertEqual(other.read_bytes(), other_before)
        review = W.next_block(self.master, "review")
        self.assertGreater(C.reference_number(review["ref"]), C.reference_number(block["ref"]))
        with self.assertRaisesRegex(ValueError, "wrong phase"):
            W.mutate(self.master, "save", self.targets(review))
        accepted = self.accept(review)
        selected = W.next_block(self.master, "review", unit_id="u000001")
        revised = W.mutate(self.master, "revise", self.targets(selected, "Correction."))
        self.assertGreater(C.reference_number(revised["next"]["ref"]), C.reference_number(selected["ref"]))
        with self.assertRaisesRegex(ValueError, "reused"):
            W.mutate(self.master, "revise", self.targets(review, "Bad stale correction."))
        self.assertEqual(self.accept(review), accepted)

    def test_separate_review_subset_revision_and_ready_gate(self):
        self.prepare()
        self.translate()
        with self.assertRaisesRegex(ValueError, "reviewed"):
            C.load_jsonl(self.master, require_ready=True)
        review = W.next_block(self.master, "review")
        accepted = self.accept(review)
        self.assertTrue(accepted["next"]["complete"])
        self.assertEqual(self.accept(review), accepted)
        C.load_jsonl(self.master, require_ready=True)
        selected = W.next_block(self.master, "review", unit_id="u000001")
        with self.assertRaisesRegex(ValueError, "not ready"):
            C.load_jsonl(self.master, require_ready=True)
        revised = W.mutate(self.master, "revise",
                           {"ref": selected["ref"], "targets": {"u000001": "Corrected."}})
        data = C.load_jsonl(self.master)
        self.assertEqual([u["status"] for u in data["units"]], ["draft", "reviewed"])
        self.assertEqual(revised["next"]["units"][0]["target"], "Corrected.")
        self.assertNotEqual(revised["next"]["ref"], selected["ref"])
        self.assertEqual(W.mutate(self.master, "revise",
                          {"ref": selected["ref"], "targets": {"u000001": "Corrected."}}), revised)
        self.accept(revised["next"])
        C.load_jsonl(self.master, require_ready=True)

    def test_review_target_budget_and_lossless_large_target_pages(self):
        self.prepare("A.\n\nB.\n\nC.")
        self.translate("T" * 4000)
        block = W.next_block(self.master, "review")
        self.assertEqual(len(block["units"]), 2)
        self.assertEqual(sum(len(u["target"]) for u in block["units"]), 8000)
        block = self.accept(block)["next"]
        self.assertEqual(len(block["units"]), 1)
        self.accept(block)
        selected = W.next_block(self.master, "review", unit_id="u000001")
        target = "译" * (W.MAX_TARGET * 2 + 7)
        response = W.mutate(self.master, "revise", {"ref": selected["ref"], "targets": {"u000001": target}})
        page = response["next"]
        self.assertNotIn("ref", page)
        hidden_ref = W._active(W._load(self.master))["ref"]
        with self.assertRaisesRegex(ValueError, "every review page"):
            self.accept({"ref": hidden_ref})
        seen = ""
        while True:
            self.assertLessEqual(len(page["units"][0]["target"]), W.MAX_TARGET)
            seen += page["units"][0]["target"]
            if page["target_page"]["complete"]:
                break
            continuation = page["continue"]
            page = W.next_block(self.master, "review", continuation=continuation)
            self.assertEqual(W.next_block(self.master, "review", continuation=continuation), page)
        self.assertEqual(seen, target)
        self.accept(page)
        C.load_jsonl(self.master, require_ready=True)

    def test_multigroup_revision_growth_rebudgets_and_restart_recovers_pages(self):
        self.prepare()
        self.translate()
        block = W.next_block(self.master, "review")
        target = "x" * 17000
        response = W.mutate(self.master, "revise", {
            "ref": block["ref"], "targets": {"u000001": target}})
        page = response["next"]
        self.assertEqual(len(page["units"]), 1)
        self.assertNotIn("ref", page)
        first_page = copy.deepcopy(page)
        page = W.next_block(self.master, "review", continuation=page["continue"])
        self.assertEqual(page["target_page"]["start"], W.MAX_TARGET)
        page = W.next_block(self.master, "review", restart=True, include_context=True)
        self.assertEqual(page["target_page"]["start"], 0)
        self.assertEqual(page["units"], first_page["units"])
        self.assertIn("languages", page)
        self.assertNotIn("ref", page)
        before = self.master.read_bytes()
        with self.assertRaises(ValueError):
            W.next_block(self.master, "review", restart=True, continuation=page["continue"])
        self.assertEqual(self.master.read_bytes(), before)
        while "continue" in page:
            page = W.next_block(self.master, "review", continuation=page["continue"])
        following = self.accept(page)["next"]
        self.assertEqual([u["id"] for u in following["units"]], ["u000002"])
        self.accept(following)
        C.load_jsonl(self.master, require_ready=True)

    def test_revision_combined_target_growth_rebudgets_without_truncation(self):
        self.prepare()
        self.translate()
        block = W.next_block(self.master, "review")
        response = W.mutate(self.master, "revise", self.targets(block, "T" * 5000))
        block = response["next"]
        self.assertEqual(len(block["units"]), 1)
        self.assertEqual(len(block["units"][0]["target"]), 5000)
        self.assertNotIn("target_page", block)
        following = self.accept(block)["next"]
        self.assertEqual([u["id"] for u in following["units"]], ["u000002"])
        self.assertEqual(len(following["units"][0]["target"]), 5000)
        self.accept(following)
        C.load_jsonl(self.master, require_ready=True)

    def test_operation_journal_validation_rejects_malformed_reserved_state(self):
        self.prepare()
        W.next_block(self.master)
        data = C.load_jsonl(self.master)
        cases = []
        for record in (None, {}, {"request_hash": "bad", "receipt": {}}):
            bad = copy.deepcopy(data)
            bad["document"]["workflow"]["operations"]["_compact_active"] = record
            cases.append(bad)
        bad = copy.deepcopy(data)
        bad["document"]["workflow"]["operations"]["_compact_seen"]["receipt"]["phases"] = ["bogus"]
        cases.append(bad)
        bad = copy.deepcopy(data)
        active = bad["document"]["workflow"]["operations"]["_compact_active"]
        active["receipt"]["binding"] = "0" * 64
        active["request_hash"] = C.digest(C._canonical(active["receipt"]))
        cases.append(bad)
        for bad in cases:
            with self.subTest(data=bad), self.assertRaises(ValueError):
                C.validate(bad)
            self.master.write_text("\n".join(C._canonical(value)
                                   for value in [bad["document"]] + bad["units"]) + "\n")
            with self.assertRaises(ValueError):
                W.status(self.master)
            with self.assertRaises(ValueError):
                W.next_block(self.master)

    def test_atomic_failure_and_post_replace_uncertainty(self):
        self.prepare("A.\n\n# Next\n\nB.")
        block = W.next_block(self.master)
        before = self.master.read_bytes()
        with patch.object(C.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                W.mutate(self.master, "save", self.targets(block))
        self.assertEqual(self.master.read_bytes(), before)
        self.assertEqual(W.next_block(self.master), block)
        replace = C.os.replace
        def replace_then_fail(*args):
            replace(*args)
            raise OSError("response lost after replacement")
        with patch.object(C.os, "replace", side_effect=replace_then_fail):
            with self.assertRaises(OSError):
                W.mutate(self.master, "save", self.targets(block))
        retried = W.mutate(self.master, "save", self.targets(block))
        self.assertEqual(W.next_block(self.master), retried["next"])
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_real_process_crash_before_and_after_atomic_replace(self):
        self.prepare("A.\n\n# Next\n\nB.")
        block = W.next_block(self.master)
        payload = self.root / "payload.json"
        payload.write_text(json.dumps(self.targets(block)))
        code = """import importlib.util,json,os,signal,sys
spec=importlib.util.spec_from_file_location('crash',sys.argv[1])
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
original=w.core.os.replace
def crash(*args):
    if sys.argv[4]=='after': original(*args)
    os.kill(os.getpid(),signal.SIGKILL)
w.core.os.replace=crash
w.mutate(sys.argv[2],'save',json.load(open(sys.argv[3])))
"""
        before = self.master.read_bytes()
        for mode in ("before", "after"):
            result = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPT),
                                     str(self.master), str(payload), mode], timeout=15)
            self.assertEqual(result.returncode, -9)
            if mode == "before":
                self.assertEqual(self.master.read_bytes(), before)
                self.assertEqual(W.next_block(self.master), block)
        receipt = W.mutate(self.master, "save", self.targets(block))
        self.assertEqual(W.next_block(self.master), receipt["next"])

    def test_parallel_same_payload_and_competing_payloads(self):
        self.prepare("A.\n\n# Next\n\nB.")
        block = W.next_block(self.master)
        payload = self.root / "payload.json"
        payload.write_text(json.dumps(self.targets(block)))
        args = [sys.executable, "-B", str(SCRIPT), "translate", "save", str(self.master), "--payload", str(payload)]
        processes = [subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        results = [p.communicate(timeout=15) for p in processes]
        self.assertEqual([p.returncode for p in processes], [0, 0], results)
        self.assertEqual(results[0][0], results[1][0])
        block = json.loads(results[0][0])["next"]
        files = []
        for index in range(2):
            file = self.root / ("compete" + str(index) + ".json")
            file.write_text(json.dumps(self.targets(block, "Different " + str(index))))
            files.append(file)
        processes = [subprocess.Popen([sys.executable, "-B", str(SCRIPT), "translate", "save",
                     str(self.master), "--payload", str(file)], stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True) for file in files]
        results = [p.communicate(timeout=15) for p in processes]
        self.assertEqual(sorted(p.returncode for p in processes), [0, 1], results)
        self.assertEqual(W.status(self.master)["saved"], 2)

    def test_numbered_refs_reject_guessed_words_and_malformed_values(self):
        self.prepare()
        block = W.next_block(self.master)
        before = self.master.read_bytes()
        number, word = block["ref"].split("-")
        wrong_word = next(candidate for candidate in C.REF_WORDS if candidate != word)
        invalid = [number, int(number), True, None, "0-maple", "01-maple",
                   "-1-maple", "1.0-maple", "1e1-maple", "１-maple",
                   number + "-unknownword", number + "-Maple", number + "-maple ",
                   "1" * 30 + "-maple", number + "-" + wrong_word]
        for value in invalid:
            with self.subTest(ref=value), self.assertRaises(ValueError):
                W.mutate(self.master, "save", dict(self.targets(block), ref=value))
            self.assertEqual(self.master.read_bytes(), before)
        self.assertEqual(W.next_block(self.master), block)
        self.assertEqual(len(C.REF_WORDS), len(set(C.REF_WORDS)))

    def test_old_preread_token_is_rejected_without_echo(self):
        self.source.write_text("Source.")
        C.read_source(self.source, self.receipt)
        state = C._json(self.receipt.read_text())
        sha = state["source_hash"]
        state["token"] = sha
        state["page"]["token"] = sha
        self.receipt.write_text(C._canonical(state))
        result = self.cli("prepare", "read", self.source, "--receipt", self.receipt, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(sha, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_all_compact_cli_success_branches_exclude_machine_hash_metadata(self):
        import re
        forbidden = {"source_hash", "source_hashes", "target_hash", "target_source_hash",
                     "request_hash", "sha256", "revision", "document_id", "block_id"}
        transcript = []
        def check(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden & value.keys())
                for key, child in value.items():
                    if key in ("ref", "continue"):
                        self.assertRegex(child, r"^[1-9][0-9]*-[a-z]+$")
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
        def call(*args):
            result = self.cli(*args)
            check(result)
            transcript.append(json.dumps(result))
            return result
        def save_payload(block, action, target="Translation."):
            payload = self.targets(block, target)
            check(payload)
            transcript.append(json.dumps(payload))
            file = self.root / "payload.json"
            file.write_text(json.dumps(payload))
            return call("translate" if action == "save" else "review", action,
                        self.master, "--payload", file)
        self.source.write_text("Sentence. " * 220 + "\n\nSecond.")
        page = call("prepare", "read", self.source, "--receipt", self.receipt)
        splits = self.root / "splits.json"
        splits.write_text(json.dumps({"u000001": [1100]}))
        initialized = call("prepare", "init", self.source, "--receipt", self.receipt,
                           "--read-ref", page["ref"], "--output", self.master,
                           "--source-lang", "en", "--target-lang", "fr", "--splits", splits)
        self.assertEqual(set(initialized), {"initialized", "units", "oversize"})
        call("status", self.master)
        call("status", self.master, "--context")
        call("validate", self.master)
        block = call("translate", "next", self.master, "--context")
        while not block.get("complete"):
            for unit in block["units"]:
                if ".part" in unit["id"]:
                    self.assertTrue({"parent_id", "part_index", "has_more"} <= unit.keys())
                else:
                    self.assertFalse({"parent_id", "part_index", "has_more"} & unit.keys())
            response = save_payload(block, "save")
            self.assertEqual(set(response), {"saved", "next"})
            block = response["next"]
        block = call("review", "next", self.master, "--context")
        block = save_payload(block, "revise", "Corrected.")["next"]
        while not block.get("complete"):
            block = call("review", "accept", self.master, "--ref", block["ref"])["next"]
        call("validate", self.master, "--ready")
        call("export", self.master, "--output", self.root / "legacy.json")
        raw = "\n".join(transcript)
        self.assertIsNone(re.search(r"[a-f0-9]{32,}", raw))
        for unit in C.load_jsonl(self.master)["units"]:
            self.assertNotIn(unit["source_hash"], raw)
            self.assertNotIn(unit["target_hash"], raw)

    def test_cli_errors_never_echo_hash_values_or_internal_hash_keys(self):
        self.prepare()
        state = C.load_jsonl(self.master)
        sha = state["units"][0]["source_hash"]
        payload = self.root / "bad.json"
        payload.write_text('{"' + sha + '":1,"' + sha + '":2}')
        empty_receipt = self.root / "empty.json"
        empty_receipt.write_text("{}")
        cases = [
            ("prepare", "split", self.master, "--ref", "rWrong", "--offsets", sha),
            ("translate", "save", self.master, "--payload", payload),
            ("prepare", "init", self.source, "--receipt", empty_receipt, "--read-ref", "pWrong",
             "--output", self.root / "other.jsonl", "--source-lang", "en", "--target-lang", "fr"),
            ("status", self.master, "--" + sha),
            ("status", self.root / sha),
            ("prepare", "read", self.source, "--receipt", self.receipt, "--continue", sha),
        ]
        for args in cases:
            with self.subTest(args=args):
                result = self.cli(*args, check=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertNotIn(sha, result.stderr)
                self.assertNotIn("source_hash", result.stderr)
                self.assertNotIn("target_hash", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(set(json.loads(result.stderr)), {"error"})
                self.assertLess(len(result.stderr), 220)

    def test_literal_hex_in_user_content_is_preserved(self):
        literal = "0123456789abcdef" * 4
        self.prepare("The published identifier is " + literal + ".")
        block = self.cli("translate", "next", self.master)
        self.assertIn(literal, block["units"][0]["source"])
        W.mutate(self.master, "save", self.targets(block, "Identifier: " + literal))
        review = self.cli("review", "next", self.master)
        self.assertIn(literal, review["units"][0]["target"])

    def test_normal_three_source_passes_one_target_read_and_global_context(self):
        context = {"summary": "Distinguish opening balance from movement; retain the ledger concept.",
                   "audience": "new volunteers", "glossary": [
                       {"source": "ledger", "target": "账簿", "note": "Use consistently throughout."}]}
        parts = ["The opening balance is preserved. " * 40, "Each movement is recorded once. " * 40]
        text = "# Ledger guidance\n\n" + "".join(parts) + "\n\n| Entry | Count |\n| --- | --- |\n| Initial | Seven |\n"
        self.source.write_bytes(text.encode("utf-8"))
        page = W.read_source(self.source, self.receipt)
        self.assertTrue(page["complete"])
        self.assertEqual(page["text"], text)  # source delivery pass 1
        plan = {page["oversize"][0]["id"]: [len(parts[0])]}
        prepared = W.initialize(self.source, self.receipt, self.master, page["ref"],
                                context=context, splits=plan)
        self.assertEqual(prepared["oversize"], [])
        expected = [(u["id"], u["source"]) for u in C.load_jsonl(self.master)["units"]]
        seen_translation, authored_targets = [], {}
        block = W.next_block(self.master)
        self.assertEqual(block["shared"], context)
        shared_count = 0
        while not block.get("complete"):
            shared_count += "shared" in block
            self.assertNotIn("context", block)
            seen_translation.extend((u["id"], u["source"]) for u in block["units"])
            self.assertTrue(all("target" not in u for u in block["units"]))
            targets = {u["id"]: "译文 " + u["id"] for u in block["units"]}
            self.assertFalse(authored_targets.keys() & targets.keys())
            authored_targets.update(targets)  # target authored once per unit
            block = W.mutate(self.master, "save", {"ref": block["ref"], "targets": targets})["next"]
        self.assertEqual(shared_count, 1)
        self.assertEqual(seen_translation, expected)  # source delivery pass 2
        reviewed_sources, reviewed_targets = [], []
        block = W.next_block(self.master, "review")
        self.assertEqual(block["shared"], context)
        shared_count = 0
        while not block.get("complete"):
            shared_count += "shared" in block
            self.assertNotIn("context", block)
            reviewed_sources.extend((u["id"], u["source"]) for u in block["units"])
            reviewed_targets.extend((u["id"], u["target"]) for u in block["units"])
            block = self.accept(block)["next"]
        self.assertEqual(shared_count, 1)
        self.assertEqual(reviewed_sources, expected)  # source delivery pass 3
        self.assertEqual(reviewed_targets, list(authored_targets.items()))  # target read once
        self.assertEqual(C.load_jsonl(self.master, True)["document"]["context"], context)

    def test_paginated_review_source_once_and_explicit_context_recovery(self):
        self.prepare("A complete source.", context={"summary": "Retain this whole-document concept."})
        target = "译" * (W.MAX_TARGET * 2 + 7)
        self.translate(target)
        page = W.next_block(self.master, "review")
        self.assertIn("source", page["units"][0])
        self.assertIn("shared", page)
        second = W.next_block(self.master, "review", continuation=page["continue"])
        self.assertNotIn("source", second["units"][0])
        self.assertNotIn("shared", second)
        self.assertNotIn("context", second)
        restored = W.next_block(self.master, "review", include_context=True)
        self.assertEqual(restored["units"][0]["source"], page["units"][0]["source"])
        self.assertEqual(restored["shared"], page["shared"])
        self.assertEqual(restored["target_page"], second["target_page"])
        last = W.next_block(self.master, "review", continuation=second["continue"])
        self.assertNotIn("source", last["units"][0])
        self.assertNotIn("shared", last)
        self.assertEqual("".join(p["units"][0]["target"] for p in (page, second, last)), target)
        restart = W.next_block(self.master, "review", restart=True)
        self.assertEqual(restart["units"], page["units"])
        self.assertGreater(C.reference_number(restart["continue"]), C.reference_number(last["ref"]))
        with self.assertRaisesRegex(ValueError, "stale/wrong"):
            self.accept(last)

    def test_initial_receipt_factory_is_atomic_and_replay_safe(self):
        self.source.write_text("Sentence. " * 220)
        page = W.read_source(self.source, self.receipt)
        plan = {"u000001": [1100]}
        with patch.object(C.os, "link", side_effect=OSError("before creation")):
            with self.assertRaises(OSError):
                W.initialize(self.source, self.receipt, self.master, page["ref"], splits=plan)
        self.assertFalse(self.master.exists())
        link = C.os.link
        def link_then_fail(*args):
            link(*args)
            raise OSError("response lost after creation")
        with patch.object(C.os, "link", side_effect=link_then_fail):
            with self.assertRaises(OSError):
                W.initialize(self.source, self.receipt, self.master, page["ref"], splits=plan)
        self.assertTrue(self.master.exists())
        state = C.load_jsonl(self.master)
        frozen = state["document"]["workflow"]["operations"]["_compact_init"]["receipt"]
        self.assertEqual(W.initialize(self.source, self.receipt, self.master, page["ref"], splits=plan), frozen)
        self.assertEqual(frozen["oversize"], [])
        self.assertEqual(len(state["units"]), 2)
        block = W.next_block(self.master)
        W.mutate(self.master, "save", self.targets(block))
        self.assertEqual(W.initialize(self.source, self.receipt, self.master, page["ref"], splits=plan), frozen)

    def test_paged_preread_metadata_complete_plan_and_changed_replay_are_atomic(self):
        first_parts = ["第一句。 " * 360] * 5
        second_parts = ["Second. " * 155] * 2
        text = "\ufeff# 第一节\r\n\r\n" + "".join(first_parts) + "\r\n\r\n## Second\r\n\r\n" + "".join(second_parts)
        self.source.write_bytes(text.encode("utf-8"))
        page = W.read_source(self.source, self.receipt)
        self.assertFalse(page["complete"])
        self.assertGreater(page["oversize"][0]["source_span"][1], page["end"])
        with self.assertRaisesRegex(ValueError, "complete"):
            W.initialize(self.source, self.receipt, self.master, page["ref"], splits={})
        delivered, metadata = page["text"], page["oversize"][:]
        while not page["complete"]:
            page = W.read_source(self.source, self.receipt, page["ref"])
            delivered += page["text"]
            metadata += page.get("oversize", [])
        self.assertEqual(delivered, text)
        self.assertEqual([entry["id"] for entry in metadata], ["u000002", "u000004"])
        for entry, source in zip(metadata, ("".join(first_parts), "".join(second_parts))):
            self.assertEqual(text[slice(*entry["source_span"])], source)
            self.assertNotIn("ref", entry)
        plan = {"u000002": [len(first_parts[0]) * n for n in range(1, 5)],
                "u000004": [len(second_parts[0])]}
        invalid = [None, {}, {"u000002": plan["u000002"]}, dict(plan, u000001=[1]),
                   dict(plan, u000004=[True]), dict(plan, u000004=[1]),
                   dict(plan, u000004=[100, 100]), dict(plan, u000004=[])]
        for candidate in invalid:
            with self.subTest(plan=candidate), self.assertRaises(ValueError):
                W.initialize(self.source, self.receipt, self.master, page["ref"], splits=candidate)
            self.assertFalse(self.master.exists())
        result = W.initialize(self.source, self.receipt, self.master, page["ref"], splits=plan)
        self.assertEqual(result, {"initialized": True, "units": 9, "oversize": []})
        state = C.load_jsonl(self.master)
        self.assertEqual(state["document"]["source"]["sha256"], C.digest(text))
        self.assertTrue(all(len(u["source"]) <= 2048 for u in state["units"]))
        self.assertEqual(W.initialize(self.source, self.receipt, self.master, page["ref"], splits=plan), result)
        before = self.master.read_bytes()
        changed = dict(plan, u000004=[len(second_parts[0]) + 8])
        with self.assertRaisesRegex(ValueError, "different initialization"):
            W.initialize(self.source, self.receipt, self.master, page["ref"], splits=changed)
        self.assertEqual(self.master.read_bytes(), before)

    def test_installed_default_master_is_current_directory_only(self):
        self.prepare()
        installation = self.root / "separate installed skill"
        shutil.copytree(SCRIPT.parents[1], installation)
        script = installation / "scripts/workflow.py"
        def run(*args, cwd=None, check=True):
            return self.cli(*args, cwd=self.root if cwd is None else cwd, script=script, check=check)
        nested = self.root / "nested"
        nested.mkdir()
        missing = run("status", cwd=nested, check=False)
        self.assertEqual(missing.returncode, 1)  # must not search its parent
        self.assertEqual(missing.stdout, "")
        self.assertFalse((nested / "master.jsonl").exists())
        other = self.root / "other task"
        other.mkdir()
        W.initialize(self.source, self.receipt, other / "master.jsonl", self.final_ref)
        block = run("translate", "next")
        other_block = run("translate", "next", cwd=other)
        self.assertEqual(C.reference_number(block["ref"]), C.reference_number(other_block["ref"]))
        payload = self.root / "target.json"
        payload.write_text(json.dumps(self.targets(block)))
        other_payload = other / "target.json"
        other_payload.write_text(json.dumps(self.targets(other_block, "Other task.")))
        root_before = self.master.read_bytes()
        self.assertTrue(run("translate", "save", "--payload", "target.json", cwd=other)["next"]["complete"])
        self.assertEqual(self.master.read_bytes(), root_before)
        self.assertEqual(run("status")["saved"], 0)
        self.assertEqual(run("status", cwd=other)["saved"], 2)
        self.assertTrue(run("translate", "save", "--payload", "target.json")["next"]["complete"])
        review = run("review", "next")
        payload.write_text(json.dumps(self.targets(review, "Corrected.")))
        revised = run("review", "revise", "--payload", "target.json")["next"]
        self.assertTrue(run("review", "accept", "--ref", revised["ref"])["next"]["complete"])
        self.assertTrue(run("validate", "--ready")["valid"])
        run("export", "--output", "exported.json")
        self.assertTrue((self.root / "exported.json").is_file())
        self.assertFalse((other / "exported.json").exists())
        self.assertEqual(run("status")["reviewed"], 2)
        self.assertEqual(run("status", cwd=other)["reviewed"], 0)
        self.assertEqual(run("status", self.master, cwd=other)["reviewed"], 2)
    def test_schema_old_reader_clean_install_and_pdf_import(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((SCRIPT.parents[1] / "schemas/translation-workflow.schema.json").read_text())
        validator = Draft202012Validator(schema)
        self.prepare()
        validator.validate(C.load_jsonl(self.master))
        self.translate()
        review = W.next_block(self.master, "review")
        validator.validate(C.load_jsonl(self.master))
        self.accept(review)
        validator.validate(C.load_jsonl(self.master, require_ready=True))
        destination = self.root / "unrelated installed skill"
        shutil.copytree(SCRIPT.parents[1], destination)
        installed_script = destination / "scripts/workflow.py"
        work = self.root / "installed work"
        work.mkdir()
        source, receipt, installed_master = (work / name for name in ("source.md", "read.json", "master.jsonl"))
        source.write_text("Sentence. " * 220 + "\n\nSecond.")
        def installed(*args):
            return self.cli(*args, script=installed_script)
        page = installed("prepare", "read", source, "--receipt", receipt)
        splits = work / "splits.json"
        splits.write_text(json.dumps({page["oversize"][0]["id"]: [1100]}))
        installed("prepare", "init", source, "--receipt", receipt, "--read-ref", page["ref"],
                  "--output", installed_master, "--source-lang", "en", "--target-lang", "fr", "--splits", splits)
        block = installed("translate", "next", installed_master)
        while not block.get("complete"):
            payload = work / "target.json"
            payload.write_text(json.dumps(self.targets(block)))
            block = installed("translate", "save", installed_master, "--payload", payload)["next"]
        block = installed("review", "next", installed_master)
        while not block.get("complete"):
            block = installed("review", "accept", installed_master, "--ref", block["ref"])["next"]
        self.assertTrue(installed("validate", installed_master, "--ready")["valid"])
        self.assertEqual(W.status(self.master), {"units": 2, "saved": 2, "reviewed": 2,
                                               "next_action": "validate --ready"})
        adapter_spec = importlib.util.spec_from_file_location(
            "pdf_translation_adapter", ROOT / "skills/bilingual-pdf/scripts/import_translation.py")
        adapter = importlib.util.module_from_spec(adapter_spec)
        with patch.object(sys, "path", [str(ROOT / "skills/bilingual-pdf/scripts")] + sys.path):
            adapter_spec.loader.exec_module(adapter)
        reader = adapter.load_workflow(destination)
        data = reader.load_jsonl(installed_master, require_ready=True)
        self.assertEqual([u["target"] for u in reader.to_legacy_document(data)["units"]],
                         ["Translated.Translated.", "Translated."])
        exported = self.root / "legacy.json"
        self.cli("export", self.master, "--output", exported)
        self.assertEqual(C.legacy.validate_document(json.loads(exported.read_text())), [])


if __name__ == "__main__":
    unittest.main()
