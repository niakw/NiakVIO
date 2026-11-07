#!/usr/bin/env python3
"""Retire one stale legacy CodeQL alert only after exact-head maintained-source proof."""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError
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
    try:
        with urlopen(req,timeout=45) as res:
            raw=res.read(5_000_001)
            if len(raw)>5_000_000:
                raise RuntimeError("GitHub security response exceeded safe limit")
            return json.loads(raw.decode("utf-8")) if raw else None
    except HTTPError as exc:
        # GitHub's 422 dismissal response can mean validation or mandatory
        # approval. Classify *only* fixed, non-sensitive flags, never log the
        # raw server text, request, Authorization header or alert payload.
        if (method=="PATCH" and path=="repos/"+REPO+"/code-scanning/alerts/"+str(LEGACY_ALERT)
            and exc.code==422):
            try:
                payload=json.loads(exc.read(4096).decode("utf-8",errors="replace"))
            except (ValueError,UnicodeError):
                payload={}
            if not isinstance(payload,dict):
                payload={}
            message=str(payload.get("message") or "").casefold()
            reasons=(
                ("approval_required",("dismissal request","review required","approval required","request a dismissal")),
                ("permission_or_policy",("policy","not permitted","permission","not authorized","forbidden")),
                ("dismissal_unavailable",("cannot dismiss","can't dismiss","not dismissible","cannot update")),
                ("already_resolved",("already dismissed","already closed","already fixed")),
                ("validation_error",("validation","invalid","unprocessable")),
            )
            kind=next((name for name,needles in reasons if any(x in message for x in needles)),"unknown_422")
            allowed_fields={"state","dismissed_reason","dismissed_comment","create_request"}
            codes=[]
            for row in (payload.get("errors") or [])[:5]:
                if not isinstance(row,dict):
                    continue
                field=row.get("field")
                code=row.get("code")
                if field in allowed_fields and isinstance(code,str) and code.isascii() and code.replace("_","").isalnum() and len(code)<=30:
                    codes.append(field+":"+code)
            print("FIELD_CODEQL_DISMISSAL_REJECTED status=422 reason="+kind+
                  " validation_fields="+(",".join(codes) if codes else "none"),flush=True)
        raise

def read_pages(path,max_pages=6,*,stop_after=None):
    """Enumerate alerts exhaustively; stop analysis history only on exact positive proof."""
    all_rows=[]
    for page in range(1,max_pages+1):
        separator="&" if "?" in path else "?"
        result=api(path+separator+"per_page=100&page="+str(page))
        if not isinstance(result,list):
            raise ValueError("GitHub alert/analysis collection shape invalid")
        all_rows.extend(result)
        if stop_after is not None and stop_after(all_rows):
            return all_rows
        if len(result)<100:
            return all_rows
    raise RuntimeError("Security listing exceeded bounded pages")

def open_high_critical_alerts():
    """Exhaustively enumerate the TWO severe groups, not the entire alert backlog.

    GitHub's Code Scanning list-alerts endpoint accepts a severity filter.
    Each filtered collection is fully paginated or fails closed. Do not sample
    an arbitrary first page of ALL open alerts, which can exceed 600 legacy rows.
    """
    found = []
    for severity in ("critical", "high"):
        path = ("repos/" + REPO
                + "/code-scanning/alerts?state=open&ref=refs/heads/main"
                + "&severity=" + severity)
        rows = read_pages(path)
        if not all(isinstance(row, dict) for row in rows):
            raise ValueError("GitHub filtered security alert shape invalid")
        found.extend(rows)
    return found


