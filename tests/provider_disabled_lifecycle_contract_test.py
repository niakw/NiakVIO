#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from manage_provider_lifecycle import RETENTION_DAYS

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
disabled={
    str(row.get("id") or "").strip().casefold().replace("_","-"):row
    for row in visible_rows if row.get("enabled") is False
}
active={
    str(row.get("id") or "").strip().casefold().replace("_","-"):row
    for row in visible_rows if row.get("enabled") is not False
}
ledger=state.get("disabled") or {}
assert state.get("retentionDays") == RETENTION_DAYS
assert set(disabled)==set(ledger), (set(disabled),set(ledger))
assert not (set(active)&set(disabled))

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

for pid,row in disabled.items():
    disabled_at=date.fromisoformat(str(row.get("disabledAt")))
    purge_after=date.fromisoformat(str(row.get("purgeAfter")))
    assert purge_after-disabled_at == timedelta(days=RETENTION_DAYS), (pid,disabled_at,purge_after)
    assert ledger[pid].get("state")=="disabled-retained"
    assert ledger[pid].get("manifestVisible") is True

print(
    f"provider disabled lifecycle contract passed active={len(active)} "
    f"disabled={len(disabled)} retention={RETENTION_DAYS} vf_only={len(vf_only_rows)}"
)
