#!/usr/bin/env python3
"""Refresh Provider v3 primary domains from authoritative address hubs.

This command is intentionally narrower than the general hub resolver:
- an official hub/channel/redirect is the authority for the provider's current site;
- the discovered terminal URL is persisted immediately after structural safety checks;
- the terminal itself is NOT fetched/probed before persistence;
- DNS/HTTP preflight remains observation-only and happens after the domain update;
- only provider_patches.<id>.official_site and provider-domain-history.json may change.

The separation matters for fast-moving provider domains: a CI runner receiving a
403, anti-bot page or timeout from the terminal must never keep yesterday's domain
when the official hub already advertises a newer one.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Any

import resolve_provider_hubs as hubresolver

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "provider-overrides.json"
HISTORY_PATH = ROOT / "provider-domain-history.json"
ALLOWED_SOURCE_TYPES = {"hub", "telegram_public", "redirect"}


def _candidate_url(row: dict[str, Any]) -> str:
    return str(row.get("url") or "").strip().rstrip("/")


def _safe_authoritative_candidate(
    provider_id: str,
    cfg: dict[str, Any],
    row: dict[str, Any],
) -> bool:
    source_type = str(row.get("source_type") or "").strip().casefold()
    url = _candidate_url(row)
    hostname = hubresolver.host(url)
    if source_type not in ALLOWED_SOURCE_TYPES:
        return False
    if not url or not hostname or not hubresolver.is_provider_terminal_site_url(url):
        return False
    if hostname in hubresolver.discovery_source_hosts(cfg):
        return False
    if hostname in {str(item).casefold().strip(".") for item in cfg.get("blocked_hosts") or []}:
        return False
    if hostname.endswith(
        hubresolver.SOCIAL_HOST_SUFFIXES
        + hubresolver.SEARCH_HOST_SUFFIXES
        + hubresolver.INFRASTRUCTURE_HOST_SUFFIXES
    ):
        return False
    return True


def _redirect_candidates_from_source_observations(
    cfg: dict[str, Any],
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Treat an authoritative source redirect as an address declaration.

    Some hubs are themselves redirectors. In that case the hub request is the
    discovery operation; the redirect destination is the advertised domain and
    must not be probed a second time as a terminal gate.
    """
    output: list[dict[str, Any]] = []
    source_hosts = hubresolver.discovery_source_hosts(cfg)
    for observation in observations:
        source_type = str(observation.get("source_type") or "").strip().casefold()
        if source_type not in ALLOWED_SOURCE_TYPES:
            continue
        source_url = str(observation.get("url") or "").strip()
        final_url = str(observation.get("final_url") or "").strip().rstrip("/")
        if not final_url or hubresolver.host(final_url) == hubresolver.host(source_url):
            continue
        if hubresolver.host(final_url) in source_hosts:
            continue
        output.append({
            "url": final_url,
            "label": "authoritative source redirect destination",
            "score": 120,
            "source_type": source_type,
            "source": source_url,
            "source_redirect": True,
        })
    return output


