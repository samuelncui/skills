#!/usr/bin/env python3
"""Actual-CLI protocol benchmark, not a translation-quality or billing benchmark.

Requires tiktoken==0.12.0 (benchmark only; installed skill remains stdlib-only).
Example:
  python3 tests/benchmark_translation_tokens.py --skill SKILL --mode legacy \
    --fixtures-skill BASELINE_SKILL --output PRIVATE_NEW_DIRECTORY

Use the same --fixtures-skill for both modes. Output preserves raw argv, payload,
stdout, UTF-8 byte lengths, token counts, fixture/code hashes and saved masters.
Each CLI command is one logical tool call. Payload authoring is counted once as
input text; a separate file-write tool's framing/call is excluded, as are MCP/JSON
transport envelopes, hidden reasoning, pricing, cache discounts and rendering.
Commands use fixed relative paths, and the actual CLI output is not normalized.
Random protocol references may cause small token-count differences between runs.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NOTE = "Compared meaning, numbers, qualifications and terminology."

def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()

def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

def fixtures(skill):
    guide = skill / "examples/guide"
    units = json.loads((guide / "translation.json").read_text())["units"]
    short = {"name": "guide_short", "source": (guide / "source.txt").read_text(),
             "source_lang": "en", "target_lang": "fr",
             "pairs": [[u["source"], u["target"]] for u in units], "splits": {}}
    chunks, targets = [], []
    for group in range(3):
        src, dst = [], []
        for number in range(group * 6 + 1, group * 6 + 7):
            src.append(f"At station {number}, record the temperature at 09:00 before opening the sample box. If the reading exceeds 30 degrees Celsius, keep the box closed and notify the coordinator; do not discard the sample. ")
            dst.append(f"在第{number}号站点，打开样品盒之前，先记录09:00的温度。如果读数超过30摄氏度，请保持盒子关闭并通知协调员；不要丢弃样品。")
        chunks.append("".join(src))
        targets.append("".join(dst))
    long_source = "".join(chunks)
    long = {"name": "long_semantic_split", "source": long_source,
            "source_lang": "en", "target_lang": "zh-CN",
            "pairs": list(map(list, zip(chunks, targets))),
            "splits": {sha(long_source): [len(chunks[0]), len(chunks[0]) + len(chunks[1])]}}
    pairs = [
        ["库存检查", "Inventory check"],
        ["2026年10月14日，仓库有12个密封箱。只有标签完整的箱子才能发出；不要打开封条。", "On October 14, 2026, the warehouse has 12 sealed boxes. Only boxes with intact labels may be dispatched; do not break the seals."],
        ["如果温度高于30摄氏度，暂停发货。温度等于30摄氏度时，这项限制不适用。", "If the temperature is above 30 degrees Celsius, suspend dispatch. This restriction does not apply when the temperature is exactly 30 degrees Celsius."],
        ["记录检查时间。", "Record the inspection time."],
        ["保留原始标签。", "Keep the original labels."],
        ["项目", "Item"], ["数量", "Quantity"], ["密封箱", "Sealed boxes"], ["12", "12"], ["备用标签", "Spare labels"], ["3", "3"]]
    source = "# " + pairs[0][0] + "\n\n" + pairs[1][0] + "\n\n" + pairs[2][0] + "\n\n- " + pairs[3][0] + "\n- " + pairs[4][0] + "\n\n| 项目 | 数量 |\n| --- | --- |\n| 密封箱 | 12 |\n| 备用标签 | 3 |\n"
    mixed = {"name": "zh_en_structure", "source": source, "source_lang": "zh-CN",
             "target_lang": "en", "pairs": pairs, "splits": {}}
    pairs = [["Shelf register", "种子架登记簿"], ["Keep each batch separate. Record the collection date before placing packets on the shelf.", "将各批次分开放置。将种子袋放上种子架之前，先记录采集日期。"], ["If a label is missing, set the packet aside; do not invent a date.", "如果标签缺失，请将种子袋单独放置；不要编造日期。"]]
    contextual = {"name": "shared_context", "source": "# " + pairs[0][0] + "\n\n" + "\n\n".join(x[0] for x in pairs[1:]) + "\n", "source_lang": "en", "target_lang": "zh-CN", "pairs": pairs, "splits": {}, "context": {"summary": "Instructions for a community seed shelf, emphasizing traceability and missing-label handling.", "audience": "Community volunteers", "glossary": [{"source": "batch", "target": "批次"}, {"source": "packet", "target": "种子袋"}]}}
    return [short, long, mixed, contextual]

class Runner:
    def __init__(self, skill, directory, encoding, mode):
        self.directory = directory
        directory.mkdir()
        shutil.copytree(skill, directory / "skill")
        self.encoding = encoding
        self.entrypoint = "workflow.py" if mode == "compact" else "translation_workflow.py"
        self.records = []
        self.phase = "preparation"

    def measure(self, text):
        return {"bytes": len(text.encode()), "tokens": len(self.encoding.encode(text))}

    def call(self, *args, payload=None):
        argv = ["python3", "-B", "skill/scripts/" + self.entrypoint, *map(str, args)]
        payload_text = ""
        if payload is not None:
            payload_text = compact(payload)
            (self.directory / "payload.json").write_text(payload_text)
            argv += ["--payload", "payload.json"]
        result = subprocess.run(argv, cwd=self.directory,
                                capture_output=True, text=True, timeout=30)
        context_text = (self.directory / "context.json").read_text() if "context.json" in argv else ""
        splits_text = (self.directory / "splits.json").read_text() if "splits.json" in argv else ""
        request = compact(argv) + ("\n" + payload_text if payload is not None else "") + ("\n" + context_text if context_text else "") + ("\n" + splits_text if splits_text else "")
        record = {"phase": self.phase, "argv": argv, "payload": payload_text, "context_payload": context_text, "splits_payload": splits_text,
                  "stdout": result.stdout, "stderr": result.stderr,
                  "returncode": result.returncode,
                  "input": self.measure(request), "output": self.measure(result.stdout)}
        self.records.append(record)
        (self.directory / "trace.json").write_text(json.dumps(self.records, ensure_ascii=False, indent=2))
        if result.returncode:
            raise RuntimeError(f"{argv}: {result.stderr}")
        return json.loads(result.stdout)

    def state(self):
        records = [json.loads(line) for line in (self.directory / "master.jsonl").read_text().splitlines() if line]
        return records[0], records[1:]

def run(skill, out, fixture, mode, encoding):
    r = Runner(skill, out / fixture["name"], encoding, mode)
    (r.directory / "source.md").write_bytes(fixture["source"].encode())
    translations = dict(fixture["pairs"])
    translated_ids, reviewed_ids = [], []
    context_args = []
    if "context" in fixture:
        (r.directory / "context.json").write_text(compact(fixture["context"]))
        context_args = ["--context", "context.json"]
    if mode == "legacy":
        page = r.call("read-source", "source.md", "--receipt", "read.json")
        delivered = page["text"]
        while not page["complete"]:
            page = r.call("read-source", "source.md", "--receipt", "read.json", "--continue", page["token"])
            delivered += page["text"]
        assert delivered == fixture["source"]
        r.call("ack-source", "source.md", "--receipt", "read.json", "--source-hash", page["source_hash"], "--token", page["token"])
        r.call("init", "source.md", "--receipt", "read.json", "--output", "master.jsonl",
               "--source-lang", fixture["source_lang"], "--target-lang", fixture["target_lang"], *context_args)
        large = r.call("oversize", "master.jsonl")["oversize"]
        for item in large:
            unit_id = item.get("id", item.get("unit"))
            inspected = r.call("inspect", "master.jsonl", "--unit", unit_id)
            u = inspected["unit"]
            r.call("split", "master.jsonl", "--unit", unit_id, "--offsets",
                   ",".join(map(str, fixture["splits"][u["source_hash"]])),
                   "--source-hash", u["source_hash"], "--revision", inspected["revision"])
        r.phase = "translation"
        while True:
            block = r.call("next", "master.jsonl")
            if block.get("complete"):
                break
            translated_ids.extend(u["id"] for u in block["units"])
            r.call("commit", "master.jsonl", payload={
                "operation_id": "save-" + block["units"][0]["id"],
                "block_id": block["block_id"], "revision": block["revision"],
                "source_hashes": block["source_hashes"],
                "targets": {u["id"]: translations[u["source"]] for u in block["units"]}})
        r.phase = "review"
        _, saved = r.state()
        for original in saved:
            inspected = r.call("inspect", "master.jsonl", "--unit", original["id"])
            u = inspected["unit"]
            assert translations[u["source"]] == u["target"]
            reviewed_ids.append(u["id"])
            r.call("review", "master.jsonl", payload={
                "operation_id": "review-" + u["id"], "revision": inspected["revision"],
                "unit": u["id"], "source_hash": u["source_hash"], "target_hash": u["target_hash"],
                "reviewer": "translation-agent", "note": NOTE})
    else:
        page = r.call("prepare", "read", "source.md", "--receipt", "read.json")
        delivered = page["text"]
        oversized = list(page.get("oversize", []))
        while not page["complete"]:
            page = r.call("prepare", "read", "source.md", "--receipt", "read.json", "--continue", page["ref"])
            delivered += page["text"]
            oversized.extend(page.get("oversize", []))
        assert delivered == fixture["source"]
        split_plan = {}
        for item in oversized:
            start, end = item["source_span"]
            source = delivered[start:end]
            assert len(source) == item["characters"]
            split_plan[item["id"]] = fixture["splits"][sha(source)]
        split_args = []
        if split_plan:
            (r.directory / "splits.json").write_text(compact(split_plan))
            split_args = ["--splits", "splits.json"]
        initialized = r.call("prepare", "init", "source.md", "--receipt", "read.json",
                             "--read-ref", page["ref"], "--output", "master.jsonl",
                             "--source-lang", fixture["source_lang"], "--target-lang", fixture["target_lang"],
                             *context_args, *split_args)
        assert initialized["oversize"] == []
        r.phase = "translation"
        block = r.call("translate", "next")
        assert block["shared"] == fixture.get("context", {})
        while not block.get("complete"):
            assert sum(len(u["source"]) for u in block["units"]) <= 2048
            translated_ids.extend(u["id"] for u in block["units"])
            result = r.call("translate", "save", payload={
                "ref": block["ref"], "targets": {u["id"]: translations[u["source"]] for u in block["units"]}})
            block = result["next"]
        r.phase = "review"
        block = r.call("review", "next")
        assert block["shared"] == fixture.get("context", {})
        while not block.get("complete"):
            for u in block["units"]:
                assert translations[u["source"]] == u["target"]
            reviewed_ids.extend(u["id"] for u in block["units"])
            result = r.call("review", "accept", "--ref", block["ref"],
                            "--reviewer", "translation-agent", "--note", NOTE)
            block = result["next"]
    r.phase = "reconciliation"
    data_args = [] if mode == "compact" else ["master.jsonl"]
    r.call("validate", *data_args, "--ready")
    r.call("export", *data_args, "--output", "export.json")
    header, units = r.state()
    assert translated_ids == reviewed_ids == [u["id"] for u in units]
    assert all(u["status"] == "reviewed" and translations[u["source"]] == u["target"] for u in units)
    source_by_parent = {}
    for u in units:
        source_by_parent[u["parent_id"]] = source_by_parent.get(u["parent_id"], "") + u["source"]
    reconstructed = "".join(item["text"] if "text" in item else source_by_parent[item["parent"]] for item in header["source_layout"])
    assert reconstructed == fixture["source"]
    exposure = exposures(r.records, units, fixture, mode)
    totals = {direction: {k: sum(x[direction][k] for x in r.records) for k in ("bytes", "tokens")}
              for direction in ("input", "output")}
    return {"fixture": fixture["name"], "fixture_hash": sha(compact(fixture)),
            "source_characters": len(fixture["source"]), "source_bytes": len(fixture["source"].encode()),
            "source_tokens": len(encoding.encode(fixture["source"])),
            "target_tokens": sum(len(encoding.encode(t)) for _, t in fixture["pairs"]),
            "exposure": exposure, "has_optional_context": "context" in fixture,
            "units": len(units), "calls": len(r.records), "calls_by_phase": dict(Counter(x["phase"] for x in r.records)),
            "phase_tokens": {phase: sum(x["input"]["tokens"] + x["output"]["tokens"] for x in r.records if x["phase"] == phase) for phase in dict.fromkeys(x["phase"] for x in r.records)},
            **totals, "protocol_tokens": totals["input"]["tokens"] + totals["output"]["tokens"],
            "ready": True, "exact_source_reconstruction": True}

def exposures(records, units, fixture, mode):
    """Count decoded body delivery, not substring matches or billing tokens."""
    counts = {u["id"]: {"translation": 0, "review": 0, "target_write": 0, "target_read": 0} for u in units}
    totals = {"prepare_source": 0, "prepare_inspect_source": 0, "translation_source": 0,
              "review_source": 0, "target_written": 0, "target_read": 0,
              "local_context_characters": 0, "shared_context_characters": 0,
              "shared_context_emissions": 0}
    for record in records:
        value = json.loads(record["stdout"])
        phase = record["phase"]
        if phase == "preparation" and isinstance(value.get("text"), str):
            totals["prepare_source"] += len(value["text"])
        if phase == "preparation" and isinstance(value.get("unit"), dict):
            totals["prepare_inspect_source"] += len(value["unit"]["source"])
        envelope = value.get("next", value)
        shown = envelope.get("units", [])
        if not isinstance(shown, list):
            shown = []
        if phase == "review" and isinstance(value.get("unit"), dict):
            shown = [value["unit"]]
        if phase in ("translation", "review"):
            for unit in shown:
                counts[unit["id"]][phase] += 1
                totals[phase + "_source"] += len(unit.get("source", ""))
                if "target" in unit and unit["target"] is not None:
                    counts[unit["id"]]["target_read"] += 1
                    totals["target_read"] += len(unit["target"])
        if envelope.get("context"):
            totals["local_context_characters"] += len(envelope["context"].get("text", ""))
        if "shared" in envelope:
            totals["shared_context_emissions"] += 1
            totals["shared_context_characters"] += len(compact(envelope["shared"]))
        if record["payload"]:
            for uid, text in json.loads(record["payload"]).get("targets", {}).items():
                counts[uid]["target_write"] += 1
                totals["target_written"] += len(text)
    body = sum(len(u["source"]) for u in units)
    expected_targets = sum(len(u["target"]) for u in units)
    assert totals["prepare_source"] == len(fixture["source"])
    assert totals["translation_source"] == totals["review_source"] == body
    assert totals["target_written"] == totals["target_read"] == expected_targets
    assert all(all(n == 1 for n in count.values()) for count in counts.values())
    if mode == "compact":
        assert totals["prepare_inspect_source"] == 0
        assert totals["local_context_characters"] == 0
        assert totals["shared_context_emissions"] == 2
    return {**totals, "unit_body_characters": body,
            "syntax_characters_read_once": len(fixture["source"]) - body,
            "primary_source_reads_per_unit": 3,
            "three_pass_without_extra_source": mode == "compact",
            "per_unit": counts,
            "context_scope": "Authored semantic summary/audience/glossary, not full source" if "context" in fixture else "No optional context supplied",
            "retry_or_revise": "Not exercised in these normal-path workloads"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--fixtures-skill", type=Path, required=True)
    parser.add_argument("--mode", choices=["legacy", "compact"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workload", action="append", help="Run only named workload(s)")
    parser.add_argument("--baseline-summary", type=Path, help="Compare against preserved baseline summary")
    args = parser.parse_args()
    import tiktoken
    if tiktoken.__version__ != "0.12.0":
        parser.error("This baseline pins tiktoken==0.12.0.")
    enc = tiktoken.get_encoding("o200k_base")
    skill = args.skill.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(skill, args.output / "skill-snapshot", ignore=shutil.ignore_patterns("__pycache__"))
    skill = (args.output / "skill-snapshot").resolve()
    cases = fixtures(args.fixtures_skill.resolve())
    if args.workload:
        cases = [case for case in cases if case["name"] in args.workload]
        assert len(cases) == len(set(args.workload)), "Unknown workload"
    (args.output / "fixtures.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2))
    docs = ["SKILL.md", "references/workflow.md"]
    summary = {"mode": args.mode, "python": sys.version, "tokenizer": "tiktoken",
               "tokenizer_version": tiktoken.__version__, "encoding": "o200k_base",
               "boundary": "Actual argv JSON + once-authored payload; actual stdout. Excludes MCP/file-write framing, reasoning, billing and rendering.",
               "quality": "Fixed reviewed fixture translations replayed by code; protocol evidence only, no live translation evaluation.",
               "code_hashes": {str(p.relative_to(skill)): sha(p.read_bytes()) for p in sorted(skill.rglob("*.py"))},
               "fixed_loading": {p: {"sha256": sha((skill / p).read_bytes()),
                                    "tokens": len(enc.encode((skill / p).read_text())),
                                    "bytes": len((skill / p).read_bytes())} for p in docs},
               "workloads": []}
    for case in cases:
        summary["workloads"].append(run(skill, args.output, case, args.mode, enc))
        (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.baseline_summary:
        baseline = json.loads(args.baseline_summary.read_text())
        assert baseline["tokenizer_version"] == summary["tokenizer_version"]
        assert baseline["encoding"] == summary["encoding"]
        comparison = []
        for before, after in zip(baseline["workloads"], summary["workloads"], strict=True):
            assert before["fixture_hash"] == after["fixture_hash"]
            comparison.append({"fixture": after["fixture"],
                "before_tokens": before["protocol_tokens"], "after_tokens": after["protocol_tokens"],
                "token_reduction_percent": 100 * (1 - after["protocol_tokens"] / before["protocol_tokens"]),
                "before_calls": before["calls"], "after_calls": after["calls"]})
        summary["comparison"] = comparison
        (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
