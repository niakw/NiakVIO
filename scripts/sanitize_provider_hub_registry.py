#!/usr/bin/env python3
"""Remove non-concrete address constructors from current provider hub/history state.

This is a conservative preflight for the scheduled Domain Refresh. It never
invents a provider address: when `direct` is invalid it may only reuse the first
already-curated concrete direct candidate, otherwise it becomes null. Invalid
history entries are removed; the newest concrete historical entry may replace an
invalid current entry so stale JS/template constructors cannot remain LKG state.

The CLI is scoped by the current manifest. Historical provider identities may
remain archived in provider-hubs/history, but Domain Refresh must never mutate
those rows or turn them back into publication candidates.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
from pathlib import Path
from typing import Any

PLACEHOLDER_TOKENS = ("${", "{{", "}}", "<%", "%>", "{", "}")


def concrete_http(value: object) -> bool:
    raw = str(value or "").strip()
    if not raw or any(token in raw for token in PLACEHOLDER_TOKENS):
        return False
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.casefold()
    return not any(token in hostname for token in ("$", "{", "}"))


def host(value: object) -> str:
    raw = str(value or "").strip()
    if "://" not in raw:
        raw = "https://" + raw
    return (urllib.parse.urlparse(raw).hostname or "").casefold().strip(".")


def canonical(value: object) -> str:
    return str(value or "").strip().casefold()


def current_provider_ids(manifest_path: Path) -> set[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = payload.get("scrapers") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise AssertionError(f"{manifest_path}: non-empty scrapers list required")
    ids = {
        canonical(row.get("id"))
        for row in rows
        if isinstance(row, dict) and canonical(row.get("id"))
    }
    if len(ids) != len(rows):
        raise AssertionError(f"{manifest_path}: duplicate or missing provider id")
    return ids


def dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.rstrip("/").casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def sanitize(
    document: dict[str, Any],
    provider_ids: set[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    providers = document.get("providers")
    if not isinstance(providers, dict):
        raise AssertionError("provider-hubs.json providers must be an object")

    scoped = {canonical(value) for value in provider_ids} if provider_ids is not None else None
    changed: list[str] = []
    for provider_id, row in providers.items():
        provider_key = canonical(provider_id)
        if scoped is not None and provider_key not in scoped:
            continue
        if not isinstance(row, dict):
            continue
        before = json.dumps(row, ensure_ascii=False, sort_keys=True)

        candidates = dedupe([
            str(value).strip()
            for value in row.get("direct_candidates") or []
            if concrete_http(value)
        ])
        row["direct_candidates"] = candidates

        direct = row.get("direct")
        if not concrete_http(direct):
            row["direct"] = candidates[0] if candidates else None
        elif str(direct).rstrip("/").casefold() not in {
            value.rstrip("/").casefold() for value in candidates
        }:
            row["direct_candidates"] = dedupe([str(direct).strip(), *candidates])

        allowed: list[str] = []
        for value in row.get("allowed_terminal_hosts") or []:
            raw = str(value or "").strip().casefold().strip(".")
            if not raw or any(token in raw for token in PLACEHOLDER_TOKENS):
                continue
            if raw not in allowed:
                allowed.append(raw)
        for value in row.get("direct_candidates") or []:
            hostname = host(value)
            if hostname and hostname not in allowed:
                allowed.append(hostname)
        row["allowed_terminal_hosts"] = allowed

        after = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if before != after:
            changed.append(str(provider_id))

    return document, sorted(changed)


def sanitize_history(
    document: dict[str, Any],
    provider_ids: set[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    providers = document.get("providers")
    if not isinstance(providers, dict):
        raise AssertionError("provider-domain-history.json providers must be an object")

    scoped = {canonical(value) for value in provider_ids} if provider_ids is not None else None
    changed: list[str] = []
    for provider_id, row in providers.items():
        provider_key = canonical(provider_id)
        if scoped is not None and provider_key not in scoped:
            continue
        if not isinstance(row, dict):
            continue
        before = json.dumps(row, ensure_ascii=False, sort_keys=True)

        previous: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for entry in row.get("previous") or []:
            if not isinstance(entry, dict) or not concrete_http(entry.get("url")):
                continue
            key = str(entry.get("url") or "").rstrip("/").casefold()
            if key in seen_urls:
                continue
            seen_urls.add(key)
            previous.append(entry)

        current = row.get("current")
        if isinstance(current, dict) and concrete_http(current.get("url")):
            current_key = str(current.get("url") or "").rstrip("/").casefold()
            previous = [
                entry for entry in previous
                if str(entry.get("url") or "").rstrip("/").casefold() != current_key
            ]
            row["current"] = current
        elif previous:
            row["current"] = previous.pop(0)
        else:
            row.pop("current", None)
        row["previous"] = previous

        after = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if before != after:
            changed.append(str(provider_id))

    return document, sorted(changed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="provider-hubs.json")
    parser.add_argument("--history", default="provider-domain-history.json")
    parser.add_argument("--manifest", default="manifest.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    provider_ids = current_provider_ids(Path(args.manifest))

    registry_path = Path(args.registry)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry, registry_changed = sanitize(registry, provider_ids)

    history_path = Path(args.history)
    history = json.loads(history_path.read_text(encoding="utf-8"))
    history, history_changed = sanitize_history(history, provider_ids)

    if args.check and (registry_changed or history_changed):
        details = []
        if registry_changed:
            details.append("registry=" + ",".join(registry_changed))
        if history_changed:
            details.append("history=" + ",".join(history_changed))
        raise SystemExit("provider hub state requires sanitization: " + " ".join(details))

    if not args.check:
        if registry_changed:
            registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if history_changed:
            history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "FIELD_HUB_REGISTRY_SANITIZE "
        f"scope={len(provider_ids)} "
        f"registry_changed={len(registry_changed)} "
        f"registry_providers={','.join(registry_changed) if registry_changed else '-'} "
        f"history_changed={len(history_changed)} "
        f"history_providers={','.join(history_changed) if history_changed else '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
