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
import os
import re
import urllib.parse
from pathlib import Path

import materialize_provider_v3_all as allmat
from provider_security_hardening import assert_hardened, harden_bytes
from current_provider_scope import projection_active_provider_ids
from provider_materialization_generation import materialization_generation

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "provider-hubs.json"
PROVIDER_CATALOG = ROOT / "provider_catalog.json"


def upsert_materialization_report(report: dict[str, object]) -> dict[str, object]:
    """Keep targeted materialization ledger truthful and incrementally repairable.

    Full materialization owns the canonical complete ledger. Targeted
    materialization must nevertheless publish its exact row so reconciliation
    can converge without requiring stale historical rows. Inactive/stale rows
    are dropped, while expectedProviderCount remains the real active scope;
    therefore a partial ledger can never masquerade as complete.
    """
    path = allmat.DEFAULT_REPORT
    if path.is_file():
        document = allmat.load(path)
    else:
        document = {
            "schemaVersion": 3,
            "providers": [],
            "devicePolicy": {
                "providerJsIsDeviceAgnostic": True,
                "devices": ["tv", "mobile", "desktop"],
                "perDeviceProviderForkAllowed": False,
                "clientManifestProjectionAllowed": True,
            },
            "legacyProviderJsExecuted": False,
            "upstreamJsExecuted": False,
        }
    active = set(projection_active_provider_ids())
    existing = [
        dict(row)
        for row in (document.get("providers") or [])
        if isinstance(row, dict)
        and allmat.canonical_id(str(row.get("provider") or "")) in active
    ]
    provider_id = allmat.canonical_id(str(report.get("provider") or ""))
    replaced = False
    rows: list[dict[str, object]] = []
    for row in existing:
        if allmat.canonical_id(str(row.get("provider") or "")) == provider_id:
            rows.append(dict(report))
            replaced = True
        else:
            rows.append(row)
    if not replaced:
        rows.append(dict(report))
    document["schemaVersion"] = 3
    document["sourceSha"] = os.environ.get("GITHUB_SHA") or str(document.get("sourceSha") or "")
    document["context"] = allmat.materialization_context()
    document["providers"] = rows
    document["providerCount"] = len(rows)
    document["activeProviderIdentityCount"] = len(active)
    document["expectedProviderCount"] = len(active)
    document["generation"] = materialization_generation(rows)
    document["publication"] = allmat.materialization_context() in {"release", "main"}
    document["mainTouched"] = allmat.materialization_context() == "main"
    targeted = [
        allmat.canonical_id(str(value or ""))
        for value in (document.get("targetedMaterializedProviders") or [])
        if allmat.canonical_id(str(value or ""))
    ]
    document["targetedMaterializedProviders"] = sorted(set(targeted + [provider_id]))
    allmat.write_json(path, document)
    return document


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


def _registry_explicit_current_site(
    registry: dict[str, object],
    provider_id: str,
) -> str:
    providers = registry.get("providers")
    if not isinstance(providers, dict):
        return ""
    row = providers.get(provider_id)
    if not isinstance(row, dict):
        return ""
    if str(row.get("direct_authority") or "").strip().casefold() not in {"explicit_current", "operator_pin"}:
        return ""
    direct = str(row.get("direct") or "").strip().rstrip("/")
    return direct if direct.startswith(("http://", "https://")) else ""


