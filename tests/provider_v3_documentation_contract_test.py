#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
readme_fr = (ROOT / "README.fr.md").read_text(encoding="utf-8")
install = (ROOT / "docs/INSTALL-NATIVE-LABS.md").read_text(encoding="utf-8")
security = (ROOT / "docs/SECURITY-THREAT-MODEL.md").read_text(encoding="utf-8")
upstreams = (ROOT / "docs/UPSTREAMS.md").read_text(encoding="utf-8")
machine = json.loads((ROOT / "automation/provider-v3-machine-model.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

required_architecture = (
    "ProviderBase v3",
    "ProviderBase (`provider-bases/*.js`)",
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

assert machine["schema_version"] >= 2
assert machine["provider_model"] == "providerbase-v3-data-lego-core"
assert machine["catalogue_provider_count"] == 96
assert machine["workflow_contract"]["single_entrypoint"] == "CORE - Verify & Publish"
assert set(machine["workflow_contract"]["modes"]) == {"quick", "deep"}
assert machine["workflow_contract"]["quick"]["repair"] is False
assert machine["workflow_contract"]["quick"]["reconstruction"] is False
assert machine["workflow_contract"]["deep"]["repair"] is False
assert machine["workflow_contract"]["deep"]["reconstruction"] is False
assert machine["workflow_contract"]["deep"]["external_upstream_calls"] is False
assert machine["workflow_contract"]["deep"]["hub_calls"] is True
assert machine["learning_contract"]["automatic_learning_runs"] is True
assert machine["learning_contract"]["providerbase_mutation_allowed"] is False
assert machine["learning_contract"]["proposal_branch_only"] is True
assert machine["learning_contract"]["direct_main_write"] is False
assert machine["domain_refresh_contract"]["hub_only"] is True
assert machine["domain_refresh_contract"]["source_code_reconstruction"] is False
assert machine["domain_refresh_contract"]["manifest_sync"] is False
assert machine["domain_refresh_contract"]["hub_update_scope"] == "official-site-and-domain-substitution-data"

# Historical reverse reference is intentionally frozen, but it is isolated from
# current operational truth and current native/type counts.
reference = machine["reference_reconstruction"]
assert reference["current_operational_truth"] is False
assert reference["reverse_byte_identical"] == "96/96"
assert reference["release_integrity"] is True
assert machine["provider_plan_contract"]["historical_plan_counts_live_only_in_reference_reconstruction"] is True
assert "executable_non_quarantined" not in machine["provider_plan_contract"]
assert "quarantined" not in machine["provider_plan_contract"]

assert machine["provider_plan_contract"]["disabled_providers_are_audited"] is True
assert machine["security_html_filtering"]["regex_html_stripping_allowed"] is False

lab = machine["native_lab_contract"]
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
    # Compare semantic support after normalizing the transport-only series alias.
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
