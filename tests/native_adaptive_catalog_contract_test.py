#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for relative in (
    "scripts/run_native_corpus_desktop_suite.sh",
    "scripts/run_native_corpus_mobile_suite.sh",
    "scripts/run_native_corpus_tv_suite.sh",
):
    text = (ROOT / relative).read_text(encoding="utf-8")
    assert "run_native_adaptive_catalog_fallbacks.sh" in text, relative
    assert "NIAKVIO_ADAPTIVE" not in text or "run_native_adaptive_catalog_fallbacks.sh" in text

orchestrator = (ROOT / "scripts/run_native_adaptive_catalog_fallbacks.sh").read_text(encoding="utf-8")
assert "clean_count" in orchestrator
assert "providers_file" in orchestrator
assert "fixed_batch=false" in orchestrator
assert "native_catalog_miss_rotation.py" in orchestrator
assert "for seed_fixture" in orchestrator
assert "count-per-lane 6" not in orchestrator

planner = (ROOT / "scripts/native_catalog_miss_rotation.py").read_text(encoding="utf-8")
assert 'state["zero"] and not state["positive"] and not state["error"] and not state["skip"]' in planner
assert 'route_mode == "capability_probe"' in planner

restage = (ROOT / "scripts/restage_native_corpus_client.py").read_text(encoding="utf-8")
assert "--provider-file" in restage
assert "provider allowlist" in restage

ios_prepare = (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")
assert "FIELD_NATIVE_IOS_CATALOG_MISS" in ios_prepare
assert "terminalProviders" in ios_prepare
assert "rotated_candidates" in ios_prepare
assert "fixed_batch=false" in ios_prepare

ios_runner = (ROOT / "scripts/run_native_corpus_ios_suite.sh").read_text(encoding="utf-8")
assert "native-hub46/manifest.json" in ios_runner
assert "manifest=manifest-hub46.json" not in ios_runner
assert "/manifest-hub46.json" not in ios_runner

print("NATIVE_ADAPTIVE_CATALOG_CONTRACT_OK lanes=3 initial=1_each clean_zero_only=true fixed_batch=false ios_transport=nested_hub46")
