#!/usr/bin/env python3
"""Keep active Global Provider v3 structured authority complete.

ProviderBase / published bytes are derived artifacts. A clean Provider v3 bundle
cannot be replayed safely unless its three durable DATA authorities exist:
provider_patches, provider_capabilities and provider-v3-static-knowledge.

This module can:
* recover a missing static-knowledge row from the exact managed CONFIG Lego
  already embedded in current NiakVIO-owned bytes;
* recover the one explicitly-supported open_archive_public_domain contract when
  an older activation published its bytes before persisting overrides;
* persist exact CONFIG-derived static DATA for newly activated Global providers.

It never performs HTTP and never executes provider JavaScript.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from current_provider_scope import active_provider_rows
from provider_base_store import canonical_id
from provider_patch_blocks import decode_managed_data

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
STATIC = ROOT / "automation/provider-v3-static-knowledge.json"

OPEN_ARCHIVE_PROVIDER = "internet-archive"
OPEN_ARCHIVE_STRATEGY = "open_archive_public_domain"
OPEN_ARCHIVE_BASE = "https://archive.org"
OPEN_ARCHIVE_LEGO = "scripts/provider_patches/internet_archive_public_domain_runtime_v1.py"


def load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return copy.deepcopy(default)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: JSON object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _fix_id(provider_id: str) -> str:
    return f"PROVIDER.{canonical_id(provider_id).upper()}.CONFIG.V1"


def decode_exact_model(provider_id: str, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if "NIAKVIO_PROVIDER_BASE_OWNED_V3" not in text:
        raise ValueError(f"{provider_id}: active bundle is not NiakVIO-owned Provider v3")
    model = decode_managed_data(text, _fix_id(provider_id))
    if not isinstance(model, dict):
        raise ValueError(f"{provider_id}: CONFIG Lego DATA is not an object")
    if canonical_id(model.get("providerId")) != canonical_id(provider_id):
        raise ValueError(f"{provider_id}: CONFIG providerId mismatch")
    return model


def _hosts(model: dict[str, Any]) -> list[str]:
    out: list[str] = []
    values: list[Any] = [
        model.get("knownSite"),
        model.get("officialSite"),
        model.get("officialHub"),
        model.get("officialApi"),
        model.get("fixedApi"),
        *(model.get("origins") or []),
        *(model.get("observedUrls") or []),
    ]
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        try:
            host = str(urlparse(raw).hostname or "").strip().casefold()
        except ValueError:
            host = ""
        if host and host not in out:
            out.append(host)
    return out[:64]


def static_row_from_exact_model(
    provider_id: str,
    model: dict[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    exact = copy.deepcopy(model)
    exact.pop("providerId", None)
    runtime_family = str(exact.get("sourceRuntimeFamily") or "unknown").strip().casefold() or "unknown"
    return {
        "model": exact,
        "knowledge": {
            "hosts": _hosts(model),
            "routes": [str(x) for x in model.get("routes") or [] if str(x).strip()][:128],
            "routeFragments": [],
            "observedUrls": [str(x) for x in model.get("observedUrls") or [] if str(x).strip()][:96],
            "decodedStaticStringCount": 0,
            "runtimeFamily": runtime_family,
        },
        "sources": [{
            "source": source,
            "sourceName": "NiakVIO exact managed Provider CONFIG",
            "upstreamId": canonical_id(provider_id),
            "manifestOrigin": "",
            "upstreamSha256": "",
            "upstreamKnowledgeSource": "managed-config-lego",
            "codeRole": "knowledge-only",
            "codeExecuted": False,
        }],
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
    }


def refresh_static_counts(static: dict[str, Any]) -> None:
    providers = static.setdefault("providers", {})
    if not isinstance(providers, dict):
        raise ValueError("provider-v3-static-knowledge providers map required")
    count = len(providers)
    static["providerCount"] = count
    static.setdefault("schemaVersion", 1)
    static.setdefault("role", "durable-structured-provider-data")
    static["legacyProviderJsExecuted"] = False
    static["upstreamJsExecuted"] = False
    for key in ("contractRecognition", "routeReconstruction", "routeRecovery"):
        row = static.get(key)
        if isinstance(row, dict) and "providerCount" in row:
            row["providerCount"] = count


def persist_static_from_bundle(
    static: dict[str, Any],
    provider_id: str,
    bundle: Path,
    *,
    source: str,
    overwrite: bool = False,
) -> bool:
    providers = static.setdefault("providers", {})
    if not isinstance(providers, dict):
        raise ValueError("provider-v3-static-knowledge providers map required")
    pid = canonical_id(provider_id)
    if pid in providers and not overwrite:
        return False
    model = decode_exact_model(pid, bundle)
    providers[pid] = static_row_from_exact_model(pid, model, source=source)
    refresh_static_counts(static)
    return True


def _generic_capability(model: dict[str, Any], types: list[str]) -> dict[str, Any]:
    strategy = str(model.get("strategy") or "unknown").strip().casefold()
    return {
        "strategy": strategy,
        "validation": "recovered_from_exact_managed_config",
        "allow_html_url": strategy in {"html_scraper", "mixed_embed_resolver", "iframe"},
        "requires_direct_media": strategy in {"api_stream_resolver", "direct_media", OPEN_ARCHIVE_STRATEGY},
        "observed_origins": [str(x) for x in model.get("origins") or [] if str(x).strip()],
        "generated_from_manifest": True,
        "generated_from_manifest_or_stage": True,
        "catalogue_types": list(types),
    }


def _open_archive_patch(model: dict[str, Any], types: list[str], *, enabled: bool) -> dict[str, Any]:
    if canonical_id(model.get("providerId")) != OPEN_ARCHIVE_PROVIDER:
        raise ValueError("open archive Provider CONFIG identity mismatch")
    if str(model.get("strategy") or "").strip().casefold() != OPEN_ARCHIVE_STRATEGY:
        raise ValueError("internet-archive CONFIG strategy mismatch")
    origins = {str(x).strip().rstrip("/") for x in model.get("origins") or [] if str(x).strip()}
    if str(model.get("officialSite") or "").strip().rstrip("/") != OPEN_ARCHIVE_BASE or OPEN_ARCHIVE_BASE not in origins:
        raise ValueError("internet-archive exact CONFIG does not bind archive.org")
    if types != ["movie"]:
        raise ValueError("internet-archive must remain movie-only")
    return {
        "notes": [
            "Recovered from exact managed Provider CONFIG after an older activation omitted durable structured authority.",
            "Runtime is restricted to explicitly public-domain Internet Archive movie items and rechecks item license metadata.",
        ],
        "replacements": {},
        "runtime_domain_replacements": {},
        "route_replacements": {},
        "profiles": [],
        "capability": OPEN_ARCHIVE_STRATEGY,
        "official_hub": None,
        "official_site": OPEN_ARCHIVE_BASE,
        "official_api": OPEN_ARCHIVE_BASE,
        "published_types": ["movie"],
        "manifest_overrides": {
            "enabled": bool(enabled),
            "disabledPlatforms": [],
        },
        "provider_lego_scripts": [OPEN_ARCHIVE_LEGO],
        "provider_lego_options": {
            OPEN_ARCHIVE_LEGO: {
                "base": OPEN_ARCHIVE_BASE,
                "provider": OPEN_ARCHIVE_PROVIDER,
                "name": "Internet Archive — Public Domain",
                "max_streams": 4,
            }
        },
        # These are durable route candidates owned by the explicit provider Lego,
        # not generic route-proof authority.
        "learned_routes": [
            "/advancedsearch.php",
            "/metadata/{identifier}",
            "/download/{identifier}/{file}",
        ],
        "identity_input": {
            "mode": "tmdb_direct",
            "requires_tmdb_before_run": False,
            "required_fields": ["tmdbId", "mediaType"],
        },
    }


def reconcile_active_global(*, apply: bool) -> dict[str, Any]:
    overrides = load(OVERRIDES, {"provider_patches": {}, "provider_capabilities": {}})
    static = load(STATIC, {"schemaVersion": 1, "providers": {}})
    patches = overrides.setdefault("provider_patches", {})
    capabilities = overrides.setdefault("provider_capabilities", {})
    static_rows = static.setdefault("providers", {})
    if not isinstance(patches, dict) or not isinstance(capabilities, dict) or not isinstance(static_rows, dict):
        raise ValueError("structured provider authority maps required")

    recovered: list[dict[str, str]] = []
    for row in active_provider_rows():
        pid = canonical_id(row.get("id"))
        bundle = (ROOT / str(row.get("filename") or "")).resolve()
        text = bundle.read_text(encoding="utf-8")
        if "NIAKVIO_PROVIDER_BASE_OWNED_V3" not in text:
            continue
        need_patch = not isinstance(patches.get(pid), dict)
        need_capability = not isinstance(capabilities.get(pid), dict)
        need_static = not isinstance(static_rows.get(pid), dict)
        if not (need_patch or need_capability or need_static):
            continue
        model = decode_exact_model(pid, bundle)
        types = [
            str(x).strip().casefold()
            for x in (row.get("canonicalSupportedTypes") or row.get("supportedTypes") or model.get("supportedTypes") or [])
            if str(x).strip().casefold() in {"movie", "tv", "anime"}
        ]
        types = list(dict.fromkeys(types))
        if need_patch:
            strategy = str(model.get("strategy") or "").strip().casefold()
            if pid == OPEN_ARCHIVE_PROVIDER and strategy == OPEN_ARCHIVE_STRATEGY:
                patches[pid] = _open_archive_patch(model, types, enabled=row.get("enabled") is not False)
                recovered.append({"provider": pid, "authority": "provider_patches"})
            else:
                raise ValueError(
                    f"{pid}: provider_patches missing; exact CONFIG alone cannot safely infer provider-specific Lego"
                )
        if need_capability:
            capabilities[pid] = _generic_capability(model, types)
            recovered.append({"provider": pid, "authority": "provider_capabilities"})
        if need_static:
            static_rows[pid] = static_row_from_exact_model(
                pid, model, source="current-published-config-recovery"
            )
            recovered.append({"provider": pid, "authority": "provider-v3-static-knowledge"})

    refresh_static_counts(static)
    if apply and recovered:
        write(OVERRIDES, overrides)
        write(STATIC, static)
    return {
        "recoveredCount": len(recovered),
        "recovered": recovered,
        "activeGlobal": len(active_provider_rows()),
        "apply": bool(apply),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = reconcile_active_global(apply=args.apply)
    print(
        "PROVIDER_STATIC_AUTHORITY_RECONCILE_OK "
        f"active_global={result['activeGlobal']} recovered={result['recoveredCount']} "
        f"mode={'apply' if args.apply else 'check'}"
    )
    for row in result["recovered"]:
        print(f"FIELD_PROVIDER_STATIC_AUTHORITY_RECOVERED provider={row['provider']} authority={row['authority']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
