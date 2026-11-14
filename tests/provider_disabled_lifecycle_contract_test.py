#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from manage_provider_lifecycle import RETENTION_DAYS, provider_artifacts
from current_provider_scope import pending_provider_ids

manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
vf_manifest=json.loads((ROOT/"vf/manifest.json").read_text(encoding="utf-8"))
state=json.loads((ROOT/"automation/provider-disabled-lifecycle.json").read_text(encoding="utf-8"))
root_rows=[row for row in manifest.get("scrapers") or [] if isinstance(row,dict)]
vf_rows=[row for row in vf_manifest.get("scrapers") or [] if isinstance(row,dict)]
root_ids={str(row.get("id") or "").strip().casefold().replace("_","-") for row in root_rows}
vf_only_rows=[
    row for row in vf_rows
    if str(row.get("id") or "").strip().casefold().replace("_","-") not in root_ids
]
visible_rows=[*root_rows,*vf_only_rows]
all_disabled={
    str(row.get("id") or "").strip().casefold().replace("_","-"):row
    for row in visible_rows if row.get("enabled") is False
}
pending=pending_provider_ids() & set(all_disabled)
disabled={pid:row for pid,row in all_disabled.items() if pid not in pending}
active={
    str(row.get("id") or "").strip().casefold().replace("_","-"):row
    for row in visible_rows if row.get("enabled") is not False
}
ledger=state.get("disabled") or {}
assert state.get("retentionDays") == RETENTION_DAYS
assert set(disabled)==set(ledger), (set(disabled),set(ledger))
assert not (set(active)&set(all_disabled))
assert pending.isdisjoint(ledger)

for row in root_rows:
    pid=str(row.get("id") or "").strip().casefold().replace("_","-")
    if row.get("enabled") is False:
        assert str(row.get("filename") or "").startswith("provider-disabled/"), (pid,row.get("filename"))
    else:
        assert str(row.get("filename") or "").startswith("providers/"), (pid,row.get("filename"))
    assert (ROOT/str(row["filename"])).is_file(), pid

for row in vf_only_rows:
    pid=str(row.get("id") or "").strip().casefold().replace("_","-")
    filename=str(row.get("filename") or "")
    expected_prefix="../provider-disabled/" if row.get("enabled") is False else "../providers/"
    assert filename.startswith(expected_prefix), (pid,filename)
    assert ((ROOT/"vf")/filename).resolve().is_file(), pid

for pid in pending:
    row=all_disabled[pid]
    assert not row.get("disabledAt") and not row.get("purgeAfter"), (pid,row)

for pid,row in disabled.items():
    disabled_at=date.fromisoformat(str(row.get("disabledAt")))
    purge_after=date.fromisoformat(str(row.get("purgeAfter")))
    assert purge_after-disabled_at == timedelta(days=RETENTION_DAYS), (pid,disabled_at,purge_after)
    assert ledger[pid].get("state")=="disabled-retained"
    assert ledger[pid].get("manifestVisible") is True

workflow=(ROOT/".github/workflows/provider-disabled-lifecycle.yml").read_text(encoding="utf-8")
assert "- 'automation/provider-census-status.json'" in workflow, "fresh canonical census must trigger lifecycle"

with tempfile.TemporaryDirectory(prefix="provider-lifecycle-prefix-") as tmp:
    folder=Path(tmp)
    exact=folder/"voiranime--nuvio--0123456789abcdef.js"
    child=folder/"voiranime-homes--nuvio--fedcba9876543210.js"
    workspace=folder/"voiranime-0011223344556677.js"
    for path in (exact,child,workspace):
        path.write_text("// fixture\n",encoding="utf-8")
    matched=[path.name for path in provider_artifacts(folder,"voiranime")]
    assert matched==sorted([exact.name,workspace.name]), matched
    assert child.name not in matched, matched

print(
    f"provider disabled lifecycle contract passed active={len(active)} "
    f"disabled={len(disabled)} pending={len(pending)} retention={RETENTION_DAYS} vf_only={len(vf_only_rows)}"
)
