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
CATALOG = ROOT / "provider_catalog.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"
PROFILE_TOKEN = {"android": "android", "ios": "ios", "desktop": "desktop"}
EXPECTED_TAGS = {
    "android": {"android"},
    "android-tv": {"android-tv", "tv"},
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


def catalog_rows(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for record in doc.get("providers") or []:
        if not isinstance(record, dict):
            continue
        scraper = record.get("scraper")
        projections = record.get("projections")
        if not isinstance(scraper, dict) or not isinstance(projections, dict):
            continue
        provider_id = str(record.get("canonicalId") or scraper.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        if provider_id in output:
            raise ValueError(f"duplicate provider catalog identity: {provider_id}")
        output[provider_id] = record
    return output


def values(row: dict[str, Any], key: str) -> list[str]:
    output: list[str] = []
    for raw in row.get(key) or []:
        item = str(raw).strip().casefold()
        if item:
            output.append(item)
    return output


def canonical_types(row: dict[str, Any]) -> tuple[str, ...]:
    raw = row.get("canonicalSupportedTypes")
    if not isinstance(raw, list) or not raw:
        raw = row.get("supportedTypes") or []
    output: list[str] = []
    for value in raw:
        item = str(value or "").strip().casefold()
        if item == "series":
            item = "tv"
        if item in {"movie", "tv", "anime"} and item not in output:
            output.append(item)
    return tuple(output)


def provider_filename(row: dict[str, Any]) -> str:
    value = str(row.get("filename") or "").strip().replace("\\", "/")
    while value.startswith("../"):
        value = value[3:]
    return value


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


def validate_projection_authority(
    errors: list[str],
    main_rows: dict[str, dict[str, Any]],
    vf_rows: dict[str, dict[str, Any]],
    catalogue: dict[str, dict[str, Any]],
) -> None:
    for provider_id, row in main_rows.items():
        validate_platform_field(errors, provider_id, row, "disabledPlatforms")
        validate_platform_field(errors, provider_id, row, "supportedPlatforms")
        if row.get("disabledPlatforms") != []:
            errors.append(f"{provider_id}: disabledPlatforms must stay empty in NiakVIO manifests")
        record = catalogue.get(provider_id)
        if not record:
            errors.append(f"{provider_id}: Global manifest identity missing from provider_catalog.json")
            continue
        if (record.get("projections") or {}).get("general") is not True:
            errors.append(f"{provider_id}: Global manifest leaked a non-General catalogue identity")
        scraper = record.get("scraper") or {}
        if provider_filename(row) != provider_filename(scraper):
            errors.append(f"{provider_id}: Global/catalog provider artifact mismatch")
        if canonical_types(row) != canonical_types(scraper):
            errors.append(f"{provider_id}: Global/catalog canonical media types mismatch")
        if bool(row.get("enabled")) != bool(scraper.get("enabled")):
            errors.append(f"{provider_id}: Global/catalog enabled mismatch")

    for provider_id, row in vf_rows.items():
        validate_platform_field(errors, f"vf:{provider_id}", row, "disabledPlatforms")
        validate_platform_field(errors, f"vf:{provider_id}", row, "supportedPlatforms")
        if row.get("disabledPlatforms") != []:
            errors.append(f"vf:{provider_id}: disabledPlatforms must stay empty in NiakVIO manifests")

        record = catalogue.get(provider_id)
        if not record:
            errors.append(f"vf:{provider_id}: France projection identity missing from provider_catalog.json")
            continue
        projections = record.get("projections") or {}
        if projections.get("vf") is not True:
            errors.append(f"vf:{provider_id}: catalogue does not authorize France projection")
        scraper = record.get("scraper") or {}
        if provider_filename(row) != provider_filename(scraper):
            errors.append(f"vf:{provider_id}: France/catalog provider artifact mismatch")
        if canonical_types(row) != canonical_types(scraper):
            errors.append(f"vf:{provider_id}: France/catalog canonical media types mismatch")
        if bool(row.get("enabled")) != bool(scraper.get("enabled")):
            errors.append(f"vf:{provider_id}: France/catalog enabled mismatch")

        main_row = main_rows.get(provider_id)
        if main_row is None:
            if projections.get("general") is not False:
                errors.append(f"vf:{provider_id}: missing Global row without strict France-only authority")
            continue
        if projections.get("general") is not True:
            errors.append(f"{provider_id}: shared Global/France identity lacks general=true")
        if bool(row.get("enabled")) != bool(main_row.get("enabled")):
            errors.append(f"{provider_id}: general/VF enabled mismatch")
        if set(values(row, "supportedPlatforms")) != set(values(main_row, "supportedPlatforms")):
            errors.append(f"{provider_id}: general/VF supportedPlatforms mismatch")
        if canonical_types(row) != canonical_types(main_row):
            errors.append(f"{provider_id}: general/VF canonical media types mismatch")
        if provider_filename(row) != provider_filename(main_row):
            errors.append(f"{provider_id}: general/VF provider artifact mismatch")

    active_global = {
        provider_id for provider_id, row in main_rows.items()
        if row.get("enabled") is not False
    }
    active_vf = {
        provider_id for provider_id, row in vf_rows.items()
        if row.get("enabled") is not False
    }
    expected_vf = {
        provider_id
        for provider_id, record in catalogue.items()
        if (record.get("projections") or {}).get("vf") is True
        and (record.get("scraper") or {}).get("enabled") is not False
    }
    if active_vf != expected_vf:
        missing = sorted(expected_vf - active_vf)
        extra = sorted(active_vf - expected_vf)
        errors.append(f"active France projection drift missing={missing} extra={extra}")

    expected_global = {
        provider_id
        for provider_id, record in catalogue.items()
        if (record.get("projections") or {}).get("general") is True
        and (record.get("scraper") or {}).get("enabled") is not False
    }
    if active_global != expected_global:
        missing = sorted(expected_global - active_global)
        extra = sorted(active_global - expected_global)
        errors.append(f"active Global projection drift missing={missing} extra={extra}")


def validate_platform_evidence_authority(
    errors: list[str],
    matrix: dict[str, Any],
    policy: dict[str, Any],
    current_release: str,
    main_rows: dict[str, dict[str, Any]],
) -> None:
    if matrix.get("manifest") != "manifest.json":
        errors.append("platform matrix was not generated from the general manifest")
    if policy.get("source_matrix") != "automation/platform-runtime-matrix.json":
        errors.append("platform policy source matrix mismatch")
    if str(policy.get("source_release") or "") != str(matrix.get("release") or ""):
        errors.append("platform policy/matrix release mismatch")
    if policy.get("legacy_android_no_proof_policy_retired") is not True:
        errors.append("legacy Android no-proof policy was not retired")
    if policy.get("manifest_projection") != "disabledPlatforms_empty_only":
        errors.append("platform policy must keep disabledPlatforms empty-only")
    defaults = policy.get("manifest_field_defaults") or {}
    if defaults.get("disabledPlatforms") != []:
        errors.append("platform policy disabledPlatforms default must be []")

    matrix_release = str(matrix.get("release") or "")
    managed = {
        str(provider_id).casefold(): {str(token).casefold() for token in tokens}
        for provider_id, tokens in (policy.get("managed_platform_tokens_by_provider") or {}).items()
    }
    classifications = policy.get("classifications") or {}

    if matrix_release != current_release:
        if matrix.get("authority") != "historical-evidence-only":
            errors.append("stale platform matrix must be explicitly historical-only")
        if policy.get("authority") != "historical-evidence-only":
            errors.append("stale platform policy must be explicitly historical-only")
        if str(policy.get("current_release") or "") != current_release:
            errors.append("historical platform policy current_release marker is stale")
        if managed:
            errors.append("historical platform policy cannot manage current providers")
        if classifications:
            errors.append("historical platform classifications cannot occupy current authority fields")
        historical = policy.get("historical_evidence") or {}
        if str(historical.get("source_release") or "") != matrix_release:
            errors.append("historical platform evidence release mismatch")
        return

    if policy.get("authority") not in {
        "current-release-observation-only",
        "current-release-evidence",
    }:
        errors.append("current-release platform policy authority is invalid")
    for provider_id, tokens in managed.items():
        if provider_id not in main_rows:
            errors.append(f"{provider_id}: managed provider missing from general manifest")
            continue
        for token in tokens:
            if token not in PROFILE_TOKEN.values():
                errors.append(f"{provider_id}: invalid managed platform token {token}")
                continue
            profile = next(name for name, value in PROFILE_TOKEN.items() if value == token)
            classification = str((classifications.get(provider_id) or {}).get(profile) or "")
            if classification not in {"conclusive_non_playable", "conclusive_runtime_error"}:
                errors.append(f"{provider_id}: {token} managed without conclusive failure ({classification})")


def run_client_upstream_guard() -> int:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return 0
    if os.environ.get("NUVIO_SKIP_CLIENT_UPSTREAM_GUARD") == "1":
        print("Nuvio client upstream drift guard skipped explicitly")
        return 0

    strict = os.environ.get("NUVIO_REQUIRE_CLIENT_UPSTREAM_GUARD") == "1"
    output = ROOT / "health-output" / "nuvio-client-upstream-status.json"
    command = [
        sys.executable,
        str(ROOT / "scripts" / "check_nuvio_client_upstreams.py"),
        "--output",
        str(output),
    ]
    if not strict:
        command.append("--no-fail")
        print("Nuvio client upstream drift is observational here; dedicated client audit remains authoritative")
    process = subprocess.run(command, cwd=ROOT, check=False)
    return int(process.returncode)


def main() -> int:
    contracts = load(CONTRACTS)
    catalogue_doc = load(CATALOG)
    main_doc = load(MAIN)
    vf_doc = load(VF)
    if not all(isinstance(value, dict) for value in (contracts, catalogue_doc, main_doc, vf_doc)):
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
    catalogue = catalog_rows(catalogue_doc)
    validate_projection_authority(errors, main_rows, vf_rows, catalogue)

    current_release = str(main_doc.get("version") or "")
    semver(current_release)
    matrix = load(MATRIX)
    policy = load(POLICY)
    if not isinstance(matrix, dict):
        errors.append("platform runtime matrix missing")
    if not isinstance(policy, dict):
        errors.append("platform runtime policy missing")
    if isinstance(matrix, dict) and isinstance(policy, dict):
        validate_platform_evidence_authority(
            errors, matrix, policy, current_release, main_rows
        )

    if errors:
        raise SystemExit("platform runtime policy validation failed:\n- " + "\n- ".join(errors))

    upstream_status = run_client_upstream_guard()
    if upstream_status != 0:
        raise SystemExit(upstream_status)

    france_only = sorted(set(vf_rows) - set(main_rows))
    print(
        "platform runtime policy validated: "
        f"release={main_doc.get('version')} global={len(main_rows)} vf={len(vf_rows)} "
        f"france_only={len(france_only)} clients=android,android-tv,ios,windows,macos,linux "
        f"matrix_authority={matrix.get('authority')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