def resolve_authoritative_hub_domain(
    provider_id: str,
    cfg: dict[str, Any],
    history_row: dict[str, Any],
    mode: str,
    timeout: float,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "provider_id": provider_id,
        "status": "hub_unresolved",
        "terminal_probe_skipped": True,
    }
    if not hubresolver.has_authoritative_hub_source(cfg):
        item["status"] = "not_applicable"
        item["reason"] = "no_authoritative_hub_source"
        return item

    candidates, observations = hubresolver.gather_candidates(
        provider_id,
        cfg,
        history_row,
        mode,
        timeout,
    )
    candidates = [
        *_redirect_candidates_from_source_observations(cfg, observations),
        *[
            dict(row)
            for row in candidates
            if str(row.get("source_type") or "").strip().casefold() in ALLOWED_SOURCE_TYPES
        ],
    ]

    deduped: dict[str, dict[str, Any]] = {}
    for row in candidates:
        url = _candidate_url(row)
        if not url or not _safe_authoritative_candidate(provider_id, cfg, row):
            continue
        previous = deduped.get(url)
        if previous is None or int(row.get("score") or 0) > int(previous.get("score") or 0):
            deduped[url] = row
    ordered = sorted(
        deduped.values(),
        key=lambda row: (-int(row.get("score") or 0), _candidate_url(row)),
    )

    item["sources"] = observations
    item["site_candidates"] = ordered
    item["site_validations"] = []
    if not ordered:
        item["reason"] = "authoritative_hub_no_safe_terminal_candidate"
        return item

    selected = ordered[0]
    terminal = _candidate_url(selected)
    item.update({
        "status": "site_authoritative",
        "reason": "authoritative_hub_primary_domain_observed_no_terminal_probe",
        "official_site": terminal,
        "site_final_url": terminal,
        "selected_source_type": selected.get("source_type"),
        "selected_source": selected.get("source"),
        "candidate_score": selected.get("score"),
        "terminal_probe_skipped": True,
        "api_candidates": [],
        "api_probes": [],
        "validated_api": None,
    })
    return item



def _domain_host(value: str) -> str:
    raw=str(value or "").strip()
    if not raw:return ""
    return hubresolver.host(raw if "://" in raw else "https://"+raw)


def _reconcile_domain_derivatives(patch: dict[str, Any], before_site: str, next_site: str) -> list[dict[str, str]]:
    changes=[];before_host=_domain_host(before_site);next_host=_domain_host(next_site)
    if not next_host:return changes
    maps=[]
    for name in ("domain_substitutions","replacements","runtime_domain_replacements"):
        row=patch.get(name)
        if isinstance(row,dict):maps.append((name,row))
    edges={}
    for _name,row in maps:
        for source,target in row.items():
            sh,th=_domain_host(source),_domain_host(target)
            if sh and th:edges[sh]=th
    if before_host and before_host!=next_host:edges[before_host]=next_host
    def canonical(hostname):
        seen=set();current=hostname
        while current and current not in seen and current in edges:seen.add(current);current=edges[current]
        return current
    for name,row in maps:
        for source,target in list(row.items()):
            th=_domain_host(target)
            if th and canonical(th)==next_host and th!=next_host:
                row[source]=next_host;changes.append({"from":str(target),"to":next_host,"kind":name})
        if before_host and before_host!=next_host and row.get(before_host)!=next_host:
            row[before_host]=next_host;changes.append({"from":before_host,"to":next_host,"kind":name})
    manifest=patch.get("manifest_overrides")
    if isinstance(manifest,dict):
        for field in ("logo","icon","favicon"):
            value=manifest.get(field);vh=_domain_host(value)
            if value and vh and canonical(vh)==next_host and vh!=next_host:
                manifest[field]=str(value).replace(vh,next_host);changes.append({"from":str(value),"to":str(manifest[field]),"kind":f"manifest_overrides.{field}"})
    notes=patch.get("notes")
    if isinstance(notes,list) and before_host and before_host!=next_host:
        patch["notes"]=[str(v).replace(before_host,next_host) for v in notes]
    elif isinstance(notes,str) and before_host and before_host!=next_host:
        patch["notes"]=notes.replace(before_host,next_host)
    return changes

