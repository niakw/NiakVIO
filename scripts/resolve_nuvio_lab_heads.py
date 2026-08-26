#!/usr/bin/env python3
"""Resolve exact latest official Nuvio client revisions for native Labs.

The upstream drift checker remains the authority for contract/semantic audit, but
``contract_review_required`` is deliberately *not* a Lab veto. Labs always exercise
the latest resolved official HEAD and let NiakVIO's version-adaptive preparation
layer prove whether our harness still fits that client revision. Only an unresolved
HEAD is fatal here; an older accepted ref is never used as a silent fallback.
Desktop reader/canary consumers intentionally share this resolver so their final
proofs are tied to the same official client-revision policy as the Core audit.
That shared resolution is also the final cross-workflow checkpoint after repository
hygiene consolidation, so native proofs never silently target a stale accepted ref.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CLIENT_OUTPUTS = {
    "nuvio-tv": "tv",
    "nuvio-mobile": "mobile",
    "nuvio-desktop": "desktop",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def safe_sha(value: Any, label: str) -> str:
    text = str(value or "").strip().lower()
    if len(text) != 40 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label}: latest official HEAD is unresolved ({text!r}); refusing stale fallback")
    return text


def clean(value: Any, limit: int = 128) -> str:
    text = str(value or "").strip().replace("\n", " ").replace("\r", " ")
    return text[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--clients", nargs="+", choices=sorted(CLIENT_OUTPUTS), required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = load(args.report)
    clients = report.get("clients") if isinstance(report.get("clients"), dict) else {}
    outputs: dict[str, str] = {}
    fingerprint_parts: list[str] = []
    resolved: dict[str, Any] = {}

    for client_id in args.clients:
        row = clients.get(client_id)
        if not isinstance(row, dict):
            raise ValueError(f"{client_id}: missing from upstream drift report")
        prefix = CLIENT_OUTPUTS[client_id]
        head = safe_sha(row.get("current_head"), client_id)
        accepted = clean(row.get("accepted_ref"), 40)
        contract = clean(row.get("contract_ref") or row.get("verified_ref"), 40)
        status = clean(row.get("status"), 96) or "unknown"
        adaptation_required = status == "contract_review_required" or bool(row.get("review_required"))
        outputs[f"{prefix}_sha"] = head
        outputs[f"{prefix}_accepted_ref"] = accepted
        outputs[f"{prefix}_contract_ref"] = contract
        outputs[f"{prefix}_drift_status"] = status
        outputs[f"{prefix}_adaptation_required"] = str(adaptation_required).lower()
        outputs[f"{prefix}_lab_blocking"] = "false"
        fingerprint_parts.append(f"{prefix}={head}")
        resolved[client_id] = {
            "head": head,
            "acceptedRef": accepted or None,
            "contractRef": contract or None,
            "driftStatus": status,
            "reviewRequired": bool(row.get("review_required")),
            "adaptationRequired": adaptation_required,
            "labBlocking": False,
            "adaptationPolicy": "latest-head-version-adaptive-preparation",
        }

    fingerprint = ";".join(fingerprint_parts)
    outputs["runtime_fingerprint"] = fingerprint
    payload = {
        "schemaVersion": 2,
        "policy": (
            "latest-official-head-for-labs; contract_review_required is observational/nonblocking; "
            "run version-adaptive NiakVIO preparation on that HEAD; promote compatibility after proof; "
            "open a NiakVIO compatibility proposal only when adaptation itself fails; no stale fallback"
        ),
        "runtimeFingerprint": fingerprint,
        "clients": resolved,
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            for key, value in outputs.items():
                handle.write(f"{key}={value}\n")

    for client_id, row in resolved.items():
        print(
            f"FIELD_NUVIO_LAB_HEAD client={client_id} head={row['head'][:12]} "
            f"accepted={(row['acceptedRef'] or '-')[:12]} contract={(row['contractRef'] or '-')[:12]} "
            f"status={row['driftStatus']} adaptation_required={str(row['adaptationRequired']).lower()} "
            "lab_blocking=false"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
