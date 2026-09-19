#!/usr/bin/env python3
"""Request fresh external analyses and wait until they cover the current main SHA."""

from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ROOT = pathlib.Path(os.environ.get("OUT", "audit/ai-external"))
ROOT.mkdir(parents=True, exist_ok=True)

TARGET_SHA = os.environ.get("AUDITED_SHA", "").strip()
SONAR_ORG = os.environ.get("SONAR_KEY", "").strip()
DEEPSOURCE_TOKEN = os.environ.get("DEEPSOURCE_API", "").strip()
CODESCENE_TOKEN = os.environ.get("CODESCENE_TOKEN", "").strip()
WAIT_SECONDS = int(os.environ.get("EXTERNAL_REFRESH_WAIT_SECONDS", "900"))
POLL_SECONDS = int(os.environ.get("EXTERNAL_REFRESH_POLL_SECONDS", "15"))

DS_ENDPOINT = "https://api.deepsource.com/graphql/"
CS_BASE = "https://api.codescene.io/v2"
SONAR_BASE = "https://sonarcloud.io"

state: dict[str, Any] = {
    "target_sha": TARGET_SHA,
    "wait_seconds": WAIT_SECONDS,
    "services": {
        "sonar": {"requested": False, "fresh": False, "notes": []},
        "deepsource": {"requested": False, "fresh": False, "notes": []},
        "codescene": {"requested": False, "fresh": False, "notes": []},
    },
}


def save() -> None:
    (ROOT / "refresh-request.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: int = 60,
) -> tuple[int, Any]:
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"User-Agent": "NiakVIO-external-audit/3.0", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            if not raw:
                return response.status, {}
            try:
                return response.status, json.loads(raw.decode("utf-8"))
            except Exception:
                return response.status, {"raw": raw.decode("utf-8", "replace")[:2000]}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")[:2000]
        try:
            payload: Any = json.loads(raw)
        except Exception:
            payload = {"raw": raw}
        return exc.code, payload


