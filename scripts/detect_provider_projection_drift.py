#!/usr/bin/env python3
"""Detect current Provider v3 publication projection drift without mutating bytes."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import active_provider_ids  # noqa: E402
from materialize_provider_v3_all import (  # noqa: E402
    normalize_anime_transport_compatibility,
    provider_model,
)
from provider_base_store import build_provider_data_model  # noqa: E402
from provider_patch_blocks import decode_managed_data, validate_managed_fixes  # noqa: E402
from reapply_published_overrides import (  # noqa: E402
    PUBLICATION_CONTRACT_SCHEMA,
    provider_build_input_sha,
    provider_policy_sha,
    publication_contract_sha,
    resolve_runtime_base,
)

MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
STATIC = ROOT / "automation" / "provider-v3-static-knowledge.json"
PROVENANCE = ROOT / "PROVENANCE.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def config_fix_id(provider_id: str) -> str:
    component = re.sub(r"[^A-Z0-9_.:-]+", "_", provider_id.upper()).strip("_.:-")
    return f"PROVIDER.{component}.CONFIG.V1"


def declared_fix_ids(patch: dict[str, Any]) -> list[str]:
    out: list[str] = []
    raw = patch.get("provider_lego_scripts")
    scripts = [raw] if isinstance(raw, str) else list(raw or []) if isinstance(raw, list) else []
    for value in scripts:
        rel = str(value or "").strip()
        if not rel:
            continue
        path = ROOT / rel
        if not path.is_file():
            out.append(f"MISSING_SCRIPT:{rel}")
            continue
        source = path.read_text(encoding="utf-8")
        match = re.search(r'^MANAGED_FIX_ID\s*=\s*["\']([^"\']+)["\']', source, re.M)
        if not match:
            out.append(f"MISSING_FIX_ID:{rel}")
            continue
        out.append(match.group(1))
    return out


def diff_keys(published: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    return sorted(
        key for key in set(published) | set(expected)
        if published.get(key) != expected.get(key)
    )


def detect() -> dict[str, Any]:
    manifest = load(MANIFEST)
    overrides = load(OVERRIDES)
    static = load(STATIC)
    provenance = load(PROVENANCE)
    active = active_provider_ids()
    patches = overrides.get("provider_patches") or {}
    capabilities = overrides.get("provider_capabilities") or {}
    static_rows = static.get("providers") or {}
    provenance_rows = provenance.get("providers")
    contract_meta = provenance.get("provider_publication_contract")
    if not isinstance(provenance_rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")
    if not isinstance(contract_meta, dict):
        contract_meta = {}
    current_contract_sha = publication_contract_sha(overrides, static)
    stored_contract_schema = int(contract_meta.get("schema_version") or 0)
    stored_contract_sha = str(contract_meta.get("sha256") or "").strip().casefold()
    global_contract_drift = (
        stored_contract_schema != PUBLICATION_CONTRACT_SCHEMA
        or stored_contract_sha != current_contract_sha
    )

    rows: list[dict[str, Any]] = []
    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = cid(entry.get("id"))
        if not provider_id or provider_id not in active:
            continue
        rel = str(entry.get("filename") or "").strip()
        path = ROOT / rel
        reasons: list[str] = []
        changed_keys: list[str] = []
        missing_fix_ids: list[str] = []
        changed_build_inputs: list[str] = []

        patch = patches.get(provider_id)
        capability = capabilities.get(provider_id)
        static_row = static_rows.get(provider_id)
        if not all(isinstance(value, dict) for value in (patch, capability, static_row)):
            reasons.append("structured-data-incomplete")
        else:
            provenance_row = provenance_rows.get(provider_id)
            if not isinstance(provenance_row, dict):
                reasons.append("publication-provenance-missing")
            else:
                try:
                    _base_path, base_sha = resolve_runtime_base(
                        provider_id, provenance_row, require=True
                    )
                    if not base_sha:
                        raise ValueError("missing runtime ProviderBase SHA")
                    current_policy_sha = provider_policy_sha(
                        overrides, provider_id, static
                    )
                    expected_build_input = provider_build_input_sha(
                        provider_id,
                        base_sha,
                        current_contract_sha,
                        current_policy_sha,
                        provenance_row,
                    )
                    if global_contract_drift:
                        changed_build_inputs.append("publicationContract")
                    if int(provenance_row.get("build_contract_schema") or 0) != PUBLICATION_CONTRACT_SCHEMA:
                        changed_build_inputs.append("buildContractSchema")
                    if str(provenance_row.get("provider_policy_sha256") or "").casefold() != current_policy_sha:
                        changed_build_inputs.append("providerPolicy")
                    if str(provenance_row.get("build_input_sha256") or "").casefold() != expected_build_input:
                        changed_build_inputs.append("buildInput")
                    if changed_build_inputs:
                        reasons.append("publication-build-input-drift")
                except Exception as exc:
                    reasons.append("publication-build-input-unresolved")
                    changed_build_inputs.append(type(exc).__name__)

        if not rel.startswith("providers/") or not path.is_file():
            reasons.append("published-bundle-missing")
        else:
            text = path.read_text(encoding="utf-8")
            ids = set(validate_managed_fixes(text))
            fix_id = config_fix_id(provider_id)
            if fix_id not in ids:
                reasons.append("config-lego-missing")
            else:
                published = decode_managed_data(text, fix_id)
                projected_entry = json.loads(json.dumps(entry))
                normalize_anime_transport_compatibility(projected_entry)
                model = provider_model(provider_id, patch, capability, static_row)
                expected = build_provider_data_model(
                    provider_id,
                    projected_entry,
                    known_site=model.get("knownSite"),
                    provider_model=model,
                )
                changed_keys = diff_keys(published, expected)
                if changed_keys:
                    reasons.append("provider-data-drift")

            for declared in declared_fix_ids(patch):
                if declared.startswith("MISSING_"):
                    missing_fix_ids.append(declared)
                elif declared not in ids:
                    missing_fix_ids.append(declared)
            if missing_fix_ids:
                reasons.append("declared-lego-drift")

        if reasons:
            rows.append({
                "provider": provider_id,
                "reasons": sorted(set(reasons)),
                "changedKeys": changed_keys,
                "missingFixIds": missing_fix_ids,
                "changedBuildInputs": sorted(set(changed_build_inputs)),
                "publishedFile": rel,
            })

    providers = sorted(row["provider"] for row in rows)
    return {
        "schemaVersion": 2,
        "providerCount": len(providers),
        "providers": providers,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = detect()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_PROJECTION_DRIFT "
        f"providers={report['providerCount']} ids={','.join(report['providers'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
