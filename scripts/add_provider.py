#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
OVERRIDES = ROOT / "provider-overrides.json"
HUBS = ROOT / "provider-hubs.json"
TYPE_POLICY = ROOT / "provider-type-policy.json"
HEALTH_CONFIG = ROOT / "health-config.json"
WORK = ROOT / ".provider-onboarding"

import sys
sys.path.insert(0, str(ROOT / "scripts"))
import provider_base_store as base_store  # noqa: E402


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm_id(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("provider id is required")
    return base_store.canonical_id(raw)


def parse_list(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[,\n;]+", str(value or ""))
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = str(item or "").strip()
        if text and text.casefold() not in seen:
            out.append(text)
            seen.add(text.casefold())
    return out


def normalized_types(value: Any) -> list[str]:
    aliases = {
        "movie": "movie",
        "film": "movie",
        "tv": "tv",
        "series": "tv",
        "serie": "tv",
        "show": "tv",
        "other": "tv",
        "anime": "anime",
        "anim": "anime",
    }
    out: list[str] = []
    for raw in parse_list(value):
        key = raw.strip().casefold()
        mapped = aliases.get(key)
        if mapped and mapped not in out:
            out.append(mapped)
    return out or ["movie", "tv"]


def normalized_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"invalid public URL syntax: {text}")
    return text


def host(value: str) -> str:
    try:
        return (urlsplit(value).hostname or "").casefold()
    except ValueError:
        return ""


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bool_value(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().casefold()
    if not text:
        return default
    return text in {"1", "true", "yes", "on", "oui"}


def first_fixture(media_type: str) -> dict[str, Any]:
    config = load_json(HEALTH_CONFIG, {})
    fixtures = config.get("fixtures") if isinstance(config.get("fixtures"), dict) else {}
    pool = fixtures.get(media_type) if isinstance(fixtures.get(media_type), list) else []
    if not pool:
        pool = fixtures.get("movie") if isinstance(fixtures.get("movie"), list) else []
    if not pool:
        raise ValueError("health-config contains no onboarding fixture")
    return dict(pool[0])


def ensure_absent(manifest: dict[str, Any], provider_id: str) -> None:
    ids = {
        norm_id(row.get("id"))
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    if provider_id in ids:
        raise ValueError(f"provider already exists: {provider_id}")


def request_sources(
    *,
    hub: str,
    direct: str,
    telegram: str,
    api: str,
    search_queries: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if hub:
        rows.append({"type": "hub", "url": hub, "priority": 100, "purpose": "Authoritative address reference"})
    # Direct terminal URLs and API origins live in direct_candidates/api_templates.
    # They are validated as terminal/API knowledge, never misclassified as hubs.
    if telegram:
        rows.append({"type": "telegram_public", "url": telegram, "priority": 80, "purpose": "Known public provider Telegram address feed"})
    for query in search_queries:
        rows.append({"type": "search", "query": query, "priority": 35, "purpose": "Fallback route discovery"})
    return rows


def stage(request_path: Path) -> dict[str, Any]:
    request = load_json(request_path, {})
    provider_id = norm_id(request.get("id") or request.get("provider"))
    name = str(request.get("name") or provider_id).strip() or provider_id
    types = normalized_types(request.get("types") or request.get("supportedTypes"))
    languages = [value.casefold() for value in parse_list(request.get("languages") or request.get("contentLanguage"))]
    formats = [value.casefold() for value in parse_list(request.get("formats"))]
    hub = normalized_url(request.get("hub") or request.get("hub_url"))
    direct = normalized_url(request.get("direct") or request.get("direct_url"))
    telegram = normalized_url(request.get("telegram") or request.get("telegram_url"))
    api = normalized_url(request.get("api") or request.get("api_url"))
    category = str(request.get("category") or ("VF" if any(value.startswith("fr") for value in languages) else "International")).strip()
    strategy = str(request.get("strategy") or "html_scraper").strip().casefold()
    routes = parse_list(request.get("routes"))
    aliases = parse_list(request.get("aliases")) or [provider_id]
    search_queries = parse_list(request.get("search_queries") or request.get("search"))
    if not search_queries:
        search_queries = [f'"{name}" official domain']
    vf = bool_value(request.get("vf"), any(value.startswith("fr") for value in languages))
    if vf and not any(value.startswith("fr") for value in languages):
        languages.insert(0, "fr")
    existing_entry = existing_entry if isinstance(existing_entry, dict) else {}
    description = str(
        request.get("description")
        or existing_entry.get("description")
        or f"{name} provider managed by NiakVIO."
    ).strip()
    author = str(request.get("author") or existing_entry.get("author") or "NiakVIO").strip()
    version = str(request.get("version") or existing_entry.get("version") or "1.0.0").strip()

    manifest = load_json(MANIFEST, {})
    replace_existing = bool_value(request.get("replace_existing"), False)
    existing_entry = next(
        (
            row for row in manifest.get("scrapers") or []
            if isinstance(row, dict) and norm_id(row.get("id")) == provider_id
        ),
        None,
    )
    if isinstance(existing_entry, dict) and not replace_existing:
        raise ValueError(f"provider already exists: {provider_id}")

    overrides = load_json(OVERRIDES, {})
    overrides.setdefault("provider_patches", {})
    overrides.setdefault("provider_capabilities", {})
    overrides.setdefault("official_domain_hubs", {})

    origins = []
    for value in (direct, hub, telegram, api):
        if value:
            origin = f"{urlsplit(value).scheme}://{urlsplit(value).netloc}"
            if origin not in origins:
                origins.append(origin)

    overrides["provider_patches"][provider_id] = {
        "notes": [
            "Created by the NiakVIO full-auto provider onboarding workflow from structured route knowledge only.",
            "Activation remains disabled until the onboarding quick Lab proves the provider on every requested runtime group.",
        ],
        "replacements": {},
        "runtime_domain_replacements": {},
        "route_replacements": {},
        "profiles": [],
        "capability": strategy,
        "official_hub": hub or telegram or None,
        "official_site": direct or None,
        "published_types": types,
        "manifest_overrides": {
            "enabled": False,
            "disabledPlatforms": [],
        },
    }
    overrides["provider_capabilities"][provider_id] = {
        "strategy": strategy,
        "validation": "onboarding_pending",
        "allow_html_url": strategy in {"html_scraper", "mixed_embed_resolver", "iframe"},
        "requires_direct_media": strategy in {"api_stream_resolver", "direct_media"},
        "observed_origins": origins,
        "generated_from_manifest": True,
        "generated_from_manifest_or_stage": True,
        "catalogue_types": types,
    }
    if hub or telegram:
        resolver = "latest_telegram_domain" if telegram and not hub else "official_outbound"
        overrides["official_domain_hubs"][provider_id] = {
            "hub": hub or telegram,
            "aliases": aliases,
            "resolver": resolver,
            "official_link_labels": [
                "Entrer",
                "Accéder",
                "Accedez",
                "site officiel",
                "adresse officielle",
                "ouvrir",
                "website",
                "click here",
            ],
            "old_site_hosts": [],
            "old_api_hosts": [],
            "api_templates": [api] if api else [],
            "api_probe_routes": ["/", "/health", "/api"],
            "api_success_statuses": [200, 400, 401, 403, 404, 405, 429],
            "require_api_validation": False,
            "persist_official_site_without_api": True,
            **({"direct_fallback": direct} if direct else {}),
        }
    write_json(OVERRIDES, overrides)

    hubs = load_json(HUBS, {})
    hubs.setdefault("providers", {})
    direct_hosts = [value for value in [host(direct)] if value]
    hubs["providers"][provider_id] = {
        "id": provider_id,
        "name": name,
        "manifest_status": "Onboarding",
        "category": category,
        "hub": hub or None,
        "direct": direct or None,
        "telegram": telegram or None,
        "api": api or None,
        "source": "provider_onboarding_workflow",
        "schema_notes": "Address sources are evaluated in trust order and every terminal route is runtime-validated before persistence.",
        "aliases": aliases,
        "direct_candidates": [direct] if direct else [],
        "allowed_terminal_hosts": direct_hosts,
        "search_queries": search_queries,
        "sources": request_sources(hub=hub, direct=direct, telegram=telegram, api=api, search_queries=search_queries),
        "search_confirmation_runs": 2,
    }
    write_json(HUBS, hubs)

    type_policy = load_json(TYPE_POLICY, {"schema_version": 1, "providers": {}})
    type_policy.setdefault("providers", {})[provider_id] = {"supportedTypes": types}
    write_json(TYPE_POLICY, type_policy)

    entry: dict[str, Any] = {
        "id": provider_id,
        "name": name,
        "description": description,
        "version": version,
        "author": author,
        "supportedTypes": types,
        "filename": "",
        "enabled": False,
        "hasSettings": False,
        "formats": formats,
        "contentLanguage": languages,
        "disabledPlatforms": [],
    }

    provider_model = {
        "strategy": strategy,
        "knownSite": direct or hub or telegram or None,
        "officialSite": direct or None,
        "officialHub": hub or telegram or None,
        "officialApi": api or None,
        "origins": origins,
        "observedUrls": [value for value in (api, direct) if value],
        "routes": routes,
    }
    base_relative, base_sha, _stripped = base_store.persist_clean_provider_seed(
        provider_id,
        entry,
        known_site=direct or hub or telegram or None,
        provider_model=provider_model,
        overrides_path=OVERRIDES,
    )
    base_path = ROOT / base_relative
    published_relative = f"providers/{provider_id}--nuvio--{base_sha[:16]}.js"
    published_path = ROOT / published_relative
    published_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(base_path, published_path)
    entry["filename"] = published_relative
    scrapers = manifest.setdefault("scrapers", [])
    if replace_existing:
        replaced = False
        for index, row in enumerate(scrapers):
            if isinstance(row, dict) and norm_id(row.get("id")) == provider_id:
                scrapers[index] = entry
                replaced = True
                break
        if not replaced:
            raise ValueError(f"{provider_id}: replace_existing requested but manifest row disappeared")
    else:
        scrapers.append(entry)
    write_json(MANIFEST, manifest)

    provenance = load_json(PROVENANCE, {})
    providers = provenance.setdefault("providers", {})
    previous_provenance = providers.get(provider_id) if isinstance(providers.get(provider_id), dict) else {}
    providers[provider_id] = {
        **previous_provenance,
        "id": provider_id,
        "published_filename": published_relative,
        "sha256": base_sha,
        "patched_sha256": base_sha,
        "base_filename": base_relative,
        "base_sha256": base_sha,
        "base_source": base_store.CLEAN_RECONSTRUCTION_SOURCE,
        "clean_reconstruction_required": False,
        "clean_reconstruction_verified": True,
        "clean_reconstruction_authoring_version": base_store.CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        "clean_reconstruction_verified_at": iso_now(),
        "local_patches": [],
        "source": "niakvio-onboarding",
        "source_name": "NiakVIO structured provider onboarding",
        "source_repository": "NiakVIO",
        "source_license": "GPL-3.0-only",
        "source_license_evidence": "LICENSE",
        "upstream_id": provider_id,
        "upstream_filename": None,
        "checked_at": iso_now(),
        "check_mode": "onboarding_quick",
        "check_status": "pending",
        "health_score": 0,
        "activation_eligible": False,
        "strict_activation_eligible": False,
        "runtime_evidence_eligible": False,
        "activation_mode": "onboarding_pending",
        "activation_blockers": ["onboarding_quick_lab_pending"],
        "onboarding_rebuild": bool(replace_existing),
    }
    write_json(PROVENANCE, provenance)
    base_store.repair_legacy_bases()

    fixture = first_fixture(types[0])
    lab_config = {
        "providers": provider_id,
        "clients": ["tv", "desktop", "mobile"],
        "fixture": {
            "tmdbId": str(fixture.get("tmdbId") or ""),
            "mediaType": str(fixture.get("mediaType") or types[0]),
            "title": fixture.get("title") or fixture.get("label"),
            "year": fixture.get("year"),
            "season": fixture.get("season"),
            "episode": fixture.get("episode"),
            "expectedDurationMinutes": fixture.get("expectedDurationMinutes"),
        },
        "provider_timeout_ms": 12000,
        "retry_provider_timeouts": False,
        "max_settings_profiles": 1,
        "max_streams_per_runtime": 2,
        "probe_all_streams": False,
        "playback_timeout_ms": 5000,
        "stream_sampling": "spread",
        "provider_concurrency": 1,
        "max_fetches": 18,
        "max_distinct_hosts": 12,
        "max_redirects": 4,
        "policy": {
            "blocking": False,
            "block_identity_contradictions": True,
            "require_identity_match": False,
        },
    }

    normalized = {
        "id": provider_id,
        "name": name,
        "types": types,
        "languages": languages,
        "formats": formats,
        "hub": hub,
        "direct": direct,
        "telegram": telegram,
        "api": api,
        "site": direct or hub or telegram,
        "vf": vf,
        "strategy": strategy,
        "routes": routes,
        "fixture": lab_config["fixture"],
        "replace_existing": bool(replace_existing),
    }
    WORK.mkdir(parents=True, exist_ok=True)
    write_json(WORK / "current.json", normalized)
    write_json(WORK / "lab-config.json", lab_config)
    print(
        "FIELD_PROVIDER_ONBOARDING_STAGE "
        f"id={provider_id} types={','.join(types)} vf={str(vf).lower()} "
        f"replace_existing={str(replace_existing).lower()} "
        f"base={base_relative} published={published_relative}"
    )
    return normalized


def refresh(provider_id: str) -> dict[str, Any]:
    provider_id = norm_id(provider_id)
    current = load_json(WORK / "current.json", {})
    manifest = load_json(MANIFEST, {})
    entry = next(
        (
            row for row in manifest.get("scrapers") or []
            if isinstance(row, dict) and norm_id(row.get("id")) == provider_id
        ),
        None,
    )
    if not isinstance(entry, dict):
        raise ValueError(f"{provider_id}: missing manifest row during route refresh")

    hubs = load_json(HUBS, {})
    hub_row = (hubs.get("providers") or {}).get(provider_id)
    if not isinstance(hub_row, dict):
        hub_row = {}
    overrides = load_json(OVERRIDES, {})
    patch = (overrides.get("provider_patches") or {}).get(provider_id)
    capability = (overrides.get("provider_capabilities") or {}).get(provider_id)
    patch = patch if isinstance(patch, dict) else {}
    capability = capability if isinstance(capability, dict) else {}

    direct = str(hub_row.get("direct") or patch.get("official_site") or current.get("direct") or "").strip()
    hub = str(hub_row.get("hub") or patch.get("official_hub") or current.get("hub") or "").strip()
    telegram = str(hub_row.get("telegram") or current.get("telegram") or "").strip()
    api = str(hub_row.get("api") or current.get("api") or "").strip()
    origins = [
        str(value).strip()
        for value in capability.get("observed_origins") or []
        if str(value).strip()
    ]
    for value in (direct, hub, telegram, api):
        if not value:
            continue
        try:
            origin = f"{urlsplit(value).scheme}://{urlsplit(value).netloc}"
        except ValueError:
            continue
        if origin and origin not in origins:
            origins.append(origin)

    model = {
        "strategy": str(current.get("strategy") or patch.get("capability") or "html_scraper"),
        "knownSite": direct or hub or telegram or None,
        "officialSite": direct or None,
        "officialHub": hub or telegram or None,
        "officialApi": api or None,
        "origins": origins,
        "observedUrls": [value for value in (api, direct) if value],
        "routes": parse_list(current.get("routes")),
    }
    base_relative, base_sha, _stripped = base_store.persist_clean_provider_seed(
        provider_id,
        entry,
        known_site=direct or hub or telegram or None,
        provider_model=model,
        overrides_path=OVERRIDES,
    )
    base_path = ROOT / base_relative
    published_relative = f"providers/{provider_id}--nuvio--{base_sha[:16]}.js"
    published_path = ROOT / published_relative
    published_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(base_path, published_path)
    entry["filename"] = published_relative
    write_json(MANIFEST, manifest)

    provenance = load_json(PROVENANCE, {})
    row = (provenance.get("providers") or {}).get(provider_id)
    if not isinstance(row, dict):
        raise ValueError(f"{provider_id}: missing provenance during route refresh")
    row["published_filename"] = published_relative
    row["sha256"] = base_sha
    row["patched_sha256"] = base_sha
    row["base_filename"] = base_relative
    row["base_sha256"] = base_sha
    row["base_source"] = base_store.CLEAN_RECONSTRUCTION_SOURCE
    row["clean_reconstruction_required"] = False
    row["clean_reconstruction_verified"] = True
    row["clean_reconstruction_authoring_version"] = base_store.CLEAN_RECONSTRUCTION_AUTHORING_VERSION
    row["clean_reconstruction_verified_at"] = iso_now()
    row["onboarding_route_refresh"] = {
        "direct": direct or None,
        "hub": hub or None,
        "telegram": telegram or None,
        "api": api or None,
    }
    write_json(PROVENANCE, provenance)
    base_store.repair_legacy_bases()

    current["direct"] = direct
    current["hub"] = hub
    current["telegram"] = telegram
    current["api"] = api
    current["site"] = direct or hub or telegram
    write_json(WORK / "current.json", current)
    print(
        "FIELD_PROVIDER_ONBOARDING_REFRESH "
        f"id={provider_id} direct={bool(direct)} hub={bool(hub)} telegram={bool(telegram)} "
        f"base={base_relative}"
    )
    return current



def finalize(provider_id: str, report_path: Path) -> bool:
    provider_id = norm_id(provider_id)
    report = load_json(report_path, {})
    provider = next(
        (
            row for row in report.get("providers") or []
            if isinstance(row, dict) and norm_id(row.get("id")) == provider_id
        ),
        None,
    )
    clients = provider.get("clients") if isinstance(provider, dict) and isinstance(provider.get("clients"), dict) else {}
    requested = [str(value) for value in report.get("clients") or ["tv", "desktop", "mobile"]]
    all_playable = bool(requested) and all(
        str((clients.get(client) or {}).get("verdict") or "") == "playable"
        and int((clients.get(client) or {}).get("identity_contradiction_count") or 0) == 0
        for client in requested
    )
    safety_pass = bool((report.get("policy") or {}).get("safety_blocking_pass", True))
    active = all_playable and safety_pass

    manifest = load_json(MANIFEST, {})
    row = next(
        (
            item for item in manifest.get("scrapers") or []
            if isinstance(item, dict) and norm_id(item.get("id")) == provider_id
        ),
        None,
    )
    if not isinstance(row, dict):
        raise ValueError(f"{provider_id}: missing staged manifest row during finalize")
    row["enabled"] = active
    write_json(MANIFEST, manifest)

    overrides = load_json(OVERRIDES, {})
    patch = (overrides.get("provider_patches") or {}).get(provider_id)
    if not isinstance(patch, dict):
        raise ValueError(f"{provider_id}: missing provider override row during finalize")
    patch.setdefault("manifest_overrides", {})["enabled"] = active
    capability = (overrides.get("provider_capabilities") or {}).get(provider_id)
    if isinstance(capability, dict):
        capability["validation"] = "onboarding_quick_pass" if active else "onboarding_pending_learning"
    write_json(OVERRIDES, overrides)

    provenance = load_json(PROVENANCE, {})
    prov = (provenance.get("providers") or {}).get(provider_id)
    if not isinstance(prov, dict):
        raise ValueError(f"{provider_id}: missing provenance during finalize")
    prov["checked_at"] = iso_now()
    prov["check_mode"] = "onboarding_quick"
    prov["check_status"] = "healthy" if active else "pending_learning"
    prov["activation_eligible"] = active
    prov["strict_activation_eligible"] = active
    prov["runtime_evidence_eligible"] = active
    prov["activation_mode"] = "onboarding_quick_pass" if active else "onboarding_pending_learning"
    prov["activation_blockers"] = [] if active else ["onboarding_quick_lab_not_fully_playable"]
    prov["onboarding_quick_lab"] = {
        "requested_clients": requested,
        "all_playable": all_playable,
        "safety_pass": safety_pass,
        "client_verdicts": {
            client: str((clients.get(client) or {}).get("verdict") or "no_report")
            for client in requested
        },
    }
    write_json(PROVENANCE, provenance)

    print(
        "FIELD_PROVIDER_ONBOARDING_FINAL "
        f"id={provider_id} active={str(active).lower()} "
        f"safety={str(safety_pass).lower()} "
        f"clients={','.join(requested)}"
    )
    return active


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    stage_parser = sub.add_parser("stage")
    stage_parser.add_argument("--request", type=Path, required=True)

    refresh_parser = sub.add_parser("refresh")
    refresh_parser.add_argument("--provider", required=True)

    finalize_parser = sub.add_parser("finalize")
    finalize_parser.add_argument("--provider", required=True)
    finalize_parser.add_argument("--report", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "stage":
        stage(args.request.resolve())
        return 0
    if args.command == "refresh":
        refresh(args.provider)
        return 0
    finalize(args.provider, args.report.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
