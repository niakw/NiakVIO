#!/usr/bin/env python3
"""Deterministic, network-free compiler for Niakvio provider bundles.

The compiler does not discover domains and does not repair provider access.
It takes the exact currently-known provider JS + manifest/config contract,
removes repository-owned cross-provider wrappers, normalizes the provider
contract, and emits a clean content-addressed candidate tree.

This creates a stable boundary between:
  1. provider source/implementation,
  2. normalized provider contract,
  3. later runtime discovery/health/resolution.

No compiled candidate is published by this script.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from provider_engine_normalizer import (
    _host,
    _host_belongs,
    _provider_api_hosts,
    normalize_mapping_keys,
    sanitize_provider_hooks,
    strip_foreign_provider_wrappers,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_OVERRIDES = ROOT / "provider-overrides.json"
DEFAULT_OUTPUT = ROOT / "staging" / "provider-rebuild"
CONTRACT_MARKER = "NUVIO_PROVIDER_CONTRACT_V1"
CONTRACT_RE = re.compile(
    r"\A/\*\s*NUVIO_PROVIDER_CONTRACT_V1:([A-Za-z0-9+/=]+)\s*\*/\n?",
    re.MULTILINE,
)


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


def _foreign_origin(value: Any, provider_id: str, api_hosts: dict[str, set[str]]) -> bool:
    host = _host(value)
    if not host:
        return False
    for owner, hosts in api_hosts.items():
        if owner == provider_id:
            continue
        if any(_host_belongs(host, owner_host) for owner_host in hosts):
            return True
    return False


def clean_origins(values: Any, provider_id: str, api_hosts: dict[str, set[str]]) -> list[str]:
    output: list[str] = []
    for raw in values if isinstance(values, list) else []:
        value = str(raw).strip()
        if not value or _foreign_origin(value, provider_id, api_hosts):
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
    api_hosts: dict[str, set[str]],
) -> dict[str, Any]:
    patches = normalize_mapping_keys(config.get("provider_patches"))
    capabilities = normalize_mapping_keys(config.get("provider_capabilities"))
    patch = patches.get(provider_id, {}) if isinstance(patches.get(provider_id), dict) else {}
    capability = capabilities.get(provider_id, {}) if isinstance(capabilities.get(provider_id), dict) else {}

    supported_types = [
        str(value) for value in manifest_row.get("supportedTypes") or []
        if str(value) in {"movie", "tv", "anime"}
    ]
    declared_types = [
        str(value) for value in patch.get("published_types") or []
        if str(value) in {"movie", "tv", "anime"}
    ]
    if declared_types:
        supported_types = declared_types

    strategy = str(
        patch.get("capability")
        or capability.get("strategy")
        or "provider_native"
    ).strip().casefold()

    routing = {
        "official_hub": str(patch.get("official_hub") or "").strip() or None,
        "official_site": str(patch.get("official_site") or "").strip() or None,
        "official_api": str(patch.get("official_api") or "").strip() or None,
        "observed_origins": clean_origins(
            capability.get("observed_origins"), provider_id, api_hosts
        ),
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
        "backend_isolation": "provider_owned_api_only",
    }


def encode_contract(contract: dict[str, Any]) -> str:
    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return base64.b64encode(payload.encode("utf-8")).decode("ascii")


def compile_provider(
    provider_id: str,
    source: str,
    manifest_row: dict[str, Any],
    config: dict[str, Any],
    api_hosts: dict[str, set[str]],
) -> tuple[bytes, dict[str, Any], list[dict[str, str]]]:
    source = strip_existing_contract(source)
    isolated, isolation_records = strip_foreign_provider_wrappers(
        source, provider_id, config
    )
    contract = provider_contract(provider_id, manifest_row, config, api_hosts)
    header = f"/* {CONTRACT_MARKER}:{encode_contract(contract)} */\n"
    compiled = (header + isolated.lstrip("\n")).encode("utf-8")
    return compiled, contract, isolation_records


def compile_manifest(
    manifest_path: Path,
    overrides_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    raw_config = load_json(overrides_path)
    config, removed_hooks = sanitize_provider_hooks(raw_config, ROOT)
    api_hosts = _provider_api_hosts(normalize_mapping_keys(config.get("provider_patches")))

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
            rows.append({
                "provider_id": provider_id,
                "status": "missing_source",
                "source_file": filename,
            })
            continue

        source_bytes = source_path.read_bytes()
        compiled, contract, isolation_records = compile_provider(
            provider_id,
            source_bytes.decode("utf-8", errors="strict"),
            manifest_row,
            config,
            api_hosts,
        )
        digest = sha256_bytes(compiled)
        target_name = f"{safe_id(provider_id)}--compiled--{digest[:16]}.js"
        target = providers_dir / target_name
        target.write_bytes(compiled)
        rows.append({
            "provider_id": provider_id,
            "status": "compiled",
            "source_file": filename,
            "source_sha256": sha256_bytes(source_bytes),
            "compiled_file": f"providers/{target_name}",
            "compiled_sha256": digest,
            "contract_sha256": sha256_bytes(
                json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ),
            "contract": contract,
            "isolation_records": isolation_records,
        })

    registry = {
        "schema_version": 1,
        "compiler": "provider_compiler_v1",
        "network_access": False,
        "publication": False,
        "provider_count": len(rows),
        "compiled_count": sum(1 for row in rows if row.get("status") == "compiled"),
        "removed_cross_provider_hooks": removed_hooks,
        "providers": rows,
    }
    (output_dir / "contracts.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
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
        f"compiled={registry['compiled_count']}/{registry['provider_count']} "
        f"output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
