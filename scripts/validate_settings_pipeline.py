#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
worker = (ROOT / "scripts/provider_worker.cjs").read_text(encoding="utf-8")
health = (ROOT / "scripts/health_check.mjs").read_text(encoding="utf-8")
promote = (ROOT / "scripts/promote_candidates.py").read_text(encoding="utf-8")

required_worker = [
    "settings_profiles_tested",
    "selected_settings_profile",
    "selected_setting_keys",
    "settings_diagnostics",
    "provider_server_http_statuses",
    "Number.isInteger(item.status)",
]
required_health = [
    "worker.settings_diagnostics",
    "settings_profiles_tested: settingsProfilesTestedTotal",
    "settings_profiles_producing_streams",
    "selected_settings_profiles",
    "settings_diagnostics: settingsProfileAttempts",
    "schema_version: 66",
    "manifest_curation_score",
    "manifest_quality_signals",
]
required_promote = [
    '"settings_validation"',
    'proof.get("settings_profiles_tested", 0)',
    'proof.get("settings_diagnostics", [])',
    '"schema_version": 63',
    "aggregate_manifest_claims",
    "minimum_manifest_curation_score",
    "manifest_ordering_profile",
    "manifest_entry_sort_key",
    "manifest_language_modes",
]
missing = []
for label, text, tokens in [
    ("provider_worker.cjs", worker, required_worker),
    ("health_check.mjs", health, required_health),
    ("promote_candidates.py", promote, required_promote),
]:
    for token in tokens:
        if token not in text:
            missing.append(f"{label}: {token}")
if missing:
    raise SystemExit("Missing settings pipeline elements:\n- " + "\n- ".join(missing))
print("[OK] Settings extraction -> health-results -> health-report pipeline is complete (health schema 66; promotion schema 63).")