def _update_history_on_change(history_row: dict[str, Any], item: dict[str, Any]) -> None:
    terminal = str(item.get("official_site") or "").rstrip("/")
    if not terminal:
        return
    current = history_row.get("current") if isinstance(history_row.get("current"), dict) else None
    if current and str(current.get("url") or "").rstrip("/") == terminal:
        return
    if current:
        history_row["previous"] = [current, *(history_row.get("previous") or [])][:5]
    history_row["current"] = {
        "url": terminal,
        "host": hubresolver.host(terminal),
        "observed_at": hubresolver.now_iso(),
        "authority": "official_hub",
        "source_type": item.get("selected_source_type"),
        "source": item.get("selected_source"),
    }
    history_row.pop("pending", None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="health-output/provider-hub-report.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mode", choices=("quick", "deep"), default="quick")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()

    config = hubresolver.load_json(CONFIG_PATH, {})
    hubs = hubresolver.merge_hub_registry(config)
    history = hubresolver.load_json(HISTORY_PATH, {"schema_version": 1, "providers": {}})
    history.setdefault("schema_version", 1)
    history_providers = history.setdefault("providers", {})
    history_before = json.dumps(history_providers, sort_keys=True, ensure_ascii=False)
    selected_ids = {hubresolver.canonical_provider_id(value) for value in args.provider}

    work: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for provider_id, cfg in sorted(hubs.items()):
        if selected_ids and provider_id not in selected_ids:
            continue
        if not hubresolver.has_authoritative_hub_source(cfg):
            continue
        disabled = str(cfg.get("manifest_status") or "").casefold() in {"désactivé", "desactive", "disabled"}
        if disabled and not args.include_disabled:
            continue
        work.append((provider_id, dict(cfg), history_providers.setdefault(provider_id, {})))

    report: dict[str, Any] = {
        "schema_version": 4,
        "generated_at": hubresolver.now_iso(),
        "mode": args.mode,
        "authority": "official_hub",
        "terminal_validation_required": False,
        "providers": {},
        "applied": 0,
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 16))) as pool:
        future_map = {
            pool.submit(
                resolve_authoritative_hub_domain,
                provider_id,
                cfg,
                history_row,
                args.mode,
                args.timeout,
            ): (provider_id, cfg, history_row)
            for provider_id, cfg, history_row in work
        }
        for future in concurrent.futures.as_completed(future_map):
            provider_id, _cfg, history_row = future_map[future]
            try:
                item = future.result()
            except Exception as exc:
                item = {
                    "provider_id": provider_id,
                    "status": "hub_unresolved",
                    "reason": "exception",
                    "terminal_probe_skipped": True,
                    "error": f"{type(exc).__name__}: {exc}",
                }

            if args.apply and item.get("status") == "site_authoritative":
                patches = config.get("provider_patches")
                patch = patches.get(provider_id) if isinstance(patches, dict) else None
                if not isinstance(patch, dict):
                    item["status"] = "hub_unresolved"
                    item["reason"] = "missing_provider_patch_domain_refresh_may_not_add_provider"
                else:
                    before_site = str(patch.get("official_site") or "").rstrip("/")
                    next_site = str(item.get("official_site") or "").rstrip("/")
                    changes: list[dict[str, str]] = []
                    if next_site and next_site != before_site:
                        patch["official_site"] = next_site
                        changes.append({"from": before_site, "to": next_site, "kind": "official_site"})
                        report["applied"] += 1
                        _update_history_on_change(history_row, item)
                    if next_site:
                        changes.extend(_reconcile_domain_derivatives(patch, before_site, next_site))
                    item["applied_changes"] = changes
            report["providers"][provider_id] = item

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    hubresolver.atomic_write_json(output, report)

    if args.apply:
        hubresolver.atomic_write_json(CONFIG_PATH, config)
        history_after = json.dumps(history_providers, sort_keys=True, ensure_ascii=False)
        if history_after != history_before:
            history["updated_at"] = hubresolver.now_iso()
            hubresolver.atomic_write_json(HISTORY_PATH, history)

    resolved = sum(1 for row in report["providers"].values() if row.get("status") == "site_authoritative")
    unresolved = sum(1 for row in report["providers"].values() if row.get("status") == "hub_unresolved")
    print(
        "authoritative hub domain refresh complete: "
        f"resolved={resolved} unresolved={unresolved} applied={report['applied']} terminal_probe=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