def verify_current_source() -> None:
    """Require the actual positive, parsed-origin invariant, not old denylist.

    Test-only CodeQL #2531 was originally detected on a negative comparison
    against one disallowed host. The source now requires every selected reader
    to match the known fixture base URL's exact origin.
    """
    text=(ROOT/"tests/response_structure_test.cjs").read_text(encoding="utf-8")
    required=(
        "selectedReferences.calls.map(address => new URL(address).origin)",
        "Array(8).fill(new URL(queryOptions.baseUrl).origin)",
        "assert.deepEqual(selectedReferences.calls.map(address => new URL(address).origin)",
    )
    if not all(marker in text for marker in required):
        raise RuntimeError("Positive exact-origin invariant is absent")
    forbidden=(
        "new URL(address).origin !== 'https://other.private.test'",
        ".includes('https://other.private.test/PRIVATE')",
    )
    if any(marker in text for marker in forbidden):
        raise RuntimeError("Incomplete negative URL substring/origin check returned")

# Only non-executable, append-only evidence may advance main after a successful scan.
# A workflow_run is attached to the event's original source SHA, not github.sha
# (the latter can refer to a newer default-branch commit).
SAFE_EVIDENCE_FILES = frozenset({
    "PROVIDER_CENSUS_STATUS.md",
    "automation/brain-repair-experience.json",
    "automation/provider-brain-repair-latest.json",
    "automation/provider-census-status.json",
    "automation/provider-fast-repair-summary.json",
    "automation/provider-repair-learn-handoff-v1.json",
    "automation/provider-repair-batch-plan-latest.json",
    "automation/provider-census-proof-history.json",
    "automation/provider-waf-browser-session-latest.json",
    "automation/provider-census-sharded-latest.json",
})
SAFE_NUMBERED_EVIDENCE = (
    r"automation/provider-census-status-[0-9]{8,14}\.json",
    r"automation/provider-census-proof-[0-9]{8,14}\.json",
    r"automation/provider-waf-browser-session-[0-9]{8,14}\.json",
    r"automation/provider-census-sharded-[0-9]{8,20}\.json",
)
# Only immutable, append-only hosted Brain diagnostic JSON. Never permit a
# provider or workflow mutation to be treated as drift-safe evidence.
HOSTED_EVIDENCE_ARCHIVE = (
    r"automation/hosted-repair-evidence/[0-9]{8,14}"
    r"(?:-(?:evaluation|http-observation|mutations|player-markup))?\.json"
)


def evidence_only_drift(expected: str, head: str) -> bool:
    if expected == head:
        return True
    import re
    compare = api("repos/"+REPO+"/compare/"+expected+"..."+head+"?per_page=100")
    if (compare.get("status") != "ahead"
        or compare.get("ahead_by", 0) > 100
        or compare.get("total_commits") != len(compare.get("commits") or [])
        or not compare.get("files")):
        return False
    for item in compare["files"]:
        path = str(item.get("filename") or "")
        if item.get("status") not in {"modified","added"}:
            return False
        if re.fullmatch(HOSTED_EVIDENCE_ARCHIVE, path):
            if item.get("status")!="added":
                return False
            continue
        numbered = any(re.fullmatch(pattern, path) for pattern in SAFE_NUMBERED_EVIDENCE)
        if numbered and item.get("status") != "added":
            return False  # Numbered archive evidence is immutable.
        if path not in SAFE_EVIDENCE_FILES and not numbered:
            return False
    return True

def scan_source_sha() -> str:
    event_path = Path(os.environ.get("GITHUB_EVENT_PATH") or "")
    if not event_path.is_file():
        raise RuntimeError("Missing authenticated workflow_run event source")
    event = json.loads(event_path.read_text(encoding="utf-8"))
    run = event.get("workflow_run") or {}
    if (run.get("name") != "SEC - CodeQL" or run.get("conclusion") != "success"
        or run.get("head_branch") != "main"):
        raise RuntimeError("Unexpected CodeQL workflow_run source")
    sha = str(run.get("head_sha") or "")
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise RuntimeError("Invalid CodeQL event source SHA")
    return sha

