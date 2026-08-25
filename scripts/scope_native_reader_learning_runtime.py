#!/usr/bin/env python3
"""Keep native-reader Brain memory useful without leaking it across client runtime drift.

Reader repair outcomes are only valid control evidence for the exact official Nuvio
client revisions on which they were observed. Historical entries are retained, but a
repair sandbox receives only entries whose runtimeFingerprint exactly matches the
current Labs runtime. Legacy unscoped entries are deliberately excluded.

The `merge` mode delegates the existing outcome aggregation to
merge_native_reader_repair_learning.py on a runtime-filtered view, then merges the
new runtime-scoped entries back into the full historical state.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MERGER = ROOT / "scripts" / "merge_native_reader_repair_learning.py"
CROSS_RUNTIME_GATE = ROOT / "scripts" / "gate_native_cross_client_runtime.cjs"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_fingerprint(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.casefold()
    if not text:
        raise ValueError("runtime fingerprint is required")
    if len(text) > 700:
        raise ValueError("runtime fingerprint is too long")
    if "://" in text or any(token in lowered for token in ("authorization=", "cookie=", "token=", "secret=")):
        raise ValueError("runtime fingerprint contains forbidden endpoint/credential material")
    return text


def memory(state: dict[str, Any]) -> dict[str, Any]:
    value = state.get("nativeReaderRepairMemory")
    return value if isinstance(value, dict) else {}


def entry_fingerprint(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("runtimeFingerprint") or "").strip()


def scoped_state(state: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    result = json.loads(json.dumps(state))
    source_memory = memory(state)
    source_entries = [row for row in source_memory.get("entries") or [] if isinstance(row, dict)]
    selected = [dict(row) for row in source_entries if entry_fingerprint(row) == fingerprint]
    scoped_memory = dict(source_memory)
    scoped_memory["schemaVersion"] = max(2, int(scoped_memory.get("schemaVersion") or 0))
    scoped_memory["runtimeAware"] = True
    scoped_memory["entries"] = selected
    scoped_memory["runtimeScope"] = {
        "fingerprint": fingerprint,
        "sourceEntryCount": len(source_entries),
        "selectedEntryCount": len(selected),
        "excludedEntryCount": len(source_entries) - len(selected),
        "legacyUnscopedExcluded": sum(1 for row in source_entries if not entry_fingerprint(row)),
    }
    result["nativeReaderRepairMemory"] = scoped_memory
    return result


def combine_runtime_memory(
    original: dict[str, Any], merged: dict[str, Any], fingerprint: str
) -> dict[str, Any]:
    result = json.loads(json.dumps(merged))
    original_memory = memory(original)
    merged_memory = memory(merged)

    historical = [
        dict(row)
        for row in original_memory.get("entries") or []
        if isinstance(row, dict) and entry_fingerprint(row) != fingerprint
    ]
    current = []
    for raw in merged_memory.get("entries") or []:
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        row["runtimeFingerprint"] = fingerprint
        current.append(row)

    imported: list[str] = []
    for source in (original_memory, merged_memory):
        for raw in source.get("importedRunIds") or []:
            value = str(raw or "").strip()
            if value.isdigit() and value not in imported:
                imported.append(value)

    combined = dict(merged_memory)
    combined["schemaVersion"] = max(2, int(combined.get("schemaVersion") or 0))
    combined["runtimeAware"] = True
    combined["entries"] = (current + historical)[:1200]
    combined["importedRunIds"] = imported[-100:]
    combined["runtimeScope"] = {
        "fingerprint": fingerprint,
        "currentRuntimeEntryCount": len(current),
        "historicalOtherRuntimeEntryCount": len(historical),
        "reusePolicy": "exact-runtime-fingerprint-only",
    }
    combined["skillStatsRuntimeFingerprint"] = fingerprint
    result["nativeReaderRepairMemory"] = combined
    result["privacy"] = (
        "Native reader memory keeps sanitized provider/fixture/failure/skill ids and exact client revision "
        "fingerprints only; historical runtime evidence is retained but never reused across client drift."
    )
    return result


def gate_representative_runtime_before_learning() -> None:
    """Fail closed on systemic TV/Mobile runtime divergence before Brain repair."""
    workspace_raw = os.environ.get("GITHUB_WORKSPACE", "").strip()
    if not workspace_raw:
        return
    baseline = Path(workspace_raw).resolve() / "baseline-reader"
    tv = baseline / "tv"
    mobile = baseline / "mobile"
    if not tv.is_dir() and not mobile.is_dir():
        return
    if not tv.is_dir() or not mobile.is_dir():
        raise RuntimeError(
            f"incomplete pre-Brain runtime evidence: tv={tv.is_dir()} mobile={mobile.is_dir()}"
        )
    command = [
        "node",
        str(CROSS_RUNTIME_GATE),
        "--dir", str(baseline),
        "--require-clients", "mobile,tv",
        "--min-comparisons", "3",
    ]
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if process.stdout:
        print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, end="")
    if process.returncode != 0:
        raise RuntimeError(
            f"pre-Brain cross-runtime gate failed with exit code {process.returncode}"
        )
    print("FIELD_NATIVE_READER_RUNTIME_PREBRAIN_GATE status=pass clients=mobile,tv")


def run_filter(args: argparse.Namespace) -> int:
    gate_representative_runtime_before_learning()
    fingerprint = clean_fingerprint(args.runtime_fingerprint)
    state = read_json(args.state)
    scoped = scoped_state(state, fingerprint)
    write_json(args.output, scoped)
    scope = scoped["nativeReaderRepairMemory"]["runtimeScope"]
    print(
        "FIELD_NATIVE_READER_RUNTIME_SCOPE "
        f"selected={scope['selectedEntryCount']} excluded={scope['excludedEntryCount']} "
        f"legacy_excluded={scope['legacyUnscopedExcluded']}"
    )
    return 0


def run_merge(args: argparse.Namespace) -> int:
    fingerprint = clean_fingerprint(args.runtime_fingerprint)
    original = read_json(args.state)
    scoped = scoped_state(original, fingerprint)

    with tempfile.TemporaryDirectory(prefix="niakvio-reader-runtime-") as raw:
        temp = Path(raw)
        scoped_path = temp / "scoped.json"
        merged_path = temp / "merged.json"
        write_json(scoped_path, scoped)
        cmd = [
            "python3", str(MERGER),
            "--state", str(scoped_path),
            "--previous-state", str(scoped_path),
            "--comparison", str(args.comparison),
            "--output", str(merged_path),
        ]
        if args.markdown_input and args.markdown_output:
            cmd += [
                "--markdown-input", str(args.markdown_input),
                "--markdown-output", str(args.markdown_output),
            ]
        process = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(process.stdout + process.stderr)
        merged = read_json(merged_path)

    combined = combine_runtime_memory(original, merged, fingerprint)
    write_json(args.output, combined)
    print(
        "FIELD_NATIVE_READER_RUNTIME_MERGE "
        f"runtime_entries={combined['nativeReaderRepairMemory']['runtimeScope']['currentRuntimeEntryCount']} "
        f"historical_entries={combined['nativeReaderRepairMemory']['runtimeScope']['historicalOtherRuntimeEntryCount']}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    filter_parser = sub.add_parser("filter")
    filter_parser.add_argument("--state", type=Path, required=True)
    filter_parser.add_argument("--runtime-fingerprint", required=True)
    filter_parser.add_argument("--output", type=Path, required=True)
    filter_parser.set_defaults(handler=run_filter)

    merge_parser = sub.add_parser("merge")
    merge_parser.add_argument("--state", type=Path, required=True)
    merge_parser.add_argument("--comparison", type=Path, required=True)
    merge_parser.add_argument("--runtime-fingerprint", required=True)
    merge_parser.add_argument("--output", type=Path, required=True)
    merge_parser.add_argument("--markdown-input", type=Path)
    merge_parser.add_argument("--markdown-output", type=Path)
    merge_parser.set_defaults(handler=run_merge)

    args = parser.parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
