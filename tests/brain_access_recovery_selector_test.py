#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "select_brain_access_recovery.py"
spec = importlib.util.spec_from_file_location("select_brain_access_recovery", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

report = {
    "providers": [
        {
            "id": "healthy-one",
            "observed_status": "healthy",
            "evidence": {"provider_server_accessible": True, "provider_server_successful_response": True, "provider_server_hosts": ["ok.test"]},
        },
        {
            "id": "blocked-but-live",
            "observed_status": "blocked",
            "evidence": {"provider_server_accessible": True, "provider_server_successful_response": True, "provider_server_hosts": ["live.test"]},
        },
        {
            "id": "dead-route",
            "observed_status": "provider_unreachable",
            "evidence": {"provider_server_accessible": False, "provider_server_successful_response": False, "provider_server_hosts": []},
        },
        {
            "id": "runtime-route",
            "observed_status": "runtime_error",
            "evidence": {"provider_server_accessible": False, "provider_server_successful_response": False, "provider_server_hosts": []},
        },
    ]
}

selected = module.select(report, day="2026-08-29")
assert selected["provider"] == "dead-route", selected
assert selected["reason"] == "daily_rotating_access_failure"

manual = module.select(report, explicit="runtime-route", day="2026-08-29")
assert manual["provider"] == "runtime-route"
assert manual["reason"] == "manual_target"

print("Brain access recovery selector tests passed")
