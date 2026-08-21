#!/usr/bin/env python3
"""Fail closed when a native human-UX lab mutates official Nuvio runtime code.

The machine-readable source of truth is automation/native-human-ux-policy.json.
The same file also persists validated lab profiles and known job blockers so later
runs reuse proven assumptions instead of re-opening the harness after every failure.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "automation/native-human-ux-policy.json"

REQUIRED_PROFILE_IDS = ("common", "tv", "mobile", "desktop")
REQUIRED_BLOCKER_IDS = {
    "stale-repository-http-instrumentation-contract",
    "stale-tv-bootstrap-wrapper-contract",
    "stale-tv-bootstrap-alias-contract",
    "reader-run-cancellation-churn",
    "repository-http-evidence-gap-after-instrumentation-disable",
    "actions-log-blob-not-ready",
}


def load_policy() -> dict:
    if not POLICY_PATH.is_file():
        raise SystemExit(f"native human-UX policy missing: {POLICY_PATH}")
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except Exception as error:
        raise SystemExit(f"native human-UX policy is invalid JSON: {error}") from error
    if int(policy.get("version") or 0) < 4:
        raise SystemExit("native human-UX policy version must include persistent profile/blocker memory")
    if policy.get("mode") != "human-ux-observation-only":
        raise SystemExit("native human-UX policy mode must remain human-ux-observation-only")

    change_control = policy.get("change_control") or {}
    for flag in (
        "policy_file_is_source_of_truth",
        "audit_must_read_this_file",
        "persistent_profiles_are_source_of_truth",
        "job_blocker_memory_is_source_of_truth",
    ):
        if change_control.get(flag) is not True:
            raise SystemExit(f"native human-UX policy must keep {flag}=true")
    if change_control.get("default_on_ambiguity") != "fail-closed":
        raise SystemExit("native human-UX policy must remain fail-closed")

    harness = policy.get("harness_change_control") or {}
    if harness.get("default") != "locked-do-not-modify":
        raise SystemExit("native harness must remain locked by default")
    if harness.get("change_policy") != "only-when-faithful-observation-is-blocked":
        raise SystemExit("native harness change policy must remain observation-blocker-only")
    required_before_change = set(harness.get("required_before_change") or [])
    if "consult persistent_profiles and job_blocker_memory" not in required_before_change:
        raise SystemExit("native harness changes must consult persistent profile/blocker memory first")

    profiles = policy.get("persistent_profiles") or {}
    if profiles.get("schema_version") != 1 or profiles.get("reuse_rule") != "reuse-before-rediagnosis":
        raise SystemExit("native persistent profile memory contract is missing or invalid")
    for profile_id in REQUIRED_PROFILE_IDS:
        profile = profiles.get(profile_id) or {}
        if profile.get("status") != "validated-and-reusable":
            raise SystemExit(f"native persistent profile is not reusable: {profile_id}")
    if profiles["common"].get("human_ux_acceptance_requires_real_ui_path") is not True:
        raise SystemExit("common native profile must require the real UI path")
    if profiles["common"].get("component_probes_are_diagnostic_only") is not True:
        raise SystemExit("common native profile must keep component probes diagnostic-only")
    if profiles["common"].get("production_player_first") is not True:
        raise SystemExit("common native profile must keep production-player-first ordering")

    blocker_memory = policy.get("job_blocker_memory") or {}
    if blocker_memory.get("schema_version") != 1:
        raise SystemExit("native job blocker memory schema is missing")
    if blocker_memory.get("consult_before_harness_change") is not True:
        raise SystemExit("native job blocker memory must be consulted before harness changes")
    entries = blocker_memory.get("entries") or []
    blocker_ids = [str(row.get("id") or "") for row in entries if isinstance(row, dict)]
    if len(blocker_ids) != len(set(blocker_ids)):
        raise SystemExit("native job blocker memory contains duplicate ids")
    missing_blockers = sorted(REQUIRED_BLOCKER_IDS - set(blocker_ids))
    if missing_blockers:
        raise SystemExit("native job blocker memory lost required entries: " + ", ".join(missing_blockers))
    for row in entries:
        if not isinstance(row, dict):
            raise SystemExit("native job blocker memory contains a non-object entry")
        for key in ("id", "status", "signature", "cause"):
            if not str(row.get(key) or "").strip():
                raise SystemExit(f"native job blocker entry missing {key}: {row.get('id') or '<unknown>'}")
        if row.get("status") == "resolved" and not str(row.get("never_repeat") or "").strip():
            raise SystemExit(f"resolved native blocker lacks never_repeat guard: {row.get('id')}")

    for key in ("allowed_checkout_changes", "allowed_gradle_additions", "forbidden_checkout_tokens"):
        if not policy.get(key):
            raise SystemExit(f"native human-UX policy missing non-empty {key}")
    return policy


POLICY = load_policy()
ALLOWED_PREFIXES = {
    str(client): tuple(str(value) for value in values)
    for client, values in POLICY["allowed_checkout_changes"].items()
}
ALLOWED_GRADLE_ADDITIONS = {
    str(client): tuple(str(value) for value in values)
    for client, values in POLICY["allowed_gradle_additions"].items()
}
FORBIDDEN_DIFF_TOKENS = tuple(str(value) for value in POLICY["forbidden_checkout_tokens"])


def _run(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout


def _status_paths(repo: Path) -> list[str]:
    paths: list[str] = []
    for line in _run(repo, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line.strip():
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(raw.strip())
    return paths


def _path_allowed(client: str, path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES[client])


def _audit_gradle_diff(client: str, diff: str) -> None:
    allowed = set(ALLOWED_GRADLE_ADDITIONS.get(client, ()))
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        value = line[1:].strip()
        if not value or value in {"{", "}"}:
            continue
        if value not in allowed:
            raise SystemExit(f"native lab forbidden Gradle mutation ({client}): {value}")


def _read_changed_file(repo: Path, relative: str) -> str:
    path = repo / relative
    if not path.is_file():
        return ""
    if path.suffix.lower() not in {".kt", ".java", ".kts", ".xml", ".gradle", ".properties", ".txt"}:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def audit_checkout(repo: Path, client: str) -> None:
    repo = Path(repo).resolve()
    client = str(client).strip().lower()
    if client not in ALLOWED_PREFIXES:
        raise SystemExit(f"unsupported native client audit target: {client}")
    if not (repo / ".git").exists():
        raise SystemExit(f"native client checkout is not a git repository: {repo}")

    paths = _status_paths(repo)
    forbidden_paths = [path for path in paths if not _path_allowed(client, path)]
    if forbidden_paths:
        raise SystemExit(
            "native human-UX lab mutated runtime-owned path(s): " + ", ".join(forbidden_paths[:20])
        )

    tracked_diff = _run(repo, "diff", "--no-ext-diff", "--unified=0", "--")
    changed_text = tracked_diff + "\n" + "\n".join(_read_changed_file(repo, path) for path in paths)
    for token in FORBIDDEN_DIFF_TOKENS:
        if token in changed_text:
            raise SystemExit(f"native human-UX lab introduced forbidden runtime mutation: {token}")

    gradle_path = {
        "mobile": "composeApp/build.gradle.kts",
        "tv": "app/build.gradle.kts",
    }.get(client)
    if gradle_path and gradle_path in paths:
        _audit_gradle_diff(
            client,
            _run(repo, "diff", "--no-ext-diff", "--unified=0", "--", gradle_path),
        )

    blocker_count = len(POLICY["job_blocker_memory"]["entries"])
    print(
        f"FIELD_NATIVE_CHECKOUT_AUDIT client={client} changed_paths={len(paths)} "
        f"policy_version={POLICY.get('version')} persistent_profile=true "
        f"known_blockers={blocker_count} runtime_mutation=false status=ok"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=tuple(ALLOWED_PREFIXES))
    parser.add_argument("repo")
    args = parser.parse_args()
    audit_checkout(Path(args.repo), args.client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
