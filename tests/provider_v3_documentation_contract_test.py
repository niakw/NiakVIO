#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
readme_fr = (ROOT / "README.fr.md").read_text(encoding="utf-8")
security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
upstreams = (ROOT / "UPSTREAMS.md").read_text(encoding="utf-8")
install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
machine = json.loads((ROOT / "automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

assert "ProviderBase v3" in architecture
assert "structured DATA" in architecture
assert "Provider Lego" in architecture
assert "Core Lego" in architecture
assert "STARTFIX" in architecture and "CLOSEFIX" in architecture
assert "provider-v3-materialization.json" in architecture
assert "scripts/provider_v3_minimizer.py" in architecture
assert "Terser" in architecture
assert "ProviderBase v3" in readme
assert "ProviderBase v3" in readme_fr
assert "exactly five Labs" in readme
assert "exactement cinq Labs" in readme_fr
assert "provider-v3-materialization.json" in readme
assert "provider-v3-materialization.json" in readme_fr
assert "provider_v3_minimizer.py" in readme
assert "provider_v3_minimizer.py" in readme_fr
assert "Terser" in readme and "Terser" in readme_fr
assert "96" in architecture
assert "96" in readme
assert "96" in readme_fr
assert "ProviderBase v3" in security
assert "ProviderBase v3" in upstreams

assert machine["schema_version"] >= 4
assert machine["provider_count"] == 96
assert machine["provider_base"]["version"] == 3
assert machine["provider_base"]["immutable"] is True
assert machine["provider_base"]["common"] is True
assert machine["provider_base"]["runtime_provider_specific_business_logic_allowed"] is False
assert machine["provider_data"]["structured"] is True
assert machine["provider_data"]["provider_specific"] is True
assert machine["provider_lego"]["owned"] is True
assert machine["provider_lego"]["before_core_boundary"] is True
assert machine["core_lego"]["provider_agnostic"] is True
assert machine["core_lego"]["after_core_boundary"] is True
assert machine["core_lego"]["identity_owner"] == "CORE.STREAM_IDENTITY.V1"
assert machine["core_lego"]["media_safety_owner"] == "CORE.RUNTIME_MEDIA_SAFETY.V4"
assert machine["minimizer"]["tool"] == "scripts/provider_v3_minimizer.py"
assert machine["minimizer"]["terser_allowed"] is False
assert machine["reverse_rebuild"]["required"] is True
assert machine["reverse_rebuild"]["byte_verification_required"] is True
assert machine["provider_plan_contract"]["all_provider_objects_in_scope"] is True
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
# freezing yesterday's route totals into docs/machine policy. Canonical media
# semantics are movie/tv/anime; `series` is a Nuvio transport alias only.
rows = manifest.get("scrapers") or []
assert len(rows) == 96
canonical_valid = {"movie", "tv", "anime"}
transport_valid = canonical_valid | {"series"}
for row in rows:
    provider = str(row.get("id") or "<unknown>")
    transport = {str(v).strip().lower() for v in (row.get("supportedTypes") or []) if str(v).strip()}
    canonical = {str(v).strip().lower() for v in (row.get("canonicalSupportedTypes") or transport) if str(v).strip()}
    assert transport and canonical, provider
    assert transport <= transport_valid, (provider, transport)
    assert canonical <= canonical_valid, (provider, canonical)
    assert "series" not in canonical, (provider, canonical)
    assert canonical <= transport, (provider, canonical, transport)
    # Episodic anime/tv must be reachable through Nuvio's tv/series lanes.
    if "anime" in canonical or "tv" in canonical:
        assert {"tv", "series"} <= transport, (provider, canonical, transport)
    # Movie is never synthesized as an anime/tv transport alias.
    assert ("movie" in transport) == ("movie" in canonical), (provider, canonical, transport)

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
    if path.name == "brain-learning-lab.yml":
        continue
    assert "run_adaptive_quick_repair.py" not in text, path.name
    assert "run_adaptive_deep_repair.py" not in text, path.name

print("provider v3 documentation/machine contract passed")
