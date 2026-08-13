#!/usr/bin/env python3
"""Build an isolated manifest for a deterministic provider-compiler generation.

This is an offline staging step. It never changes the published manifest and
never performs network access. Activation state is preserved from the source
manifest; only provider filenames and compiler metadata are projected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "manifest.json"
DEFAULT_REGISTRY = ROOT / "staging" / "provider-rebuild" / "contracts.json"
DEFAULT_OUTPUT = ROOT / "staging" / "provider-rebuild" / "manifest.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canonical_sha(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_compiled_manifest(
    source_manifest: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    if registry.get("compiler") != "provider_compiler_v1":
        raise ValueError("unsupported provider compiler registry")
    if registry.get("network_access") is not False:
        raise ValueError("compiled registry must be network-free")
    if registry.get("publication") is not False:
        raise ValueError("compiler output may not self-authorize publication")

    compiled = {
        str(row.get("provider_id") or "").casefold(): row
        for row in registry.get("providers") or []
        if isinstance(row, dict)
        and row.get("status") == "compiled"
        and str(row.get("provider_id") or "").strip()
    }
    if len(compiled) != int(registry.get("compiled_count") or 0):
        raise ValueError("compiled provider registry count mismatch")

    output = json.loads(json.dumps(source_manifest))
    projected = 0
    missing: list[str] = []
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
        filename = str(candidate.get("compiled_file") or "").strip()
        digest = str(candidate.get("compiled_sha256") or "").strip()
        if not filename.startswith("providers/") or len(digest) != 64:
            raise ValueError(f"{provider_id}: invalid compiled artifact record")
        row["filename"] = filename
        row["compiledProviderSha256"] = digest
        row["compiledContractSha256"] = str(candidate.get("contract_sha256") or "")
        projected += 1

    output["providerCompiler"] = {
        "schema_version": 1,
        "compiler": "provider_compiler_v1",
        "source_manifest_sha256": canonical_sha(source_manifest),
        "registry_sha256": canonical_sha(registry),
        "provider_count": projected,
        "missing_provider_ids": sorted(set(missing)),
        "publication_authorized": False,
    }
    if missing:
        raise ValueError(
            "compiler generation is incomplete for source manifest: "
            + ", ".join(sorted(set(missing)))
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = load_json(args.source.resolve())
    registry = load_json(args.registry.resolve())
    compiled = build_compiled_manifest(source, registry)
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(compiled, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "compiled provider manifest generated: "
        f"providers={compiled['providerCompiler']['provider_count']} "
        f"output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
