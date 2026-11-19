#!/usr/bin/env python3
"""Offline Egress gate regression: no residential label without changed route."""
import importlib.util
import io
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
script = root / "scripts/verify_waf_exit_route.py"
spec = importlib.util.spec_from_file_location("waf_egress", script)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
selected = {"BackendState": "Running", "ExitNodeStatus": {"ID": "redacted", "Online": True}}
mod.attest("8.8.4.4", "9.9.9.9", selected)
for before, after, status in (
    ("8.8.4.4", "8.8.4.4", selected),
    ("8.8.4.4", "9.9.9.9", {"BackendState": "Running"}),
    ("8.8.4.4", "9.9.9.9", {"BackendState": "Stopped", "ExitNodeStatus": {"ID": "x"}}),
    ("8.8.4.4", "9.9.9.9", {"BackendState": "Running", "ExitNodeStatus": {"ID": "x", "Online": False}}),
    ("8.8.4.4", "10.0.0.1", selected),
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
assert '"--fail"' in source
assert "FIELD_WAF_EXIT_ENDPOINT" in source
assert '"--max-time", "6"' in source
assert "https://1.1.1.1/cdn-cgi/trace" in source
assert mod.PUBLIC_IP_COMMAND_TIMEOUT_SECONDS <= 10
assert mod._extract_public_ipv4("9.9.9.9\n") == "9.9.9.9"
assert mod._extract_public_ipv4("fl=1\nip=9.9.9.10\nts=1\n") == "9.9.9.10"
for not_public in ("10.0.0.1", "100.64.0.1", "127.0.0.1", "198.51.100.2", "203.0.113.4"):
    try:
        mod._extract_public_ipv4("ip=" + not_public + "\n")
    except ValueError:
        pass
    else:
        raise AssertionError(f"non-public address accepted: {not_public}")
assert mod.TAILSCALE_SET_TIMEOUT_SECONDS <= 15
assert mod.TAILSCALE_CLEAR_TIMEOUT_SECONDS <= 10
assert "pre_tailnet=true" in source
assert "baseline-public-ip-unavailable" in source
assert "post-exit-public-ip-unavailable" in source
assert "exit-selected-public-internet-unavailable" in source
assert "FIELD_WAF_EXIT_STATUS" in source
assert "FIELD_WAF_EXIT_PUBLIC_PROBE" in source
assert mod.EGRESS_VERIFY_ATTEMPTS == 3
assert "egress-unchanged" in source

original_which = mod.shutil.which
original_run = mod.subprocess.run
try:
    mod.shutil.which = lambda name: "/usr/bin/curl" if name == "curl" else original_which(name)
    ip_calls = []
    responses = [
        SimpleNamespace(returncode=0, stdout="not-an-ip\n", stderr=""),
        SimpleNamespace(returncode=0, stdout="9.9.9.9\n", stderr=""),
    ]
    def fake_ip_run(args, **kwargs):
        ip_calls.append((list(args), kwargs.get("timeout")))
        return responses.pop(0)
    mod.subprocess.run = fake_ip_run
    safe_trace = io.StringIO()
    with redirect_stdout(safe_trace):
        assert mod.observed_public_ipv4() == "9.9.9.9"
    assert len(ip_calls) == 2
    assert "result=no_public_ipv4" in safe_trace.getvalue()
    assert "result=public_ipv4" in safe_trace.getvalue()
    assert "9.9.9.9" not in safe_trace.getvalue()
    assert all(timeout == mod.PUBLIC_IP_COMMAND_TIMEOUT_SECONDS for _, timeout in ip_calls)
    assert all("--max-time" in args and "--noproxy" in args for args, _ in ip_calls)
finally:
    mod.subprocess.run = original_run
    mod.shutil.which = original_which

# Exit selection is control-plane evidence only. Dataplane qualification retries
# a bounded number of times and succeeds only after public egress changes.
original_status = mod.exit_status
original_observed = mod.observed_public_ipv4
original_sleep = mod.time.sleep
try:
    mod.exit_status = lambda: selected
    observations = [RuntimeError("public IPv4 cannot be independently established"), "8.8.4.4", "9.9.9.11"]
    def fake_observed():
        value = observations.pop(0)
        if isinstance(value, Exception):
            raise value
        return value
    sleeps = []
    mod.observed_public_ipv4 = fake_observed
    mod.time.sleep = lambda value: sleeps.append(value)
    assert mod.verify_converged_exit("8.8.4.4", attempts=3) == "9.9.9.11"
    assert sleeps == [2, 4], sleeps
finally:
    mod.exit_status = original_status
    mod.observed_public_ipv4 = original_observed
    mod.time.sleep = original_sleep

original_status = mod.exit_status
original_observed = mod.observed_public_ipv4
original_sleep = mod.time.sleep
try:
    mod.exit_status = lambda: selected
    mod.observed_public_ipv4 = lambda: (_ for _ in ()).throw(RuntimeError("public IPv4 cannot be independently established"))
    mod.time.sleep = lambda _: None
    try:
        mod.verify_converged_exit("8.8.4.4", attempts=3)
    except RuntimeError as error:
        assert "no observable public internet" in str(error)
    else:
        raise AssertionError("exit without public internet accepted")
finally:
    mod.exit_status = original_status
    mod.observed_public_ipv4 = original_observed
    mod.time.sleep = original_sleep

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
