#!/usr/bin/env python3
"""Repair generated sources and compatibility tests after the Active44 migration."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_function(path: Path, start_name: str, next_name: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.find(f"def {start_name}(")
    end = text.find(f"\ndef {next_name}(", start + 1)
    if start < 0 or end < 0:
        raise SystemExit(f"{path}: cannot locate {start_name}->{next_name}")
    updated = text[:start] + body.rstrip() + "\n\n" + text[end + 1 :]
    path.write_text(updated, encoding="utf-8")


def fix_hub_activation_publication() -> None:
    path = ROOT / "scripts/hub_activation_publication.py"
    body = r'''def append_memory(scope: dict) -> None:
    memory = ROOT / "MEMORY.md"
    text = memory.read_text(encoding="utf-8")
    marker = "## 2026-09-15 — active matrix publication authority"
    if marker in text:
        return
    block = f"""\n\n{marker}\n\n- Recoverable catalogue census: **{scope['catalogueProviderCount']}**.\n- Executable/visible providers: **{scope['enabledProviderCount']}**, owned by `automation/evidence/hub-lab-matrix-46.json`.\n- Disabled providers: **{scope['disabledProviderCount']}**. `official_hub` is discovery/address metadata only and cannot activate a provider.\n- Explicit manual OFF states remain disabled until separately re-authorized; Repair/Learn must not target them automatically.\n"""
    memory.write_text(text.rstrip() + block + "\n", encoding="utf-8")'''
    replace_function(path, "append_memory", "main", body)


def fix_release_normalizer() -> None:
    path = ROOT / "scripts/normalize_hub46_release_gate_sources.py"
    body = r'''def patch_strategy_plan_contract() -> bool:
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
    return False'''
    replace_function(path, "patch_strategy_plan_contract", "patch_engine_language_contract", body)


def fix_repair_contract_compatibility() -> None:
    """Teach the wrapper about the current V21.12 boundary without editing history."""
    path = ROOT / "tests/provider_repair_pipeline_v6_contract_test.py"
    text = path.read_text(encoding="utf-8")
    marker = "ACTIVE44_REPAIR_V21_12_COMPAT"
    if marker in text:
        return
    anchor = "# Activation is now an exact release authority:"
    pos = text.find(anchor)
    if pos < 0:
        raise SystemExit("repair contract compatibility insertion anchor missing")
    block = r'''# ACTIVE44_REPAIR_V21_12_COMPAT
# V21.10's provider-specific VoirAnime authority is historical evidence only.
# The canonical current Repair boundary intentionally skips replaying it and
# proceeds V21.9 -> V21.11 retirement -> V21.12 generic reconstruction.
legacy_v21_10 = "    'scripts/upgrade_provider_voiranime_homes_authority_v21_10.py',\n"
legacy_v21_10_test = "    'tests/provider_voiranime_homes_authority_v21_10_test.py',\n"
if legacy_v21_10 not in source:
    raise AssertionError("repair contract no longer contains expected historical V21.10 assertion")
source = source.replace(legacy_v21_10, "")
source = source.replace(legacy_v21_10_test, "")
v21_11 = "    'scripts/retire_provider_neko_sama_v21_11.py',\n"
v21_12 = "    'scripts/upgrade_provider_runtime_reconstruction_v21_12.py',\n"
source = source.replace(v21_11, v21_11 + v21_12)
source = source.replace(
    "assert '\"routePlanRevision\": \"v21.11\"' in pipeline",
    "assert '\"routePlanRevision\": \"v21.12\"' in pipeline",
)
source = source.replace(
    "V15->V16->V17->V21.9->V21.10->V21.11 order",
    "V15->V16->V17->V21.9->V21.11->V21.12 order",
)

'''
    text = text[:pos] + block + text[pos:]
    path.write_text(text, encoding="utf-8")


def main() -> int:
    fix_hub_activation_publication()
    fix_release_normalizer()
    fix_repair_contract_compatibility()
    print("ACTIVE44_GENERATED_SOURCE_FIX_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
