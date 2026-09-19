#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
state=json.loads((ROOT/"automation/provider-disabled-lifecycle.json").read_text(encoding="utf-8"))
rows=[row for row in manifest.get("scrapers") or [] if isinstance(row,dict)]
disabled={str(row.get("id") or "").strip().casefold().replace("_","-"):row for row in rows if row.get("enabled") is False}
active={str(row.get("id") or "").strip().casefold().replace("_","-"):row for row in rows if row.get("enabled") is not False}
ledger=state.get("disabled") or {}
assert set(disabled)==set(ledger), (set(disabled),set(ledger))
assert not (set(active)&set(disabled))
for pid,row in active.items():
 assert str(row.get("filename") or "").startswith("providers/"), (pid,row.get("filename"))
 assert (ROOT/str(row["filename"])).is_file(), pid
for pid,row in disabled.items():
 assert str(row.get("filename") or "").startswith("provider-disabled/"), (pid,row.get("filename"))
 assert (ROOT/str(row["filename"])).is_file(), pid
 disabled_at=date.fromisoformat(str(row.get("disabledAt")))
 purge_after=date.fromisoformat(str(row.get("purgeAfter")))
 assert purge_after-disabled_at == timedelta(days=28), (pid,disabled_at,purge_after)
 assert ledger[pid].get("state")=="disabled-retained"
 assert ledger[pid].get("manifestVisible") is True
print(f"provider disabled lifecycle contract passed active={len(active)} disabled={len(disabled)} retention=28")
