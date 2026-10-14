#!/usr/bin/env python3
"""Actual-CLI protocol benchmark, not a translation-quality or billing benchmark.

Requires tiktoken==0.12.0 (benchmark only; installed skill remains stdlib-only).
Example:
  python3 tests/benchmark_translation_tokens.py --skill SKILL \
    --fixtures-skill BASELINE_SKILL --output PRIVATE_NEW_DIRECTORY

Use the same --fixtures-skill for comparable runs. Historical protocol baselines
must use the runner from their recorded source snapshot. Output preserves raw argv, payload,
stdout, UTF-8 byte lengths, token counts, fixture/code hashes and saved masters.
Each CLI command is one logical tool call. Payload authoring is counted once as
agent-output text; stdout is agent-input. File-write framing/calls are excluded, as are MCP/JSON
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

def decode(stdout):
    results, units = [], []
    for line in stdout.splitlines():
        record = json.loads(line)
        kind = record.pop("record_type")
        if kind == "unit":
            units.append(record)
        else:
            assert kind == "receipt"
            results.append({**record, "units": units})
            units = []
    assert results and not units
    return results


class Runner:
    def __init__(self, skill, directory, encoding, mode):
        self.directory, self.encoding, self.mode = directory, encoding, mode
        directory.mkdir(parents=True)
        shutil.copytree(skill, directory / "skill")
        self.records = []
        self.phase = "preparation"

    def measure(self, text):
        return {"bytes": len(text.encode()), "tokens": len(self.encoding.encode(text))}

    def call(self, *actions):
        standalone = self.mode == "direct" or actions[0]["op"] == "export"
        assert not standalone or len(actions) == 1
        argv = ["python3", "-B", "skill/scripts/workflow.py", "--master", "master.jsonl",
                *(actions[0]["op"].split() if standalone else ["run"])]
        payload = "".join(compact(action) + "\n" for action in actions)
        result = subprocess.run(argv, cwd=self.directory, input=payload,
                                capture_output=True, text=True, timeout=30)
        request = compact(argv) + "\n" + payload
        record = {"phase": self.phase, "argv": argv, "stdin": payload,
                  "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode,
                  "agent_output": self.measure(request), "agent_input": self.measure(result.stdout)}
        self.records.append(record)
        (self.directory / "trace.json").write_text(json.dumps(self.records, ensure_ascii=False, indent=2))
        if result.returncode:
            raise RuntimeError(f"{argv}: {result.stderr}")
        decoded = decode(result.stdout)
        assert len(decoded) == len(actions)
        for action, receipt in zip(actions, decoded):
            if action["op"] == "translate save":
                assert type(receipt.get("saved")) is int
                assert receipt["saved"] == len(action["targets"])
            elif action["op"] == "review accept":
                assert type(receipt.get("accepted")) is int and receipt["accepted"] > 0
        return decoded[-1]

    def advance(self, mutation, next_op):
        # Save/accept and next remain separate actions, including in one run packet.
        if self.mode == "run":
            return self.call(mutation, {"op": next_op})
        ack = self.call(mutation)
        assert not ack["units"] and "next" not in ack
        return self.call({"op": next_op})


def run(skill, out, fixture, encoding, mode):
    r = Runner(skill, out / mode / fixture["name"], encoding, mode)
    (r.directory / "source.md").write_bytes(fixture["source"].encode())
    translations = dict(fixture["pairs"])
    translated_ids, reviewed_ids, prepared = [], [], []
    page = r.call({"op": "prepare init", "source": "source.md",
                   "source_lang": fixture["source_lang"], "target_lang": fixture["target_lang"],
                   "context": fixture.get("context", {})})
    while True:
        prepared.extend(u["source"] for u in page["units"])
        for item in page.get("oversize", []):
            source = next(u["source"] for u in page["units"] if u["id"] == item["id"])
            offsets = fixture["splits"][sha(source)]
            ack = r.call({"op": "prepare split", "ref": page["ref"], "unit": item["id"],
                          "cuts": [{"left": source[max(0, n-48):n], "right": source[n:n+48]}
                                   for n in offsets]})
            page["complete"] = ack["complete"]
        if page["complete"]:
            break
        page = r.call({"op": "prepare init", "ref": page["ref"]})
    for phase, next_op, mutation in (("translation", "translate next", "translate save"),
                                     ("review", "review next", "review accept")):
        r.phase = phase
        block = r.call({"op": next_op})
        assert block.get("context", {}) == fixture.get("context", {})
        while not block.get("complete"):
            assert sum(len(u["source"]) for u in block["units"]) <= 2048
            if phase == "translation":
                translated_ids.extend(u["id"] for u in block["units"])
                action = {"op": mutation, "ref": block["ref"],
                          "targets": {u["id"]: translations[u["source"]] for u in block["units"]}}
            else:
                for u in block["units"]:
                    assert translations[u["source"]] == u["target"]
                reviewed_ids.extend(u["id"] for u in block["units"])
                action = {"op": mutation, "ref": block["ref"], "reviewer": "translation-agent", "note": NOTE}
            block = r.advance(action, next_op)
    r.phase = "reconciliation"
    r.call({"op": "validate"})
    r.call({"op": "export", "output": "export.json"})
    header, *units = [json.loads(line) for line in (r.directory / "master.jsonl").read_text().splitlines()]
    assert translated_ids == reviewed_ids == [u["id"] for u in units]
    assert all(u["status"] == "reviewed" and translations[u["source"]] == u["target"] for u in units)
    parents = {}
    for u in units:
        parents[u["parent_id"]] = parents.get(u["parent_id"], "") + u["source"]
    assert prepared == list(parents.values())
    reconstructed = "".join(item["text"] if "text" in item else parents[item["parent"]]
                            for item in header["source_layout"])
    assert reconstructed == fixture["source"]
    exposure = exposures(r.records, units, fixture)
    totals = {direction: {k: sum(x[direction][k] for x in r.records) for k in ("bytes", "tokens")}
              for direction in ("agent_input", "agent_output")}
    return {"fixture": fixture["name"], "mode": mode, "fixture_hash": sha(compact(fixture)),
            "source_characters": len(fixture["source"]), "source_bytes": len(fixture["source"].encode()),
            "source_tokens": len(encoding.encode(fixture["source"])),
            "target_tokens": sum(len(encoding.encode(t)) for _, t in fixture["pairs"]),
            "exposure": exposure, "has_optional_context": "context" in fixture,
            "units": len(units), "calls": len(r.records),
            "calls_by_phase": dict(Counter(x["phase"] for x in r.records)),
            "phase_tokens": {phase: sum(x["agent_input"]["tokens"] + x["agent_output"]["tokens"]
                             for x in r.records if x["phase"] == phase)
                             for phase in dict.fromkeys(x["phase"] for x in r.records)},
            "progress_tokens": sum(len(encoding.encode(compact(result["progress"])))
                                   for record in r.records for result in decode(record["stdout"])
                                   if "progress" in result),
            **totals, "protocol_tokens": sum(v["tokens"] for v in totals.values()),
            "ready": True, "exact_source_reconstruction": True}


def exposures(records, units, fixture):
    counts = {u["id"]: {"translation": 0, "review": 0, "target_write": 0, "target_read": 0} for u in units}
    totals = {"prepare_source": 0, "translation_source": 0, "review_source": 0,
              "target_written": 0, "target_read": 0, "shared_context_emissions": 0}
    saved_count, accepted_count = 0, 0
    by_id = {u["id"]: u for u in units}
    for record in records:
        phase = record["phase"]
        for result in decode(record["stdout"]):
            saved_count += result.get("saved", 0)
            accepted_count += result.get("accepted", 0)
            if phase == "preparation":
                totals["prepare_source"] += sum(len(u["source"]) for u in result["units"])
            if "context" in result:
                totals["shared_context_emissions"] += 1
            if phase in ("translation", "review"):
                for u in result["units"]:
                    master_unit = by_id[u["id"]]
                    assert u.get("parent_id", u["id"]) == master_unit["parent_id"]
                    assert u.get("part_index", 0) == master_unit["part_index"]
                    assert u.get("has_more", False) == master_unit["has_more"]
                    counts[u["id"]][phase] += 1
                    totals[phase + "_source"] += len(u["source"])
                    if u.get("target") is not None:
                        counts[u["id"]]["target_read"] += 1
                        totals["target_read"] += len(u["target"])
        for line in record["stdin"].splitlines():
            for uid, target in json.loads(line).get("targets", {}).items():
                counts[uid]["target_write"] += 1
                totals["target_written"] += len(target)
    body = sum(len(u["source"]) for u in units)
    assert totals["prepare_source"] == totals["translation_source"] == totals["review_source"] == body
    assert totals["target_written"] == totals["target_read"] == sum(len(u["target"]) for u in units)
    assert all(all(n == 1 for n in count.values()) for count in counts.values())
    assert saved_count == accepted_count == len(units)
    assert totals["shared_context_emissions"] == (2 if fixture.get("context") else 0)
    return {**totals, "unit_body_characters": body,
            "syntax_characters_preserved_in_master": len(fixture["source"]) - body,
            "primary_source_reads_per_unit": 3, "three_pass_without_extra_source": True,
            "per_unit": counts, "retry_or_revise": "Not exercised in these normal-path workloads"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--fixtures-skill", type=Path, required=True)
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
    summary = {"protocol": "workflow", "python": sys.version, "tokenizer": "tiktoken",
               "tokenizer_version": tiktoken.__version__, "encoding": "o200k_base",
               "boundary": "Actual argv JSON + once-authored payload; actual stdout. Excludes MCP/file-write framing, reasoning, billing and rendering.",
               "quality": "Fixed reviewed fixture translations replayed by code; protocol evidence only, no live translation evaluation.",
               "code_hashes": {str(p.relative_to(skill)): sha(p.read_bytes()) for p in sorted(skill.rglob("*.py"))},
               "fixed_loading": {p: {"sha256": sha((skill / p).read_bytes()),
                                    "tokens": len(enc.encode((skill / p).read_text())),
                                    "bytes": len((skill / p).read_bytes())} for p in docs},
               "workloads": []}
    for mode in ("direct", "run"):
        for case in cases:
            summary["workloads"].append(run(skill, args.output, case, enc, mode))
            (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.baseline_summary:
        baseline = json.loads(args.baseline_summary.read_text())
        assert baseline["tokenizer_version"] == summary["tokenizer_version"]
        assert baseline["encoding"] == summary["encoding"]
        comparison = []
        for after in summary["workloads"]:
            before = next(row for row in baseline["workloads"] if row["fixture"] == after["fixture"])
            assert before["fixture_hash"] == after["fixture_hash"]
            comparison.append({"fixture": after["fixture"], "mode": after["mode"],
                "before_tokens": before["protocol_tokens"], "after_tokens": after["protocol_tokens"],
                "token_reduction_percent": 100 * (1 - after["protocol_tokens"] / before["protocol_tokens"]),
                "before_calls": before["calls"], "after_calls": after["calls"]})
        summary["comparison"] = comparison
        (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
