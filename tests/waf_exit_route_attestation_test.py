#!/usr/bin/env python3
"""Offline Egress gate regression: no residential label without changed route."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

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
source = script.read_text(encoding="utf-8")
assert "ProxyHandler({})" not in source
assert '"--ipv4"' in source and '"--noproxy", "*"' in source
assert '"--max-time", "8"' in source
assert mod.PUBLIC_IP_COMMAND_TIMEOUT_SECONDS <= 12
assert mod.TAILSCALE_SET_TIMEOUT_SECONDS <= 15
assert mod.TAILSCALE_CLEAR_TIMEOUT_SECONDS <= 10
assert "pre_tailnet=true" in source
assert "baseline-public-ip-unavailable" in source
assert "post-exit-public-ip-unavailable" in source
assert "egress-unchanged" in source

original_which = mod.shutil.which
original_run = mod.subprocess.run
try:
    mod.shutil.which = lambda name: "/usr/bin/curl" if name == "curl" else original_which(name)
    ip_calls = []
    def fake_ip_run(args, **kwargs):
        ip_calls.append((list(args), kwargs.get("timeout")))
        return SimpleNamespace(returncode=0, stdout="203.0.113.22\n", stderr="")
    mod.subprocess.run = fake_ip_run
    assert mod.observed_public_ipv4() == "203.0.113.22"
    assert len(ip_calls) == len(mod.ENDPOINTS)
    assert all(timeout == mod.PUBLIC_IP_COMMAND_TIMEOUT_SECONDS for _, timeout in ip_calls)
    assert all("--max-time" in args and "--noproxy" in args for args, _ in ip_calls)
finally:
    mod.subprocess.run = original_run
    mod.shutil.which = original_which

calls = []
original_run = mod.subprocess.run
original_sleep = mod.time.sleep
try:
    def fake_run(args, **kwargs):
        calls.append((list(args), kwargs.get("timeout")))
        return SimpleNamespace(returncode=0, stdout="")

    mod.subprocess.run = fake_run
    mod.time.sleep = lambda _: None
    mod.select_exit_node("redacted-exit", attempts=1)
    mod.clear_exit_node()
finally:
    mod.subprocess.run = original_run
    mod.time.sleep = original_sleep

assert calls[0][0][:3] == ["sudo", "tailscale", "set"]
assert "--exit-node=redacted-exit" in calls[0][0]
assert calls[0][1] == mod.TAILSCALE_SET_TIMEOUT_SECONDS
assert calls[1][0][-1] == "--exit-node="
assert calls[1][1] == mod.TAILSCALE_CLEAR_TIMEOUT_SECONDS
print("WAF independent egress attestation contract passed")
