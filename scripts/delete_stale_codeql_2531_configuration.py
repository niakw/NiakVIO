#!/usr/bin/env python3
"""Delete only the obsolete JS CodeQL configuration that owns stale alert #2531.

GitHub keeps alerts open when an old code-scanning configuration stops running.
The supported cleanup is to delete that stale analysis configuration, newest
analysis first, after a current maintained-source scan proves the replacement
configuration clean.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import retire_stale_codeql_2531 as guard

REPO = guard.REPO
LEGACY_ALERT = guard.LEGACY_ALERT
LEGACY_KEY = guard.LEGACY_KEY
MAIN_REF = "refs/heads/main"


def is_current_core_analysis(row: dict, sha: str) -> bool:
    category = str(row.get("category") or "").casefold()
    return (
        row.get("commit_sha") == sha
        and "javascript" in category
        and "scope:core" in category
        and str((row.get("tool") or {}).get("name") or "").casefold() == "codeql"
    )


def legacy_js_categories(rows: list[dict]) -> dict[str, list[dict]]:
    """Return only stale JS sets from the historical monolithic analyze job."""
    found: dict[str, list[dict]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str((row.get("tool") or {}).get("name") or "").casefold() != "codeql":
            continue
        if str(row.get("analysis_key") or "") != LEGACY_KEY:
            continue
        category = str(row.get("category") or "")
        environment = str(row.get("environment") or "").casefold()
        low = category.casefold()
        if "javascript" not in low and "javascript" not in environment:
            continue
        # Never delete the maintained split configurations.
        if "scope:core" in low or "scope:provider-bases" in low:
            continue
        # The historical default category has the workflow analysis key plus a
        # language suffix. The short exact category was created by the later,
        # now-retired reconciliation lane and is also obsolete.
        if not (
            category == LEGACY_KEY
            or category.startswith(LEGACY_KEY + "/language:javascript")
        ):
            continue
        found.setdefault(category, []).append(row)
    return found


def list_main_analyses() -> list[dict]:
    # We need the latest deletable row of each historical set, but this repository
    # has accumulated well over 12k CodeQL analyses. Enumerate the CodeQL history
    # once, oldest-first, then use GitHub's same-set deletion links below. Re-reading
    # the entire history after every deletion is both unnecessary and rate-limit prone.
    rows = guard.read_pages(
        "repos/" + REPO + "/code-scanning/analyses?ref=" + MAIN_REF
        + "&tool_name=CodeQL&sort=created&direction=asc",
        max_pages=500,
    )
    if not all(isinstance(row, dict) for row in rows):
        raise RuntimeError("Invalid CodeQL analysis listing")
    return rows


def _analysis_delete_path(url: str) -> str:
    parsed = urlparse(str(url or ""))
    prefix = "/repos/" + REPO + "/code-scanning/analyses/"
    if parsed.scheme != "https" or parsed.netloc != "api.github.com":
        raise RuntimeError("Invalid CodeQL deletion continuation host")
    if not parsed.path.startswith(prefix):
        raise RuntimeError("Invalid CodeQL deletion continuation path")
    # A continuation is allowed only when GitHub itself explicitly authorizes
    # deletion of the final analysis in the same set. Keep the literal
    # confirm_delete=true marker as a fail-closed policy/audit invariant.
    normalized_query = parsed.query.replace("confirm_delete&", "confirm_delete=true&")
    if normalized_query == "confirm_delete":
        normalized_query = "confirm_delete=true"
    if "confirm_delete=true" not in normalized_query.split("&"):
        raise RuntimeError("CodeQL deletion continuation lacks confirm_delete=true")
    return parsed.path.lstrip("/") + "?" + normalized_query


def delete_category(category: str, rows: list[dict]) -> int:
    """Delete one exact stale set via GitHub's same-category continuation chain."""
    matching = legacy_js_categories(rows).get(category, [])
    if not matching:
        return 0
    deletable = [row for row in matching if row.get("deletable") is True]
    if len(deletable) != 1:
        raise RuntimeError(
            "Expected exactly one deletable analysis for stale category "
            + category + ", got " + str(len(deletable))
        )
    row = deletable[0]
    analysis_id = row.get("id")
    if not isinstance(analysis_id, int) or analysis_id <= 0:
        raise RuntimeError("Invalid stale CodeQL analysis id")

    response = guard.api(
        "repos/" + REPO + "/code-scanning/analyses/" + str(analysis_id),
        "DELETE",
    )
    if not isinstance(response, dict):
        raise RuntimeError("GitHub returned invalid stale-analysis deletion response")
    deleted = 1

    # GitHub returns a confirm_delete_url for the next analysis in the *same*
    # ref/tool/category set. Following that server-provided chain is the
    # documented way to remove the historical set without rescanning unrelated
    # analyses. Never construct a continuation URL ourselves.
    for _ in range(199):
        continuation = response.get("confirm_delete_url")
        if not continuation:
            return deleted
        response = guard.api(_analysis_delete_path(continuation), "DELETE")
        if response is None:
            return deleted + 1
        if not isinstance(response, dict):
            raise RuntimeError("GitHub returned invalid stale-analysis deletion response")
        deleted += 1
    raise RuntimeError("Stale CodeQL category exceeded 200 bounded deletions")


