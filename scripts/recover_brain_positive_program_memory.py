#!/usr/bin/env python3
"""Recover durable positive Brain program priors from historical accepted reports.

This is a recovery mechanism for accidental state loss only. Historical accepted
programs remain priors: every future replay must still pass current-byte,
playback, identity and non-regression gates.

Only rows that were strict playable improvements and whose accepted program still
compiles under the current compiler are eligible.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
AUTOMATION = ROOT / "automation"

from brain_positive_program_memory import MEMORY_PATH, merge_records
from compile_brain_accepted_program_v3 import compile_program


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def eligible(row: dict[str, Any], compiled_providers: set[str]) -> bool:
    provider = cid(row.get("provider"))
    if not provider or provider not in compiled_providers:
        return False
    if str(row.get("reason") or "") != "strict_playable_stream_improvement":
        return False
    if max(0, int(row.get("playableAfter") or 0)) <= max(0, int(row.get("playableBefore") or 0)):
        return False
    program = row.get("acceptedProgram")
    if not isinstance(program, dict) or not program:
        return False
    persistence = row.get("v3ProgramPersistence")
    if isinstance(persistence, dict) and persistence.get("status") not in {None, "compiled"}:
        return False
    return True


def recover(report_paths: list[Path], *, memory_path: Path = MEMORY_PATH) -> dict[str, Any]:
    accepted_compiled: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen: set[tuple[str, str, int, int]] = set()
    rejected: dict[str, str] = {}

    for path in report_paths:
        report = load(path)
        compiled_providers = {
            cid(value)
            for value in report.get("acceptedProgramCompiledProviders") or []
            if cid(value)
        }
        for raw in report.get("acceptedRepairs") or []:
            if not isinstance(raw, dict) or not eligible(raw, compiled_providers):
                continue
            provider = cid(raw.get("provider"))
            plan = raw.get("brainPlan") if isinstance(raw.get("brainPlan"), dict) else {}
            key = (
                provider,
                str(plan.get("signature") or ""),
                max(0, int(plan.get("experimentVariant") or 0)),
                max(1, int(plan.get("experimentGeneration") or 1)),
            )
            if key in seen:
                continue
            seen.add(key)
            try:
                compiled = compile_program(raw["acceptedProgram"], provider)
            except (TypeError, ValueError) as exc:
                rejected[f"{provider}:{path.name}"] = str(exc)[:240] or type(exc).__name__
                continue
            accepted_compiled.append((raw, compiled))

    memory = merge_records(accepted_compiled, path=memory_path) if accepted_compiled else None
    if memory is None:
        from brain_positive_program_memory import load_memory
        memory = load_memory(memory_path)

    providers = sorted({
        cid(row.get("providerId"))
        for row in memory.get("entries") or []
        if isinstance(row, dict) and cid(row.get("providerId"))
    })
    return {
        "schemaVersion": 1,
        "reportCount": len(report_paths),
        "recoveredRecordCount": len(accepted_compiled),
        "durableRecordCount": len(memory.get("entries") or []),
        "durableProviders": providers,
        "rejected": dict(sorted(rejected.items())),
        "publicationAuthority": False,
        "currentByteValidationRequired": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory", type=Path, default=MEMORY_PATH)
    parser.add_argument("--report", type=Path, action="append", default=[])
    parser.add_argument("--report-glob", default="automation/provider-brain-repair-*.json")
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    reports = list(args.report)
    if not reports:
        reports = sorted(
            path
            for path in ROOT.glob(args.report_glob)
            if path.is_file() and path.name != "provider-brain-repair-latest.json"
        )
    result = recover(reports, memory_path=args.memory)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        "FIELD_BRAIN_POSITIVE_MEMORY_RECOVERY "
        f"reports={result['reportCount']} recovered={result['recoveredRecordCount']} "
        f"durable={result['durableRecordCount']} providers={','.join(result['durableProviders']) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
