#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/provider_patches/global_media_type_resolution_v1.py"
spec=importlib.util.spec_from_file_location("global_media_type_timeout_tested",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

source='module.exports={getStreams:async function(){return []}};\n'
default=mod.apply(source,options={"semantic_types":["movie","tv"]})
assert '"providerTimeoutMs":25000' in default, default[-3000:]
assert '"tvProviderTimeoutMs":25000' in default, default[-3000:]
assert '"fetchSliceMs":12000' in default, default[-3000:]
assert 'c.fetchSliceMs||12000' in default
assert 'Math.min(n,15000)' in default

bounded=mod.apply(source,options={"fetch_slice_ms":99999})
assert '"fetchSliceMs":15000' in bounded
short=mod.apply(source,options={"fetch_slice_ms":4000})
assert '"fetchSliceMs":4000' in short

migration=(ROOT/"scripts/upgrade_provider_execution_failfast_v33.py").read_text(encoding="utf-8")
assert 'cfg.get("fetch_slice_ms", 12_000)' in migration
assert 'c.fetchSliceMs||12000' in migration
assert 'fetch_slice_ms=12000' in migration

print("provider fetch-slice budget contract passed")
