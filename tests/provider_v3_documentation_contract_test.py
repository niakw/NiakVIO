#!/usr/bin/env python3
"""Fail closed when docs/workflows drift from current Provider v3 ownership."""
from __future__ import annotations

import json
from pathlib import Path
from current_provider_scope import active_provider_count, visible_provider_count

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_EXPECTED = active_provider_count()
VISIBLE_EXPECTED = visible_provider_count()
HISTORICAL_PROVIDER_COUNT = 50

architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
readme_fr = (ROOT / "README.fr.md").read_text(encoding="utf-8")
health = (ROOT / "HEALTH-CHECK.md").read_text(encoding="utf-8")
contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
validation = (ROOT / "VALIDATION.md").read_text(encoding="utf-8")
upstreams = (ROOT / "UPSTREAMS.md").read_text(encoding="utf-8")
engine = (ROOT / "engine_v2/README.md").read_text(encoding="utf-8")
sync = (ROOT / ".github/workflows/sync.yml").read_text(encoding="utf-8")
manual = (ROOT / ".github/workflows/provider-v3-reconstruct-all.yml").read_text(encoding="utf-8")
machine = json.loads((ROOT / "automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

for required in (
    "NIAKVIO_PROVIDER_BASE_OWNED_V3",
    "STARTFIX:<ID>",
    "CLOSEFIX:<ID>",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "provider-v3-reconstruct-all.yml",
    "TVAndroid",
    "MobileAndroid",
    "MobileIOS",
    "DesktopMACOS",
    "DesktopWindows",
    "Quick/Deep ne réparent ni ne reconstruisent les providers",
):
    assert required in architecture, required

for text, label in (
    (architecture, "ARCHITECTURE"),
    (readme, "README"),
    (readme_fr, "README.fr"),
    (health, "HEALTH-CHECK"),
    (contributing, "CONTRIBUTING"),
    (install, "INSTALL"),
    (security, "SECURITY"),
    (validation, "VALIDATION"),
    (upstreams, "UPSTREAMS"),
    (engine, "engine_v2/README"),
):
    for forbidden in (
        "NIAKVIO_PROVIDER_BASE_OWNED_V2",
        "core-media-finalize-main.yml",
        ".github/triggers/deep-provider-repair",
        "Quick est une maintenance **réparatrice",
        "Quick handles routine maintenance such as hub/domain refresh, canonical provider validation and bounded repairs",
        "maintenance courante, repair-first",
        "10 providers dont 3 VF",
        "audit/preview-only",
        "workbench/provider-v3-performance-playback",
        "workbench/provider-v3-recognition-routes-data",
    ):
        assert forbidden not in text, f"{label}: stale architecture contract: {forbidden}"

assert "FIELD_PROVIDER_VERIFY_MODE mode=$MODE repair=false reconstruction=false" in sync
assert "python scripts/materialize_provider_v3_all.py" not in sync
assert "run_adaptive_quick_repair.py" not in sync
assert "run_adaptive_deep_repair.py" not in sync

assert "NUVIO_PROVIDER_V3_CONTEXT: workspace" in manual
assert 'GITHUB_REF_NAME}" != "main"' in manual
assert "python scripts/materialize_provider_v3_all.py" in manual
assert "python scripts/verify_provider_v3_reverse_rebuild.py" in manual

assert machine["schema_version"] >= 5
source = machine["provider_source_of_truth"]
assert source["canonical_provider_base_marker"] == "NIAKVIO_PROVIDER_BASE_OWNED_V3"
assert source["legacy_provider_js_seed_allowed"] is False
assert source["upstream_provider_js_seed_allowed"] is False
assert source["published_provider_js_is_reconstruction_seed"] is False

media = machine["media_types"]
assert media["semantic_field"] == "canonicalSupportedTypes"
assert media["transport_field"] == "supportedTypes"
assert media["anime_only_transport_compatibility"] == ["anime", "tv"]
assert media["transport_aliases_do_not_expand_semantic_capability"] is True
assert media["capability_gate_before_provider_network"] is True

assert machine["routine"]["quick"]["repair_allowed"] is False
assert machine["routine"]["quick"]["provider_reconstruction_allowed"] is False
assert machine["routine"]["deep"]["repair_allowed"] is False
assert machine["routine"]["deep"]["provider_reconstruction_allowed"] is False
assert machine["manual_reconstruction"]["main_write_allowed"] is False
assert "expected_provider_count" not in machine["manual_reconstruction"]
assert machine["manual_reconstruction"]["provider_scope_authority"] == "scripts/current_provider_scope.py:active_provider_ids"
assert machine["manual_reconstruction"]["historical_provider_count"] == HISTORICAL_PROVIDER_COUNT
assert machine["manual_reconstruction"]["historical_provider_directory"] == "provider-old"
assert machine["native_labs"] == [
    "TVAndroid",
    "MobileAndroid",
    "MobileIOS",
    "DesktopMACOS",
    "DesktopWindows",
]

assert machine["minifier"]["enabled_in_production"] is True
assert machine["minifier"]["phase"] == "pre-hash-safe-whitespace"
assert machine["minifier"]["tool"] == "scripts/provider_v3_minimizer.py"
assert machine["minifier"]["transformations_enabled"] == [
    "code-line-leading-indentation",
    "code-line-trailing-whitespace",
    "code-blank-lines",
    "unmanaged-full-line-comments",
]
assert machine["minifier"]["managed_comment_architecture_must_be_preserved"] is True
assert machine["minifier"]["unmanaged_full_line_comments_may_be_removed"] is True
assert machine["minifier"]["newline_asi_contract"] == (
    "remove only code-only blank/comment lines while retaining a physical line "
    "boundary between adjacent nonblank code lines"
)
assert machine["minifier"]["template_literal_policy"] == (
    "lexically protect template payload bytes and nested ${...}; minimize only "
    "code-state line whitespace/comments"
)
assert machine["minifier"]["terser_allowed"] is False

# Historical reverse reference is intentionally frozen, but it is isolated from
# current operational truth and current native/type counts.
reference = machine["reference_reconstruction"]
assert reference["current_operational_truth"] is False
assert reference["provider_count"] == 96
assert reference["reverse_byte_identical"] == "96/96"
assert reference["release_integrity"] is True
assert machine["provider_plan_contract"]["historical_plan_counts_live_only_in_reference_reconstruction"] is True
assert "executable_non_quarantined" not in machine["provider_plan_contract"]
assert "quarantined" not in machine["provider_plan_contract"]

plan = machine["provider_plan_contract"]
assert "catalogue_provider_count" not in plan
assert plan["provider_scope_authority"] == "scripts/current_provider_scope.py:visible_provider_ids"
assert plan["historical_provider_count"] == HISTORICAL_PROVIDER_COUNT
assert plan["historical_provider_directory"] == "provider-old"
assert plan["disabled_providers_are_audited"] is True
assert machine["security_html_filtering"]["regex_html_stripping_allowed"] is False

lab = machine["native_lab_contract"]
assert "provider_count" not in lab
assert lab["provider_scope_authority"] == "scripts/current_provider_scope.py:active_provider_ids"
assert lab["historical_provider_count"] == HISTORICAL_PROVIDER_COUNT
assert lab["historical_provider_directory"] == "provider-old"
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

rows = manifest.get("scrapers") or []
assert len(rows) == VISIBLE_EXPECTED
assert sum(1 for row in rows if row.get("enabled") is not False) == ACTIVE_EXPECTED
canonical_valid = {"movie", "tv", "anime"}
transport_valid = canonical_valid
for row in rows:
    provider = str(row.get("id") or "<unknown>")
    transport = {str(v).strip().lower() for v in (row.get("supportedTypes") or []) if str(v).strip()}
    canonical = {str(v).strip().lower() for v in (row.get("canonicalSupportedTypes") or transport) if str(v).strip()}
    assert transport and canonical, provider
    assert transport <= transport_valid, (provider, transport)
    assert canonical <= canonical_valid, (provider, canonical)
    assert canonical <= transport, (provider, canonical, transport)
    if "anime" in canonical:
        assert "tv" in transport, (provider, canonical, transport)
    assert ("movie" in transport) == ("movie" in canonical), (provider, canonical, transport)

archive = ROOT / "provider-old"
assert archive.is_dir(), "provider-old historical archive missing"
archived_ids = {path.name.split("--base--", 1)[0] for path in archive.glob("*--base--*.js")}
current_ids = {str(row.get("id") or "").strip().casefold() for row in rows}
assert len(archived_ids - current_ids) == HISTORICAL_PROVIDER_COUNT, (
    len(archived_ids - current_ids), sorted(archived_ids & current_ids)
)

for text, label in ((architecture, "ARCHITECTURE"), (readme, "README"), (readme_fr, "README.fr")):
    assert "current route-recognition workbench" not in text.lower(), label

assert "exactement cinq Labs" in install
assert "8 jours" in install
assert "ProviderBase v3 + structured DATA + owned Lego" in security
assert "ne sont **pas** rafraîchis par CORE Deep" in upstreams
assert "jamais une seed JavaScript exécutable" in upstreams
assert not (ROOT / ".github/triggers/deep-provider-repair").exists()

for path in (ROOT / ".github/workflows").glob("*.yml"):
    text = path.read_text(encoding="utf-8")
    if path.name == "brain-learning-lab.yml":
        continue
    assert "run_adaptive_quick_repair.py" not in text, path.name
    assert "run_adaptive_deep_repair.py" not in text, path.name

print("Provider v3 documentation and workflow ownership contract passed: current=46 historical=50")
