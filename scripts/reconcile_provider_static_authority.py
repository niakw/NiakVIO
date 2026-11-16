#!/usr/bin/env python3
"""Keep active Global + France-only Provider v3 structured authority complete.

ProviderBase / published bytes are derived artifacts. A clean Provider v3 bundle
cannot be replayed safely unless its three durable DATA authorities exist:
provider_patches, provider_capabilities and provider-v3-static-knowledge.

This module can:
* recover a missing static-knowledge row from the exact managed CONFIG Lego
  already embedded in current NiakVIO-owned bytes;
* recover the one explicitly-supported open_archive_public_domain contract when
  an older activation published its bytes before persisting overrides;
* persist exact CONFIG-derived static DATA for newly activated Global and France-only providers.

It never performs HTTP and never executes provider JavaScript.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from current_provider_scope import (
    active_provider_rows,
    visible_provider_rows,
    projection_active_provider_ids,
    projection_runtime_visible_provider_ids,
)
from generate_language_manifests import france_only_catalog_rows
from provider_base_store import canonical_id
from provider_patch_blocks import decode_managed_data, validate_managed_fixes

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
STATIC = ROOT / "automation/provider-v3-static-knowledge.json"
MATERIALIZATION = ROOT / "provider-v3-materialization.json"

OPEN_ARCHIVE_PROVIDER = "internet-archive"
OPEN_ARCHIVE_STRATEGY = "open_archive_public_domain"
OPEN_ARCHIVE_BASE = "https://archive.org"
OPEN_ARCHIVE_LEGO = "scripts/provider_patches/internet_archive_public_domain_runtime_v1.py"

def normalize_active_activation_overrides(
    overrides: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[str]:
    """Remove stale enabled flags from providers already active by lifecycle.

    Provider-folder/lifecycle state is the sole activation authority. A retained
    manifest_overrides.enabled field on an active provider is a stale second
    authority and can re-disable that provider during later rebuilds. Other
    manifest overrides remain untouched.
    """
    patches = overrides.get("provider_patches")
    if not isinstance(patches, dict):
        raise ValueError("provider override map required")
    changed: list[str] = []
    for row in rows:
        pid = canonical_id(row.get("id"))
        if not pid:
            continue
        patch = patches.get(pid)
        if not isinstance(patch, dict):
            continue
        manifest_overrides = patch.get("manifest_overrides")
        if not isinstance(manifest_overrides, dict) or "enabled" not in manifest_overrides:
            continue
        manifest_overrides.pop("enabled", None)
        if not manifest_overrides:
            patch.pop("manifest_overrides", None)
        changed.append(pid)
    return sorted(set(changed))


def active_current_rows() -> list[dict[str, Any]]:
    """Return active current catalogue rows across Global + France-only authority."""
    rows = [dict(row) for row in active_provider_rows() if isinstance(row, dict)]
    seen = {canonical_id(row.get("id")) for row in rows if canonical_id(row.get("id"))}
    for row in france_only_catalog_rows(root=ROOT):
        if not isinstance(row, dict) or row.get("enabled") is False:
            continue
        pid = canonical_id(row.get("id"))
        if not pid:
            raise ValueError("France-only active provider without canonical id")
        if pid in seen:
            raise ValueError(f"{pid}: France-only identity collides with Global active scope")
        seen.add(pid)
        rows.append(dict(row))
    return rows


def runtime_visible_current_rows() -> list[dict[str, Any]]:
    """Return exact Global+France runtime-visible rows, including retained disabled.

    Pending onboarding rows are deliberately excluded by the canonical projection
    runtime scope. France-only rows come from provider_catalog authority and are
    never injected into the Global manifest.
    """
    rows = [dict(row) for row in visible_provider_rows() if isinstance(row, dict)]
    seen = {canonical_id(row.get("id")) for row in rows if canonical_id(row.get("id"))}
    for row in france_only_catalog_rows(root=ROOT):
        if not isinstance(row, dict):
            continue
        pid = canonical_id(row.get("id"))
        if not pid:
            raise ValueError("France-only runtime-visible provider without canonical id")
        if pid in seen:
            raise ValueError(f"{pid}: France-only identity collides with Global visible scope")
        seen.add(pid)
        rows.append(dict(row))

    runtime_ids = projection_runtime_visible_provider_ids()
    filtered = [
        row for row in rows
        if canonical_id(row.get("id")) in runtime_ids
    ]
    filtered_ids = {
        canonical_id(row.get("id"))
        for row in filtered
        if canonical_id(row.get("id"))
    }
    if filtered_ids != runtime_ids:
        raise ValueError(
            "runtime-visible current row mismatch "
            f"missing={sorted(runtime_ids-filtered_ids)} extra={sorted(filtered_ids-runtime_ids)}"
        )
    return filtered



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


def _materialization_row_from_bundle(provider_id: str, bundle: Path, model: dict[str, Any]) -> dict[str, Any]:
    raw = bundle.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")
    fix_ids = validate_managed_fixes(text)
    core_ids = [fix_id for fix_id in fix_ids if fix_id.startswith("CORE.")]
    data_digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "provider": canonical_id(provider_id),
        "file": bundle.relative_to(ROOT).as_posix(),
        "sha256": digest,
        "providerDataSha256": data_digest,
        "baseStrippedGeneratedCore": False,
        "fixIds": fix_ids,
        "coreCount": len(core_ids),
        "applied": [],
        "deviceSpecificJs": False,
        "devices": ["tv", "mobile", "desktop"],
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
        "staticAuthorityReconciledProviders": [canonical_id(provider_id)],
        "materializationRecoveredFromExactPublishedBytes": True,
        "minimizer": {
            "enabled": True,
            "savedBytes": 0,
            "transformedLines": 0,
            "skippedReason": "published-byte-recovery",
        },
    }


def _materialization_row_matches_bundle(
    row: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    """Exact executable authority is file + bytes + structured CONFIG digest."""
    return all(
        str(row.get(key) or "") == str(expected.get(key) or "")
        for key in ("file", "sha256", "providerDataSha256")
    )


def _rebind_materialization_row(
    previous: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Refresh exact-byte authority without discarding historical diagnostics."""
    out = copy.deepcopy(previous)
    for key in (
        "provider",
        "file",
        "sha256",
        "providerDataSha256",
        "baseStrippedGeneratedCore",
        "fixIds",
        "coreCount",
        "deviceSpecificJs",
        "devices",
        "legacyProviderJsExecuted",
        "upstreamJsExecuted",
    ):
        out[key] = copy.deepcopy(expected.get(key))
    reconciled = {
        canonical_id(value)
        for value in [
            *(out.get("staticAuthorityReconciledProviders") or []),
            *(expected.get("staticAuthorityReconciledProviders") or []),
        ]
        if canonical_id(value)
    }
    out["staticAuthorityReconciledProviders"] = sorted(reconciled)
    out["materializationReboundFromExactPublishedBytes"] = True
    if not isinstance(out.get("minimizer"), dict):
        out["minimizer"] = copy.deepcopy(expected.get("minimizer") or {})
    if not isinstance(out.get("applied"), list):
        out["applied"] = copy.deepcopy(expected.get("applied") or [])
    return out


