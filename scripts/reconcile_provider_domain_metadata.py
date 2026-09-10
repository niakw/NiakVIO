#!/usr/bin/env python3
"""Reconcile provider-owned domain metadata with the current terminal.

Domain Refresh can rotate a provider origin without changing its Core. Provider-
owned asset URLs (logo/icon/favicon) and stale site-domain replacement targets
must follow that rotation as well, otherwise later static checks and generated
manifests can keep yesterday's host alive.

Only hosts already known as the provider's own current/historical terminals are
rewritten. External/CDN assets are left untouched.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
from pathlib import Path
from typing import Any

import domain_refresh_transaction_v2 as transaction

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
REGISTRY = ROOT / "provider-hubs.json"
HISTORY = ROOT / "provider-domain-history.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def host(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    return (urllib.parse.urlparse(raw).hostname or "").casefold().strip(".")


def rows(document: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    raw = document.get(key) or {}
    if isinstance(raw, dict):
        return {str(k).casefold(): v for k, v in raw.items() if isinstance(v, dict)}
    return {}


def known_site_hosts(
    provider_id: str,
    patch: dict[str, Any],
    registry_row: dict[str, Any],
    history_row: dict[str, Any],
) -> set[str]:
    values: list[object] = []
    values.append(patch.get("official_site"))
    values.append(registry_row.get("direct"))
    values.extend(registry_row.get("direct_candidates") or [])
    values.extend(registry_row.get("allowed_terminal_hosts") or [])
    current = history_row.get("current")
    if isinstance(current, dict):
        values.append(current.get("url"))
    for prior in history_row.get("previous") or []:
        if isinstance(prior, dict):
            values.append(prior.get("url"))
    for mapping_name in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
        mapping = patch.get(mapping_name)
        if isinstance(mapping, dict):
            values.extend(mapping.keys())
            values.extend(mapping.values())
    return {host(value) for value in values if host(value)}


def rewrite_url_host(value: str, next_host: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if not parsed.hostname:
        return value
    port = f":{parsed.port}" if parsed.port else ""
    netloc = next_host + port
    return urllib.parse.urlunparse((
        parsed.scheme or "https",
        netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment,
    ))


def reconcile_patch(
    provider_id: str,
    patch: dict[str, Any],
    registry_row: dict[str, Any],
    history_row: dict[str, Any],
) -> list[str]:
    current_site = str(patch.get("official_site") or registry_row.get("direct") or "").strip()
    current_host = host(current_site)
    if not current_host:
        return []
    known_hosts = known_site_hosts(provider_id, patch, registry_row, history_row)
    changed: list[str] = []

    manifest = patch.get("manifest_overrides")
    if isinstance(manifest, dict):
        for field in ("logo", "icon", "favicon"):
            value = str(manifest.get(field) or "").strip()
            value_host = host(value)
            if value and value_host and value_host != current_host and value_host in known_hosts:
                manifest[field] = rewrite_url_host(value, current_host)
                changed.append(f"manifest_overrides.{field}")

    # Normalize only site-host mappings. API-host mappings intentionally keep
    # their own authority and are not collapsed onto the web origin.
    for mapping_name in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
        mapping = patch.get(mapping_name)
        if not isinstance(mapping, dict):
            continue
        if current_host in mapping:
            mapping.pop(current_host, None)
            changed.append(f"{mapping_name}.cycle")
        for source, target in list(mapping.items()):
            target_host = host(target)
            if (
                target_host
                and target_host != current_host
                and target_host in known_hosts
                and not target_host.startswith("api.")
            ):
                mapping[source] = current_host
                changed.append(mapping_name)

    return sorted(set(changed))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    overrides = load(OVERRIDES)
    registry = load(REGISTRY)
    history = load(HISTORY)
    patches = rows(overrides, "provider_patches")
    registry_rows = rows(registry, "providers")
    history_rows = rows(history, "providers")

    changed: dict[str, list[str]] = {}
    for provider_id, patch in sorted(patches.items()):
        fields = reconcile_patch(
            provider_id,
            patch,
            registry_rows.get(provider_id) or {},
            history_rows.get(provider_id) or {},
        )
        if fields:
            changed[provider_id] = fields

    if changed:
        write(OVERRIDES, overrides)
        if args.rebuild:
            transaction.rebuild_provider_configs(sorted(changed))

    print(
        "FIELD_DOMAIN_METADATA_RECONCILE "
        f"changed={len(changed)} providers={','.join(sorted(changed)) if changed else '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
