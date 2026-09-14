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
    "FIELD_NATIVE_IOS_WATCHDOG action=drained",
    "FIELD_NATIVE_IOS_WATCHDOG action=late_terminal",
    "FIELD_NATIVE_IOS_WATCHDOG action=confirmed_timeout",
    "MAX_WATCHDOG_RESTARTS",
    "WATCHDOG_DRAIN_SECONDS",
    "watchdog_restart_budget_exhausted",
    "drain_lab_output",
    "provider_end_after_line",
    "BLOCKED_BEGIN_LINE",
    "begin_line=$BLOCKED_BEGIN_LINE",
    "simctl terminate",
    "RESUME_FIXTURE",
    "RESUME_AFTER_PROVIDER",
):
    assert marker in runner, marker

# A watchdog restart must terminate and drain the old console generation before
# any new launch. Otherwise a late PROVIDER_END from generation N can be consumed
# as the terminal of generation N+1.
restart_block = runner.split('echo "FIELD_NATIVE_IOS_WATCHDOG action=restart', 1)[1]
stop_index = restart_block.index("    stop_lab")
drain_index = restart_block.index("    drain_lab_output")
launch_index = restart_block.index("    launch_lab")
assert stop_index < drain_index < launch_index

# The old implementation treated any historical PROVIDER_END as authoritative
# and could fail with idle_after_provider_end. Generation correlation now uses
# the exact provider BEGIN line and must never reintroduce that verdict.
assert "idle_after_provider_end" not in runner
assert 'tail -n "+$((begin_line + 1))" "$LOG"' in runner
assert 'RESUME_AFTER_PROVIDER=""' in runner
assert 'RESUME_AFTER_PROVIDER="$BLOCKED_PROVIDER"' in runner

assert 'if [[ "$MODE" != "full" ]]' in runner
assert "status=completed" in runner
assert ".github/triggers/native-ios-lab-validation.json" in workflow

print("native iOS watchdog/resume generation-safety contract passed")
