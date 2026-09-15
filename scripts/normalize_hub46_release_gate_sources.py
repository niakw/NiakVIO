#!/usr/bin/env python3
"""Normalize remaining release-gate sources to the current Hub46 contract.

This is a narrow, idempotent migration for permanent validation code that still
encoded the retired 96-provider publication model. Historical snapshots remain
history; current executable scope is exactly the 46 providers in manifest.json.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: Path, old: str, new: str, label: str, *, all_matches: bool = False) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return False
        raise AssertionError(f"{label}: neither legacy nor normalized shape found")
    updated = text.replace(old, new) if all_matches else text.replace(old, new, 1)
    path.write_text(updated, encoding="utf-8")
    return True


def patch_history_builders() -> bool:
    changed = False
    paths = [
        ROOT / "scripts/build_provider_history_matrix.py",
        ROOT / "scripts/build_provider_history_matrix_v2.py",
        ROOT / "scripts/build_provider_history_matrix_v3.py",
    ]
    for path in paths:
        changed |= replace(path, "EXPECTED = 96", "EXPECTED = 46", f"{path.name} current count")
        text = path.read_text(encoding="utf-8")
        updated = (
            text.replace("96/96", "46 current / 50 historical archive")
            .replace("96-provider matrix", "46-current-provider matrix")
            .replace("96 provider", "46 current provider")
        )
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed = True

    base = paths[0]
    changed |= replace(
        base,
        "    retention = load_json(RETENTION)\n",
        "    retention = load_json(RETENTION) if RETENTION.exists() else {}\n",
        "history retention ledger optional after Hub46 archival split",
    )
    return changed


def patch_route_reconstructor_contract() -> bool:
    path = ROOT / "tests/provider_route_reconstructor_test.py"
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        "# Real 96/96 route-only census: every Provider Object receives the canonical field,",
        "# Real Hub46 route-only census: every current Provider Object receives the canonical field,",
    )
    text = text.replace('assert census["providerCount"] == 96, census', 'assert census["providerCount"] == 46, census')
    text = text.replace('census=96 routes={census[\'routeCount\']}', 'census=46 routes={census[\'routeCount\']}')
    if 'census["providerCount"] == 96' in text:
        raise AssertionError("route reconstructor still contains a 96-provider current census")
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def patch_strategy_plan_contract() -> bool:
    path = ROOT / "tests/provider_v3_strategy_plan_contract_test.py"
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        "    executable_count = 96 - diagnostic_non_executable\n",
        "    executable_count = len(rows) - diagnostic_non_executable\n",
    )
    text = text.replace(
        "    executable_count = 46 - diagnostic_non_executable\n",
        "    executable_count = len(rows) - diagnostic_non_executable\n",
    )
    text = text.replace(
        "    if enabled_count != 46:\n        failures.append(f\"hub46 enabled count mismatch: {enabled_count} != 46\")",
        "    if enabled_count != len(targets):\n        failures.append(f\"active enabled count mismatch: {enabled_count} != {len(targets)}\")",
    )
    if "enabled_count != 46" in text or "enabled=46 disabled=0" in text:
        raise AssertionError("strategy plan still encodes a fixed active-provider count")
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False

def patch_engine_language_contract() -> bool:
    path = ROOT / "engine_v2/src/stream-presentation.mjs"
    old = '  if (/^(?:VF|VFF)$/i.test(explicit || "")) return "VF";\n'
    new = '  if (/^(?:VF|VFF|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS)$/i.test(explicit || "")) return "VF";\n'
    changed = replace(path, old, new, "Engine v2 French/VF normalization")
    text = path.read_text(encoding="utf-8")
    if new not in text:
        raise AssertionError("Engine v2 French/VF normalization missing")
    return changed


def main() -> int:
    changes = {
        "history_builders": patch_history_builders(),
        "route_reconstructor_contract": patch_route_reconstructor_contract(),
        "strategy_plan_contract": patch_strategy_plan_contract(),
        "engine_language_contract": patch_engine_language_contract(),
    }
    print("HUB46_RELEASE_GATE_SOURCE_NORMALIZE " + " ".join(f"{key}={int(value)}" for key, value in changes.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
