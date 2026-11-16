#!/usr/bin/env python3
"""Materialize the durable cross-client TMDB/IMDb identity contract.

This migration is intentionally idempotent. It records the identity surface that
NiakVIO Core/provider code already consumes so future runtime refactors cannot
silently regress to a TMDB-only positional interpretation.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "automation" / "platform-runtime-contracts.json"
MATRIX = ROOT / "automation" / "nuvio-client-compatibility-matrix.json"
CAPABILITY = "media_identity_hydration"
CONTEXT_PATH = "__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id"
CACHE_GLOBAL = "__nuvioTmdbMetadataCacheV1"
CACHE_SHAPE = '{state:"ok",metadata:{external_ids:{imdb_id:"tt..."}}}'


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def upgrade_platform(data: dict) -> None:
    if data.get("schema_version") != 2:
        raise SystemExit("platform-runtime-contracts schema_version must remain 2")
    order = list(data.get("capability_order") or [])
    if CAPABILITY not in order:
        try:
            index = order.index("tmdb_api_key") + 1
        except ValueError as exc:
            raise SystemExit("tmdb_api_key capability missing") from exc
        order.insert(index, CAPABILITY)
    data["capability_order"] = order

    identity = data.setdefault("media_identity_contract", {})
    identity.update({
        "version": 1,
        "positional_tmdb_id_is_complete_identity": False,
        "canonical_context_imdb_path": CONTEXT_PATH,
        "canonical_metadata_cache_global": CACHE_GLOBAL,
        "canonical_metadata_cache_entry_shape": CACHE_SHAPE,
        "cache_population_timing": (
            "after provider/Core bundle initialization and before getStreams invocation "
            "using an audited official runtime capability or canonical host context"
        ),
        "user_tmdb_credential_required": False,
        "secret_projection_to_provider_javascript": False,
        "rule": (
            "Preserve TMDB and IMDb as one media identity contract. Current official "
            "clients may expose an audited runtime TMDB key capability that lets NiakVIO "
            "Core hydrate its canonical metadata cache; the credential must never be "
            "embedded in published provider bytes and an end-user key must not be required "
            "when the official build supplies its fallback."
        ),
    })

    clients = data.get("clients") or {}
    for client_id, client in clients.items():
        caps = client.setdefault("capabilities", {})
        tmdb = caps.get("tmdb_api_key") or {}
        tmdb_state = str(tmdb.get("state") or "").casefold()
        if tmdb_state not in {"native", "bridge"}:
            raise SystemExit(
                f"{client_id}: audited runtime TMDB capability missing; "
                "refuse to fabricate identity hydration"
            )
        caps[CAPABILITY] = {
            "state": "bridge",
            "detail": (
                "NiakVIO Core can hydrate its canonical TMDB/IMDb metadata cache from "
                "the audited runtime TMDB capability without embedding a credential in "
                "published provider bytes."
            ),
        }


def upgrade_matrix(data: dict) -> None:
    policy = data.setdefault("policy", {})
    policy["media_identity_contract"] = (
        "The positional getStreams(tmdbId, mediaType, season, episode) argument is "
        "transport, not the full media identity. NiakVIO Core owns the canonical "
        f"TMDB/IMDb metadata path {CONTEXT_PATH} and cache {CACHE_GLOBAL}. "
        "An audited official runtime TMDB capability may hydrate that cache, while "
        "published provider bytes remain credential-free."
    )
    clients = data.get("clients") or {}
    for client_id, client in clients.items():
        contract = client.setdefault("provider_contract", {})
        contract["positional_id_is_complete_identity"] = False
        contract["canonical_identity_context_path"] = CONTEXT_PATH
        contract["canonical_identity_cache"] = CACHE_GLOBAL
        contract["canonical_identity_cache_entry_shape"] = CACHE_SHAPE
        contract["user_tmdb_credential_required"] = False
        contract["tmdb_secret_projection_required"] = False
        contract["identity_hydration_status"] = "equivalent-runtime-tmdb-key-bridge"
        contract["identity_hydration_note"] = (
            "The currently audited official runtime exposes a TMDB key capability "
            "to the plugin host. NiakVIO Core may use it to hydrate external_ids/IMDb; "
            "shared provider bytes must not embed or directly require the credential."
        )


def main() -> int:
    platform = load(PLATFORM)
    matrix = load(MATRIX)
    upgrade_platform(platform)
    upgrade_matrix(matrix)
    dump(PLATFORM, platform)
    dump(MATRIX, matrix)
    print(
        "runtime media identity contract upgraded: "
        f"context={CONTEXT_PATH} cache={CACHE_GLOBAL} user_tmdb_credential_required=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
