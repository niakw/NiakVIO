#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "automation" / "platform-runtime-contracts.json"
MATRIX = ROOT / "automation" / "platform-runtime-matrix.json"
POLICY = ROOT / "automation" / "platform-runtime-policy.json"
LEGACY = ROOT / "automation" / "mobile-vf-runtime-policy.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"
PROFILE_TOKEN = {"android": "android", "ios": "ios", "desktop": "desktop"}
EXPECTED_TAGS = {
    "android": {"android"},
    "ios": {"ios"},
    "windows": {"desktop", "jvm", "windows"},
    "macos": {"desktop", "jvm", "macos"},
    "linux": {"desktop", "jvm", "linux"},
}


def load(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def semver(value: object) -> tuple[int, int, int]:
    parts = str(value or "").split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"invalid semantic version: {value!r}")
    return tuple(map(int, parts))


def rows(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in doc.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def values(row: dict[str, Any], key: str) -> list[str]:
    output: list[str] = []
    for raw in row.get(key) or []:
        item = str(raw).strip().casefold()
        if item:
            output.append(item)
    return output


def validate_platform_field(errors: list[str], provider_id: str, row: dict[str, Any], key: str) -> None:
    raw = row.get(key)
    if raw is None:
        return
    if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
        errors.append(f"{provider_id}: {key} must be a string list")
        return
    normalized = values(row, key)
    if len(normalized) != len(set(normalized)):
        errors.append(f"{provider_id}: duplicate {key} entries")
    if any(item != str(raw[index]).strip() for index, item in enumerate(normalized)):
        errors.append(f"{provider_id}: {key} entries must be normalized lowercase")


def run_client_upstream_guard() -> int:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return 0
    # Upstream Nuvio heads are external, time-varying inputs. A contract change
    # must be reviewed by the dedicated client-drift/lab workflows, but must not
    # make an otherwise deterministic pull-request regression gate flaky. Keep
    # the guard strict for main pushes, schedules and manual production runs.
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        print("Nuvio client upstream drift guard deferred to dedicated PR client-drift checks")
        return 0
    if os.environ.get("NUVIO_SKIP_CLIENT_UPSTREAM_GUARD") == "1":
        print("Nuvio client upstream drift guard skipped explicitly")
        return 0
    output = ROOT / "health-output" / "nuvio-client-upstream-status.json"
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_nuvio_client_upstreams.py"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
    )
    return int(process.returncode)


