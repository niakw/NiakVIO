#!/usr/bin/env python3
"""Export a compact, transport-safe delta for the canonical ProviderBase store.

This does not mutate provider or publication state. It is intended for external
validation/transport tooling that cannot carry the full multi-megabyte
PROVENANCE.json plus every identical ProviderBase copy.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import projection_active_provider_ids

PROVENANCE = ROOT / "PROVENANCE.json"
DEFAULT_DELTA = ROOT / "automation" / "providerbase-materialization-delta.json"
DEFAULT_COMMON = ROOT / "automation" / "providerbase-common-export.js"

MATERIALIZED_FIELDS = (
    "base_filename",
    "base_sha256",
    "legacy_base_filename_before_clean_v3",
    "legacy_base_sha256_before_clean_v3",
    "base_source",
    "clean_reconstruction_verified",
    "clean_reconstruction_candidate",
    "clean_reconstruction_required",
    "clean_reconstruction_authoring_version",
    "clean_reconstruction_verified_at",
    "provider_base_role",
    "legacy_provider_js_role",
    "legacy_provider_js_executed_for_reconstruction",
    "upstream_code_executed_for_reconstruction",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delta", type=Path, default=DEFAULT_DELTA)
    parser.add_argument("--common", type=Path, default=DEFAULT_COMMON)
    args = parser.parse_args()

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    store = provenance.get("provider_base_store")
    if not isinstance(rows, dict) or not isinstance(store, dict):
        raise SystemExit("ProviderBase provenance/store missing")

    active = projection_active_provider_ids()
    exported = {}
    common_sha = None
    sample_path = None
    for provider_id in sorted(active):
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f"{provider_id}: missing provenance row")
        base_path = str(row.get("base_filename") or "").strip()
        base_sha = str(row.get("base_sha256") or "").strip().casefold()
        if not base_path.startswith("provider-bases/") or len(base_sha) != 64:
            raise SystemExit(f"{provider_id}: invalid materialized ProviderBase authority")
        path = ROOT / base_path
        if not path.is_file():
            raise SystemExit(f"{provider_id}: materialized ProviderBase missing: {base_path}")
        if common_sha is None:
            common_sha = base_sha
            sample_path = path
        elif base_sha != common_sha:
            raise SystemExit(
                f"{provider_id}: ProviderBase common digest drift {base_sha} != {common_sha}"
            )
        exported[provider_id] = {
            key: row[key]
            for key in MATERIALIZED_FIELDS
            if key in row
        }
        exported[provider_id]["delete_fields"] = ["clean_reconstruction_candidate_role"]

    if sample_path is None or common_sha is None:
        raise SystemExit("no active ProviderBase rows")

    args.delta.parent.mkdir(parents=True, exist_ok=True)
    args.common.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(sample_path, args.common)
    payload = {
        "schema_version": 1,
        "provider_count": len(exported),
        "active_provider_ids": sorted(active),
        "common_base_sha256": common_sha,
        "sample_base_path": sample_path.relative_to(ROOT).as_posix(),
        "provider_base_store": store,
        "providers": exported,
    }
    args.delta.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "FIELD_PROVIDER_BASE_MATERIALIZATION_DELTA "
        f"providers={len(exported)} common_sha256={common_sha} "
        f"sample={payload['sample_base_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