def _normalize_runtime_option_domains(
    patch: dict[str, object],
    authority_hosts: set[str],
) -> bool:
    """Project stale provider-owned runtime option URLs onto current domain DATA.

    Domain Refresh owns address discovery and records old->current mappings in
    runtime_domain_replacements/domain_substitutions. Provider Lego options are
    executable DATA, so the materializer must not keep calling an obsolete host
    after current authority has moved. Only concrete HTTP(S) URLs whose source
    host is already mapped to a current authority host are rewritten.
    """
    redirects: dict[str, str] = {}
    for key in ("runtime_domain_replacements", "domain_substitutions"):
        mapping = patch.get(key)
        if not isinstance(mapping, dict):
            continue
        for source, target in mapping.items():
            source_host = _host(source)
            target_host = _host(target)
            if source_host and target_host and target_host in authority_hosts:
                redirects[source_host] = target_host
    if not redirects:
        return False

    def rewrite(value: object) -> tuple[object, bool]:
        if isinstance(value, dict):
            changed = False
            out: dict[object, object] = {}
            for key, child in value.items():
                next_child, child_changed = rewrite(child)
                out[key] = next_child
                changed = changed or child_changed
            return out, changed
        if isinstance(value, list):
            changed = False
            out: list[object] = []
            for child in value:
                next_child, child_changed = rewrite(child)
                out.append(next_child)
                changed = changed or child_changed
            return out, changed
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            return value, False
        try:
            parsed = urllib.parse.urlparse(value)
        except ValueError:
            return value, False
        source_host = str(parsed.hostname or "").strip().casefold()
        target_host = redirects.get(source_host)
        if not target_host:
            return value, False
        # Provider domain migrations are host-level. Preserve path/query/fragment
        # exactly while moving the executable option to the current authority.
        port = f":{parsed.port}" if parsed.port else ""
        rewritten = urllib.parse.urlunparse(
            (parsed.scheme or "https", target_host + port, parsed.path, parsed.params, parsed.query, parsed.fragment)
        )
        return rewritten, rewritten != value

    changed = False
    for key in ("provider_lego_options", "patch_script_options"):
        section = patch.get(key)
        if not isinstance(section, dict):
            continue
        rewritten, section_changed = rewrite(section)
        if section_changed:
            patch[key] = rewritten
            changed = True
    return changed


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
    registry: dict[str, object] | None = None,
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
    model = copy.deepcopy(_current_model(static_knowledge, canonical_id))
    if not model:
        return []

    # PROVIDER_DOMAIN_EXPLICIT_CURRENT_PRECEDENCE_V1
    # Domain Refresh's curated explicit-current registry is newer authority than
    # static Provider memory. Incremental materialization must never resurrect a
    # stale static host after Domain Refresh has selected a newer terminal.
    explicit_current_site = _registry_explicit_current_site(registry or {}, canonical_id)
    if explicit_current_site:
        model["knownSite"] = explicit_current_site
        model["officialSite"] = explicit_current_site

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

    # MATERIALIZER_EXECUTION_AUTHORITY_MONOTONIC_V26
    # Static knowledge may reconcile a stale, unproved address recipe, but it is
    # candidate memory rather than executable authority. A proof-owned recipe
    # (route proof >=5 + recipe proof >=5) is provider-specific live HTTP
    # evidence and must never be overwritten by an older static model. This is
    # the VidLove V1/api.vidlove.cc regression exposed after PR #127/#122 A/B.
    canonical_recipe = model.get("apiRecipe")
    patch_recipe = patch.get("api_recipe")
    patch_recipe_proof = (
        int(patch_recipe.get("proofModelVersion") or 0)
        if isinstance(patch_recipe, dict)
        else 0
    )
    patch_has_proven_recipe_authority = bool(
        isinstance(patch_recipe, dict)
        and int(patch.get("route_proof_version") or 0) >= 5
        and patch_recipe_proof >= 5
    )
    if (
        isinstance(canonical_recipe, dict)
        and isinstance(patch_recipe, dict)
        and not patch_has_proven_recipe_authority
    ):
        reconciled_recipe = copy.deepcopy(patch_recipe)
        canonical_base = str(
            canonical_recipe.get("base")
            or model.get("fixedApi")
            or model.get("officialApi")
            or ""
        ).strip()
        canonical_referer = str(
            canonical_recipe.get("referer")
            or canonical_recipe.get("referrer")
            or model.get("officialSite")
            or model.get("knownSite")
            or ""
        ).strip()
        if canonical_base and reconciled_recipe.get("base") != canonical_base:
            reconciled_recipe["base"] = canonical_base
        if canonical_referer and reconciled_recipe.get("referer") != canonical_referer:
            reconciled_recipe["referer"] = canonical_referer
        if reconciled_recipe != patch_recipe:
            patch["api_recipe"] = reconciled_recipe
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

        if _normalize_runtime_option_domains(patch, authority_hosts):
            changed = True

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