def main() -> int:
    contracts = load(CONTRACTS)
    main_doc = load(MAIN)
    vf_doc = load(VF)
    if not all(isinstance(value, dict) for value in (contracts, main_doc, vf_doc)):
        raise SystemExit("platform runtime validation inputs are missing")

    errors: list[str] = []
    clients = contracts.get("clients") or {}
    if set(clients) != set(EXPECTED_TAGS):
        errors.append(f"client contract set mismatch: {sorted(clients)}")
    for name, expected_tags in EXPECTED_TAGS.items():
        client = clients.get(name) or {}
        if set(client.get("platform_tags") or []) != expected_tags:
            errors.append(f"{name}: platform tags mismatch")
        if client.get("plugin_runtime") != "quickjs-positional-getStreams":
            errors.append(f"{name}: unexpected plugin runtime")
        if client.get("external_player_hint_preserved") is not False:
            errors.append(f"{name}: external-player hint must not be assumed preserved")

    if str(main_doc.get("version") or "") != str(vf_doc.get("version") or ""):
        errors.append("general/VF manifest version mismatch")

    main_rows = rows(main_doc)
    vf_rows = rows(vf_doc)
    for provider_id, row in main_rows.items():
        validate_platform_field(errors, provider_id, row, "disabledPlatforms")
        validate_platform_field(errors, provider_id, row, "supportedPlatforms")
    for provider_id, row in vf_rows.items():
        validate_platform_field(errors, f"vf:{provider_id}", row, "disabledPlatforms")
        validate_platform_field(errors, f"vf:{provider_id}", row, "supportedPlatforms")
        main_row = main_rows.get(provider_id)
        if main_row is None:
            errors.append(f"vf:{provider_id}: missing from general manifest")
            continue
        if bool(row.get("enabled")) != bool(main_row.get("enabled")):
            errors.append(f"{provider_id}: general/VF enabled mismatch")
        if set(values(row, "disabledPlatforms")) != set(values(main_row, "disabledPlatforms")):
            errors.append(f"{provider_id}: general/VF disabledPlatforms mismatch")
        if set(values(row, "supportedPlatforms")) != set(values(main_row, "supportedPlatforms")):
            errors.append(f"{provider_id}: general/VF supportedPlatforms mismatch")
        if [str(x).casefold() for x in row.get("supportedTypes") or []] != [str(x).casefold() for x in main_row.get("supportedTypes") or []]:
            errors.append(f"{provider_id}: general/VF supportedTypes mismatch")
        vf_filename = str(row.get("filename") or "")
        main_filename = str(main_row.get("filename") or "")
        if vf_filename.removeprefix("../") != main_filename:
            errors.append(f"{provider_id}: general/VF provider artifact mismatch")

    current = semver(main_doc.get("version"))
    matrix = load(MATRIX)
    policy = load(POLICY)
    strict_release = current >= (5, 20, 28)
    if strict_release and not isinstance(matrix, dict):
        errors.append("platform runtime matrix missing for release >= 5.20.28")
    if strict_release and not isinstance(policy, dict):
        errors.append("platform runtime policy missing for release >= 5.20.28")

    if isinstance(matrix, dict) and isinstance(policy, dict):
        if matrix.get("manifest") != "manifest.json":
            errors.append("platform matrix was not generated from the general manifest")
        if policy.get("source_matrix") != "automation/platform-runtime-matrix.json":
            errors.append("platform policy source matrix mismatch")
        if str(policy.get("source_release") or "") != str(matrix.get("release") or ""):
            errors.append("platform policy/matrix release mismatch")
        if policy.get("legacy_android_no_proof_policy_retired") is not True:
            errors.append("legacy Android no-proof policy was not retired")

        matrix_rows = {
            str(row.get("id") or "").casefold(): row
            for row in matrix.get("providers") or []
            if isinstance(row, dict) and str(row.get("id") or "").strip()
        }
        managed = {
            str(provider_id).casefold(): {str(token).casefold() for token in tokens}
            for provider_id, tokens in (policy.get("managed_platform_tokens_by_provider") or {}).items()
        }
        classifications = policy.get("classifications") or {}
        for provider_id, tokens in managed.items():
            row = main_rows.get(provider_id)
            if row is None:
                errors.append(f"{provider_id}: managed provider missing from general manifest")
                continue
            disabled = set(values(row, "disabledPlatforms"))
            for token in tokens:
                if token not in PROFILE_TOKEN.values():
                    errors.append(f"{provider_id}: invalid managed platform token {token}")
                    continue
                if token not in disabled:
                    errors.append(f"{provider_id}: managed block {token} absent from general manifest")
                profile = next(name for name, value in PROFILE_TOKEN.items() if value == token)
                classification = str((classifications.get(provider_id) or {}).get(profile) or "")
                if classification not in {"conclusive_non_playable", "conclusive_runtime_error"}:
                    errors.append(f"{provider_id}: {token} managed without conclusive failure ({classification})")

        legacy = load(LEGACY, {}) or {}
        weak = {str(value).casefold() for value in legacy.get("android_disabled_no_direct_movie_proof") or []}
        for provider_id in weak:
            matrix_row = matrix_rows.get(provider_id)
            row = main_rows.get(provider_id)
            if not matrix_row or not row:
                continue
            classification = str(((matrix_row.get("profiles") or {}).get("android") or {}).get("classification") or "inconclusive")
            if classification in {"compatible_direct", "inconclusive"} and "android" in set(values(row, "disabledPlatforms")):
                if "android" not in managed.get(provider_id, set()):
                    errors.append(f"{provider_id}: stale legacy Android no-proof block remains")

    if errors:
        raise SystemExit("platform runtime policy validation failed:\n- " + "\n- ".join(errors))

    upstream_status = run_client_upstream_guard()
    if upstream_status != 0:
        raise SystemExit(upstream_status)

    print(
        "platform runtime policy validated: "
        f"release={main_doc.get('version')} general={len(main_rows)} vf={len(vf_rows)} "
        "clients=android,ios,windows,macos,linux"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())