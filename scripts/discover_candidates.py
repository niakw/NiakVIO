#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage every non-P2P provider declared by the configured upstream manifests.

The published manifest and provider directory are never modified by this script.
All downloaded candidates live under staging/ until a separate read-only test job
has completed and the promotion policy accepts them.
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

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "sources.json"
DEFAULT_STAGE = ROOT / "staging"
USER_AGENT = "Nuvio-Curated-Discovery/5.12 (+GitHub Actions)"


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument(
        "--require-all-upstreams",
        action="store_true",
        help="Fail if any upstream manifest cannot be loaded.",
    )
    args = parser.parse_args()

    config = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    exclusions = config.get("exclusions", {})
    stage = args.stage.resolve()
    if stage.exists():
        shutil.rmtree(stage)
    providers_dir = stage / "providers"
    manifests_dir = stage / "manifests"
    providers_dir.mkdir(parents=True)
    manifests_dir.mkdir(parents=True)

    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    upstream_reports: dict[str, Any] = {}
    errors: list[str] = []

    for priority, (source_key, source_cfg) in enumerate(config["upstreams"].items()):
        try:
            manifest, manifest_url = fetch_manifest(source_cfg["manifest_urls"])
            (manifests_dir / f"{safe_fragment(source_key)}.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            source_count = 0
            source_excluded = 0
            source_failures: list[dict[str, str]] = []

            for index, entry in enumerate(manifest["scrapers"]):
                if not isinstance(entry, dict):
                    continue
                upstream_id = str(entry.get("id") or entry.get("name") or f"entry-{index}")
                preliminary_reason = exclusion_reason(entry, None, exclusions)
                if preliminary_reason:
                    excluded.append({"source": source_key, "id": upstream_id, "reason": preliminary_reason})
                    source_excluded += 1
                    print(f"[SKIP] {source_key}:{upstream_id}: {preliminary_reason}")
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
                    data = fetch_bytes(provider_url)
                    validate_javascript(data, provider_url)
                    reason = exclusion_reason(entry, data, exclusions)
                    if reason:
                        excluded.append({"source": source_key, "id": upstream_id, "reason": reason})
                        source_excluded += 1
                        print(f"[SKIP] {source_key}:{upstream_id}: {reason}")
                        continue

                    upstream_digest = hashlib.sha256(data).hexdigest()
                    data, applied_patches = apply_overrides(canonical_id(upstream_id), data)
                    validate_javascript(data, provider_url)
                    local_path.write_bytes(data)
                    subprocess.run([
                        "node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(local_path)
                    ], check=True, capture_output=True, text=True)
                    digest = hashlib.sha256(data).hexdigest()
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
                            "upstream_id": upstream_id,
                            "canonical_id": canonical_id(upstream_id),
                            "provider_url": provider_url,
                            "local_path": str(local_path.relative_to(stage)),
                            "sha256": digest,
                            "upstream_sha256": upstream_digest,
                            "local_patches": applied_patches,
                            "bytes": len(data),
                            "metadata": entry,
                        }
                    )
                    source_count += 1
                    print(f"[OK] {source_key}:{upstream_id}")
                except Exception as exc:
                    source_failures.append({"id": upstream_id, "error": str(exc)})
                    print(f"[WARN] {source_key}:{upstream_id}: {exc}", file=sys.stderr)

            upstream_reports[source_key] = {
                "status": "loaded",
                "manifest_url": manifest_url,
                "declared": len(manifest["scrapers"]),
                "downloaded": source_count,
                "excluded": source_excluded,
                "failures": source_failures,
            }
        except Exception as exc:
            message = f"{source_key}: {exc}"
            errors.append(message)
            upstream_reports[source_key] = {"status": "failed", "error": str(exc)}
            print(f"[ERROR] {message}", file=sys.stderr)

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
        if key in known_keys:
            continue
        data = source_path.read_bytes()
        validate_javascript(data, filename)
        local_path = baseline_dir / f"{safe_fragment(provider_id)}.js"
        local_path.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
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
            "local_path": str(local_path.relative_to(stage)),
            "sha256": digest,
            "upstream_sha256": digest,
            "local_patches": ["published_baseline"],
            "bytes": len(data),
            "metadata": dict(entry),
            "baseline": True,
        })
        known_keys.add(key)

    # Attach a canonical metadata summary before runtime validation so fixture
    # selection can use the combined descriptions of all three manifests rather
    # than whichever upstream variant happens to execute first.
    canonical_variants: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        canonical_variants.setdefault(candidate["canonical_id"], []).append(candidate)
    for variants in canonical_variants.values():
        descriptions: list[str] = []
        supported_types: list[str] = []
        content_languages: list[str] = []
        formats: list[str] = []
        sources: list[str] = []
        for variant in variants:
            metadata = variant.get("metadata", {}) if isinstance(variant.get("metadata"), dict) else {}
            description = str(metadata.get("description") or "").strip()
            if description and description not in descriptions:
                descriptions.append(description)
            for value in metadata.get("supportedTypes", []) if isinstance(metadata.get("supportedTypes"), list) else []:
                text = str(value).strip()
                if text and text not in supported_types:
                    supported_types.append(text)
            for value in metadata.get("contentLanguage", []) if isinstance(metadata.get("contentLanguage"), list) else []:
                text = str(value).strip()
                if text and text not in content_languages:
                    content_languages.append(text)
            for value in metadata.get("formats", []) if isinstance(metadata.get("formats"), list) else []:
                text = str(value).strip()
                if text and text not in formats:
                    formats.append(text)
            source = str(variant.get("source") or "").strip()
            if source and source not in sources:
                sources.append(source)
        summary = {
            "descriptions": descriptions,
            "supportedTypes": supported_types,
            "contentLanguage": content_languages,
            "formats": formats,
            "sources": sources,
        }
        for variant in variants:
            variant["canonical_metadata"] = summary

    registry = {
        "schema_version": 63,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "canonical_provider_count": len({item["canonical_id"] for item in candidates}),
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
        return 1

    print(
        f"Discovered {len(candidates)} variants for "
        f"{registry['canonical_provider_count']} canonical providers; "
        f"excluded {len(excluded)} P2P/torrent entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
