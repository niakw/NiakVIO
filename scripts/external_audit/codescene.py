#!/usr/bin/env python3
"""Export CodeScene REST API data for AI consumption."""

from __future__ import annotations

import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

OUT = pathlib.Path(os.environ.get("OUT", "audit/ai-external")) / "codescene"
OUT.mkdir(parents=True, exist_ok=True)
TOKEN = os.environ.get("CODESCENE_TOKEN", "").strip()
BASE = "https://api.codescene.io/v2"

status: dict[str, Any] = {
    "source": "CodeScene",
    "ok": False,
    "errors": [],
    "access_mode": "REST API bearer token",
}


def save(name: str, value: Any) -> None:
    (OUT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get(path: str, params: dict[str, Any] | None = None) -> tuple[Any | None, str | None]:
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Accept": "application/json",
                "User-Agent": "NiakVIO-external-audit/2.0",
            },
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:
        return None, type(exc).__name__


if not TOKEN:
    status["errors"].append("CODESCENE_TOKEN repository secret is missing/unavailable")
    save("status.json", status)
    raise SystemExit(0)

projects, error = get("/projects")
if projects is None:
    status["errors"].append(f"project discovery failed: {error}")
    save("status.json", status)
    raise SystemExit(0)
save("projects.json", projects)

if isinstance(projects, list):
    project_list = projects
elif isinstance(projects, dict):
    project_list = projects.get("projects") or projects.get("items") or projects.get("data") or []
else:
    project_list = []
if isinstance(project_list, dict):
    project_list = list(project_list.values())

matches = [
    project
    for project in project_list
    if isinstance(project, dict) and "niakvio" in json.dumps(project).lower()
]
project = matches[0] if matches else (
    project_list[0]
    if project_list and isinstance(project_list[0], dict)
    else None
)
if not project:
    status["errors"].append("NiakVIO project not found")
    save("status.json", status)
    raise SystemExit(0)

project_id = project.get("id") or project.get("project_id")
if project_id is None:
    status["errors"].append("project id not returned by API")
    save("status.json", status)
    raise SystemExit(0)
status["project"] = project.get("name") or str(project_id)

latest, latest_error = get(f"/projects/{project_id}/analyses/latest")
save(
    "analysis-latest.json",
    latest if latest is not None else {"unavailable": True, "error": latest_error},
)

files: list[dict[str, Any]] = []
for page in range(1, 201):
    payload, file_error = get(
        f"/projects/{project_id}/analyses/latest/files",
        {"page": page, "page_size": 100, "order_by": "code_health"},
    )
    if payload is None:
        status["errors"].append(f"files export: {file_error}")
        break
    if isinstance(payload, dict):
        batch = payload.get("files", [])
    elif isinstance(payload, list):
        batch = payload
    else:
        batch = []
    files.extend(batch)
    if len(batch) < 100:
        break
save("files.json", files)

hotspots, hotspot_error = get(f"/projects/{project_id}/analyses/latest/hotspots")
save(
    "hotspots.json",
    hotspots
    if hotspots is not None
    else {"hotspots": [], "unavailable": True, "error": hotspot_error},
)

architecture_hotspots = None
for endpoint in (
    "architecture/hotspots",
    "architectural-hotspots",
    "architecture-hotspots",
):
    architecture_hotspots, _ = get(
        f"/projects/{project_id}/analyses/latest/{endpoint}"
    )
    if architecture_hotspots is not None:
        break
save(
    "architecture-hotspots.json",
    architecture_hotspots
    if architecture_hotspots is not None
    else {"unavailable": True},
)

latest_summary = latest.get("summary", {}) if isinstance(latest, dict) else {}
high_level = latest.get("high_level_metrics", {}) if isinstance(latest, dict) else {}
lines = [
    "# CodeScene audit",
    "",
    f"- Project: `{status['project']}`",
    f"- File metrics exported: **{len(files)}**",
]
if high_level:
    lines.extend(
        [
            f"- Code Health weighted average: `{high_level.get('code_health_weighted_average_current')}`",
            f"- Hotspot score: `{high_level.get('current_score')}`",
        ]
    )
if latest_summary:
    lines.append(
        f"- Files with Code Health: `{latest_summary.get('files_with_code_health')}`"
    )
lines.extend(["", "## Files", ""])
for file_item in files:
    if not isinstance(file_item, dict):
        continue
    name = file_item.get("name") or file_item.get("path") or "?"
    lines.append(
        f"- `{name}` — changes `{file_item.get('change_frequency', '?')}`; "
        f"defects `{file_item.get('number_of_defects', '?')}`; "
        f"LOC `{file_item.get('lines_of_code', '?')}`; "
        f"Code Health `{file_item.get('code_health', '?')}`"
    )
(OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

status.update({"ok": True, "file_count": len(files)})
save("status.json", status)
