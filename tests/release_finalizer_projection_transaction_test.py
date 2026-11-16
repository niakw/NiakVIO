#!/usr/bin/env python3
"""Release finalization must restore projection parity before union authority checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "release-finalize.yml").read_text(encoding="utf-8")

step = workflow.index("- name: Reapply durable provider patches, minimize and rebuild current projections")
reapply = workflow.index("python3 scripts/reapply_published_overrides.py", step)
sync = workflow.index("python3 scripts/sync_manifest_projection_rows.py", reapply)
sync_check = workflow.index("python3 scripts/sync_manifest_projection_rows.py --check", sync)
reconcile = workflow.index("python3 scripts/reconcile_provider_static_authority.py --apply", sync_check)
materialize = workflow.index("python3 scripts/materialize_provider_v3_all.py", reconcile)
second_reconcile = workflow.index("python3 scripts/reconcile_provider_static_authority.py --apply", materialize)
validate = workflow.index("python3 scripts/validate_provider_materialization_authority.py", second_reconcile)

assert reapply < sync < sync_check < reconcile < materialize < second_reconcile < validate
assert "'scripts/sync_manifest_projection_rows.py'" in workflow
print("release finalizer projection transaction ordering passed")
