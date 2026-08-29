#!/usr/bin/env python3
"""Register and finalize one NiakVIO-owned provider from structured intake data.

This onboarding path never copies or executes third-party provider JavaScript.
It stores address knowledge, authors a clean ProviderBase through the canonical
NiakVIO generator, lets the normal Core derive the public bundle, and activates
the provider only after targeted current runtime proof.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import ipaddress
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from provider_base_store import (
    CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
    CLEAN_RECONSTRUCTION_SOURCE,
    is_clean_reconstructed,
    persist_clean_provider_seed,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CATALOG = ROOT / "provider_catalog.json"
OVERRIDES = ROOT / "provider-overrides.json"
HUBS = ROOT / "provider-hubs.json"
TYPE_POLICY = ROOT / "provider-type-policy.json"
PROVENANCE = ROOT / "PROVENANCE.json"
ONBOARDING_DIR = ROOT / "provider-onboarding"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def canonical(value: Any) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", str(value or "").strip().casefold()).strip(".-")


def list_values(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    elif value is None:
        raw = []
    else:
        raw = re.split(r"[,\n]+", str(value))
    return list(dict.fromkeys(str(item).strip() for item in raw if str(item).strip()))


def public_url(value: Any, *, optional: bool = True) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        if optional:
            return None
        raise ValueError("missing required URL")
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"unsupported URL: {raw}")
    hostname = parsed.hostname.casefold().strip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise ValueError(f"private hostname forbidden: {hostname}")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private or address.is_loopback or address.is_link_local
        or address.is_reserved or address.is_multicast
    ):
        raise ValueError(f"private address forbidden: {hostname}")
    return raw.rstrip("/") + ("/" if parsed.path in {"", "/"} else "")


def normalize_intake(raw: dict[str, Any]) -> dict[str, Any]:
    provider_id = canonical(raw.get("id") or raw.get("provider_id"))
    if not provider_id:
        raise ValueError("provider id is required")
    types = [
        item.casefold() for item in list_values(raw.get("supportedTypes") or raw.get("types"))
        if item.casefold() in {"movie", "tv", "anime"}
    ]
    if not types:
        types = ["movie", "tv", "anime"]
    languages = [item.casefold() for item in list_values(raw.get("contentLanguage") or raw.get("language"))]
    hub = public_url(raw.get("hub"))
    direct = public_url(raw.get("direct"))
    telegram = public_url(raw.get("telegram"))
    api = public_url(raw.get("api") or raw.get("api_url"))
    if not any((hub, direct, telegram, api)):
        raise ValueError("at least one hub/direct/telegram/api URL is required")
    aliases = list_values(raw.get("aliases")) or [provider_id]
    search_queries = list_values(raw.get("search_queries") or raw.get("search"))
    terminal_hosts = list_values(raw.get("allowed_terminal_hosts") or raw.get("terminal_hosts"))
    for url in (direct, api):
        if url:
            host = (urlparse(url).hostname or "").casefold()
            if host and host not in terminal_hosts:
                terminal_hosts.append(host)
    source_rows = [copy.deepcopy(row) for row in raw.get("sources") or [] if isinstance(row, dict)]
    return {
        "id": provider_id,
        "name": str(raw.get("name") or provider_id).strip(),
        "description": str(raw.get("description") or f"Provider {provider_id} géré par NiakVIO.").strip(),
        "category": str(raw.get("category") or "International").strip(),
        "hub": hub,
        "direct": direct,
        "telegram": telegram,
        "api": api,
        "aliases": aliases,
        "search_queries": search_queries,
        "allowed_terminal_hosts": terminal_hosts,
        "official_link_labels": list_values(raw.get("official_link_labels") or raw.get("link_labels")),
        "supportedTypes": list(dict.fromkeys(types)),
        "contentLanguage": list(dict.fromkeys(languages)),
        "formats": list_values(raw.get("formats")),
        "strategy": str(raw.get("strategy") or "html_scraper").strip().casefold(),
        "supportsExternalPlayer": bool(raw.get("supportsExternalPlayer", True)),
        "enableRequested": bool(raw.get("enableRequested", raw.get("enabled", True))),
        "projectionGeneral": bool(raw.get("projectionGeneral", True)),
        "projectionVF": bool(raw.get("projectionVF", any(x.startswith("fr") for x in languages))),
        "logo": public_url(raw.get("logo")),
        "routes": list_values(raw.get("routes")),
        "sources": source_rows,
    }


def upsert_hub_registry(data: dict[str, Any], intake: dict[str, Any]) -> None:
    providers = data.setdefault("providers", {})
    if not isinstance(providers, dict):
        raise ValueError("provider-hubs.providers must be an object")
    pid = intake["id"]
    sources: list[dict[str, Any]] = []
    if intake["hub"]:
        sources.append({"type": "hub", "url": intake["hub"], "priority": 110, "purpose": "Authoritative address hub"})
    if intake["telegram"]:
        sources.append({"type": "telegram_public", "url": intake["telegram"], "priority": 105, "purpose": "Public official address channel"})
    if intake["api"]:
        sources.append({"type": "direct", "url": intake["api"], "priority": 80, "purpose": "Known official API"})
    sources.extend(intake["sources"])
    for query in intake["search_queries"]:
        sources.append({"type": "search", "query": query, "priority": 35, "purpose": "Fallback public discovery"})
    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in sources:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("type") or "hub")
        identity = str(row.get("url") or row.get("query") or "").strip()
        if identity:
            dedup[(kind, identity)] = row
    labels = intake["official_link_labels"] or ["Entrer", "Accéder", "site officiel", "adresse officielle", "ouvrir"]
    providers[pid] = {
        "id": pid,
        "name": intake["name"],
        "manifest_status": "Actif",
        "category": intake["category"],
        "hub": intake["hub"],
        "direct": intake["direct"],
        "source": "niakvio_structured_onboarding",
        "resolver": "official_outbound",
        "aliases": intake["aliases"],
        "schema_notes": "Structured onboarding; hub/Telegram/search are discovery sources and only a runtime-validated terminal route may be persisted.",
        "direct_candidates": [intake["direct"]] if intake["direct"] else [],
        "allowed_terminal_hosts": intake["allowed_terminal_hosts"],
        "search_queries": intake["search_queries"],
        "sources": list(dedup.values()),
        "official_link_labels": labels,
        "search_confirmation_runs": 2,
        "require_api_validation": False,
        "persist_official_site_without_api": True,
    }


def upsert_overrides(data: dict[str, Any], intake: dict[str, Any]) -> None:
    pid = intake["id"]
    patches = data.setdefault("provider_patches", {})
    capabilities = data.setdefault("provider_capabilities", {})
    if not isinstance(patches, dict) or not isinstance(capabilities, dict):
        raise ValueError("provider override maps must be objects")
    existing = patches.get(pid) if isinstance(patches.get(pid), dict) else {}
    patch = copy.deepcopy(existing)
    patch.update({
        "notes": [
            "Created from structured NiakVIO onboarding; no third-party provider JavaScript is copied or executed.",
            "Address discovery follows hub/direct/Telegram/search trust order and persists only runtime-validated terminal routes.",
        ],
        "capability": intake["strategy"],
        "official_hub": intake["hub"],
        "official_site": intake["direct"] or patch.get("official_site"),
        "official_api": intake["api"] or patch.get("official_api"),
        "published_types": intake["supportedTypes"],
    })
    patch.setdefault("replacements", {})
    patch.setdefault("required_values", [])
    patch.setdefault("route_replacements", {})
    patch.setdefault("required_route_values", [])
    patch.setdefault("profiles", [])
    patch.setdefault("runtime_domain_replacements", {})
    patch.setdefault("patch_scripts", [])
    manifest_overrides = patch.setdefault("manifest_overrides", {})
    if not isinstance(manifest_overrides, dict):
        manifest_overrides = {}
        patch["manifest_overrides"] = manifest_overrides
    manifest_overrides.setdefault("disabledPlatforms", [])
    if intake["logo"]:
        manifest_overrides["logo"] = intake["logo"]
    patches[pid] = patch
    capabilities[pid] = {
        "strategy": intake["strategy"],
        "validation": "provider_native_and_final_output",
        "allow_html_url": intake["strategy"] in {"html_scraper", "iframe_player", "mixed_embed_resolver"},
        "requires_direct_media": intake["strategy"] in {"direct_media", "api_stream_resolver"},
        "observed_origins": list(dict.fromkeys(
            [value.rstrip("/") for value in (intake["direct"], intake["api"]) if value]
        )),
        "generated_from_structured_onboarding": True,
        "catalogue_types": intake["supportedTypes"],
        "identity_request_source": "original_nuvio_request",
    }


def manifest_row(intake: dict[str, Any], filename: str, *, enabled: bool) -> dict[str, Any]:
    row = {
        "id": intake["id"],
        "name": intake["name"],
        "description": intake["description"],
        "version": "1.0.0",
        "author": "NiakVIO",
        "supportedTypes": intake["supportedTypes"],
        "filename": filename,
        "enabled": bool(enabled),
        "contentLanguage": intake["contentLanguage"],
        "formats": intake["formats"],
        "limited": False,
        "disabledPlatforms": [],
        "supportsExternalPlayer": intake["supportsExternalPlayer"],
    }
    if intake["logo"]:
        row["logo"] = intake["logo"]
    return row


def upsert_manifest(manifest: dict[str, Any], row: dict[str, Any]) -> None:
    rows = manifest.setdefault("scrapers", [])
    pid = canonical(row["id"])
    for index, existing in enumerate(rows):
        if isinstance(existing, dict) and canonical(existing.get("id")) == pid:
            old_version = existing.get("version")
            rows[index] = {**existing, **row}
            if old_version:
                rows[index]["version"] = old_version
            return
    rows.append(row)


def upsert_catalog(catalog: dict[str, Any], intake: dict[str, Any], row: dict[str, Any]) -> None:
    providers = catalog.setdefault("providers", [])
    cid = intake["id"]
    projected = {
        "general": intake["projectionGeneral"],
        "vf": intake["projectionVF"],
    }
    replacement = {"canonicalId": cid, "scraper": copy.deepcopy(row), "projections": projected}
    for index, existing in enumerate(providers):
        if isinstance(existing, dict) and canonical(existing.get("canonicalId")) == cid:
            providers[index] = replacement
            break
    else:
        providers.append(replacement)
    order = catalog.setdefault("manifestOrder", {})
    for key, enabled in projected.items():
        values = [canonical(value) for value in order.get(key) or [] if canonical(value)]
        values = [value for value in values if value != cid]
        if enabled:
            values.append(cid)
        order[key] = values


def refresh_store(provenance: dict[str, Any], manifest: dict[str, Any]) -> None:
    rows = provenance.setdefault("providers", {})
    ids = [canonical(row.get("id")) for row in manifest.get("scrapers") or [] if isinstance(row, dict) and canonical(row.get("id"))]
    clean = sum(1 for pid in ids if is_clean_reconstructed(rows.get(pid)))
    bases = {
        str(rows.get(pid, {}).get("base_filename") or "")
        for pid in ids if isinstance(rows.get(pid), dict) and rows.get(pid, {}).get("base_filename")
    }
    store = provenance.setdefault("provider_base_store", {})
    store["provider_count"] = len(ids)
    store["unique_base_count"] = len(bases)
    store["clean_reconstructed"] = clean
    store["reconstruction_required"] = len(ids) - clean
    store.setdefault("initial_reconstruction_scope", max(0, len(ids) - clean))
    store["future_source"] = "provider_pipeline_only"
    store["core_may_create_or_mutate_base"] = False


def register(intake: dict[str, Any]) -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    catalog = load_json(CATALOG)
    overrides = load_json(OVERRIDES)
    hubs = load_json(HUBS)
    type_policy = load_json(TYPE_POLICY)
    provenance = load_json(PROVENANCE)
    pid = intake["id"]

    upsert_hub_registry(hubs, intake)
    upsert_overrides(overrides, intake)
    type_policy.setdefault("providers", {})[pid] = {
        "supportedTypes": intake["supportedTypes"],
        "description": intake["description"],
    }
    write_json(HUBS, hubs)
    write_json(OVERRIDES, overrides)
    write_json(TYPE_POLICY, type_policy)

    patch = (overrides.get("provider_patches") or {}).get(pid) or {}
    known_site = str(patch.get("official_site") or intake["direct"] or intake["hub"] or "").strip() or None
    model = {
        "knownSite": known_site,
        "officialSite": patch.get("official_site") or intake["direct"],
        "officialHub": patch.get("official_hub") or intake["hub"],
        "officialApi": patch.get("official_api") or intake["api"],
        "strategy": intake["strategy"],
        "origins": [value for value in (patch.get("official_site"), intake["direct"]) if value],
        "observedUrls": [value for value in (patch.get("official_api"), intake["api"]) if value],
        "routes": intake["routes"],
    }
    seed_entry = {
        "id": pid,
        "name": intake["name"],
        "supportedTypes": intake["supportedTypes"],
    }
    base_relative, base_sha, _stripped = persist_clean_provider_seed(
        pid,
        seed_entry,
        known_site=known_site,
        provider_model=model,
        overrides_path=OVERRIDES,
    )
    base_path = ROOT / base_relative
    provisional_relative = f"providers/{pid}--niakvio-clean--{base_sha[:16]}.js"
    provisional_path = ROOT / provisional_relative
    provisional_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base_path, provisional_path)
    public_sha = hashlib.sha256(provisional_path.read_bytes()).hexdigest()

    existing_manifest = next(
        (row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and canonical(row.get("id")) == pid),
        None,
    )
    row = manifest_row(
        intake,
        provisional_relative,
        enabled=bool(existing_manifest and existing_manifest.get("enabled") is True),
    )
    upsert_manifest(manifest, row)

    providers = provenance.setdefault("providers", {})
    existing_provenance = providers.get(pid) if isinstance(providers.get(pid), dict) else {}
    provider_row = copy.deepcopy(existing_provenance)
    provider_row.update({
        "id": pid,
        "published_filename": provisional_relative,
        "sha256": public_sha,
        "patched_sha256": public_sha,
        "source": "niakvio-clean-onboarding",
        "source_name": "NiakVIO structured Add Provider workflow",
        "source_repository": "NiakVIO",
        "source_license": "GPL-3.0-only",
        "source_license_evidence": "LICENSE",
        "upstream_id": pid,
        "upstream_filename": provisional_relative,
        "checked_at": now_iso(),
        "check_mode": "targeted-onboarding",
        "check_status": "pending",
        "health_score": 0,
        "activation_eligible": False,
        "strict_activation_eligible": False,
        "base_filename": base_relative,
        "base_sha256": base_sha,
        "base_source": CLEAN_RECONSTRUCTION_SOURCE,
        "clean_reconstruction_verified": True,
        "clean_reconstruction_required": False,
        "clean_reconstruction_authoring_version": CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        "clean_reconstruction_verified_at": now_iso(),
        "upstream_code_role": "knowledge-only",
        "upstream_code_executed": False,
        "legacy_provider_js_executed_for_reconstruction": False,
    })
    providers[pid] = provider_row
    upsert_catalog(catalog, intake, next(row for row in manifest["scrapers"] if canonical(row.get("id")) == pid))
    refresh_store(provenance, manifest)
    write_json(MANIFEST, manifest)
    write_json(CATALOG, catalog)
    write_json(PROVENANCE, provenance)
    return {"provider": pid, "base": base_relative, "provisional": provisional_relative}


def sync_from_manifest(intake: dict[str, Any]) -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    catalog = load_json(CATALOG)
    provenance = load_json(PROVENANCE)
    pid = intake["id"]
    row = next((row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and canonical(row.get("id")) == pid), None)
    if row is None:
        raise ValueError(f"{pid}: manifest row missing")
    upsert_catalog(catalog, intake, row)
    refresh_store(provenance, manifest)
    write_json(CATALOG, catalog)
    write_json(PROVENANCE, provenance)
    return {"provider": pid, "filename": row.get("filename"), "enabled": bool(row.get("enabled"))}


def health_result(report: dict[str, Any], pid: str) -> dict[str, Any] | None:
    for row in report.get("results") or []:
        if isinstance(row, dict) and canonical(row.get("canonical_id") or row.get("upstream_id")) == pid:
            return row
    return None


def finalize(intake: dict[str, Any], health_path: Path) -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    catalog = load_json(CATALOG)
    provenance = load_json(PROVENANCE)
    report = load_json(health_path)
    pid = intake["id"]
    result = health_result(report, pid)
    if result is None:
        raise ValueError(f"{pid}: targeted health result missing")
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    playable = int(evidence.get("streams_playable") or 0)
    contradictions = int(evidence.get("identity_contradiction_count") or 0)
    disallowed = int(evidence.get("disallowed_streams") or 0)
    healthy = (
        str(result.get("status") or "") == "healthy"
        and playable > 0
        and contradictions == 0
        and disallowed == 0
    )
    enabled = bool(intake["enableRequested"] and healthy)

    row = next((row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and canonical(row.get("id")) == pid), None)
    if row is None:
        raise ValueError(f"{pid}: manifest row missing")
    row["enabled"] = enabled

    providers = provenance.setdefault("providers", {})
    prow = providers.get(pid)
    if not isinstance(prow, dict):
        raise ValueError(f"{pid}: provenance row missing")
    prow["checked_at"] = now_iso()
    prow["check_mode"] = "targeted-onboarding"
    prow["check_status"] = str(result.get("status") or "unknown")
    prow["health_score"] = int(result.get("score") or 0)
    prow["activation_eligible"] = healthy
    prow["strict_activation_eligible"] = healthy
    prow["activation_mode"] = "targeted_onboarding_proof" if enabled else "onboarding_disabled_pending_learning"
    prow["activation_blockers"] = [] if enabled else ["targeted_onboarding_current_playable_proof"]
    prow["onboarding_evidence"] = {
        "status": result.get("status"),
        "playable_streams": playable,
        "identity_contradictions": contradictions,
        "disallowed_streams": disallowed,
    }

    upsert_catalog(catalog, intake, row)
    refresh_store(provenance, manifest)
    write_json(MANIFEST, manifest)
    write_json(CATALOG, catalog)
    write_json(PROVENANCE, provenance)

    summary = {
        "schemaVersion": 1,
        "provider": pid,
        "generatedAt": now_iso(),
        "requestedActivation": intake["enableRequested"],
        "healthy": healthy,
        "enabled": enabled,
        "status": result.get("status"),
        "score": int(result.get("score") or 0),
        "playableStreams": playable,
        "identityContradictions": contradictions,
        "disallowedStreams": disallowed,
        "policy": {
            "thirdPartyProviderCodeExecuted": False,
            "cleanProviderBaseRequired": True,
            "activationRequiresCurrentTargetedProof": True,
            "fullNativeLabsRequiredForOnboarding": False,
            "weeklyFullNativeLabsRemainIndependent": True,
        },
    }
    write_json(ONBOARDING_DIR / f"{pid}.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--phase", choices=("register", "sync", "finalize"), required=True)
    parser.add_argument("--health", type=Path)
    args = parser.parse_args()
    intake = normalize_intake(load_json(args.input.resolve()))
    if args.phase == "register":
        result = register(intake)
    elif args.phase == "sync":
        result = sync_from_manifest(intake)
    else:
        if args.health is None:
            raise SystemExit("--health is required for finalize")
        result = finalize(intake, args.health.resolve())
    print("FIELD_ADD_PROVIDER " + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
