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

# ACTIVE44_REPAIR_V21_12_COMPAT
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

# Activation belongs to the physical current-provider lifecycle:
# providers/ = enabled, provider-disabled/ = visible but disabled.
# Repair/off is separate route debt and must never invent provider cardinality.
compat_replacements = {
    "    'active-but-broken',": "    '\"activationAuthority\": \"provider-folder-lifecycle\"',",
    "    'enabled = True',": "    'enabled = provider in active_ids',",
    "    'def off_evidence_ok(patch: dict) -> bool:',": "    'def off_evidence_ok(patch: dict, expected_enabled: bool) -> bool:',",
}
for old, new in compat_replacements.items():
    if source.count(old) != 1:
        raise AssertionError(f"repair contract activation assertion anchor changed: {old}")
    source = source.replace(old, new, 1)

exec(compile(source, str(impl_path), "exec"), globals(), globals())
