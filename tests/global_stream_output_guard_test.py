#!/usr/bin/env python3
"""Every published provider must materialize the Core terminal stream sanitizer."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides  # noqa: E402

# Keep the historical legacy-guard removal contract too.
result = subprocess.run([sys.executable, str(ROOT / "tests/provider_capabilities_test.py")], check=False)
if result.returncode:
    raise SystemExit(result.returncode)

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
rows = manifest.get("scrapers") or []
assert len(rows) == 96, f"expected complete 96-provider publication, got {len(rows)}"

missing = []
weak = []
for row in rows:
    provider_id = str(row.get("id") or "").strip()
    relative = str(row.get("filename") or "").strip()
    assert provider_id and relative.startswith("providers/"), row
    source = (ROOT / relative).read_bytes()
    patched, _records = apply_overrides(provider_id, source, phase="discovery")
    text = patched.decode("utf-8")
    sanitizer_start = "/* STARTFIX:CORE.STREAM_SANITIZER.V6 */"
    sanitizer_close = "/* CLOSEFIX:CORE.STREAM_SANITIZER.V6 */"
    if text.count(sanitizer_start) != 1 or text.count(sanitizer_close) != 1:
        missing.append(provider_id)
    if "/* START NIAKVIO_FIX:CORE.STREAM_SANITIZER.V6 */" in text:
        weak.append(provider_id)
    if "NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6" in text:
        weak.append(provider_id)
    branding = text.rfind("/* STARTFIX:CORE.PROVIDER_BRANDING.V1 */")
    sanitizer = text.rfind(sanitizer_start)
    if branding >= 0 and sanitizer <= branding:
        weak.append(provider_id)
    compact = "".join(text.split())
    if "if(!item.probe)returnconfig.probeAllUrls?null:item.stream;" not in compact:
        weak.append(provider_id)

assert not missing, f"providers missing terminal sanitizer V6: {missing}"
assert not weak, f"providers still pass unprobed stream rows or stale ownership markers: {sorted(set(weak))}"
print(f"global stream output guard passed: providers={len(rows)} managed_terminal_sanitizer={len(rows)} startfix_v3=true")
