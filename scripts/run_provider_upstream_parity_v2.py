#!/usr/bin/env python3
"""Compatibility launcher for provider parity using the current upstream registry.

The legacy parity harness still reads ``sources.json['upstreams']`` even though
upstream provider repositories moved to ``engine_v2/config/provider-upstreams.json``.
Keep the proven A/B worker and classification logic unchanged, but replace only
its upstream catalogue loader with the current authoritative registry.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import run_provider_upstream_parity as parity

ROOT = Path(__file__).resolve().parents[1]
UPSTREAMS = ROOT / "engine_v2" / "config" / "provider-upstreams.json"


def upstream_catalog() -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    config = json.loads(UPSTREAMS.read_text(encoding="utf-8"))
    rows = config.get("upstreams") if isinstance(config, dict) else []
    catalog: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []

    for cfg in rows if isinstance(rows, list) else []:
        if not isinstance(cfg, dict):
            continue
        source_id = str(cfg.get("id") or "").strip()
        repositories = [
            str(cfg.get("repository") or "").strip(),
            str(cfg.get("fallback_repository") or "").strip(),
        ]
        branch = str(cfg.get("branch") or "main").strip() or "main"
        manifest_path = str(cfg.get("manifest") or "manifest.json").strip() or "manifest.json"
        selected_repo = None
        manifest = None
        last_error = None

        for repo in [value for value in repositories if value]:
            manifest_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{manifest_path.lstrip('/')}"
            try:
                manifest = parity.get_json(manifest_url)
                selected_repo = repo
                break
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"[:240]

        if not source_id or not selected_repo or not isinstance(manifest, dict):
            errors.append({"source": source_id or "unknown", "error": last_error or "manifest unavailable"})
            continue

        provider_rows = manifest.get("scrapers") or manifest.get("providers") or []
        if not isinstance(provider_rows, list):
            provider_rows = []
        raw_base = f"https://raw.githubusercontent.com/{selected_repo}/{branch}/"
        for row in provider_rows:
            if not isinstance(row, dict):
                continue
            provider_id = parity.cid(row.get("id"))
            filename = str(row.get("filename") or "").strip()
            if not provider_id or not filename or provider_id in catalog:
                continue
            catalog[provider_id] = {
                "source": source_id,
                "entry": row,
                "url": urllib.parse.urljoin(raw_base, filename.lstrip("/")),
            }

    return catalog, errors


parity.upstream_catalog = upstream_catalog

if __name__ == "__main__":
    raise SystemExit(parity.main())
