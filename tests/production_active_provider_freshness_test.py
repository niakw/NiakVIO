#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")

status = json.loads((ROOT / "automation/provider-census-status.json").read_text(encoding="utf-8"))
proof = {canon(row.get("provider")): row for row in status.get("providers") or [] if isinstance(row, dict)}

for manifest_path in (ROOT / "manifest.json", ROOT / "vf" / "manifest.json"):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    active = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is not False]
    for row in active:
        pid = canon(row.get("id"))
        assert pid, (manifest_path, row)
        evidence = proof.get(pid)
        assert evidence is not None, f"{manifest_path}: active {pid} missing from current census"
        assert evidence.get("status") == "FULL OK", (manifest_path, pid, evidence.get("status"))
        assert evidence.get("testedThisRun") is True, f"{manifest_path}: active {pid} is carried-only"
        declared = set(row.get("canonicalSupportedTypes") or row.get("supportedTypes") or [])
        verified = set(evidence.get("currentVerifiedLanes") or [])
        assert declared <= verified, (manifest_path, pid, sorted(declared), sorted(verified))
        assert evidence.get("repairEligible") is not True, f"{manifest_path}: active {pid} remains repair-eligible"

print("Production active providers require fresh FULL OK evidence")
