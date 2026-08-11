#!/usr/bin/env python3
"""Harden V5 all-URL probing so unproven overflow rows are fail-closed.

V5 treats ``maxProbes`` as a probing budget, but rows beyond that budget are
returned unchanged even when ``probe_all_urls`` is true. That is acceptable for
best-effort probing, but not for a NuvioTV-only provider whose desktop/mobile
platforms are deliberately blocked: every published row must either have media
proof or be discarded.

V6 preserves V5 for all parsing/probing behavior and changes only that overflow
semantic. It is intentionally opt-in via a separate patch script so providers
that rely on best-effort V5 behavior are not changed implicitly.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V5_PATH = ROOT / "stream_output_sanitizer_v5.py"
MARKER = "/* NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6 */"
OLD = "if(!item.probe)return item.stream;"
NEW = "if(!item.probe)return config.probeAllUrls?null:item.stream;"


def _load_v5_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v5_for_v6", V5_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V5_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V5_APPLY = _load_v5_apply()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    cfg = dict(options or {})
    if not bool(cfg.get("probe_all_urls")):
        raise ValueError("stream sanitizer v6 requires probe_all_urls=true")
    if int(cfg.get("max_probes") or 0) <= 0:
        raise ValueError("stream sanitizer v6 requires max_probes>0")

    # V5 owns the content-addressed configuration. Always let it run first so
    # changing blocked paths or probe policy cannot be hidden by a static V6
    # marker from an older materialization.
    patched = V5_APPLY(text, options=cfg, **kwargs)
    if patched == text and MARKER in text:
        return text

    patched = patched.replace(MARKER, "").rstrip()
    if NEW not in patched:
        if OLD not in patched:
            raise ValueError("stream sanitizer all-URL overflow hook not found")
        patched = patched.replace(OLD, NEW, 1)
    return patched.rstrip() + "\n" + MARKER + "\n"


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