def ds_graphql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    status, payload = http_json(
        DS_ENDPOINT,
        method="POST",
        headers={
            "Authorization": f"Bearer {DEEPSOURCE_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
    )
    if status >= 400:
        raise RuntimeError(f"HTTP {status}: {str(payload)[:500]}")
    if isinstance(payload, dict) and payload.get("errors"):
        raise RuntimeError(
            "; ".join(str(item.get("message", "GraphQL error")) for item in payload["errors"][:5])
        )
    return (payload or {}).get("data") or {}


def request_deepsource() -> None:
    service = state["services"]["deepsource"]
    if not DEEPSOURCE_TOKEN:
        service["notes"].append("DEEPSOURCE_API missing")
        return
    try:
        data = ds_graphql(
            """query {
              repository(name:"NiakVIO", login:"niakw", vcsProvider:GITHUB) {
                id defaultBranch latestCommitOid isActivated
              }
            }"""
        )
        repo = data.get("repository") or {}
        service["repository_latest_sha_before"] = repo.get("latestCommitOid")
        service["activated"] = repo.get("isActivated")
        repo_id = repo.get("id")
        branch = repo.get("defaultBranch") or "main"
        if not repo_id:
            raise RuntimeError("repository id unavailable")
        mutation = """
        mutation Refresh($input: UpdateRepositoryDefaultBranchInput!) {
          updateRepositoryDefaultBranch(input:$input) { ok }
        }
        """
        result = ds_graphql(
            mutation,
            {"input": {"id": repo_id, "defaultBranchName": branch}},
        )
        service["requested"] = bool(
            (result.get("updateRepositoryDefaultBranch") or {}).get("ok")
        )
        if not service["requested"]:
            service["notes"].append("refresh mutation returned ok=false")
    except Exception as exc:
        service["notes"].append(f"request failed: {type(exc).__name__}: {str(exc)[:400]}")


def codescene_projects() -> tuple[list[dict[str, Any]], str | None]:
    if not CODESCENE_TOKEN:
        return [], "CODESCENE_TOKEN missing"
    status, payload = http_json(
        f"{CS_BASE}/projects",
        headers={"Authorization": f"Bearer {CODESCENE_TOKEN}", "Accept": "application/json"},
    )
    if status >= 400:
        return [], f"HTTP {status}"
    if isinstance(payload, list):
        return payload, None
    if isinstance(payload, dict):
        items = payload.get("projects") or payload.get("items") or payload.get("data") or []
        if isinstance(items, dict):
            items = list(items.values())
        return items if isinstance(items, list) else [], None
    return [], "unexpected response"


def find_codescene_project() -> tuple[dict[str, Any] | None, str | None]:
    projects, error = codescene_projects()
    if error:
        return None, error
    matches = [p for p in projects if isinstance(p, dict) and "niakvio" in json.dumps(p).lower()]
    if matches:
        return matches[0], None
    if len(projects) == 1 and isinstance(projects[0], dict):
        return projects[0], None
    return None, "NiakVIO project not found"


def request_codescene() -> None:
    service = state["services"]["codescene"]
    project, error = find_codescene_project()
    if error or not project:
        service["notes"].append(error or "project unavailable")
        return
    project_id = project.get("id") or project.get("project_id")
    service["project_id"] = project_id
    if project_id is None:
        service["notes"].append("project id unavailable")
        return
    status, payload = http_json(
        f"{CS_BASE}/projects/{project_id}/run-analysis",
        method="POST",
        headers={
            "Authorization": f"Bearer {CODESCENE_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        data=b"{}",
    )
    service["request_http_status"] = status
    if status < 300:
        service["requested"] = True
    else:
        service["notes"].append(f"run-analysis returned HTTP {status}: {str(payload)[:300]}")


def discover_sonar_project() -> str | None:
    if not SONAR_ORG:
        return None
    params = urllib.parse.urlencode({"organization": SONAR_ORG, "ps": 500, "p": 1})
    for path in ("/api/components/search_projects", "/api/components/search"):
        url = SONAR_BASE + path + "?" + params
        status, payload = http_json(url, headers={"Accept": "application/json"})
        if status >= 400 or not isinstance(payload, dict):
            continue
        components = payload.get("components") or []
        matches = [
            p for p in components
            if isinstance(p, dict)
            and (
                "niakvio" in str(p.get("name", "")).lower()
                or "niakvio" in str(p.get("key", "")).lower()
            )
        ]
        if matches:
            return str(matches[0].get("key") or "")
    return None


def sonar_latest() -> tuple[str | None, str | None]:
    key = state["services"]["sonar"].get("project_key") or discover_sonar_project()
    if not key:
        return None, None
    state["services"]["sonar"]["project_key"] = key
    params = urllib.parse.urlencode({"project": key, "ps": 10})
    status, payload = http_json(
        f"{SONAR_BASE}/api/project_analyses/search?{params}",
        headers={"Accept": "application/json"},
    )
    if status >= 400 or not isinstance(payload, dict):
        return None, None
    analyses = payload.get("analyses") or []
    if not analyses:
        return None, None
    first = analyses[0]
    return first.get("revision"), first.get("date")


def deepsource_current() -> tuple[bool, str | None, str | None]:
    if not DEEPSOURCE_TOKEN or not TARGET_SHA:
        return False, None, None
    try:
        data = ds_graphql(
            """query Run($oid:String!) {
              run(commitOid:$oid) { status commitOid createdAt finishedAt }
            }""",
            {"oid": TARGET_SHA},
        )
        run = data.get("run")
        if not run:
            return False, None, None
        status = str(run.get("status") or "")
        return status == "SUCCESS", status, run.get("finishedAt")
    except Exception:
        return False, None, None


def codescene_latest() -> tuple[str | None, str | None]:
    project_id = state["services"]["codescene"].get("project_id")
    if project_id is None:
        project, _ = find_codescene_project()
        if project:
            project_id = project.get("id") or project.get("project_id")
            state["services"]["codescene"]["project_id"] = project_id
    if project_id is None:
        return None, None
    status, payload = http_json(
        f"{CS_BASE}/projects/{project_id}/analyses/latest",
        headers={"Authorization": f"Bearer {CODESCENE_TOKEN}", "Accept": "application/json"},
    )
    if status >= 400 or not isinstance(payload, dict):
        return None, None
    revisions = payload.get("analysis_repo_revisions") or []
    revision = None
    for item in revisions:
        if isinstance(item, dict) and "niakvio" in str(item.get("repo", "")).lower():
            revision = item.get("revision")
            break
    if revision is None and revisions and isinstance(revisions[0], dict):
        revision = revisions[0].get("revision")
    return revision, payload.get("readable_analysis_time")


if not TARGET_SHA:
    state["services"]["sonar"]["notes"].append("AUDITED_SHA missing")
    state["services"]["deepsource"]["notes"].append("AUDITED_SHA missing")
    state["services"]["codescene"]["notes"].append("AUDITED_SHA missing")
    save()
    raise SystemExit(0)

# Sonar automatic analysis is triggered by GitHub pushes. There is no public
# force-reanalysis API in the no-token setup, so this step verifies and waits
# for the automatic analysis corresponding to TARGET_SHA.
state["services"]["sonar"]["requested"] = True
state["services"]["sonar"]["request_mode"] = "GitHub automatic analysis (latest main push)"

request_deepsource()
request_codescene()
save()

deadline = time.time() + WAIT_SECONDS
while True:
    sonar_revision, sonar_date = sonar_latest()
    sonar = state["services"]["sonar"]
    sonar["latest_sha"] = sonar_revision
    sonar["latest_analysis_at"] = sonar_date
    sonar["fresh"] = sonar_revision == TARGET_SHA

    ds_fresh, ds_status, ds_finished = deepsource_current()
    ds = state["services"]["deepsource"]
    ds["target_run_status"] = ds_status
    ds["target_run_finished_at"] = ds_finished
    ds["fresh"] = ds_fresh

    cs_revision, cs_date = codescene_latest()
    cs = state["services"]["codescene"]
    cs["latest_sha"] = cs_revision
    cs["latest_analysis_at"] = cs_date
    cs["fresh"] = cs_revision == TARGET_SHA

    save()
    fresh = [state["services"][name]["fresh"] for name in ("sonar", "deepsource", "codescene")]
    print(
        "freshness:",
        f"sonar={fresh[0]}",
        f"deepsource={fresh[1]}",
        f"codescene={fresh[2]}",
        flush=True,
    )
    if all(fresh):
        break
    if time.time() >= deadline:
        for name in ("sonar", "deepsource", "codescene"):
            if not state["services"][name]["fresh"]:
                state["services"][name]["notes"].append(
                    f"did not reach target SHA within {WAIT_SECONDS}s"
                )
        save()
        break
    time.sleep(POLL_SECONDS)

save()
