#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_base_store.py"

spec = importlib.util.spec_from_file_location("provider_base_store", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = b"module.exports={getStreams:async()=>[]};\n"
digest = module.sha256(data)
relative = module.base_relative("Stream Zo", digest)
assert relative.startswith("provider-bases/stream-zo--base--"), relative
assert relative.endswith(".js"), relative
assert module.safe_base_path(relative) == (ROOT / relative).resolve()
assert module.safe_base_path("../providers/escape.js") is None
assert module.safe_base_path("providers/not-a-base.js") is None

print("ProviderBase store unit tests passed")
