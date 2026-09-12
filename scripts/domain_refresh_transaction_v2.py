#!/usr/bin/env python3
"""Atomic authoritative hub -> Provider v3 domain publication.

Domain Refresh is address authority, not provider repair. A successful run:
1. resolves the current terminal only from authoritative hub/channel/redirect sources;
2. persists that terminal in provider-overrides, provider-domain-history and provider-hubs;
3. reconciles only domain-routing derivatives connected to the previous terminal;
4. rebuilds the complete managed CONFIG DATA block for changed Provider v3 bundles;
5. republishes changed bundles with their existing source-qualified namespace;
6. leaves every byte outside PROVIDER.*.CONFIG.V1 (including all Core Lego) unchanged.

Manifest/release version synchronization is intentionally performed by the workflow
after this transaction, once the domain mutation and Provider CONFIG rebuild pass.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
from typing import Any

import materialize_provider_v3_all as allmat
import refresh_authoritative_hub_domains as refresh
import resolve_provider_hubs as resolver
from provider_patch_blocks import (
    decode_managed_data,
    owned_span,
    replace_provider_fix,
    validate_managed_fixes,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "provider-overrides.json"
REGISTRY_PATH = ROOT / "provider-hubs.json"
HISTORY_PATH = ROOT / "provider-domain-history.json"
MANIFEST_PATH = ROOT / "manifest.json"
MATERIALIZATION_PATH = ROOT / "provider-v3-materialization.json"
STATIC_KNOWLEDGE_PATH = ROOT / "automation" / "provider-v3-static-knowledge.json"
PROVIDERS_DIR = ROOT / "providers"

DOMAIN_PATCH_FIELDS = {
    "official_site",
    "official_hub",
    "domain_substitutions",
    "replacements",
    "runtime_domain_replacements",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: object required")
    return value


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical(value: object) -> str:
    return str(value or "").strip().casefold()


def domain_host(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return resolver.host(raw if "://" in raw else f"https://{raw}")


def _authoritative_hub_configs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return hub configs where provider-hubs.json outranks legacy embedded config.

    resolve_provider_hubs.merge_hub_registry historically starts from
    provider-overrides.official_domain_hubs and then uses setdefault for the curated
    registry. That permits stale embedded values to shadow a newer registry row.
    Domain Refresh must invert that authority: curated provider-hubs is the current
    address registry; legacy-only entries remain available only when no curated row
    exists.
    """
    legacy = resolver.merge_hub_registry(config)
    clean_config = {"provider_patches": config.get("provider_patches") or {}}
    curated = resolver.merge_hub_registry(clean_config)
    legacy.update(curated)
    return legacy


