#!/usr/bin/env python3
"""Retire obsolete one-shot CodeQL analysis sets after exact maintained proof.

The historical SEC - One-shot Full Audit scanned every retained generated
provider version. Production now has a stricter maintained matrix:
- Actions
- Python
- JS Core
- exact published Active Providers
- ProviderBase

This cleanup deletes only the old analysis *sets* after all replacement
categories have analyzed the exact main SHA and no current maintained CodeQL
alert remains open. It never dismisses findings and never deletes provider
files or their 10-version retention history.
"""
from __future__ import annotations

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import retire_stale_codeql_2531 as guard
from delete_stale_codeql_2531_configuration import _analysis_delete_path

REPO = guard.REPO
MAIN_REF = "refs/heads/main"
MAINTAINED_KEY = ".github/workflows/codeql.yml:analyze"
STALE_ONE_SHOT_KEY = ".github/workflows/security-audit-now.yml:codeql"

REQUIRED_CATEGORY_MARKERS = (
    "/language:actions",
    "/language:python",
    "/language:javascript-typescript/scope:core",
    "/language:javascript-typescript/scope:active-providers",
    "/language:javascript-typescript/scope:provider-bases",
)


def is_codeql(row: dict) -> bool:
    return str((row.get("tool") or {}).get("name") or "").casefold() == "codeql"


def maintained_categories(rows: list[dict], sha: str) -> set[str]:
    return {
        str(row.get("category") or "")
        for row in rows
        if isinstance(row, dict)
        and is_codeql(row)
        and row.get("commit_sha") == sha
        and str(row.get("analysis_key") or "") == MAINTAINED_KEY
    }


def replacement_complete(rows: list[dict], sha: str) -> bool:
    categories = maintained_categories(rows, sha)
    return all(
        any(marker in category for category in categories)
        for marker in REQUIRED_CATEGORY_MARKERS
    )


def stale_one_shot_categories(rows: list[dict]) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = {}
    for row in rows:
        if not isinstance(row, dict) or not is_codeql(row):
            continue
        if str(row.get("analysis_key") or "") != STALE_ONE_SHOT_KEY:
            continue
        category = str(row.get("category") or "")
        if "/one-shot" not in category:
            continue
        found.setdefault(category, []).append(row)
    return found


def list_main_analyses() -> list[dict]:
    rows = guard.read_pages(
        "repos/" + REPO + "/code-scanning/analyses?ref=" + MAIN_REF
        + "&tool_name=CodeQL&sort=created&direction=asc",
        max_pages=500,
    )
    if not all(isinstance(row, dict) for row in rows):
        raise RuntimeError("Invalid CodeQL analysis listing")
    return rows


def current_maintained_open_alerts(expected: str) -> list[dict]:
    rows = guard.read_pages(
        "repos/" + REPO + "/code-scanning/alerts?state=open&ref=" + MAIN_REF,
        max_pages=10,
    )
    current: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        recent = row.get("most_recent_instance") or {}
        if (
            str((row.get("tool") or {}).get("name") or "").casefold() == "codeql"
            and str(recent.get("analysis_key") or "") == MAINTAINED_KEY
            and str(recent.get("commit_sha") or "") == expected
        ):
            current.append(row)
    return current


def delete_category(category: str, rows: list[dict]) -> int:
    matching = stale_one_shot_categories(rows).get(category, [])
    if not matching:
        return 0
    deletable = [row for row in matching if row.get("deletable") is True]
    if len(deletable) != 1:
        raise RuntimeError(
            "Expected exactly one deletable analysis for stale one-shot category "
            + category + ", got " + str(len(deletable))
        )
    analysis_id = deletable[0].get("id")
    if not isinstance(analysis_id, int) or analysis_id <= 0:
        raise RuntimeError("Invalid stale CodeQL analysis id")

    response = guard.api(
        "repos/" + REPO + "/code-scanning/analyses/" + str(analysis_id),
        "DELETE",
    )
    if not isinstance(response, dict):
        raise RuntimeError("GitHub returned invalid stale-analysis deletion response")
    deleted = 1
    for _ in range(499):
        continuation = response.get("confirm_delete_url")
        if not continuation:
            return deleted
        response = guard.api(_analysis_delete_path(continuation), "DELETE")
        deleted += 1
        if response is None:
            return deleted
        if not isinstance(response, dict):
            raise RuntimeError("GitHub returned invalid stale-analysis deletion response")
    raise RuntimeError("Stale one-shot CodeQL category exceeded bounded deletions")


def remaining_stale_alerts() -> list[dict]:
    rows = guard.read_pages(
        "repos/" + REPO + "/code-scanning/alerts?state=open&ref=" + MAIN_REF,
        max_pages=10,
    )
    return [
        row for row in rows
        if isinstance(row, dict)
        and str(((row.get("most_recent_instance") or {}).get("analysis_key") or ""))
        == STALE_ONE_SHOT_KEY
    ]


def main() -> None:
    expected = guard.scan_source_sha()
    branch = guard.api("repos/" + REPO + "/branches/main")
    head = (branch or {}).get("commit", {}).get("sha")
    if not head or not guard.evidence_only_drift(expected, head):
        raise RuntimeError(
            "CodeQL one-shot cleanup deferred: maintained scan is not current main"
        )

    rows = list_main_analyses()
    if not replacement_complete(rows, expected):
        raise RuntimeError(
            "Exact-main maintained CodeQL matrix is incomplete; stale cleanup forbidden"
        )

    open_current = current_maintained_open_alerts(expected)
    if open_current:
        numbers = sorted(
            int(row.get("number"))
            for row in open_current
            if isinstance(row.get("number"), int)
        )
        raise RuntimeError(
            "Current maintained CodeQL alerts remain open: "
            + ",".join(str(value) for value in numbers[:20])
        )

    categories = stale_one_shot_categories(rows)
    if not categories:
        print(
            "FIELD_CODEQL_ONE_SHOT_CLEANUP categories=0 analyses=0 "
            "already_absent=true retention_unchanged=true"
        )
        return

    removed: dict[str, int] = {}
    for category in sorted(categories):
        removed[category] = delete_category(category, rows)

    remaining = remaining_stale_alerts()
    if remaining:
        raise RuntimeError(
            "Stale one-shot CodeQL alerts remain after configuration deletion: "
            + ",".join(str(row.get("number") or "?") for row in remaining[:20])
        )

    after = (guard.api("repos/" + REPO + "/branches/main") or {}).get(
        "commit", {}
    ).get("sha")
    if not after or not guard.evidence_only_drift(expected, after):
        raise RuntimeError("Main moved in executable way during one-shot CodeQL cleanup")

    print(
        "FIELD_CODEQL_ONE_SHOT_CLEANUP categories="
        + str(len(removed))
        + " analyses="
        + str(sum(removed.values()))
        + " alerts_remaining=0 retention_unchanged=true"
    )


if __name__ == "__main__":
    main()
