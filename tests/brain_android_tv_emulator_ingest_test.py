#!/usr/bin/env python3
"""Official Android TV emulator -> Brain loop: exact SHA and zero authority."""
from __future__ import annotations
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/ingest_brain_android_tv_emulator.py"
spec = importlib.util.spec_from_file_location("brain_android_tv", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def report(provider="demo", *, selected=True, returned=0, complete=False):
    return {
        "schemaVersion": 5, "evidenceComplete": complete,
        "appSelectionObservations": [{
            "client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
            "requestType": "anime", "eligible": selected,
            "rawUrl": "https://PRIVATE.example/should-not-leak",
        }],
        "nativeExecutionDiagnostics": [{
            "client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
            "requestType": "anime", "failureClass": "provider_hard_timeout",
            "observedDurationMs": 25000, "configuredTimeoutMs": 25000,
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerJsMutationAllowed": False,
            "rawError": "https://PRIVATE.example/?token=SECRET",
        }],
        "quickJsPromiseControls": [{
            "client": "tv", "fixture": "jujutsu-kaisen-s01e01",
            "status": "promise_delivery_gap",
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerJsMutationAllowed": False,
            "headers": {"Authorization": "SECRET"},
        }],
        "quickJsDiagnostics": [
            {"client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
             "requestType": "anime", "phase": "call", "category": "none", "count": 0},
            {"client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
             "requestType": "anime", "phase": "result", "category": "none", "count": returned},
            {"client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
             "requestType": "anime", "phase": "error", "category": "reference_error", "count": 0,
             "rawError": "Bearer SECRET_TOKEN and URL https://PRIVATE.example"},
        ],
        "observations": [
            {"client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
             "requestType": "anime", "routeMode": "declared",
             "observationLayer": "extraction", "state": "empty",
             "failureClass": "media_extraction_gap", "returnedCount": 0,
             "url": "https://PRIVATE.example/should-never-leak"},
            {"client": "desktop", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
             "requestType": "anime", "observationLayer": "player",
             "state": "ready", "failureClass": "healthy",
             "headers": {"Cookie": "SECRET"}},
        ],
    }


with tempfile.TemporaryDirectory() as folder:
    root = Path(folder) / "source"
    (root / "providers").mkdir(parents=True)
    (root / "vf").mkdir()
    (root / "providers/demo.js").write_bytes(b"provider-js-source-a")
    (root / "manifest.json").write_text(json.dumps({"scrapers": [
        {"id": "DEMO", "enabled": True, "filename": "providers/demo.js"},
        {"id": "disabled", "enabled": False, "filename": "providers/demo.js"},
    ]}))
    (root / "vf/manifest.json").write_text('{"scrapers":[]}')
    sha = "a" * 40
    a = mod.merge({}, [report()], source_root=root, source_sha=sha, run_id="1001")
    assert a["authority"] == "official-android-tv-emulator-diagnostic-only"
    assert a["primaryClient"] == "tv"
    assert a["providerCount"] == 1 and a["observationCount"] == 1
    x = a["rows"][0]
    assert x["appSelected"] is True
    assert x["quickJsReturned"] == 0
    assert x["tvPromiseControl"] == "promise_delivery_gap"
    assert x["nativeHardTimeoutObserved"] is True
    assert x["nativeHardTimeoutMs"] == 25000
    assert x["nativeExtractionZeroObserved"] is True
    assert x["nativeExtractionPositiveObserved"] is False
    assert x["quickJsErrors"] == ["reference_error"]
    assert x["quickJsPhases"] == ["call", "result", "error"]
    assert x["playerStates"] == []
    assert x["readerEvidenceComplete"] is False
    assert len(x["providerArtifactSha256"]) == 64
    for flag in ("proofAuthority", "publicationAuthority",
                 "nativePlaybackAuthority", "providerMutationAuthority"):
        assert x[flag] is False
        assert a[flag] is False
    wire = json.dumps(a)
    for forbidden in ("PRIVATE", "Bearer", "SECRET", "Cookie", "https://", "rawError"):
        assert forbidden not in wire, forbidden

    assert mod.merge(a, [report()], source_root=root,
                     source_sha=sha, run_id="1001")["observationCount"] == 1
    (root / "providers/demo.js").write_bytes(b"provider-js-source-b")
    b = mod.merge(a, [report(returned=2, complete=True)],
                  source_root=root, source_sha="b"*40, run_id="1002")
    assert b["observationCount"] == 2
    assert b["rows"][0]["quickJsReturned"] == 2
    assert b["rows"][0]["nativeExtractionZeroObserved"] is True  # independent native result, no media proof
    assert b["rows"][0]["readerEvidenceComplete"] is True
    assert b["rows"][0]["providerArtifactSha256"] != b["rows"][1]["providerArtifactSha256"]
    assert b["rows"][0]["nativePlaybackAuthority"] is False
    assert b["rows"][1]["tvPromiseControl"] == "promise_delivery_gap"
    assert b["rows"][1]["nativeHardTimeoutObserved"] is True
    assert b["rows"][1]["nativeHardTimeoutMs"] == 25000
    for i in range(1003, 1035):
        b = mod.merge(b, [report()], source_root=root, source_sha="b"*40, run_id=str(i))
    assert b["observationCount"] == 10
    assert b["providerCount"] == 1

    disabled_report = report("disabled")
    # Never learn from a disabled provider as an executable test.
    assert mod.merge({}, [disabled_report], source_root=root,
                     source_sha=sha, run_id="1005")["observationCount"] == 0
    for invalid in ("", "short", "x" * 40):
        try:
            mod.merge({}, [report()], source_root=root, source_sha=invalid, run_id="2000")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid source SHA accepted")

    # A faked successful desktop event cannot pass as a TV player result.
    spoof = report()
    spoof["quickJsDiagnostics"] = []
    spoof["appSelectionObservations"] = []
    # Even a forged native extraction record without app selection and
    # QuickJS markers must never enter the Brain at all.
    assert mod.sanitized_rows(spoof) == []
    forged_execution = report()
    forged_execution["nativeExecutionDiagnostics"][0]["publicationAuthority"] = True
    assert mod.sanitized_rows(forged_execution)[0]["nativeHardTimeoutObserved"] is False
    forged_execution = report()
    forged_execution["nativeExecutionDiagnostics"][0]["failureClass"] = "https://private.example/t"
    assert mod.sanitized_rows(forged_execution)[0]["nativeHardTimeoutObserved"] is False
    forged_control = report()
    forged_control["quickJsPromiseControls"][0]["publicationAuthority"] = True
    assert mod.sanitized_rows(forged_control)[0]["tvPromiseControl"] == "not_observed"
    forged_control = report()
    forged_control["quickJsPromiseControls"][0]["status"] = "https://private.example/t"
    assert mod.sanitized_rows(forged_control)[0]["tvPromiseControl"] == "not_observed"
    invisible_control = report(selected=False)
    assert mod.sanitized_rows(invisible_control)[0]["tvPromiseControl"] == "not_observed"
    assert mod.sanitized_rows(invisible_control)[0]["nativeHardTimeoutObserved"] is False

    malicious = report()
    malicious["quickJsDiagnostics"][2]["category"] = "https://PRIVATE.example"
    assert mod.sanitized_rows(malicious)[0]["quickJsErrors"] == []

# Exact source-pinned TV: two results, HLS probe HTTP 403 and player READY
# without video format. Separate transport-probe hypothesis from native decode.
tv_terminal = report(returned=0, complete=True)
tv_terminal["extractionHealthyObservations"] = [
    {"client": "tv", "provider": "demo", "fixture": "jujutsu-kaisen-s01e01",
     "requestType": "anime", "routeMode": "declared",
     "observationLayer": "extraction", "state": "non_empty",
     "failureClass": "healthy", "returnedCount": 2,
     "url": "https://PRIVATE.example/?secret=TOKEN"},
]
tv_terminal["observations"] = [
    {"client": "tv", "provider": "demo", "fixture": "jujutsu-kaisen-s01e01",
     "requestType": "anime", "routeMode": "declared",
     "observationLayer": "player", "state": "ready",
     "failureClass": "healthy", "playerVideoFormatObserved": False,
     "playerAudioTrackCount": 0, "url": "https://PRIVATE.example/?secret=TOKEN"},
]
tv_terminal["terminalTransportDiagnostics"] = [{
    "client": "tv", "provider": "demo", "fixture": "jujutsu-kaisen-s01e01",
    "requestType": "anime", "index": 0,
    "source": "independent-terminal-transport-probe",
    "state": "dead", "kind": "hls", "httpStatus": 403,
    "proofAuthority": False, "publicationAuthority": False,
    "nativePlaybackAuthority": False, "providerJsMutationAllowed": False,
    "url": "https://PRIVATE.example/?secret=TOKEN",
    "headers": {"Cookie": "PRIVATE"},
}]
tv_row = mod.sanitized_rows(tv_terminal)[0]
assert tv_row["nativeExtractionPositiveObserved"] is True
assert tv_row["nativeExtractionReturnedCount"] == 2
assert tv_terminal["quickJsDiagnostics"][0]["phase"] == "call"
assert tv_terminal["extractionHealthyObservations"][0]["returnedCount"] == 2
assert tv_row["quickJsReturned"] == 0  # no QuickJS console result is not empty extraction
assert tv_row["playerVideoFormatUnverified"] is True
assert tv_row["independentTerminalHttpStatuses"] == [403]
assert tv_row["nativePlaybackAuthority"] is False
assert "PRIVATE" not in json.dumps(tv_row)
faked = json.loads(json.dumps(tv_terminal))
faked["terminalTransportDiagnostics"][0]["providerJsMutationAllowed"] = True
assert mod.sanitized_rows(faked)[0]["independentTerminalHttpStatuses"] == []
faked = json.loads(json.dumps(tv_terminal))
faked["terminalTransportDiagnostics"][0]["httpStatus"] = 200
assert mod.sanitized_rows(faked)[0]["independentTerminalHttpStatuses"] == []
faked = json.loads(json.dumps(tv_terminal))
faked["observations"][0]["playerVideoFormatObserved"] = True
assert mod.sanitized_rows(faked)[0]["playerVideoFormatUnverified"] is False
faked = report(selected=False)
faked["terminalTransportDiagnostics"] = tv_terminal["terminalTransportDiagnostics"]
assert mod.sanitized_rows(faked)[0]["independentTerminalHttpStatuses"] == []

native_workflow = (ROOT / ".github/workflows/native-corpus-device-targeted.yml").read_text()
feedback_workflow = (ROOT / ".github/workflows/brain-android-tv-emulator-feedback.yml").read_text()
assert "Diagnose sanitized targeted native evidence for Brain" in native_workflow
assert "native-corpus-tv-*" in feedback_workflow
assert "github.event.workflow_run.head_repository.full_name == github.repository" in feedback_workflow
assert "github.event.workflow_run.head_branch == 'main'" in feedback_workflow
assert "tested-source" in feedback_workflow
assert "ingest_brain_android_tv_emulator.py" in feedback_workflow
assert "automation/brain-android-tv-emulator-history.json" in feedback_workflow
assert "route_android_tv_emulator_feedback.py" in feedback_workflow
assert "--source-sha \"$NATIVE_SOURCE_SHA\"" in feedback_workflow
assert "--run-id \"$NATIVE_RUN_ID\"" in feedback_workflow
assert "brain-tv-route-" in feedback_workflow
assert "persist-credentials: false" in feedback_workflow
print("Brain Android TV emulator exact-SHA feedback and privacy contract passed")
