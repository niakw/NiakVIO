#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build the public Nuvio manifest deterministically from the curated source list.

Important invariants:
- Health/quality results are NEVER used to select, replace, enable or disable a provider.
- Every configured provider is synchronized from its fixed primary source, then from
  explicitly configured fallbacks only if the primary file cannot be downloaded.
- Every downloaded script receives a content-hashed filename so Nuvio is forced to
  fetch a changed script instead of reusing a cached stable URL.
- New files are prepared under publish/providers/. The workflow commits those files
  before it publishes manifest.next.json.
- If every configured source fails for a provider, the currently published file is
  retained when it still exists. An enabled provider with no downloadable or retained
  file aborts publication rather than producing a partial manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "sources.json"
CURRENT_MANIFEST_PATH = ROOT / "manifest.json"
CURRENT_PROVENANCE_PATH = ROOT / "PROVENANCE.json"
NEXT_MANIFEST_PATH = ROOT / "manifest.next.json"
NEXT_PROVENANCE_PATH = ROOT / "PROVENANCE.next.json"
REPORT_PATH = ROOT / "sync-report.json"
PUBLISH_ROOT = ROOT / "publish"
PUBLISH_PROVIDERS = PUBLISH_ROOT / "providers"
PUBLIC_PROVIDERS = ROOT / "providers"

USER_AGENT = "Nuvio-Curated-Deterministic-Sync/4.0 (+GitHub Actions)"
REQUEST_TIMEOUT_SECONDS = 40
DOWNLOAD_ATTEMPTS = 3

