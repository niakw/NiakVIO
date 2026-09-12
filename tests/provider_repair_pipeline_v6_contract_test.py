#!/usr/bin/env python3
"""Compatibility-aware entrypoint for the canonical Repair V6 static contract.

The durable implementation test is preserved byte-identically. Repair gate
entrypoints may now wrap their implementation modules so stream-level acceptance,
runtime-domain authority and activation policy stay small and reviewable; static
assertions must inspect both layers instead of requiring all implementation text
inline.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
impl_path = ROOT / "tests" / "provider_repair_pipeline_v6_contract_test_impl.py"
source = impl_path.read_text(encoding="utf-8")

replacements = {
    "finalizer = (ROOT / 'scripts/finalize_provider_repair_disposition_v1.py').read_text(encoding='utf-8')":
        "finalizer = (ROOT / 'scripts/finalize_provider_repair_disposition_v1.py').read_text(encoding='utf-8') + '\\n' + (ROOT / 'scripts/finalize_provider_repair_disposition_v1_impl.py').read_text(encoding='utf-8')",
    "yield_audit = (ROOT / 'scripts/audit_provider_repair_yield_v6.py').read_text(encoding='utf-8')":
        "yield_audit = (ROOT / 'scripts/audit_provider_repair_yield_v6.py').read_text(encoding='utf-8') + '\\n' + (ROOT / 'scripts/audit_provider_repair_yield_v6_impl.py').read_text(encoding='utf-8')",
    "portfolio_compare = (ROOT / 'scripts/compare_quick_yield_preservation.py').read_text(encoding='utf-8')":
        "portfolio_compare = (ROOT / 'scripts/compare_quick_yield_preservation.py').read_text(encoding='utf-8') + '\\n' + (ROOT / 'scripts/compare_quick_yield_preservation_impl.py').read_text(encoding='utf-8')",
}
for old, new in replacements.items():
    if source.count(old) != 1:
        raise AssertionError(f"repair contract compatibility anchor changed: {old}")
    source = source.replace(old, new, 1)

# Activation is now an exact release authority: only the 46 current-live-positive
# matrix members are visible. Repair/off remains separate route debt and can never
# widen that set. Replace only historical static spellings; the implementation test
# remains otherwise unchanged.
compat_replacements = {
    "    'active-but-broken',": "    '\"activationAuthority\": \"hub-lab-matrix-46\"',",
    "    'enabled = True',": "    'enabled = provider in target_hubs',",
    "    'def off_evidence_ok(patch: dict) -> bool:',": "    'def off_evidence_ok(patch: dict, expected_enabled: bool) -> bool:',",
}
for old, new in compat_replacements.items():
    if source.count(old) != 1:
        raise AssertionError(f"repair contract activation assertion anchor changed: {old}")
    source = source.replace(old, new, 1)

exec(compile(source, str(impl_path), "exec"), globals(), globals())
