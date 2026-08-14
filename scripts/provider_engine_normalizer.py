#!/usr/bin/env python3
"""Access-neutral provider policy normalization and isolation enforcement.

Provider-specific hooks may adapt a provider's own protocol or catalogue, but
must never turn provider A into a hidden client of provider B. The module is
network-free and never changes provider activation, routing or quarantine state.
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
    "github.com", "www.github.com", "graphql.anilist.co", "api.jikan.moe",
    "api.tvmaze.com", "cdn.jsdelivr.net", "unpkg.com", "fonts.googleapis.com",
    "fonts.gstatic.com", "image.tmdb.org", "objects.githubusercontent.com",
}
URL_RE = re.compile(r"https?://[^\s\"'`<>\\)]+", re.I)
OWNED_WRAPPER_MARKER_RE = re.compile(r"/\*\s*(NUVIO_[A-Z0-9_:.-]+)\s*\*/", re.I)
FAMILY_SUFFIXES = ("official", "homes", "home", "new", "rip", "co", "tv", "app", "web")


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


def _host_belongs(host: str, owner_host: str) -> bool:
    return host == owner_host or host.endswith("." + owner_host)


def _provider_token(provider_id: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(provider_id).casefold())


def _provider_family_token(provider_id: str) -> str:
    token = _provider_token(provider_id)
    changed = True
    while changed:
        changed = False
        for suffix in FAMILY_SUFFIXES:
            if token.endswith(suffix) and len(token) - len(suffix) >= 4:
                token = token[:-len(suffix)]
                changed = True
                break
    return token


def _same_provider_family(left: str, right: str) -> bool:
    return _provider_family_token(left) == _provider_family_token(right)


def _looks_provider_owned(candidate: str, provider_id: str, strong: set[str]) -> bool:
    if any(_host_belongs(candidate, base) or _host_belongs(base, candidate) for base in strong):
        return True
    token = _provider_token(provider_id)
    normalized = re.sub(r"[^a-z0-9]", "", candidate.casefold())
    return len(token) >= 4 and token in normalized


def _provider_api_hosts(patches: dict[str, Any]) -> dict[str, set[str]]:
    """Return complete provider-owned backend hosts.

    The historical function name is retained for compatibility, but ownership
    now covers official API, site and hub hosts plus strongly provider-related
    fixed/replacement endpoints. Shared players/CDNs are intentionally ignored.
    """
    output: dict[str, set[str]] = {}
    for raw_provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        provider_id = str(raw_provider_id).casefold()
        strong: set[str] = set()
        for key in ("official_api", "official_site", "official_hub"):
            value = _host(patch.get(key))
            if value and value not in INFRASTRUCTURE_HOSTS:
                strong.add(value)

        derived: set[str] = set()
        fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
        for key in ("api", "referer", "origin"):
            value = _host(fixed.get(key))
            if value and value not in INFRASTRUCTURE_HOSTS and _looks_provider_owned(value, provider_id, strong):
                derived.add(value)

        for mapping_key in ("runtime_domain_replacements", "route_replacements", "replacements"):
            mapping = patch.get(mapping_key) if isinstance(patch.get(mapping_key), dict) else {}
            for raw in mapping.values():
                value = _host(raw)
                if value and value not in INFRASTRUCTURE_HOSTS and _looks_provider_owned(value, provider_id, strong):
                    derived.add(value)

        owned = strong | derived
        if owned:
            output[provider_id] = owned
    return output


def _current_provider_owns(host: str, provider_id: str, ownership: dict[str, set[str]]) -> bool:
    provider_id = str(provider_id).casefold()
    if any(_host_belongs(host, own) for own in ownership.get(provider_id, set())):
        return True
    token = _provider_token(provider_id)
    normalized = re.sub(r"[^a-z0-9]", "", host.casefold())
    return len(token) >= 4 and token in normalized


def _foreign_owners_for_host(
    host: str, provider_id: str, ownership: dict[str, set[str]]
) -> list[str]:
    provider_id = str(provider_id).casefold()
    if not host or host in INFRASTRUCTURE_HOSTS or _current_provider_owns(host, provider_id, ownership):
        return []
    return sorted(
        owner
        for owner, hosts in ownership.items()
        if owner != provider_id
        and not _same_provider_family(provider_id, owner)
        and any(_host_belongs(host, owner_host) for owner_host in hosts)
    )


def _foreign_hits(text: str, provider_id: str, ownership: dict[str, set[str]]) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for raw in URL_RE.findall(text):
        try:
            host = (urlparse(raw.rstrip(".,;")).hostname or "").casefold()
        except ValueError:
            continue
        for owner in _foreign_owners_for_host(host, provider_id, ownership):
            hits.append((host, owner))
    return sorted(set(hits))


def _script_paths(patch: dict[str, Any]) -> list[str]:
    scripts = [str(value) for value in patch.get("patch_scripts") or [] if str(value).strip()]
    legacy = str(patch.get("patch_script") or "").strip()
    if legacy and legacy not in scripts:
        scripts.append(legacy)
    return scripts


def normalize_provider_engine(data: dict[str, Any]) -> dict[str, Any]:
    output = copy.deepcopy(data)
    output["provider_patches"] = normalize_mapping_keys(output.get("provider_patches"))
    output["provider_capabilities"] = normalize_mapping_keys(output.get("provider_capabilities"))
    output["provider_engine_normalization"] = {
        "schema_version": 3,
        "case_insensitive_provider_keys": True,
        "activation_state_unchanged": True,
        "route_state_unchanged": True,
        "safety_quarantines_unchanged": True,
        "cross_provider_backends_forbidden": True,
    }
    return output


def _sanitize_observed_origins_in_place(
    output: dict[str, Any], ownership: dict[str, set[str]]
) -> list[dict[str, str]]:
    capabilities = output.get("provider_capabilities")
    if not isinstance(capabilities, dict):
        return []
    removed: list[dict[str, str]] = []
    for raw_provider_id, row in capabilities.items():
        if not isinstance(row, dict) or not isinstance(row.get("observed_origins"), list):
            continue
        provider_id = str(raw_provider_id).casefold()
        kept: list[Any] = []
        for raw in row["observed_origins"]:
            candidate = _host(raw)
            owners = _foreign_owners_for_host(candidate or "", provider_id, ownership)
            if owners:
                removed.append({
                    "provider_id": provider_id,
                    "origin": str(raw),
                    "foreign_owner": ",".join(owners),
                })
                continue
            if raw not in kept:
                kept.append(raw)
        row["observed_origins"] = kept
    return removed


def sanitize_provider_hooks(
    data: dict[str, Any], root: Path = ROOT
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Remove cross-provider hooks and foreign capability origins non-destructively."""
    output = copy.deepcopy(data)
    raw_patches = output.get("provider_patches")
    if not isinstance(raw_patches, dict):
        return output, []

    ownership_view = normalize_mapping_keys(raw_patches)
    ownership = _provider_api_hosts(ownership_view)
    removed: list[dict[str, str]] = []

    for raw_provider_id, patch in raw_patches.items():
        if not isinstance(patch, dict):
            continue
        provider_id = str(raw_provider_id).casefold()
        unsafe: set[str] = set()
        for script in _script_paths(patch):
            path = (root / script).resolve()
            if root not in path.parents or not path.is_file():
                continue
            hits = _foreign_hits(
                path.read_text(encoding="utf-8", errors="ignore"),
                provider_id,
                ownership,
            )
            if hits:
                unsafe.add(script)
                removed.append({
                    "provider_id": provider_id,
                    "script": script,
                    "foreign_backends": ",".join(
                        f"{host}:{owner}" for host, owner in hits
                    ),
                })

        if unsafe:
            configured = patch.get("patch_scripts")
            if isinstance(configured, list):
                patch["patch_scripts"] = [
                    value for value in configured if str(value) not in unsafe
                ]
            if str(patch.get("patch_script") or "") in unsafe:
                patch.pop("patch_script", None)
                patch.pop("patch_options", None)
            options = patch.get("patch_script_options")
            if isinstance(options, dict):
                for script in unsafe:
                    options.pop(script, None)

    removed_origins = _sanitize_observed_origins_in_place(output, ownership)

    meta = output.get("provider_engine_normalization")
    if not isinstance(meta, dict):
        meta = {}
        output["provider_engine_normalization"] = meta
    meta.update({
        "schema_version": max(int(meta.get("schema_version") or 0), 3),
        "activation_state_unchanged": True,
        "route_state_unchanged": True,
        "safety_quarantines_unchanged": True,
        "cross_provider_backends_forbidden": True,
        "removed_cross_provider_hooks": len(removed),
        "removed_cross_provider_capability_origins": len(removed_origins),
    })
    return output, removed