P2P_PROTOCOL_PREFIXES = ("magnet:", "torrent:", "acestream:", "sop:")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def safe_fragment(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")
    return cleaned[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def fetch_bytes(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,application/javascript,*/*",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=REQUEST_TIMEOUT_SECONDS,
            ) as response:
                data = response.read()
            if not data:
                raise RuntimeError("empty response")
            return data
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < DOWNLOAD_ATTEMPTS:
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


def find_entry(scrapers: list[dict[str, Any]], upstream_id: str) -> dict[str, Any]:
    exact = next((item for item in scrapers if item.get("id") == upstream_id), None)
    if exact is not None:
        return exact

    wanted = str(upstream_id).casefold()
    insensitive = next(
        (
            item
            for item in scrapers
            if str(item.get("id", "")).casefold() == wanted
        ),
        None,
    )
    if insensitive is not None:
        return insensitive
    raise KeyError(f"provider not found in upstream manifest: {upstream_id}")


def validate_javascript(data: bytes, url: str) -> None:
    if len(data) < 100:
        raise ValueError(f"JavaScript file is too small ({len(data)} bytes): {url}")
    head = data[:500].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        raise ValueError(f"HTML received instead of JavaScript: {url}")


def exclusion_reason(
    entry: dict[str, Any],
    data: bytes | None,
    exclusions: dict[str, Any],
) -> str | None:
    provider_id = canonical_id(str(entry.get("id") or entry.get("name") or ""))
    explicit_ids = {
        canonical_id(str(value))
        for value in exclusions.get("provider_ids", [])
    }
    if provider_id in explicit_ids:
        return "explicitly excluded P2P/torrent provider id"

    metadata_text = json.dumps(
        entry,
        ensure_ascii=False,
        sort_keys=True,
    ).casefold()
    for pattern in exclusions.get("metadata_patterns", []):
        if str(pattern).casefold() in metadata_text:
            return f"metadata contains excluded marker: {pattern}"

    if data is not None:
        script_text = data[:2_000_000].decode(
            "utf-8",
            errors="ignore",
        ).casefold()
        for pattern in exclusions.get("script_patterns", []):
            if str(pattern).casefold() in script_text:
                return f"script contains excluded marker: {pattern}"

    return None


def safe_existing_provider_path(filename: Any) -> Path | None:
    if not isinstance(filename, str) or not filename.strip():
        return None
    candidate = (ROOT / filename).resolve()
    try:
        candidate.relative_to(PUBLIC_PROVIDERS.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def provider_candidates(local_cfg: dict[str, Any]) -> list[dict[str, str]]:
    values = [{
        "source": str(local_cfg["source"]),
        "upstream_id": str(local_cfg["upstream_id"]),
    }]
    for fallback in local_cfg.get("fallback_sources", []):
        values.append({
            "source": str(fallback["source"]),
            "upstream_id": str(fallback["upstream_id"]),
        })
    return values


def build_entry(
    upstream_entry: dict[str, Any],
    local_cfg: dict[str, Any],
    filename: str,
) -> dict[str, Any]:
    # Preserve the upstream manifest shape exactly, then override only the fields
    # controlled by this curated manifest.
    entry = dict(upstream_entry)
    entry["id"] = str(local_cfg["id"])
    entry["filename"] = filename
    entry["enabled"] = bool(local_cfg["enabled"])
    return entry


def validate_final_manifest(
    manifest: dict[str, Any],
    new_files: set[str],
    exclusions: dict[str, Any],
) -> None:
    scrapers = manifest.get("scrapers")
    if not isinstance(scrapers, list) or not scrapers:
        raise RuntimeError("refusing to publish an empty manifest")

    seen: set[str] = set()
    for entry in scrapers:
        if not isinstance(entry, dict):
            raise RuntimeError("manifest contains a non-object scraper entry")

        cid = canonical_id(str(entry.get("id", "")))
        if not cid:
            raise RuntimeError("manifest contains an empty provider id")
        if cid in seen:
            raise RuntimeError(f"duplicate provider id in final manifest: {cid}")
        seen.add(cid)

        filename = entry.get("filename")
        if not isinstance(filename, str) or not filename.startswith("providers/"):
            raise RuntimeError(f"unsafe provider filename for {cid}: {filename!r}")

        if filename not in new_files and safe_existing_provider_path(filename) is None:
            raise RuntimeError(
                f"manifest references a missing provider file for {cid}: {filename}"
            )

        reason = exclusion_reason(entry, None, exclusions)
        if reason is not None:
            raise RuntimeError(f"excluded provider reached final manifest: {cid}: {reason}")


def main() -> int:
    config = load_json(SOURCES_PATH, {})
    current_manifest = load_json(CURRENT_MANIFEST_PATH, {"scrapers": []})
    current_provenance = load_json(CURRENT_PROVENANCE_PATH, {"providers": []})
    exclusions = config.get("exclusions", {})

    current_by_id = {
        canonical_id(str(entry.get("id", ""))): entry
        for entry in current_manifest.get("scrapers", [])
        if isinstance(entry, dict)
    }
    current_provenance_by_id = {
        canonical_id(str(item.get("id", ""))): item
        for item in current_provenance.get("providers", [])
        if isinstance(item, dict)
    }

    if PUBLISH_ROOT.exists():
        shutil.rmtree(PUBLISH_ROOT)
    PUBLISH_PROVIDERS.mkdir(parents=True)

    loaded_upstreams: dict[str, dict[str, Any]] = {}
    upstream_errors: dict[str, str] = {}
    for source_key, source_cfg in config.get("upstreams", {}).items():
        try:
            manifest, manifest_url = fetch_manifest(source_cfg["manifest_urls"])
            loaded_upstreams[source_key] = {
                "manifest": manifest,
                "manifest_url": manifest_url,
                "repository": source_cfg.get("repository"),
                "license": source_cfg.get("license"),
            }
            print(f"[OK] upstream manifest {source_key}: {manifest_url}")
        except Exception as exc:
            upstream_errors[source_key] = str(exc)
            print(f"[WARN] upstream manifest {source_key}: {exc}", file=sys.stderr)

    output_entries: list[dict[str, Any]] = []
    provenance_items: list[dict[str, Any]] = []
    report_items: list[dict[str, Any]] = []
    blocking_failures: list[str] = []
    new_files: set[str] = set()
    generated_at = datetime.now(timezone.utc).isoformat()

    for local_cfg in config.get("providers", []):
        local_id = canonical_id(str(local_cfg["id"]))
        attempts: list[dict[str, str]] = []
        selected: dict[str, Any] | None = None

        for candidate in provider_candidates(local_cfg):
            source_key = candidate["source"]
            upstream_id = candidate["upstream_id"]
            upstream = loaded_upstreams.get(source_key)

            if upstream is None:
                attempts.append({
                    "source": source_key,
                    "upstream_id": upstream_id,
                    "error": upstream_errors.get(source_key, "upstream manifest unavailable"),
                })
                continue

            try:
                upstream_entry = find_entry(
                    upstream["manifest"]["scrapers"],
                    upstream_id,
                )
                preliminary_reason = exclusion_reason(
                    upstream_entry,
                    None,
                    exclusions,
                )
                if preliminary_reason is not None:
                    raise ValueError(preliminary_reason)

                upstream_filename = upstream_entry.get("filename")
                if not isinstance(upstream_filename, str) or not upstream_filename.strip():
                    raise ValueError("missing upstream filename")

                provider_url = urllib.parse.urljoin(
                    upstream["manifest_url"],
                    upstream_filename,
                )
                data = fetch_bytes(provider_url)
                validate_javascript(data, provider_url)

                script_reason = exclusion_reason(
                    upstream_entry,
                    data,
                    exclusions,
                )
                if script_reason is not None:
                    raise ValueError(script_reason)

                digest = hashlib.sha256(data).hexdigest()
                short_digest = digest[:16]
                published_name = (
                    f"{safe_fragment(local_cfg['id'])}--"
                    f"{safe_fragment(source_key)}--{short_digest}.js"
                )
                published_relative = f"providers/{published_name}"
                destination = PUBLISH_PROVIDERS / published_name
                destination.write_bytes(data)

                selected = {
                    "source": source_key,
                    "upstream_id": upstream_id,
                    "upstream_entry": upstream_entry,
                    "provider_url": provider_url,
                    "sha256": digest,
                    "published_relative": published_relative,
                    "bytes": len(data),
                    "repository": upstream.get("repository"),
                    "license": upstream.get("license"),
                }
                break
            except Exception as exc:
                attempts.append({
                    "source": source_key,
                    "upstream_id": upstream_id,
                    "error": str(exc),
                })

        if selected is not None:
            entry = build_entry(
                selected["upstream_entry"],
                local_cfg,
                selected["published_relative"],
            )
            output_entries.append(entry)
            new_files.add(selected["published_relative"])
            provenance_items.append({
                "id": str(local_cfg["id"]),
                "source": selected["source"],
                "upstream_id": selected["upstream_id"],
                "repository": selected["repository"],
                "provider_url": selected["provider_url"],
                "license": selected["license"],
                "sha256": selected["sha256"],
                "published_filename": selected["published_relative"],
                "synchronized_at": generated_at,
            })
            report_items.append({
                "id": str(local_cfg["id"]),
                "status": "synchronized",
                "enabled": bool(local_cfg["enabled"]),
                "source": selected["source"],
                "upstream_id": selected["upstream_id"],
                "published_filename": selected["published_relative"],
                "sha256": selected["sha256"],
                "bytes": selected["bytes"],
                "failed_candidates": attempts,
            })
            print(
                f"[OK] {local_cfg['id']} <- {selected['source']}:"
                f"{selected['upstream_id']} -> {selected['published_relative']}"
            )
            continue

        current_entry = current_by_id.get(local_id)
        current_path = (
            safe_existing_provider_path(current_entry.get("filename"))
            if current_entry
            else None
        )

        if current_entry is not None and current_path is not None:
            retained = dict(current_entry)
            retained["id"] = str(local_cfg["id"])
            retained["enabled"] = bool(local_cfg["enabled"])
            output_entries.append(retained)

            old_provenance = current_provenance_by_id.get(local_id, {})
            provenance_items.append({
                **old_provenance,
                "id": str(local_cfg["id"]),
                "published_filename": retained["filename"],
                "sha256": hashlib.sha256(current_path.read_bytes()).hexdigest(),
                "retained_at": generated_at,
                "retention_reason": "all configured upstream candidates failed",
            })
            report_items.append({
                "id": str(local_cfg["id"]),
                "status": "retained-current-file",
                "enabled": bool(local_cfg["enabled"]),
                "published_filename": retained["filename"],
                "failed_candidates": attempts,
            })
            print(
                f"[RETAIN] {local_cfg['id']} -> {retained['filename']}",
                file=sys.stderr,
            )
            continue

        message = f"{local_cfg['id']}: no downloadable or existing provider file"
        report_items.append({
            "id": str(local_cfg["id"]),
            "status": "missing",
            "enabled": bool(local_cfg["enabled"]),
            "failed_candidates": attempts,
        })
        if bool(local_cfg["enabled"]):
            blocking_failures.append(message)
        else:
            print(f"[SKIP] disabled provider unavailable: {message}", file=sys.stderr)

    report = {
        "schema_version": 4,
        "generated_at": generated_at,
        "mode": "deterministic-curated-sync",
        "health_results_used_for_publication": False,
        "configured_providers": len(config.get("providers", [])),
        "published_providers": len(output_entries),
        "enabled_providers": sum(
            1 for entry in output_entries if entry.get("enabled") is True
        ),
        "upstream_errors": upstream_errors,
        "blocking_failures": blocking_failures,
        "items": report_items,
    }
    atomic_write_json(REPORT_PATH, report)

    if blocking_failures:
        print(
            "Publication aborted because one or more enabled providers have no file:\n- "
            + "\n- ".join(blocking_failures),
            file=sys.stderr,
        )
        return 1

    manifest = {
        "name": config["repository"]["name"],
        "version": config["repository"]["manifest_version"],
        "scrapers": output_entries,
    }
    validate_final_manifest(manifest, new_files, exclusions)

    provenance = {
        "schema_version": 4,
        "generated_at": generated_at,
        "publication_mode": "deterministic-curated-sync",
        "health_results_used_for_publication": False,
        "providers": provenance_items,
    }

    atomic_write_json(NEXT_MANIFEST_PATH, manifest)
    atomic_write_json(NEXT_PROVENANCE_PATH, provenance)

    print(
        f"Prepared {len(output_entries)} providers "
        f"({sum(1 for item in output_entries if item.get('enabled'))} enabled)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
