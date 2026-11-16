#!/usr/bin/env python3
"""Release finalization must restore projection parity before every union authority check."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "release-finalize.yml").read_text(encoding="utf-8")

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
assert release_types < reapply2 < minimize2 < minimize2_check < sync3 < sync3_check < final_reconcile
assert workflow.count("python3 scripts/sync_manifest_projection_rows.py\n") >= 3
assert workflow.count("python3 scripts/sync_manifest_projection_rows.py --check") >= 3
assert "'scripts/sync_manifest_projection_rows.py'" in workflow
print("release finalizer projection transaction ordering passed")
