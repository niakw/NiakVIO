#!/usr/bin/env python3
"""One-shot, network-free rebuild of a complete Niakvio provider generation.

Pipeline:
  source manifest + exact JS + overrides
    -> provider_compiler_v2
    -> verify every compiled SHA and embedded contract
    -> build isolated manifest referencing only compiled bytes
    -> emit immutable generation evidence

This script never probes providers and never publishes to the repository.
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

import provider_compiler

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_OVERRIDES = ROOT / "provider-overrides.json"
DEFAULT_OUTPUT = ROOT / "staging" / "provider-rebuild"
MARKER = re.compile(r"\A/\*\s*NUVIO_PROVIDER_CONTRACT_V1:([A-Za-z0-9+/=]+)\s*\*/")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_compiled_registry(registry: dict[str, Any], output_dir: Path) -> list[dict[str, str]]:
    if registry.get("compiler") != "provider_compiler_v2" or int(registry.get("schema_version") or 0) != 2:
        raise ValueError("provider_compiler_v2 registry required")
    if registry.get("network_access") is not False or registry.get("publication") is not False:
        raise ValueError("compiler registry must be offline and non-publishing")
    if registry.get("residual_cross_provider_backends_allowed") is not False:
        raise ValueError("compiler did not assert fail-closed backend isolation")

    verified: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for row in registry.get("providers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("provider_id") or "").strip().casefold()
        if row.get("status") != "compiled":
            raise ValueError(f"{provider_id or 'provider'}: compiler generation is incomplete")
        if not provider_id or provider_id in seen_ids:
            raise ValueError(f"duplicate or missing provider id: {provider_id!r}")
        seen_ids.add(provider_id)
        relative = str(row.get("compiled_file") or "").strip()
        if not relative.startswith("providers/") or relative in seen_files:
            raise ValueError(f"{provider_id}: invalid or duplicate compiled file: {relative}")
        seen_files.add(relative)
        path = (output_dir / relative).resolve()
        if output_dir.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"{provider_id}: missing compiled artifact: {relative}")
        data = path.read_bytes()
        actual_sha = sha256(data)
        if actual_sha != str(row.get("compiled_sha256") or ""):
            raise ValueError(f"{provider_id}: compiled SHA mismatch")
        text = data.decode("utf-8", errors="strict")
        marker = MARKER.match(text)
        if marker is None:
            raise ValueError(f"{provider_id}: missing embedded provider contract")
        try:
            embedded = json.loads(base64.b64decode(marker.group(1)).decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"{provider_id}: invalid embedded provider contract") from exc
        declared = row.get("contract")
        if not isinstance(declared, dict) or declared != embedded:
            raise ValueError(f"{provider_id}: registry/embedded contract mismatch")
        if str(embedded.get("provider_id") or "").casefold() != provider_id:
            raise ValueError(f"{provider_id}: embedded provider id mismatch")
        if embedded.get("backend_isolation") != "provider_owned_backend_only":
            raise ValueError(f"{provider_id}: backend isolation contract missing")
        contract_sha = sha256(canonical_bytes(embedded))
        if contract_sha != str(row.get("contract_sha256") or ""):
            raise ValueError(f"{provider_id}: contract SHA mismatch")
        verified.append({
            "provider_id": provider_id,
            "path": relative,
            "sha256": actual_sha,
            "contract_sha256": contract_sha,
            "source_sha256": str(row.get("source_sha256") or ""),
        })
    if len(verified) != int(registry.get("compiled_count") or 0):
        raise ValueError("compiled registry count mismatch")
    return sorted(verified, key=lambda row: row["provider_id"])


def build_rebuilt_manifest(source: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    compiled = {
        str(row.get("provider_id") or "").casefold(): row
        for row in registry.get("providers") or []
        if isinstance(row, dict) and row.get("status") == "compiled"
    }
    output = json.loads(json.dumps(source))
    missing: list[str] = []
    projected = 0
    for row in output.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        candidate = compiled.get(provider_id)
        if candidate is None:
            missing.append(provider_id)
            continue
        row["filename"] = str(candidate["compiled_file"])
        row["compiledProviderSha256"] = str(candidate["compiled_sha256"])
        row["compiledContractSha256"] = str(candidate["contract_sha256"])
        projected += 1
    if missing:
        raise ValueError("rebuild missing provider ids: " + ", ".join(sorted(set(missing))))
    output["providerRebuild"] = {
        "schema_version": 1,
        "compiler": "provider_compiler_v2",
        "provider_count": projected,
        "backend_isolation": "provider_owned_backend_only",
        "network_access": False,
        "publication_authorized": False,
    }
    return output


def rebuild(manifest_path: Path, overrides_path: Path, output_dir: Path) -> dict[str, Any]:
    registry = provider_compiler.compile_manifest(manifest_path, overrides_path, output_dir)
    verified = verify_compiled_registry(registry, output_dir)
    source = load_json(manifest_path)
    rebuilt_manifest = build_rebuilt_manifest(source, registry)
    manifest_path_out = output_dir / "manifest.json"
    manifest_path_out.write_text(json.dumps(rebuilt_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    generation_payload = {
        "schema_version": 1,
        "compiler": "provider_compiler_v2",
        "source_manifest_sha256": sha256(manifest_path.read_bytes()),
        "source_overrides_sha256": sha256(overrides_path.read_bytes()),
        "rebuilt_manifest_sha256": sha256(manifest_path_out.read_bytes()),
        "providers": verified,
    }
    generation = {
        **generation_payload,
        "generation_sha256": sha256(canonical_bytes(generation_payload)),
    }
    (output_dir / "generation.json").write_text(json.dumps(generation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return generation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.clean and output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    generation = rebuild(args.manifest.resolve(), args.overrides.resolve(), output)
    print(
        "provider rebuild complete: "
        f"providers={len(generation['providers'])} generation={generation['generation_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
