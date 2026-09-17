#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "assert_active_provider_live_coverage.py"


def run(manifest: dict, report: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        manifest_path = root / "manifest.json"
        report_path = root / "report.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report_path.write_text(json.dumps(report), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--report", str(report_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )


manifest = {
    "scrapers": [
        {"id": "a", "enabled": True},
        {"id": "b", "enabled": True},
        {"id": "c", "enabled": False},
    ]
}
qualified = {
    "providers": [
        {
            "providerId": "a",
            "completionState": "declared-types-qualified",
            "liveValidatedRouteCount": 2,
            "declaredTypeCoverageRatio": 1.0,
            "typeComplete": True,
            "requiredTypes": ["movie", "tv"],
            "validatedTypes": ["movie", "tv"],
            "playableChainValidatedTypes": ["movie", "tv"],
            "missingTypes": [],
            "advancedToNextProvider": True,
            "playableVerified": True,
            "finalBundleVerified": True,
        },
        {
            "providerId": "b",
            "completionState": "direct-output-verified",
            "liveValidatedRouteCount": 0,
            "declaredTypeCoverageRatio": 1.0,
            "typeComplete": True,
            "requiredTypes": ["movie"],
            "validatedTypes": ["movie"],
            "playableChainValidatedTypes": ["movie"],
            "missingTypes": [],
            "advancedToNextProvider": True,
            "playableVerified": True,
            "finalBundleVerified": True,
        },
        {
            "providerId": "c",
            "completionState": "terminal-unreachable",
            "liveValidatedRouteCount": 0,
            "declaredTypeCoverageRatio": 0.0,
            "typeComplete": False,
            "requiredTypes": ["movie"],
            "validatedTypes": [],
            "playableChainValidatedTypes": [],
            "missingTypes": ["movie"],
            "advancedToNextProvider": True,
            "playableVerified": False,
            "finalBundleVerified": False,
        },
    ]
}
result = run(manifest, qualified)
assert result.returncode == 0, result.stdout + result.stderr
assert "active=2 qualified=2 missing=0" in result.stdout, result.stdout
assert "playable_gate=true" in result.stdout, result.stdout

# The exact historical loophole: a provider may traverse every declared route but
# return no playable stream. It must never remain active.
route_only = json.loads(json.dumps(qualified))
route_only["providers"][0]["playableVerified"] = False
route_only["providers"][0]["playableChainValidatedTypes"] = []
result = run(manifest, route_only)
assert result.returncode != 0
assert "qualified=1/2" in (result.stdout + result.stderr)
assert "playable=False" in (result.stdout + result.stderr)

partial_type = json.loads(json.dumps(qualified))
partial_type["providers"][0]["declaredTypeCoverageRatio"] = 0.5
partial_type["providers"][0]["typeComplete"] = False
partial_type["providers"][0]["validatedTypes"] = ["movie"]
partial_type["providers"][0]["playableChainValidatedTypes"] = ["movie"]
partial_type["providers"][0]["missingTypes"] = ["tv"]
result = run(manifest, partial_type)
assert result.returncode != 0
assert "qualified=1/2" in (result.stdout + result.stderr)
assert "missing=tv" in (result.stdout + result.stderr)

blocked_active = json.loads(json.dumps(qualified))
blocked_active["providers"][1]["completionState"] = "terminal-blocked"
blocked_active["providers"][1]["playableVerified"] = False
blocked_active["providers"][1]["playableChainValidatedTypes"] = []
result = run(manifest, blocked_active)
assert result.returncode != 0
assert "qualified=1/2" in (result.stdout + result.stderr)
assert "b: active but not playable-qualified" in (result.stdout + result.stderr)

missing_active = {"providers": [qualified["providers"][0], qualified["providers"][2]]}
result = run(manifest, missing_active)
assert result.returncode != 0
assert "active provider has no sequential live report" in (result.stdout + result.stderr)

current_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
active_count = sum(
    1
    for row in current_manifest.get("scrapers") or []
    if isinstance(row, dict) and row.get("enabled") is not False
)
assert active_count > 0, "current manifest must contain at least one active provider"

print(
    f"Active provider playable coverage tests passed: current active={active_count}; route-only proof is rejected and "
    "every declared semantic lane needs current playable/identity-safe proof."
)
