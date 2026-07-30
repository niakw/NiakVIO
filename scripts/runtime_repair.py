#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Provider-agnostic runtime diagnosis and repair candidate generation.

The module contains no provider ids or domains. Runtime signatures select a
reusable structural profile, then the exact generated JavaScript is statically
validated and deep-tested before it may replace its parent candidate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from apply_provider_overrides import apply_overrides, load_overrides, profile_matches

ROOT = Path(__file__).resolve().parents[1]
OBSOLETE_STATUSES = {404, 410}
HARD_FAILURES = {"runtime_error", "excluded"}
STATUS_RANK = {
    "excluded": -2,
    "runtime_error": -1,
    "unavailable": 0,
    "provider_unreachable": 1,
    "no_streams": 2,
    "blocked": 3,
    "degraded": 4,
    "reachable": 5,
    "healthy": 6,
}


def _tests(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in result.get("tests") or [] if isinstance(item, dict)]


def observations(result: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for test in _tests(result):
        output.extend(
            observation
            for observation in (test.get("network_observations") or [])
            if isinstance(observation, dict)
        )
    return output


def stream_count(result: dict[str, Any]) -> int:
    values = [int(test.get("stream_count") or 0) for test in _tests(result)]
    evidence = result.get("evidence") or {}
    values.append(int(evidence.get("streams_playable") or 0))
    return max(values or [0])


def _provider_flags(result: dict[str, Any]) -> tuple[bool, bool]:
    evidence = result.get("evidence") or {}
    accessible = bool(evidence.get("provider_server_accessible"))
    successful = bool(evidence.get("provider_server_successful_response"))
    for test in _tests(result):
        accessible = accessible or bool(test.get("provider_server_accessible"))
        successful = successful or bool(test.get("provider_server_successful_response"))
    return accessible, successful


def _observation_summary(result: dict[str, Any]) -> dict[str, Any]:
    rows = observations(result)
    infrastructure = [row for row in rows if row.get("infrastructure")]
    provider_rows = [row for row in rows if not row.get("infrastructure")]
    provider_success = [
        row
        for row in provider_rows
        if isinstance(row.get("status"), int) and 200 <= int(row["status"]) < 400
    ]
    obsolete = [row for row in provider_rows if row.get("status") in OBSOLETE_STATUSES]
    forbidden = [row for row in provider_rows if row.get("status") in {401, 403}]
    by_host: dict[str, dict[str, int]] = defaultdict(lambda: {"success": 0, "obsolete": 0})
    for row in provider_success:
        if row.get("host"):
            by_host[str(row["host"])]["success"] += 1
    for row in obsolete:
        if row.get("host"):
            by_host[str(row["host"])]["obsolete"] += 1
    return {
        "rows": rows,
        "infrastructure_success": sum(
            1
            for row in infrastructure
            if isinstance(row.get("status"), int) and 200 <= int(row["status"]) < 400
        ),
        "provider_rows": len(provider_rows),
        "provider_success": len(provider_success),
        "obsolete": len(obsolete),
        "forbidden": len(forbidden),
        "hosts": dict(by_host),
    }


def runtime_trigger_matches(trigger: str, result: dict[str, Any]) -> bool:
    """Match a named failure schema using only runtime evidence."""
    status = str(result.get("status") or "runtime_error")
    summary = _observation_summary(result)
    accessible, successful = _provider_flags(result)
    streams = stream_count(result)

    if trigger == "metadata_only_no_origin":
        return (
            status in {"no_streams", "runtime_error", "provider_unreachable"}
            and streams == 0
            and summary["infrastructure_success"] >= 1
            and summary["provider_rows"] == 0
            and not accessible
            and not successful
        )

    if trigger == "search_success_with_obsolete_fallback":
        same_host_pattern = any(
            counts["success"] >= 1 and counts["obsolete"] >= 2
            for counts in summary["hosts"].values()
        )
        return (
            status in {"no_streams", "reachable", "degraded"}
            and streams == 0
            and accessible
            and successful
            and same_host_pattern
        )

    if trigger == "provider_http_forbidden":
        return (
            status in {"no_streams", "reachable", "degraded", "provider_unreachable"}
            and streams == 0
            and summary["forbidden"] >= 1
            and summary["provider_success"] == 0
        )

    if trigger == "stream_http_forbidden":
        return (
            status in {"healthy", "reachable", "degraded", "no_streams"}
            and streams > 0
            and summary["forbidden"] >= 1
        )

    if trigger == "runtime_error_after_local_patch":
        return status == "runtime_error"

    raise ValueError(f"unknown runtime repair trigger: {trigger}")


def applied_profiles(candidate: dict[str, Any]) -> set[str]:
    return {
        str(record.get("profile"))
        for record in candidate.get("local_patches") or []
        if isinstance(record, dict)
        and record.get("type") == "patch_profile"
        and record.get("profile")
    }


def matching_profiles(
    candidate: dict[str, Any],
    result: dict[str, Any],
    source_text: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    config = config or load_overrides()
    profiles = config.get("patch_profiles") or {}
    already = applied_profiles(candidate)
    matches: list[tuple[int, str]] = []
    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        if str(profile.get("phase") or "discovery") != "runtime":
            continue
        if name in already:
            continue
        trigger = str(profile.get("runtime_trigger") or "").strip()
        if not trigger or not runtime_trigger_matches(trigger, result):
            continue
        if not profile_matches(source_text, profile):
            continue
        matches.append((int(profile.get("priority") or 100), str(name)))
    return [name for _, name in sorted(matches)]


def _safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def _validate_artifact(path: Path) -> None:
    subprocess.run(
        ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def create_repair_candidate(
    stage: Path,
    candidate: dict[str, Any],
    profile_name: str,
    round_number: int,
) -> tuple[dict[str, Any] | None, str | None]:
    source_path = (stage / str(candidate.get("local_path") or "")).resolve()
    providers_root = (stage / "providers").resolve()
    try:
        source_path.relative_to(providers_root)
    except ValueError:
        return None, "unsafe_parent_path"
    if not source_path.is_file():
        return None, "missing_parent_artifact"

    parent_data = source_path.read_bytes()
    try:
        patched, records = apply_overrides(
            str(candidate.get("canonical_id") or candidate.get("upstream_id") or ""),
            parent_data,
            phase="runtime",
            profile_names=[profile_name],
        )
    except Exception as exc:
        return None, f"patch_exception:{type(exc).__name__}:{exc}"
    profile_records = [
        record
        for record in records
        if record.get("type") == "patch_profile" and record.get("profile") == profile_name
    ]
    if patched == parent_data or not profile_records:
        return None, "structural_profile_made_no_change"

    digest = hashlib.sha256(patched).hexdigest()
    parent_digest = hashlib.sha256(parent_data).hexdigest()
    repair_dir = stage / "providers" / "runtime-repairs" / _safe_fragment(str(candidate.get("source") or "source"))
    repair_dir.mkdir(parents=True, exist_ok=True)
    target = repair_dir / (
        f"{_safe_fragment(str(candidate.get('canonical_id') or 'provider'))}--"
        f"r{round_number}--{_safe_fragment(profile_name)}--{digest[:16]}.js"
    )
    target.write_bytes(patched)
    try:
        _validate_artifact(target)
    except Exception as exc:
        target.unlink(missing_ok=True)
        return None, f"artifact_validation_failed:{type(exc).__name__}:{exc}"

    repaired = copy.deepcopy(candidate)
    parent_key = str(candidate.get("key"))
    repaired["key"] = f"{parent_key}::repair:r{round_number}:{profile_name}:{digest[:8]}"
    repaired["local_path"] = target.relative_to(stage).as_posix()
    repaired["sha256"] = digest
    repaired["bytes"] = len(patched)
    repaired["local_patches"] = list(candidate.get("local_patches") or []) + profile_records
    repaired["runtime_repair"] = {
        "parent_key": parent_key,
        "parent_sha256": parent_digest,
        "round": round_number,
        "profile": profile_name,
    }
    return repaired, None


def _obsolete_count(result: dict[str, Any]) -> int:
    return _observation_summary(result)["obsolete"]


def _successful_provider_requests(result: dict[str, Any]) -> int:
    return _observation_summary(result)["provider_success"]


def quality_vector(result: dict[str, Any]) -> tuple[int, ...]:
    status = str(result.get("status") or "runtime_error")
    accessible, successful = _provider_flags(result)
    evidence = result.get("evidence") or {}
    playable = int(evidence.get("streams_playable") or 0)
    returned = stream_count(result)
    return (
        0 if status in HARD_FAILURES else 1,
        1 if playable > 0 else 0,
        playable,
        1 if returned > 0 else 0,
        returned,
        1 if successful else 0,
        1 if accessible else 0,
        STATUS_RANK.get(status, -1),
        int(result.get("score") or 0),
        _successful_provider_requests(result),
    )


def compare_results(parent: dict[str, Any], repaired: dict[str, Any]) -> tuple[bool, str]:
    repaired_status = str(repaired.get("status") or "runtime_error")
    if repaired_status in HARD_FAILURES:
        return False, f"hard_failure:{repaired_status}"
    parent_vector = quality_vector(parent)
    repaired_vector = quality_vector(repaired)
    if repaired_vector > parent_vector:
        return True, "strict_runtime_improvement"
    return False, "no_strict_runtime_improvement"


def result_with_parent_key(result: dict[str, Any], parent_key: str, parent_sha: str | None = None) -> dict[str, Any]:
    updated = copy.deepcopy(result)
    updated["key"] = parent_key
    if parent_sha:
        updated["sha256"] = parent_sha
    return updated


def health_counts(results: Iterable[dict[str, Any]]) -> dict[str, int]:
    statuses = [
        "healthy",
        "reachable",
        "blocked",
        "degraded",
        "no_streams",
        "provider_unreachable",
        "runtime_error",
        "unavailable",
        "excluded",
    ]
    rows = list(results)
    return {status: sum(1 for item in rows if item.get("status") == status) for status in statuses}
