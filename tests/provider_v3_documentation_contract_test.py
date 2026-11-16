#!/usr/bin/env python3
"""Fail closed when docs/workflows drift from current Provider v3 ownership."""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_provider_scope import active_provider_count, pending_provider_ids, projection_active_provider_count, projection_runtime_visible_provider_count, projection_visible_provider_rows, runtime_visible_provider_count, visible_provider_count

ACTIVE_EXPECTED = active_provider_count()
VISIBLE_EXPECTED = visible_provider_count()
RUNTIME_VISIBLE_EXPECTED = runtime_visible_provider_count()
PENDING_IDS = pending_provider_ids()
HISTORICAL_PROVIDER_COUNT = 50

architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
family_architecture = (ROOT / "PROVIDER_FAMILY_ARCHITECTURE.md").read_text(encoding="utf-8")
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
validation_machine = json.loads((ROOT / "VALIDATION.json").read_text(encoding="utf-8"))
sources_machine = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
provider_catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))

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
    "fingerprint de publication est en **schéma v4**",
    "placeholder d'environ **4,5 s**",
    "StreamBadge public actuel est **v10**",
    "runtime_visible_provider_ids()",
    "bulk_onboarding_pending",
):
    assert required in architecture, required

for required in (
    "**B. Famille Provider**",
    "**C. Provider personnel**",
    "**D. CORE**",
    "PROVIDER.<ID>.RUNTIME.*",
    "CORE.PROVIDER_SECURITY_BOUNDARY.V1",
    "CORE.STREAM_SANITIZER",
    "CORE.STREAM_SCORE.V1",
    "famille de runtime/protocole",
    "famille de panne/réparation",
    "recompiler sur les bytes exacts",
    "NO PROOF",
    "Recognition traversal only",
    "runtime_template_prior",
    "Existing shared renderer",
    "provider_bloc",
):
    assert required in family_architecture, f"PROVIDER_FAMILY_ARCHITECTURE: {required}"

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
    for banned_term in ("Lego", "LEGO"):
        assert banned_term not in text, f"{label}: terminology must use Bloc, found {banned_term}"
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
# Full reconstruction has two explicit projection-union denominators:
# runtime-visible for sequential audit (including disabled lifecycle rows), and
# active for the final executable materialization/reverse proof.
assert "from scripts.current_provider_scope import projection_runtime_visible_provider_count" in manual
assert "expected=projection_runtime_visible_provider_count()" in manual
assert "from scripts.current_provider_scope import projection_active_provider_count, projection_active_provider_ids" in manual
assert "expected=projection_active_provider_count()" in manual
assert 'report.get("providerCount") == expected' in manual
assert 'report.get("completedProviderCount") == expected' in manual
assert 'r.get("providerCount")==expected' in manual
assert "material_ids==active_ids" in manual
assert "==46" not in manual and "46/46" not in manual


assert machine["schema_version"] >= 10
source = machine["provider_source_of_truth"]
assert source["canonical_provider_base_marker"] == "NIAKVIO_PROVIDER_BASE_OWNED_V3"
assert source["legacy_provider_js_seed_allowed"] is False
assert source["upstream_provider_js_seed_allowed"] is False
assert source["published_provider_js_is_reconstruction_seed"] is False

media = machine["media_types"]
assert media["semantic_field"] == "canonicalSupportedTypes"
assert media["transport_field"] == "supportedTypes"
assert media["anime_only_transport_compatibility"] == ["anime", "tv"]
assert media["provider_runtime_request_values"] == ["movie", "tv"]
assert media["tv_input_aliases"] == ["series", "show", "other"]
assert media["anime_provider_runtime_type"] == "tv"
assert media["series_published_supported_type"] is False
assert media["transport_aliases_do_not_expand_semantic_capability"] is True
assert media["capability_gate_before_provider_network"] is True