def reconcile_materialization_from_active_bundles(*, apply: bool) -> dict[str, Any]:
    """Rebind executable materialization to the exact active Global+France union.

    Existing rows are not assumed current merely because their provider identity
    is present. Content-addressed filenames can rotate during Global or
    France-only minimization, so stale file/hash/CONFIG-digest rows are rebound
    from the exact current published bundle.
    """
    doc = load(MATERIALIZATION, {"schemaVersion": 3, "providers": []})
    current_rows = active_current_rows()
    current_ids = {canonical_id(row.get("id")) for row in current_rows if canonical_id(row.get("id"))}
    projection_ids = projection_active_provider_ids()
    if current_ids != projection_ids:
        raise ValueError(
            "active current/projection identity mismatch "
            f"missing={sorted(projection_ids-current_ids)} extra={sorted(current_ids-projection_ids)}"
        )

    raw_rows = [row for row in doc.get("providers") or [] if isinstance(row, dict)]
    retired = sorted(
        canonical_id(row.get("provider"))
        for row in raw_rows
        if canonical_id(row.get("provider")) and canonical_id(row.get("provider")) not in current_ids
    )
    existing_rows = [
        row for row in raw_rows
        if canonical_id(row.get("provider")) in current_ids
    ]
    by_id = {
        canonical_id(row.get("provider")): row
        for row in existing_rows if canonical_id(row.get("provider"))
    }
    if len(by_id) != len(existing_rows):
        raise ValueError("duplicate active provider materialization identity")

    recovered: list[str] = []
    rebound: list[str] = []
    by_current = {
        canonical_id(row.get("id")): row for row in current_rows
        if canonical_id(row.get("id"))
    }
    rows: list[dict[str, Any]] = []
    for pid in sorted(current_ids):
        row = by_current[pid]
        bundle = (ROOT / str(row.get("filename") or "")).resolve()
        model = decode_exact_model(pid, bundle)
        expected = _materialization_row_from_bundle(pid, bundle, model)
        previous = by_id.get(pid)
        if previous is None:
            item = expected
            recovered.append(pid)
        elif not _materialization_row_matches_bundle(previous, expected):
            item = _rebind_materialization_row(previous, expected)
            rebound.append(pid)
        else:
            item = previous
        rows.append(item)

    runtime_visible = projection_runtime_visible_provider_ids()
    doc["providers"] = rows
    doc["providerCount"] = len(current_ids)
    doc["expectedProviderCount"] = len(current_ids)
    doc["activeProviderIdentityCount"] = len(current_ids)
    doc["staticKnowledgeProviderCount"] = len(runtime_visible)
    doc["targetedPublicationReconciledProviders"] = sorted(set(
        [str(x) for x in doc.get("targetedPublicationReconciledProviders") or []]
        + recovered
        + rebound
    ))
    changed = bool(recovered or rebound or retired or raw_rows != rows)
    if apply and changed:
        write(MATERIALIZATION, doc)
    return {
        "recoveredCount": len(recovered),
        "recovered": recovered,
        "reboundCount": len(rebound),
        "rebound": rebound,
        "retiredCount": len(retired),
        "retired": retired,
        "activeProviderIdentityCount": len(current_ids),
        "staticKnowledgeProviderCount": len(runtime_visible),
    }