def strip_foreign_provider_wrappers(
    text: str, provider_id: str, data: dict[str, Any]
) -> tuple[str, list[dict[str, str]]]:
    """Strip only repository-owned NUVIO wrapper blocks that call another provider backend."""
    patches = normalize_mapping_keys(data.get("provider_patches"))
    ownership = _provider_api_hosts(patches)
    markers = list(OWNED_WRAPPER_MARKER_RE.finditer(text))
    if not markers:
        return text, []
    parts: list[str] = []
    cursor = 0
    removed: list[dict[str, str]] = []
    for index, marker in enumerate(markers):
        start = marker.start()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        segment = text[start:end]
        hits = _foreign_hits(segment, provider_id.casefold(), ownership)
        parts.append(text[cursor:start])
        if hits:
            removed.append({
                "provider_id": provider_id.casefold(),
                "marker": marker.group(1),
                "foreign_backends": ",".join(f"{host}:{owner}" for host, owner in hits),
            })
        else:
            parts.append(segment)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts).rstrip() + "\n", removed


def validate_provider_isolation(data: dict[str, Any], root: Path = ROOT) -> list[str]:
    patches = normalize_mapping_keys(data.get("provider_patches"))
    ownership = _provider_api_hosts(patches)
    violations: list[str] = []
    for provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        for script in _script_paths(patch):
            path = (root / script).resolve()
            if root not in path.parents or not path.is_file():
                continue
            for host, owner in _foreign_hits(
                path.read_text(encoding="utf-8", errors="ignore"), provider_id, ownership
            ):
                violations.append(
                    f"{provider_id}: {script} references foreign provider backend {host} owned by {owner}"
                )
    return sorted(set(violations))


def validate_published_provider_isolation(
    data: dict[str, Any], manifest: dict[str, Any], root: Path = ROOT
) -> list[str]:
    patches = normalize_mapping_keys(data.get("provider_patches"))
    ownership = _provider_api_hosts(patches)
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
        for host, owner in _foreign_hits(
            path.read_text(encoding="utf-8", errors="ignore"), provider_id, ownership
        ):
            violations.append(
                f"{provider_id}: published bundle {filename} references foreign provider backend {host} owned by {owner}"
            )
    return sorted(set(violations))