def project_authoritative_types(
    entry: dict[str, object],
    patch: dict[str, object],
    capability: dict[str, object],
) -> bool:
    """Project provider-owned semantic lanes before targeted materialization.

    published_types is durable publication authority. capability catalogue_types
    is the fallback for providers without an explicit narrowed publication set.
    This mirrors the full publication path and prevents targeted materialization
    from re-advertising unverified lanes.
    """
    raw = patch.get("published_types")
    if not isinstance(raw, list) or not raw:
        raw = capability.get("catalogue_types")
    semantic: list[str] = []
    for value in raw if isinstance(raw, list) else []:
        item = str(value or "").strip().casefold()
        if item in {"movie", "tv", "anime"} and item not in semantic:
            semantic.append(item)
    if not semantic:
        return False

    before_supported = [
        str(value or "").strip().casefold()
        for value in entry.get("supportedTypes") or []
        if str(value or "").strip().casefold() in {"movie", "tv", "anime"}
    ]
    had_canonical = "canonicalSupportedTypes" in entry
    before_canonical = [
        str(value or "").strip().casefold()
        for value in entry.get("canonicalSupportedTypes") or []
        if str(value or "").strip().casefold() in {"movie", "tv", "anime"}
    ]
    transport = list(semantic)
    if "anime" in semantic and "tv" not in transport:
        transport.append("tv")

    entry["supportedTypes"] = transport
    if transport != semantic or had_canonical:
        entry["canonicalSupportedTypes"] = semantic
    else:
        entry.pop("canonicalSupportedTypes", None)
    after_canonical = semantic if "canonicalSupportedTypes" in entry else []
    return before_supported != transport or before_canonical != after_canonical



