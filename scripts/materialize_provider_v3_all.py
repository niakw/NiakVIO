#!/usr/bin/env python3
"""Materialize every clean Provider v3 bundle from one cross-device source of truth.

Provider JavaScript is device-agnostic. TV, Mobile and Desktop manifests may select
or disable providers, but they must all reference the exact same materialized JS
bytes for a given provider/version.

Source:
  ProviderBase v3 + structured provider DATA + owned PROVIDER.* / CORE.* Lego.

Forbidden as executable seeds:
  published legacy provider JS, upstream provider JS, per-device JS forks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_base_store import (  # noqa: E402
    build_base_from_seed,
    build_clean_provider_seed,
    build_provider_data_model,
    canonical_id,
    compose_provider_bundle,
)
from apply_provider_overrides import apply_overrides  # noqa: E402
from provider_patch_blocks import validate_managed_fixes  # noqa: E402

DEFAULT_SOURCE_MANIFEST = ROOT / "manifest.json"
DEFAULT_OVERRIDES = ROOT / "provider-overrides.json"
DEFAULT_OUT = ROOT / "providers"
DEFAULT_REPORT = ROOT / "provider-v3-materialization.json"
EXPECTED_PROVIDER_COUNT = 96


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def origin(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return ""
        return f"{parsed.scheme}://{parsed.hostname.casefold()}"
    except ValueError:
        return ""


def identity_input(patch: dict[str, Any]) -> dict[str, Any]:
    raw = patch.get("identity_input")
    if not isinstance(raw, dict):
        mode = "catalog_search" if (
            patch.get("api_recipe")
            or patch.get("official_site")
            or patch.get("learned_urls")
            or patch.get("learned_routes")
        ) else "tmdb_direct"
        return {
            "mode": mode,
            "requiresTmdbBeforeRun": mode != "tmdb_direct",
            "requiredFields": (
                ["title", "year", "mediaType"]
                if mode != "tmdb_direct"
                else ["tmdbId", "mediaType"]
            ),
        }
    mode = str(raw.get("mode") or "tmdb_direct").strip().casefold()
    if mode not in {"tmdb_direct", "catalog_search", "external_id"}:
        raise ValueError(f"invalid identity mode: {mode}")
    required = [
        str(v).strip()
        for v in raw.get("required_fields") or raw.get("requiredFields") or []
        if str(v).strip()
    ]
    return {
        "mode": mode,
        "requiresTmdbBeforeRun": bool(
            raw.get(
                "requires_tmdb_before_run",
                raw.get("requiresTmdbBeforeRun", mode != "tmdb_direct"),
            )
        ),
        "requiredFields": required or (
            ["title", "year", "mediaType"]
            if mode != "tmdb_direct"
            else ["tmdbId", "mediaType"]
        ),
    }


def provider_model(
    provider_id: str,
    patch: dict[str, Any],
    capability: dict[str, Any],
) -> dict[str, Any]:
    fixed = patch.get("fixed_endpoint")
    fixed = fixed if isinstance(fixed, dict) else {}

    official_site = str(patch.get("official_site") or "").strip() or None
    official_hub = str(patch.get("official_hub") or "").strip() or None
    official_api = str(patch.get("official_api") or "").strip() or None
    fixed_api = str(fixed.get("api") or "").strip() or None

    origins: list[str] = []
    for value in (official_site, official_hub, official_api, fixed_api):
        item = origin(value)
        if item and item not in origins:
            origins.append(item)

    observed_urls: list[str] = []
    for value in patch.get("learned_urls") or []:
        item = str(value).strip()
        if item and item not in observed_urls:
            observed_urls.append(item)
    # Explicit current endpoints are safe provenance facts and help generic
    # route expansion without importing historical/upstream executable code.
    for value in (official_site, official_api, fixed_api):
        item = str(value or "").strip()
        if item and item not in observed_urls:
            observed_urls.append(item)

    routes = [
        str(v).strip()
        for v in patch.get("learned_routes") or []
        if str(v).strip()
    ]

    return {
        "knownSite": official_site,
        "strategy": str(
            patch.get("capability")
            or capability.get("strategy")
            or capability.get("capability")
            or "unknown"
        ).strip().casefold(),
        "officialSite": official_site,
        "officialHub": official_hub,
        "officialApi": official_api,
        "fixedApi": fixed_api,
        "origins": origins,
        "observedUrls": observed_urls,
        "routes": routes,
        "apiRecipe": (
            patch.get("api_recipe")
            if isinstance(patch.get("api_recipe"), dict)
            else None
        ),
        "identityInput": identity_input(patch),
        "strictIdentity": bool(patch.get("strict_identity", False)),
        "strictHtmlIdentity": bool(patch.get("strict_html_identity", False)),
        "outputUrlHostRewrites": patch.get("output_url_host_rewrites") or [],
        "outputLanguageRules": patch.get("output_language_rules") or [],
        "domainSubstitutions": patch.get("domain_substitutions") or {},
    }


def base_version(value: object) -> str:
    raw = str(value or "0.0.0").strip() or "0.0.0"
    for token in ("-v3-all-", "-tv-native", "-tv-lab", "-tv-strict"):
        if token in raw:
            return raw.split(token, 1)[0]
    return raw


def strict_projection(
    source_manifest: dict[str, Any],
    ids: list[str],
    generation: str,
) -> dict[str, Any]:
    wanted = [canonical_id(v) for v in ids if canonical_id(v)]
    rows_by_id = {
        canonical_id(str(row.get("id") or "")): row
        for row in source_manifest.get("scrapers") or []
        if isinstance(row, dict)
    }
    missing = [provider_id for provider_id in wanted if provider_id not in rows_by_id]
    if missing:
        raise ValueError(f"projection missing providers: {missing}")
    rows = [dict(rows_by_id[provider_id]) for provider_id in wanted]
    return {
        "name": "NiakVIO STRICT CLIENT LAB",
        "version": f"{source_manifest.get('version', '0')}-projection-{generation[:10]}",
        "scrapers": rows,
        "description": (
            "Client validation projection only. Provider JS bytes are the same "
            "cross-device global v3 artifacts used by TV, Mobile and Desktop."
        ),
    }


def materialize_all(
    *,
    source_manifest_path: Path = DEFAULT_SOURCE_MANIFEST,
    overrides_path: Path = DEFAULT_OVERRIDES,
    output_dir: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
    project_manifest_path: Path | None = None,
    project_ids: list[str] | None = None,
) -> dict[str, Any]:
    manifest = load(source_manifest_path)
    overrides = load(overrides_path)
    patches = overrides.get("provider_patches")
    capabilities = overrides.get("provider_capabilities")
    if not isinstance(patches, dict) or not isinstance(capabilities, dict):
        raise ValueError("provider override maps required")

    rows = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canonical_id(str(row.get("id") or ""))
    ]
    if len(rows) != EXPECTED_PROVIDER_COUNT:
        raise ValueError(
            f"global v3 manifest provider count={len(rows)} expected={EXPECTED_PROVIDER_COUNT}"
        )

    ids = [canonical_id(str(row.get("id") or "")) for row in rows]
    if len(set(ids)) != EXPECTED_PROVIDER_COUNT:
        raise ValueError("global v3 manifest contains duplicate provider ids")

    patch_ids = {canonical_id(v) for v in patches}
    capability_ids = {canonical_id(v) for v in capabilities}
    missing_patches = sorted(set(ids) - patch_ids)
    missing_capabilities = sorted(set(ids) - capability_ids)
    if missing_patches or missing_capabilities:
        raise ValueError(
            f"structured DATA incomplete patches={missing_patches} "
            f"capabilities={missing_capabilities}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    report_rows: list[dict[str, Any]] = []
    aggregate = hashlib.sha256()

    for index, entry in enumerate(rows, start=1):
        provider_id = canonical_id(str(entry.get("id") or ""))
        print(
            "FIELD_PROVIDER_V3_MATERIALIZE_BEGIN "
            f"index={index} total={len(rows)} provider={provider_id}",
            flush=True,
        )
        patch = patches.get(provider_id)
        capability = capabilities.get(provider_id)
        if not isinstance(patch, dict) or not isinstance(capability, dict):
            raise ValueError(f"{provider_id}: missing structured DATA")

        model = provider_model(provider_id, patch, capability)
        seed = build_clean_provider_seed(
            provider_id,
            entry,
            known_site=model.get("knownSite"),
            provider_model=model,
        )
        base, stripped = build_base_from_seed(
            provider_id,
            seed,
            overrides_path=overrides_path,
        )
        data = build_provider_data_model(
            provider_id,
            entry,
            known_site=model.get("knownSite"),
            provider_model=model,
        )
        bundle = compose_provider_bundle(provider_id, base, data)
        bundle, applied = apply_overrides(
            provider_id,
            bundle,
            phase="discovery",
            include_global_core=True,
            config_path=overrides_path,
        )
        text = bundle.decode("utf-8", errors="strict")

        if text.count("/* BEGIN NIAKVIO_PROVIDER */") != 1:
            raise ValueError(f"{provider_id}: BEGIN PROVIDER cardinality")
        if text.count("/* END NIAKVIO_PROVIDER */") != 1:
            raise ValueError(f"{provider_id}: END PROVIDER cardinality")
        if not text.rstrip().endswith("/* END NIAKVIO_PROVIDER */"):
            raise ValueError(f"{provider_id}: bytes after END PROVIDER")
        if "searchParams.set(" in text or "searchParams.delete(" in text:
            raise ValueError(f"{provider_id}: QuickJS URLSearchParams mutation remains")

        fix_ids = validate_managed_fixes(text)
        config_id = f"PROVIDER.{provider_id.upper()}.CONFIG.V1"
        if config_id not in fix_ids:
            raise ValueError(f"{provider_id}: provider CONFIG Lego missing")
        core_ids = [fix_id for fix_id in fix_ids if fix_id.startswith("CORE.")]
        if not core_ids:
            raise ValueError(f"{provider_id}: no Core Lego materialized")

        digest = hashlib.sha256(bundle).hexdigest()
        filename = f"{provider_id}-{digest[:16]}.js"
        relative = f"providers/{filename}"
        (output_dir / filename).write_bytes(bundle)

        entry["filename"] = relative
        entry["version"] = base_version(entry.get("version"))

        aggregate.update(provider_id.encode("utf-8"))
        aggregate.update(bytes.fromhex(digest))
        report_rows.append({
            "provider": provider_id,
            "file": relative,
            "sha256": digest,
            "providerDataSha256": hashlib.sha256(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            "baseStrippedGeneratedCore": bool(stripped),
            "fixIds": fix_ids,
            "coreCount": len(core_ids),
            "applied": applied,
            "deviceSpecificJs": False,
            "devices": ["tv", "mobile", "desktop"],
            "legacyProviderJsExecuted": False,
            "upstreamJsExecuted": False,
        })

    generation = aggregate.hexdigest()
    manifest["version"] = str(manifest.get("version") or "0")
    manifest["description"] = (
        "NiakVIO Provider v3 production artifacts. One Provider JS per provider/version "
        "for TV, Mobile and Desktop; client manifests only project these same bytes."
    )
    write_json(source_manifest_path, manifest)

    report = {
        "schemaVersion": 2,
        "sourceSha": os.environ.get("GITHUB_SHA") or "",
        "generation": generation,
        "providerCount": len(report_rows),
        "expectedProviderCount": EXPECTED_PROVIDER_COUNT,
        "providers": report_rows,
        "devicePolicy": {
            "providerJsIsDeviceAgnostic": True,
            "devices": ["tv", "mobile", "desktop"],
            "perDeviceProviderForkAllowed": False,
            "clientManifestProjectionAllowed": True,
        },
        "publication": True,
        "mainTouched": True,
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
    }
    write_json(report_path, report)

    if project_manifest_path is not None:
        ids_for_projection = project_ids or []
        if not ids_for_projection:
            raise ValueError("project manifest requested without project ids")
        write_json(
            project_manifest_path,
            strict_projection(manifest, ids_for_projection, generation),
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--project-manifest", type=Path)
    parser.add_argument("--project-ids", default="")
    args = parser.parse_args()

    project_ids = [
        value.strip()
        for value in str(args.project_ids or "").split(",")
        if value.strip()
    ]
    report = materialize_all(
        source_manifest_path=args.source_manifest.resolve(),
        overrides_path=args.overrides.resolve(),
        output_dir=args.output_dir.resolve(),
        report_path=args.report.resolve(),
        project_manifest_path=(
            args.project_manifest.resolve()
            if args.project_manifest is not None
            else None
        ),
        project_ids=project_ids,
    )
    print(
        "FIELD_PROVIDER_V3_ALL_MATERIALIZED "
        f"providers={report['providerCount']} generation={report['generation'][:16]} "
        "devices=tv,mobile,desktop"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
