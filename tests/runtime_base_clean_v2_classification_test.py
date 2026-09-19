#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_base_store as base_store  # noqa: E402
import reapply_published_overrides as reapply  # noqa: E402

provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
rows = provenance.get("providers") or {}

pending_checked = 0
clean_checked = 0
for provider_id, row in rows.items():
    if not isinstance(row, dict):
        continue
    if base_store.is_clean_reconstruction_candidate(row):
        runtime_path, _ = base_store.resolve_runtime_base(provider_id, row, require=True)
        assert runtime_path is not None
        legacy = str(row.get("legacy_base_filename_before_clean_candidate") or "").strip()
        if legacy and runtime_path.relative_to(ROOT).as_posix() == legacy:
            assert reapply.runtime_base_is_clean_v2(provider_id, row, runtime_path) is False
            pending_checked += 1
    elif base_store.is_clean_reconstructed(row):
        runtime_path, _ = base_store.resolve_runtime_base(provider_id, row, require=True)
        assert runtime_path is not None
        assert reapply.runtime_base_is_clean_v2(provider_id, row, runtime_path) is True
        clean_checked += 1

assert pending_checked > 0, "expected at least one pending clean candidate using preserved legacy LKG"
assert clean_checked > 0, "expected at least one verified clean v2 ProviderBase"
print(
    "runtime ProviderBase classification passed: "
    f"pending_legacy={pending_checked} verified_clean={clean_checked}"
)
