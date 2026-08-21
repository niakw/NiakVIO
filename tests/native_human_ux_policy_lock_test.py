#!/usr/bin/env python3
"""Lock the native reader harness to faithful human-UX observation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "automation/native-human-ux-policy.json").read_text(encoding="utf-8"))

assert POLICY["version"] >= 3
assert POLICY["mode"] == "human-ux-observation-only"

harness = POLICY["harness_change_control"]
assert harness["default"] == "locked-do-not-modify"
assert harness["change_policy"] == "only-when-faithful-observation-is-blocked"
for requirement in (
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
):
    assert forbidden_reason in harness["forbidden_reasons"], forbidden_reason

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

assert POLICY["change_control"]["default_on_ambiguity"] == "fail-closed"
print("native human UX harness lock policy tests passed")
