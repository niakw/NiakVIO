#!/usr/bin/env python3
"""Export DeepSource findings for AI consumption via the official GraphQL API."""

from __future__ import annotations

import json
import os
import pathlib
import urllib.error
import urllib.request
from collections import Counter
from typing import Any

ENDPOINT = "https://api.deepsource.com/graphql/"
REPO_LOGIN = "niakw"
REPO_NAME = "NiakVIO"

OUT = pathlib.Path(os.environ.get("OUT", "audit/ai-external")) / "deepsource"
OUT.mkdir(parents=True, exist_ok=True)
TOKEN = os.environ.get("DEEPSOURCE_API", "").strip()

status: dict[str, Any] = {
    "source": "DeepSource",
    "ok": False,
    "errors": [],
    "access_mode": "GraphQL API bearer token",
    "endpoint": ENDPOINT,
    "repository": f"{REPO_LOGIN}/{REPO_NAME}",
}


def save(name: str, value: Any) -> None:
    (OUT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def graphql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "NiakVIO-external-audit/2.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[:1200]
        except Exception:
            detail = ""
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc

    if payload.get("errors"):
        messages = "; ".join(
            str(item.get("message", "GraphQL error"))
            for item in payload["errors"][:10]
        )
        raise RuntimeError(messages)
    return payload.get("data") or {}


def fail(message: str) -> None:
    status["errors"].append(message)
    save("status.json", status)
    raise SystemExit(0)


if not TOKEN:
    fail("DEEPSOURCE_API repository secret is missing/unavailable")

# Verify authentication without persisting profile data.
try:
    graphql("query { viewer { email } }")
except Exception as exc:
    fail(f"API authentication failed: {str(exc)[:600]}")

REPOSITORY_ISSUES_QUERY = r"""
query Repo($name:String!, $login:String!, $after:String) {
  repository(name:$name, login:$login, vcsProvider:GITHUB) {
    id
    name
    defaultBranch
    latestCommitOid
    isPrivate
    isActivated
    issues(first:100, after:$after) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id
          issue {
            shortcode
            title
            severity
            category
            shortDescription
            description
            tags
            autofixAvailable
            autofixAiAvailable
            isRecommended
          }
        }
      }
    }
  }
}
"""

repository_meta: dict[str, Any] | None = None
repository_issues: list[dict[str, Any]] = []
cursor: str | None = None

try:
    for _ in range(200):
        data = graphql(
            REPOSITORY_ISSUES_QUERY,
            {"name": REPO_NAME, "login": REPO_LOGIN, "after": cursor},
        )
        repository = data.get("repository")
        if not repository:
            raise RuntimeError("repository query returned null for niakw/NiakVIO")
        if repository_meta is None:
            repository_meta = {
                key: value for key, value in repository.items() if key != "issues"
            }
        connection = repository.get("issues") or {}
        repository_issues.extend(
            edge["node"]
            for edge in connection.get("edges", [])
            if edge.get("node")
        )
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    save("repository.json", repository_meta or {})
except Exception as exc:
    fail(f"repository/issues query failed: {str(exc)[:800]}")

OCCURRENCES_QUERY = r"""
query Occurrences($id:ID!, $after:String) {
  node(id:$id) {
    ... on RepositoryIssue {
      occurrences(first:100, after:$after) {
        totalCount
        pageInfo { hasNextPage endCursor }
        edges {
          node {
            id
            path
            beginLine
            beginColumn
            endLine
            endColumn
          }
        }
      }
    }
  }
}
"""

findings: list[dict[str, Any]] = []
structured_issues: list[dict[str, Any]] = []

for repository_issue in repository_issues:
    issue = repository_issue.get("issue") or {}
    occurrences: list[dict[str, Any]] = []
    cursor = None
    try:
        for _ in range(200):
            data = graphql(
                OCCURRENCES_QUERY,
                {"id": repository_issue.get("id"), "after": cursor},
            )
            node = data.get("node") or {}
            connection = node.get("occurrences") or {}
            batch = [
                edge["node"]
                for edge in connection.get("edges", [])
                if edge.get("node")
            ]
            occurrences.extend(batch)
            page_info = connection.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            if not cursor:
                break
    except Exception as exc:
        status["errors"].append(
            f"occurrence pagination failed for {issue.get('shortcode', '?')}: "
            f"{str(exc)[:250]}"
        )

    structured_issues.append(
        {
            "repositoryIssueId": repository_issue.get("id"),
            "issue": issue,
            "occurrenceCount": len(occurrences),
            "occurrences": occurrences,
        }
    )
    for occurrence in occurrences:
        findings.append(
            {
                "shortcode": issue.get("shortcode"),
                "title": issue.get("title"),
                "severity": issue.get("severity"),
                "category": issue.get("category"),
                "shortDescription": issue.get("shortDescription"),
                "autofixAvailable": issue.get("autofixAvailable"),
                "autofixAiAvailable": issue.get("autofixAiAvailable"),
                "isRecommended": issue.get("isRecommended"),
                **occurrence,
            }
        )

save("issues.json", structured_issues)
save("findings.json", findings)

VULNERABILITIES_QUERY = r"""
query Vulnerabilities($name:String!, $login:String!, $after:String) {
  repository(name:$name, login:$login, vcsProvider:GITHUB) {
    dependencyVulnerabilityOccurrences(first:100, after:$after) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id
          reachability
          fixability
          vulnerability {
            identifier
            aliases
            summary
            severity
            cvssV3BaseScore
            cvssV3Severity
            epssScore
            publishedAt
            fixedVersions
            referenceUrls
          }
          package { name ecosystem }
          packageVersion { version }
        }
      }
    }
  }
}
"""

vulnerabilities: list[dict[str, Any]] = []
cursor = None
try:
    for _ in range(200):
        data = graphql(
            VULNERABILITIES_QUERY,
            {"name": REPO_NAME, "login": REPO_LOGIN, "after": cursor},
        )
        connection = (
            (data.get("repository") or {}).get("dependencyVulnerabilityOccurrences")
            or {}
        )
        vulnerabilities.extend(
            edge["node"]
            for edge in connection.get("edges", [])
            if edge.get("node")
        )
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
except Exception as exc:
    status["errors"].append(
        f"dependency vulnerabilities query failed: {str(exc)[:500]}"
    )
save("vulnerabilities.json", vulnerabilities)

RUNS_QUERY = r"""
query Runs($name:String!, $login:String!, $after:String) {
  repository(name:$name, login:$login, vcsProvider:GITHUB) {
    analysisRuns(first:50, after:$after) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          runUid
          status
          branchName
          baseOid
          commitOid
          createdAt
          finishedAt
          summary {
            occurrencesIntroduced
            occurrencesResolved
            occurrencesSuppressed
            vulnerabilitiesIntroduced
            occurrenceDistributionByAnalyzer { analyzerShortcode introduced }
            occurrenceDistributionByCategory { category introduced }
          }
        }
      }
    }
  }
}
"""

analysis_runs: list[dict[str, Any]] = []
cursor = None
try:
    for _ in range(20):
        data = graphql(
            RUNS_QUERY,
            {"name": REPO_NAME, "login": REPO_LOGIN, "after": cursor},
        )
        connection = (data.get("repository") or {}).get("analysisRuns") or {}
        analysis_runs.extend(
            edge["node"]
            for edge in connection.get("edges", [])
            if edge.get("node")
        )
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
except Exception as exc:
    status["errors"].append(f"analysis runs query failed: {str(exc)[:500]}")
save("analysis-runs.json", analysis_runs)

severity_counts = Counter(str(item.get("severity") or "UNKNOWN") for item in findings)
category_counts = Counter(str(item.get("category") or "UNKNOWN") for item in findings)
autofix_count = sum(bool(item.get("autofixAvailable")) for item in findings)
ai_autofix_count = sum(bool(item.get("autofixAiAvailable")) for item in findings)

lines = [
    "# DeepSource API audit",
    "",
    "- Access: official DeepSource GraphQL API using GitHub Actions secret `DEEPSOURCE_API`.",
    "- Endpoint: `https://api.deepsource.com/graphql/`",
    f"- Repository: `{REPO_LOGIN}/{REPO_NAME}`",
    f"- Default branch: `{(repository_meta or {}).get('defaultBranch')}`",
    f"- Repository issue rules exported: **{len(structured_issues)}**",
    f"- Concrete issue occurrences exported: **{len(findings)}**",
    f"- Dependency vulnerabilities exported: **{len(vulnerabilities)}**",
    f"- Analysis runs exported: **{len(analysis_runs)}**",
    f"- Autofix-capable occurrences: **{autofix_count}**",
    f"- AI-autofix-capable occurrences: **{ai_autofix_count}**",
    "- Severity: "
    + (", ".join(f"`{key}` {value}" for key, value in severity_counts.most_common()) or "none"),
    "- Category: "
    + (", ".join(f"`{key}` {value}" for key, value in category_counts.most_common()) or "none"),
    "",
    "## Findings",
    "",
]

for finding in findings:
    location = f"{finding.get('path', '?')}:{finding.get('beginLine', '?')}"
    message = " ".join(
        str(finding.get("shortDescription") or finding.get("title") or "").split()
    )
    flags: list[str] = []
    if finding.get("isRecommended"):
        flags.append("recommended")
    if finding.get("autofixAvailable"):
        flags.append("autofix")
    if finding.get("autofixAiAvailable"):
        flags.append("AI-autofix")
    suffix = f" [{', '.join(flags)}]" if flags else ""
    lines.append(
        f"- `{location}` **{finding.get('severity', '?')} / {finding.get('category', '?')}** "
        f"`{finding.get('shortcode', '?')}` — {message}{suffix}"
    )

if vulnerabilities:
    lines.extend(["", "## Dependency vulnerabilities", ""])
    for item in vulnerabilities:
        vulnerability = item.get("vulnerability") or {}
        package = item.get("package") or {}
        version = item.get("packageVersion") or {}
        lines.append(
            f"- `{vulnerability.get('identifier', '?')}` **{vulnerability.get('severity', '?')}** "
            f"`{package.get('name', '?')}@{version.get('version', '?')}` — "
            f"{vulnerability.get('summary') or ''} (fixability `{item.get('fixability', '?')}`)"
        )

(OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

status.update(
    {
        "ok": bool(repository_meta),
        "finding_count": len(findings),
        "issue_rule_count": len(structured_issues),
        "vulnerability_count": len(vulnerabilities),
        "analysis_run_count": len(analysis_runs),
        "default_branch": (repository_meta or {}).get("defaultBranch"),
    }
)
save("status.json", status)
