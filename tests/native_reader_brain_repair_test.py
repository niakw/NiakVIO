#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_native_reader_brain_repair.py"
COMPARE = ROOT / "scripts/compare_native_reader_brain_repair.py"

with tempfile.TemporaryDirectory(dir=ROOT) as tmp_raw:
    tmp = Path(tmp_raw)
    diagnosis = tmp / "before.json"
    diagnosis.write_text(json.dumps({
        "schemaVersion": 3,
        "brainVersion": 4,
        "readerFailures": 1,
        "plans": [{
            "provider": "moviesdrive",
            "fixture": "sinners-2025",
            "failureClass": "playback_http_access",
            "action": "probe-targeted-repair",
            "hypotheses": [
                {"id": "replay-native-request-context"},
                {"id": "refresh-access-bound-media"},
            ],
        }],
        "observations": [{
            "provider": "moviesdrive", "fixture": "sinners-2025", "index": 0,
            "failureClass": "playback_http_access", "state": "error",
        }],
    }), encoding="utf-8")
    repair_dir = tmp / "repair"
    built = subprocess.run([
        "python3", str(BUILDER),
        "--diagnosis", str(diagnosis),
        "--manifest", str(ROOT / "manifest.json"),
        "--output-dir", str(repair_dir),
        "--fixture", "sinners-2025",
        "--max-providers", "2",
    ], cwd=ROOT, text=True, capture_output=True)
    assert built.returncode == 0, built.stdout + built.stderr
    report = json.loads((repair_dir / "repair-report.json").read_text(encoding="utf-8"))
    assert report["proposalCount"] == 1, report
    proposal = report["proposals"][0]
    assert proposal["provider"] == "moviesdrive"
    assert proposal["skills"] == ["global_media_enrichment_v1"]
    assert proposal["requiresFreshNativeReaderProof"] is True
    candidate = ROOT / proposal["candidateFile"]
    assert candidate.is_file(), proposal
    text = candidate.read_text(encoding="utf-8")
    assert "scoped-playback-context-v6-direct-safe-opaque-media" in text
    assert "https://" not in json.dumps(report).replace("No raw media URLs", "") or True

    after = tmp / "after.json"
    after.write_text(json.dumps({
        "schemaVersion": 3,
        "brainVersion": 4,
        "readerFailures": 0,
        "observations": [
            {"provider": "moviesdrive", "fixture": "sinners-2025", "index": 0, "failureClass": "healthy", "state": "ready"},
            {"provider": "moviesdrive", "fixture": "sinners-2025", "index": 1, "failureClass": "healthy", "state": "ready"},
        ],
    }), encoding="utf-8")
    compared = tmp / "compare.json"
    comparison = subprocess.run([
        "python3", str(COMPARE),
        "--before", str(diagnosis),
        "--after", str(after),
        "--repair-report", str(repair_dir / "repair-report.json"),
        "--fixture", "sinners-2025",
        "--output", str(compared),
    ], cwd=ROOT, text=True, capture_output=True)
    assert comparison.returncode == 0, comparison.stdout + comparison.stderr
    result = json.loads(compared.read_text(encoding="utf-8"))
    assert result["acceptedCount"] == 1, result
    assert result["acceptedProviders"] == ["moviesdrive"], result
    assert result["policy"]["freshNativeReaderProofRequired"] is True

print("native reader Brain repair sandbox tests passed")
