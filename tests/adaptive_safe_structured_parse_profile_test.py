#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/adaptive_runtime/runtime_repair.py"
sys.path.insert(0, str(ROOT / "scripts/adaptive_runtime"))
sys.path.insert(1, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("adaptive_runtime_repair_safe_parse_test", MODULE_PATH)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

source = r'''
module.exports = {
  async getStreams() {
    const rawFile = '[{"title":"A\\u00e9","file":"https:\\/\\/cdn.example\\/master.m3u8"}]';
    try {
      const unescaped = rawFile.replace(/\\(.)/g, "$1");
      return JSON.parse(unescaped);
    } catch (_error) {
      return JSON.parse(rawFile);
    }
  }
};
'''
result = {
    "status": "runtime_error",
    "tests": [{
        "status": "runtime_error",
        "error_details": {"message": "SyntaxError: invalid JSON escape while JSON.parse"},
    }],
}
candidate = {
    "key": "fixture:structured-parse",
    "canonical_id": "fixture-provider",
    "source": "fixture",
    "local_path": "providers/fixture-provider.js",
    "bytes": len(source.encode("utf-8")),
    "local_patches": [],
}

profiles = runtime.matching_profiles(candidate, result, source, config={})
assert runtime.SAFE_STRUCTURED_PARSE_PROFILE in profiles, profiles

with tempfile.TemporaryDirectory(prefix="niakvio-safe-parse-") as tmp:
    stage = Path(tmp)
    provider = stage / candidate["local_path"]
    provider.parent.mkdir(parents=True, exist_ok=True)
    provider.write_text(source, encoding="utf-8")
    repaired, error = runtime.create_repair_candidate(
        stage,
        candidate,
        runtime.SAFE_STRUCTURED_PARSE_PROFILE,
        1,
    )
    assert error is None, error
    assert repaired is not None
    repaired_path = stage / repaired["local_path"]
    repaired_source = repaired_path.read_text(encoding="utf-8")
    assert "NUVIO_SAFE_STRUCTURED_PARSE_V1" in repaired_source
    assert r'replace(/\\(.)/g, "$1")' not in repaired_source
    assert repaired["runtime_repair"]["profile"] == runtime.SAFE_STRUCTURED_PARSE_PROFILE
    assert repaired["runtime_repair"]["strategy"] == runtime.SAFE_STRUCTURED_PARSE_PROFILE
    records = repaired.get("local_patches") or []
    assert any(
        row.get("profile") == runtime.SAFE_STRUCTURED_PARSE_PROFILE
        and row.get("scope") == "global_structured_parse"
        for row in records
        if isinstance(row, dict)
    )

print(json.dumps({"safe_structured_parse_profile": "ok"}, sort_keys=True))
