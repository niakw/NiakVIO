#!/usr/bin/env python3
"""Release finalization must restore projection parity before every union authority check."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "release-finalize.yml").read_text(encoding="utf-8")

runtime_step = workflow.index("- name: Validate current Nuvio métier ABI and projection authority")
runtime_render = workflow.index("python3 scripts/render_platform_runtime_contracts.py", runtime_step)
runtime_gate = workflow.index("python3 scripts/runtime_contract_gate.py", runtime_render)
runtime_matrix = workflow.index("python3 scripts/nuvio_runtime_compatibility.py", runtime_gate)
runtime_policy = workflow.index("python3 scripts/validate_platform_runtime_policy.py", runtime_matrix)
portable_gate = workflow.index("python3 tests/nuvio_portable_stream_result_contract_test.py", runtime_policy)

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
assert runtime_step < runtime_render < runtime_gate < runtime_matrix < runtime_policy < portable_gate < step
assert release_types < reapply2 < minimize2 < minimize2_check < sync3 < sync3_check < final_reconcile
reverse_rebuild = workflow.index("python3 scripts/verify_provider_v3_reverse_rebuild.py", final_reconcile)
finalize_versions = workflow.index("- name: Finalize synchronized release and provider cache versions", reverse_rebuild)
assert final_reconcile < reverse_rebuild < finalize_versions
assert workflow.count("python3 scripts/sync_manifest_projection_rows.py\n") >= 3
assert workflow.count("python3 scripts/sync_manifest_projection_rows.py --check") >= 3
assert "'scripts/sync_manifest_projection_rows.py'" in workflow
for required in (
    "'automation/nuvio-client-compatibility-matrix.json'",
    "'automation/platform-runtime-contracts.json'",
    "'scripts/runtime_contract_gate.py'",
    "'scripts/verify_provider_v3_reverse_rebuild.py'",
    "'scripts/generate_release_hashes.py'",
):
    assert required in workflow, required
print("release finalizer projection transaction ordering passed")
