#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/prune_unreferenced_providers.py"
spec = importlib.util.spec_from_file_location("prune", TARGET)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

calls=[]
original=mod.subprocess.run
try:
    def fake_run(args, **kwargs):
        calls.append(list(args))
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "__NIAKVIO_COMMIT_TS__300\nproviders/a--src--aaaaaaaaaaaaaaaa.js\n"
                "__NIAKVIO_COMMIT_TS__100\nproviders/a--src--bbbbbbbbbbbbbbbb.js\n"
                "__NIAKVIO_COMMIT_TS__200\nproviders/b--src--cccccccccccccccc.js\n"
            ),
            stderr="",
        )
    mod.subprocess.run=fake_run
    existing={
        "a":["providers/a--src--aaaaaaaaaaaaaaaa.js","providers/a--src--bbbbbbbbbbbbbbbb.js"],
        "b":["providers/b--src--cccccccccccccccc.js"],
    }
    order={}
    mod.bootstrap_missing_order(ROOT,existing,order)
finally:
    mod.subprocess.run=original

assert len(calls)==1, calls
assert "--name-only" in calls[0], calls
assert "--follow" not in calls[0], calls
assert order["a"]==[
    "providers/a--src--bbbbbbbbbbbbbbbb.js",
    "providers/a--src--aaaaaaaaaaaaaaaa.js",
], order
assert order["b"]==["providers/b--src--cccccccccccccccc.js"], order
source=TARGET.read_text(encoding="utf-8")
assert "NIAKVIO_PROVIDER_PRUNE_BATCH_HISTORY_V1" in source
assert '"--follow"' not in source
print("provider prune batch history test passed")
