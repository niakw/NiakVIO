#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "enforce_route_proof_manifest_policy_v1.py"

import route_proof_activation_preservation_v1 as preservation  # noqa: E402


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def legacy_fallback(record, *, missing: bool):
    return False, "legacy-fallback"


def legacy_disable_record(proven_route_count: object = 0) -> dict[str, object]:
    return {
        "id": "movix",
        "enabled": False,
        "action": preservation.LEGACY_ROUTE_PROOF_DISABLE_ACTION,
        "failed_gates": [preservation.ROUTE_PROOF_FAILED_GATE],
        "evidence": {
            "authority": preservation.ROUTE_PROOF_AUTHORITY,
            "provider_id": "movix",
            "route_proof_version": 5,
            "proven_route_count": proven_route_count,
            "status": "no-proven-route",
        },
    }


with tempfile.TemporaryDirectory(prefix="niakvio-route-policy-") as raw:
    tmp = Path(raw)
    report = tmp / "report.json"
    manifest = tmp / "manifest.json"
    overrides = tmp / "overrides.json"
    health = tmp / "health.json"
    dump(report, {
        "schemaVersion": 5,
        "providers": [{"providerId": "movix", "status": "no-proven-route", "routes": []}],
    })
    dump(manifest, {"scrapers": [{"id": "MOVIX", "enabled": True}, {"id": "KEHFLIX", "enabled": True}]})
    dump(overrides, {
        "provider_patches": {
            "movix": {
                "live_route_gate": {"completion_state": "terminal-blocked"},
                "route_proof": {"provenRouteCount": 0},
                "manifest_overrides": {"supportsExternalPlayer": True, "enabled": False},
            }
        }
    })
    dump(health, {
        "providers": [
            {"id": "movix", "enabled": True, "action": "enabled-current-dns-access-stream-quality-passed", "failed_gates": []},
            {"id": "kehflix", "enabled": True, "action": "enabled-current-dns-access-stream-quality-passed", "failed_gates": []},
        ]
    })
    done = subprocess.run(
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
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    m = json.loads(manifest.read_text(encoding="utf-8"))
    o = json.loads(overrides.read_text(encoding="utf-8"))
    h = json.loads(health.read_text(encoding="utf-8"))
    movix = next(row for row in m["scrapers"] if row["id"] == "MOVIX")
    kehflix = next(row for row in m["scrapers"] if row["id"] == "KEHFLIX")
    health_movix = next(row for row in h["providers"] if str(row.get("id")).casefold() == "movix")
    assert movix["enabled"] is True, movix
    assert kehflix["enabled"] is True, kehflix
    assert "enabled" not in o["provider_patches"]["movix"]["manifest_overrides"]
    assert health_movix["enabled"] is True, health_movix
    assert health_movix["action"] == preservation.ROUTE_PROOF_DIAGNOSTIC_ACTION, health_movix
    assert health_movix["failed_gates"] == [preservation.ROUTE_PROOF_FAILED_GATE], health_movix
    evidence = health_movix.get("evidence") or {}
    assert evidence.get("authority") == preservation.ROUTE_PROOF_AUTHORITY, evidence
    assert evidence.get("route_proof_version") == 5, evidence
    assert evidence.get("proven_route_count") == 0, evidence
    assert evidence.get("status") == "no-proven-route", evidence
    assert evidence.get("activation_destructive") is False, evidence

    diagnostic = preservation.conclusive_disablement_with_route_proof(
        legacy_fallback, health_movix, missing=False
    )
    assert diagnostic[0] is False and "may_not_disable" in diagnostic[1], diagnostic

    legacy = preservation.conclusive_disablement_with_route_proof(
        legacy_fallback, legacy_disable_record(), missing=False
    )
    assert legacy[0] is False and "forbidden_force_all_enabled" in legacy[1], legacy

with tempfile.TemporaryDirectory(prefix="niakvio-route-policy-positive-") as raw:
    tmp = Path(raw)
    report = tmp / "report.json"
    manifest = tmp / "manifest.json"
    overrides = tmp / "overrides.json"
    health = tmp / "health.json"
    dump(report, {
        "schemaVersion": 5,
        "providers": [{"providerId": "movix", "status": "proven", "routes": ["/api/swiftflow/movie/{id}"]}],
    })
    dump(manifest, {"scrapers": [{"id": "MOVIX", "enabled": False}]})
    dump(overrides, {"provider_patches": {"movix": {"route_proof": {"provenRouteCount": 1}, "manifest_overrides": {"enabled": False}}}})
    dump(health, {"providers": [legacy_disable_record()]})
    done = subprocess.run(
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
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    m = json.loads(manifest.read_text(encoding="utf-8"))
    o = json.loads(overrides.read_text(encoding="utf-8"))
    h = json.loads(health.read_text(encoding="utf-8"))
    movix = m["scrapers"][0]
    health_movix = h["providers"][0]
    assert movix["enabled"] is False, "route proof must preserve activation rather than own it"
    assert "enabled" not in o["provider_patches"]["movix"]["manifest_overrides"]
    assert health_movix["enabled"] is False, health_movix
    assert health_movix["action"] == "route-proof-present-preserve-activation", health_movix
    assert preservation.ROUTE_PROOF_FAILED_GATE not in (health_movix.get("failed_gates") or []), health_movix
    evidence = health_movix.get("evidence") or {}
    assert evidence.get("proven_route_count") == 1, health_movix
    assert evidence.get("activation_destructive") is False, health_movix

print("route-proof diagnostic-only activation policy tests passed: manifest+override+health+force-ON preservation")
