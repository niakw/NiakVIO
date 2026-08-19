#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGE = ROOT / "scripts/merge_native_reader_backlog.py"


def run_merge(state: Path, root: Path, run_id: str, output: Path, md_in: Path, md_out: Path) -> dict:
    run = subprocess.run([
        "python3", str(MERGE),
        "--state", str(state),
        "--diagnostics-root", str(root),
        "--run-id", run_id,
        "--output", str(output),
        "--markdown-input", str(md_in),
        "--markdown-output", str(md_out),
    ], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "FIELD_NATIVE_READER_BACKLOG" in run.stdout, run.stdout
    return json.loads(output.read_text(encoding="utf-8"))


with tempfile.TemporaryDirectory(dir=ROOT) as tmp_raw:
    tmp = Path(tmp_raw)
    state = tmp / "state.json"
    state.write_text(json.dumps({
        "publicationAllowed": False,
        "productionWritesAllowed": False,
        "proposals": [],
    }), encoding="utf-8")
    md = tmp / "latest.md"
    md.write_text("# NiakVIO Brain Learning\n", encoding="utf-8")
    evidence = tmp / "evidence"
    evidence.mkdir()
    diag = evidence / "tv-route-sinners-2025-brain.json"

    first_diag = {
        "generatedAt": "2026-08-19T17:00:00Z",
        "evidenceComplete": True,
        "readerObserved": 3,
        "readerFailures": 2,
        "providerLoadObservedFailures": 1,
        "observations": [
            {
                "provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "failureClass": "playback_http_access",
            },
            {
                "provider": "videasy", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "failureClass": "healthy",
            },
            {
                "provider": "anime-sama", "client": "tv", "fixture": "jujutsu-kaisen-s01e01",
                "requestType": "tv", "routeMode": "capability_probe", "failureClass": "playback_parser",
            },
        ],
        "providerLoadIssues": [
            {
                "provider": "goated", "client": "tv", "fixture": "sinners-2025",
                "failureClass": "provider_repository_load_error", "layer": "repository",
                "reason": "https://unsafe.example/signed?token=secret",
            }
        ],
        "providerOutcomes": [],
    }
    diag.write_text(json.dumps(first_diag), encoding="utf-8")

    first_out = tmp / "first.json"
    first_md = tmp / "first.md"
    first = run_merge(state, evidence, "100", first_out, md, first_md)
    backlog = first["nativeReaderBacklog"]
    assert backlog["openCount"] == 2, backlog
    assert backlog["resolvedCount"] == 0, backlog
    assert backlog["externalCandidateOpenCount"] == 1, backlog
    assert backlog["importedRunIds"] == ["100"], backlog
    assert len(backlog["importedEvidenceIds"]) == 1, backlog
    assert all(row["providerId"] != "anime-sama" for row in backlog["entries"]), backlog["entries"]

    movie = next(row for row in backlog["entries"] if row["providerId"] == "moviesdrive")
    assert movie["failureClass"] == "playback_http_access"
    assert movie["scope"] == "external_or_context"
    assert movie["externalCandidate"] is True
    assert movie["providerJsMutationAllowed"] is False

    load = next(row for row in backlog["entries"] if row["providerId"] == "goated")
    assert load["requestType"] == "repository"
    assert load["providerJsMutationAllowed"] is False
    assert "http" not in json.dumps(load).lower(), load

    # Exact same artifact is idempotent even with the same run id.
    duplicate_out = tmp / "duplicate.json"
    duplicate_md = tmp / "duplicate.md"
    duplicate = run_merge(first_out, evidence, "100", duplicate_out, first_md, duplicate_md)
    duplicate_backlog = duplicate["nativeReaderBacklog"]
    assert duplicate_backlog["skippedDuplicateThisRun"] == 1, duplicate_backlog
    assert next(row for row in duplicate_backlog["entries"] if row["providerId"] == "moviesdrive")["occurrences"] == 1

    # A rerun of the same GitHub run id with different complete evidence is new
    # evidence: old failures resolve and a changed causal failure opens separately.
    second_diag = {
        "generatedAt": "2026-08-19T17:30:00Z",
        "evidenceComplete": True,
        "readerObserved": 3,
        "readerFailures": 1,
        "providerLoadObservedFailures": 0,
        "observations": [
            {
                "provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "failureClass": "healthy",
            },
            {
                "provider": "goated", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "failureClass": "healthy",
            },
            {
                "provider": "videasy", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "failureClass": "playback_parser",
            },
        ],
        "providerLoadIssues": [],
        "providerOutcomes": [],
    }
    diag.write_text(json.dumps(second_diag), encoding="utf-8")
    second_out = tmp / "second.json"
    second_md = tmp / "second.md"
    second = run_merge(duplicate_out, evidence, "100", second_out, duplicate_md, second_md)
    second_backlog = second["nativeReaderBacklog"]
    assert second_backlog["importedRunIds"] == ["100"], second_backlog
    assert len(second_backlog["importedEvidenceIds"]) == 2, second_backlog
    assert second_backlog["openCount"] == 1, second_backlog
    assert second_backlog["resolvedCount"] == 2, second_backlog
    assert next(row for row in second_backlog["entries"] if row["providerId"] == "moviesdrive")["status"] == "resolved"
    assert next(row for row in second_backlog["entries"] if row["providerId"] == "goated")["status"] == "resolved"
    parser = next(row for row in second_backlog["entries"] if row["providerId"] == "videasy" and row["failureClass"] == "playback_parser")
    assert parser["status"] == "open" and parser["providerJsMutationAllowed"] is True, parser
    assert "Native reader bug backlog" in second_md.read_text(encoding="utf-8")

    # Incomplete evidence is fail-closed and does not consume the run id/evidence.
    diag.write_text(json.dumps({
        "generatedAt": "2026-08-19T18:00:00Z",
        "evidenceComplete": False,
        "evidenceProblems": ["missing_player_end"],
        "observations": [{
            "provider": "videasy", "client": "tv", "fixture": "sinners-2025",
            "requestType": "movie", "routeMode": "declared", "failureClass": "healthy",
        }],
    }), encoding="utf-8")
    incomplete_out = tmp / "incomplete.json"
    incomplete_md = tmp / "incomplete.md"
    incomplete = run_merge(second_out, evidence, "101", incomplete_out, second_md, incomplete_md)
    incomplete_backlog = incomplete["nativeReaderBacklog"]
    assert incomplete_backlog["openCount"] == 1, incomplete_backlog
    assert incomplete_backlog["importedRunIds"] == ["100"], incomplete_backlog
    assert incomplete_backlog["skippedIncompleteThisRun"] == 1, incomplete_backlog
    assert len(incomplete_backlog["importedEvidenceIds"]) == 2, incomplete_backlog

print("native reader automatic backlog lifecycle tests passed")
