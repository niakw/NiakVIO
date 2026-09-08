#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
readme_fr = (ROOT / "README.fr.md").read_text(encoding="utf-8")
install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
upstreams = (ROOT / "UPSTREAMS.md").read_text(encoding="utf-8")
model = json.loads((ROOT / "automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

required_architecture = (
    "ProviderBase v3",
    "provider-bases/",
    "Provider DATA",
    "Provider Lego",
    "Core Lego",
    "ProviderBase immuable",
    "CORE - Verify & Publish",
    "Quick",
    "Deep",
    "TV Android",
    "Mobile Android",
    "Mobile iOS",
    "Desktop macOS",
    "Desktop Windows",
    "Reader",
    "Learning",
    "Domain Refresh",
)
for needle in required_architecture:
    assert needle in architecture, needle

for needle in (
    "ProviderBase + DATA + Provider Lego + Core Lego",
    "CORE - Verify & Publish",
    "Quick",
    "Deep",
    "TV Android",
    "Mobile Android",
    "Mobile iOS",
    "Desktop macOS",
    "Desktop Windows",
):
    assert needle in readme, needle

for needle in (
    "ProviderBase + DATA + Provider Lego + Core Lego",
    "CORE - Verify & Publish",
    "Quick",
    "Deep",
    "TV Android",
    "Mobile Android",
    "Mobile iOS",
    "Desktop macOS",
    "Desktop Windows",
):
    assert needle in readme_fr, needle

for needle in (
    "exactement cinq Labs",
    "TV Android",
    "Mobile Android",
    "Mobile iOS",
    "Desktop macOS",
    "Desktop Windows",
    "8 jours",
):
    assert needle in install, needle

for needle in (
    "ProviderBase v3 + structured DATA + owned Lego",
    "ProviderBase",
    "Provider DATA",
    "Provider Lego",
    "Core Lego",
):
    assert needle in security, needle

for needle in (
    "ne sont **pas** rafraîchis par CORE Deep",
    "jamais une seed JavaScript exécutable",
):
    assert needle in upstreams, needle

# automation/provider-v3-architecture.json is the single machine-readable
# architecture contract. The retired provider-v3-machine-model.json must not be
# recreated as a second, drifting source of truth.
assert not (ROOT / "automation/provider-v3-machine-model.json").exists()
assert model["schema_version"] >= 5
assert model["branch_contract"] == "provider-v3-clean-architecture"
source = model["provider_source_of_truth"]
assert source["canonical_provider_base_marker"] == "NIAKVIO_PROVIDER_BASE_OWNED_V3"
assert source["legacy_provider_js_seed_allowed"] is False
assert source["upstream_provider_js_seed_allowed"] is False
assert source["published_provider_js_is_reconstruction_seed"] is False
assert set(source["managed_markers"]) == {"STARTFIX", "CLOSEFIX", "FIXDATA"}

assert model["route_recognition"]["provider_object_count"] == 96
assert model["provider_plan_contract"]["catalogue_provider_count"] == 96
workflow = model["routine_workflow"]
assert workflow["path"] == ".github/workflows/sync.yml"
assert workflow["display_name"] == "CORE - Verify & Publish"
assert workflow["workflow_count"] == 1
assert set(workflow["profiles"]) == {"quick", "deep"}
assert workflow["profiles"]["quick"]["provider_reconstruction"] is False
assert workflow["profiles"]["quick"]["network_health"] is False
assert workflow["profiles"]["deep"]["provider_reconstruction"] is False
assert workflow["profiles"]["deep"]["network_health"] is True
assert workflow["provider_mutation_allowed"] is False
assert workflow["provider_reconstruction_allowed"] is False
assert model["legacy_duplicate_core_workflow_removed"] is True
assert not (ROOT / ".github/workflows/core-media-finalize-main.yml").exists()

routine = model["routine"]
for mode in ("quick", "deep"):
    assert routine[mode]["repair_allowed"] is False
    assert routine[mode]["provider_fix_mutation_allowed"] is False
    assert routine[mode]["provider_reconstruction_allowed"] is False
assert any("domains/hubs read-only" in value for value in routine["deep"]["responsibilities"])
learning = routine["learning"]
assert learning["repair_allowed"] is True
assert learning["production_write_allowed"] is False
assert learning["proposal_pr_only"] is True
assert learning["exclusive_code_evolution_owner"] is True
assert learning["includes_disabled_providers"] is True

domain = model["domain_refresh"]
assert domain["autonomous_main_write"] is True
assert domain["repair_allowed"] is False
assert domain["provider_fix_mutation_allowed"] is False
assert domain["api_mutation_allowed"] is False
assert domain["route_mutation_allowed"] is False
assert domain["full_provider_reconstruction_allowed"] is False
assert domain["provider_config_data_update_only"] is True
assert domain["provider_js_structure_must_remain_byte_identical_outside_config"] is True

# Historical reverse reference is intentionally frozen, but it is isolated from
# current operational truth and current native/type counts.
reference = model["reference_reconstruction"]
assert reference["current_operational_truth"] is False
assert reference["reverse_byte_identical"] == "96/96"
assert reference["release_integrity"] is True
assert model["provider_plan_contract"]["historical_plan_counts_live_only_in_reference_reconstruction"] is True
assert "executable_non_quarantined" not in model["provider_plan_contract"]
assert "quarantined" not in model["provider_plan_contract"]
assert model["provider_plan_contract"]["disabled_providers_are_audited"] is True
assert model["security_html_filtering"]["regex_html_stripping_allowed"] is False

lab = model["native_lab_contract"]
assert lab["provider_count"] == 96
assert lab["route_matrix_source"] == "manifest.json:scrapers[*].supportedTypes"
assert lab["semantic_capability_source"] == "manifest.json:scrapers[*].canonicalSupportedTypes"
assert lab["declared_route_counts_are_dynamic"] is True
assert "declared_routes" not in lab
assert "declared_routes_by_type" not in lab
assert lab["coverage_is_blocking"] is True
assert lab["reader_outcomes_are_observational"] is True
assert lab["external_nuvio_repo_repairs_allowed"] is False
assert lab["external_build_dependency_packaging_repairs_allowed"] is False
assert lab["test_plumbing_must_not_change_official_runtime_behavior"] is True
assert set(model["native_labs"]) == {
    "TVAndroid", "MobileAndroid", "MobileIOS", "DesktopMACOS", "DesktopWindows"
}

# Validate the dynamic matrix source against the current manifest instead of
# freezing yesterday's route totals into docs/machine policy. `series` is a
# Nuvio transport alias for canonical `tv`: it belongs in supportedTypes only.
rows = manifest.get("scrapers") or []
assert len(rows) == 96
transport_valid = {"movie", "tv", "anime", "series"}
canonical_valid = {"movie", "tv", "anime"}
for row in rows:
    provider = str(row.get("id") or "<unknown>")
    transport = {str(v).strip().lower() for v in (row.get("supportedTypes") or []) if str(v).strip()}
    canonical = {str(v).strip().lower() for v in (row.get("canonicalSupportedTypes") or transport) if str(v).strip()}
    assert transport and canonical, provider
    assert transport <= transport_valid, (provider, transport)
    assert canonical <= canonical_valid, (provider, canonical)
    assert "series" not in canonical, (provider, canonical)
    transport_semantic = {"tv" if value == "series" else value for value in transport}
    assert canonical <= transport_semantic, (provider, canonical, transport)
    if canonical == {"anime"}:
        assert {"anime", "tv"} <= transport_semantic, (provider, transport)

# No dead workbench should remain part of the permanent documentation contract.
for text, label in ((architecture, "ARCHITECTURE"), (readme, "README"), (readme_fr, "README.fr")):
    assert "current route-recognition workbench" not in text.lower(), label

assert "exactement cinq Labs" in install
assert "8 jours" in install
assert "ProviderBase v3 + structured DATA + owned Lego" in security
assert "ne sont **pas** rafraîchis par CORE Deep" in upstreams
assert "jamais une seed JavaScript exécutable" in upstreams
assert not (ROOT / ".github/triggers/deep-provider-repair").exists()

# Active workflows may use bounded repair primitives only in Learning.
for path in (ROOT / ".github/workflows").glob("*.yml"):
    text = path.read_text(encoding="utf-8")
    if path.name == "brain.yml":
        continue
    assert "provider-repair-fast" not in text, path.name
    assert "recover_provider_routes_from_upstreams.py" not in text, path.name

print("provider v3 documentation contract passed")
