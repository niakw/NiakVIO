#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
prep = (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")
runner = (ROOT / "scripts/run_native_corpus_ios_suite.sh").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")

for marker in (
    "FIELD_NATIVE_IOS_PROVIDER_BEGIN",
    "FIELD_NATIVE_IOS_PROVIDER_END",
    "NIAKVIO_IOS_RESUME_FIXTURE",
    "NIAKVIO_IOS_RESUME_AFTER_PROVIDER",
    "state=watchdog_timeout",
):
    assert marker in prep, marker

for marker in (
    "FIELD_NATIVE_IOS_WATCHDOG action=restart",
    "MAX_WATCHDOG_RESTARTS",
    "watchdog_restart_budget_exhausted",
    "simctl terminate",
    "RESUME_FIXTURE",
    "RESUME_AFTER_PROVIDER",
):
    assert marker in runner, marker

assert 'if [[ "$MODE" != "full" ]]' in runner
assert "status=completed" in runner
assert ".github/triggers/native-ios-lab-validation.json" in workflow

print("native iOS watchdog/resume contract passed")
