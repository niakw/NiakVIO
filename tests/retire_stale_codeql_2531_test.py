#!/usr/bin/env python3
"""No network: fail-closed CodeQL source-to-main drift contract."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
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
def page_number(url):
    # An 'in' substring match on "page=1" also matches "per_page=100".
    # Always extract the page parameter from the decoded query string.
    values=parse_qs(urlsplit(url).query)
    assert values.get("per_page")==["100"], url
    return int(values["page"][0])

def core_page(path):
    seen.append(path)
    if page_number(path)==1:
        return [old]*100
    if page_number(path)==2:
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
    return [{}]*100 if page_number(path)==1 else [{"number":2531}]
with patch.object(mod,"api",side_effect=alert_page):
    assert len(mod.read_pages("repos/"+mod.REPO+"/code-scanning/alerts?state=open"))==101
    assert len(seen)==2
# A permanently full listing must fail closed, never yield partial security rows.
with patch.object(mod,"api",return_value=[{}]*100):
    try:mod.read_pages("unbounded-list",max_pages=2)
    except RuntimeError as exc:
        assert "exceeded bounded pages" in str(exc)
    else:raise AssertionError("truncated security inventory was accepted")

# The retiring workflow must not reject the upgraded positive URL-origin
# invariant. A previous stale assertion made the entire security gate fail.
mod.verify_current_source()
with TemporaryDirectory() as directory:
    original=mod.ROOT
    try:
        fixture=Path(directory)/"tests"
        fixture.mkdir()
        file=fixture/"response_structure_test.cjs"
        mod.ROOT=Path(directory)
        for content in (
            "assert.ok(selectedReferences.calls.every(address => new URL(address).origin !== 'https://other.private.test'));",
            "assert.ok(selectedReferences.calls.every(address => !address.includes('https://other.private.test/PRIVATE')));",
            "",
        ):
            file.write_text(content,encoding="utf-8")
            try:
                mod.verify_current_source()
            except RuntimeError: pass
            else: raise AssertionError("Incomplete origin check accepted by security retirement")
    finally:
        mod.ROOT=original

# Only the immutable, added JSON facts emitted by hosted Brain proof may
# follow a successful CodeQL source SHA. Modifications or unknown files fail.
hosted_paths=[
    "automation/hosted-repair-evidence/42326911944.json",
    "automation/hosted-repair-evidence/42326911944-evaluation.json",
    "automation/hosted-repair-evidence/42326911944-http-observation.json",
    "automation/hosted-repair-evidence/42326911944-mutations.json",
    "automation/hosted-repair-evidence/42326911944-player-markup.json",
]
with patch.object(mod,"api",return_value={
    **response([]), "files":[{"filename":path,"status":"added"} for path in hosted_paths],
}):
    assert mod.evidence_only_drift(src,head)
for invalid in (
    {"filename":hosted_paths[0],"status":"modified"},
    {"filename":"automation/hosted-repair-evidence/42326911944-source.js","status":"added"},
    {"filename":"automation/hosted-repair-evidence/42326911944-context.json","status":"added"},
    {"filename":"scripts/provider_worker.cjs","status":"added"},
):
    with patch.object(mod,"api",return_value={**response([]),"files":[invalid]}):
        assert not mod.evidence_only_drift(src,head), invalid

# Filter BEFORE pagination: unrelated medium/low and test-only alerts may exceed
# the six-page bound. A severe category must still be exhausted independently.
seen.clear()
def severe_page(path):
    seen.append(path)
    if "severity=critical" in path:
        return [{"number": 9001, "rule": {"security_severity_level": "critical"}}]
    if "severity=high" in path:
        return [{"number": 9002, "rule": {"security_severity_level": "high"}}]
    raise AssertionError("unfiltered security inventory requested")
with patch.object(mod, "api", side_effect=severe_page):
    alerts=mod.open_high_critical_alerts()
    assert [row["number"] for row in alerts]==[9001,9002]
    assert len(seen)==2 and all("state=open" in path and "ref=refs/heads/main" in path
                                 for path in seen)
    assert all("severity=" in path for path in seen)
with patch.object(mod, "api", return_value=[{"number": 9001}]*100):
    try:
        mod.open_high_critical_alerts()
    except RuntimeError as exc:
        assert "exceeded bounded pages" in str(exc)
    else:
        raise AssertionError("permanently full severe list was incorrectly accepted")


# A live 422 must be visible without exposing arbitrary GitHub payload contents.
from contextlib import redirect_stdout
from io import StringIO, BytesIO
from urllib.error import HTTPError
def refused_update(request,timeout=0):
    assert request.get_method()=="PATCH"
    raise HTTPError(request.full_url,422,"Unprocessable Entity",{},
        BytesIO(json.dumps({"message":"Dismissal request approval required",
            "errors":[{"field":"dismissed_reason","code":"invalid",
                       "message":"PRIVATE-TOKEN"}]}).encode("utf-8")))
with patch.object(mod,"urlopen",side_effect=refused_update), patch.dict(os.environ,{
    "GH_TOKEN":"test-token-not-for-logs", "GITHUB_REPOSITORY":mod.REPO}):
    stdout=StringIO()
    with redirect_stdout(stdout):
        try:
            mod.api("repos/"+mod.REPO+"/code-scanning/alerts/"+str(mod.LEGACY_ALERT),
                    "PATCH",{"state":"dismissed","dismissed_reason":"false positive"})
        except HTTPError as exc:
            assert exc.code==422
        else:
            raise AssertionError("422 was swallowed")
    line=stdout.getvalue()
    assert "FIELD_CODEQL_DISMISSAL_REJECTED status=422 reason=approval_required" in line
    assert "dismissed_reason:invalid" in line
    assert "PRIVATE" not in line and "test-token" not in line


# Explicitly request policy-compliant review and never turn a pending request
# into a cleared security gate. No Final Gate dispatch until state dismissed.
with patch.object(mod,"verify_current_source"), patch.object(mod,"scan_source_sha",return_value=src), \
     patch.object(mod,"evidence_only_drift",return_value=True), \
     patch.object(mod,"read_pages",return_value=[core]), \
     patch.object(mod,"open_high_critical_alerts",return_value=[]):
    calls=[]
    def pending_api(path,method="GET",body=None):
        calls.append((path,method,body))
        if path.endswith("/branches/main"):
            return {"commit":{"sha":src}}
        if path.endswith("/code-scanning/alerts/2531") and method=="GET":
            return {"number":2531,"state":"open",
                    "rule":{"id":"js/incomplete-url-substring-sanitization"},
                    "most_recent_instance":{
                        "analysis_key":mod.LEGACY_KEY,
                        "location":{"path":"tests/response_structure_test.cjs",
                                    "start_line":166}}}
        if path.endswith("/code-scanning/alerts/2531") and method=="PATCH":
            return {"number":2531,"state":"open"}
        raise AssertionError("Unexpected security API call: "+path)
    with patch.object(mod,"api",side_effect=pending_api):
        buf=StringIO()
        with redirect_stdout(buf):
            mod.main()
    changes=[(path,body) for path,method,body in calls if method=="PATCH"]
    assert len(changes)==1
    assert changes[0][0].endswith("/code-scanning/alerts/2531")
    assert changes[0][1]["create_request"] is True
    assert changes[0][1]["dismissed_reason"]=="used in tests"
    assert "FIELD_CODEQL_STALE_2531_NOT_DISMISSED" in buf.getvalue()
    assert not any("/dispatches" in path for path,_,_ in calls)

print("CodeQL evidence-only drift regression passed")
