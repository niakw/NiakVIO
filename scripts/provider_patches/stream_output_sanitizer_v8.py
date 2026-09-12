#!/usr/bin/env python3
"""V8 terminal policy: unknown probe outcomes are not publishable media proof.

V7 already preserves only exact correlated non-direct player fallbacks and Core
media proof. For every ordinary probed URL, publication is now strict: only a
positive media verdict survives. Network errors, timeouts, opaque/unknown probe
results and hard invalid media all fail closed instead of leaking dead rows to
the client.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V7_PATH = ROOT / "stream_output_sanitizer_v7.py"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
MARKER = "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8"
OLD = "return verdict===false?null:clearPrivateProofs(item.stream);"
NEW = "return verdict===true?clearPrivateProofs(item.stream):null;"
ANCHOR = "  function clearPrivateProofs(stream){\n"


def _load_v7_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v7_for_v8", V7_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V7_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V7_APPLY = _load_v7_apply()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    if MARKER in text:
        validate(text)
        return text
    patched = V7_APPLY(text, options=options, **kwargs)
    if patched.count(OLD) != 1:
        raise ValueError(f"stream sanitizer v8 verdict hook count={patched.count(OLD)}")
    patched = patched.replace(OLD, NEW, 1)
    if patched.count(ANCHOR) != 1:
        raise ValueError(f"stream sanitizer v8 marker anchor count={patched.count(ANCHOR)}")
    patched = patched.replace(ANCHOR, f"  /* {MARKER} */\n" + ANCHOR, 1)
    validate(patched)
    return patched


def validate(text: str) -> None:
    if text.count(MARKER) != 1:
        raise ValueError(f"stream sanitizer v8 marker count={text.count(MARKER)}")
    if text.count(NEW) != 1:
        raise ValueError(f"stream sanitizer v8 strict verdict count={text.count(NEW)}")
    if OLD in text:
        raise ValueError("stream sanitizer v8 retained fail-open unknown verdict")
    if "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7" not in text:
        raise ValueError("stream sanitizer v8 lost V7 correlated player policy")
    section = text.split(f"/* {MARKER} */", 1)[1].split("function clearPrivateProofs", 1)[0].casefold()
    for forbidden in ("hindmoviez", "anime-sama", "animesama", "mugiwara", "moviebox"):
        if forbidden in section:
            raise ValueError(f"provider-specific token leaked into V8 policy: {forbidden}")


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
