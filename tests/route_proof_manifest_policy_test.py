#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "enforce_route_proof_manifest_policy_v1.py"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


with tempfile.TemporaryDirectory(prefix="niakvio-route-policy-") as raw:
    tmp = Path(raw)
    report = tmp / "report.json"
    manifest = tmp / "manifest.json"
    overrides = tmp / "overrides.json"
    dump(report, {"providers": [{"providerId": "movix", "status": "no-proven-route", "routes": []}]})
    dump(manifest, {"scrapers": [{"id": "MOVIX", "enabled": True}, {"id": "KEHFLIX", "enabled": True}]})
    dump(overrides, {
        "provider_patches": {
            "movix": {
                "live_route_gate": {"completion_state": "terminal-blocked"},
                "route_proof": {"provenRouteCount": 0},
                "manifest_overrides": {"supportsExternalPlayer": True},
            }
        }
    })
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--report", str(report), "--manifest", str(manifest), "--overrides", str(overrides)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    m = json.loads(manifest.read_text(encoding="utf-8"))
    o = json.loads(overrides.read_text(encoding="utf-8"))
    movix = next(row for row in m["scrapers"] if row["id"] == "MOVIX")
    kehflix = next(row for row in m["scrapers"] if row["id"] == "KEHFLIX")
    assert movix["enabled"] is False, movix
    assert kehflix["enabled"] is True, kehflix
    assert o["provider_patches"]["movix"]["manifest_overrides"]["enabled"] is False

with tempfile.TemporaryDirectory(prefix="niakvio-route-policy-positive-") as raw:
    tmp = Path(raw)
    report = tmp / "report.json"
    manifest = tmp / "manifest.json"
    overrides = tmp / "overrides.json"
    dump(report, {"providers": [{"providerId": "movix", "status": "proven", "routes": ["/api/swiftflow/movie/{id}"]}]})
    dump(manifest, {"scrapers": [{"id": "MOVIX", "enabled": False}]})
    dump(overrides, {"provider_patches": {"movix": {"route_proof": {"provenRouteCount": 1}}}})
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--report", str(report), "--manifest", str(manifest), "--overrides", str(overrides)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    m = json.loads(manifest.read_text(encoding="utf-8"))
    movix = m["scrapers"][0]
    assert movix["enabled"] is False, "positive proof must not auto-enable production"

print("route-proof manifest activation policy tests passed")
