#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_provider_repair_pipeline_v6.py"
spec = importlib.util.spec_from_file_location("repair_pipeline", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

assert mod.route_recovery_provider_timeout(55, 3) == 225
assert mod.route_recovery_provider_timeout(120, 4) == 300
assert mod.route_recovery_provider_timeout(15, 1) == 120

combined = mod.combine_targeted_route_reports(
    [
        {
            "method": "proof",
            "providers": [{
                "providerId": "mallumv",
                "status": "proven",
                "routes": ["/confirm/{id}"],
                "apiRecipe": {"base": "https://provider.invalid"},
            }],
        },
        {
            "method": "per-provider-fail-soft-route-recovery",
            "providers": [{
                "providerId": "animevostfr",
                "status": "route-recovery-timeout",
                "error": "TimeoutExpired",
                "routes": [],
                "tasks": [],
            }],
        },
    ],
    ["animevostfr", "mallumv"],
    duration_ms=1234,
)
rows = {row["providerId"]: row for row in combined["providers"]}
assert rows["mallumv"]["status"] == "proven"
assert rows["mallumv"]["routes"] == ["/confirm/{id}"]
assert rows["animevostfr"]["status"] == "route-recovery-timeout"
assert combined["providersWithProvenRoutes"] == 1
assert combined["provenRouteCount"] == 1
assert combined["providerCount"] == 2

source = SCRIPT.read_text(encoding="utf-8")
assert "run_targeted_route_recovery_fail_soft" in source
assert "route-recovery-timeout" in source
assert 'if args.mode in {"repair", "force"}:' in source

print("Provider targeted route recovery fail-soft tests passed")
