#!/usr/bin/env python3
'''Create the canonical 96 ProviderBase v3 store from the owned common skeleton.

Before importing the ProviderBase generator, apply the deterministic execution
route sanitizer and the common runtime v5 upgrade. This ordering guarantees that
all 96 generated bundles use the same repaired DATA/runtime contract.
'''
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
EXPECTED = 96


def prepare_runtime() -> None:
    commands = (
        ROOT / "scripts" / "sanitize_provider_v3_execution_routes_v1.py",
        ROOT / "scripts" / "upgrade_provider_base_runtime_v5.py",
    )
    for script in commands:
        subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)


def main() -> int:
    prepare_runtime()

    # Import after runtime preparation. Importing earlier would cache the v4
    # ProviderBase module and silently materialize stale bytes.
    sys.path.insert(0, str(ROOT / "scripts"))
    from materialize_provider_v3_all import load, provider_model
    from provider_base_store import (
        CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        CLEAN_RECONSTRUCTION_SOURCE,
        MANIFEST,
        PROVENANCE,
        canonical_id,
        persist_clean_provider_seed,
        provider_base_store_metadata,
    )

    manifest = load(MANIFEST)
    overrides = load(OVERRIDES)
    provenance = load(PROVENANCE)
    patches = overrides.get("provider_patches")
    capabilities = overrides.get("provider_capabilities")
    rows = provenance.get("providers")
    if not isinstance(patches, dict) or not isinstance(capabilities, dict) or not isinstance(rows, dict):
        raise SystemExit("ProviderBase v3 store requires patches/capabilities/provenance maps")

    entries = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canonical_id(str(row.get("id") or ""))
    ]
    if len(entries) != EXPECTED:
        raise SystemExit(f"ProviderBase v3 store requires {EXPECTED} providers, got {len(entries)}")

    # Read the sanitized static knowledge explicitly so ProviderBase seed DATA
    # and the later all-provider materializer see the same runtime family.
    static_knowledge = load(ROOT / "automation" / "provider-v3-static-knowledge.json")
    static_rows = static_knowledge.get("providers")
    if not isinstance(static_rows, dict) or len(static_rows) != EXPECTED:
        raise SystemExit("sanitized Provider v3 static knowledge must contain 96 providers")

    now = datetime.now(timezone.utc).isoformat()
    created = []
    unique = set()
    for entry in entries:
        pid = canonical_id(str(entry.get("id") or ""))
        patch = patches.get(pid)
        capability = capabilities.get(pid)
        row = rows.get(pid)
        static_row = static_rows.get(pid)
        if not isinstance(patch, dict) or not isinstance(capability, dict) or not isinstance(row, dict) or not isinstance(static_row, dict):
            raise SystemExit(f"{pid}: incomplete ProviderBase source metadata")

        model = provider_model(pid, patch, capability, static_row)
        old_file = str(row.get("base_filename") or "").strip()
        old_sha = str(row.get("base_sha256") or "").strip().casefold()
        relative, digest, _ = persist_clean_provider_seed(
            pid,
            entry,
            known_site=model.get("knownSite"),
            provider_model=model,
            overrides_path=OVERRIDES,
        )
        if old_file and old_file != relative and not row.get("legacy_base_filename_before_clean_v3"):
            row["legacy_base_filename_before_clean_v3"] = old_file
            if old_sha:
                row["legacy_base_sha256_before_clean_v3"] = old_sha

        row["base_filename"] = relative
        row["base_sha256"] = digest
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
        row.pop("clean_reconstruction_candidate_role", None)
        unique.add(relative)
        created.append(pid)

    store = provenance.get("provider_base_store")
    if not isinstance(store, dict):
        store = {}
        provenance["provider_base_store"] = store
    store.update(provider_base_store_metadata(
        provider_count=len(created),
        unique_base_count=len(unique),
        clean_reconstructed=len(created),
        reconstruction_required=0,
        previous_store=store,
    ))
    store["materialization_mode"] = "owned-common-v3-skeleton"
    store["provider_js_seed_used"] = False
    store["upstream_js_seed_used"] = False
    store["materialized_at"] = now
    store["runtime_reader_version"] = 5
    store["execution_route_sanitizer_version"] = 1

    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"FIELD_PROVIDER_BASE_V3_STORE providers={len(created)} "
        f"unique_paths={len(unique)} reconstruction_required=0 "
        "provider_js_seed=false upstream_js_seed=false runtime_reader=v5 route_sanitizer=v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
