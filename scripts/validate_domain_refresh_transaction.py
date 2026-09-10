#!/usr/bin/env python3
"""Fail-closed guard for the scheduled Provider domain refresh transaction.

The daily Domain Refresh is allowed to publish address changes only when the
change is explicitly supported by the current authoritative hub/channel/redirect
observation. Ambiguous or unresolved discovery must preserve the published state.

This guard intentionally runs *after* discovery/mutation in the ephemeral Actions
workspace and *before* any commit. A failure therefore discards the candidate
transaction without changing main.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

AUTHORITY_TYPES = {"hub", "telegram_public", "redirect"}
FRESH_LABEL_TOKENS = (
    "new", "nouveau", "nouvelle", "current", "actuel", "actuelle",
    "latest", "dernier", "derniere", "officiel", "officielle", "official",
)
PLACEHOLDER_TOKENS = ("${", "{{", "}}", "<%", "%>", "{", "}")


def load(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: JSON object required")
    return value


def canonical(value: object) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", str(value or "").casefold()).strip(".-")


def host(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    return (urllib.parse.urlparse(raw).hostname or "").casefold().strip(".")


def concrete_http(value: object) -> bool:
    raw = str(value or "").strip()
    if not raw or any(token in raw for token in PLACEHOLDER_TOKENS):
        return False
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.casefold()
    return not any(token in hostname for token in ("$", "{", "}"))


def provider_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = document.get("providers") or {}
    if isinstance(raw, dict):
        return {
            canonical(key): row
            for key, row in raw.items()
            if canonical(key) and isinstance(row, dict)
        }
    if isinstance(raw, list):
        return {
            canonical(row.get("id")): row
            for row in raw
            if isinstance(row, dict) and canonical(row.get("id"))
        }
    raise AssertionError("provider-hubs.json providers must be object or array")


def patch_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = document.get("provider_patches") or {}
    if not isinstance(raw, dict):
        raise AssertionError("provider-overrides.json provider_patches must be object")
    return {
        canonical(key): row
        for key, row in raw.items()
        if canonical(key) and isinstance(row, dict)
    }


def history_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = document.get("providers") or {}
    if not isinstance(raw, dict):
        return {}
    return {
        canonical(key): row
        for key, row in raw.items()
        if canonical(key) and isinstance(row, dict)
    }


def historical_previous_urls(row: dict[str, Any]) -> set[str]:
    output: set[str] = set()
    for prior in row.get("previous") or []:
        if isinstance(prior, dict):
            value = str(prior.get("url") or "").rstrip("/").casefold()
            if value:
                output.add(value)
    return output


def selected_candidate(item: dict[str, Any], terminal: str) -> dict[str, Any]:
    normalized = terminal.rstrip("/").casefold()
    for row in item.get("site_candidates") or []:
        if isinstance(row, dict) and str(row.get("url") or "").rstrip("/").casefold() == normalized:
            return row
    return {}


def has_fresh_rollback_evidence(item: dict[str, Any], terminal: str) -> bool:
    source_type = str(item.get("selected_source_type") or "").casefold()
    candidate = selected_candidate(item, terminal)
    if source_type in {"redirect", "telegram_public"}:
        return True
    if bool(candidate.get("source_redirect")):
        return True
    label = str(candidate.get("label") or "").casefold()
    return any(token in label for token in FRESH_LABEL_TOKENS)


def validate(
    before_overrides: dict[str, Any],
    after_overrides: dict[str, Any],
    before_hubs: dict[str, Any],
    after_hubs: dict[str, Any],
    before_history: dict[str, Any],
    report: dict[str, Any],
    changes: dict[str, Any],
) -> dict[str, Any]:
    before_patches = patch_rows(before_overrides)
    after_patches = patch_rows(after_overrides)
    before_registry = provider_rows(before_hubs)
    after_registry = provider_rows(after_hubs)
    previous_history = history_rows(before_history)
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
        if source_type not in AUTHORITY_TYPES:
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

    # Existing registry rows may change metadata, but a provider with an official
    # site mutation must be listed in registry_changed or already match exactly.
    registry_changed = {canonical(value) for value in changes.get("registry_changed") or [] if canonical(value)}
    for provider_id in changed_actual:
        if provider_id not in after_registry:
            raise AssertionError(f"{provider_id}: changed provider missing from registry")
        if provider_id not in registry_changed and after_registry.get(provider_id) == before_registry.get(provider_id):
            raise AssertionError(f"{provider_id}: official_site changed without registry reconciliation")

    return {
        "changed": sorted(changed_actual),
        "registry_changed": sorted(registry_changed),
        "idempotent": not changed_actual and before_hubs == after_hubs,
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
        load(args.before_overrides),
        load(args.after_overrides),
        load(args.before_hubs),
        load(args.after_hubs),
        load(args.before_history),
        load(args.report),
        load(args.changes),
    )
    print(
        "FIELD_DOMAIN_REFRESH_GUARD "
        f"changed={len(result['changed'])} registry={len(result['registry_changed'])} "
        f"idempotent={'true' if result['idempotent'] else 'false'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