scopes = machine["provider_scopes"]
assert scopes["global_catalogue_visible"] == "scripts/current_provider_scope.py:visible_provider_ids"
assert scopes["global_active"] == "scripts/current_provider_scope.py:active_provider_ids"
assert scopes["global_pending"] == "scripts/current_provider_scope.py:pending_provider_ids"
assert scopes["global_runtime_visible"] == "scripts/current_provider_scope.py:runtime_visible_provider_ids"
assert scopes["pending_is_executable"] is False
assert scopes["pending_is_lifecycle_retention"] is False
assert scopes["france_only_must_not_leak_global"] is True
assert machine["provider_source_of_truth"]["runtime_ledger_scope_authority"] == "scripts/current_provider_scope.py:projection_runtime_visible_provider_ids"
domain_refresh = machine["domain_refresh"]
assert domain_refresh["provider_scope_authority"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert domain_refresh["global_publication_authority"] == "manifest.json"
assert domain_refresh["france_only_publication_authority"] == "provider_catalog.json projections general=false,vf=true"
assert machine["route_recognition"]["provider_scope_authority"] == "scripts/current_provider_scope.py:projection_runtime_visible_provider_ids"
assert machine["route_recognition"]["global_publication_authority"] == "manifest.json"
assert machine["route_recognition"]["france_only_publication_authority"] == "provider_catalog.json projections general=false,vf=true"

assert machine["routine"]["quick"]["repair_allowed"] is False
assert machine["routine"]["quick"]["provider_reconstruction_allowed"] is False
assert provider_catalog["policy"]["quickRefreshMayRepairAndPublish"] is False
assert machine["routine"]["deep"]["repair_allowed"] is False
assert machine["routine"]["deep"]["provider_reconstruction_allowed"] is False
assert machine["manual_reconstruction"]["main_write_allowed"] is False
assert "expected_provider_count" not in machine["manual_reconstruction"]
assert machine["manual_reconstruction"]["provider_scope_authority"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert machine["manual_reconstruction"]["sequential_audit_scope_authority"] == "scripts/current_provider_scope.py:projection_runtime_visible_provider_ids"
assert machine["manual_reconstruction"]["global_publication_authority"] == "manifest.json"
assert machine["manual_reconstruction"]["france_only_publication_authority"] == "provider_catalog.json projections general=false,vf=true"
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
assert plan["provider_scope_authority"] == "scripts/current_provider_scope.py:projection_visible_provider_ids"
assert plan["historical_provider_count"] == HISTORICAL_PROVIDER_COUNT
assert plan["historical_provider_directory"] == "provider-old"
assert plan["disabled_providers_are_audited"] is True
assert plan["runtime_scope_authority"] == "scripts/current_provider_scope.py:projection_runtime_visible_provider_ids"
assert plan["france_only_first_class"] is True
assert plan["pending_scope_authority"] == "scripts/current_provider_scope.py:pending_provider_ids"
assert plan["pending_staging_is_executable"] is False
assert plan["pending_staging_requires_lifecycle_timestamps"] is False
assert machine["security_html_filtering"]["regex_html_stripping_allowed"] is False

lab = machine["native_lab_contract"]
assert "provider_count" not in lab
assert lab["provider_scope_authority"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert lab["historical_provider_count"] == HISTORICAL_PROVIDER_COUNT
assert lab["historical_provider_directory"] == "provider-old"
assert lab["route_matrix_sources"] == ["manifest.json:scrapers[*].supportedTypes", "vf/manifest.json:scrapers[*].supportedTypes"]
assert lab["semantic_capability_sources"] == ["manifest.json:scrapers[*].canonicalSupportedTypes", "vf/manifest.json:scrapers[*].canonicalSupportedTypes"]
assert lab["declared_route_counts_are_dynamic"] is True
assert "declared_routes" not in lab
assert "declared_routes_by_type" not in lab
assert lab["coverage_is_blocking"] is True
assert lab["reader_outcomes_are_observational"] is True
assert lab["external_nuvio_repo_repairs_allowed"] is False
assert lab["external_build_dependency_packaging_repairs_allowed"] is False
assert lab["test_plumbing_must_not_change_official_runtime_behavior"] is True
assert machine["provider_scopes"]["projection_active"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert machine["provider_scopes"]["projection_runtime_visible"] == "scripts/current_provider_scope.py:projection_runtime_visible_provider_ids"
assert machine["provider_scopes"]["native_acceptance"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert machine["provider_scopes"]["native_acceptance_includes_france_only"] is True
assert machine["provider_scopes"]["availability_active"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert machine["provider_scopes"]["availability_report_visible"] == "scripts/current_provider_scope.py:projection_visible_provider_ids"

assert validation_machine["schema_version"] >= 71
runtime_contract = validation_machine["nuvio_runtime_contract"]
assert runtime_contract["current_audited_refs_must_match"] is True
assert runtime_contract["positional_get_streams_signature"] == "getStreams(tmdbId, mediaType, season, episode)"
assert runtime_contract["runtime_tmdb_capability_required"] is True
assert runtime_contract["credential_embedding_in_provider_bytes_allowed"] is False
assert runtime_contract["rich_fields_are_additive_only"] is True
assert runtime_contract["historical_platform_matrix_is_current_authority"] is False
assert runtime_contract["france_only_projection_is_first_class"] is True
assert runtime_contract["native_platform_proof_is_independent"] is True
assert runtime_contract["published_supported_types"] == ["movie", "tv", "anime"]
assert runtime_contract["provider_runtime_request_types"] == ["movie", "tv"]
assert runtime_contract["tv_input_aliases"] == ["series", "show", "other"]
assert runtime_contract["anime_provider_runtime_type"] == "tv"
assert runtime_contract["series_published_supported_type"] is False
assert runtime_contract["portable_provider_result_fields"] == [
    "title", "name", "url", "quality", "size", "language", "provider",
    "type", "seeders", "peers", "infoHash", "headers", "subtitles",
]
machine_runtime = machine["nuvio_runtime_contract"]
assert machine_runtime["provider_call_signature"] == "getStreams(tmdbId, mediaType, season, episode)"
assert machine_runtime["historical_platform_matrix_authority"] is False
assert machine_runtime["native_labs_use_latest_official_head"] is True
assert machine_runtime["native_proof_transitive_between_clients"] is False
assert machine_runtime["france_only_projection_authority"] == "provider_catalog.json projections general=false,vf=true"
assert validation_machine["release_authority"] == "manifest.json:version"
catalogue_contract = validation_machine["catalogue"]
assert catalogue_contract["cardinality_policy"] == "derived-never-frozen"
assert catalogue_contract["projection_active_authority"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert catalogue_contract["native_lab_scope_authority"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert catalogue_contract["availability_active_scope_authority"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert catalogue_contract["availability_report_scope_authority"] == "scripts/current_provider_scope.py:projection_visible_provider_ids"
assert catalogue_contract["france_only_first_class"] is True
for stale_count in ("provider_objects", "active_provider_objects", "physical_native_lab_scope", "historical_recovery_census"):
    assert stale_count not in catalogue_contract
assert validation_machine["core_contract"]["stream_sanitizer"] == "strict_v10"
assert validation_machine["native_transport"]["scope"] == "Global+France active projection union"
stream_contract = machine["stream_multiplicity_contract"]
assert stream_contract["provider_runtime_output_cap"] == 40
assert stream_contract["terminal_validation_max_playback_identities"] == 40
assert stream_contract["enumerate_announced_variants_before_final_cap"] is True
assert stream_contract["first_success_short_circuit_allowed"] is False
assert stream_contract["dedupe_key"] == "url+required_request_headers"
assert stream_contract["native_probe_batch"] == 4
assert stream_contract["mandatory_regression_fixtures"] == ["spartacus-s00e01"]
assert stream_contract["season_zero_is_valid"] is True
assert stream_contract["season_zero_may_fallback_to_one"] is False
assert validation_machine["stream_multiplicity"]["runtime_output_cap"] == 40
assert validation_machine["stream_multiplicity"]["terminal_validation_cap"] == 40
assert validation_machine["stream_multiplicity"]["first_success_does_not_end_discovery"] is True
assert validation_machine["special_episodes"]["season_zero_valid"] is True
assert validation_machine["special_episodes"]["season_zero_fallback_to_one"] is False
assert validation_machine["special_episodes"]["mandatory_native_fixture"] == "spartacus-s00e01"
source_policy = sources_machine["selection_policy"]
assert "catalogue_provider_count" not in source_policy
assert source_policy["catalogue_scope_authority"] == "scripts/current_provider_scope.py:projection_visible_provider_ids"
assert source_policy["executable_scope_authority"] == "scripts/current_provider_scope.py:projection_active_provider_ids"
assert source_policy["catalogue_cardinality_policy"] == "derived-never-frozen"
assert source_policy["content_type_inference"] == (
    "Canonical capability is movie|tv|anime. Anime-only publication adds only the tv launch alias; "
    "series/show/other are client input aliases normalized to tv and are never published supportedTypes. "
    "Movie transport requires canonical movie capability."
)
assert source_policy["stream_multiplicity_policy"] == "coverage-before-final-cap"
assert source_policy["stream_dedupe_identity"] == "url+required_request_headers"
assert source_policy["first_playable_stream_ends_discovery"] is False
assert "at most one playable stream" not in source_policy["runtime_check"]
assert projection_active_provider_count() >= ACTIVE_EXPECTED
assert projection_runtime_visible_provider_count() >= RUNTIME_VISIBLE_EXPECTED

rows = manifest.get("scrapers") or []
assert len(rows) == VISIBLE_EXPECTED
assert sum(1 for row in rows if row.get("enabled") is not False) == ACTIVE_EXPECTED
row_ids = {str(row.get("id") or "").strip().casefold().replace("_", "-") for row in rows}
global_pending_ids = PENDING_IDS & row_ids
assert all(
    row.get("enabled") is False
    for row in rows
    if str(row.get("id") or "").strip().casefold().replace("_", "-") in global_pending_ids
)
# pending_provider_ids() is catalogue-wide and may contain first-class VF-only
# staging identities. Global runtime scope subtracts only pending IDs that are
# actually visible in manifest.json.
assert RUNTIME_VISIBLE_EXPECTED == VISIBLE_EXPECTED - len(global_pending_ids)
canonical_valid = {"movie", "tv", "anime"}
transport_valid = canonical_valid
projection_rows = projection_visible_provider_rows()
assert projection_rows, "Global+France projection union must not be empty"
for row in projection_rows:
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
# provider-old is frozen historical evidence, not current lifecycle authority.
# A provider may legitimately be reintroduced as new current V3 bytes while its
# historical base remains archived for provenance/replay.
assert len(archived_ids) == HISTORICAL_PROVIDER_COUNT, (
    len(archived_ids), sorted(archived_ids & current_ids)
)

for text, label in ((architecture, "ARCHITECTURE"), (readme, "README"), (readme_fr, "README.fr")):
    assert "current route-recognition workbench" not in text.lower(), label

assert "exactement cinq Labs" in install
assert "8 jours" in install
assert "ProviderBase v3 + structured DATA + owned Bloc" in security
assert "ne sont **pas** rafraîchis par CORE Deep" in upstreams
assert "jamais une seed JavaScript exécutable" in upstreams
assert not (ROOT / ".github/triggers/deep-provider-repair").exists()

for path in (ROOT / ".github/workflows").glob("*.yml"):
    text = path.read_text(encoding="utf-8")
    if path.name == "brain-learning-lab.yml":
        continue
    # A workflow may *watch* an executable's source path as a change trigger.
    # Only executing legacy Quick/Deep scripts outside Learning violates the
    # ownership contract; scanning raw YAML gave a false red for valid "paths".
    watched_source = re.compile(
        r"""^\s*-\s*["']?scripts/run_adaptive_(?:quick|deep)_repair\.py["']?\s*$"""
    )
    executable_yaml = "\n".join(
        line for line in text.splitlines() if not watched_source.fullmatch(line)
    )
    assert "run_adaptive_quick_repair.py" not in executable_yaml, path.name
    assert "run_adaptive_deep_repair.py" not in executable_yaml, path.name

assert "46 providers" not in validation and "46 Provider Objects" not in validation
print(f"Provider v3 documentation and workflow ownership contract passed: visible={VISIBLE_EXPECTED} runtime={RUNTIME_VISIBLE_EXPECTED} active={ACTIVE_EXPECTED} pending={len(PENDING_IDS)} historical={HISTORICAL_PROVIDER_COUNT}")
