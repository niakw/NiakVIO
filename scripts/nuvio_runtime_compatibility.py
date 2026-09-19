#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "automation" / "nuvio-client-compatibility-matrix.json"
UPSTREAMS_PATH = ROOT / "automation" / "nuvio-client-upstreams.json"
PLATFORM_CONTRACTS = ROOT / "automation" / "platform-runtime-contracts.json"
TV_CONTRACT = ROOT / "automation" / "nuvio-tv-runtime-contract.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def validate_matrix() -> list[str]:
    errors: list[str] = []
    matrix = _load(MATRIX_PATH)
    upstreams = _load(UPSTREAMS_PATH)
    platform = _load(PLATFORM_CONTRACTS)
    tv_contract = _load(TV_CONTRACT)
    universe = {
        str(value)
        for value in matrix.get("capability_universe") or []
        if str(value).strip()
    }
    clients = matrix.get("clients") or {}
    upstream_clients = upstreams.get("clients") or {}
    platform_clients = platform.get("clients") or {}

    if not universe:
        errors.append("compatibility matrix capability_universe is empty")
    if not isinstance(clients, dict) or not clients:
        return errors + ["compatibility matrix clients are empty"]

    for client_id, row in clients.items():
        if not isinstance(row, dict):
            errors.append(f"{client_id}: matrix row is not an object")
            continue
        upstream = upstream_clients.get(client_id)
        if not isinstance(upstream, dict):
            errors.append(f"{client_id}: missing upstream registry row")
            continue
        if row.get("repository") != upstream.get("repository"):
            errors.append(f"{client_id}: repository mismatch")
        if row.get("branch") != upstream.get("branch"):
            errors.append(f"{client_id}: branch mismatch")

        baseline = row.get("baseline") or {}
        current = row.get("current_audited") or {}
        supported = row.get("supported_version_code") or {}
        baseline_ref = str(baseline.get("ref") or "")
        current_ref = str(current.get("ref") or "")
        verified_ref = str(upstream.get("verified_ref") or "")
        if len(baseline_ref) != 40 or len(current_ref) != 40:
            errors.append(f"{client_id}: baseline/current refs must be full SHAs")
        if current_ref != verified_ref:
            errors.append(
                f"{client_id}: matrix current_audited ref {current_ref or '<missing>'} "
                f"!= upstream verified_ref {verified_ref or '<missing>'}"
            )
        try:
            baseline_code = int(baseline.get("version_code"))
            current_code = int(current.get("version_code"))
            minimum = int(supported.get("min"))
            maximum = int(supported.get("max"))
        except (TypeError, ValueError):
            errors.append(f"{client_id}: invalid version code range")
        else:
            if not (minimum <= baseline_code <= current_code <= maximum):
                errors.append(
                    f"{client_id}: unsupported version ordering "
                    f"min={minimum} baseline={baseline_code} current={current_code} max={maximum}"
                )

        capabilities = {
            str(value)
            for value in row.get("brain_capabilities") or []
            if str(value).strip()
        }
        unknown = capabilities - universe
        if unknown:
            errors.append(f"{client_id}: unknown capabilities {sorted(unknown)}")

        if client_id == "nuvio-tv":
            if tv_contract.get("source_ref") != current_ref:
                errors.append("nuvio-tv: runtime contract source_ref differs from compatibility matrix")
        else:
            matching = [
                value
                for value in platform_clients.values()
                if isinstance(value, dict) and value.get("source_repository") == row.get("repository")
            ]
            refs = {str(value.get("source_ref") or "") for value in matching}
            if refs != {current_ref}:
                errors.append(f"{client_id}: platform contract refs differ from compatibility matrix: {sorted(refs)}")

    return errors


def planner_runtime_compatibility() -> dict[str, Any]:
    errors = validate_matrix()
    if errors:
        raise RuntimeError("invalid Nuvio runtime compatibility matrix: " + " | ".join(errors))

    matrix = _load(MATRIX_PATH)
    universe = {
        str(value)
        for value in matrix.get("capability_universe") or []
        if str(value).strip()
    }
    clients = matrix.get("clients") or {}
    capability_sets: list[set[str]] = []
    generations: dict[str, Any] = {}
    for client_id, row in clients.items():
        capabilities = {
            str(value)
            for value in row.get("brain_capabilities") or []
            if str(value).strip()
        }
        capability_sets.append(capabilities)
        baseline = row.get("baseline") or {}
        current = row.get("current_audited") or {}
        supported = row.get("supported_version_code") or {}
        generations[str(client_id)] = {
            "family": row.get("family"),
            "repository": row.get("repository"),
            "baselineRef": baseline.get("ref"),
            "baselineVersion": baseline.get("version_name"),
            "baselineVersionCode": baseline.get("version_code"),
            "currentRef": current.get("ref"),
            "currentVersion": current.get("version_name"),
            "currentVersionCode": current.get("version_code"),
            "supportedMinVersionCode": supported.get("min"),
            "supportedMaxVersionCode": supported.get("max"),
        }

    common = set.intersection(*capability_sets) if capability_sets else set()
    invalid = sorted(universe - common)
    return {
        "matrixVersion": int(matrix.get("schema_version") or 1),
        "policy": matrix.get("policy") or {},
        "supportedCapabilities": sorted(common),
        "invalidCapabilities": invalid,
        "clients": generations,
    }


def main() -> int:
    errors = validate_matrix()
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    payload = planner_runtime_compatibility()
    print(
        "FIELD_NUVIO_RUNTIME_COMPAT "
        f"clients={len(payload['clients'])} "
        f"supported_capabilities={len(payload['supportedCapabilities'])} "
        f"invalid_capabilities={len(payload['invalidCapabilities'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
