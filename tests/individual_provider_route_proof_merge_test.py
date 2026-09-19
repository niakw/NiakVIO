#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "merge_provider_route_recovery_reports.py"
spec = importlib.util.spec_from_file_location("merge_individual", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

active = sorted(module.current_scope.active_provider_ids())
assert active
with tempfile.TemporaryDirectory(prefix="niakvio-individual-merge-") as tmp:
    root = Path(tmp)
    paths = []
    for index, provider_id in enumerate(active):
        payload = {
            "schemaVersion": module.recovery.PROOF_VERSION,
            "providerCount": 1,
            "catalogueProviderCount": len(active),
            "providers": [{
                "providerId": provider_id,
                "status": "proven" if index == 0 else "no-proven-route",
                "routes": ["/?s={query}"] if index == 0 else [],
                "executionRoutes": ["/?s={query}"] if index == 0 else [],
                "routeData": [],
                "apiRecipe": None,
                "tasks": [],
            }],
        }
        path = root / f"{index:03d}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths.append(path)

    merged = module.merge(paths, "active")
    assert merged["providerCount"] == len(active), merged
    assert len(merged["providers"]) == len(active), merged
    assert merged["providersWithProvenRoutes"] == 1, merged
    assert merged["authorityIsolation"] == "one-provider-one-proof-job-no-cross-provider-domain-or-route-sharing"

print("individual provider route proof merge test passed")
