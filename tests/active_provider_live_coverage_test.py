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
            "missingTypes": [],
            "advancedToNextProvider": True,
            "playableVerified": False,
        },
        {
            "providerId": "b",
            "completionState": "direct-output-verified",
            "liveValidatedRouteCount": 0,
            "declaredTypeCoverageRatio": 1.0,
            "typeComplete": True,
            "requiredTypes": ["movie"],
            "validatedTypes": ["movie"],
            "missingTypes": [],
            "advancedToNextProvider": True,
            "playableVerified": True,
        },
        {
            "providerId": "c",
            "completionState": "terminal-unreachable",
            "liveValidatedRouteCount": 0,
            "declaredTypeCoverageRatio": 0.0,
            "typeComplete": False,
            "requiredTypes": ["movie"],
            "validatedTypes": [],
            "missingTypes": ["movie"],
            "advancedToNextProvider": True,
            "playableVerified": False,
        },
    ]
}
result = run(manifest, qualified)
assert result.returncode == 0, result.stdout + result.stderr
assert "active=2 qualified=2 missing=0" in result.stdout, result.stdout
assert "declared_type_gate=1.000" in result.stdout, result.stdout

partial_type = json.loads(json.dumps(qualified))
partial_type["providers"][0]["declaredTypeCoverageRatio"] = 0.5
partial_type["providers"][0]["typeComplete"] = False
partial_type["providers"][0]["validatedTypes"] = ["movie"]
partial_type["providers"][0]["missingTypes"] = ["tv"]
result = run(manifest, partial_type)
assert result.returncode != 0
assert "qualified=1/2" in (result.stdout + result.stderr)
assert "missing=tv" in (result.stdout + result.stderr)

blocked_active = json.loads(json.dumps(qualified))
blocked_active["providers"][1]["completionState"] = "terminal-blocked"
blocked_active["providers"][1]["playableVerified"] = False
result = run(manifest, blocked_active)
assert result.returncode != 0
assert "qualified=1/2" in (result.stdout + result.stderr)
assert "b: active but not declared-type live-qualified" in (result.stdout + result.stderr)

missing_active = {"providers": [qualified["providers"][0], qualified["providers"][2]]}
result = run(manifest, missing_active)
assert result.returncode != 0
assert "active provider has no sequential live report" in (result.stdout + result.stderr)

current_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
active_count = sum(1 for row in current_manifest.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is not False)
assert active_count == 63, f"current branch expected 63 active providers, got {active_count}"

print(
    "Active provider live coverage tests passed: current active=63, publication requires 63/63 active providers, "
    "and each active provider must prove 100% of its declared semantic types."
)
