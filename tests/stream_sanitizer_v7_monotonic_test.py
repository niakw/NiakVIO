#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "upgrade_stream_sanitizer_v7_selection.py"
spec = importlib.util.spec_from_file_location("stream_sanitizer_v7_monotonic", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

synthetic = (
    '# NUVIO_STREAM_SANITIZER_V10_SELECTION\n'
    'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v10.py"\n'
    '    "scripts/provider_patches/stream_output_sanitizer_v7.py",\n'
)
version, selected = mod._current_selection(synthetic)
assert version == 10, (version, selected)
assert selected.endswith("stream_output_sanitizer_v10.py"), selected
assert mod._newer_current(synthetic) is True
assert mod.NEWER_SANITIZERS[8].endswith("stream_output_sanitizer_v8.py")
assert mod.NEWER_SANITIZERS[9].endswith("stream_output_sanitizer_v9.py")
assert mod.NEWER_SANITIZERS[10].endswith("stream_output_sanitizer_v10.py")

before_overrides = mod.OVERRIDES.read_text(encoding="utf-8")
before_hashes = mod.HASHES.read_text(encoding="utf-8")
version, selected = mod._current_selection(before_overrides)
assert version >= 8, (version, selected)
assert selected in before_hashes, selected
assert mod.patch_overrides() is False
assert mod.patch_hashes() is False
assert mod.OVERRIDES.read_text(encoding="utf-8") == before_overrides
assert mod.HASHES.read_text(encoding="utf-8") == before_hashes

print(f"stream sanitizer V7 monotonic migration contract passed current=v{version}")
