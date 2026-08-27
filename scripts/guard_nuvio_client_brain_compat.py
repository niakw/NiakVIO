#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Nuvio client compatibility guard before provider Brain mutation.

The full upstream checker remains stricter than this guard: reader/UI/player
changes still require native reader re-audit. A linear upstream
``contract_review_required`` is an adaptation signal, not a pipeline veto: Quick
and Deep exercise NiakVIO's version-adaptive layers against the latest official
client contract and retain the exact changed paths/tokens for native review.

We still fail closed when the upstream state itself cannot be established
(verification error/inconclusive) or when history diverges. In those cases there
is no trustworthy version to adapt against.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
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
    """Return (unverifiable blockers, linear adaptation/re-audit pending clients).

    A known linear HEAD with provider-contract changes is safe to *exercise* via
    the adaptive NiakVIO layers. It remains pending native proof, but it must not
    make Quick/Deep red before that proof can even be produced. Only states where
    the target revision itself is unknown/untrustworthy remain blocking.
    """
    blockers: list[str] = []
    adaptation_pending: list[str] = []
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

        # Linear provider-contract drift is adaptation work, not an inability to
        # establish the target runtime. Keep it visible and require native proof,
        # while allowing the adaptive provider pipeline to exercise the new HEAD.
        if hard_hits or semantic_hits:
            adaptation_pending.append(client_id)
            continue

        if bool(result.get("review_required")) or client_id in (report.get("review_required") or []):
            adaptation_pending.append(client_id)

    return blockers, sorted(set(adaptation_pending))


def guard(output: Path) -> dict[str, Any]:
    if os.environ.get("NIAKVIO_SKIP_CLIENT_DRIFT_GUARD", "0").strip() == "1":
        return {"skipped": True, "reason": "explicit_test_override"}

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] | None = None
    for attempt in range(1, 4):
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
        candidate = load_json(output)
        transient = [
            str(client_id)
            for client_id, row in (candidate.get("clients") or {}).items()
            if isinstance(row, dict)
            and str(row.get("status") or "")
            in {"verification_error", "verification_inconclusive"}
        ]
        if transient and attempt < 3:
            print(
                "FIELD_NUVIO_CLIENT_VERIFY_RETRY "
                f"attempt={attempt} clients={','.join(sorted(transient))}"
            )
            time.sleep(attempt * 2)
            continue
        report = candidate
        break

    if report is None:
        raise RuntimeError("Nuvio client verification produced no usable report")

    config = load_json(CONFIG)
    blockers, adaptation_pending = classify_provider_mutation_compat(report, config)
    if blockers:
        raise RuntimeError(
            "Nuvio client state cannot be established safely for adaptive provider repair: "
            + " | ".join(blockers)
        )

    inconclusive = [str(value) for value in report.get("inconclusive") or [] if str(value)]
    if inconclusive:
        # Defensive redundancy: classification above blocks each configured
        # inconclusive client; never let a malformed summary weaken that fence.
        raise RuntimeError(
            "Nuvio client runtime verification is inconclusive; target revision cannot be adapted safely: "
            + ", ".join(inconclusive)
        )

    print(
        "FIELD_NUVIO_CLIENT_BRAIN_COMPAT "
        f"verified={len(report.get('verified') or [])} "
        f"safe_advance={len(report.get('safe_advance_available') or [])} "
        f"adaptation_pending={len(adaptation_pending)} "
        "unverifiable_blockers=0 provider_mutation_allowed=true"
    )
    if adaptation_pending:
        print(
            "FIELD_NUVIO_CLIENT_ADAPTATION_PENDING clients="
            + ",".join(adaptation_pending)
            + " contract_review_blocking=false provider_mutation_allowed=true "
              "native_reader_acceptance_required=true compatibility_proposal_on_adaptation_failure=true"
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
