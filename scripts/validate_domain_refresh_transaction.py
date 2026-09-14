#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_TYPES = {"hub", "curated_direct", "source_redirect", "provider_config", "live_current"}
REGISTRY_SCOPED_AUTHORITY_TYPES = {"telegram_public"}
PLACEHOLDER_TOKENS = ("${", "{{", "}}", "function(", "=>", "`", "<%", "%>")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def concrete_http(value: object) -> bool:
    raw = str(value or "").strip()
    if not raw.startswith(("http://", "https://")):
        return False
    if any(token in raw for token in PLACEHOLDER_TOKENS):
        return False
    try:
        parsed = urlparse(raw)
    except ValueError:
        return False
    return bool(parsed.scheme in {"http", "https"} and parsed.hostname)


def provider_patches(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = document.get("provider_patches") or {}
    return {canonical(key): value for key, value in rows.items() if canonical(key) and isinstance(value, dict)}


def registry_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = document.get("providers") or document
    return {canonical(key): value for key, value in rows.items() if canonical(key) and isinstance(value, dict)}


def history_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = document.get("providers") or document
    return {canonical(key): value for key, value in rows.items() if canonical(key) and isinstance(value, dict)}


def history_urls(row: dict[str, Any]) -> list[str]:
    output: list[str] = []
    current = row.get("current")
    if isinstance(current, dict):
        url = str(current.get("url") or "").strip().rstrip("/")
        if url:
            output.append(url)
    for item in row.get("previous") or []:
        if isinstance(item, dict):
            url = str(item.get("url") or "").strip().rstrip("/")
        else:
            url = str(item or "").strip().rstrip("/")
        if url and url not in output:
            output.append(url)
    return output


def historical_previous_urls(row: dict[str, Any]) -> set[str]:
    current = row.get("current")
    current_url = str((current or {}).get("url") or "").strip().rstrip("/").casefold() if isinstance(current, dict) else ""
    return {url.casefold() for url in history_urls(row) if url.casefold() != current_url}


def selected_candidate(item: dict[str, Any], terminal: str) -> dict[str, Any]:
    normalized = str(terminal or "").strip().rstrip("/").casefold()
    for row in item.get("site_candidates") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("url") or "").strip().rstrip("/").casefold() == normalized:
            return row
    return {}


def selected_source_is_authoritative(
    provider_id: str,
    item: dict[str, Any],
    before_registry: dict[str, dict[str, Any]],
) -> bool:
    """Accept global authority types or narrowly registry-authorized public feeds.

    A public Telegram page is never authority by type alone. It qualifies only
    when the current provider-hubs.json row explicitly lists the exact selected
    source URL and labels its purpose as an authoritative address/domain
    reference. This keeps arbitrary public/community Telegram links fail-closed.
    """
    source_type = str(item.get("selected_source_type") or "").strip().casefold()
    if source_type in AUTHORITY_TYPES:
        return True
    if source_type not in REGISTRY_SCOPED_AUTHORITY_TYPES:
        return False

    selected_source = str(item.get("selected_source") or "").strip().rstrip("/").casefold()
    if not selected_source:
        return False
    registry_row = before_registry.get(provider_id) or {}
    for source in registry_row.get("sources") or []:
        if not isinstance(source, dict):
            continue
        configured_type = str(source.get("type") or "").strip().casefold()
        configured_url = str(source.get("url") or "").strip().rstrip("/").casefold()
        purpose = str(source.get("purpose") or "").strip().casefold()
        if configured_type != source_type or configured_url != selected_source:
            continue
        if "authoritative" in purpose and ("address" in purpose or "domain" in purpose):
            return True
    return False


def has_fresh_rollback_evidence(item: dict[str, Any], terminal: str) -> bool:
    candidate = selected_candidate(item, terminal)
    label = str(candidate.get("label") or "").casefold()
    source_type = str(candidate.get("source_type") or item.get("selected_source_type") or "").casefold()
    if source_type not in {"hub", "source_redirect"}:
        return False
    positive = (
        "nouvelle adresse",
        "new address",
        "adresse officielle",
        "official address",
        "nouveau domaine",
        "new domain",
        "homepage",
        "accueil",
        "principal",
        "primary",
    )
    return any(token in label for token in positive)


