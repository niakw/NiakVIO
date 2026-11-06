#!/usr/bin/env python3
"""Retire one stale legacy CodeQL alert only after exact-head maintained-source proof."""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

REPO="niakw/NiakVIO"
ROOT=Path(__file__).resolve().parents[1]
LEGACY_ALERT=2531
LEGACY_KEY=".github/workflows/codeql.yml:analyze"

def api(path,method="GET",body=None):
    token=os.environ.get("GH_TOKEN","").strip()
    if not token or os.environ.get("GITHUB_REPOSITORY")!=REPO:
        raise RuntimeError("Expected exact GitHub repository and authenticated token")
    req=Request("https://api.github.com/"+path,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        method=method,headers={"Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json",
        "Content-Type":"application/json",
        "X-GitHub-Api-Version":"2022-11-28"})
    with urlopen(req,timeout=45) as res:
        raw=res.read(5_000_001)
        if len(raw)>5_000_000:
            raise RuntimeError("GitHub security response exceeded safe limit")
        return json.loads(raw.decode("utf-8")) if raw else None

def read_pages(path,max_pages=6):
    all_rows=[]
    for page in range(1,max_pages+1):
        separator="&" if "?" in path else "?"
        result=api(path+separator+"per_page=100&page="+str(page))
        if not isinstance(result,list):
            raise ValueError("GitHub alert/analysis collection shape invalid")
        all_rows.extend(result)
        if len(result)<100:
            return all_rows
    raise RuntimeError("Security listing exceeded bounded pages")

def verify_current_source() -> None:
    text=(ROOT/"tests/response_structure_test.cjs").read_text(encoding="utf-8")
    if "new URL(address).origin !== 'https://other.private.test'" not in text:
        raise RuntimeError("Parsed URL origin regression is absent")
    if ".includes('https://other.private.test/PRIVATE')" in text:
        raise RuntimeError("Legacy incomplete URL substring check returned")

def main() -> None:
    verify_current_source()
    branch=api("repos/"+REPO+"/branches/main")
    head=(branch or {}).get("commit",{}).get("sha")
    expected=os.environ.get("GITHUB_SHA","").strip()
    if head!=expected:
        raise RuntimeError("Default branch advanced since requested exact scan")
    alert=api("repos/"+REPO+"/code-scanning/alerts/"+str(LEGACY_ALERT))
    if alert.get("state")!="open":
        print("FIELD_CODEQL_LEGACY_CATEGORY_CLEANUP already_nonopen "+str(alert.get("state")))
        return
    inst=alert.get("most_recent_instance") or {}
    loc=inst.get("location") or {}
    if (alert.get("number")!=LEGACY_ALERT
        or (alert.get("rule") or {}).get("id")!="js/incomplete-url-substring-sanitization"
        or loc.get("path")!="tests/response_structure_test.cjs"
        or loc.get("start_line")!=166
        or inst.get("analysis_key")!=LEGACY_KEY):
        raise RuntimeError("Live alert is not the exact known stale test-only finding")
    analyses=read_pages("repos/"+REPO+"/code-scanning/analyses?ref=refs/heads/main")
    matched=[row for row in analyses
        if row.get("commit_sha")==expected
        and "javascript" in str(row.get("category") or row.get("analysis_key") or "").lower()
        and "scope:core" in str(row.get("category") or row.get("analysis_key") or "").lower()]
    if not matched:
        raise RuntimeError("Exact-main maintained JS Core CodeQL analysis not found")
    alerts=read_pages("repos/"+REPO+"/code-scanning/alerts?state=open&ref=refs/heads/main")
    for row in alerts:
        severity=str((row.get("rule") or {}).get("security_severity_level") or "").lower()
        if severity not in ("high","critical"):
            continue
        recent=row.get("most_recent_instance") or {}
        category=str(recent.get("analysis_key") or "").lower()
        if "scope:core" in category and row.get("number")!=LEGACY_ALERT:
            raise RuntimeError("Unresolved current JS Core High/Critical alerts remain")
    explanation=("Obsolete CodeQL analysis key after split to maintained JS Core category; "
                 "former test line used URL substring matching, now uses parsed URL.origin equality. "
                 "Exact current main analyzed cleanly in CodeQL core category. "
                 "This is a historical test-only diagnostic, not a provider runtime bypass.")
    updated=api("repos/"+REPO+"/code-scanning/alerts/"+str(LEGACY_ALERT),
        "PATCH",{"state":"dismissed","dismissed_reason":"false positive",
                 "dismissed_comment":explanation})
    if updated.get("state")!="dismissed":
        raise RuntimeError("CodeQL did not confirm dismissal of stale historical alert")
    print("FIELD_CODEQL_STALE_2531_DISMISSED exact_main="+expected+" core_analyses="+str(len(matched)))
    # The Final Gate must run AFTER this status change, on the exact same main.
    after=(api("repos/"+REPO+"/branches/main") or {}).get("commit",{}).get("sha")
    if after!=expected:
        raise RuntimeError("Main moved after stale alert resolution; no validation dispatch")
    api("repos/"+REPO+"/actions/workflows/security-final-gate.yml/dispatches",
        "POST",{"ref":"main"})
    print("FIELD_CODEQL_POST_CLEANUP_FINAL_GATE_DISPATCH sha="+expected)

if __name__=="__main__":
    main()
