#!/usr/bin/env python3
"""Release finalization must restore projection parity before every union authority check."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assert not (ROOT / ".github/workflows/temp-release-finalize-recovery.yml").exists(), "retired temporary release bypass returned"
assert not (ROOT / ".github/triggers/temp-release-finalize-recovery.json").exists(), "retired temporary release trigger returned"
workflow = (ROOT / ".github" / "workflows" / "release-finalize.yml").read_text(encoding="utf-8")
assert "group: niakvio-release-finalizer-main" in workflow
assert "cancel-in-progress: true" in workflow, "release lane must cancel superseded Finalizers so latest accepted SHA can run"
assert "cancel-in-progress: false" not in workflow, "release lane claims latest-wins and may not queue obsolete 90-minute Finalizers"
assert "NUVIO_SKIP_CLIENT_UPSTREAM_GUARD" not in workflow, "release finalizer may not bypass current Nuvio upstream freshness"
runtime_step = workflow.index("- name: Validate current Nuvio métier ABI and projection authority")
upstream_guard = workflow.index(
    'python3 scripts/check_nuvio_client_upstreams.py --output "$RUNNER_TEMP/nuvio-client-upstream-status.json"',
    runtime_step,
)
runtime_render = workflow.index("python3 scripts/render_platform_runtime_contracts.py", upstream_guard)
runtime_gate = workflow.index("python3 scripts/runtime_contract_gate.py", runtime_render)
runtime_matrix = workflow.index("python3 scripts/nuvio_runtime_compatibility.py", runtime_gate)
runtime_policy = workflow.index("python3 scripts/validate_platform_runtime_policy.py", runtime_matrix)
portable_gate = workflow.index("python3 tests/nuvio_portable_stream_result_contract_test.py", runtime_policy)
clean_base = workflow.index("python3 tests/provider_clean_reconstruction_contract_test.py", portable_gate)
metier_docs = workflow.index("python3 tests/provider_v3_documentation_contract_test.py", clean_base)
metier_plans = workflow.index("python3 tests/provider_v3_strategy_plan_contract_test.py", metier_docs)
core_metadata = workflow.index("python3 tests/provider_v3_core_metadata_route_sanitizer_test.py", metier_plans)
cardinality = workflow.index("python3 tests/provider_cardinality_source_of_truth_test.py", core_metadata)
census_proof = workflow.index("python3 tests/provider_census_status_markdown_test.py", cardinality)
semantic_transport = workflow.index("python3 tests/provider_anime_semantic_transport_contract_test.py", census_proof)
multiplicity = workflow.index("python3 tests/provider_stream_multiplicity_contract_test.py", semantic_transport)
season_zero = workflow.index("python3 tests/special_season_zero_identity_test.py", multiplicity)
five_labs = workflow.index("python3 tests/native_five_lab_coverage_test.py", season_zero)
native_scope = workflow.index("python3 tests/native_hub46_scope_contract_test.py", five_labs)
native_transport = workflow.index("python3 tests/native_hub46_transport_manifest_test.py", native_scope)
native_corpus = workflow.index("python3 tests/native_corpus_device_lab_test.py", native_transport)
native_evidence = workflow.index("python3 tests/native_evidence_contract_test.py", native_corpus)
native_floor = workflow.index("node tests/native_evidence_completeness_test.cjs", native_evidence)
native_codegen = workflow.index("python3 tests/native_player_diagnostics_codegen_test.py", native_floor)
native_pipeline = workflow.index("python3 tests/native_evidence_codegen_pipeline_test.py", native_codegen)
native_ios_audio = workflow.index("python3 tests/native_ios_multi_audio_gate_test.py", native_pipeline)
native_multi_audio = workflow.index("node tests/native_multi_audio_coverage_gate_test.cjs", native_ios_audio)
native_provenance = workflow.index("node tests/native_provider_provenance_gate_test.cjs", native_multi_audio)
branding_provenance = workflow.index("python3 tests/global_provider_branding_test.py", native_provenance)
domain_registry = workflow.index("python3 tests/provider_hub_registry_test.py", branding_provenance)
presentation = workflow.index("python3 tests/global_stream_presentation_test.py", domain_registry)
metadata = workflow.index("python3 tests/global_stream_metadata_preservation_contract_test.py", presentation)
score = workflow.index("python3 tests/stream_score_contract_test.py", metadata)
hls_facts = workflow.index("python3 tests/hls_master_facts_short_test.py", score)
hls_integrity = workflow.index("python3 tests/hls_playback_integrity_test.py", hls_facts)
hls_presentation = workflow.index("python3 tests/hls_presentation_badge_integration_test.py", hls_integrity)
multi_variant = workflow.index("python3 tests/stream_output_sanitizer_multi_variant_test.py", hls_presentation)
telemetry = workflow.index("python3 tests/global_telemetry_contract_test.py", multi_variant)
core_ownership = workflow.index("python3 tests/global_core_runtime_ownership_test.py", telemetry)

step = workflow.index("- name: Reapply durable provider patches, minimize and rebuild current projections")
reapply = workflow.index("python3 scripts/reapply_published_overrides.py", step)
sync = workflow.index("python3 scripts/sync_manifest_projection_rows.py", reapply)
sync_check = workflow.index("python3 scripts/sync_manifest_projection_rows.py --check", sync)
reconcile = workflow.index("python3 scripts/reconcile_provider_static_authority.py --apply", sync_check)
materialize = workflow.index("python3 scripts/materialize_provider_v3_all.py", reconcile)
sync2 = workflow.index("python3 scripts/sync_manifest_projection_rows.py", materialize)
sync2_check = workflow.index("python3 scripts/sync_manifest_projection_rows.py --check", sync2)
second_reconcile = workflow.index("python3 scripts/reconcile_provider_static_authority.py --apply", sync2_check)
validate = workflow.index("python3 scripts/validate_provider_materialization_authority.py", second_reconcile)

# A later structured-authority/type reconciliation deliberately performs a
# second Global reapply + minimizer pass. Those final bytes can rotate every
# content-addressed filename again, so the derived projections must be synced
# a third time before reconcile_active_provider_publication audits the
# Global+France union.
release_types = workflow.index("python3 scripts/reconcile_release_manifest_types.py", validate)
reapply2 = workflow.index("python3 scripts/reapply_published_overrides.py", release_types)
minimize2 = workflow.index("python3 scripts/finalize_provider_v3_minimizer.py", reapply2)
minimize2_check = workflow.index("python3 scripts/finalize_provider_v3_minimizer.py --check", minimize2)
sync3 = workflow.index("python3 scripts/sync_manifest_projection_rows.py", minimize2_check)
sync3_check = workflow.index("python3 scripts/sync_manifest_projection_rows.py --check", sync3)
final_reconcile = workflow.index("python3 scripts/reconcile_active_provider_publication.py", sync3_check)

assert reapply < sync < sync_check < reconcile < materialize < sync2 < sync2_check < second_reconcile < validate
assert runtime_step < upstream_guard < runtime_render < runtime_gate < runtime_matrix < runtime_policy < portable_gate < clean_base
assert portable_gate < metier_docs < metier_plans < cardinality < semantic_transport < multiplicity < season_zero < five_labs < native_scope
assert native_scope < native_transport < native_corpus < native_evidence < native_floor < native_codegen < native_pipeline < native_ios_audio < native_multi_audio < native_provenance < branding_provenance < domain_registry < presentation < metadata < score < hls_facts < hls_integrity < hls_presentation < multi_variant < telemetry < core_ownership < step
assert release_types < reapply2 < minimize2 < minimize2_check < sync3 < sync3_check < final_reconcile
reverse_rebuild = workflow.index("python3 scripts/verify_provider_v3_reverse_rebuild.py", final_reconcile)
finalize_versions = workflow.index("- name: Finalize synchronized release and provider cache versions", reverse_rebuild)
assert final_reconcile < reverse_rebuild < finalize_versions
assert workflow.count("python3 scripts/sync_manifest_projection_rows.py\n") >= 3
assert workflow.count("python3 scripts/sync_manifest_projection_rows.py --check") >= 3
assert "'scripts/sync_manifest_projection_rows.py'" in workflow
assert "--matrix automation/evidence/hub-lab-matrix-46.json" not in workflow
assert workflow.count("--vf-source vf/manifest.json") >= 2
for required in (
    "'automation/nuvio-client-compatibility-matrix.json'",
    "'automation/platform-runtime-contracts.json'",
    "'engine_v2/config/nuvio-clients.json'",
    "'scripts/prepare_native_corpus_validation.py'",
    "'scripts/native_player_diagnostics_codegen.py'",
    "'scripts/augment_native_desktop_player.py'",
    "'scripts/prepare_native_ios_reader_acceptance.py'",
    "'scripts/gate_native_ios_multi_audio.py'",
    "'scripts/gate_native_multi_audio_coverage.cjs'",
    "'scripts/gate_native_provider_provenance.cjs'",
    "'tests/native_provider_provenance_gate_test.cjs'",
    "'tests/global_provider_branding_test.py'",
    "'scripts/resolve_provider_hubs.py'",
    "'tests/provider_hub_registry_test.py'",
    "'scripts/native_evidence_completeness.cjs'",
    "'scripts/analyze_native_ios_results.py'",
    "'scripts/prebuild_native_android_reader_suite.sh'",
    "'scripts/run_native_corpus_mobile_suite.sh'",
    "'scripts/run_native_corpus_tv_suite.sh'",
    "'scripts/run_native_corpus_desktop_suite.sh'",
    "'scripts/run_native_corpus_ios_suite.sh'",
    "'scripts/apply_hub46_native_lab_scope.py'",
    "'tests/native_hub46_transport_manifest_test.py'",
    "'tests/native_corpus_device_lab_test.py'",
    "'tests/native_evidence_contract_test.py'",
    "'tests/native_evidence_completeness_test.cjs'",
    "'tests/native_player_diagnostics_codegen_test.py'",
    "'tests/native_evidence_codegen_pipeline_test.py'",
    "'tests/native_ios_multi_audio_gate_test.py'",
    "'tests/native_multi_audio_coverage_gate_test.cjs'",
    "'.github/workflows/native-mobile-android-reader.yml'",
    "'.github/workflows/native-mobile-ios-reader.yml'",
    "'.github/workflows/native-desktop-reader-acceptance.yml'",
    "'.github/workflows/release-candidate-validation.yml'",
    "'.github/workflows/github-actions-gate.yml'",
    "'tests/workflow_security_policy_test.py'",
    "'tests/repository_hygiene_contract_test.py'",
    "'.github/workflows/sync.yml'",
    "'.github/workflows/provider-non-regression.yml'",
    "'.github/workflows/core-stream-metadata-contract.yml'",
    "'.github/workflows/canonical-media-types.yml'",
    "'.github/workflows/provider-overrides-gate.yml'",
    "'.github/workflows/codeql.yml'",
    "'.github/workflows/security-final-gate.yml'",
    "'.github/workflows/retire-stale-codeql-2531.yml'",
    "'scripts/retire_stale_codeql_2531.py'",
    "'scripts/delete_stale_codeql_2531_configuration.py'",
    "'tests/retire_stale_codeql_2531_test.py'",
    "'tests/retire_stale_codeql_2531_policy_test.py'",
    "'tests/delete_stale_codeql_configuration_test.py'",
    "'.github/workflows/external-code-audit.yml'",
    "'scripts/check_nuvio_client_upstreams.py'",
    "'scripts/runtime_contract_gate.py'",
    "'scripts/materialize_provider_base_v3_store.py'",
    "'scripts/materialize_provider_v3_one.py'",
    "'scripts/reconcile_provider_static_authority.py'",
    "'scripts/sanitize_provider_v3_core_metadata_routes.py'",
    "'tests/provider_v3_core_metadata_route_sanitizer_test.py'",
    "'.github/workflows/provider-projection-reconcile.yml'",
    "'tests/provider_projection_reconcile_workflow_test.py'",
    "'tests/provider_static_authority_france_only_test.py'",
    "'scripts/upgrade_provider_route_media_binding_v35.py'",
    "'tests/provider_route_media_binding_v35_test.py'",
    "'tests/provider_clean_reconstruction_contract_test.py'",
    "'.github/provider-portfolio-policy.json'",
    "'.github/workflows/provider-bulk-activation.yml'",
    "'scripts/activate_bulk_proven_providers.py'",
    "'tests/provider_bulk_activation_test.py'",
    "'tests/provider_bulk_activation_workflow_test.py'",
    "'tests/provider_bulk_activation_catalog_projection_test.py'",
    "'scripts/rank_provider_portfolio.cjs'",
    "'scripts/protect_provider_coverage.cjs'",
    "'tests/provider_portfolio_ranking_test.py'",
    "'tests/provider_coverage_preservation_test.py'",
    "'scripts/verify_provider_v3_reverse_rebuild.py'",
    "'scripts/generate_release_hashes.py'",
    "'automation/provider-v3-architecture.json'",
    "'VALIDATION.json'",
    "'tests/provider_v3_documentation_contract_test.py'",
    "'tests/provider_v3_strategy_plan_contract_test.py'",
    "'tests/provider_cardinality_source_of_truth_test.py'",
    "'scripts/render_provider_census_status.py'",
    "'tests/provider_census_status_markdown_test.py'",
    "'tests/provider_anime_semantic_transport_contract_test.py'",
    "'tests/native_five_lab_coverage_test.py'",
    "'tests/native_hub46_scope_contract_test.py'",
    "'tests/global_stream_presentation_test.py'",
    "'tests/global_stream_metadata_preservation_contract_test.py'",
    "'tests/stream_score_contract_test.py'",
    "'tests/hls_master_facts_short_test.py'",
    "'tests/hls_playback_integrity_test.py'",
    "'tests/hls_presentation_badge_integration_test.py'",
    "'tests/stream_output_sanitizer_multi_variant_test.py'",
    "'tests/global_telemetry_contract_test.py'",
    "'tests/global_core_runtime_ownership_test.py'",
):
    assert required in workflow, required
assert "python3 tests/provider_projection_reconcile_workflow_test.py" in workflow
assert "python3 tests/provider_static_authority_france_only_test.py" in workflow
print("release finalizer projection transaction ordering passed")
