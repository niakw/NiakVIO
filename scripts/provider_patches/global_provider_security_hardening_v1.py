#!/usr/bin/env python3
"""Core-wide final security transform for every reconstructed provider bundle.

The underlying transformations live in ``provider_security_hardening.py`` so the
same deterministic implementation is shared by staging, Brain repair candidates,
publication reconstruction and security audits. This adapter exists only to make
that implementation composable through the normal provider Core hook scheduler.
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


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    hardened, _report = harden_text(text)
    assert_hardened(hardened)
    if HOOK_MARKER in hardened:
        return hardened
    # The hook marker is evidence that the full Core reconstruction traversed the
    # security layer even when a source already had no known unsafe shape.
    return hardened.rstrip() + f"\n/* {HOOK_MARKER} */\n"