def _registry_rows(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = registry.get("providers") or {}
    if isinstance(raw, dict):
        return {
            canonical(provider_id): row
            for provider_id, row in raw.items()
            if isinstance(row, dict) and canonical(provider_id)
        }
    if isinstance(raw, list):
        return {
            canonical(row.get("id")): row
            for row in raw
            if isinstance(row, dict) and canonical(row.get("id"))
        }
    raise SystemExit("provider-hubs.json providers must be object or array")


def _unique_urls(values: list[object]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value or not resolver.is_http_url(value):
            continue
        identity = value.rstrip("/").casefold()
        if identity in seen:
            continue
        seen.add(identity)
        output.append(value)
    return output


def sync_registry_terminal(registry: dict[str, Any], provider_id: str, terminal: str) -> bool:
    """Persist current terminal while retaining older curated direct fallbacks."""
    rows = _registry_rows(registry)
    row = rows.get(canonical(provider_id))
    if not isinstance(row, dict):
        return False
    terminal = str(terminal or "").strip().rstrip("/")
    if not resolver.is_http_url(terminal):
        return False
    terminal_host = domain_host(terminal)
    if not terminal_host:
        return False

    normalized = terminal + "/"
    before = json.dumps(row, ensure_ascii=False, sort_keys=True)
    old_direct = row.get("direct")
    old_candidates = list(row.get("direct_candidates") or [])
    row["direct"] = normalized
    row["direct_candidates"] = _unique_urls([normalized, old_direct, *old_candidates])

    allowed: list[str] = []
    for value in [terminal_host, *(row.get("allowed_terminal_hosts") or [])]:
        item = domain_host(value)
        if item and item not in allowed:
            allowed.append(item)
    for value in row["direct_candidates"]:
        item = domain_host(value)
        if item and item not in allowed:
            allowed.append(item)
    row["allowed_terminal_hosts"] = allowed
    return before != json.dumps(row, ensure_ascii=False, sort_keys=True)


def _rewrite_connected_domain_map(
    mapping: dict[str, Any],
    before_host: str,
    next_host: str,
) -> bool:
    """Redirect only chains that actually lead to the previous site terminal."""
    if not next_host:
        return False
    original = json.dumps(mapping, ensure_ascii=False, sort_keys=True)
    edges = {
        domain_host(source): domain_host(target)
        for source, target in mapping.items()
        if domain_host(source) and domain_host(target)
    }

    def reaches_previous(value: object) -> bool:
        current = domain_host(value)
        seen: set[str] = set()
        for _ in range(16):
            if not current or current in seen:
                return False
            if current == before_host:
                return True
            seen.add(current)
            current = edges.get(current, "")
        return False

    for source in list(mapping):
        source_host = domain_host(source)
        if source_host == next_host:
            # A current terminal can never be a replacement source. Keeping it
            # would recreate fs27 -> fs16 style rollback cycles.
            mapping.pop(source, None)
            continue
        if before_host and reaches_previous(mapping.get(source)):
            mapping[source] = next_host

    if before_host and before_host != next_host:
        mapping[before_host] = next_host
    return original != json.dumps(mapping, ensure_ascii=False, sort_keys=True)


def sync_patch_domain_authority(
    patch: dict[str, Any],
    cfg: dict[str, Any],
    terminal: str,
) -> list[str]:
    """Update only address-authority DATA and its execution-domain derivatives."""
    changed: list[str] = []
    before_site = str(patch.get("official_site") or "").strip().rstrip("/")
    next_site = str(terminal or "").strip().rstrip("/")
    before_host = domain_host(before_site)
    next_host = domain_host(next_site)
    if not next_site or not next_host:
        return changed

    if before_site != next_site:
        patch["official_site"] = next_site
        changed.append("official_site")

    hub = str(cfg.get("hub") or "").strip().rstrip("/")
    if hub and str(patch.get("official_hub") or "").strip().rstrip("/") != hub:
        patch["official_hub"] = hub
        changed.append("official_hub")

    # Runtime domain substitution is the execution authority consumed by the
    # ProviderBase DATA model. Ensure old terminal URLs can follow the new site.
    for name in ("runtime_domain_replacements", "domain_substitutions"):
        mapping = patch.get(name)
        if not isinstance(mapping, dict):
            mapping = {}
            patch[name] = mapping
        if _rewrite_connected_domain_map(mapping, before_host, next_host):
            changed.append(name)

    # Build-time replacements are preserved if present, but Domain Refresh does
    # not invent a new textual-rewrite layer solely for a domain move.
    replacements = patch.get("replacements")
    if isinstance(replacements, dict) and _rewrite_connected_domain_map(
        replacements, before_host, next_host
    ):
        changed.append("replacements")

    return sorted(set(changed))


def _config_fix_id(text: str, provider_id: str) -> str:
    fix_ids = validate_managed_fixes(text)
    expected = f"PROVIDER.{provider_id.upper()}.CONFIG.V1"
    if expected in fix_ids:
        return expected
    matches = [
        fix_id
        for fix_id in fix_ids
        if fix_id.startswith("PROVIDER.") and fix_id.endswith(".CONFIG.V1")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"{provider_id}: CONFIG Lego cardinality={len(matches)}")
    return matches[0]


def _data_digest(data: dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# DOMAIN_REFRESH_SOURCE_QUALIFIED_PUBLICATION_V3
def _safe_fragment(value: object) -> str:
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return cleaned[:120] or "provider"


def source_qualified_provider_name(provider_id: str, old_path: Path, digest: str) -> str:
    """Retain the publisher/source namespace while rotating content hash."""
    parts = old_path.stem.split("--")
    source = parts[-2] if len(parts) >= 3 else "nuvio"
    if source.endswith("-audit-quarantine"):
        source = source[: -len("-audit-quarantine")] or "nuvio"
    return f"{_safe_fragment(provider_id.casefold())}--{_safe_fragment(source)}--{digest[:16]}.js"


def _generation(rows: list[dict[str, Any]]) -> str:
    aggregate = hashlib.sha256()
    for row in rows:
        provider_id = canonical(row.get("provider"))
        digest = str(row.get("sha256") or "")
        if not provider_id or len(digest) != 64:
            raise RuntimeError(f"invalid materialization row: {provider_id!r}")
        aggregate.update(provider_id.encode("utf-8"))
        aggregate.update(bytes.fromhex(digest))
    return aggregate.hexdigest()


def rebuild_provider_configs(provider_ids: list[str]) -> list[dict[str, str]]:
    """Rebuild complete CONFIG DATA for changed providers, preserving Core bytes."""
    if not provider_ids:
        return []
    manifest = load(MANIFEST_PATH)
    overrides = load(CONFIG_PATH)
    materialization = load(MATERIALIZATION_PATH)
    static = load(STATIC_KNOWLEDGE_PATH)

    manifest_rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    material_rows = [row for row in materialization.get("providers") or [] if isinstance(row, dict)]
    if len(manifest_rows) != 96 or len(material_rows) != 96:
        raise RuntimeError(
            f"domain publication requires 96/96 state: manifest={len(manifest_rows)} materialization={len(material_rows)}"
        )

    manifest_by_id = {canonical(row.get("id")): row for row in manifest_rows}
    material_by_id = {canonical(row.get("provider")): row for row in material_rows}
    patches = overrides.get("provider_patches") or {}
    capabilities = overrides.get("provider_capabilities") or {}
    static_rows = static.get("providers") or {}
    updates: list[dict[str, str]] = []

    for provider_id in sorted(set(canonical(value) for value in provider_ids if canonical(value))):
        entry = manifest_by_id.get(provider_id)
        report = material_by_id.get(provider_id)
        patch = patches.get(provider_id)
        capability = capabilities.get(provider_id)
        static_row = static_rows.get(provider_id)
        if not all(isinstance(value, dict) for value in (entry, report, patch, capability, static_row)):
            raise RuntimeError(f"{provider_id}: incomplete Provider v3 structured state")

        model = allmat.provider_model(provider_id, patch, capability, static_row)
        data = allmat.build_provider_data_model(
            provider_id,
            entry,
            known_site=model.get("knownSite"),
            provider_model=model,
        )

        old_rel = str(entry.get("filename") or "")
        old_path = ROOT / old_rel
        if not old_rel.startswith("providers/") or not old_path.is_file():
            raise RuntimeError(f"{provider_id}: published provider missing: {old_rel}")
        before = old_path.read_text(encoding="utf-8")
        fix_id = _config_fix_id(before, provider_id)
        before_span = owned_span(before, fix_id)
        if before_span is None:
            raise RuntimeError(f"{provider_id}: CONFIG span missing")
        previous_data = decode_managed_data(before, fix_id)
        if canonical(previous_data.get("providerId")) != provider_id:
            raise RuntimeError(f"{provider_id}: CONFIG providerId mismatch")

        payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        after = replace_provider_fix(
            before,
            fix_id,
            f"const NIAKVIO_PROVIDER_MODEL = Object.freeze({payload});",
            data=data,
        )
        validate_managed_fixes(after)
        after_span = owned_span(after, fix_id)
        if after_span is None:
            raise RuntimeError(f"{provider_id}: CONFIG span lost")
        if before[: before_span[0]] + before[before_span[1] :] != after[: after_span[0]] + after[after_span[1] :]:
            raise RuntimeError(f"{provider_id}: domain refresh changed bytes outside CONFIG Lego")

        raw = after.encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        new_rel = f"providers/{source_qualified_provider_name(provider_id, old_path, digest)}"
        new_path = ROOT / new_rel
        new_path.write_bytes(raw)
        entry["filename"] = new_rel
        report["file"] = new_rel
        report["sha256"] = digest
        report["providerDataSha256"] = _data_digest(data)
        if old_path != new_path and old_path.exists():
            old_path.unlink()
        updates.append({"provider": provider_id, "from": old_rel, "to": new_rel})

    materialization["generation"] = _generation(material_rows)
    materialization["providerCount"] = 96
    materialization["expectedProviderCount"] = 96
    materialization["domainAuthorityOnlyUpdate"] = True
    materialization["domainAuthorityUpdatedProviders"] = [row["provider"] for row in updates]
    write(MANIFEST_PATH, manifest)
    write(MATERIALIZATION_PATH, materialization)
    return updates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="health-output/provider-hub-report.json")
    parser.add_argument("--changes-output", default="health-output/domain-site-changes.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mode", choices=("quick", "deep"), default="quick")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()

    config = load(CONFIG_PATH)
    registry = load(REGISTRY_PATH)
    history = load(HISTORY_PATH)
    history.setdefault("schema_version", 1)
    history_rows = history.setdefault("providers", {})
    if not isinstance(history_rows, dict):
        raise SystemExit("provider-domain-history.json providers must be object")

    hubs = _authoritative_hub_configs(config)
    selected = {canonical(value) for value in args.provider if canonical(value)}
    work: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for provider_id, cfg in sorted(hubs.items()):
        if selected and provider_id not in selected:
            continue
        if not resolver.has_authoritative_hub_source(cfg):
            continue
        disabled = str(cfg.get("manifest_status") or "").casefold() in {
            "désactivé",
            "desactive",
            "disabled",
        }
        if disabled and not args.include_disabled:
            continue
        work.append((provider_id, dict(cfg), history_rows.setdefault(provider_id, {})))

    report: dict[str, Any] = {
        "schema_version": 5,
        "generated_at": resolver.now_iso(),
        "mode": args.mode,
        "authority": "provider-hubs-authoritative-terminal",
        "terminal_validation_required": False,
        "providers": {},
        "applied": 0,
    }
    changed_provider_ids: list[str] = []
    registry_changed_ids: list[str] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 16))) as pool:
        futures = {
            pool.submit(
                refresh.resolve_authoritative_hub_domain,
                provider_id,
                cfg,
                history_row,
                args.mode,
                args.timeout,
            ): (provider_id, cfg, history_row)
            for provider_id, cfg, history_row in work
        }
        for future in concurrent.futures.as_completed(futures):
            provider_id, cfg, history_row = futures[future]
            try:
                item = future.result()
            except Exception as exc:  # fail closed per provider, keep the rest observable
                item = {
                    "provider_id": provider_id,
                    "status": "hub_unresolved",
                    "reason": "exception",
                    "terminal_probe_skipped": True,
                    "error": f"{type(exc).__name__}: {exc}",
                }

            if args.apply and item.get("status") == "site_authoritative":
                patches = config.get("provider_patches") or {}
                patch = patches.get(provider_id) if isinstance(patches, dict) else None
                if not isinstance(patch, dict):
                    item["status"] = "hub_unresolved"
                    item["reason"] = "missing_provider_patch_domain_refresh_may_not_add_provider"
                else:
                    terminal = str(item.get("official_site") or "").strip().rstrip("/")
                    patch_fields = sync_patch_domain_authority(patch, cfg, terminal)
                    registry_changed = sync_registry_terminal(registry, provider_id, terminal)
                    if registry_changed:
                        registry_changed_ids.append(provider_id)
                    if patch_fields:
                        changed_provider_ids.append(provider_id)
                        refresh._update_history_on_change(history_row, item)
                        report["applied"] += 1
                    item["applied_patch_fields"] = patch_fields
                    item["registry_synced"] = registry_changed
            report["providers"][provider_id] = item

    bundle_updates: list[dict[str, str]] = []
    if args.apply:
        # Persist structured authority first so the CONFIG rebuild reads exactly
        # the same DATA that will be committed.
        write(CONFIG_PATH, config)
        write(REGISTRY_PATH, registry)
        history["updated_at"] = resolver.now_iso()
        write(HISTORY_PATH, history)
        bundle_updates = rebuild_provider_configs(changed_provider_ids)

    changes = {
        "schema_version": 2,
        "changed": sorted(set(changed_provider_ids)),
        "registry_changed": sorted(set(registry_changed_ids)),
        "bundle_updates": bundle_updates,
        "allowed_patch_fields": sorted(DOMAIN_PATCH_FIELDS),
        "core_mutation": False,
    }
    output = ROOT / args.output
    changes_output = ROOT / args.changes_output
    write(output, report)
    write(changes_output, changes)

    resolved = sum(
        1 for row in report["providers"].values() if row.get("status") == "site_authoritative"
    )
    unresolved = sum(
        1 for row in report["providers"].values() if row.get("status") == "hub_unresolved"
    )
    print(
        "FIELD_DOMAIN_REFRESH_V2 "
        f"resolved={resolved} unresolved={unresolved} applied={len(set(changed_provider_ids))} "
        f"registry={len(set(registry_changed_ids))} bundles={len(bundle_updates)} "
        "terminal_probe=false core_mutation=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
