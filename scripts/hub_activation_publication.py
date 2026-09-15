#!/usr/bin/env python3
"""Validate/persist active-matrix publication state.

This helper never discovers hubs and never repairs providers. It only projects the
active provider matrix authority into a durable scope,
verifies the rendered catalogue, and appends a recovery checkpoint when asked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 46
MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def active_scope() -> set[str]:
    matrix = load("automation/evidence/hub-lab-matrix-46.json")
    ids = {cid(row.get("manifestId") or row.get("provider")) for row in matrix.get("rows") or [] if isinstance(row, dict) and cid(row.get("manifestId") or row.get("provider"))}
    declared = int(matrix.get("hubCount") or 0)
    assert declared > 0 and len(ids) == declared, (declared, len(ids))
    return ids


def compute_scope() -> dict:
    manifest = load("manifest.json")
    overrides = load("provider-overrides.json")
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    assert len(rows) == EXPECTED, len(rows)
    targets = active_scope()
    enabled, disabled = [], []
    for row in rows:
        pid = cid(row.get("id"))
        patch = patches.get(pid) if isinstance(patches.get(pid), dict) else {}
        expected = pid in targets
        assert bool(row.get("enabled")) is expected, (pid, row.get("enabled"), expected)
        mo = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        assert bool(mo.get("enabled")) is expected, (pid, mo.get("enabled"), expected)
        (enabled if expected else disabled).append(pid)
    assert enabled and len(enabled) < EXPECTED
    return {
        "schemaVersion": 1,
        "authority": "automation/evidence/hub-lab-matrix-46.json:rows[].manifestId",
        "catalogueProviderCount": EXPECTED,
        "enabledProviderCount": len(enabled),
        "disabledProviderCount": len(disabled),
        "enabledProviders": sorted(enabled),
        "disabledProviders": sorted(disabled),
        "repairScope": "declared-hub-providers-only",
        "nativeLabPolicy": "reuse-existing-artifacts-first; rerun-only-for-specific-fix-validation",
    }


def write_scope(scope: dict) -> None:
    target = ROOT / "automation/hub-activation-scope.json"
    target.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_catalog(scope: dict) -> None:
    catalog = load("provider_catalog.json")
    overrides = load("provider-overrides.json")
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    actual = []
    providers = catalog.get("providers") or []
    assert len(providers) == EXPECTED, len(providers)
    for row in providers:
        scraper = row.get("scraper") or {}
        pid = cid(row.get("canonicalId") or scraper.get("id"))
        patch = patches.get(pid) if isinstance(patches.get(pid), dict) else {}
        expected = pid in set(scope["enabledProviders"])
        assert bool(scraper.get("enabled")) == expected, (pid, scraper.get("enabled"), expected)
        if scraper.get("enabled"):
            actual.append(pid)
    assert sorted(actual) == sorted(scope["enabledProviders"]), (actual, scope["enabledProviders"])


def append_memory(scope: dict) -> None:
    memory = ROOT / "MEMORY.md"
    text = memory.read_text(encoding="utf-8")
    marker = "## 2026-09-15 — active matrix publication authority"
    if marker in text:
        return
    block = f"""\n\n{marker}\n\n- Recoverable catalogue census: **{scope['catalogueProviderCount']}**.\n- Executable/visible providers: **{scope['enabledProviderCount']}**, owned by `automation/evidence/hub-lab-matrix-46.json`.\n- Disabled providers: **{scope['disabledProviderCount']}**. `official_hub` is discovery/address metadata only and cannot activate a provider.\n- Explicit manual OFF states remain disabled until separately re-authorized; Repair/Learn must not target them automatically.\n"""
    memory.write_text(text.rstrip() + block + "\n", encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-scope", action="store_true")
    ap.add_argument("--verify-catalog", action="store_true")
    ap.add_argument("--append-memory", action="store_true")
    args = ap.parse_args()
    scope = compute_scope()
    if args.write_scope:
        write_scope(scope)
    if args.verify_catalog:
        verify_catalog(scope)
    if args.append_memory:
        append_memory(scope)
    print("HUB_ACTIVATION_SCOPE", f"enabled={scope['enabledProviderCount']}", f"disabled={scope['disabledProviderCount']}", ",".join(scope["enabledProviders"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
