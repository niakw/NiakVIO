#!/usr/bin/env python3
"""Core-wide final security transform for every reconstructed provider bundle.

The underlying transformations live in ``provider_security_hardening.py`` so the
same deterministic implementation is shared by staging, Brain repair candidates,
publication reconstruction and security audits. This adapter exists only to make
that implementation composable through the normal provider Core hook scheduler.

The first statement emitted by this hook is also the durable Core-tail boundary.
It is a side-effect-free JavaScript string expression rather than a comment because
Terser may reattach comments while printing a minified bundle. Statement order is
preserved by the conservative purification profile, so repeated reconstruction can
always recover the exact provider-derived prefix without cutting through its code.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from provider_security_hardening import assert_hardened, harden_text  # noqa: E402

HOOK_MARKER = "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1"
HOOK_SENTINEL = f'"{HOOK_MARKER}"'
TRUSTED_CORE_TAIL_MARKERS = (
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
)


def _split_trusted_core_tail(text: str) -> tuple[str, str]:
    """Separate an already-generated trusted Core tail from provider-derived code."""
    starts = [
        index
        for marker in TRUSTED_CORE_TAIL_MARKERS
        if (index := text.find(f"/* {marker}:")) >= 0
    ]
    if not starts:
        return text, ""
    start = min(starts)
    return text[:start], text[start:]


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    provider_text, trusted_tail = _split_trusted_core_tail(text)
    hardened, _report = harden_text(provider_text)
    assert_hardened(hardened)
    if HOOK_SENTINEL not in hardened:
        # This side-effect-free statement is deliberately positional. Unlike a
        # comment, Terser cannot reattach it ahead of provider source code.
        hardened = hardened.rstrip() + f"\n{HOOK_SENTINEL};\n"
    return hardened + trusted_tail