def main() -> None:
    verify_current_source()
    expected = scan_source_sha()
    branch=api("repos/"+REPO+"/branches/main")
    head=(branch or {}).get("commit",{}).get("sha")
    if not head or not evidence_only_drift(expected, head):
        print("FIELD_CODEQL_STALE_2531_DEFERRED source="+expected+" current="+str(head)+
              " reason=non_evidence_drift_or_unverifiable_comparison",flush=True)
        # No verified dismissal occurred. A green retirement job would falsely
        # suggest that the security backlog was resolved. Fail closed so the
        # workflow cannot be mistaken for a successful cleanup.
        raise RuntimeError("CodeQL legacy alert retirement deferred: unverified source drift")
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
    def is_exact_core_analysis(row):
        category=str(row.get("category") or row.get("analysis_key") or "").lower()
        return (row.get("commit_sha")==expected and "javascript" in category
                and "scope:core" in category)
    # Analysis history is unbounded. The exact-SHA current category is a positive
    # witness; unlike the High/Critical alert inventory, older rows need not be scanned.
    analyses=read_pages("repos/"+REPO+"/code-scanning/analyses?ref=refs/heads/main",
                        stop_after=lambda rows:any(is_exact_core_analysis(row) for row in rows))
    matched=[row for row in analyses if is_exact_core_analysis(row)]
    if not matched:
        raise RuntimeError("Exact-main maintained JS Core CodeQL analysis not found")
    alerts=open_high_critical_alerts()
    for row in alerts:
        severity=str((row.get("rule") or {}).get("security_severity_level") or "").lower()
        if severity not in ("high","critical"):
            continue
        recent=row.get("most_recent_instance") or {}
        category=str(recent.get("analysis_key") or "").lower()
        if "scope:core" in category and row.get("number")!=LEGACY_ALERT:
            raise RuntimeError("Unresolved current JS Core High/Critical alerts remain")
    # This is a historical *test-only* alert, not a live provider finding.
    # GitHub officially accepts "used in tests"; previous false-positive PATCH
    # and create_request attempts returned 422. Never hide a current alert.
    explanation=("Obsolete CodeQL analysis key after split to maintained JS Core category; "
                 "former test line excluded only one host, now asserts a positive exact-origin allowlist. "
                 "Exact current main analyzed cleanly in CodeQL core category. "
                 "This is a historical test-only diagnostic, not a provider runtime bypass.")
    # Use GitHub's ordinary dismissal endpoint. The optional create_request
    # flag was explicitly set in prior runs and produced HTTP 422 without
    # field-level errors on this repository; do not assume delegated requests
    # are supported. An enabled approval policy is enforced by GitHub itself,
    # and any unresolved/pending response remains a failing security gate.
    updated=api("repos/"+REPO+"/code-scanning/alerts/"+str(LEGACY_ALERT),
        "PATCH",{"state":"dismissed","dismissed_reason":"used in tests",
                 "dismissed_comment":explanation})
    if not isinstance(updated,dict):
        raise RuntimeError("GitHub returned an invalid CodeQL dismissal response")
    if updated.get("state")!="dismissed":
        print("FIELD_CODEQL_STALE_2531_NOT_DISMISSED state="+str(updated.get("state"))[:32]+
              " approval_or_policy_recheck_required=true",flush=True)
        raise RuntimeError("CodeQL legacy alert remains unresolved after dismissal request")
    print("FIELD_CODEQL_STALE_2531_DISMISSED scanned_source="+expected+" current_main="+str(head)+" core_analyses="+str(len(matched)))
    # The Final Gate must run AFTER this status change, on the exact same main.
    after=(api("repos/"+REPO+"/branches/main") or {}).get("commit",{}).get("sha")
    if not after or not evidence_only_drift(expected, after):
        raise RuntimeError("Main moved in unverified or executable way after stale alert resolution")
    api("repos/"+REPO+"/actions/workflows/security-final-gate.yml/dispatches",
        "POST",{"ref":"main"})
    print("FIELD_CODEQL_POST_CLEANUP_FINAL_GATE_DISPATCH sha="+str(after))

if __name__=="__main__":
    main()
