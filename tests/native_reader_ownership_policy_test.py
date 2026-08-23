#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER = ROOT / "scripts" / "classify_native_reader_ownership.py"
MERGER = ROOT / "scripts" / "merge_native_reader_learning_failures.py"
SUMMARY = ROOT / "scripts" / "build_native_reader_learning_summary.py"

with tempfile.TemporaryDirectory() as raw:
    tmp = Path(raw)
    diagnostics = tmp / "diagnostics"
    diagnostics.mkdir()
    report = {
        "evidenceComplete": True,
        "evidenceProblems": [],
        "observations": [
            {
                "provider": "cineby",
                "client": "tv",
                "fixture": "sinners-2025",
                "routeMode": "declared",
                "failureClass": "playback_http_access",
                "failureDomain": "provider_stream",
                "providerMutationEligible": True,
                "failureStage": "http_access",
            },
            {
                "provider": "videasy",
                "client": "desktop",
                "fixture": "sinners-2025",
                "routeMode": "declared",
                "failureClass": "playback_runtime_setup",
                "failureDomain": "client_runtime",
                "providerMutationEligible": False,
                "failureStage": "player_setup",
            },
            {
                "provider": "ignored-capability",
                "client": "tv",
                "fixture": "sinners-2025",
                "routeMode": "capability_probe",
                "failureClass": "playback_http_access",
                "failureDomain": "provider_stream",
                "providerMutationEligible": True,
            },
        ],
        "providerLoadIssues": [],
    }
    (diagnostics / "sample-brain.json").write_text(json.dumps(report), encoding="utf-8")

    ownership = tmp / "ownership.json"
    subprocess.run(
        [sys.executable, str(CLASSIFIER), "--diagnostics-root", str(diagnostics), "--output", str(ownership), "--fail-on-lab-infra"],
        cwd=ROOT,
        check=True,
    )
    classified = json.loads(ownership.read_text(encoding="utf-8"))
    assert classified["labEmulationFailures"] == 0
    assert classified["providerLearningFailures"] == 1
    assert classified["nuvioVendorWaitFailures"] == 1
    assert classified["policy"]["nuvioVendorWaitBlocksProviderPublication"] is False
    assert classified["policy"]["providerLearningBlocksProviderPublication"] is False

    state = tmp / "state.json"
    state.write_text('{"publicationAllowed":false,"productionWritesAllowed":false}\n', encoding="utf-8")
    subprocess.run(
        [sys.executable, str(MERGER), "--state", str(state), "--diagnostics-root", str(diagnostics), "--run-id", "12345", "--output", str(state)],
        cwd=ROOT,
        check=True,
    )
    summary = tmp / "summary.json"
    subprocess.run([sys.executable, str(SUMMARY), "--state", str(state), "--output", str(summary)], cwd=ROOT, check=True)
    learned = json.loads(summary.read_text(encoding="utf-8"))
    assert learned["nativeReaderFailures"] == 1
    assert learned["totalNativeReaderFailures"] == 2
    assert learned["providerLearningFailures"] == 1
    assert learned["nuvioVendorWaitFailures"] == 1
    assert learned["providerReaderFailures"][0]["provider"] == "cineby"
    assert learned["providerReaderFailures"][0]["deepRetryRequested"] is True
    assert learned["nuvioVendorWait"][0]["provider"] == "videasy"
    assert learned["nuvioVendorWait"][0]["deepRetryRequested"] is False

    # Emulator/runner evidence is a Lab infrastructure defect: it must never be
    # converted into provider learning, and the strict final classifier rejects it.
    infra = {
        "evidenceComplete": False,
        "evidenceProblems": ["runner shutdown while emulator device offline"],
        "observations": [],
        "providerLoadIssues": [],
    }
    (diagnostics / "infra-brain.json").write_text(json.dumps(infra), encoding="utf-8")
    rejected = subprocess.run(
        [sys.executable, str(CLASSIFIER), "--diagnostics-root", str(diagnostics), "--output", str(ownership), "--fail-on-lab-infra"],
        cwd=ROOT,
        check=False,
    )
    assert rejected.returncode == 5
    classified = json.loads(ownership.read_text(encoding="utf-8"))
    assert classified["labEmulationFailures"] >= 1

print("native reader ownership policy contract passed")
