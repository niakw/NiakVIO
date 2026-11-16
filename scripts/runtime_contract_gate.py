#!/usr/bin/env python3
"""Executable cross-client runtime contract for generated NiakVIO providers.

The JSON contract files are generation/CI inputs, not documentation. This gate
validates shared provider ABI/projection guarantees and the durable media identity
contract; client-specific source audits and Native Labs may add stricter evidence
without weakening these rules.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM_PATH = ROOT / "automation" / "platform-runtime-contracts.json"
MATRIX_PATH = ROOT / "automation" / "nuvio-client-compatibility-matrix.json"
PUBLISHED_SUPPORTED_TYPES = frozenset({"movie", "tv", "anime"})
PROVIDER_RUNTIME_REQUEST_TYPES = frozenset({"movie", "tv"})
TV_INPUT_ALIASES = frozenset({"series", "show", "other"})
EXPECTED_SIGNATURE = "getStreams(tmdbId, mediaType, season, episode)"
IDENTITY_CAPABILITY = "media_identity_hydration"
IDENTITY_CONTEXT_PATH = "__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id"
IDENTITY_CACHE_GLOBAL = "__nuvioTmdbMetadataCacheV1"
REQUIRED_RESULT_FIELDS = frozenset(
    {
        "title", "name", "url", "quality", "size", "language", "provider",
        "type", "seeders", "peers", "infoHash", "headers", "subtitles",
    }
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


def _validate_identity_contract(platform: dict, clients: dict) -> None:
    identity = platform.get("media_identity_contract")
    if not isinstance(identity, dict):
        raise ValueError("platform runtime contract missing media_identity_contract")
    if identity.get("positional_tmdb_id_is_complete_identity") is not False:
        raise ValueError("positional TMDB id must never be treated as complete media identity")
    if identity.get("canonical_context_imdb_path") != IDENTITY_CONTEXT_PATH:
        raise ValueError("canonical IMDb context path drifted")
    if identity.get("canonical_metadata_cache_global") != IDENTITY_CACHE_GLOBAL:
        raise ValueError("canonical TMDB metadata cache global drifted")
    cache_shape = str(identity.get("canonical_metadata_cache_entry_shape") or "")
    if "state" not in cache_shape or "metadata" not in cache_shape or "external_ids" not in cache_shape or "imdb_id" not in cache_shape:
        raise ValueError("canonical metadata cache entry shape lost IMDb external_ids contract")
    if identity.get("user_tmdb_credential_required") is not False:
        raise ValueError("runtime identity hydration must not require an end-user TMDB credential")
    if identity.get("secret_projection_to_provider_javascript") is not False:
        raise ValueError("TMDB credential must not be embedded in published provider bytes")
    timing = str(identity.get("cache_population_timing") or "").casefold()
    if "after" not in timing or "before getstreams" not in timing:
        raise ValueError("host metadata cache timing must remain after Core init and before getStreams")

    for key, client in clients.items():
        state = _state(client, IDENTITY_CAPABILITY)
        if state not in {"native", "bridge"}:
            raise ValueError(
                f"{key}: current official runtime must expose equivalent TMDB/IMDb "
                f"identity hydration, got {state!r}"
            )


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

    _validate_identity_contract(platform, clients)

    media_boundary = platform.get("media_type_boundary") or {}
    if set(media_boundary.get("published_supported_types") or []) != PUBLISHED_SUPPORTED_TYPES:
        raise ValueError("published supportedTypes boundary drifted")
    if set(media_boundary.get("provider_runtime_request_types") or []) != PROVIDER_RUNTIME_REQUEST_TYPES:
        raise ValueError("provider runtime request media types drifted")
    if set(media_boundary.get("tv_input_aliases") or []) != TV_INPUT_ALIASES:
        raise ValueError("TV input alias boundary drifted")
    if media_boundary.get("anime_provider_runtime_type") != "tv":
        raise ValueError("anime provider runtime mapping must remain anime -> tv")

    portable_fields = {
        str(value).strip()
        for value in platform.get("portable_provider_result_fields") or []
        if str(value).strip()
    }
    if portable_fields != REQUIRED_RESULT_FIELDS:
        raise ValueError(
            "portable provider result ABI drift: "
            f"actual={sorted(portable_fields)} expected={sorted(REQUIRED_RESULT_FIELDS)}"
        )
    if not str(platform.get("portable_presentation_rule") or "").strip():
        raise ValueError("portable provider presentation rule missing")

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
        if _state(client, "tmdb_api_key") not in {"native", "bridge"}:
            raise ValueError(f"{key}: current runtime TMDB_API_KEY capability missing")
        if _state(client, "stream_headers") in {"absent", "incompatible"}:
            raise ValueError(f"{key}: stream headers are not preserved")
        if _state(client, "subtitles") in {"absent", "incompatible"}:
            raise ValueError(f"{key}: subtitles are not preserved")
        if _state(client, "torrent_fields") in {"absent", "incompatible"}:
            raise ValueError(f"{key}: torrent metadata projection drifted")
        for capability in (
            "stream_title_projection",
            "stream_description_projection",
            "stream_badge_projection",
        ):
            if _state(client, capability) in {"absent", "incompatible", "audit-required"}:
                raise ValueError(f"{key}: portable presentation capability drifted: {capability}")

    tv = clients["android-tv"]
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

    matrix_policy = matrix.get("policy") or {}
    if not str(matrix_policy.get("media_identity_contract") or "").strip():
        raise ValueError("compatibility matrix missing durable media_identity_contract policy")
    matrix_media = matrix_policy.get("media_type_boundary") or {}
    if set(matrix_media.get("published_supported_types") or []) != PUBLISHED_SUPPORTED_TYPES:
        raise ValueError("compatibility matrix published media types drifted")
    if set(matrix_media.get("provider_runtime_request_types") or []) != PROVIDER_RUNTIME_REQUEST_TYPES:
        raise ValueError("compatibility matrix provider runtime types drifted")
    if set(matrix_media.get("tv_input_aliases") or []) != TV_INPUT_ALIASES:
        raise ValueError("compatibility matrix TV input aliases drifted")
    if matrix_media.get("anime_provider_runtime_type") != "tv":
        raise ValueError("compatibility matrix anime runtime mapping drifted")

    universe = {str(value).strip() for value in matrix.get("capability_universe") or [] if str(value).strip()}
    if "series" not in universe:
        raise ValueError("compatibility matrix must retain series reasoning/input-alias capability")

    for key, client in matrix_clients.items():
        contract = client.get("provider_contract") or {}
        if contract.get("request_shape") != EXPECTED_SIGNATURE:
            raise ValueError(f"{key}: compatibility matrix getStreams ABI drift")
        if contract.get("runtime_family_equivalent_to_sibling_clients") is not False:
            raise ValueError(f"{key}: sibling runtime equivalence must remain false")
        if contract.get("positional_id_is_complete_identity") is not False:
            raise ValueError(f"{key}: positional TMDB id cannot become complete identity")
        if contract.get("canonical_identity_context_path") != IDENTITY_CONTEXT_PATH:
            raise ValueError(f"{key}: canonical identity context path drift")
        if contract.get("canonical_identity_cache") != IDENTITY_CACHE_GLOBAL:
            raise ValueError(f"{key}: canonical identity cache drift")
        if contract.get("user_tmdb_credential_required") is not False:
            raise ValueError(f"{key}: end-user TMDB credential must not be required")
        if contract.get("tmdb_secret_projection_required") is not False:
            raise ValueError(f"{key}: TMDB credential embedding in published provider bytes must remain false")
        status = str(contract.get("identity_hydration_status") or "")
        if status not in {"equivalent-runtime-tmdb-key-bridge", "canonical-host-bridge"}:
            raise ValueError(f"{key}: invalid current identity hydration status {status!r}")
        capabilities = {str(value).strip() for value in client.get("brain_capabilities") or [] if str(value).strip()}
        if "series" not in capabilities:
            raise ValueError(f"{key}: series transport capability missing")

    return {
        "platform_clients": len(clients),
        "matrix_clients": len(matrix_clients),
        "published_supported_types": sorted(PUBLISHED_SUPPORTED_TYPES),
        "provider_runtime_request_types": sorted(PROVIDER_RUNTIME_REQUEST_TYPES),
        "tv_input_aliases": sorted(TV_INPUT_ALIASES),
        "required_result_fields": sorted(REQUIRED_RESULT_FIELDS),
        "identity_context": IDENTITY_CONTEXT_PATH,
        "identity_cache": IDENTITY_CACHE_GLOBAL,
    }


def main() -> int:
    summary = validate_contract_files()
    print(
        "runtime contract gate passed: "
        f"platform_clients={summary['platform_clients']} matrix_clients={summary['matrix_clients']} "
        f"published_types={','.join(summary['published_supported_types'])} "
        f"runtime_types={','.join(summary['provider_runtime_request_types'])} "
        f"tv_aliases={','.join(summary['tv_input_aliases'])} "
        f"identity_cache={summary['identity_cache']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
