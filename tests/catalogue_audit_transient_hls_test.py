#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "audit_catalogue_identity_media.py"
spec = importlib.util.spec_from_file_location("catalogue_audit", path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

assert module.is_transient_media_error("hls_variant_TimeoutError: The operation was aborted due to timeout")
assert module.is_transient_media_error("hls_audio_fetch failed")
assert module.is_transient_media_error("hls_variant_HTTP 503")
assert not module.is_transient_media_error("hls_variant_invalid_playlist")
assert not module.is_transient_media_error("hls_audio_declared_track_missing")

probe = {"streams": [
    {"media": {"kind": "hls", "hls_master": True, "error": "hls_variant_TimeoutError: The operation was aborted due to timeout"}},
    {"media": {"kind": "hls", "hls_master": True, "error": "hls_variant_invalid_playlist"}},
]}
summary = module.summarize_media(probe)
assert summary["hls_transient_failures"] == 1, summary
assert summary["hls_variant_failures"] == 1, summary
assert summary["hls_audio_failures"] == 0, summary
print("catalogue audit transient-vs-structural HLS tests passed")
