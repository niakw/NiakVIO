#!/usr/bin/env python3
"""Deterministic, network-free compiler for Niakvio provider bundles.

The compiler turns the exact currently-known JS into an isolated candidate
bundle with an embedded provider contract. It never discovers routes, never
repairs access and never publishes its output.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from provider_engine_normalizer import normalize_mapping_keys, sanitize_provider_hooks

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_OVERRIDES = ROOT / "provider-overrides.json"
DEFAULT_OUTPUT = ROOT / "staging" / "provider-rebuild"
CONTRACT_MARKER = "NUVIO_PROVIDER_CONTRACT_V1"
CONTRACT_RE = re.compile(r"\A/\*\s*NUVIO_PROVIDER_CONTRACT_V1:([A-Za-z0-9+/=]+)\s*\*/\n?", re.MULTILINE)
URL_RE = re.compile(r"https?://[^\s\"'`<>\\)]+", re.I)
MARKER_RE = re.compile(r"/\*\s*(NUVIO_[A-Z0-9_:.-]+)\s*\*/", re.I)
INFRASTRUCTURE_HOSTS = {
    "api.themoviedb.org", "raw.githubusercontent.com", "api.github.com", "github.com",
    "www.github.com", "graphql.anilist.co", "api.jikan.moe", "api.tvmaze.com",
    "cdn.jsdelivr.net", "unpkg.com", "fonts.googleapis.com", "fonts.gstatic.com",
    "image.tmdb.org", "objects.githubusercontent.com",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.casefold()).strip(".-") or "provider"


def strip_existing_contract(source: str) -> str:
    return CONTRACT_RE.sub("", source, count=1)


def host(raw: Any) -> str | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = "https://" + value.lstrip("/")
    try:
        return (urlparse(value).hostname or "").casefold() or None
    except ValueError:
        return None


def belongs(hostname: str, owner_host: str) -> bool:
    return hostname == owner_host or hostname.endswith("." + owner_host)


def provider_token(provider_id: str) -> str:
    return re.sub(r"[^a-z0-9]", "", provider_id.casefold())


FAMILY_SUFFIXES = ("official", "homes", "home", "new", "rip", "co", "tv", "app", "web")


def provider_family_token(provider_id: str) -> str:
    token = provider_token(provider_id)
    changed = True
    while changed:
        changed = False
        for suffix in FAMILY_SUFFIXES:
            if token.endswith(suffix) and len(token) - len(suffix) >= 4:
                token = token[:-len(suffix)]
                changed = True
                break
    return token


def same_provider_family(left: str, right: str) -> bool:
    return provider_family_token(left) == provider_family_token(right)


def looks_provider_owned(candidate: str, provider_id: str, strong: set[str]) -> bool:
    if any(belongs(candidate, base) or belongs(base, candidate) for base in strong):
        return True
    token = provider_token(provider_id)
    normalized = re.sub(r"[^a-z0-9]", "", candidate)
    return len(token) >= 4 and token in normalized


def declared_backend_hosts(config: dict[str, Any]) -> dict[str, set[str]]:
    """Map each provider to strong hosts it owns.

    Explicit official API/site/hub hosts are strong. Fixed endpoints and domain
    replacements are included only if they are related to a strong provider
    host or visibly provider-branded, so shared CDN/player hosts are not claimed.
    """
    patches = normalize_mapping_keys(config.get("provider_patches"))
    output: dict[str, set[str]] = {}
    for provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        strong: set[str] = set()
        for key in ("official_api", "official_site", "official_hub"):
            value = host(patch.get(key))
            if value and value not in INFRASTRUCTURE_HOSTS:
                strong.add(value)
        derived: set[str] = set()
        fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
        for key in ("api", "referer", "origin"):
            value = host(fixed.get(key))
            if value and value not in INFRASTRUCTURE_HOSTS and looks_provider_owned(value, provider_id, strong):
                derived.add(value)
        for mapping_key in ("runtime_domain_replacements", "route_replacements", "replacements"):
            mapping = patch.get(mapping_key) if isinstance(patch.get(mapping_key), dict) else {}
            for raw in mapping.values():
                value = host(raw)
                if value and value not in INFRASTRUCTURE_HOSTS and looks_provider_owned(value, provider_id, strong):
                    derived.add(value)
        owned = strong | derived
        if owned:
            output[provider_id] = owned
    return output


def current_provider_owns(hostname: str, provider_id: str, ownership: dict[str, set[str]]) -> bool:
    provider_id = provider_id.casefold()
    if any(belongs(hostname, own) for own in ownership.get(provider_id, set())):
        return True
    token = provider_token(provider_id)
    normalized = re.sub(r"[^a-z0-9]", "", hostname.casefold())
    return len(token) >= 4 and token in normalized


def foreign_hits(text: str, provider_id: str, ownership: dict[str, set[str]]) -> list[tuple[str, str]]:
    provider_id = provider_id.casefold()
    hits: list[tuple[str, str]] = []
    for raw in URL_RE.findall(text):
        value = host(raw.rstrip(".,;"))
        if not value or value in INFRASTRUCTURE_HOSTS:
            continue
        if current_provider_owns(value, provider_id, ownership):
            continue
        for owner, hosts in ownership.items():
            if owner == provider_id or same_provider_family(provider_id, owner):
                continue
            if any(belongs(value, owner_host) for owner_host in hosts):
                hits.append((value, owner))
    return sorted(set(hits))


def script_paths(patch: dict[str, Any]) -> list[str]:
    scripts = [str(value) for value in patch.get("patch_scripts") or [] if str(value).strip()]
    legacy = str(patch.get("patch_script") or "").strip()
    if legacy and legacy not in scripts:
        scripts.append(legacy)
    return scripts


def sanitize_complete_backend_hooks(
    config: dict[str, Any], root: Path
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    output = copy.deepcopy(config)
    patches = normalize_mapping_keys(output.get("provider_patches"))
    output["provider_patches"] = patches
    ownership = declared_backend_hosts(output)
    removed: list[dict[str, str]] = []
    root = root.resolve()
    for provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        unsafe: set[str] = set()
        for script in script_paths(patch):
            path = (root / script).resolve()
            if root not in path.parents or not path.is_file():
                continue
            hits = foreign_hits(path.read_text(encoding="utf-8", errors="ignore"), provider_id, ownership)
            if not hits:
                continue
            unsafe.add(script)
            removed.append({
                "provider_id": provider_id,
                "script": script,
                "foreign_backends": ",".join(f"{backend}:{owner}" for backend, owner in hits),
            })
        if not unsafe:
            continue
        configured = patch.get("patch_scripts")
        if isinstance(configured, list):
            patch["patch_scripts"] = [str(value) for value in configured if str(value) not in unsafe]
        if str(patch.get("patch_script") or "") in unsafe:
            patch.pop("patch_script", None)
            patch.pop("patch_options", None)
        options = patch.get("patch_script_options")
        if isinstance(options, dict):
            for script in unsafe:
                options.pop(script, None)
    return output, removed


def sanitize_observed_origins(
    config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    output = copy.deepcopy(config)
    ownership = declared_backend_hosts(output)
    capabilities = normalize_mapping_keys(output.get("provider_capabilities"))
    output["provider_capabilities"] = capabilities
    removed: list[dict[str, str]] = []
    for provider_id, row in capabilities.items():
        if not isinstance(row, dict) or not isinstance(row.get("observed_origins"), list):
            continue
        kept: list[Any] = []
        for raw in row["observed_origins"]:
            value = host(raw)
            owners: list[str] = []
            if value and not current_provider_owns(value, provider_id, ownership):
                owners = sorted(
                    owner for owner, hosts in ownership.items()
                    if owner != provider_id
                    and not same_provider_family(provider_id, owner)
                    and any(belongs(value, own) for own in hosts)
                )
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
    return output, removed


def strip_foreign_owned_wrappers(
    text: str, provider_id: str, config: dict[str, Any]
) -> tuple[str, list[dict[str, str]]]:
    ownership = declared_backend_hosts(config)
    markers = list(MARKER_RE.finditer(text))
    if not markers:
        return text, []
    parts: list[str] = []
    cursor = 0
    removed: list[dict[str, str]] = []
    for index, marker in enumerate(markers):
        start = marker.start()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        segment = text[start:end]
        hits = foreign_hits(segment, provider_id, ownership)
        parts.append(text[cursor:start])
        if hits:
            removed.append({
                "provider_id": provider_id.casefold(),
                "marker": marker.group(1),
                "foreign_backends": ",".join(f"{backend}:{owner}" for backend, owner in hits),
            })
        else:
            parts.append(segment)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts).rstrip() + "\n", removed


def clean_origins(values: Any, provider_id: str, ownership: dict[str, set[str]]) -> list[str]:
    output: list[str] = []
    for raw in values if isinstance(values, list) else []:
        value = str(raw).strip()
        parsed_host = host(value)
        if not parsed_host:
            continue
        foreign = False
        if not current_provider_owns(parsed_host, provider_id, ownership):
            foreign = any(
                owner != provider_id
                and not same_provider_family(provider_id, owner)
                and any(belongs(parsed_host, own) for own in hosts)
                for owner, hosts in ownership.items()
            )
        if foreign:
            continue
        try:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            origin = f"{parsed.scheme}://{parsed.hostname.casefold()}"
        except ValueError:
            continue
        if origin not in output:
            output.append(origin)
    return output


def provider_contract(
    provider_id: str,
    manifest_row: dict[str, Any],
    config: dict[str, Any],
    ownership: dict[str, set[str]],
) -> dict[str, Any]:
    patches = normalize_mapping_keys(config.get("provider_patches"))
    capabilities = normalize_mapping_keys(config.get("provider_capabilities"))
    patch = patches.get(provider_id, {}) if isinstance(patches.get(provider_id), dict) else {}
    capability = capabilities.get(provider_id, {}) if isinstance(capabilities.get(provider_id), dict) else {}
    supported_types = [str(value) for value in manifest_row.get("supportedTypes") or [] if str(value) in {"movie", "tv", "anime"}]
    declared_types = [str(value) for value in patch.get("published_types") or [] if str(value) in {"movie", "tv", "anime"}]
    if declared_types:
        supported_types = declared_types
    strategy = str(patch.get("capability") or capability.get("strategy") or "provider_native").strip().casefold()
    routing = {
        "official_hub": str(patch.get("official_hub") or "").strip() or None,
        "official_site": str(patch.get("official_site") or "").strip() or None,
        "official_api": str(patch.get("official_api") or "").strip() or None,
        "observed_origins": clean_origins(capability.get("observed_origins"), provider_id, ownership),
    }
    fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
    if fixed:
        routing["fixed_endpoint"] = {
            "resolver_function": str(fixed.get("resolver_function") or "").strip() or None,
            "api": str(fixed.get("api") or "").strip() or None,
            "referer": str(fixed.get("referer") or "").strip() or None,
        }
    return {
        "schema_version": 1,
        "provider_id": provider_id,
        "display_name": str(manifest_row.get("name") or provider_id),
        "supported_types": supported_types,
        "strategy": strategy,
        "validation": str(capability.get("validation") or "provider_native"),
        "allow_html_url": bool(capability.get("allow_html_url", strategy in {"iframe_player", "mixed_embed_resolver", "html_scraper"})),
        "requires_direct_media": bool(capability.get("requires_direct_media", strategy == "direct_media")),
        "supports_external_player": bool(manifest_row.get("supportsExternalPlayer", False)),
        "routing": routing,
        "backend_isolation": "provider_owned_backend_only",
    }


def encode_contract(contract: dict[str, Any]) -> str:
    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return base64.b64encode(payload.encode("utf-8")).decode("ascii")


def compile_provider(
    provider_id: str,
    source: str,
    manifest_row: dict[str, Any],
    config: dict[str, Any],
    ownership: dict[str, set[str]],
) -> tuple[bytes, dict[str, Any], list[dict[str, str]]]:
    source = strip_existing_contract(source)
    isolated, isolation_records = strip_foreign_owned_wrappers(source, provider_id, config)
    remaining = foreign_hits(isolated, provider_id, ownership)
    if remaining:
        detail = ",".join(f"{backend}:{owner}" for backend, owner in remaining)
        raise ValueError(
            f"{provider_id}: cross-provider backend reference remains after isolation: {detail}"
        )
    contract = provider_contract(provider_id, manifest_row, config, ownership)
    header = f"/* {CONTRACT_MARKER}:{encode_contract(contract)} */\n"
    return (header + isolated.lstrip("\n")).encode("utf-8"), contract, isolation_records


def compile_manifest(
    manifest_path: Path,
    overrides_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    raw_config = load_json(overrides_path)
    config, removed_api_hooks = sanitize_provider_hooks(raw_config, ROOT)
    config, removed_backend_hooks = sanitize_complete_backend_hooks(config, ROOT)
    config, removed_origins = sanitize_observed_origins(config)
    removed_hooks = list(removed_api_hooks)
    removed_hooks.extend(row for row in removed_backend_hooks if row not in removed_hooks)
    ownership = declared_backend_hosts(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    providers_dir = output_dir / "providers"
    providers_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for manifest_row in manifest.get("scrapers") or []:
        if not isinstance(manifest_row, dict):
            continue
        provider_id = str(manifest_row.get("id") or "").strip().casefold()
        filename = str(manifest_row.get("filename") or "").strip()
        if not provider_id or not filename or provider_id in seen:
            continue
        seen.add(provider_id)
        source_path = (manifest_path.parent / filename).resolve()
        if ROOT not in source_path.parents or not source_path.is_file():
            rows.append({"provider_id": provider_id, "status": "missing_source", "source_file": filename})
            continue
        source_bytes = source_path.read_bytes()
        compiled, contract, isolation_records = compile_provider(
            provider_id,
            source_bytes.decode("utf-8", errors="strict"),
            manifest_row,
            config,
            ownership,
        )
        digest = sha256_bytes(compiled)
        target_name = f"{safe_id(provider_id)}--compiled--{digest[:16]}.js"
        (providers_dir / target_name).write_bytes(compiled)
        rows.append({
            "provider_id": provider_id,
            "status": "compiled",
            "source_file": filename,
            "source_sha256": sha256_bytes(source_bytes),
            "compiled_file": f"providers/{target_name}",
            "compiled_sha256": digest,
            "contract_sha256": sha256_bytes(json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")),
            "contract": contract,
            "isolation_records": isolation_records,
        })
    registry = {
        "schema_version": 2,
        "compiler": "provider_compiler_v2",
        "network_access": False,
        "publication": False,
        "provider_count": len(rows),
        "compiled_count": sum(1 for row in rows if row.get("status") == "compiled"),
        "removed_cross_provider_hooks": removed_hooks,
        "removed_cross_provider_origins": removed_origins,
        "backend_ownership": "official_api_site_hub_and_provider_related_endpoints",
        "residual_cross_provider_backends_allowed": False,
        "providers": rows,
    }
    (output_dir / "contracts.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--clean", action="store_true", help="Remove the previous compiler output first.")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    overrides_path = args.overrides.resolve()
    output_dir = args.output.resolve()
    if args.clean and output_dir.exists():
        shutil.rmtree(output_dir)
    registry = compile_manifest(manifest_path, overrides_path, output_dir)
    print(
        "provider compiler complete: "
        f"compiled={registry['compiled_count']}/{registry['provider_count']} output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
