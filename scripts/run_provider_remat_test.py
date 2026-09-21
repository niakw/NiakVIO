#!/usr/bin/env python3
"""Ephemeral Provider v3 rematerialization + current-byte retest lane.

This lane answers a narrow question: does the current structured Provider DATA
rebuild into better/different executable bytes? It never runs Brain Repair,
route recovery, WAF discovery, or publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import run_provider_retest as retest  # noqa: E402

STATUS = ROOT / "automation" / "provider-census-status.json"
AUTHORITY = ROOT / "automation" / "provider-authority-status.json"
MANIFEST = ROOT / "manifest.json"
REPORT = ROOT / "automation" / "provider-remat-test-latest.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def run(*args: str) -> None:
    print("FIELD_PROVIDER_REMAT_TEST_CMD " + " ".join(args), flush=True)
    subprocess.run(list(args), cwd=ROOT, env=os.environ.copy(), check=True)


def manifest_rows() -> dict[str, dict[str, Any]]:
    manifest = load(MANIFEST)
    return {
        cid(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }


def byte_state(provider: str, rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = rows.get(provider) or {}
    rel = str(row.get("filename") or "")
    path = ROOT / rel
    raw = path.read_bytes() if rel and path.is_file() else b""
    return {
        "provider": provider,
        "filename": rel,
        "sha256": hashlib.sha256(raw).hexdigest() if raw else "",
        "size": len(raw),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rematerialize current Provider DATA then retest exact bytes")
    parser.add_argument("--scope", choices=("non-full", "repair", "all"), default="non-full")
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--output", type=Path, default=REPORT)
    args = parser.parse_args()

    run(sys.executable, "scripts/classify_provider_authority.py")
    status = load(STATUS)
    authority = load(AUTHORITY)
    requested = {cid(value) for value in args.provider if cid(value)}
    selected = retest.select_providers(
        status,
        authority,
        scope=args.scope,
        requested=requested,
        include_disabled=args.include_disabled,
    )
    if not selected:
        payload = {
            "schemaVersion": 1,
            "scope": args.scope,
            "selectedProviders": [],
            "changedByteProviders": [],
            "message": "no providers selected",
        }
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"FIELD_PROVIDER_REMAT_TEST_EMPTY scope={args.scope}", flush=True)
        return 0

    before_rows = manifest_rows()
    before = {provider: byte_state(provider, before_rows) for provider in selected}

    for provider in selected:
        run(sys.executable, "scripts/materialize_provider_v3_one.py", provider)

    after_rows = manifest_rows()
    after = {provider: byte_state(provider, after_rows) for provider in selected}
    changed = sorted(
        provider
        for provider in selected
        if before[provider]["sha256"] != after[provider]["sha256"]
        or before[provider]["filename"] != after[provider]["filename"]
    )

    retest_cmd = [sys.executable, "scripts/run_provider_retest.py", "--scope", "all"]
    for provider in selected:
        retest_cmd.extend(["--provider", provider])
    run(*retest_cmd)

    refreshed = load(STATUS)
    status_by_provider = {
        cid(row.get("provider")): str(row.get("status") or "")
        for row in refreshed.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }
    payload = {
        "schemaVersion": 1,
        "scope": args.scope,
        "sourceCensusRunId": status.get("runId"),
        "selectedProviders": selected,
        "providerCount": len(selected),
        "changedByteProviders": changed,
        "changedByteProviderCount": len(changed),
        "before": before,
        "after": after,
        "statusesAfterRemat": {
            provider: status_by_provider.get(provider, "missing")
            for provider in selected
        },
        "repairQueueAfterRemat": list(refreshed.get("repairQueue") or []),
        "publicationAllowed": False,
        "publicationPolicy": (
            "ephemeral rematerialization diagnostic only; publish only through the "
            "owning Domain/Repair transaction after independent current-byte proof"
        ),
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_REMAT_TEST_DONE "
        f"providers={len(selected)} changed_bytes={len(changed)} "
        f"repair_queue={len(refreshed.get('repairQueue') or [])}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
