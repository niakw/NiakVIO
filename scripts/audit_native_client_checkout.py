#!/usr/bin/env python3
"""Fail closed when a native human-UX lab mutates official Nuvio runtime code.

The machine-readable source of truth is automation/native-human-ux-policy.json.
This script intentionally contains no independent allow-list for Nuvio checkout
paths or forbidden runtime tokens: changing the lab boundary requires an explicit
policy diff that is visible to canonical CI and review.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "automation/native-human-ux-policy.json"


def load_policy() -> dict:
    if not POLICY_PATH.is_file():
        raise SystemExit(f"native human-UX policy missing: {POLICY_PATH}")
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except Exception as error:
        raise SystemExit(f"native human-UX policy is invalid JSON: {error}") from error
    if policy.get("mode") != "human-ux-observation-only":
        raise SystemExit("native human-UX policy mode must remain human-ux-observation-only")
    change_control = policy.get("change_control") or {}
    if change_control.get("policy_file_is_source_of_truth") is not True:
        raise SystemExit("native human-UX policy must remain the source of truth")
    if change_control.get("audit_must_read_this_file") is not True:
        raise SystemExit("native human-UX policy must require audit consumption")
    if change_control.get("default_on_ambiguity") != "fail-closed":
        raise SystemExit("native human-UX policy must remain fail-closed")
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
    # Binary provider/test assets are irrelevant to runtime-mutation tokens.
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

    print(
        f"FIELD_NATIVE_CHECKOUT_AUDIT client={client} changed_paths={len(paths)} "
        f"policy_version={POLICY.get('version')} runtime_mutation=false status=ok"
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