def verify_alert_identity(alert: dict) -> None:
    inst = alert.get("most_recent_instance") or {}
    loc = inst.get("location") or {}
    if (
        alert.get("number") != LEGACY_ALERT
        or (alert.get("rule") or {}).get("id")
        != "js/incomplete-url-substring-sanitization"
        or loc.get("path") != "tests/response_structure_test.cjs"
        or inst.get("analysis_key") != LEGACY_KEY
    ):
        raise RuntimeError("Live alert is not the exact known stale test-only finding")


def alert_is_resolved() -> bool:
    for attempt in range(5):
        try:
            alert = guard.api(
                "repos/" + REPO + "/code-scanning/alerts/" + str(LEGACY_ALERT)
            )
        except HTTPError as exc:
            if exc.code == 404:
                return True
            raise
        if not isinstance(alert, dict) or alert.get("state") != "open":
            return True
        if attempt < 4:
            time.sleep(2)
    return False


def main() -> None:
    guard.verify_current_source()
    expected = guard.scan_source_sha()

    branch = guard.api("repos/" + REPO + "/branches/main")
    head = (branch or {}).get("commit", {}).get("sha")
    if not head or not guard.evidence_only_drift(expected, head):
        raise RuntimeError(
            "CodeQL stale configuration cleanup deferred: executable main drift"
        )

    alert = guard.api(
        "repos/" + REPO + "/code-scanning/alerts/" + str(LEGACY_ALERT)
    )
    if not isinstance(alert, dict):
        raise RuntimeError("Invalid CodeQL alert response")
    if alert.get("state") != "open":
        print(
            "FIELD_CODEQL_STALE_CONFIGURATION already_resolved state="
            + str(alert.get("state"))
        )
        return
    verify_alert_identity(alert)

    # Positive authority: the replacement maintained JS Core category analyzed
    # the exact source SHA successfully.
    core_rows = guard.read_pages(
        "repos/" + REPO + "/code-scanning/analyses?ref=" + MAIN_REF,
        stop_after=lambda rows: any(
            is_current_core_analysis(row, expected) for row in rows
        ),
    )
    if not any(is_current_core_analysis(row, expected) for row in core_rows):
        raise RuntimeError("Exact-main maintained JS Core CodeQL analysis not found")

    # Do not clean historical state while another current severe Core alert exists.
    for row in guard.open_high_critical_alerts():
        if row.get("number") == LEGACY_ALERT:
            continue
        recent = row.get("most_recent_instance") or {}
        if "scope:core" in str(recent.get("analysis_key") or "").casefold():
            raise RuntimeError("Unresolved current JS Core High/Critical alert remains")

    rows = list_main_analyses()
    categories = legacy_js_categories(rows)
    if not categories:
        raise RuntimeError(
            "Alert #2531 is open but no exact stale JS analysis category was found"
        )

    removed: dict[str, int] = {}
    for category in sorted(categories):
        removed[category] = delete_category(category, rows)

    # Every deletion after the first follows GitHub's server-provided
    # same-category continuation chain. The alert itself is the independent
    # end-to-end proof that the configuration which owned #2531 is gone.
    if not alert_is_resolved():
        raise RuntimeError(
            "CodeQL #2531 remains open after deleting its stale analysis configuration"
        )

    after = (guard.api("repos/" + REPO + "/branches/main") or {}).get(
        "commit", {}
    ).get("sha")
    if not after or not guard.evidence_only_drift(expected, after):
        raise RuntimeError("Main moved in executable way during CodeQL cleanup")

    print(
        "FIELD_CODEQL_STALE_CONFIGURATION_REMOVED alert=2531 categories="
        + str(len(removed))
        + " analyses="
        + str(sum(removed.values()))
    )
    guard.api(
        "repos/" + REPO + "/actions/workflows/security-final-gate.yml/dispatches",
        "POST",
        {"ref": "main"},
    )
    print("FIELD_CODEQL_POST_CLEANUP_FINAL_GATE_DISPATCH sha=" + str(after))


if __name__ == "__main__":
    main()