def validate(
    before_overrides_doc: dict[str, Any],
    after_overrides_doc: dict[str, Any],
    before_hubs_doc: dict[str, Any],
    after_hubs_doc: dict[str, Any],
    before_history_doc: dict[str, Any],
    report: dict[str, Any],
    changes: dict[str, Any],
) -> dict[str, Any]:
    before_patches = provider_patches(before_overrides_doc)
    after_patches = provider_patches(after_overrides_doc)
    before_registry = registry_rows(before_hubs_doc)
    after_registry = registry_rows(after_hubs_doc)
    previous_history = history_rows(before_history_doc)
    report_rows = {
        canonical(key): row
        for key, row in (report.get("providers") or {}).items()
        if canonical(key) and isinstance(row, dict)
    }

    changed_actual: set[str] = set()
    for provider_id in sorted(set(before_patches) | set(after_patches)):
        before_site = str((before_patches.get(provider_id) or {}).get("official_site") or "").rstrip("/")
        after_site = str((after_patches.get(provider_id) or {}).get("official_site") or "").rstrip("/")
        if before_site == after_site:
            continue
        changed_actual.add(provider_id)
        if not concrete_http(after_site):
            raise AssertionError(f"{provider_id}: non-concrete official_site proposed: {after_site!r}")
        item = report_rows.get(provider_id) or {}
        if item.get("status") != "site_authoritative":
            raise AssertionError(f"{provider_id}: domain changed without site_authoritative proof")
        source_type = str(item.get("selected_source_type") or "").casefold()
        if not selected_source_is_authoritative(provider_id, item, before_registry):
            raise AssertionError(f"{provider_id}: non-authoritative source attempted domain publication: {source_type!r}")
        reported_site = str(item.get("official_site") or "").rstrip("/")
        if reported_site != after_site:
            raise AssertionError(f"{provider_id}: report/config terminal mismatch: {reported_site!r} != {after_site!r}")

        registry_row = after_registry.get(provider_id) or {}
        registry_direct = str(registry_row.get("direct") or "").rstrip("/")
        if registry_direct != after_site:
            raise AssertionError(f"{provider_id}: registry/config terminal divergence: {registry_direct!r} != {after_site!r}")

        historical = historical_previous_urls(previous_history.get(provider_id) or {})
        if after_site.casefold() in historical and after_site.casefold() != before_site.casefold():
            if not has_fresh_rollback_evidence(item, after_site):
                raise AssertionError(
                    f"{provider_id}: attempted rollback to historical terminal without fresh hub evidence: {after_site}"
                )

    # An unresolved/not-applicable provider may never be mutated indirectly.
    for provider_id, item in report_rows.items():
        if item.get("status") == "site_authoritative":
            continue
        before_site = str((before_patches.get(provider_id) or {}).get("official_site") or "").rstrip("/")
        after_site = str((after_patches.get(provider_id) or {}).get("official_site") or "").rstrip("/")
        if before_site != after_site:
            raise AssertionError(f"{provider_id}: unresolved discovery mutated official_site")

    # Registry address fields must never retain JS/template constructors.
    for provider_id, row in after_registry.items():
        direct = row.get("direct")
        if direct not in (None, "") and not concrete_http(direct):
            raise AssertionError(f"{provider_id}: invalid registry direct URL: {direct!r}")
        for value in row.get("direct_candidates") or []:
            if not concrete_http(value):
                raise AssertionError(f"{provider_id}: invalid registry direct candidate: {value!r}")
        for value in row.get("allowed_terminal_hosts") or []:
            raw = str(value or "")
            if not raw or any(token in raw for token in PLACEHOLDER_TOKENS):
                raise AssertionError(f"{provider_id}: invalid allowed terminal host: {raw!r}")

    declared = {canonical(value) for value in changes.get("changed") or [] if canonical(value)}
    if changed_actual != declared:
        raise AssertionError(
            f"domain change accounting mismatch actual={sorted(changed_actual)} declared={sorted(declared)}"
        )

    # A current provider mutation is reconciled when the registry terminal equals
    # the final provider terminal. The registry may already have that exact value,
    # in which case registry_changed is intentionally a no-op rather than an error.
    registry_changed = {canonical(value) for value in changes.get("registry_changed") or [] if canonical(value)}
    for provider_id in changed_actual:
        if provider_id not in after_registry:
            raise AssertionError(f"{provider_id}: changed provider missing from registry")
        after_site = str((after_patches.get(provider_id) or {}).get("official_site") or "").rstrip("/")
        registry_direct = str((after_registry.get(provider_id) or {}).get("direct") or "").rstrip("/")
        if registry_direct != after_site:
            raise AssertionError(f"{provider_id}: official_site changed without registry reconciliation")

    return {
        "changed": sorted(changed_actual),
        "registry_changed": sorted(registry_changed),
        "idempotent": not changed_actual and before_hubs_doc == after_hubs_doc,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-overrides", required=True)
    parser.add_argument("--after-overrides", default="provider-overrides.json")
    parser.add_argument("--before-hubs", required=True)
    parser.add_argument("--after-hubs", default="provider-hubs.json")
    parser.add_argument("--before-history", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--changes", required=True)
    args = parser.parse_args()

    result = validate(
        load(Path(args.before_overrides)),
        load(Path(args.after_overrides)),
        load(Path(args.before_hubs)),
        load(Path(args.after_hubs)),
        load(Path(args.before_history)),
        load(Path(args.report)),
        load(Path(args.changes)),
    )
    print("FIELD_DOMAIN_REFRESH_GUARD " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
