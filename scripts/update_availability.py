#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Update frequent availability history and cautiously toggle published entries.

Only hard availability failures count toward automatic disabling. Datacenter
blocks, rate limits and empty search results are recorded but do not disable a
provider. Providers disabled by this script can be re-enabled after repeated
successful checks only when the last publication audit marked them eligible,
either through all ten strict gates, finite strict grace, or exact SHA-pinned Nuvio
runtime evidence. Manually disabled entries are never force-enabled.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.json"
NEXT_MANIFEST_PATH = ROOT / "manifest.next.json"
CONFIG_PATH = ROOT / "health-config.json"
SOURCES_PATH = ROOT / "sources.json"
RESULTS_PATH = Path(os.environ.get("NUVIO_HEALTH_RESULTS", ROOT / "health-results.json")).resolve()
HISTORY_PATH = ROOT / "availability-history.json"
REPORT_PATH = ROOT / "availability-report.json"
PROVENANCE_PATH = ROOT / "PROVENANCE.json"


def load_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def atomic_write_json(path: Path, payload: Any) -> None:
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def file_sha(entry: dict[str, Any]) -> str | None:
    filename = entry.get("filename")
    if not isinstance(filename, str):
        return None
    path = (ROOT / filename).resolve()
    try:
        path.relative_to((ROOT / "providers").resolve())
    except ValueError:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main() -> int:
    manifest = load_json(MANIFEST_PATH, {"scrapers": []})
    config = load_json(CONFIG_PATH, {})
    sources = load_json(SOURCES_PATH, {})
    results = load_json(RESULTS_PATH, {})
    history = load_json(HISTORY_PATH, {"schema_version": 63, "providers": {}})
    provenance = load_json(PROVENANCE_PATH, {"providers": {}})
    previous_report = load_json(REPORT_PATH, {})
    if results.get("mode") not in {"availability", "retry"}:
        raise RuntimeError("availability or retry health results are required")

    policy = config.get("availability", {})
    disable_after = int(policy.get("auto_disable_after_hard_failures", 6))
    reenable_after = int(policy.get("auto_reenable_after_successes", 2))
    minimum_failure_window_hours = float(policy.get("minimum_failure_window_hours", 8))
    auto_disable = bool(policy.get("auto_disable", True))
    explicit_excluded = {canonical_id(str(x)) for x in sources.get("exclusions", {}).get("provider_ids", [])}
    result_by_id = {canonical_id(str(item.get("canonical_id", ""))): item for item in results.get("results", [])}
    previous = dict(history.get("providers", {}))
    updated_history: dict[str, Any] = {}
    report_items: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    changed = False
    new_entries = []

    for original in manifest.get("scrapers", []):
        entry = dict(original)
        cid = canonical_id(str(entry.get("id", "")))
        if cid in explicit_excluded:
            changed = True
            report_items.append({"id": cid, "status": "excluded", "action": "removed-disallowed-p2p"})
            continue

        result = result_by_id.get(cid)
        old = dict(previous.get(cid, {}))
        provider_provenance = provenance.get("providers", {}).get(cid, {})
        activation_eligible = bool(provider_provenance.get("activation_eligible", False))
        activation_mode = provider_provenance.get("activation_mode", "disabled")
        current_sha = file_sha(entry)
        result_matches = result is not None and result.get("sha256") == current_sha
        if not result_matches:
            # Retry jobs contain only a subset of providers. Missing/stale results
            # must not reset another provider's outage or recovery counters.
            updated_history[cid] = old
            report_items.append({
                "id": cid,
                "status": "not-checked",
                "action": "unchanged",
                "enabled": bool(entry.get("enabled", False)),
                "consecutive_hard_failures": int(old.get("consecutive_hard_failures", 0)),
                "hard_failure_started_at": old.get("hard_failure_started_at"),
                "consecutive_successes": int(old.get("consecutive_successes", 0)),
                "hosts": old.get("hosts", []),
                "response_categories": old.get("response_categories", []),
                "host_health": old.get("host_health", {}),
            })
            new_entries.append(entry)
            continue

        status = result.get("status", "runtime_error")
        hard_host_results = [
            item for item in result.get("host_results", [])
            if isinstance(item, dict)
            and item.get("category") in {"host_down", "not_found"}
            and not item.get("reachable")
        ]
        is_hard_failure = status == "unavailable" and bool(hard_host_results)
        is_success = status == "healthy"
        is_inconclusive = status in {"blocked", "degraded", "no_streams", "provider_unreachable", "runtime_error"}
        old_hard_failures = int(old.get("consecutive_hard_failures", 0))
        hard_failures = old_hard_failures + 1 if is_hard_failure else (old_hard_failures if is_inconclusive else 0)
        successes = int(old.get("consecutive_successes", 0)) + 1 if is_success else 0
        auto_disabled = bool(old.get("auto_disabled", False))
        action = "unchanged"
        if is_hard_failure:
            failure_started_at = old.get("hard_failure_started_at") or now
        elif is_inconclusive:
            failure_started_at = old.get("hard_failure_started_at")
        else:
            failure_started_at = None
        failure_started = parse_datetime(failure_started_at)
        elapsed_failure_hours = (datetime.now(timezone.utc) - failure_started).total_seconds() / 3600 if failure_started else 0.0
        failure_window_satisfied = minimum_failure_window_hours <= 0 or elapsed_failure_hours >= minimum_failure_window_hours

        if (
            auto_disable
            and is_hard_failure
            and hard_failures >= disable_after
            and failure_window_satisfied
            and entry.get("enabled", False)
        ):
            entry["enabled"] = False
            auto_disabled = True
            action = "auto-disabled-after-sustained-hard-failures"
            changed = True
        elif (
            is_success
            and auto_disabled
            and successes >= reenable_after
            and not entry.get("enabled", False)
            and activation_eligible
        ):
            entry["enabled"] = True
            auto_disabled = False
            action = "auto-reenabled-after-successes"
            changed = True
        elif (
            is_success
            and auto_disabled
            and successes >= reenable_after
            and not activation_eligible
        ):
            action = "not-reenabled-failed-publication-activation-policy"

        old_host_health = dict(old.get("host_health", {}))
        host_health = dict(old_host_health)
        if result_matches:
            seen_hosts: set[str] = set()
            for host_result in result.get("host_results", []):
                host = str(host_result.get("host", "")).strip().casefold()
                if not host:
                    continue
                seen_hosts.add(host)
                previous_host = dict(old_host_health.get(host, {}))
                category = str(host_result.get("category", "unknown"))
                reachable = bool(host_result.get("reachable", False))
                host_hard_failure = category in {"host_down", "not_found"}
                host_health[host] = {
                    "last_checked_at": now,
                    "last_category": category,
                    "reachable": reachable,
                    "http_status": host_result.get("http_status"),
                    "latency_ms": host_result.get("latency_ms"),
                    "kind": host_result.get("kind"),
                    "consecutive_hard_failures": int(previous_host.get("consecutive_hard_failures", 0)) + 1 if host_hard_failure else 0,
                    "consecutive_successes": int(previous_host.get("consecutive_successes", 0)) + 1 if reachable else 0,
                    "consecutive_blocked": int(previous_host.get("consecutive_blocked", 0)) + 1 if category == "blocked" else 0,
                }
            if is_success:
                for old_host in set(old_host_health) - seen_hosts:
                    previous_host = dict(old_host_health.get(old_host, {}))
                    host_health[old_host] = {
                        **previous_host,
                        "last_checked_at": now,
                        "last_category": "not_returned",
                        "reachable": False,
                        "http_status": None,
                        "latency_ms": None,
                        "consecutive_hard_failures": 0,
                        "consecutive_successes": 0,
                        "consecutive_blocked": 0,
                    }

        should_update_history = (
            not old
            or is_hard_failure
            or (is_success and (auto_disabled or old.get("last_status") != "healthy" or int(old.get("consecutive_successes", 0)) < reenable_after))
            or (status in {"blocked", "no_streams", "degraded", "provider_unreachable", "runtime_error"} and old.get("last_status") != status)
            or action != "unchanged"
        )
        if should_update_history:
            updated_history[cid] = {
                **old,
                "last_checked_at": now,
                "last_status": status,
                "last_score": result.get("score") if result_matches else None,
                "last_sha256": current_sha,
                "consecutive_hard_failures": hard_failures,
                "hard_failure_started_at": failure_started_at,
                "consecutive_successes": successes,
                "consecutive_blocked": int(old.get("consecutive_blocked", 0)) + 1 if status == "blocked" else 0,
                "consecutive_no_streams": int(old.get("consecutive_no_streams", 0)) + 1 if status == "no_streams" else 0,
                "auto_disabled": auto_disabled,
                "last_success_at": now if is_success else old.get("last_success_at"),
                "hosts": result.get("hosts", []) if result_matches else old.get("hosts", []),
                "response_categories": result.get("response_categories", []) if result_matches else old.get("response_categories", []),
                "host_health": host_health,
            }
        else:
            updated_history[cid] = old
        effective_history = updated_history[cid]
        report_items.append({
            "id": cid,
            "status": status,
            "action": action,
            "enabled": bool(entry.get("enabled", False)),
            "consecutive_hard_failures": int(effective_history.get("consecutive_hard_failures", 0)),
            "hard_failure_started_at": effective_history.get("hard_failure_started_at"),
            "consecutive_successes": int(effective_history.get("consecutive_successes", 0)),
            "hosts": effective_history.get("hosts", []),
            "response_categories": effective_history.get("response_categories", []),
            "host_health": effective_history.get("host_health", {}),
            "activation_eligible": activation_eligible,
            "activation_mode": activation_mode,
        })
        new_entries.append(entry)

    new_manifest = {**manifest, "scrapers": new_entries}
    public_report = {
        "schema_version": 63,
        "generated_at": now,
        "test_environment": results.get("environment"),
        "checked_providers": len(results.get("results", [])),
        "status_counts": results.get("counts", {}),
        "policy": {
            "check_frequency_target": "hourly targeted retry" if results.get("mode") == "retry" else "every 4 hours full sweep",
            "auto_disable_after_hard_failures": disable_after if auto_disable else None,
            "minimum_failure_window_hours": minimum_failure_window_hours if auto_disable else None,
            "auto_reenable_after_successes": reenable_after,
            "blocked_or_rate_limited_does_not_disable": True,
            "runtime_or_provider_search_errors_do_not_disable": True,
            "only_confirmed_media_endpoint_outages_disable": True,
            "no_streams_does_not_disable_between_full_syncs": True,
            "publication_activation_eligibility_required_for_reenable": True,
            "accepted_activation_modes": [
                "strict",
                "strict_grace_inconclusive",
                "runtime_evidence"
            ],
        },
        "manifest_changed": changed,
        "providers": report_items,
    }
    new_history = {"schema_version": 63, "updated_at": now, "providers": updated_history}
    history_changed = updated_history != previous
    report_snapshot = {
        "status_counts": public_report["status_counts"],
        "manifest_changed": public_report["manifest_changed"],
        "providers": public_report["providers"],
    }
    previous_snapshot = {
        "status_counts": previous_report.get("status_counts", {}),
        "manifest_changed": previous_report.get("manifest_changed"),
        "providers": previous_report.get("providers", []),
    }
    if history_changed or not HISTORY_PATH.exists():
        atomic_write_json(HISTORY_PATH, new_history)
    if report_snapshot != previous_snapshot or not REPORT_PATH.exists():
        atomic_write_json(REPORT_PATH, public_report)
    atomic_write_json(NEXT_MANIFEST_PATH, new_manifest)
    print(f"Availability report prepared for {len(report_items)} providers; manifest changed={changed}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