def reconcile_active_global(*, apply: bool) -> dict[str, Any]:
    overrides = load(OVERRIDES, {"provider_patches": {}, "provider_capabilities": {}})
    static = load(STATIC, {"schemaVersion": 1, "providers": {}})
    patches = overrides.setdefault("provider_patches", {})
    capabilities = overrides.setdefault("provider_capabilities", {})
    static_rows = static.setdefault("providers", {})
    if not isinstance(patches, dict) or not isinstance(capabilities, dict) or not isinstance(static_rows, dict):
        raise ValueError("structured provider authority maps required")

    current_rows = active_current_rows()
    runtime_rows = runtime_visible_current_rows()
    activation_reconciled = normalize_active_activation_overrides(overrides, current_rows)

    recovered: list[dict[str, str]] = []

    # Static knowledge is Brain reconstruction authority, not executable-only
    # authority. Recover every current runtime-visible identity (active plus
    # retained disabled, Global plus France-only) from its exact managed CONFIG
    # Lego before validating the canonical union.
    for row in runtime_rows:
        pid = canonical_id(row.get("id"))
        if isinstance(static_rows.get(pid), dict):
            continue
        bundle = (ROOT / str(row.get("filename") or "")).resolve()
        model = decode_exact_model(pid, bundle)
        static_rows[pid] = static_row_from_exact_model(
            pid,
            model,
            source="current-runtime-visible-config-recovery",
        )
        recovered.append({"provider": pid, "authority": "provider-v3-static-knowledge"})

    runtime_visible = projection_runtime_visible_provider_ids()
    retired_static = sorted(
        canonical_id(value)
        for value in list(static_rows)
        if canonical_id(value) and canonical_id(value) not in runtime_visible
    )
    for pid in retired_static:
        static_rows.pop(pid, None)

    for row in current_rows:
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
    static_ids = {canonical_id(value) for value in static_rows}
    missing_runtime_static = sorted(runtime_visible - static_ids)
    extra_runtime_static = sorted(static_ids - runtime_visible)
    if missing_runtime_static or extra_runtime_static:
        raise ValueError(
            "provider-v3-static-knowledge/runtime-visible identity mismatch "
            f"missing={missing_runtime_static} extra={extra_runtime_static}"
        )
    if apply and (recovered or retired_static or activation_reconciled):
        write(OVERRIDES, overrides)
        write(STATIC, static)
    materialization = reconcile_materialization_from_active_bundles(apply=apply)
    return {
        "recoveredCount": len(recovered),
        "recovered": recovered,
        "activationReconciledCount": len(activation_reconciled),
        "activationReconciled": activation_reconciled,
        "materializationRecoveredCount": materialization["recoveredCount"],
        "materializationRecovered": materialization["recovered"],
        "materializationReboundCount": materialization["reboundCount"],
        "materializationRebound": materialization["rebound"],
        "materializationRetiredCount": materialization["retiredCount"],
        "materializationRetired": materialization["retired"],
        "activeGlobal": len(active_provider_rows()),
        "activeCurrent": len(active_current_rows()),
        "activeProjectionUnion": len(projection_active_provider_ids()),
        "runtimeVisibleProjectionUnion": len(runtime_visible),
        "runtimeVisibleCurrent": len(runtime_rows),
        "staticRetiredCount": len(retired_static),
        "staticRetired": retired_static,
        "apply": bool(apply),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = reconcile_active_global(apply=args.apply)
    print(
        "PROVIDER_STATIC_AUTHORITY_RECONCILE_OK "
        f"active_global={result['activeGlobal']} active_current={result['activeCurrent']} recovered={result['recoveredCount']} "
        f"activation_reconciled={result['activationReconciledCount']} "
        f"materialization_recovered={result['materializationRecoveredCount']} "
        f"materialization_rebound={result['materializationReboundCount']} "
        f"mode={'apply' if args.apply else 'check'}"
    )
    for row in result["recovered"]:
        print(f"FIELD_PROVIDER_STATIC_AUTHORITY_RECOVERED provider={row['provider']} authority={row['authority']}")
    for provider in result["activationReconciled"]:
        print(f"FIELD_PROVIDER_ACTIVATION_OVERRIDE_RECONCILED provider={provider} authority=provider-folder-lifecycle")
    for provider in result["materializationRecovered"]:
        print(f"FIELD_PROVIDER_MATERIALIZATION_RECOVERED provider={provider} source=exact-published-bytes")
    for provider in result["materializationRebound"]:
        print(f"FIELD_PROVIDER_MATERIALIZATION_REBOUND provider={provider} source=exact-current-published-bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
