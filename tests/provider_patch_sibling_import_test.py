#!/usr/bin/env python3
"""Provider patch loader must support sibling helper imports for Lego families."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import _load_patch_module  # noqa: E402


CASES = {
    "persianstremio": (
        "scripts/provider_patches/persianstremio_runtime_v1.py",
        "PROVIDER.PERSIANSTREMIO.RUNTIME.V1",
    ),
    "fullanime": (
        "scripts/provider_patches/fullanime_runtime_v1.py",
        "PROVIDER.FULLANIME.RUNTIME.V1",
    ),
}

for provider_id, (script, expected_fix) in CASES.items():
    module = _load_patch_module(script, provider_id)
    assert getattr(module, "MANAGED_FIX_ID", "") == expected_fix
    assert callable(getattr(module, "apply", None))

print(f"provider patch sibling import contract passed cases={len(CASES)}")
