#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Persist high-confidence DNS migration discoveries and repatch staged JS.

Only same-brand candidates above the configured threshold and supported by a
real HTTP redirect are accepted automatically. The exact old host is replaced
with the exact discovered host; no api. subdomain or unrelated route is guessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from apply_provider_overrides import apply_overrides

ROOT = Path(__file__).resolve().parents[1]


def canonical(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def replace_host_in_url(value: str, old_host: str, new_host: str) -> str:
    try:
        parsed = urlsplit(value)
    except Exception:
        return value
    if (parsed.hostname or "").casefold() != old_host.casefold():
        return value
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit((parsed.scheme, f"{new_host}{port}", parsed.path, parsed.query, parsed.fragment))


def accepted_migration(decision: dict, config: dict) -> dict | None:
    migration = decision.get("migration_candidate")
    if not isinstance(migration, dict):
        return None
    migration_config = config.get("migration_discovery") or {}
    if migration_config.get("automatic_override") is not True:
        return None
    threshold = int(migration_config.get("minimum_confidence", 80))
    if int(migration.get("confidence", 0)) < threshold:
        return None
    if migration_config.get("same_brand_required", True) and not migration.get("same_brand"):
        return None
    evidence = {str(item) for item in migration.get("evidence") or []}
    if not any(item.startswith("http_redirect_") for item in evidence):
        return None
    old_host = str(migration.get("original_host") or "").strip().lower()
    new_host = str(migration.get("host") or "").strip().lower()
    if not old_host or not new_host or old_host == new_host:
        return None
    return migration


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    parser.add_argument("--report", type=Path, default=ROOT / "health-output" / "dns-preflight-report.json")
    parser.add_argument("--config", type=Path, default=ROOT / "health-config.json")
    parser.add_argument("--overrides", type=Path, default=ROOT / "provider-overrides.json")
    args = parser.parse_args()

    stage = args.stage.resolve()
    registry_path = stage / "candidates.json"
    report = json.loads(args.report.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8")).get("dns_preflight") or {}
    overrides = json.loads(args.overrides.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    by_key = {str(item.get("key")): item for item in registry.get("candidates", []) if isinstance(item, dict)}
    changes: list[dict] = []

    provider_patches = overrides.setdefault("provider_patches", {})
    for provider in report.get("providers", []):
        if not isinstance(provider, dict):
            continue
        migration = accepted_migration(provider.get("decision") or {}, config)
        if not migration:
            continue
        provider_id = canonical(provider.get("canonical_id"))
        candidate = by_key.get(str(provider.get("key")))
        if not provider_id or not candidate:
            continue
        old_host = str(migration["original_host"]).lower()
        new_host = str(migration["host"]).lower()
        patch = provider_patches.setdefault(provider_id, {})
        replacements = patch.setdefault("replacements", {})
        runtime = patch.setdefault("runtime_domain_replacements", {})
        changed = False
        if replacements.get(old_host) != new_host:
            replacements[old_host] = new_host
            changed = True
        if runtime.get(old_host) != new_host:
            runtime[old_host] = new_host
            changed = True

        fixed = patch.get("fixed_endpoint")
        if isinstance(fixed, dict):
            for field in ("api", "referer"):
                current = fixed.get(field)
                if isinstance(current, str):
                    updated = replace_host_in_url(current, old_host, new_host)
                    if updated != current:
                        fixed[field] = updated
                        changed = True

        if not changed:
            continue
        notes = patch.setdefault("notes", [])
        note = f"Automatically migrated {old_host} to {new_host} after French ISP DNS/HTTP preflight redirect validation."
        if note not in notes:
            notes.append(note)
        changes.append({
            "provider": provider_id,
            "key": provider.get("key"),
            "from": old_host,
            "to": new_host,
            "confidence": migration.get("confidence"),
            "evidence": migration.get("evidence") or [],
        })

    if not changes:
        print("DNS migration overrides: no safe automatic changes")
        return 0

    args.overrides.write_text(json.dumps(overrides, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Repatch every staged variant sharing an affected canonical provider id.
    # A migration may be discovered by aio:animepahe while yoru:animepahe is a
    # different staged artefact containing the same obsolete host. Validating
    # immediately after patching only the discovering candidate would therefore
    # reject the still-unpatched sibling variant.
    changes_by_provider: dict[str, list[dict]] = {}
    for change in changes:
        changes_by_provider.setdefault(change["provider"], []).append(change)

    providers_root = (stage / "providers").resolve()
    repatched_variants = 0
    for candidate in registry.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        candidate_provider = canonical(candidate.get("canonical_id") or candidate.get("upstream_id"))
        provider_changes = changes_by_provider.get(candidate_provider)
        if not provider_changes:
            continue

        local_path = (stage / str(candidate.get("local_path") or "")).resolve()
        local_path.relative_to(providers_root)
        original = local_path.read_bytes()
        patched, records = apply_overrides(candidate_provider, original, phase="discovery")
        local_path.write_bytes(patched)
        candidate["sha256"] = hashlib.sha256(patched).hexdigest()

        existing_records = candidate.setdefault("local_patches", [])
        for record in records:
            if record not in existing_records:
                existing_records.append(record)

        existing_migrations = candidate.setdefault("dns_migration_overrides", [])
        for change in provider_changes:
            if change not in existing_migrations:
                existing_migrations.append(change)
        repatched_variants += 1

    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"DNS migration overrides applied: {len(changes)}")
    for change in changes:
        print(f"- {change['provider']}: {change['from']} -> {change['to']} ({change['confidence']})")
    print(f"Staged provider variants repatched: {repatched_variants}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
