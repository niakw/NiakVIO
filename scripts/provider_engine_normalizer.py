#!/usr/bin/env python3
"""Access-neutral provider policy normalization and isolation audit.

Provider-specific hooks may adapt a provider's own protocol or catalogue, but
must never turn provider A into a hidden client of provider B.  The module is
network-free and does not change provider activation, routing or quarantine
state.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE_HOSTS = {
    "api.themoviedb.org", "raw.githubusercontent.com", "api.github.com",
    "github.com", "graphql.anilist.co", "api.jikan.moe", "api.tvmaze.com",
    "cdn.jsdelivr.net", "unpkg.com",
}
URL_RE = re.compile(r"https?://[^\s\"'`<>\\)]+", re.I)


def _merge_missing(target: Any, incoming: Any) -> Any:
    if isinstance(target, dict) and isinstance(incoming, dict):
        out = copy.deepcopy(target)
        for key, value in incoming.items():
            out[key] = _merge_missing(out[key], value) if key in out else copy.deepcopy(value)
        return out
    if isinstance(target, list) and isinstance(incoming, list):
        out = list(target)
        for value in incoming:
            if value not in out:
                out.append(copy.deepcopy(value))
        return out
    return copy.deepcopy(incoming) if target in (None, "", [], {}) else copy.deepcopy(target)


def normalize_mapping_keys(mapping: Any) -> dict[str, Any]:
    if not isinstance(mapping, dict):
        return {}
    output: dict[str, Any] = {}
    for raw_key, value in mapping.items():
        key = str(raw_key).casefold()
        output[key] = _merge_missing(output[key], value) if key in output else copy.deepcopy(value)
    return output


def normalize_provider_engine(data: dict[str, Any]) -> dict[str, Any]:
    output = copy.deepcopy(data)
    output["provider_patches"] = normalize_mapping_keys(output.get("provider_patches"))
    output["provider_capabilities"] = normalize_mapping_keys(output.get("provider_capabilities"))
    output["provider_engine_normalization"] = {
        "schema_version": 1,
        "case_insensitive_provider_keys": True,
        "activation_state_unchanged": True,
        "route_state_unchanged": True,
        "safety_quarantines_unchanged": True,
        "cross_provider_api_hooks_forbidden": True,
    }
    return output


def _host(raw: Any) -> str | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = "https://" + value.lstrip("/")
    try:
        return (urlparse(value).hostname or "").casefold() or None
    except ValueError:
        return None


def _provider_api_hosts(patches: dict[str, Any]) -> dict[str, set[str]]:
    output: dict[str, set[str]] = {}
    for provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        hosts: set[str] = set()
        official = _host(patch.get("official_api"))
        if official:
            hosts.add(official)
        fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
        fixed_host = _host(fixed.get("api"))
        if fixed_host:
            hosts.add(fixed_host)
        for value in (patch.get("runtime_domain_replacements") or {}).values():
            host = _host(value)
            if host and host.startswith("api."):
                hosts.add(host)
        if hosts:
            output[str(provider_id).casefold()] = hosts
    return output


def _host_belongs(host: str, owner_host: str) -> bool:
    return host == owner_host or host.endswith("." + owner_host)


def _script_paths(patch: dict[str, Any]) -> list[str]:
    scripts = [str(value) for value in patch.get("patch_scripts") or [] if str(value).strip()]
    legacy = str(patch.get("patch_script") or "").strip()
    if legacy and legacy not in scripts:
        scripts.append(legacy)
    return scripts


def validate_provider_isolation(data: dict[str, Any], root: Path = ROOT) -> list[str]:
    """Report provider hooks that reference another provider's configured API."""
    patches = normalize_mapping_keys(data.get("provider_patches"))
    api_hosts = _provider_api_hosts(patches)
    violations: list[str] = []
    for provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        foreign = {owner: hosts for owner, hosts in api_hosts.items() if owner != provider_id}
        for script in _script_paths(patch):
            path = (root / script).resolve()
            if root not in path.parents or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for raw in URL_RE.findall(text):
                try:
                    host = (urlparse(raw.rstrip(".,;")).hostname or "").casefold()
                except ValueError:
                    continue
                if not host or host in INFRASTRUCTURE_HOSTS:
                    continue
                for owner, hosts in foreign.items():
                    if any(_host_belongs(host, owner_host) for owner_host in hosts):
                        violations.append(
                            f"{provider_id}: {script} references foreign provider API {host} owned by {owner}"
                        )
    return sorted(set(violations))


def validate_published_provider_isolation(
    data: dict[str, Any], manifest: dict[str, Any], root: Path = ROOT
) -> list[str]:
    """Apply the same ownership rule to the exact bundles referenced by a manifest."""
    patches = normalize_mapping_keys(data.get("provider_patches"))
    api_hosts = _provider_api_hosts(patches)
    rows = manifest.get("scrapers") if isinstance(manifest, dict) else []
    violations: list[str] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename:
            continue
        path = (root / filename).resolve()
        if root not in path.parents or not path.is_file():
            continue
        foreign = {owner: hosts for owner, hosts in api_hosts.items() if owner != provider_id}
        text = path.read_text(encoding="utf-8", errors="ignore")
        for raw in URL_RE.findall(text):
            try:
                host = (urlparse(raw.rstrip(".,;")).hostname or "").casefold()
            except ValueError:
                continue
            if not host or host in INFRASTRUCTURE_HOSTS:
                continue
            for owner, hosts in foreign.items():
                if any(_host_belongs(host, owner_host) for owner_host in hosts):
                    violations.append(
                        f"{provider_id}: published bundle {filename} references foreign provider API {host} owned by {owner}"
                    )
    return sorted(set(violations))