def _native_brain_origin_priority(provider_id: str) -> dict[str, object] | None:
    raw = os.environ.get("NIAKVIO_NATIVE_BRAIN_ORIGIN_PRIORITY", "").strip()
    if not raw:
        return None
    if allmat.materialization_context() != "workspace":
        raise ValueError("Brain native origin priority is candidate-workspace only")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("invalid Brain native origin priority")
    if value.get("experimentType") != "native-blocking-player-origin-priority":
        raise ValueError("unsupported Brain native experiment")
    if allmat.canonical_id(str(value.get("providerId") or "")) != allmat.canonical_id(provider_id):
        raise ValueError("Brain native experiment provider mismatch")
    if value.get("candidateOnly") is not True or value.get("generatedByBrain") is not True:
        raise ValueError("Brain native experiment lost candidate provenance")
    if any(value.get(flag) is not False for flag in (
        "proofAuthority", "publicationAuthority", "nativePlaybackAuthority",
        "providerMutationAuthority",
    )):
        raise ValueError("Brain native experiment cannot carry publication authority")
    fingerprint = str(value.get("experimentFingerprint") or "").strip().casefold()
    if not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
        raise ValueError("Brain native experiment fingerprint invalid")
    host_re = re.compile(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")
    def hosts(key: str) -> list[str]:
        out: list[str] = []
        for item in value.get(key) or []:
            host = str(item or "").strip().casefold().rstrip(".")
            if host_re.fullmatch(host) and host not in out:
                out.append(host)
            if len(out) >= 4:
                break
        return out
    preferred = hosts("preferredHosts")
    deprioritized = [host for host in hosts("deprioritizedHosts") if host not in preferred]
    if not preferred:
        raise ValueError("Brain native experiment has no preferred host")
    return {
        "preferredHosts": preferred,
        "deprioritizedHosts": deprioritized,
        "experimentFingerprint": fingerprint,
    }


def _native_brain_hls_root_receipt(provider_id: str) -> dict[str, object] | None:
    """Accept only the next Brain-selected generic Core candidate in a workspace."""
    raw = os.environ.get("NIAKVIO_NATIVE_BRAIN_HLS_ROOT_RECEIPT", "").strip()
    if not raw:
        return None
    if allmat.materialization_context() != "workspace":
        raise ValueError("Brain HLS receipt experiment is candidate-workspace only")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("experimentType") != "native-hls-master-receipt-v30":
        raise ValueError("unsupported Brain HLS receipt experiment")
    if allmat.canonical_id(str(value.get("providerId") or "")) != allmat.canonical_id(provider_id):
        raise ValueError("Brain HLS receipt provider mismatch")
    if value.get("runtimeScope") != "native-blocking-fetch":
        raise ValueError("Brain HLS receipt must run only on native blocking fetch")
    if value.get("candidateOnly") is not True or value.get("generatedByBrain") is not True:
        raise ValueError("Brain HLS receipt provenance is missing")
    if any(value.get(k) is not False for k in (
        "proofAuthority", "publicationAuthority", "nativePlaybackAuthority",
        "providerMutationAuthority",
    )):
        raise ValueError("Brain HLS receipt cannot carry mutation/publication authority")
    fingerprint = str(value.get("experimentFingerprint") or "").strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
        raise ValueError("Brain HLS receipt fingerprint invalid")
    return {"experimentFingerprint": fingerprint}


def _apply_native_brain_origin_priority_candidate(base: bytes) -> bytes:
    """Compile V29 only into ephemeral candidate ProviderBase bytes."""
    text = base.decode("utf-8", errors="strict")
    marker = "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29"
    if marker in text:
        raise ValueError("V29 candidate logic leaked into production ProviderBase seed")
    score_anchor = """function _spv187QueueScore(url) {
  let bonus = 0;
  try {
    const path = _text(new URL(url).pathname);
    if (/^\\/v\\/[A-Za-z0-9_-]{3,160}\\/?$/i.test(path)) bonus = 1000;
  } catch (_) {}
  return _crawlUrlScore(url) + bonus;
}
"""
    candidate_helper = score_anchor + """/* NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29 */
function _spv29NativeBlockingQueueScore(url) {
  let score = _spv187QueueScore(url);
  try {
    if (typeof globalThis.__native_fetch !== "function" ||
        globalThis.__nuvioNonBlockingNativeFetchV1 === true) return score;
    const rule = NIAKVIO_PROVIDER_MODEL &&
      NIAKVIO_PROVIDER_MODEL.nativeBlockingOriginPriority;
    if (!rule || typeof rule !== "object") return score;
    const host = _text(new URL(url).hostname).toLowerCase().replace(/\\.$/, "");
    const preferred = Array.isArray(rule.preferredHosts) ? rule.preferredHosts : [];
    const deprioritized = Array.isArray(rule.deprioritizedHosts) ? rule.deprioritizedHosts : [];
    if (preferred.includes(host)) score += 6000;
    if (deprioritized.includes(host)) score -= 6000;
  } catch (_) {}
  return score;
}
"""
    if text.count(score_anchor) != 1:
        raise ValueError("candidate ProviderBase queue score anchor drift")
    text = text.replace(score_anchor, candidate_helper, 1)
    initial = "sort((a,b)=>_spv187QueueScore(b)-_spv187QueueScore(a))"
    iterative = "queue.sort((a,b)=>_spv187QueueScore(b.url)-_spv187QueueScore(a.url));"
    if text.count(initial) != 1 or text.count(iterative) != 1:
        raise ValueError("candidate ProviderBase queue ordering anchor drift")
    text = text.replace(
        initial,
        "sort((a,b)=>_spv29NativeBlockingQueueScore(b)-_spv29NativeBlockingQueueScore(a))",
        1,
    )
    text = text.replace(
        iterative,
        "queue.sort((a,b)=>_spv29NativeBlockingQueueScore(b.url)-_spv29NativeBlockingQueueScore(a.url));",
        1,
    )
    return text.encode("utf-8")


def materialize_one(
    provider_id: str,
    *,
    preserve_structured_data: bool = False,
) -> dict[str, object]:
    provider_id = allmat.canonical_id(provider_id)
    manifest = allmat.load(allmat.DEFAULT_SOURCE_MANIFEST)
    catalog = allmat.load(PROVIDER_CATALOG) if PROVIDER_CATALOG.is_file() else {}
    overrides = allmat.load(allmat.DEFAULT_OVERRIDES)
    static_knowledge = allmat.load(allmat.DEFAULT_STATIC_KNOWLEDGE)
    registry = allmat.load(REGISTRY)

    # Projection-only reconstruction must be a pure function of already accepted
    # structured DATA. It may rebuild published bytes, but it must never let
    # historical/static memory rewrite provider-overrides as a side effect.
    # Repair/Domain flows keep the existing reconciliation behavior.
    if preserve_structured_data:
        authority_changed: list[str] = []
        changed_domains: list[str] = []
    else:
        authority_changed = reconcile_provider_authority(
            overrides,
            static_knowledge,
            provider_id,
            registry,
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
    entry_authority = "global-manifest"
    catalog_record: dict[str, object] | None = None
    if not isinstance(entry, dict):
        providers = catalog.get("providers") if isinstance(catalog, dict) else None
        if isinstance(providers, list):
            for record in providers:
                if not isinstance(record, dict):
                    continue
                scraper = record.get("scraper")
                projections = record.get("projections")
                canonical = allmat.canonical_id(
                    str(record.get("canonicalId") or (scraper or {}).get("id") or "")
                )
                if canonical != provider_id or not isinstance(scraper, dict):
                    continue
                if not isinstance(projections, dict) or projections.get("vf") is not True or projections.get("general") is not False:
                    raise ValueError(
                        f"{provider_id}: non-global catalog row lacks strict France-only projection authority"
                    )
                entry = scraper
                catalog_record = record
                entry_authority = "france-only-catalog"
                break
    if not isinstance(entry, dict):
        raise ValueError(f"{provider_id}: manifest/catalog row not found")
    patch = patches.get(provider_id)
    capability = capabilities.get(provider_id)
    static_row = static_rows.get(provider_id)
    if not isinstance(patch, dict) or not isinstance(capability, dict):
        raise ValueError(f"{provider_id}: incomplete structured DATA")
    # A newly onboarded provider can already have canonical provider-owned DATA
    # (catalog row + override/capability + Lego/routes) before the next static
    # knowledge census has observed it.  Static knowledge is historical/RAG
    # input, not publication authority.  Projection-only materialization may
    # therefore build from the explicit current DATA without inventing static
    # history; Repair/Domain flows remain strict and require their normal
    # reconciliation evidence.
    if not isinstance(static_row, dict):
        if not preserve_structured_data:
            raise ValueError(f"{provider_id}: static knowledge missing outside projection-only materialization")
        static_row = {
            "model": {},
            "knowledge": {},
            "sources": [],
            "legacyProviderJsExecuted": False,
            "upstreamJsExecuted": False,
        }

    project_authoritative_types(entry, patch, capability)
    allmat.normalize_anime_transport_compatibility(entry)
    model = allmat.provider_model(provider_id, patch, capability, static_row)
    native_brain_origin_priority = _native_brain_origin_priority(provider_id)
    native_brain_hls_receipt = _native_brain_hls_root_receipt(provider_id)
    if native_brain_origin_priority and native_brain_hls_receipt:
        raise ValueError("only one native Brain experiment per candidate")
    if native_brain_origin_priority:
        model["nativeBlockingOriginPriority"] = native_brain_origin_priority
    if native_brain_hls_receipt:
        model["nativeHlsRootReceiptV30"] = native_brain_hls_receipt
    if preserve_structured_data:
        # Provider-owned runtime Legos are executable authority in their own
        # right when the structured identity contract is explicit. This applies
        # equally to Global and France-only projections; restricting it to the
        # France catalogue made valid Global manual-oracle Legos impossible to
        # rematerialize even though compose_provider_bundle executes them.
        # external_id is also a metadata-preflight mode: Core supplies external
        # IDs before execution, so an owned Lego must not be rejected merely
        # because its executable plan lives in that Lego instead of route DATA.
        provider_owned_identity_lego = allmat.provider_patch_has_owned_identity_lego_execution(patch)
        if not allmat.provider_model_has_executable_plan(model) and not provider_owned_identity_lego:
            raise ValueError(f"{provider_id}: projection-only DATA lacks executable plan")
        if not allmat.provider_model_has_identity_execution_plan(model) and not provider_owned_identity_lego:
            raise ValueError(f"{provider_id}: projection-only DATA lacks identity execution plan")
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
    if native_brain_origin_priority:
        base = _apply_native_brain_origin_priority_candidate(base)
    if native_brain_hls_receipt:
        from provider_patches.native_hls_root_receipt_v1 import apply as apply_native_hls_receipt
        base = apply_native_hls_receipt(base)
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

    # PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1
    # Single-provider materialization is publication-capable and used by
    # targeted Repair, projection reconciliation and sequential reconstruction.
    # Security hardening can rewrite provider bytes, so it must happen before
    # the optional final-stage minimizer. Otherwise the written publication is
    # no longer guaranteed to be a minimizer fixed-point.
    context = allmat.materialization_context()
    minimize_enabled = allmat.final_minimizer_enabled(context)
    minimizer_report = {
        "enabled": False,
        "savedBytes": 0,
        "transformedLines": 0,
        "skippedReason": "final-stage-only",
    }

    bundle = text.encode("utf-8")
    security_hardened, security_report = harden_bytes(bundle)
    hardened_text = security_hardened.decode("utf-8", errors="strict")
    assert_hardened(hardened_text)

    final_fix_ids = allmat.validate_managed_fixes(hardened_text)
    if set(final_fix_ids) != set(fix_ids):
        raise ValueError(
            f"{provider_id}: security hardening changed managed Lego ownership "
            f"before final minimization"
        )
    if hardened_text.count(boundary) != 1:
        raise ValueError(f"{provider_id}: security hardening changed Core boundary")

    if minimize_enabled:
        minimized = allmat.minimize_text(hardened_text)
        allmat.validate_transform(hardened_text, minimized.text)
        hardened_text = minimized.text
        minimizer_report = {
            "enabled": True,
            "savedBytes": minimized.saved_bytes,
            "transformedLines": minimized.transformed_lines,
            "skippedReason": minimized.skipped_reason,
        }
        if set(allmat.validate_managed_fixes(hardened_text)) != set(final_fix_ids):
            raise ValueError(f"{provider_id}: minimizer changed managed Lego ownership")
        if hardened_text.count(boundary) != 1:
            raise ValueError(f"{provider_id}: minimizer changed Core boundary")
        assert_hardened(hardened_text)

    bundle = hardened_text.encode("utf-8")

    try:
        verified_bundle, byte_validation = allmat.verify_bytes(bundle)
    except Exception as exc:
        raise RuntimeError(
            f"{provider_id}: materialized provider artifact validation failed: {exc}"
        ) from exc
    if verified_bundle != bundle:
        raise AssertionError(
            f"{provider_id}: materialized byte validator rewrote provider bytes"
        )
    bundle = verified_bundle
    assert_hardened(bundle.decode("utf-8", errors="strict"))

    digest = hashlib.sha256(bundle).hexdigest()
    filename = f"{provider_id}-{digest[:16]}.js"
    relative = f"providers/{filename}"
    allmat.DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    (allmat.DEFAULT_OUT / filename).write_bytes(bundle)
    entry["filename"] = relative
    entry["version"] = allmat.base_version(entry.get("version"))
    if entry_authority == "global-manifest":
        allmat.write_json(allmat.DEFAULT_SOURCE_MANIFEST, manifest)
    else:
        if not isinstance(catalog_record, dict) or catalog_record.get("scraper") is not entry:
            raise AssertionError(f"{provider_id}: France-only catalog authority detached during materialization")
        allmat.write_json(PROVIDER_CATALOG, catalog)
    from sync_manifest_projection_rows import sync as sync_manifest_projections
    sync_manifest_projections(check=False)

    report = {
        "provider": provider_id,
        "entryAuthority": entry_authority,
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
        "brainCandidateOriginPriority": bool(native_brain_origin_priority),
        "brainCandidateHlsRootReceipt": bool(native_brain_hls_receipt),
        "brainCandidateExperimentFingerprint": (
            str((native_brain_origin_priority or native_brain_hls_receipt or {}).get("experimentFingerprint") or "")
        ),
        "securityHardening": {
            "changed": bool(security_report.get("changed")),
            "alreadyHardened": bool(security_report.get("alreadyHardened")),
            "literalDecodeChanges": int(security_report.get("literalDecodeChanges") or 0),
            "hostnameChanges": int(security_report.get("hostnameChanges") or 0),
            "percentDecodeChanges": int(security_report.get("percentDecodeChanges") or 0),
            "htmlEntityDecodeReorders": int(security_report.get("htmlEntityDecodeReorders") or 0),
            "consoleSinkChanges": int(security_report.get("consoleSinkChanges") or 0),
            "consoleShadow": bool(security_report.get("consoleShadow")),
        },
        "byteValidation": {
            "tool": byte_validation.get("tool"),
            "toolVersion": byte_validation.get("toolVersion"),
            "phase": byte_validation.get("phase"),
            "sourceSha256": byte_validation.get("sourceSha256"),
            "fixedPointVerified": bool(byte_validation.get("fixedPointVerified")),
        },
        "staticAuthorityReconciledProviders": authority_changed,
        "domainSubstitutionReconciledProviders": changed_domains,
        "minimizer": minimizer_report,
    }
    ledger = upsert_materialization_report(report)
    print(
        "FIELD_PROVIDER_V3_ONE_MATERIALIZED "
        f"provider={provider_id} sha256={digest[:16]} file={relative} "
        f"ledger={ledger.get('providerCount')}/{ledger.get('expectedProviderCount')}"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider_id")
    parser.add_argument(
        "--preserve-structured-data",
        action="store_true",
        help="rebuild bytes from accepted DATA without mutating provider-overrides",
    )
    args = parser.parse_args()
    materialize_one(
        args.provider_id,
        preserve_structured_data=args.preserve_structured_data,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
