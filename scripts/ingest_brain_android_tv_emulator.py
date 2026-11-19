#!/usr/bin/env python3
"""Import official Android-TV emulator diagnoses into source-pinned Brain memory.

The native emulator remains in its existing GitHub Actions workflow. This
consumer reads only its already-redacted *-brain.json outputs, never raw
logcat, player URLs, HTTP headers, credentials or screenshots.

All imported observations are hypotheses, not provider mutation, successful
playback, or publication authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
IDENT = re.compile(r"[a-z0-9][a-z0-9_-]{0,95}")
FIXTURE = re.compile(r"[a-z0-9][a-z0-9-]{0,95}")
LANES = {"movie", "tv", "anime"}
QUICKJS_PHASES = {"call", "result", "error", "missing_export"}
TV_PROMISE_STATUSES = {"bridge_ok", "promise_delivery_gap", "baseline_failed"}
QUICKJS_CLASSES = {
    "none", "reference_error", "type_error", "syntax_error", "timeout",
    "network_error", "http_error", "unspecified_js_exception",
}
PLAYER_STATES = {
    "ready", "playing", "error", "short_media", "buffering", "unknown",
    "ended", "timeout", "not_reached", "paused",
}
PLAYER_FAILURES = {
    "healthy", "http_access", "playback_runtime_setup", "playback_player_error",
    "playback_decoder", "duration_identity", "terminal_media_gap",
    "runtime_contract_drift", "media_extraction_gap", "client_runtime_error",
}
MAX_REPORT_BYTES = 2 * 1024 * 1024
MAX_PER_PROVIDER = 10
MAX_PROVIDERS = 140
MAX_ROWS = MAX_PROVIDERS * MAX_PER_PROVIDER


def safe_id(value: Any, pattern: re.Pattern[str]) -> str:
    value = str(value or "").strip().lower()
    return value if pattern.fullmatch(value) else ""


def safe_count(value: Any) -> int:
    return min(10000, max(0, value)) if type(value) is int else 0


def digest_for(source_root: Path, provider: str) -> tuple[str, str]:
    """Only active canonical Global/VF bytes are valid native test targets."""
    root = source_root.resolve()
    for manifest_name in ("manifest.json", "vf/manifest.json"):
        manifest_path = root / manifest_name
        manifest = json.loads(manifest_path.read_text("utf-8"))
        for row in manifest.get("scrapers") or []:
            if not isinstance(row, dict):
                continue
            if safe_id(row.get("id"), IDENT).replace("_", "-") != provider.replace("_", "-"):
                continue
            if row.get("enabled") is not True:
                continue
            source = (manifest_path.parent / str(row.get("filename") or "")).resolve()
            try:
                relative = source.relative_to(root).parts
            except ValueError:
                raise ValueError("active provider escapes exact source checkout") from None
            if not relative or relative[0] != "providers" or not source.is_file():
                raise ValueError("active provider must resolve into providers/")
            return hashlib.sha256(source.read_bytes()).hexdigest(), manifest_name
    return "", ""


def sanitized_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    if report.get("schemaVersion") != 5:
        return []
    if type(report.get("evidenceComplete")) is not bool:
        return []
    samples: dict[tuple[str, str, str], dict[str, Any]] = {}

    def get(raw: dict[str, Any]) -> dict[str, Any] | None:
        if raw.get("client") != "tv":
            return None
        provider = safe_id(raw.get("provider"), IDENT)
        fixture = safe_id(raw.get("fixture"), FIXTURE)
        lane = str(raw.get("requestType") or "").strip().lower()
        if not provider or not fixture or lane not in LANES:
            return None
        key = (provider.replace("_", "-"), fixture, lane)
        if key not in samples:
            samples[key] = {
                "provider": key[0], "fixture": fixture, "requestType": lane,
                "appSelected": None, "tvPromiseControl": "not_observed", "quickJsPhases": [],
                "nativeHardTimeoutObserved": False, "nativeHardTimeoutMs": 0,
                "quickJsErrors": [], "quickJsReturned": 0,
                "nativeExtractionZeroObserved": False,
                "nativeExtractionPositiveObserved": False,
                "nativeExtractionReturnedCount": 0,
                "playerVideoFormatUnverified": False,
                "independentTerminalHttpStatuses": [],
                "playerStates": [], "playerFailureClasses": [],
                "readerEvidenceComplete": report["evidenceComplete"],
                "proofAuthority": False, "publicationAuthority": False,
                "nativePlaybackAuthority": False,
                "providerMutationAuthority": False,
            }
        return samples[key]

    for raw in (report.get("appSelectionObservations") or [])[:200]:
        if not isinstance(raw, dict):
            continue
        row = get(raw)
        if row is not None and type(raw.get("eligible")) is bool:
            row["appSelected"] = raw["eligible"]

    for raw in (report.get("quickJsDiagnostics") or [])[:300]:
        if not isinstance(raw, dict):
            continue
        row = get(raw)
        if row is None:
            continue
        phase = str(raw.get("phase") or "")
        error = str(raw.get("category") or "")
        if phase not in QUICKJS_PHASES or error not in QUICKJS_CLASSES:
            continue
        if phase not in row["quickJsPhases"]:
            row["quickJsPhases"].append(phase)
        if phase == "error" and error not in row["quickJsErrors"]:
            row["quickJsErrors"].append(error)
        if phase == "result":
            row["quickJsReturned"] = max(row["quickJsReturned"], safe_count(raw.get("count")))

    # Native diagnosis deliberately publishes successful extraction separately
    # from failure-only "observations". Without this union the Brain saw
    # QuickJS call_count=0 even when official FIELD_NATIVE_RESULT count=2.
    # Both channels still require exact same provider/app selection.
    failure_rows = report.get("observations")
    positive_rows = report.get("extractionHealthyObservations")
    failure_rows = failure_rows if isinstance(failure_rows, list) else []
    positive_rows = positive_rows if isinstance(positive_rows, list) else []
    for raw in failure_rows[:400] + positive_rows[:128]:
        if not isinstance(raw, dict):
            continue
        layer = raw.get("observationLayer")
        if layer not in {"player", "extraction"}:
            continue
        row = get(raw)
        if row is None:
            continue
        if layer == "extraction":
            # Source-pinned FIELD_NATIVE_RESULT count=0 can prove a completed
            # empty extractor even when console only exposes QuickJS phase=call.
            # It does not prove that a media player or episode was validated.
            returned = raw.get("returnedCount")
            if (
                raw.get("routeMode") == "declared"
                and raw.get("state") == "empty"
                and raw.get("failureClass") == "media_extraction_gap"
                and type(returned) is int and returned == 0
            ):
                row["nativeExtractionZeroObserved"] = True
            elif (
                raw.get("routeMode") == "declared"
                and raw.get("state") == "non_empty"
                and raw.get("failureClass") == "healthy"
                and type(returned) is int and 0 < returned <= 10000
            ):
                row["nativeExtractionPositiveObserved"] = True
                row["nativeExtractionReturnedCount"] = max(
                    row["nativeExtractionReturnedCount"], safe_count(returned)
                )
            continue
        state = str(raw.get("state") or "")
        failure = str(raw.get("failureClass") or "")
        if state in PLAYER_STATES and state not in row["playerStates"]:
            row["playerStates"].append(state)
        if failure in PLAYER_FAILURES and failure not in row["playerFailureClasses"]:
            row["playerFailureClasses"].append(failure)
        # An official READY state can precede decoded/video-track proof. Do
        # not transmute a missing track into player health or mutation rights.
        if (
            state in {"ready", "ended"}
            and raw.get("playerVideoFormatObserved") is False
            and raw.get("routeMode") == "declared"
        ):
            row["playerVideoFormatUnverified"] = True

    # HTTP status comes from an independent network probe, NOT an observed
    # player decoder/network result; it remains a bounded negative hypothesis.
    for item in (report.get("terminalTransportDiagnostics") or [])[:128]:
        if not isinstance(item, dict):
            continue
        row = get(item)
        if (
            row is None or item.get("source") != "independent-terminal-transport-probe"
            or item.get("state") not in {"dead", "error"}
            or item.get("kind") not in {"hls", "dash", "video", "html", "unknown"}
            or any(item.get(k) is not False for k in (
                "proofAuthority", "publicationAuthority",
                "nativePlaybackAuthority", "providerJsMutationAllowed",
            ))
            or type(item.get("index")) is not int or not 0 <= item["index"] <= 40
            or type(item.get("httpStatus")) is not int
            or not 400 <= item["httpStatus"] <= 599
        ):
            continue
        if item["httpStatus"] not in row["independentTerminalHttpStatuses"]:
            row["independentTerminalHttpStatuses"].append(item["httpStatus"])
            row["independentTerminalHttpStatuses"].sort()
            row["independentTerminalHttpStatuses"] = row["independentTerminalHttpStatuses"][:8]

    for item in (report.get("nativeExecutionDiagnostics") or [])[:200]:
        if not isinstance(item, dict):
            continue
        row = get(item)
        if (
            row is None
            or item.get("failureClass") != "provider_hard_timeout"
            or any(item.get(key) is not False for key in (
                "proofAuthority", "publicationAuthority",
                "nativePlaybackAuthority", "providerJsMutationAllowed",
            ))
        ):
            continue
        duration = item.get("observedDurationMs")
        configured = item.get("configuredTimeoutMs")
        if (
            type(duration) is int and 1000 <= duration <= 180000
            and type(configured) is int and 1000 <= configured <= 180000
        ):
            row["nativeHardTimeoutObserved"] = True
            row["nativeHardTimeoutMs"] = duration

    # Synthetic control status is fixture-scoped test-harness diagnostics,
    # not proof of any actual media URL, episode or provider correction.
    controls: dict[str, str] = {}
    for item in (report.get("quickJsPromiseControls") or [])[:32]:
        if not isinstance(item, dict):
            continue
        fixture = safe_id(item.get("fixture"), FIXTURE)
        status = str(item.get("status") or "")
        if (item.get("client") != "tv" or not fixture or status not in TV_PROMISE_STATUSES):
            continue
        if any(item.get(key) is not False for key in (
            "proofAuthority", "publicationAuthority", "nativePlaybackAuthority",
            "providerJsMutationAllowed",
        )):
            continue
        controls[fixture] = status
    for row in samples.values():
        if row["appSelected"] is True:
            row["tvPromiseControl"] = controls.get(row["fixture"], "not_observed")

    # An extracted QuickJS/media marker without a matching official app
    # selection cannot prove the provider was eligible or executed. Preserve
    # legitimate excluded-client observations only as client selection facts.
    accepted = []
    for row in samples.values():
        if type(row["appSelected"]) is not bool:
            continue
        if row["appSelected"] is False:
            row["quickJsPhases"] = []
            row["quickJsErrors"] = []
            row["quickJsReturned"] = 0
            row["nativeExtractionZeroObserved"] = False
            row["nativeExtractionPositiveObserved"] = False
            row["nativeExtractionReturnedCount"] = 0
            row["playerVideoFormatUnverified"] = False
            row["independentTerminalHttpStatuses"] = []
            row["nativeHardTimeoutObserved"] = False
            row["nativeHardTimeoutMs"] = 0
            row["playerStates"] = []
            row["playerFailureClasses"] = []
        accepted.append(row)
    return accepted[:32]


def merge(previous: dict[str, Any], reports: list[dict[str, Any]], *,
          source_root: Path, source_sha: str, run_id: str) -> dict[str, Any]:
    if not SHA40.fullmatch(source_sha) or not run_id.isdigit():
        raise ValueError("native run requires a complete source commit and numeric run id")
    previous_rows = previous.get("rows") if isinstance(previous, dict) else []
    if not isinstance(previous_rows, list):
        previous_rows = []
    # Never trust old entries as an authority. Resanitize through exact static
    # whitelists even if a previous ledger was modified externally.
    entries: list[dict[str, Any]] = []
    for record in previous_rows[:MAX_ROWS]:
        if not isinstance(record, dict):
            continue
        provider = safe_id(record.get("provider"), IDENT)
        fixture = safe_id(record.get("fixture"), FIXTURE)
        lane = str(record.get("requestType") or "")
        digest = str(record.get("providerArtifactSha256") or "")
        sha = str(record.get("sourceNiakvioSha") or "")
        run = str(record.get("nativeRunId") or "")
        if not (provider and fixture and lane in LANES and SHA64.fullmatch(digest)
                and SHA40.fullmatch(sha) and run.isdigit()):
            continue
        sanitized = {
            "provider": provider, "fixture": fixture, "requestType": lane,
            "providerArtifactSha256": digest, "sourceNiakvioSha": sha,
            "nativeRunId": run,
            "manifestScope": record.get("manifestScope")
                if record.get("manifestScope") in {"manifest.json", "vf/manifest.json"} else "",
            "appSelected": record.get("appSelected")
                if type(record.get("appSelected")) is bool else None,
            "tvPromiseControl": record.get("tvPromiseControl")
                if record.get("tvPromiseControl") in TV_PROMISE_STATUSES else "not_observed",
            "nativeHardTimeoutObserved": record.get("nativeHardTimeoutObserved") is True,
            "nativeHardTimeoutMs": min(180000, max(0, record.get("nativeHardTimeoutMs")))
                if record.get("nativeHardTimeoutObserved") is True
                and type(record.get("nativeHardTimeoutMs")) is int
                and record.get("nativeHardTimeoutMs") >= 1000 else 0,
            "quickJsPhases": [x for x in (record.get("quickJsPhases") or [])
                              if x in QUICKJS_PHASES][:4],
            "quickJsErrors": [x for x in (record.get("quickJsErrors") or [])
                              if x in QUICKJS_CLASSES][:8],
            "quickJsReturned": safe_count(record.get("quickJsReturned")),
            "nativeExtractionZeroObserved": record.get("nativeExtractionZeroObserved") is True,
            "nativeExtractionPositiveObserved": record.get("nativeExtractionPositiveObserved") is True,
            "nativeExtractionReturnedCount": safe_count(record.get("nativeExtractionReturnedCount"))
                if record.get("nativeExtractionPositiveObserved") is True else 0,
            "playerVideoFormatUnverified": record.get("playerVideoFormatUnverified") is True,
            "independentTerminalHttpStatuses": sorted({
                v for v in (record.get("independentTerminalHttpStatuses") or [])
                if type(v) is int and 400 <= v <= 599
            })[:8],
            "playerStates": [x for x in (record.get("playerStates") or [])
                             if x in PLAYER_STATES][:8],
            "playerFailureClasses": [x for x in (record.get("playerFailureClasses") or [])
                                     if x in PLAYER_FAILURES][:8],
            "readerEvidenceComplete": record.get("readerEvidenceComplete") is True,
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerMutationAuthority": False,
        }
        entries.append(sanitized)

    for report in reports[:32]:
        for row in sanitized_rows(report):
            provider = row["provider"]
            digest, scope = digest_for(source_root, provider)
            if not digest:
                continue
            entries.append({
                **row, "providerArtifactSha256": digest,
                "sourceNiakvioSha": source_sha,
                "nativeRunId": run_id, "manifestScope": scope,
            })

    seen: set[tuple[str, str, str, str, str]] = set()
    per_provider: dict[str, int] = {}
    result = []
    for row in reversed(entries):
        key = (
            row["provider"], row["providerArtifactSha256"],
            row["nativeRunId"], row["fixture"], row["requestType"],
        )
        if key in seen or per_provider.get(row["provider"], 0) >= MAX_PER_PROVIDER:
            continue
        if row["provider"] not in per_provider and len(per_provider) >= MAX_PROVIDERS:
            continue
        seen.add(key)
        per_provider[row["provider"]] = per_provider.get(row["provider"], 0) + 1
        result.append(row)
    return {
        "schemaVersion": 1,
        "authority": "official-android-tv-emulator-diagnostic-only",
        "primaryClient": "tv",
        "providerCount": len(per_provider),
        "observationCount": len(result),
        "rows": result,
        "proofAuthority": False, "publicationAuthority": False,
        "nativePlaybackAuthority": False, "providerMutationAuthority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.reports.rglob("*-brain.json")) if args.reports.is_dir() else []
    reports = []
    for path in files[:32]:
        if path.stat().st_size > MAX_REPORT_BYTES:
            raise ValueError("native diagnostic report exceeds maximum size")
        report = json.loads(path.read_text("utf-8"))
        if not isinstance(report, dict):
            raise ValueError("invalid emulator diagnostic report")
        reports.append(report)
    previous = json.loads(args.ledger.read_text("utf-8")) if args.ledger.exists() else {}
    result = merge(previous, reports,
                   source_root=args.source_root, source_sha=args.source_sha,
                   run_id=args.run_id)
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", "utf-8")
    print("FIELD_BRAIN_ANDROID_TV_INGEST "
          f"reports={len(reports)} rows={result['observationCount']} "
          f"providers={result['providerCount']} mutation_authority=false "
          "native_playback_authority=false")


if __name__ == "__main__":
    main()
