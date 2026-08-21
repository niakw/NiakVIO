#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail-closed Nuvio client provider-contract guard before Brain mutation.

The full upstream checker deliberately remains stricter than this guard: reader/UI/player
changes still require native reader re-audit, while provider Brain mutation is blocked only
when the changed client surface can alter provider request/result/extraction semantics.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_nuvio_client_upstreams.py"
CONFIG = ROOT / "automation/nuvio-client-upstreams.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def path_matches(filename: str, rules: list[str]) -> bool:
    normalized = str(filename or "").strip().lstrip("/")
    for raw in rules:
        rule = str(raw or "").strip().lstrip("/")
        if not rule:
            continue
        if rule.endswith("/") and normalized.startswith(rule):
            return True
        if not rule.endswith("/") and normalized == rule:
            return True
    return False


def classify_provider_mutation_compat(
    report: dict[str, Any], config: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Return (blocking provider drift, reader-only re-audit pending)."""
    blockers: list[str] = []
    reader_pending: list[str] = []
    configured = config.get("clients") or {}
    results = report.get("clients") or {}

    for client_id, row in configured.items():
        if not isinstance(row, dict):
            blockers.append(f"{client_id}:invalid_config")
            continue
        result = results.get(client_id)
        if not isinstance(result, dict):
            blockers.append(f"{client_id}:missing_verification")
            continue

        status = str(result.get("status") or "")
        if status == "verification_inconclusive":
            blockers.append(f"{client_id}:verification_inconclusive")
            continue
        if status == "verification_error":
            blockers.append(f"{client_id}:verification_error")
            continue

        compare_status = str(result.get("compare_status") or "")
        if compare_status and compare_status != "ahead":
            blockers.append(f"{client_id}:history_{compare_status}")
            continue

        brain_paths = [
            str(value)
            for value in (row.get("brain_mutation_contract_paths") or row.get("contract_paths") or [])
            if str(value).strip()
        ]
        hard_hits = [
            str(filename)
            for filename in (result.get("contract_changed_files") or [])
            if path_matches(str(filename), brain_paths)
        ]

        brain_tokens = {
            str(value).casefold()
            for value in (
                row.get("brain_mutation_semantic_tokens")
                or row.get("semantic_review_tokens")
                or []
            )
            if str(value).strip()
        }
        semantic_hits: dict[str, list[str]] = {}
        for filename, hits in (result.get("semantic_token_hits") or {}).items():
            relevant = [
                str(token)
                for token in (hits or [])
                if str(token).casefold() in brain_tokens
            ]
            if relevant:
                semantic_hits[str(filename)] = relevant

        if hard_hits or semantic_hits:
            detail: list[str] = []
            if hard_hits:
                detail.append("paths=" + ",".join(hard_hits[:8]))
            if semantic_hits:
                semantic_detail = ",".join(
                    f"{filename}:{'/'.join(tokens)}"
                    for filename, tokens in list(semantic_hits.items())[:8]
                )
                detail.append("semantic=" + semantic_detail)
            blockers.append(f"{client_id}:provider_contract_drift:" + ";".join(detail))
            continue

        if bool(result.get("review_required")) or client_id in (report.get("review_required") or []):
            reader_pending.append(client_id)

    return blockers, reader_pending


def guard(output: Path) -> dict[str, Any]:
    if os.environ.get("NIAKVIO_SKIP_CLIENT_DRIFT_GUARD", "0").strip() == "1":
        return {"skipped": True, "reason": "explicit_test_override"}

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(CHECKER), "--no-fail", "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    if completed.returncode != 0:
        details = "\n".join(
            part.strip()
            for part in (completed.stdout, completed.stderr)
            if part and part.strip()
        )
        raise RuntimeError(
            "Nuvio client verification failed before provider Brain mutation: "
            + details[-2200:]
        )

    report = load_json(output)
    config = load_json(CONFIG)
    blockers, reader_pending = classify_provider_mutation_compat(report, config)
    if blockers:
        raise RuntimeError(
            "Nuvio client provider contract drift blocks provider Brain mutation: "
            + " | ".join(blockers)
        )

    inconclusive = [str(value) for value in report.get("inconclusive") or [] if str(value)]
    if inconclusive:
        # Defensive redundancy: classify_provider_mutation_compat already blocks each
        # configured inconclusive client, but never let a malformed summary weaken it.
        raise RuntimeError(
            "Nuvio client runtime verification is inconclusive; fail-closed before provider Brain mutation: "
            + ", ".join(inconclusive)
        )

    print(
        "FIELD_NUVIO_CLIENT_BRAIN_COMPAT "
        f"verified={len(report.get('verified') or [])} "
        f"safe_advance={len(report.get('safe_advance_available') or [])} "
        f"reader_reaudit_pending={len(reader_pending)} "
        "provider_contract_blockers=0 provider_mutation_allowed=true"
    )
    if reader_pending:
        print(
            "FIELD_NUVIO_CLIENT_READER_REAUDIT_PENDING clients="
            + ",".join(reader_pending)
            + " provider_mutation_allowed=true native_reader_acceptance_required=true"
        )
    return report


def main() -> int:
    output = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else ROOT / "health-output/nuvio-client-upstream-status.json"
    )
    guard(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
