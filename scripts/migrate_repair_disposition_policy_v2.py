#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINALIZER = ROOT / "scripts" / "finalize_provider_repair_disposition_v1.py"
STRATEGY = ROOT / "tests" / "provider_v3_strategy_plan_contract_test.py"
CONTRACT = ROOT / "tests" / "provider_repair_pipeline_v6_contract_test.py"


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    if old not in text:
        raise SystemExit(f"{label}: source anchor missing in {path.relative_to(ROOT)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> int:
    changed: list[str] = []

    old = '''        if complete and not quarantined:\n            route_state = "on"\n            reason_codes = ["all_declared_lanes_live_proven"]\n            # Do not override a deliberate disabled state owned elsewhere. This\n            # finalizer is authoritative for disabling broken providers, not for\n            # bypassing promotion/quarantine policy.\n            enabled = manifest_row.get("enabled") is not False\n'''
    new = '''        if complete and not quarantined:\n            route_state = "on"\n            reason_codes = ["all_declared_lanes_live_proven"]\n            # Repair disposition is the activation authority for this candidate:\n            # complete live proof restores execution, while incomplete proof is\n            # disabled below as explicit repair/off debt. A stale historical\n            # enabled=false must not keep a fully recovered provider disabled.\n            enabled = True\n'''
    if replace_once(FINALIZER, old, new, "complete proof reactivation"):
        changed.append(str(FINALIZER.relative_to(ROOT)))

    old = '''def repair_evidence_ok(patch: dict) -> bool:\n    disposition = patch.get("repair_disposition") if isinstance(patch.get("repair_disposition"), dict) else {}\n    if disposition.get("authority") != "provider-repair-disposition-v1":\n        return False\n    if disposition.get("activationState") != "disabled" or disposition.get("routeDataState") != "repair":\n        return False\n    missing = disposition.get("missingLanes") if isinstance(disposition.get("missingLanes"), list) else []\n    reasons = disposition.get("reasonCodes") if isinstance(disposition.get("reasonCodes"), list) else []\n    if not missing or not reasons:\n        return False\n    if disposition.get("completeCapabilityProof") is not False:\n        return False\n    return True\n\n\ndef main() -> int:\n'''
    new = '''def repair_evidence_ok(patch: dict) -> bool:\n    disposition = patch.get("repair_disposition") if isinstance(patch.get("repair_disposition"), dict) else {}\n    if disposition.get("authority") != "provider-repair-disposition-v1":\n        return False\n    if disposition.get("activationState") != "disabled" or disposition.get("routeDataState") != "repair":\n        return False\n    missing = disposition.get("missingLanes") if isinstance(disposition.get("missingLanes"), list) else []\n    reasons = disposition.get("reasonCodes") if isinstance(disposition.get("reasonCodes"), list) else []\n    if not missing or not reasons:\n        return False\n    if disposition.get("completeCapabilityProof") is not False:\n        return False\n    return True\n\n\ndef off_evidence_ok(patch: dict) -> bool:\n    disposition = patch.get("repair_disposition") if isinstance(patch.get("repair_disposition"), dict) else {}\n    if disposition.get("authority") != "provider-repair-disposition-v1":\n        return False\n    if disposition.get("activationState") != "disabled" or disposition.get("routeDataState") != "off":\n        return False\n    reasons = disposition.get("reasonCodes") if isinstance(disposition.get("reasonCodes"), list) else []\n    if not reasons or disposition.get("completeCapabilityProof") is not False:\n        return False\n    terminal = str(disposition.get("terminalState") or "").strip().casefold()\n    quarantined = disposition.get("quarantined") is True\n    return quarantined or terminal in TERMINAL_DISABLED\n\n\ndef main() -> int:\n'''
    if replace_once(STRATEGY, old, new, "off disposition evidence"):
        changed.append(str(STRATEGY.relative_to(ROOT)))

    old = '''    repair_audited: list[str] = []\n\n    for row, provider_id in zip(rows, ids):\n'''
    new = '''    repair_audited: list[str] = []\n    off_audited: list[str] = []\n\n    for row, provider_id in zip(rows, ids):\n'''
    replace_once(STRATEGY, old, new, "off audited list")

    old = '''            if not enabled and state in TERMINAL_DISABLED and terminal_evidence_ok(model, patch, state):\n                terminal_audited.append(provider_id)\n                continue\n            if not enabled and repair_evidence_ok(patch):\n                repair_audited.append(provider_id)\n                continue\n'''
    new = '''            if not enabled and state in TERMINAL_DISABLED and terminal_evidence_ok(model, patch, state):\n                terminal_audited.append(provider_id)\n                continue\n            if not enabled and off_evidence_ok(patch):\n                off_audited.append(provider_id)\n                continue\n            if not enabled and repair_evidence_ok(patch):\n                repair_audited.append(provider_id)\n                continue\n'''
    replace_once(STRATEGY, old, new, "off strategy acceptance")

    old = '''    executable_count = 96 - len(quarantined) - len(terminal_audited) - len(repair_audited)\n    print(\n        "PROVIDER_V3_STRATEGY_PLAN_OK "\n        f"providers=96 executable={executable_count} quarantined={len(quarantined)} "\n        f"terminal_disabled={len(terminal_audited)} repair_disabled={len(repair_audited)} "\n'''
    new = '''    executable_count = 96 - len(quarantined) - len(terminal_audited) - len(off_audited) - len(repair_audited)\n    print(\n        "PROVIDER_V3_STRATEGY_PLAN_OK "\n        f"providers=96 executable={executable_count} quarantined={len(quarantined)} "\n        f"terminal_disabled={len(terminal_audited)} off_disabled={len(off_audited)} repair_disabled={len(repair_audited)} "\n'''
    replace_once(STRATEGY, old, new, "off strategy summary")

    old = '''finalizer = (ROOT / 'scripts/finalize_provider_repair_disposition_v1.py').read_text(encoding='utf-8')\nupgrade ='''
    new = '''finalizer = (ROOT / 'scripts/finalize_provider_repair_disposition_v1.py').read_text(encoding='utf-8')\nstrategy_contract = (ROOT / 'tests/provider_v3_strategy_plan_contract_test.py').read_text(encoding='utf-8')\nupgrade ='''
    if replace_once(CONTRACT, old, new, "strategy contract ownership"):
        changed.append(str(CONTRACT.relative_to(ROOT)))

    old = '''    'route_state = "repair"',\n    'manifest_row["enabled"] = enabled',\n'''
    new = '''    'route_state = "repair"',\n    'enabled = True',\n    'manifest_row["enabled"] = enabled',\n'''
    replace_once(CONTRACT, old, new, "complete proof static guard")

    old = '''    assert marker in finalizer, marker\n\nassert 'raw_providers' in portfolio_compare\n'''
    new = '''    assert marker in finalizer, marker\n\nfor marker in (\n    'def off_evidence_ok(patch: dict) -> bool:',\n    'disposition.get("routeDataState") != "off"',\n    'quarantined or terminal in TERMINAL_DISABLED',\n    'off_audited.append(provider_id)',\n):\n    assert marker in strategy_contract, marker\n\nassert 'raw_providers' in portfolio_compare\n'''
    replace_once(CONTRACT, old, new, "off evidence static guard")

    print("REPAIR_DISPOSITION_POLICY_V2 changed=" + (",".join(changed) if changed else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
