#!/usr/bin/env python3
"""One-shot tracer for the published-provider fixed-point check.

This file is temporary diagnostic machinery and must be removed once the slow
provider/profile is identified. It deliberately executes the real checker while
wrapping its apply_overrides call so GitHub logs show the exact provider where a
second-pass reconstruction stalls.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reapply_published_overrides as target  # noqa: E402

_real_apply = target.apply_overrides


def traced_apply(provider_id, data, **kwargs):
    started = time.monotonic()
    print(
        f"FIELD_CORE_REAPPLY_TRACE provider={provider_id} phase={kwargs.get('phase', 'discovery')} stage=begin bytes={len(data)}",
        flush=True,
    )
    result = _real_apply(provider_id, data, **kwargs)
    elapsed = time.monotonic() - started
    print(
        f"FIELD_CORE_REAPPLY_TRACE provider={provider_id} stage=end elapsed={elapsed:.3f}s output_bytes={len(result[0])} records={len(result[1])}",
        flush=True,
    )
    return result


target.apply_overrides = traced_apply
sys.argv = [sys.argv[0], "--check"]
raise SystemExit(target.main())
