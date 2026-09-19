#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
dispatch = (ROOT / "scripts/provider_patches/global_provider_runtime_dispatch_v1.py").read_text(encoding="utf-8")
probe = (ROOT / "scripts/nuvio_tv_probe_tmdb_ci.cjs").read_text(encoding="utf-8")
audit = (ROOT / "scripts/audit_provider_quick_yield.py").read_text(encoding="utf-8")

for needle in (
    "__niakvioProviderRuntimeDispatchErrorV1",
    'provider:String(hook&&hook.provider||"")',
    'message:String(_hookError&&_hookError.message||_hookError||"").slice(0,400)',
    '"fallback": "native-on-null-or-error"',
):
    assert needle in dispatch, needle

assert "provider_runtime_dispatch_error_v1" in probe
assert "__niakvioProviderRuntimeDispatchErrorV1" in probe
assert '"provider_runtime_hook_exception"' in audit
assert 'debug.get("provider_runtime_dispatch_error_v1")' in audit

print("provider runtime dispatch diagnostics contract passed")
