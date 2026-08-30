#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage every non-P2P provider declared by configured upstream manifests.

Upstream JavaScript is knowledge input only: it may reveal metadata, routes,
domains and exclusion signals, but it is never executed, patched into a runtime
candidate, persisted as ProviderBase, or published. Executable candidates are
always built from an existing NiakVIO ProviderBase or a fresh NiakVIO-owned
clean seed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides
from provider_base_store import build_clean_provider_seed, is_clean_reconstruction_candidate, requires_clean_reconstruction, resolve_base
from upstream_lkg import (
    create_pending, load_manifest_snapshot, load_provider_snapshot, load_registry,
    record_pending_source, validate_manifest_quality, write_pending,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "sources.json"
DEFAULT_STAGE = ROOT / "staging"
LKG_PATH = ROOT / "provider-lkg.json"
PROVENANCE_PATH = ROOT / "PROVENANCE.json"
OVERRIDES_PATH = ROOT / "provider-overrides.json"
USER_AGENT = "Nuvio-Curated-Discovery/5.13 (+GitHub Actions)"
URL_RE = re.compile(r"https?://[^\\s\"'\`<>\\)]+", re.I)
INFRASTRUCTURE_HOSTS = {
    "api.themoviedb.org", "image.tmdb.org", "api.jikan.moe",
    "graphql.anilist.co", "api.tvmaze.com", "api.github.com",
    "raw.githubusercontent.com", "github.com",
}


def fetch_bytes(url: str, attempts: int = 3, timeout: int = 35) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,application/javascript,*/*",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
            if not data:
                raise RuntimeError("empty response")
            return data
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise RuntimeError(f"download failed for {url}: {last_error}")


def fetch_manifest(urls: list[str]) -> tuple[dict[str, Any], str]:
    errors: list[str] = []
    for url in urls:
        try:
            payload = json.loads(fetch_bytes(url).decode("utf-8-sig"))
            if not isinstance(payload, dict) or not isinstance(payload.get("scrapers"), list):
                raise ValueError("missing scrapers array")
            return payload, url
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("; ".join(errors))


def safe_fragment(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip(".-")
    return cleaned[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def validate_javascript(data: bytes, url: str) -> None:
    if len(data) < 100:
        raise ValueError(f"JavaScript file is too small ({len(data)} bytes): {url}")
    head = data[:500].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        raise ValueError(f"HTML received instead of JavaScript: {url}")


def exclusion_reason(entry: dict[str, Any], data: bytes | None, exclusions: dict[str, Any]) -> str | None:
    provider_id = canonical_id(str(entry.get("id") or entry.get("name") or ""))
    explicit_ids = {canonical_id(str(value)) for value in exclusions.get("provider_ids", [])}
    if provider_id in explicit_ids:
        return "explicitly excluded P2P/torrent provider id"

    metadata_text = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    for pattern in exclusions.get("metadata_patterns", []):
        if str(pattern).casefold() in metadata_text:
            return f"metadata contains excluded P2P/torrent marker: {pattern}"

    if data is not None:
        script_text = data[:2_000_000].decode("utf-8", errors="ignore").casefold()
        for pattern in exclusions.get("script_patterns", []):
            if str(pattern).casefold() in script_text:
                return f"script contains excluded P2P/torrent marker: {pattern}"
    return None


def observed_site_from_upstream(data: bytes, provider_id: str) -> str | None:
    """Extract a provider-looking site hint without importing upstream code."""
    text = data[:2_000_000].decode("utf-8", errors="ignore")
    token = re.sub(r"[^a-z0-9]", "", provider_id.casefold())
    candidates: list[tuple[int, str]] = []
    for raw in URL_RE.findall(text):
        raw = raw.rstrip(".,;")
        try:
            parsed = urllib.parse.urlparse(raw)
        except ValueError:
            continue
        host = (parsed.hostname or "").casefold()
        if not host or host in INFRASTRUCTURE_HOSTS:
            continue
        normalized = re.sub(r"[^a-z0-9]", "", host)
        score = 2 if token and len(token) >= 4 and token in normalized else 1
        origin = f"{parsed.scheme}://{host}"
        candidates.append((score, origin))
    if not candidates:
        return None
    candidates.sort(key=lambda row: (-row[0], row[1]))
    return candidates[0][1]


def known_site_for_provider(
    provider_id: str,
    raw_upstream: bytes,
    overrides: dict[str, Any],
) -> str | None:
    patch = (overrides.get("provider_patches") or {}).get(provider_id, {})
    if isinstance(patch, dict):
        for key in ("official_site", "official_api", "official_hub"):
            value = str(patch.get(key) or "").strip()
            if value:
                return value
    return observed_site_from_upstream(raw_upstream, provider_id)


def upstream_knowledge(provider_id: str, entry: dict[str, Any], raw_upstream: bytes) -> dict[str, Any]:
    """Extract bounded route knowledge without importing or executing upstream code."""
    text = raw_upstream[:2_000_000].decode("utf-8", errors="ignore")
    urls: list[str] = []
    hosts: list[str] = []
    routes: list[str] = []
    for raw in URL_RE.findall(text):
        raw = raw.rstrip(".,;")
        try:
            parsed = urllib.parse.urlparse(raw)
        except ValueError:
            continue
        host = (parsed.hostname or "").casefold()
        if not host or host in INFRASTRUCTURE_HOSTS:
            continue
        safe_url = urllib.parse.urlunparse((
            parsed.scheme if parsed.scheme in {"http", "https"} else "https",
            host,
            parsed.path or "/",
            "",
            "",
            "",
        ))
        if safe_url not in urls:
            urls.append(safe_url)
        if host not in hosts:
            hosts.append(host)
        route = parsed.path or "/"
        if route not in routes:
            routes.append(route)
        if len(urls) >= 32:
            break
    supported = entry.get("supportedTypes") if isinstance(entry, dict) else []
    if isinstance(supported, str):
        supported = [supported]
    return {
        "providerId": provider_id,
        "supportedTypes": [str(value) for value in supported or []][:8],
        "hosts": hosts[:24],
        "routes": routes[:32],
        "observedUrls": urls[:32],
        "codeRole": "knowledge-only",
        "codeExecuted": False,
    }


def clean_provider_model(
    provider_id: str,
    knowledge: dict[str, Any],
    overrides: dict[str, Any],
    known_site: str | None,
) -> dict[str, Any]:
    """Translate observed facts/configuration into a bounded NiakVIO provider model."""
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    capabilities = overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"), dict) else {}
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    capability = capabilities.get(provider_id) if isinstance(capabilities.get(provider_id), dict) else {}
    fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}

    learned_routes: list[str] = []
    for source in (
        patch.get("learned_routes"),
        capability.get("routes"),
        knowledge.get("routes"),
    ):
        for raw in source if isinstance(source, list) else []:
            value = str(raw or "").strip()
            if value and value not in learned_routes:
                learned_routes.append(value)

    learned_urls: list[str] = []
    for source in (
        patch.get("learned_urls"),
        capability.get("observed_urls"),
        knowledge.get("observedUrls"),
    ):
        for raw in source if isinstance(source, list) else []:
            value = str(raw or "").strip()
            if value and value not in learned_urls:
                learned_urls.append(value)

    origins: list[str] = []
    for value in capability.get("observed_origins") or []:
        value = str(value or "").strip()
        if value and value not in origins:
            origins.append(value)
    for host in knowledge.get("hosts") or []:
        value = str(host or "").strip()
        if value:
            origin = "https://" + value
            if origin not in origins:
                origins.append(origin)
    for mapping_key in ("runtime_domain_replacements", "route_replacements", "replacements"):
        mapping = patch.get(mapping_key) if isinstance(patch.get(mapping_key), dict) else {}
        for raw in mapping.values():
            value = str(raw or "").strip()
            if not value:
                continue
            if not value.startswith(("http://", "https://")):
                value = "https://" + value.lstrip("/")
            try:
                parsed = urllib.parse.urlparse(value)
                origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
            except ValueError:
                origin = ""
            if origin and origin not in origins:
                origins.append(origin)

    return {
        "knownSite": str(known_site or "").strip() or None,
        "strategy": str(
            patch.get("capability")
            or capability.get("strategy")
            or "unknown"
        ).strip().casefold(),
        "officialSite": str(patch.get("official_site") or "").strip() or None,
        "officialHub": str(patch.get("official_hub") or "").strip() or None,
        "officialApi": str(patch.get("official_api") or "").strip() or None,
        "fixedApi": str(fixed.get("api") or "").strip() or None,
        "origins": origins[:24],
        "observedUrls": learned_urls[:32],
        "routes": learned_routes[:32],
        "knowledgeRole": "structured-observation-only",
        "legacyCodeEmbedded": False,
        "legacyCodeExecuted": False,
    }


def executable_seed(
    provider_id: str,
    entry: dict[str, Any],
    raw_upstream: bytes,
    provenance_rows: dict[str, Any],
    overrides: dict[str, Any],
    *,
    clean_reconstruction: bool,
) -> tuple[bytes, str, str | None, bool, dict[str, Any], dict[str, Any]]:
    previous = provenance_rows.get(provider_id)
    previous_row = previous if isinstance(previous, dict) else {}
    site = known_site_for_provider(provider_id, raw_upstream, overrides)
    knowledge = upstream_knowledge(provider_id, entry, raw_upstream)
    provider_model = clean_provider_model(provider_id, knowledge, overrides, site)
    reconstruction_required = requires_clean_reconstruction(previous_row)

    pending_clean = is_clean_reconstruction_candidate(previous_row)

    if pending_clean:
        path, _digest = resolve_base(provider_id, previous_row, require=True)
        assert path is not None
        return (
            path.read_bytes(),
            "pending-niakvio-clean-reconstruction-v2",
            site,
            True,
            knowledge,
            provider_model,
        )

    if reconstruction_required and clean_reconstruction:
        return (
            build_clean_provider_seed(
                provider_id,
                entry,
                known_site=site,
                provider_model=provider_model,
            ),
            "new-niakvio-clean-seed",
            site,
            True,
            knowledge,
            provider_model,
        )

    if isinstance(previous, dict):
        path, _digest = resolve_base(provider_id, previous, require=False)
        if path is not None:
            return (
                path.read_bytes(),
                (
                    "legacy-providerbase-compatibility-only"
                    if reconstruction_required
                    else "existing-niakvio-provider-base-v2"
                ),
                site,
                reconstruction_required,
                knowledge,
                provider_model,
            )

    return (
        build_clean_provider_seed(
            provider_id,
            entry,
            known_site=site,
            provider_model=provider_model,
        ),
        "new-niakvio-clean-seed",
        site,
        True,
        knowledge,
        provider_model,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument(
        "--require-all-upstreams",
        action="store_true",
        help="Fail if any upstream manifest cannot be loaded.",
    )
    parser.add_argument(
        "--clean-reconstruction",
        action="store_true",
        help="Build reconstruction-required providers from a fresh NiakVIO seed instead of compatibility LKG bytes.",
    )
    args = parser.parse_args()

    config = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    exclusions = config.get("exclusions", {})
    overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    try:
        provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        provenance = {"providers": {}}
    provenance_rows = provenance.get("providers") if isinstance(provenance, dict) else {}
    if not isinstance(provenance_rows, dict):
        provenance_rows = {}
    stage = args.stage.resolve()
    if stage.exists():
        shutil.rmtree(stage)
    providers_dir = stage / "providers"
    manifests_dir = stage / "manifests"
    providers_dir.mkdir(parents=True)
    manifests_dir.mkdir(parents=True)

    candidates: list[dict[str, Any]] = []
    seen_canonical_ids: dict[str, dict[str, str]] = {}
    duplicate_inputs: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    upstream_reports: dict[str, Any] = {}
    errors: list[str] = []

    upstream_lkg_registry = load_registry(ROOT)
    upstream_lkg_pending = create_pending(stage)

    for priority, (source_key, source_cfg) in enumerate(config["upstreams"].items()):
        manifest_origin = "live"
        live_manifest = False
        raw_provider_records: dict[str, tuple[bytes, str]] = {}
        try:
            manifest, manifest_url = fetch_manifest(source_cfg["manifest_urls"])
            validate_manifest_quality(manifest, source_key, upstream_lkg_registry)
            live_manifest = True
        except Exception as live_exc:
            snapshot = load_manifest_snapshot(upstream_lkg_registry, source_key, ROOT)
            if snapshot is None:
                message = f"{source_key}: live manifest unavailable/corrupt and no upstream LKG snapshot: {live_exc}"
                errors.append(message)
                upstream_reports[source_key] = {
                    "status": "published_fallback_only",
                    "error": str(live_exc),
                    "fallback": "current published provider bundles",
                }
                print(f"[ERROR] {message}", file=sys.stderr)
                continue
            manifest, manifest_url = snapshot
            validate_manifest_quality(manifest, source_key, upstream_lkg_registry)
            manifest_origin = "upstream_lkg"
            print(f"[WARN] {source_key}: using last-known-good upstream snapshot: {live_exc}", file=sys.stderr)

        (manifests_dir / f"{safe_fragment(source_key)}.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        source_count = 0
        source_excluded = 0
        source_failures: list[dict[str, str]] = []
        source_lkg_provider_fallbacks = 0

        for index, entry in enumerate(manifest["scrapers"]):
            if not isinstance(entry, dict):
                continue
            upstream_id = str(entry.get("id") or entry.get("name") or f"entry-{index}")
            provider_id = canonical_id(upstream_id)
            preliminary_reason = exclusion_reason(entry, None, exclusions)
            if preliminary_reason:
                excluded.append({"source": source_key, "id": upstream_id, "reason": preliminary_reason})
                source_excluded += 1
                print(f"[SKIP] {source_key}:{upstream_id}: {preliminary_reason}")
                continue
            if provider_id in seen_canonical_ids:
                existing = seen_canonical_ids[provider_id]
                duplicate_inputs.append({
                    "canonical_id": provider_id,
                    "rejected_source": source_key,
                    "rejected_id": upstream_id,
                    "existing_source": existing["source"],
                    "existing_key": existing["key"],
                })
                source_excluded += 1
                print(
                    f"[DUPLICATE] {source_key}:{upstream_id} rejected; "
                    f"{provider_id} already imported as {existing['key']}"
                )
                continue

            filename = entry.get("filename")
            if not isinstance(filename, str) or not filename.strip():
                source_failures.append({"id": upstream_id, "error": "missing filename"})
                continue

            provider_url = urllib.parse.urljoin(manifest_url, filename)
            local_dir = providers_dir / safe_fragment(source_key)
            local_dir.mkdir(parents=True, exist_ok=True)
            local_name = f"{safe_fragment(upstream_id)}.js"
            local_path = local_dir / local_name

            try:
                data: bytes | None = None
                download_error: Exception | None = None
                if live_manifest:
                    try:
                        data = fetch_bytes(provider_url)
                        validate_javascript(data, provider_url)
                        raw_provider_records[upstream_id] = (data, provider_url)
                    except Exception as exc:
                        download_error = exc
                if data is None:
                    data = load_provider_snapshot(upstream_lkg_registry, source_key, upstream_id, ROOT)
                    if data is not None:
                        source_lkg_provider_fallbacks += 1
                        validate_javascript(data, f"upstream-lkg:{source_key}:{upstream_id}")
                    elif not live_manifest:
                        # A partially populated LKG may still reference a reachable historical URL.
                        try:
                            data = fetch_bytes(provider_url)
                            validate_javascript(data, provider_url)
                        except Exception as exc:
                            download_error = exc
                if data is None:
                    raise RuntimeError(f"live and LKG provider downloads failed: {download_error}")

                reason = exclusion_reason(entry, data, exclusions)
                if reason:
                    excluded.append({"source": source_key, "id": upstream_id, "reason": reason})
                    source_excluded += 1
                    print(f"[SKIP] {source_key}:{upstream_id}: {reason}")
                    continue

                upstream_digest = hashlib.sha256(data).hexdigest()
                (
                    seed,
                    code_origin,
                    observed_site,
                    reconstruction_required,
                    knowledge,
                    provider_model,
                ) = executable_seed(
                    provider_id,
                    entry,
                    data,
                    provenance_rows,
                    overrides,
                    clean_reconstruction=bool(args.clean_reconstruction),
                )
                candidate_data, applied_patches = apply_overrides(provider_id, seed)
                validate_javascript(candidate_data, f"niakvio:{provider_id}")
                local_path.write_bytes(candidate_data)
                subprocess.run([
                    "node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(local_path)
                ], check=True, capture_output=True, text=True)
                digest = hashlib.sha256(candidate_data).hexdigest()
                candidates.append(
                    {
                        "key": f"{source_key}:{upstream_id}",
                        "source": source_key,
                        "source_name": source_cfg.get("name", source_key),
                        "source_priority": priority,
                        "source_repository": source_cfg.get("repository"),
                        "source_license": source_cfg.get("license"),
                        "source_license_evidence": source_cfg.get("license_evidence"),
                        "manifest_url": manifest_url,
                        "manifest_origin": manifest_origin,
                        "upstream_id": upstream_id,
                        "canonical_id": provider_id,
                        "provider_url": provider_url,
                        "observed_upstream_site": observed_site,
                        "local_path": str(local_path.relative_to(stage)),
                        "sha256": digest,
                        "upstream_sha256": upstream_digest,
                        "upstream_code_role": "knowledge-only",
                        "upstream_code_executed": False,
                        "upstream_knowledge": knowledge,
                        "clean_provider_model": provider_model,
                        "candidate_code_origin": code_origin,
                        "provider_base_reconstruction_required": bool(reconstruction_required),
                        "clean_reconstruction_mode": bool(args.clean_reconstruction),
                        "legacy_provider_js_executed_for_reconstruction": False,
                        "local_patches": applied_patches,
                        "bytes": len(candidate_data),
                        "metadata": entry,
                    }
                )
                seen_canonical_ids[provider_id] = {
                    "source": source_key,
                    "key": f"{source_key}:{upstream_id}",
                }
                source_count += 1
                print(f"[OK] {source_key}:{upstream_id} ({manifest_origin})")
            except Exception as exc:
                source_failures.append({"id": upstream_id, "error": str(exc)})
                print(f"[WARN] {source_key}:{upstream_id}: {exc}", file=sys.stderr)

        if live_manifest:
            record_pending_source(
                upstream_lkg_pending, stage, source_key, manifest, manifest_url, raw_provider_records
            )
        upstream_reports[source_key] = {
            "status": "loaded" if live_manifest else "loaded_from_upstream_lkg",
            "manifest_origin": manifest_origin,
            "manifest_url": manifest_url,
            "declared": len(manifest["scrapers"]),
            "downloaded": source_count,
            "excluded": source_excluded,
            "provider_lkg_fallbacks": source_lkg_provider_fallbacks,
            "failures": source_failures,
        }

    write_pending(upstream_lkg_pending, stage)

    # Stage the currently published artifacts as low-priority baseline variants.
    # They are executed by the exact same movie/TV/anime health checks as fresh
    # upstream candidates. When an upstream update regresses to zero streams,
    # the last working local artifact can therefore win promotion instead of
    # being overwritten and pruned before the regression is visible in Nuvio.
    manifest_path = ROOT / "manifest.json"
    try:
        published_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        published_manifest = {"scrapers": []}
    baseline_dir = providers_dir / "published-baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    try:
        lkg_registry = json.loads(LKG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        lkg_registry = {"providers": {}}
    lkg_records = lkg_registry.get("providers", {}) if isinstance(lkg_registry, dict) else {}
    known_keys = {str(item.get("key")) for item in candidates}
    for entry in published_manifest.get("scrapers", []):
        if not isinstance(entry, dict):
            continue
        provider_id = canonical_id(str(entry.get("id") or entry.get("name") or ""))
        filename = entry.get("filename")
        if not provider_id or not isinstance(filename, str):
            continue
        source_path = (ROOT / filename).resolve()
        try:
            source_path.relative_to((ROOT / "providers").resolve())
        except ValueError:
            continue
        if not source_path.is_file() or exclusion_reason(entry, source_path.read_bytes(), exclusions):
            continue
        key = f"published:{provider_id}"
        if provider_id in seen_canonical_ids or key in known_keys:
            continue
        data = source_path.read_bytes()
        validate_javascript(data, filename)
        upstream_digest = hashlib.sha256(data).hexdigest()
        (
            seed,
            code_origin,
            observed_site,
            reconstruction_required,
            knowledge,
            provider_model,
        ) = executable_seed(
            provider_id,
            dict(entry),
            data,
            provenance_rows,
            overrides,
            clean_reconstruction=bool(args.clean_reconstruction),
        )
        candidate_data, applied_patches = apply_overrides(provider_id, seed)
        validate_javascript(candidate_data, f"niakvio:{provider_id}")
        local_path = baseline_dir / f"{safe_fragment(provider_id)}.js"
        local_path.write_bytes(candidate_data)
        subprocess.run([
            "node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(local_path)
        ], check=True, capture_output=True, text=True)
        digest = hashlib.sha256(candidate_data).hexdigest()
        lkg_record = lkg_records.get(provider_id, {}) if isinstance(lkg_records, dict) else {}
        is_registered_lkg = isinstance(lkg_record, dict) and lkg_record.get("sha256") == upstream_digest
        candidates.append({
            "key": key,
            "source": "published-baseline",
            "source_name": "Last published local artifact",
            "source_priority": len(config.get("upstreams", {})) + 100,
            "source_repository": config.get("repository", {}).get("name"),
            "source_license": "GPL-3.0-only",
            "source_license_evidence": "LICENSE",
            "manifest_url": "manifest.json",
            "upstream_id": str(entry.get("id") or provider_id),
            "canonical_id": provider_id,
            "provider_url": filename,
            "observed_upstream_site": observed_site,
            "local_path": str(local_path.relative_to(stage)),
            "sha256": digest,
            "upstream_sha256": upstream_digest,
            "upstream_code_role": "knowledge-only",
            "upstream_code_executed": False,
            "upstream_knowledge": knowledge,
            "clean_provider_model": provider_model,
            "candidate_code_origin": code_origin,
            "provider_base_reconstruction_required": bool(reconstruction_required),
            "clean_reconstruction_mode": bool(args.clean_reconstruction),
            "legacy_provider_js_executed_for_reconstruction": False,
            "local_patches": applied_patches,
            "baseline_origin": "published_manifest",
            "bytes": len(candidate_data),
            "metadata": dict(entry),
            "baseline": True,
            "lkg": is_registered_lkg,
            "lkg_verified_categories": list(lkg_record.get("verified_categories") or []) if is_registered_lkg else [],
        })
        known_keys.add(key)
        seen_canonical_ids[provider_id] = {"source": "published-baseline", "key": key}

    # Keep registered last-known-good artifacts available even after a future
    # manifest has moved to another hash. The pruner also retains these files.
    existing_entries = {
        canonical_id(str(entry.get("id") or entry.get("name") or "")): entry
        for entry in published_manifest.get("scrapers", []) if isinstance(entry, dict)
    }
    for provider_id, record in sorted(lkg_records.items() if isinstance(lkg_records, dict) else []):
        if not isinstance(record, dict):
            continue
        filename = record.get("filename")
        expected_sha = record.get("sha256")
        if not isinstance(filename, str) or not isinstance(expected_sha, str):
            continue
        source_path = (ROOT / filename).resolve()
        try:
            source_path.relative_to((ROOT / "providers").resolve())
        except ValueError:
            continue
        if not source_path.is_file():
            continue
        data = source_path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_sha:
            continue
        published_key = f"published:{provider_id}"
        published = next((item for item in candidates if item.get("key") == published_key), None)
        if published and published.get("sha256") == digest:
            published["lkg"] = True
            published["lkg_verified_categories"] = list(record.get("verified_categories") or [])
            continue
        key = f"lkg:{provider_id}"
        if provider_id in seen_canonical_ids or key in known_keys:
            continue
        local_path = baseline_dir / f"lkg-{safe_fragment(provider_id)}.js"
        local_path.write_bytes(data)
        metadata = dict(existing_entries.get(provider_id) or {"id": provider_id, "name": provider_id})
        metadata["filename"] = filename
        candidates.append({
            "key": key,
            "source": "local-lkg",
            "source_name": "Registered last-known-good artifact",
            "source_priority": len(config.get("upstreams", {})) + 101,
            "source_repository": config.get("repository", {}).get("name"),
            "source_license": "GPL-3.0-only",
            "source_license_evidence": "LICENSE",
            "manifest_url": "provider-lkg.json",
            "upstream_id": provider_id,
            "canonical_id": provider_id,
            "provider_url": filename,
            "local_path": str(local_path.relative_to(stage)),
            "sha256": digest,
            "upstream_sha256": digest,
            "local_patches": [],
            "baseline_origin": "provider_lkg_registry",
            "bytes": len(data),
            "metadata": metadata,
            "baseline": True,
            "lkg": True,
            "lkg_verified_categories": list(record.get("verified_categories") or []),
        })
        known_keys.add(key)
        seen_canonical_ids[provider_id] = {"source": "local-lkg", "key": key}

    # Every duplicate has already been rejected at import time. Health/Repair
    # therefore receives exactly one candidate per canonical provider.
    candidates = sorted(
        candidates,
        key=lambda row: (str(row.get("canonical_id") or ""), int(row.get("source_priority", 999))),
    )

    if len(candidates) != len({item["canonical_id"] for item in candidates}):
        raise RuntimeError("duplicate canonical candidate escaped input rejection")

    registry = {
        "schema_version": 65,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "canonical_provider_count": len(seen_canonical_ids),
        "input_duplicate_count": len(duplicate_inputs),
        "input_duplicates": duplicate_inputs,
        "excluded_count": len(excluded),
        "excluded": excluded,
        "upstreams": upstream_reports,
        "errors": errors,
        "candidates": candidates,
    }
    (stage / "candidates.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if not candidates:
        print("No non-P2P provider candidate was downloaded.", file=sys.stderr)
        return 1
    if errors and args.require_all_upstreams:
        published_fallbacks = sum(1 for item in candidates if item.get("source") == "published-baseline")
        if published_fallbacks <= 0:
            return 1
        print(
            f"[WARN] {len(errors)} upstream source(s) unavailable without an upstream snapshot; "
            f"continuing with {published_fallbacks} current published functional fallbacks.",
            file=sys.stderr,
        )

    print(
        f"Imported {len(candidates)} canonical providers "
        f"({registry['input_duplicate_count']} duplicate declaration(s) rejected at input); "
        f"excluded {len(excluded)} P2P/torrent entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
