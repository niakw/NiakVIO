#!/usr/bin/env python3
"""One-shot deletion of a specifically archived, closed, failed PR branch."""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"cleanup/stale-4khdhub-branch-2026-11-06.json"
REPO="niakw/NiakVIO"

def api(path: str, method: str="GET"):
    token=os.environ.get("GH_TOKEN","").strip()
    if not token or os.environ.get("GITHUB_REPOSITORY") != REPO:
        raise RuntimeError("Missing exact authorised repository/token")
    req=Request("https://api.github.com/"+path,method=method,headers={
        "Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
    })
    try:
        with urlopen(req,timeout=30) as r:
            raw=r.read(1000000)
            return json.loads(raw.decode("utf-8")) if raw else None
    except HTTPError as err:
        if err.code==404 and method=="GET":
            return None
        raise

def verify_policy(doc: dict) -> None:
    assert doc["schemaVersion"]==1 and doc["repository"]==REPO
    assert doc["prNumber"]==252 and doc["failedProofRun"]==41702179015
    assert doc["branch"]=="fix/4khdhub-exact-css-class-20261101"
    assert doc["sha"]=="a4cc1f5c1afd60fe64548fd8e5bf61d5c712af85"

def main() -> None:
    doc=json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_policy(doc)
    name,sha=doc["branch"],doc["sha"]
    ref="repos/"+REPO+"/git/ref/heads/"+quote(name,safe="/")
    branch="repos/"+REPO+"/branches/"+quote(name,safe="")
    current=api(ref)
    if current is None:
        print("FIELD_NIAKVIO_STALE_BRANCH_CLEANUP already_absent")
        return
    pr=api("repos/"+REPO+"/pulls/252")
    status=api("repos/"+REPO+"/actions/runs/41702179015")
    details=api(branch)
    active=api("repos/"+REPO+"/pulls?"+urlencode({"state":"open","head":"niakw:"+name,"per_page":100}))
    if (not isinstance(pr,dict) or pr.get("state")!="closed" or pr.get("merged_at")
        or pr.get("head",{}).get("ref")!=name or pr.get("head",{}).get("sha")!=sha
        or (pr.get("head",{}).get("repo") or {}).get("full_name")!=REPO
        or not isinstance(status,dict) or status.get("conclusion")!="failure"
        or not isinstance(details,dict) or details.get("protected",True)
        or not isinstance(active,list) or active
        or (current.get("object") or {}).get("sha")!=sha):
        raise RuntimeError("Closed/unmerged failed PR branch proof changed; no deletion")
    last=api(ref)
    if not last or (last.get("object") or {}).get("sha")!=sha:
        raise RuntimeError("Branch moved during delete preflight")
    api("repos/"+REPO+"/git/refs/heads/"+quote(name,safe="/"),"DELETE")
    print("FIELD_NIAKVIO_STALE_BRANCH_CLEANUP deleted="+name+" sha="+sha+" archived_pr=252")

if __name__=="__main__":
    main()
