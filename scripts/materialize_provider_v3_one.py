#!/usr/bin/env python3
"""Materialize exactly one Provider v3 bundle from current structured DATA.

Used by the strict sequential live reconstruction gate. The provider's candidate
bundle is probed, its DATA is finalized, then this script immediately rebuilds the
same provider from the finalized DATA before the workflow may advance to the next
provider.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import materialize_provider_v3_all as allmat

ROOT = Path(__file__).resolve().parents[1]


def _host(value: object) -> str:
    raw = str(value or "").strip().casefold()
    if not raw:
        return ""
    if "://" in raw:
        try:
            from urllib.parse import urlparse
            return str(urlparse(raw).hostname or "").strip().casefold()
        except ValueError:
            return ""
    return raw.split("/", 1)[0].strip().casefold()


def _current_model(static_knowledge: dict[str, object], provider_id: str) -> dict[str, object]:
    providers = static_knowledge.get("providers")
    if not isinstance(providers, dict):
        return {}
    row = providers.get(provider_id)
    if not isinstance(row, dict):
        return {}
    model = row.get("model")
    return model if isinstance(model, dict) else {}


def _current_authority_hosts(model: dict[str, object]) -> set[str]:
    values: list[object] = [
        model.get("knownSite"),
        model.get("officialSite"),
        model.get("officialHub"),
        model.get("officialApi"),
        model.get("fixedApi"),
    ]
    recipe = model.get("apiRecipe")
    if isinstance(recipe, dict):
        values.extend(
            recipe.get(key)
            for key in ("base", "api", "baseUrl", "endpoint", "statusUrl")
        )
    return {_host(value) for value in values if _host(value)}


def reconcile_provider_authority(
    overrides: dict[str, object],
    static_knowledge: dict[str, object],
    provider_id: str,
) -> list[str]:
    """Project current canonical Provider DATA over stale historical overrides.

    ``automation/provider-v3-static-knowledge.json`` is enriched immediately before
    the strict sequential loop and is therefore the current canonical DATA for the
    provider being materialized. ``provider-overrides.json`` can still retain useful
    historical aliases and migration evidence, but an old endpoint/recipe must not
    override that current model or redirect one of its canonical hosts away from the
    current terminal.

    Only provider N is touched here. This preserves the strict N -> proof -> N+1
    contract instead of pre-mutating future providers.
    """
    canonical_id = allmat.canonical_id(provider_id)
    patches = overrides.get("provider_patches")
    if not isinstance(patches, dict):
        return []
    patch = patches.get(canonical_id)
    if not isinstance(patch, dict):
        return []
    model = _current_model(static_knowledge, canonical_id)
    if not model:
        return []

    changed = False

    def assign(key: str, value: object) -> None:
        nonlocal changed
        text = str(value or "").strip()
        if not text:
            return
        if patch.get(key) != text:
            patch[key] = text
            changed = True

    assign("official_site", model.get("officialSite") or model.get("knownSite"))
    assign("official_hub", model.get("officialHub"))
    assign("official_api", model.get("officialApi"))

    fixed_api = str(model.get("fixedApi") or "").strip()
    if fixed_api:
        fixed = patch.get("fixed_endpoint")
        fixed = copy.deepcopy(fixed) if isinstance(fixed, dict) else {}
        if fixed.get("api") != fixed_api:
            fixed["api"] = fixed_api
            patch["fixed_endpoint"] = fixed
            changed = True

    recipe = model.get("apiRecipe")
    if isinstance(recipe, dict) and recipe:
        canonical_recipe = copy.deepcopy(recipe)
        if patch.get("api_recipe") != canonical_recipe:
            patch["api_recipe"] = canonical_recipe
            changed = True

    # Historical replacement graphs may contain the reverse of the current
    # transition (e.g. current.example -> old.example). Keep aliases and unrelated
    # evidence, but never let a canonical current host be redirected to a host that
    # is outside the current model's authority set.
    authority_hosts = _current_authority_hosts(model)
    if authority_hosts:
        for key in ("replacements", "runtime_domain_replacements"):
            mapping = patch.get(key)
            if not isinstance(mapping, dict):
                continue
            cleaned: dict[object, object] = {}
            for source, target in mapping.items():
                source_host = _host(source)
                target_host = _host(target)
                if (
                    source_host in authority_hosts
                    and target_host
                    and target_host not in authority_hosts
                ):
                    changed = True
                    continue
                cleaned[source] = target
            if cleaned != mapping:
                patch[key] = cleaned

        substitutions = patch.get("domain_substitutions")
        if isinstance(substitutions, dict):
            cleaned_substitutions: dict[object, object] = {}
            for source, target in substitutions.items():
                source_host = _host(source)
                target_host = _host(target)
                if (
                    source_host in authority_hosts
                    and target_host
                    and target_host not in authority_hosts
                ):
                    changed = True
                    continue
                cleaned_substitutions[source] = target
            if cleaned_substitutions != substitutions:
                patch["domain_substitutions"] = cleaned_substitutions

    if changed:
        print(
            "FIELD_PROVIDER_STATIC_AUTHORITY_RECONCILED "
            f"providers=1 ids={canonical_id}",
            flush=True,
        )
        return [canonical_id]
    return []


def reconcile_domain_substitutions(
    overrides: dict[str, object],
    *,
    provider_id: str | None = None,
) -> list[str]:
    """Collapse stale domain substitutions through current replacement DATA.

    Some providers retain an older terminal in ``domain_substitutions`` while
    ``replacements`` / ``runtime_domain_replacements`` already know the newer
    terminal. ProviderBase consumes ``domain_substitutions`` directly, so leaving
    that chain uncollapsed can make a freshly rebuilt provider call a blocked old
    domain even when ``official_site`` is already correct.

    We only rewrite substitution chains that are already connected to replacement
    DATA; unrelated replacement entries are not promoted into routing authority.
    When ``provider_id`` is supplied, only provider N may be mutated.
    """
    patches = overrides.get("provider_patches")
    if not isinstance(patches, dict):
        return []
    scope = allmat.canonical_id(provider_id) if provider_id else None
    changed: list[str] = []
    for current_provider_id, patch in patches.items():
        canonical_current = allmat.canonical_id(str(current_provider_id))
        if scope and canonical_current != scope:
            continue
        if not isinstance(patch, dict):
            continue
        raw_substitutions = patch.get("domain_substitutions")
        if not isinstance(raw_substitutions, dict) or not raw_substitutions:
            continue

        redirects: dict[str, str] = {}
        for key in ("replacements", "runtime_domain_replacements"):
            mapping = patch.get(key)
            if not isinstance(mapping, dict):
                continue
            for source, target in mapping.items():
                source_host = _host(source)
                target_host = _host(target)
                if source_host and target_host:
                    redirects[source_host] = target_host
        if not redirects:
            continue

        def terminal(host: str) -> str:
            current = _host(host)
            seen: set[str] = set()
            for _ in range(12):
                if not current or current in seen:
                    break
                seen.add(current)
                next_host = _host(redirects.get(current))
                if not next_host or next_host == current:
                    break
                current = next_host
            return current

        substitutions = {
            _host(source): _host(target)
            for source, target in raw_substitutions.items()
            if _host(source) and _host(target)
        }
        original = dict(substitutions)
        original_targets = set(substitutions.values())

        for source, target in list(substitutions.items()):
            substitutions[source] = terminal(target)

        # If an old substitution target itself now redirects to a newer terminal,
        # preserve that continuation so URLs already carrying the old target are
        # also normalized by ProviderBase.
        for source, target in redirects.items():
            if source in substitutions or source in original_targets:
                substitutions[source] = terminal(target)

        if substitutions == original:
            continue
        patch["domain_substitutions"] = dict(sorted(substitutions.items()))
        changed.append(canonical_current)

    if changed:
        print(
            "FIELD_PROVIDER_DOMAIN_SUBSTITUTIONS_RECONCILED "
            f"providers={len(changed)} ids={','.join(sorted(changed))}",
            flush=True,
        )
    return changed


def materialize_one(provider_id: str) -> dict[str, object]:
    provider_id = allmat.canonical_id(provider_id)
    manifest = allmat.load(allmat.DEFAULT_SOURCE_MANIFEST)
    overrides = allmat.load(allmat.DEFAULT_OVERRIDES)
    static_knowledge = allmat.load(allmat.DEFAULT_STATIC_KNOWLEDGE)

    authority_changed = reconcile_provider_authority(
        overrides,
        static_knowledge,
        provider_id,
    )
    changed_domains = reconcile_domain_substitutions(
        overrides,
        provider_id=provider_id,
    )
    if authority_changed or changed_domains:
        allmat.write_json(allmat.DEFAULT_OVERRIDES, overrides)

    patches = overrides.get("provider_patches") or {}
    capabilities = overrides.get("provider_capabilities") or {}
    static_rows = static_knowledge.get("providers") or {}

    entry = next(
        (
            row for row in manifest.get("scrapers") or []
            if isinstance(row, dict)
            and allmat.canonical_id(str(row.get("id") or "")) == provider_id
        ),
        None,
    )
    if not isinstance(entry, dict):
        raise ValueError(f"{provider_id}: manifest row not found")
    patch = patches.get(provider_id)
    capability = capabilities.get(provider_id)
    static_row = static_rows.get(provider_id)
    if not isinstance(patch, dict) or not isinstance(capability, dict) or not isinstance(static_row, dict):
        raise ValueError(f"{provider_id}: incomplete structured DATA")

    allmat.normalize_anime_transport_compatibility(entry)
    model = allmat.provider_model(provider_id, patch, capability, static_row)
    seed = allmat.build_clean_provider_seed(
        provider_id,
        entry,
        known_site=model.get("knownSite"),
        provider_model=model,
    )
    base, stripped = allmat.build_base_from_seed(
        provider_id,
        seed,
        overrides_path=allmat.DEFAULT_OVERRIDES,
    )
    data = allmat.build_provider_data_model(
        provider_id,
        entry,
        known_site=model.get("knownSite"),
        provider_model=model,
    )
    bundle = allmat.compose_provider_bundle(provider_id, base, data)
    bundle, applied = allmat.apply_overrides(
        provider_id,
        bundle,
        phase="discovery",
        include_global_core=True,
        config_path=allmat.DEFAULT_OVERRIDES,
    )
    text = bundle.decode("utf-8", errors="strict")

    if text.count("/* BEGIN NIAKVIO_PROVIDER */") != 1:
        raise ValueError(f"{provider_id}: BEGIN PROVIDER cardinality")
    if text.count("/* END NIAKVIO_PROVIDER */") != 1:
        raise ValueError(f"{provider_id}: END PROVIDER cardinality")
    if not text.rstrip().endswith("/* END NIAKVIO_PROVIDER */"):
        raise ValueError(f"{provider_id}: bytes after END PROVIDER")
    if "searchParams.set(" in text or "searchParams.delete(" in text:
        raise ValueError(f"{provider_id}: QuickJS URLSearchParams mutation remains")

    fix_ids = allmat.validate_managed_fixes(text)
    config_id = f"PROVIDER.{provider_id.upper()}.CONFIG.V1"
    if config_id not in fix_ids:
        raise ValueError(f"{provider_id}: provider CONFIG Lego missing")
    core_ids = [fix_id for fix_id in fix_ids if fix_id.startswith("CORE.")]
    if not core_ids:
        raise ValueError(f"{provider_id}: no Core Lego materialized")

    boundary = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
    if text.count(boundary) != 1:
        raise ValueError(f"{provider_id}: Core boundary count={text.count(boundary)} expected=1")
    boundary_at = text.index(boundary)
    provider_fix_positions: list[int] = []
    core_fix_positions: list[int] = []
    for fix_id in fix_ids:
        span = allmat.owned_span(text, fix_id)
        if span is None:
            raise ValueError(f"{provider_id}: managed Lego span missing: {fix_id}")
        if fix_id.startswith("PROVIDER."):
            provider_fix_positions.append(span[0])
        elif fix_id.startswith("CORE."):
            core_fix_positions.append(span[0])
    if provider_fix_positions and max(provider_fix_positions) >= boundary_at:
        raise ValueError(f"{provider_id}: Provider Lego found after Core boundary")
    if core_fix_positions and min(core_fix_positions) <= boundary_at:
        raise ValueError(f"{provider_id}: Core Lego found before Core boundary")

    minimized = allmat.minimize_text(text)
    allmat.validate_transform(text, minimized.text)
    text = minimized.text
    bundle = text.encode("utf-8")
    if allmat.validate_managed_fixes(text) != fix_ids:
        raise ValueError(f"{provider_id}: minimizer changed managed Lego ownership")
    if text.count(boundary) != 1:
        raise ValueError(f"{provider_id}: minimizer changed Core boundary")

    digest = hashlib.sha256(bundle).hexdigest()
    filename = f"{provider_id}-{digest[:16]}.js"
    relative = f"providers/{filename}"
    allmat.DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    (allmat.DEFAULT_OUT / filename).write_bytes(bundle)
    entry["filename"] = relative
    entry["version"] = allmat.base_version(entry.get("version"))
    allmat.write_json(allmat.DEFAULT_SOURCE_MANIFEST, manifest)

    report = {
        "provider": provider_id,
        "file": relative,
        "sha256": digest,
        "providerDataSha256": hashlib.sha256(
            json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "baseStrippedGeneratedCore": bool(stripped),
        "fixIds": fix_ids,
        "coreCount": len(core_ids),
        "applied": applied,
        "deviceSpecificJs": False,
        "devices": ["tv", "mobile", "desktop"],
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
        "staticAuthorityReconciledProviders": authority_changed,
        "domainSubstitutionReconciledProviders": changed_domains,
        "minimizer": {
            "enabled": True,
            "savedBytes": minimized.saved_bytes,
            "transformedLines": minimized.transformed_lines,
            "skippedReason": minimized.skipped_reason,
        },
    }
    print(
        "FIELD_PROVIDER_V3_ONE_MATERIALIZED "
        f"provider={provider_id} sha256={digest[:16]} file={relative}"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider_id")
    args = parser.parse_args()
    materialize_one(args.provider_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
