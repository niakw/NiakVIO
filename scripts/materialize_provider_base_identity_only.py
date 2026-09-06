#!/usr/bin/env python3
"""One-shot 96/96 ProviderBase v9 materialization without route/domain mutation.

Used only by the Core identity publication transaction and removed after success.
ProviderBase is common and DATA-free, so no route sanitizer/discovery is needed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
EXPECTED = 96
RUNTIME_READER_VERSION = 9


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    # Upgrade the single common source first. This must not read or mutate routes.
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "upgrade_provider_base_runtime_v5.py")],
        cwd=ROOT,
        check=True,
    )

    sys.path.insert(0, str(ROOT / "scripts"))
    from provider_base_store import (  # noqa: PLC0415
        CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        CLEAN_RECONSTRUCTION_SOURCE,
        canonical_id,
        persist_clean_provider_seed,
        provider_base_store_metadata,
    )

    manifest = load(MANIFEST)
    provenance = load(PROVENANCE)
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise SystemExit("PROVENANCE providers map missing")
    entries = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canonical_id(str(row.get("id") or ""))
    ]
    if len(entries) != EXPECTED:
        raise SystemExit(f"expected {EXPECTED} providers, got {len(entries)}")

    now = datetime.now(timezone.utc).isoformat()
    paths: set[str] = set()
    digest: str | None = None
    for entry in entries:
        provider_id = canonical_id(str(entry.get("id") or ""))
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f"{provider_id}: missing provenance row")
        relative, current_digest, stripped = persist_clean_provider_seed(provider_id, entry)
        if stripped:
            raise SystemExit(f"{provider_id}: clean ProviderBase unexpectedly required stripping")
        if digest is None:
            digest = current_digest
        elif current_digest != digest:
            raise SystemExit(
                f"{provider_id}: common ProviderBase digest drift {current_digest} != {digest}"
            )
        paths.add(relative)
        row["base_filename"] = relative
        row["base_sha256"] = current_digest
        row["base_source"] = CLEAN_RECONSTRUCTION_SOURCE
        row["clean_reconstruction_verified"] = True
        row["clean_reconstruction_candidate"] = False
        row["clean_reconstruction_required"] = False
        row["clean_reconstruction_authoring_version"] = CLEAN_RECONSTRUCTION_AUTHORING_VERSION
        row["clean_reconstruction_verified_at"] = now
        row["provider_base_role"] = "canonical-v3-common-skeleton"
        row["legacy_provider_js_role"] = "knowledge-only"
        row["legacy_provider_js_executed_for_reconstruction"] = False
        row["upstream_code_executed_for_reconstruction"] = False

    store = provenance.get("provider_base_store")
    if not isinstance(store, dict):
        store = {}
        provenance["provider_base_store"] = store
    store.update(
        provider_base_store_metadata(
            provider_count=len(entries),
            unique_base_count=len(paths),
            clean_reconstructed=len(entries),
            reconstruction_required=0,
            previous_store=store,
        )
    )
    store["materialization_mode"] = "identity-only-owned-common-v3-skeleton"
    store["provider_js_seed_used"] = False
    store["upstream_js_seed_used"] = False
    store["route_or_domain_mutation"] = False
    store["materialized_at"] = now
    store["runtime_reader_version"] = RUNTIME_READER_VERSION

    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "IDENTITY_ONLY_PROVIDER_BASE_OK "
        f"providers={len(entries)} unique_paths={len(paths)} common_digest={digest} "
        f"runtime_reader=v{RUNTIME_READER_VERSION} route_or_domain_mutation=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
