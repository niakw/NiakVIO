#!/usr/bin/env python3
"""Classify whether a provider has enough current network authority for Repair.

This gate separates address/identity discovery from runtime extraction repair.
Search remains useful supplementary evidence for the historical catalogue, but a
search result by itself never grants Repair/publication authority.

Safe-disable decisions are deliberately narrow:
* an already-manual-off provider stays off;
* an authoritative registry source explicitly marked removed/dead may disable a
  site-dependent provider when no independent API/backend authority exists;
* a site-dependent provider with no authoritative route source is rediscovery-
  blocked first, and is disabled only after repeated persisted Domain failures.

API/embed/backend-driven providers may remain repairable without a homepage when
their structured backend authority is explicit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
HUBS = ROOT / "provider-hubs.json"
OVERRIDES = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.json"
HISTORY = ROOT / "provider-domain-history.json"
OUTPUT = ROOT / "automation/provider-authority-status.json"

REMOVED_SOURCE_STATES = {"removed", "dead", "retired", "graveyard", "compromised"}
NON_PROVIDER_AUTHORITY_HOSTS = {
    "api.themoviedb.org",
    "v3-cinemeta.strem.io",
    "arm.haglund.dev",
}
SITE_DEPENDENT_CAPABILITIES = {"html_scraper", "mixed_embed_resolver", "official_domain_hub"}
API_CAPABILITIES = {"api_stream_resolver", "api_resolver", "stremio_api"}
AUTHORITY_SOURCE_TYPES = {"hub", "redirect", "telegram_public"}
DISABLED_STATUS = {"désactivé", "desactive", "disabled", "inactif", "inactive"}


def load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    return value


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def http_url(value: object) -> bool:
    raw = str(value or "").strip()
    if not raw.startswith(("http://", "https://")):
        return False
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return False
    return bool(parsed.hostname)


def source_state(row: dict[str, Any]) -> str:
    return str(row.get("source_status") or row.get("status") or "").strip().casefold()


def active_authority_sources(registry: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in registry.get("sources") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("type") or "").casefold() not in AUTHORITY_SOURCE_TYPES:
            continue
        if not http_url(row.get("url")):
            continue
        if source_state(row) in REMOVED_SOURCE_STATES:
            continue
        out.append(row)
    return out


def removed_authority_sources(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in registry.get("sources") or []
        if isinstance(row, dict)
        and str(row.get("type") or "").casefold() in AUTHORITY_SOURCE_TYPES
        and source_state(row) in REMOVED_SOURCE_STATES
    ]


def backend_urls(patch: dict[str, Any]) -> list[str]:
    """Return only explicit provider execution backends, never generic site fallbacks."""
    # PROVIDER_AUTHORITY_BACKEND_SCOPE_V1
    values: list[str] = []

    def add(value: object) -> None:
        if not http_url(value):
            return
        url = str(value).rstrip("/")
        hostname = (urlsplit(url).hostname or "").casefold()
        if not hostname or hostname in NON_PROVIDER_AUTHORITY_HOSTS:
            return
        values.append(url)

    add(patch.get("official_api"))
    fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
    for key in ("api", "base", "url"):
        add(fixed.get(key))
    recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else {}
    for key in ("api", "base", "url"):
        add(recipe.get(key))
    for options in (patch.get("provider_lego_options") or {}).values():
        if not isinstance(options, dict):
            continue
        for key in ("api", "db", "api_base", "apiBase", "backend", "endpoint"):
            add(options.get(key))
    return list(dict.fromkeys(values))


def fresh_history_authority(history: dict[str, Any], max_age_days: int = 3) -> bool:
    current = history.get("current") if isinstance(history.get("current"), dict) else {}
    stamp = str(current.get("last_seen") or "").strip()
    if not stamp:
        return False
    try:
        seen = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - seen.astimezone(timezone.utc)
    return age.total_seconds() >= 0 and age.total_seconds() <= max_age_days * 86400


def has_positive_route_prior(patch: dict[str, Any]) -> bool:
    proof = patch.get("route_proof") if isinstance(patch.get("route_proof"), dict) else {}
    last = proof.get("lastRepairProbe") if isinstance(proof.get("lastRepairProbe"), dict) else {}
    return bool(last.get("positiveExecutionEvidence")) or int(proof.get("provenRouteCount") or 0) > 0


def authority_failures(history: dict[str, Any]) -> int:
    row = history.get("authority_failures") if isinstance(history.get("authority_failures"), dict) else {}
    return max(0, int(row.get("consecutive") or 0))


def has_search(registry: dict[str, Any]) -> bool:
    if any(str(value or "").strip() for value in registry.get("search_queries") or []):
        return True
    return any(
        isinstance(row, dict) and str(row.get("type") or "").casefold() == "search"
        for row in registry.get("sources") or []
    )


def classify(
    provider: str,
    manifest_row: dict[str, Any],
    registry: dict[str, Any],
    patch: dict[str, Any],
    history: dict[str, Any],
) -> dict[str, Any]:
    enabled = manifest_row.get("enabled") is not False
    manual_off = str(patch.get("manual_off_reason") or registry.get("manual_off_reason") or "").strip()
    capability = str(patch.get("capability") or "").strip().casefold()
    backends = backend_urls(patch)
    strong_sources = active_authority_sources(registry)
    removed_sources = removed_authority_sources(registry)
    direct = str(registry.get("direct") or "").strip()
    direct_current_authority = str(registry.get("direct_authority") or "").strip().casefold() in {"explicit_current", "operator_pin"}
    failures = authority_failures(history)
    search = has_search(registry)
    legacy_search = registry.get("legacy_search_refresh") is True
    official_site = str(patch.get("official_site") or "").strip()

    reasons: list[str] = []
    # A curated/manual non-activation decision must be executable policy, not a
    # label that leaves the provider enabled forever. Enabled providers with an
    # explicit manual_off_reason enter the normal disabled-retention lifecycle.
    if manual_off and enabled:
        reasons.append(manual_off)
        return {
            "provider": provider,
            "action": "DISABLE_MANUAL_POLICY",
            "repairEligible": False,
            "confidence": "terminal",
            "authorityClass": "manual-off",
            "failureCount": failures,
            "reasons": reasons,
        }
    if manual_off or not enabled:
        reasons.append(manual_off or "already_disabled")
        return {
            "provider": provider,
            "action": "KEEP_DISABLED",
            "repairEligible": False,
            "confidence": "terminal",
            "authorityClass": "disabled",
            "failureCount": failures,
            "reasons": reasons,
        }

    # backend_urls() only collects explicit provider execution backends and
    # excludes shared identity infrastructure / generic fallback site bases.
    # Their presence is therefore
    # enough to establish backend authority even for mixed_embed_resolver.
    backend_authority = bool(backends)
    if backend_authority:
        reasons.append("structured_backend_authority")
        return {
            "provider": provider,
            "action": "KEEP_BACKEND",
            "repairEligible": True,
            "confidence": "high",
            "authorityClass": "api-or-backend",
            "failureCount": failures,
            "backendUrls": backends,
            "reasons": reasons,
        }

    if removed_sources and not strong_sources:
        reasons.append("authoritative_source_removed")
        return {
            "provider": provider,
            "action": "DISABLE_SOURCE_REMOVED",
            "repairEligible": False,
            "confidence": "high",
            "authorityClass": "source-removed",
            "failureCount": failures,
            "reasons": reasons,
        }

    if strong_sources:
        reasons.append("authoritative_route_source")
        return {
            "provider": provider,
            "action": "KEEP_ROUTE_AUTHORITY",
            "repairEligible": True,
            "confidence": "high",
            "authorityClass": "hub-or-redirect",
            "failureCount": failures,
            "reasons": reasons,
        }

    if http_url(direct):
        # PROVIDER_AUTHORITY_DIRECT_PROOF_V1
        # A direct URL is not automatically authority. explicit_current is an
        # operator/Domain pin; otherwise the candidate needs provider-owned
        # positive route evidence or a fresh matching runtime observation.
        direct_route_proven = has_positive_route_prior(patch)
        current = history.get("current") if isinstance(history.get("current"), dict) else {}
        current_url = str(current.get("url") or "").rstrip("/")
        direct_url = direct.rstrip("/")
        fresh_direct_observation = (
            failures == 0
            and fresh_history_authority(history)
            and current_url == direct_url
        )

        if direct_current_authority and failures < 2:
            reasons.append("current_authority_direct")
            return {
                "provider": provider,
                "action": "KEEP_DIRECT",
                "repairEligible": True,
                "confidence": "high",
                "authorityClass": "direct",
                "failureCount": failures,
                "reasons": reasons,
            }
        if not direct_current_authority and failures < 2 and direct_route_proven:
            reasons.extend(["curated_direct", "existing_positive_route_prior"])
            return {
                "provider": provider,
                "action": "KEEP_DIRECT",
                "repairEligible": True,
                "confidence": "medium",
                "authorityClass": "direct",
                "failureCount": failures,
                "reasons": reasons,
            }
        if not direct_current_authority and fresh_direct_observation:
            reasons.append("fresh_curated_candidate_runtime_observation")
            return {
                "provider": provider,
                "action": "KEEP_LIVE_CANDIDATE",
                "repairEligible": True,
                "confidence": "medium",
                "authorityClass": "fresh-curated-candidate",
                "failureCount": failures,
                "reasons": reasons,
            }
        if failures >= 3 and capability in SITE_DEPENDENT_CAPABILITIES:
            reasons.extend(["direct_repeatedly_unresolved", "site_dependent"])
            return {
                "provider": provider,
                "action": "DISABLE_AUTHORITY_EXHAUSTED",
                "repairEligible": False,
                "confidence": "high",
                "authorityClass": "stale-direct",
                "failureCount": failures,
                "reasons": reasons,
            }
        reasons.append("direct_candidate_unproven")
        if search:
            reasons.append("search_supplement_only")
        return {
            "provider": provider,
            "action": "REDISCOVER_SEARCH" if search else "REDISCOVER_DIRECT",
            "repairEligible": False,
            "confidence": "low",
            "authorityClass": "unproven-direct-candidate",
            "failureCount": failures,
            "reasons": reasons,
        }

    if capability in SITE_DEPENDENT_CAPABILITIES or not capability:
        if failures == 0 and http_url(official_site) and has_positive_route_prior(patch):
            reasons.extend(["structured_official_site", "existing_positive_route_prior"])
            return {
                "provider": provider,
                "action": "KEEP_PROVEN_SITE",
                "repairEligible": True,
                "confidence": "medium",
                "authorityClass": "structured-site-plus-route-proof",
                "failureCount": failures,
                "reasons": reasons,
            }
        current = history.get("current") if isinstance(history.get("current"), dict) else {}
        current_url = str(current.get("url") or "").rstrip("/")
        direct_candidates = {str(value or "").rstrip("/") for value in registry.get("direct_candidates") or [] if http_url(value)}
        if failures == 0 and fresh_history_authority(history):
            if current_url and current_url in direct_candidates:
                reasons.append("fresh_curated_candidate_runtime_observation")
                return {
                    "provider": provider,
                    "action": "KEEP_LIVE_CANDIDATE",
                    "repairEligible": True,
                    "confidence": "medium",
                    "authorityClass": "fresh-curated-candidate",
                    "failureCount": failures,
                    "reasons": reasons,
                }
            if registry.get("legacy_search_refresh") is True and has_positive_route_prior(patch):
                reasons.extend(["fresh_lkg_observation", "existing_positive_route_prior"])
                return {
                    "provider": provider,
                    "action": "KEEP_LKG_COMBO",
                    "repairEligible": True,
                    "confidence": "medium",
                    "authorityClass": "historical-combined-evidence",
                    "failureCount": failures,
                    "reasons": reasons,
                }
        if failures >= 2:
            reasons.extend(["no_authoritative_route_source", "repeated_domain_failure"])
            return {
                "provider": provider,
                "action": "DISABLE_AUTHORITY_EXHAUSTED",
                "repairEligible": False,
                "confidence": "high",
                "authorityClass": "search-only-or-missing",
                "failureCount": failures,
                "reasons": reasons,
            }
        reasons.append("no_authoritative_route_source")
        if search:
            reasons.append("search_supplement_only")
        if legacy_search:
            reasons.append("historical_search_refresh_enabled")
        if official_site:
            reasons.append("published_site_is_lkg_only")
        return {
            "provider": provider,
            "action": "REDISCOVER_SEARCH" if search else "REDISCOVER_MISSING_REGISTRY",
            "repairEligible": False,
            "confidence": "low",
            "authorityClass": "search-only-or-missing",
            "failureCount": failures,
            "reasons": reasons,
        }

    reasons.append("no_specific_authority_rule")
    return {
        "provider": provider,
        "action": "KEEP_DIAGNOSTIC",
        "repairEligible": True,
        "confidence": "low",
        "authorityClass": "unknown",
        "failureCount": failures,
        "reasons": reasons,
    }


def apply_disable(
    row: dict[str, Any],
    registry: dict[str, Any],
    patch: dict[str, Any],
    action: str,
) -> str:
    if action == "DISABLE_SOURCE_REMOVED":
        reason = "auto_off_authoritative_source_removed"
    elif action == "DISABLE_AUTHORITY_EXHAUSTED":
        reason = "auto_off_domain_authority_exhausted"
    elif action == "DISABLE_MANUAL_POLICY":
        reason = str(
            patch.get("manual_off_reason")
            or registry.get("manual_off_reason")
            or "manual_off_registry_nonactivable"
        ).strip()
    else:
        raise ValueError(f"unsupported disable action: {action}")
    row["enabled"] = False
    row["disabledReason"] = reason
    manifest_overrides = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
    manifest_overrides["enabled"] = False
    patch["manifest_overrides"] = manifest_overrides
    patch["route_data_state"] = "off"
    patch["activation_eligible"] = False
    patch["manual_off_reason"] = reason
    registry["manifest_status"] = "Désactivé"
    registry["activation_eligible"] = False
    registry["manual_off_reason"] = reason
    return reason


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--apply-safe-disables", action="store_true")
    args = parser.parse_args()

    hubs = load(HUBS, {"providers": {}})
    overrides = load(OVERRIDES, {"provider_patches": {}})
    manifest = load(MANIFEST, {"scrapers": []})
    history = load(HISTORY, {"providers": {}})
    registries = hubs.setdefault("providers", {})
    patches = overrides.setdefault("provider_patches", {})
    histories = history.get("providers") if isinstance(history.get("providers"), dict) else {}

    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    results: list[dict[str, Any]] = []
    disabled_now: list[str] = []
    for manifest_row in rows:
        provider = cid(manifest_row.get("id"))
        if not provider:
            continue
        registry = registries.get(provider) if isinstance(registries.get(provider), dict) else {}
        patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
        hist = histories.get(provider) if isinstance(histories.get(provider), dict) else {}
        result = classify(provider, manifest_row, registry, patch, hist)
        if args.apply_safe_disables and result["action"] in {
            "DISABLE_SOURCE_REMOVED", "DISABLE_AUTHORITY_EXHAUSTED", "DISABLE_MANUAL_POLICY"
        } and manifest_row.get("enabled") is not False:
            reason = apply_disable(manifest_row, registry, patch, result["action"])
            registries[provider] = registry
            patches[provider] = patch
            disabled_now.append(provider)
            result["appliedDisableReason"] = reason
        results.append(result)

    report = {
        "schemaVersion": 1,
        "authority": "provider-authority-arbiter-v1",
        "policy": {
            "searchRole": "historical-supplement-only",
            "futureHubSearchDefault": False,
            "repairRequiresAddressAuthorityForSiteDependentProviders": True,
            "disableAfterConsecutiveDomainFailures": 2,
            "staleDirectDisableAfterConsecutiveDomainFailures": 3,
            "apiBackendMayOperateWithoutHomepage": True,
            "manualOffEntersDisabledRetentionImmediately": True,
        },
        "providerCount": len(results),
        "repairEligible": sorted(row["provider"] for row in results if row.get("repairEligible") is True),
        "repairBlocked": sorted(row["provider"] for row in results if row.get("repairEligible") is not True),
        "disabledNow": sorted(disabled_now),
        "providers": results,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    write(output, report)
    if args.apply_safe_disables:
        write(MANIFEST, manifest)
        write(HUBS, hubs)
        write(OVERRIDES, overrides)
    print(
        "FIELD_PROVIDER_AUTHORITY "
        f"providers={len(results)} repair_eligible={len(report['repairEligible'])} "
        f"blocked={len(report['repairBlocked'])} disabled_now={len(disabled_now)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
