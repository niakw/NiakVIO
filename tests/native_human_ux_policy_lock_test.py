#!/usr/bin/env python3
"""Lock native reader harness behavior and its persistent profile/blocker memory."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "automation/native-human-ux-policy.json").read_text(encoding="utf-8"))

assert POLICY["version"] >= 4
assert POLICY["mode"] == "human-ux-observation-only"

harness = POLICY["harness_change_control"]
assert harness["default"] == "locked-do-not-modify"
assert harness["change_policy"] == "only-when-faithful-observation-is-blocked"
for requirement in (
    "consult persistent_profiles and job_blocker_memory",
    "identify the exact harness blocker",
    "show that the blocker prevents observation rather than merely producing a bad playback result",
    "show that the proposed change cannot make Nuvio, the player, networking or the OS more permissive",
):
    assert requirement in harness["required_before_change"], requirement
for forbidden_reason in (
    "make CI green",
    "increase playback success rate",
    "work around a Nuvio player failure",
    "work around an OS or emulator playback/network limitation",
    "re-diagnose a resolved blocker without a changed signature or invalidated profile",
):
    assert forbidden_reason in harness["forbidden_reasons"], forbidden_reason

profiles = POLICY["persistent_profiles"]
assert profiles["schema_version"] == 1
assert profiles["reuse_rule"] == "reuse-before-rediagnosis"
for profile_id in ("common", "tv", "mobile", "desktop"):
    assert profiles[profile_id]["status"] == "validated-and-reusable", profile_id
common = profiles["common"]
assert common["production_player_first"] is True
assert common["transport_probe_after_player_only"] is True
assert common["preserve_warm_profile_plugin_cache_state"] is True
assert common["nuvio_runtime_source_read_only"] is True
assert common["os_network_security_policy_read_only"] is True
assert common["component_probes_are_diagnostic_only"] is True
assert common["human_ux_acceptance_requires_real_ui_path"] is True
assert "a stale regression-test assertion" in common["not_invalidated_by"]
assert "stream playback failure" in common["not_invalidated_by"]
assert profiles["tv"]["known_entry"] == "native_client_test_bootstrap.enable_tv_tests"
assert profiles["mobile"]["known_entry"] == "native_client_test_bootstrap.enable_mobile_device_tests"
assert profiles["mobile"]["launcher_package"] == "com.nuviodebug.com"
assert profiles["desktop"]["execution_policy"] == "ordinary-user"

blockers = POLICY["job_blocker_memory"]
assert blockers["schema_version"] == 1
assert blockers["consult_before_harness_change"] is True
entries = {row["id"]: row for row in blockers["entries"]}
for blocker_id in (
    "stale-repository-http-instrumentation-contract",
    "stale-tv-bootstrap-wrapper-contract",
    "stale-tv-bootstrap-alias-contract",
    "reader-run-cancellation-churn",
    "repository-http-evidence-gap-after-instrumentation-disable",
    "actions-log-blob-not-ready",
):
    assert blocker_id in entries, blocker_id
for blocker_id in (
    "stale-repository-http-instrumentation-contract",
    "stale-tv-bootstrap-wrapper-contract",
    "stale-tv-bootstrap-alias-contract",
):
    assert entries[blocker_id]["status"] == "resolved", blocker_id
    assert entries[blocker_id]["never_repeat"], blocker_id
assert entries["repository-http-evidence-gap-after-instrumentation-disable"]["status"] == "watch"
assert "never restore Nuvio runtime HTTP instrumentation" in entries["repository-http-evidence-gap-after-instrumentation-disable"]["next_action"]
assert entries["reader-run-cancellation-churn"]["status"] == "operational-guard"
assert "freeze the head until evidence is collected" in entries["reader-run-cancellation-churn"]["resolution"]

human_path = POLICY["human_ux_acceptance_path"]
for step in (
    "launch the official Nuvio client",
    "reach the real Nuvio stream-selection surface",
    "select the returned stream through the real Nuvio UI",
    "let the real Nuvio player attempt playback before any media transport diagnostic",
    "record first-frame success or the visible/native player failure",
):
    assert step in human_path, step

classes = POLICY["evidence_classes"]
assert classes["human_ux_proof"]["can_gate_acceptance"] is True
assert classes["human_ux_proof"]["requires_real_ui_path"] is True
assert classes["human_ux_proof"]["requires_production_player"] is True
assert classes["human_ux_proof"]["may_patch_nuvio_runtime"] is False
assert classes["component_probe"]["can_gate_acceptance"] is False
assert classes["component_probe"]["role"] == "diagnostic-only"

for forbidden_behavior in (
    "count a direct player/provider component probe as human-UX acceptance",
    "retouch the harness merely because playback or player tests are failing",
):
    assert forbidden_behavior in POLICY["forbidden_behaviors"], forbidden_behavior

change_control = POLICY["change_control"]
assert change_control["persistent_profiles_are_source_of_truth"] is True
assert change_control["job_blocker_memory_is_source_of_truth"] is True
assert change_control["default_on_ambiguity"] == "fail-closed"
print("native human UX harness + persistent profile/blocker memory tests passed")
