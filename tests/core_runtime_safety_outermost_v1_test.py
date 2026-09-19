#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scripts" / "apply_provider_overrides.py").read_text(encoding="utf-8")

assert "CORE_RUNTIME_MEDIA_SAFETY_OUTERMOST_V1" in SOURCE
apply_start = SOURCE.index("def apply_overrides(")
sanitizer_scope = SOURCE.index('"scope": "global_terminal_stream_sanitizer"', apply_start)
safety_scope = SOURCE.index('"scope": "global_runtime_media_safety"', apply_start)
assert safety_scope > sanitizer_scope, (sanitizer_scope, safety_scope)
needle = "text = _apply_patch_script(text, provider_id, GLOBAL_RUNTIME_MEDIA_SAFETY, safety_options, None)"
assert SOURCE.count(needle) == 1, SOURCE.count(needle)
print("CORE_RUNTIME_MEDIA_SAFETY_OUTERMOST_V1_CONTRACT_OK")
