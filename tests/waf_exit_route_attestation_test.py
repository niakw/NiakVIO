#!/usr/bin/env python3
"""Offline Egress gate regression: no residential label without changed route."""
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
script = root / "scripts/verify_waf_exit_route.py"
spec = importlib.util.spec_from_file_location("waf_egress", script)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
selected = {"BackendState": "Running", "ExitNodeStatus": {"ID": "redacted", "Online": True}}
mod.attest("198.51.100.11", "203.0.113.22", selected)
for before, after, status in (
    ("198.51.100.11", "198.51.100.11", selected),
    ("198.51.100.11", "203.0.113.22", {"BackendState": "Running"}),
    ("198.51.100.11", "203.0.113.22", {"BackendState": "Stopped", "ExitNodeStatus": {"ID": "x"}}),
    ("198.51.100.11", "203.0.113.22", {"BackendState": "Running", "ExitNodeStatus": {"ID": "x", "Online": False}}),
):
    try:
        mod.attest(before, after, status)
    except RuntimeError:
        pass
    else:
        raise AssertionError("unverified route accepted")
assert all(x.startswith("https://") for x in mod.ENDPOINTS)
assert "ProxyHandler({})" in script.read_text(encoding="utf-8")
print("WAF independent egress attestation contract passed")
