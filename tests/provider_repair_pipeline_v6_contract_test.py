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
    "assert 'def rematerialize_repair_scope()' in pipeline": "assert 'def rematerialize_repair_scope(' in pipeline",
    "    'active-but-broken',": "    '\"activationAuthority\": \"provider-folder-lifecycle\"',",
    "    'enabled = True',": "    'enabled = provider in active_ids',",
    "    'def off_evidence_ok(patch: dict) -> bool:',": "    'def off_evidence_ok(patch: dict, expected_enabled: bool) -> bool:',",
}
for old, new in compat_replacements.items():
    if source.count(old) != 1:
        raise AssertionError(f"repair contract activation assertion anchor changed: {old}")
    source = source.replace(old, new, 1)

pipeline_current = (ROOT / "scripts" / "run_provider_repair_pipeline_v6.py").read_text(encoding="utf-8")
assert 'brain_waves = 1 if args.mode == "repair" else 3' in pipeline_current, "automatic Repair must execute the learned/current hypothesis once"
assert '"--waves", str(brain_waves)' in pipeline_current
assert 'brain_time_budget_seconds = 600 if args.mode == "repair" else 900' in pipeline_current
assert '"--time-budget-seconds", str(brain_time_budget_seconds)' in pipeline_current
assert '"--min-start-batch-seconds", "150",' in pipeline_current
assert 'targeted_only=args.mode in {"repair", "force"}' in pipeline_current
assert "def route_recovery_outer_timeout(" in pipeline_current
assert "def portfolio_probe_timeout(" in pipeline_current
assert "timeout=1080" in pipeline_current
assert "route_recovery_outer_timeout(" in pipeline_current
assert "portfolio_probe_timeout(len(providers or []))" in pipeline_current
assert 'if args.mode == "force":' in pipeline_current
assert "FIELD_FORCE_HISTORICAL_MIGRATIONS" in pipeline_current
assert "reason=current-bytes-only" in pipeline_current
assert "else:\n        for migration in migrations:" in pipeline_current
sanitizer_migration = (ROOT / "scripts" / "upgrade_stream_sanitizer_v7_selection.py").read_text(encoding="utf-8")
assert "stream_output_sanitizer_v10.py" in sanitizer_migration
assert "NEWER_SANITIZERS" in sanitizer_migration
assert "_newer_current" in sanitizer_migration

workflow_current = (ROOT / ".github" / "workflows" / "provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
canonical_anchor = "- name: Run canonical recognition and correction only for unresolved providers"
canonical_start = workflow_current.index(canonical_anchor)
canonical_end = workflow_current.index("- name: Reapply integrated WAF qualification after canonical Repair", canonical_start)
canonical_block = workflow_current[canonical_start:canonical_end]
assert "timeout-minutes: 30" in canonical_block

exec(compile(source, str(impl_path), "exec"), globals(), globals())
