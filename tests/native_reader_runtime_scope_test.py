#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "scripts/scope_native_reader_learning_runtime.py"

FP_OLD = "tv=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;mobile=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
FP_NEW = "tv=cccccccccccccccccccccccccccccccccccccccc;mobile=dddddddddddddddddddddddddddddddddddddddd"

with tempfile.TemporaryDirectory(dir=ROOT) as tmp_raw:
    tmp = Path(tmp_raw)
    state = tmp / "state.json"
    state.write_text(json.dumps({
        "publicationAllowed": False,
        "productionWritesAllowed": False,
        "proposals": [],
        "nativeReaderRepairMemory": {
            "schemaVersion": 2,
            "entries": [
                {
                    "providerId": "moviesdrive", "fixture": "sinners-2025",
                    "failureClass": "playback_http_access", "skill": "global_media_enrichment_v1",
                    "failures": 2, "successes": 0, "attempts": 2, "consecutiveFailures": 2,
                    "runtimeFingerprint": FP_OLD,
                },
                {
                    "providerId": "cineby", "fixture": "sinners-2025",
                    "failureClass": "decoder_error", "skill": "global_media_enrichment_v1",
                    "failures": 1, "successes": 0, "attempts": 1, "consecutiveFailures": 1,
                },
            ],
        },
    }), encoding="utf-8")

    scoped = tmp / "scoped.json"
    run = subprocess.run([
        "python3", str(SCOPE), "filter",
        "--state", str(state),
        "--runtime-fingerprint", FP_NEW,
        "--output", str(scoped),
    ], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    filtered = json.loads(scoped.read_text(encoding="utf-8"))
    memory = filtered["nativeReaderRepairMemory"]
    assert memory["entries"] == [], memory
    assert memory["runtimeScope"]["excludedEntryCount"] == 2
    assert memory["runtimeScope"]["legacyUnscopedExcluded"] == 1

    comparison = tmp / "comparison.json"
    comparison.write_text(json.dumps({
        "runtimeFingerprint": FP_NEW,
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
            "skills": ["global_media_enrichment_v1"],
            "reason": "reader_failure_persisted_or_changed",
        }],
    }), encoding="utf-8")
    merged = tmp / "merged.json"
    run = subprocess.run([
        "python3", str(SCOPE), "merge",
        "--state", str(state),
        "--comparison", str(comparison),
        "--runtime-fingerprint", FP_NEW,
        "--output", str(merged),
    ], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    learned = json.loads(merged.read_text(encoding="utf-8"))
    entries = learned["nativeReaderRepairMemory"]["entries"]
    new_rows = [row for row in entries if row.get("runtimeFingerprint") == FP_NEW]
    old_rows = [row for row in entries if row.get("runtimeFingerprint") == FP_OLD]
    legacy_rows = [row for row in entries if not row.get("runtimeFingerprint")]
    assert len(new_rows) == 1, entries
    assert new_rows[0]["failures"] == 1, new_rows[0]
    assert len(old_rows) == 1 and old_rows[0]["failures"] == 2, entries
    assert len(legacy_rows) == 1, entries
    assert learned["nativeReaderRepairMemory"]["runtimeScope"]["reusePolicy"] == "exact-runtime-fingerprint-only"

print("native reader runtime-scoped Brain memory tests passed")
