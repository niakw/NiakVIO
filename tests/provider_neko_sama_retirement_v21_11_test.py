#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/retire_provider_neko_sama_v21_11.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("retire_provider_neko_sama_v21_11", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.PROVIDER_ID == "neko-sama"
assert module.RETIREMENT_ALLOWED is False
assert module.REVISION == "v21.11-proof-first-retirement-guard"

provider_files = sorted((ROOT / "providers").glob("neko-sama-*.js"))
assert provider_files, "Neko-Sama still has published provider material and must not be silently retired"
tracked = [
    ROOT / "manifest.json",
    ROOT / "provider-overrides.json",
    ROOT / "nuvio-client-id-state.json",
    *provider_files,
]
tracked = [path for path in tracked if path.exists()]
before = {path: digest(path) for path in tracked}

assert module.main() == 0

after = {path: digest(path) for path in tracked}
assert after == before, "V21.11 retirement guard must be non-destructive without terminal proof"

print("provider Neko-Sama V21.11 retirement guard passed: current provider material preserved")
