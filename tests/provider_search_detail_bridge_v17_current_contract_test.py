#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATH = ROOT / "scripts" / "upgrade_provider_search_detail_bridge_v17.py"
spec = importlib.util.spec_from_file_location("upgrade_provider_search_detail_bridge_v17", PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

current = mod.BASE.read_text(encoding="utf-8")
mod.validate(current)
assert "NIAKVIO_PROVIDER_PLAN_STREAM_COVERAGE_V28" in current
assert "const boundedDetails = _uniq(details).slice(0, 8);" in current
assert "_crawlDirectMedia(boundedDetails, payload.base || url, 3)" in current

broken = current.replace(
    "const crawled = await _crawlDirectMedia(boundedDetails, payload.base || url, 3);",
    "const crawled = [];",
    1,
)
try:
    mod.validate(broken)
except AssertionError as exc:
    assert "V17 bounded detail fallback missing" in str(exc), exc
else:
    raise AssertionError("V17 accepted ProviderBase with bounded fallback crawl removed")

broken_resolver = current.replace(
    "const detailStreams = await _spv4ResolveDetail(",
    "const detailStreams = await _missingResolveDetail(",
    1,
)
try:
    mod.validate(broken_resolver)
except AssertionError as exc:
    assert "V17 missing" in str(exc), exc
else:
    raise AssertionError("V17 accepted ProviderBase with canonical detail resolver removed")

print("Provider search-detail bridge V17 current/evolved contract passed")
