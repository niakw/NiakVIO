#!/usr/bin/env python3
"""Export public SonarQube Cloud findings for AI consumption."""

from __future__ import annotations

import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any

OUT = pathlib.Path(os.environ.get("OUT", "audit/ai-external")) / "sonar"
OUT.mkdir(parents=True, exist_ok=True)
ORG = os.environ.get("SONAR_KEY", "").strip()
BASE = "https://sonarcloud.io"

status: dict[str, Any] = {
    "source": "SonarQube Cloud",
    "ok": False,
    "errors": [],
    "access_mode": "public organization key",
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


if not ORG:
    status["errors"].append("SONAR_KEY repository secret is missing/unavailable")
    save("status.json", status)
    raise SystemExit(0)

projects, error = get(
    "/api/components/search_projects",
    {"organization": ORG, "ps": 500, "p": 1},
)
if error or not isinstance(projects, dict):
    projects, error = get(
        "/api/components/search",
        {"organization": ORG, "qualifiers": "TRK", "ps": 500, "p": 1},
    )
if error or not isinstance(projects, dict):
    status["errors"].append(f"public project discovery failed: {error}")
    save("status.json", status)
    raise SystemExit(0)

save("projects.json", projects)
components = projects.get("components", [])
matches = [
    project
    for project in components
    if "niakvio" in str(project.get("name", "")).lower()
    or "niakvio" in str(project.get("key", "")).lower()
]
project = matches[0] if matches else (components[0] if len(components) == 1 else None)
if not project:
    status["errors"].append("NiakVIO project not found in public organization project list")
    status["project_count"] = len(components)
    save("status.json", status)
    raise SystemExit(0)

project_key = project.get("key")
status["project"] = project.get("name") or project_key
status["project_key"] = project_key

issues: list[dict[str, Any]] = []
for page in range(1, 201):
    payload, issue_error = get(
        "/api/issues/search",
        {
            "componentKeys": project_key,
            "resolved": "false",
            "ps": 500,
            "p": page,
        },
    )
    if issue_error or not isinstance(payload, dict):
        status["errors"].append(f"public issues export unavailable: {issue_error}")
        break
    batch = payload.get("issues", [])
    issues.extend(batch)
    total = (payload.get("paging") or {}).get("total", payload.get("total", len(issues)))
    if not batch or len(issues) >= int(total or 0):
        break
save("issues.json", issues)

hotspots, hotspot_error = get(
    "/api/hotspots/search",
    {"projectKey": project_key, "ps": 500},
)
save(
    "hotspots.json",
    hotspots
    if hotspots is not None
    else {"hotspots": [], "unavailable": True, "error": hotspot_error},
)

measures, measures_error = get(
    "/api/measures/component",
    {
        "component": project_key,
        "metricKeys": (
            "bugs,vulnerabilities,security_hotspots,code_smells,"
            "duplicated_lines_density,cognitive_complexity,complexity,sqale_index,"
            "reliability_rating,security_rating,sqale_rating,ncloc,coverage"
        ),
    },
)
save(
    "measures.json",
    measures if measures is not None else {"unavailable": True, "error": measures_error},
)

analyses, analyses_error = get(
    "/api/project_analyses/search",
    {"project": project_key, "ps": 100},
)
save(
    "analyses.json",
    analyses if analyses is not None else {"unavailable": True, "error": analyses_error},
)

severity_counts = Counter(str(issue.get("severity", "UNKNOWN")) for issue in issues)
type_counts = Counter(str(issue.get("type", "UNKNOWN")) for issue in issues)
lines = [
    "# SonarQube Cloud audit",
    "",
    "- Access: public Sonar organization/project; no Sonar login or API token used.",
    f"- Project: `{status['project']}`",
    f"- Project key: `{project_key}`",
    f"- Open findings exported: **{len(issues)}**",
    "- Severity: "
    + (", ".join(f"`{key}` {value}" for key, value in severity_counts.most_common()) or "none"),
    "- Type: "
    + (", ".join(f"`{key}` {value}" for key, value in type_counts.most_common()) or "none"),
    "",
    "## Findings",
    "",
]
for issue in issues:
    component = str(issue.get("component", "?"))
    line = issue.get("line") or (issue.get("textRange") or {}).get("startLine")
    location = f"{component}:{line}" if line else component
    message = " ".join(str(issue.get("message", "")).split())
    lines.append(
        f"- `{location}` **{issue.get('severity', '?')} / {issue.get('type', '?')}** "
        f"`{issue.get('rule', '?')}` — {message}"
    )
(OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

status.update(
    {
        "ok": True,
        "finding_count": len(issues),
        "public_measures_available": measures is not None,
        "public_hotspots_available": hotspots is not None,
    }
)
save("status.json", status)
