#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "enforce_route_proof_manifest_policy_v1.py"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    report = root / "report.json"
    manifest = root / "manifest.json"
    overrides = root / "overrides.json"
    health = root / "health.json"

    report.write_text(json.dumps({
        "providers": [{"providerId": "anime-sama", "status": "proven", "routes": ["/catalogue/?search={query}"]}]
    }), encoding="utf-8")
    manifest.write_text(json.dumps({
        "scrapers": [{"id": "anime-sama", "enabled": True}]
    }), encoding="utf-8")
    overrides.write_text(json.dumps({
        "provider_patches": {"anime-sama": {"manifest_overrides": {"enabled": True}}}
    }), encoding="utf-8")
    health.write_text(json.dumps({"providers": []}), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--report", str(report),
            "--manifest", str(manifest),
            "--overrides", str(overrides),
            "--health-report", str(health),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "movix_current=false" in proc.stdout, proc.stdout
    assert json.loads(manifest.read_text(encoding="utf-8"))["scrapers"][0]["enabled"] is True
    assert json.loads(overrides.read_text(encoding="utf-8"))["provider_patches"]["anime-sama"]["manifest_overrides"]["enabled"] is True

print("route-proof manifest policy current-scope test passed: archived Movix cannot block current catalogue")
