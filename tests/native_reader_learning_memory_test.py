#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGE = ROOT / "scripts/merge_native_reader_repair_learning.py"
BUILD = ROOT / "scripts/build_native_reader_brain_repair.py"

with tempfile.TemporaryDirectory(dir=ROOT) as tmp_raw:
    tmp = Path(tmp_raw)
    base = tmp / "base.json"
    base.write_text(json.dumps({
        "publicationAllowed": False,
        "productionWritesAllowed": False,
        "proposals": [],
        "nativeReaderRepairMemory": {
            "importedRunIds": ["111", "222", "111", "invalid", "https://unsafe.example/333"],
            "entries": [],
        },
    }), encoding="utf-8")
    comparison = tmp / "comparison.json"
    rejected = {
        "fixture": "sinners-2025",
        "acceptedCount": 0,
        "rejectedCount": 1,
        "inconclusiveCount": 0,
        "accepted": [],
        "inconclusive": [],
        "rejected": [{
            "provider": "moviesdrive",
            "fixture": "sinners-2025",
            "failureClasses": ["playback_http_access"],
            "hypotheses": ["replay-native-request-context"],
            "skills": ["global_media_enrichment_v1"],
            "reason": "reader_failure_persisted_or_changed",
        }],
    }
    comparison.write_text(json.dumps(rejected), encoding="utf-8")

    first = tmp / "first.json"
    second = tmp / "second.json"
    for previous, output in ((base, first), (first, second)):
        run = subprocess.run([
            "python3", str(MERGE),
            "--state", str(previous),
            "--previous-state", str(previous),
            "--comparison", str(comparison),
            "--output", str(output),
        ], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stdout + run.stderr
        merged = json.loads(output.read_text(encoding="utf-8"))
        assert merged["nativeReaderRepairMemory"]["importedRunIds"] == ["111", "222"], merged["nativeReaderRepairMemory"]

    learned = json.loads(second.read_text(encoding="utf-8"))
    entries = learned["nativeReaderRepairMemory"]["entries"]
    assert len(entries) == 1, entries
    entry = entries[0]
    assert entry["failures"] == 2 and entry["consecutiveFailures"] == 2, entry
    assert any(row.get("type") == "avoid_native_reader_skill" for row in learned["proposals"]), learned["proposals"]
    assert "http://" not in second.read_text(encoding="utf-8").lower()
    assert "https://" not in second.read_text(encoding="utf-8").lower()

    # The repair Brain now requires cross-client confirmation before a global
    # provider mutation is even eligible. Exercise negative memory *after* that
    # guard by presenting the same declared-route failure from TV and Mobile.
    diagnosis = tmp / "diagnosis.json"
    diagnosis.write_text(json.dumps({
        "brainVersion": 4,
        "readerFailures": 2,
        "plans": [
            {
                "provider": "moviesdrive",
                "fixture": "sinners-2025",
                "requestType": "movie",
                "client": "tv",
                "failureClass": "playback_http_access",
                "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
            {
                "provider": "moviesdrive",
                "fixture": "sinners-2025",
                "requestType": "movie",
                "client": "mobile",
                "failureClass": "playback_http_access",
                "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
        ],
    }), encoding="utf-8")
    repair_dir = tmp / "repair-suppressed"
    build = subprocess.run([
        "python3", str(BUILD),
        "--diagnosis", str(diagnosis),
        "--manifest", str(ROOT / "manifest.json"),
        "--learning-state", str(second),
        "--output-dir", str(repair_dir),
        "--fixture", "sinners-2025",
    ], cwd=ROOT, text=True, capture_output=True)
    assert build.returncode == 0, build.stdout + build.stderr
    report = json.loads((repair_dir / "repair-report.json").read_text(encoding="utf-8"))
    assert report["learningApplied"] is True
    assert report["proposalCount"] == 0, report
    # If this were still blocked by client compatibility, compatibilityOnlyCount
    # would be non-zero. Zero proves the target passed cross-client eligibility;
    # the explicit skip reason then proves negative memory suppressed the skill.
    assert report["compatibilityOnlyCount"] == 0, report
    assert report["skipped"][0]["reason"] == "all_compatible_reader_skills_suppressed_by_negative_memory", report

    accepted = dict(rejected)
    accepted.update({"acceptedCount": 1, "rejectedCount": 0, "accepted": rejected["rejected"], "rejected": []})
    accepted["accepted"][0] = dict(accepted["accepted"][0], reason="fresh_native_reader_proof_green")
    comparison.write_text(json.dumps(accepted), encoding="utf-8")
    recovered = tmp / "recovered.json"
    run = subprocess.run([
        "python3", str(MERGE),
        "--state", str(second),
        "--previous-state", str(second),
        "--comparison", str(comparison),
        "--output", str(recovered),
    ], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    recovered_state = json.loads(recovered.read_text(encoding="utf-8"))
    recovered_entry = recovered_state["nativeReaderRepairMemory"]["entries"][0]
    assert recovered_entry["successes"] == 1 and recovered_entry["consecutiveFailures"] == 0, recovered_entry
    assert recovered_state["nativeReaderRepairMemory"]["importedRunIds"] == ["111", "222"]

print("native reader learning memory and imported-run history tests passed")
