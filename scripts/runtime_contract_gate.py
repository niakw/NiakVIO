#!/usr/bin/env python3
"""Executable cross-client runtime contract for generated NiakVIO providers.

The JSON contract files are generation/CI inputs, not documentation. This gate
validates only shared provider ABI/projection guarantees; client-specific source
audits and Native Labs may add stricter evidence without weakening these rules.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM_PATH = ROOT / "automation" / "platform-runtime-contracts.json"
MATRIX_PATH = ROOT / "automation" / "nuvio-client-compatibility-matrix.json"
RUNTIME_TRANSPORT_TYPES = frozenset({"movie", "tv", "series"})
EXPECTED_SIGNATURE = "getStreams(tmdbId, mediaType, season, episode)"
REQUIRED_RESULT_FIELDS = frozenset(
    {"url", "headers", "type", "quality", "language", "seeders", "peers", "infoHash", "subtitles"}
)


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        raise ValueError(f"invalid runtime contract JSON {path.relative_to(ROOT)}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"runtime contract must be an object: {path.relative_to(ROOT)}")
    return value


def _cap(client: dict, name: str) -> dict:
    value = (client.get("capabilities") or {}).get(name)
    if not isinstance(value, dict):
        raise ValueError(f"missing capability {name}")
    return value


def _detail(client: dict, name: str) -> str:
    return str(_cap(client, name).get("detail") or "").strip()


def _state(client: dict, name: str) -> str:
    return str(_cap(client, name).get("state") or "").strip().casefold()


def validate_contract_files() -> dict:
    platform = _load(PLATFORM_PATH)
    matrix = _load(MATRIX_PATH)
    clients = platform.get("clients") or {}
    if not isinstance(clients, dict) or not clients:
        raise ValueError("platform runtime contract has no clients")

    required_platforms = {"android", "ios", "macos", "windows", "android-tv"}
    missing = sorted(required_platforms - set(clients))
    if missing:
        raise ValueError("platform runtime contract missing clients: " + ", ".join(missing))

    for key, client in clients.items():
        if not isinstance(client, dict):
            raise ValueError(f"invalid client contract: {key}")
        if _detail(client, "get_streams_signature") != EXPECTED_SIGNATURE:
            raise ValueError(f"{key}: getStreams ABI drift")
        if _state(client, "exception_to_empty") not in {"native", "shim", "bridge"}:
            raise ValueError(f"{key}: getStreams errors must fail to []")
        tags = client.get("platform_tags") or []
        if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
            raise ValueError(f"{key}: invalid platform_tags")
        if key != "android-tv" and _state(client, "tmdb_api_key") != "absent":
            raise ValueError(f"{key}: TMDB_API_KEY global must remain absent")
        if _state(client, "stream_headers") in {"absent", "incompatible"}:
            raise ValueError(f"{key}: stream headers are not preserved")
        if _state(client, "subtitles") in {"absent", "incompatible"}:
            raise ValueError(f"{key}: subtitles are not preserved")
        if _state(client, "torrent_fields") in {"absent", "incompatible"}:
            raise ValueError(f"{key}: torrent metadata projection drifted")

    tv = clients["android-tv"]
    if _state(tv, "tmdb_api_key") not in {"native", "bridge"}:
        raise ValueError("android-tv: TMDB_API_KEY runtime global must remain available")
    if _state(tv, "text_codec") not in {"absent", "incompatible"}:
        raise ValueError("android-tv: generated providers must not require TextEncoder/TextDecoder")
    if _state(tv, "webassembly") not in {"absent", "incompatible"}:
        raise ValueError("android-tv: generated providers must not require WebAssembly")
    if _state(tv, "behavior_hints_projection") in {"absent", "incompatible"}:
        raise ValueError("android-tv: behaviorHints.proxyHeaders projection is required")

    matrix_clients = matrix.get("clients") or {}
    if not isinstance(matrix_clients, dict):
        raise ValueError("client compatibility matrix has no clients")
    expected_matrix = {"nuvio-mobile", "nuvio-desktop", "nuvio-tv"}
    missing_matrix = sorted(expected_matrix - set(matrix_clients))
    if missing_matrix:
        raise ValueError("compatibility matrix missing clients: " + ", ".join(missing_matrix))

    universe = {str(value).strip() for value in matrix.get("capability_universe") or [] if str(value).strip()}
    if "series" not in universe:
        raise ValueError("compatibility matrix must retain series transport capability")

    for key, client in matrix_clients.items():
        contract = client.get("provider_contract") or {}
        if contract.get("request_shape") != EXPECTED_SIGNATURE:
            raise ValueError(f"{key}: compatibility matrix getStreams ABI drift")
        if contract.get("runtime_family_equivalent_to_sibling_clients") is not False:
            raise ValueError(f"{key}: sibling runtime equivalence must remain false")
        capabilities = {str(value).strip() for value in client.get("brain_capabilities") or [] if str(value).strip()}
        if "series" not in capabilities:
            raise ValueError(f"{key}: series transport capability missing")

    return {
        "platform_clients": len(clients),
        "matrix_clients": len(matrix_clients),
        "runtime_transport_types": sorted(RUNTIME_TRANSPORT_TYPES),
        "required_result_fields": sorted(REQUIRED_RESULT_FIELDS),
    }


def main() -> int:
    summary = validate_contract_files()
    print(
        "runtime contract gate passed: "
        f"platform_clients={summary['platform_clients']} matrix_clients={summary['matrix_clients']} "
        f"runtime_transport_types={','.join(summary['runtime_transport_types'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
