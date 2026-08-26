#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parts=[ROOT/f"scripts/.v12-staging-part{i}.b64" for i in range(1,5)]
payload=base64.b64decode("".join(p.read_text(encoding="utf-8").strip() for p in parts))
expected="8b436e032540e3c3f054efdcb43447234a079d57000555d96b366ca52fcb17a5"
actual=hashlib.sha256(payload).hexdigest()
if actual != expected:
    raise SystemExit(f"V12 payload checksum mismatch: {actual} != {expected}")
target=ROOT/"scripts/provider_patches/global_stream_presentation_v1.py"
target.write_bytes(payload)
for p in parts:
    p.unlink()
Path(__file__).unlink()
print(f"FIELD_STREAM_PRESENTATION_V12_MATERIALIZED sha256={actual} bytes={len(payload)}")
