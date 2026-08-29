#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "select_brain_learning_target.py"
spec = importlib.util.spec_from_file_location("select_brain_learning_target", path)
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
assert selected["selected"] is True
assert selected["reason"] == "daily_anomaly_rotation"
assert selected["core_is_authoritative"] is False
assert selected["provider"] in {"dead-route", "runtime-route", "blocked-but-live"}
if selected["provider"] == "dead-route":
    assert selected["needs_route_search"] is True

manual = module.select(report, explicit="runtime-route", day="2026-08-29")
assert manual["provider"] == "runtime-route"
assert manual["reason"] == "manual_target"

print("Brain Learning target selector tests passed")

healthy_report = {
    "providers": [
        {"id": "alpha", "observed_status": "healthy", "evidence": {"provider_server_accessible": True, "provider_server_successful_response": True, "provider_server_hosts": ["alpha.test"]}},
        {"id": "beta", "observed_status": "healthy", "evidence": {"provider_server_accessible": True, "provider_server_successful_response": True, "provider_server_hosts": ["beta.test"]}},
    ]
}
explore = module.select(healthy_report, day="2026-08-29")
assert explore["selected"] is True
assert explore["reason"] == "daily_hidden_failure_exploration"
assert explore["provider"] in {"alpha", "beta"}
assert explore["needs_route_search"] is False
assert explore["core_is_authoritative"] is False
