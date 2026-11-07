#!/usr/bin/env python3
"""No network: fail-closed CodeQL source-to-main drift contract."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json, os

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("retire_codeql",root/"scripts/retire_stale_codeql_2531.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
src="a"*40
head="b"*40

def response(files, *, status="ahead", commits=1, total=1):
    return {"status":status,"ahead_by":commits,"total_commits":total,
            "commits":[{"sha":head} for _ in range(commits)],
            "files":[{"filename":path,"status":"modified"} for path in files]}

with patch.object(mod,"api",side_effect=lambda *_:response([
    "automation/provider-census-status.json","PROVIDER_CENSUS_STATUS.md",
    "automation/provider-census-status-42308514242.json"])):
    assert mod.evidence_only_drift(src,head)
    assert mod.evidence_only_drift(src,src)
for invalid in (
    response(["scripts/response_structure.cjs"]),
    response(["provider-overrides.json"]),
    response(["automation/provider-census-status.json"],commits=2,total=3),
    response(["automation/provider-census-status.json"],status="diverged"),
    response(["automation/provider-census-status.json"],commits=101,total=101),
    response([]),
):
    with patch.object(mod,"api",return_value=invalid):
        assert not mod.evidence_only_drift(src,head),invalid
with TemporaryDirectory() as tmp:
    p=Path(tmp)/"event.json"
    p.write_text(json.dumps({"workflow_run":{"name":"SEC - CodeQL","head_branch":"main",
        "conclusion":"success","head_sha":src}}),encoding="utf-8")
    with patch.dict(os.environ,{"GITHUB_EVENT_PATH":str(p)}):
        assert mod.scan_source_sha()==src
        p.write_text(json.dumps({"workflow_run":{"name":"Other","head_branch":"main",
            "conclusion":"success","head_sha":src}}),encoding="utf-8")
        try:mod.scan_source_sha()
        except RuntimeError:pass
        else:raise AssertionError("unexpected workflow name accepted")
# CodeQL analyses can have thousands of old rows. Stop only when the
# exact current SHA + maintained JS Core category is present.
core={"commit_sha":src,"category":"javascript-typescript/scope:core"}
old={"commit_sha":head,"category":"javascript-typescript/scope:core"}
seen=[]
def core_page(path):
    seen.append(path)
    if "page=1" in path:
        return [old]*100
    if "page=2" in path:
        return [core]+[old]*99
    raise AssertionError("analysis traversal continued beyond exact proof")
with patch.object(mod,"api",side_effect=core_page):
    results=mod.read_pages("repos/"+mod.REPO+"/code-scanning/analyses?ref=refs/heads/main",
        stop_after=lambda rows:any(row.get("commit_sha")==src and
        row.get("category")=="javascript-typescript/scope:core" for row in rows))
    assert len(results)==200 and len(seen)==2
# Alerts MUST still be enumerated to completion, not stopped after a sample.
seen.clear()
def alert_page(path):
    seen.append(path)
    return [{}]*100 if "page=1" in path else [{"number":2531}]
with patch.object(mod,"api",side_effect=alert_page):
    assert len(mod.read_pages("repos/"+mod.REPO+"/code-scanning/alerts?state=open"))==101
    assert len(seen)==2
# A permanently full listing must fail closed, never yield partial security rows.
with patch.object(mod,"api",return_value=[{}]*100):
    try:mod.read_pages("unbounded-list",max_pages=2)
    except RuntimeError as exc:
        assert "exceeded bounded pages" in str(exc)
    else:raise AssertionError("truncated security inventory was accepted")

print("CodeQL evidence-only drift regression passed")
