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

spec = importlib.util.spec_from_file_location("adaptive_runtime_html_class_token_test", MODULE_PATH)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

source = r'''
function classText(html,cls){var re=new RegExp("<div\\b[^>]*class=[\\\"'][^\\\"']*\\b"+cls+"\\b[^\\\"']*[\\\"']","i");return re.test(html)}
function classBlocks(html,cls){var esc=cls;var re=new RegExp("<li\\b[^>]*class=[\\\"'][^\\\"']*\\b"+esc+"\\b[^\\\"']*[\\\"']","gi");return re.test(html)}
'''
result = {"status": "no_streams", "tests": [{"status": "no_streams", "stream_count": 0}]}
candidate = {
    "key": "fixture:html-class-token",
    "canonical_id": "fixture-provider",
    "source": "fixture",
    "local_path": "providers/fixture-provider.js",
    "bytes": len(source.encode("utf-8")),
    "local_patches": [],
}
profiles = runtime.matching_profiles(candidate, result, source, config={})
assert runtime.HTML_CLASS_TOKEN_PROFILE in profiles, profiles

with tempfile.TemporaryDirectory(prefix="niakvio-html-class-token-") as tmp:
    stage = Path(tmp)
    provider = stage / candidate["local_path"]
    provider.parent.mkdir(parents=True, exist_ok=True)
    provider.write_text(source, encoding="utf-8")
    repaired, error = runtime.create_repair_candidate(stage, candidate, runtime.HTML_CLASS_TOKEN_PROFILE, 1)
    assert error is None, error
    assert repaired is not None
    repaired_source = (stage / repaired["local_path"]).read_text(encoding="utf-8")
    assert "NUVIO_HTML_CLASS_TOKEN_EXACT_V1" in repaired_source
    assert "(?![-_A-Za-z0-9])" in repaired_source
    assert r'+"\\b' not in repaired_source
    records = repaired.get("local_patches") or []
    assert any(
        row.get("profile") == runtime.HTML_CLASS_TOKEN_PROFILE
        and row.get("scope") == "generic_html_class_token_contract"
        for row in records if isinstance(row, dict)
    )

print(json.dumps({"html_class_token_exact_profile": "ok"}, sort_keys=True))
