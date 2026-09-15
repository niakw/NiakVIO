#!/usr/bin/env python3
"""Repair source-generation quoting after the Active44 one-shot migration.

This is deliberately narrow: the original migration uses regex replacement for two
whole Python functions, where replacement-string backslash processing can turn a
literal ``\\n`` into an actual newline inside a quoted string. Rebuild those two
functions by source slicing so the resulting modules are valid Python.
"""
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


def main() -> int:
    fix_hub_activation_publication()
    fix_release_normalizer()
    print("ACTIVE44_GENERATED_SOURCE_FIX_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
