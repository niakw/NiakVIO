#!/usr/bin/env python3
"""Merge complete native-reader diagnoses into a persistent sanitized backlog.

The backlog is keyed by client/provider/fixture/request-type/failure-class and is
updated only from complete official-reader evidence. Capability probes are not
bugs. Healthy fresh evidence resolves prior failures for the same route. No raw
media URLs, query strings, header values, cookies, tokens, or exception payloads
are persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECTION_BEGIN = "<!-- NATIVE_READER_BACKLOG_BEGIN -->"
SECTION_END = "<!-- NATIVE_READER_BACKLOG_END -->"


def read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def clean(value: Any, limit: int = 128) -> str:
    text = str(value or "").strip()
    folded = text.casefold()
    if "://" in text or any(token in folded for token in ("authorization=", "cookie=", "token=", "secret=")):
        return ""
    return text[:limit]


def non_negative(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def route_key(client: str, provider: str, fixture: str, request_type: str) -> str:
    return "\0".join((client, provider, fixture, request_type))


def issue_key(client: str, provider: str, fixture: str, request_type: str, failure_class: str) -> str:
    return "\0".join((client, provider, fixture, request_type, failure_class))


def issue_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def evidence_id(run_id: str, path: Path, payload: dict[str, Any]) -> str:
    safe = {
        "runId": run_id,
        "file": path.name,
        "generatedAt": clean(payload.get("generatedAt"), 64),
        "readerObserved": non_negative(payload.get("readerObserved")),
        "readerFailures": non_negative(payload.get("readerFailures")),
        "providerLoadObservedFailures": non_negative(payload.get("providerLoadObservedFailures")),
        "providerOutcomes": payload.get("providerOutcomes") if isinstance(payload.get("providerOutcomes"), list) else [],
    }
    raw = json.dumps(safe, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def classification(failure_class: str, *, load_issue: dict[str, Any] | None = None) -> dict[str, Any]:
    failure = clean(failure_class, 96) or "unknown_failure"
    if load_issue is not None or failure.startswith("provider_repository_"):
        return {
            "layer": clean((load_issue or {}).get("layer"), 64) or "repository",
            "scope": "repository_or_manifest",
            "externalCandidate": False,
            "providerJsMutationAllowed": False,
        }
    if failure in {"playback_runtime_setup", "runtime_contract_drift"}:
        return {
            "layer": "client_runtime",
            "scope": "client_or_core",
            "externalCandidate": False,
            "providerJsMutationAllowed": False,
        }
    if failure in {
        "playback_http_access", "playback_http_gone", "playback_rate_limited",
        "playback_http_upstream", "playback_dns", "playback_tls",
    }:
        return {
            "layer": "playback_transport",
            "scope": "external_or_context",
            "externalCandidate": True,
            "providerJsMutationAllowed": False,
        }
    if failure in {"playback_decoder", "short_media", "playback_duration_unknown", "media_validation_gap", "playback_parser"}:
        return {
            "layer": "media_candidate",
            "scope": "provider_media_or_compatibility",
            "externalCandidate": False,
            "providerJsMutationAllowed": True,
        }
    return {
        "layer": "provider_or_playback_context",
        "scope": "provider_or_context",
        "externalCandidate": False,
        "providerJsMutationAllowed": True,
    }


def sanitize_existing(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    client = clean(raw.get("client"), 32).lower()
    provider = clean(raw.get("providerId"), 128).casefold()
    fixture = clean(raw.get("fixture"), 96)
    request_type = clean(raw.get("requestType"), 32).lower() or "unknown"
    failure_class = clean(raw.get("failureClass"), 96) or "unknown_failure"
    if not client or not provider or not fixture:
        return None
    key = issue_key(client, provider, fixture, request_type, failure_class)
    return {
        "id": clean(raw.get("id"), 32) or issue_id(key),
        "client": client,
        "providerId": provider,
        "fixture": fixture,
        "requestType": request_type,
        "failureClass": failure_class,
        "layer": clean(raw.get("layer"), 64) or "unknown",
        "scope": clean(raw.get("scope"), 64) or "unknown",
        "status": clean(raw.get("status"), 24) or "open",
        "externalCandidate": bool(raw.get("externalCandidate", False)),
        "providerJsMutationAllowed": bool(raw.get("providerJsMutationAllowed", False)),
        "occurrences": non_negative(raw.get("occurrences")),
        "consecutiveFailures": non_negative(raw.get("consecutiveFailures")),
        "healthyRetests": non_negative(raw.get("healthyRetests")),
        "firstSeenAt": clean(raw.get("firstSeenAt"), 64) or None,
        "lastSeenAt": clean(raw.get("lastSeenAt"), 64) or None,
        "resolvedAt": clean(raw.get("resolvedAt"), 64) or None,
        "lastRunId": clean(raw.get("lastRunId"), 32) or None,
        "lastOutcome": clean(raw.get("lastOutcome"), 32) or None,
        "lastReason": clean(raw.get("lastReason"), 160) or None,
        "hypotheses": [clean(v, 96) for v in raw.get("hypotheses") or [] if clean(v, 96)][:12],
        "skills": [clean(v, 96) for v in raw.get("skills") or [] if clean(v, 96)][:12],
    }


def render_markdown(base: str, backlog: dict[str, Any]) -> str:
    if SECTION_BEGIN in base and SECTION_END in base:
        prefix = base.split(SECTION_BEGIN, 1)[0].rstrip()
        suffix = base.split(SECTION_END, 1)[1].lstrip()
        base = prefix + ("\n\n" + suffix if suffix else "")
    entries = [row for row in backlog.get("entries") or [] if isinstance(row, dict)]
    open_rows = [row for row in entries if row.get("status") == "open"]
    resolved_rows = [row for row in entries if row.get("status") == "resolved"]
    external_rows = [row for row in open_rows if row.get("externalCandidate")]
    lines = [
        SECTION_BEGIN,
        "## Native reader bug backlog",
        "",
        f"Open reader bugs: **{len(open_rows)}**  ",
        f"Resolved reader bugs retained: **{len(resolved_rows)}**  ",
        f"Open external/context candidates: **{len(external_rows)}**",
        "",
    ]
    if open_rows:
        lines.extend([
            "| Provider | Client | Fixture | Failure | Scope | Count |",
            "|---|---|---|---|---|---:|",
        ])
        for row in open_rows[:80]:
            lines.append(
                f"| `{clean(row.get('providerId'), 64)}` | {clean(row.get('client'), 24)} | "
                f"{clean(row.get('fixture'), 64)} | `{clean(row.get('failureClass'), 64)}` | "
                f"{clean(row.get('scope'), 48)} | {non_negative(row.get('occurrences'))} |"
            )
        lines.append("")
    lines.append(SECTION_END)
    return base.rstrip() + "\n\n" + "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--diagnostics-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-input", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--max-entries", type=int, default=2000)
    parser.add_argument("--max-evidence-ids", type=int, default=500)
    args = parser.parse_args()

    run_id = clean(args.run_id, 32)
    if not run_id.isdigit():
        raise SystemExit(f"invalid run id: {run_id!r}")
    state = read_json(args.state)
    output = args.output or args.state
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    prior = state.get("nativeReaderBacklog") if isinstance(state.get("nativeReaderBacklog"), dict) else {}
    imported_evidence = [clean(v, 40) for v in prior.get("importedEvidenceIds") or [] if clean(v, 40)]
    imported_evidence = list(dict.fromkeys(imported_evidence))[-max(1, int(args.max_evidence_ids)):]
    imported_set = set(imported_evidence)
    imported_runs = [clean(v, 32) for v in prior.get("importedRunIds") or [] if clean(v, 32).isdigit()]
    imported_runs = list(dict.fromkeys(imported_runs))[-100:]

    entries: dict[str, dict[str, Any]] = {}
    for raw in prior.get("entries") or []:
        row = sanitize_existing(raw)
        if row:
            entries[issue_key(row["client"], row["providerId"], row["fixture"], row["requestType"], row["failureClass"])] = row

    roots = sorted(args.diagnostics_root.rglob("*brain.json")) if args.diagnostics_root.exists() else []
    imported_files = 0
    skipped_incomplete = 0
    skipped_duplicate = 0
    opened = 0
    resolved = 0

    for path in roots:
        diagnosis = read_json(path)
        if not diagnosis:
            continue
        if diagnosis.get("evidenceComplete") is not True:
            skipped_incomplete += 1
            continue
        eid = evidence_id(run_id, path, diagnosis)
        if eid in imported_set:
            skipped_duplicate += 1
            continue

        observations = [row for row in diagnosis.get("observations") or [] if isinstance(row, dict)]
        load_issues = [row for row in diagnosis.get("providerLoadIssues") or [] if isinstance(row, dict)]
        routes: dict[str, dict[str, Any]] = {}
        providers_seen: set[tuple[str, str, str]] = set()

        for raw in observations:
            if clean(raw.get("routeMode"), 32).lower() == "capability_probe":
                continue
            client = clean(raw.get("client"), 32).lower()
            provider = clean(raw.get("provider"), 128).casefold()
            fixture = clean(raw.get("fixture"), 96)
            request_type = clean(raw.get("requestType"), 32).lower() or "unknown"
            failure = clean(raw.get("failureClass"), 96) or "unknown_failure"
            if not client or not provider or not fixture:
                continue
            providers_seen.add((client, provider, fixture))
            rkey = route_key(client, provider, fixture, request_type)
            route = routes.setdefault(rkey, {
                "client": client,
                "provider": provider,
                "fixture": fixture,
                "requestType": request_type,
                "healthy": 0,
                "failures": {},
            })
            if failure == "healthy":
                route["healthy"] += 1
            else:
                route["failures"][failure] = non_negative(route["failures"].get(failure)) + 1

        load_keys: set[str] = set()
        for issue in load_issues:
            client = clean(issue.get("client"), 32).lower()
            provider = clean(issue.get("provider"), 128).casefold()
            fixture = clean(issue.get("fixture"), 96)
            failure = clean(issue.get("failureClass"), 96) or "provider_repository_load_error"
            if not client or not provider or not fixture:
                continue
            key = issue_key(client, provider, fixture, "repository", failure)
            load_keys.add(key)
            current = entries.get(key)
            cls = classification(failure, load_issue=issue)
            if current is None:
                current = {
                    "id": issue_id(key), "client": client, "providerId": provider, "fixture": fixture,
                    "requestType": "repository", "failureClass": failure,
                    "occurrences": 0, "consecutiveFailures": 0, "healthyRetests": 0,
                    "firstSeenAt": now, "resolvedAt": None, "hypotheses": [], "skills": [],
                }
                opened += 1
            current.update(cls)
            current["status"] = "open"
            current["occurrences"] = non_negative(current.get("occurrences")) + 1
            current["consecutiveFailures"] = non_negative(current.get("consecutiveFailures")) + 1
            current["lastSeenAt"] = now
            current["resolvedAt"] = None
            current["lastRunId"] = run_id
            current["lastOutcome"] = "failure"
            current["lastReason"] = clean(issue.get("reason"), 160) or failure
            entries[key] = current

        for route in routes.values():
            client, provider, fixture, request_type = route["client"], route["provider"], route["fixture"], route["requestType"]
            failures: dict[str, int] = route["failures"]
            base = route_key(client, provider, fixture, request_type)

            # Any previous failure class for this exact route that disappeared in
            # fresh complete evidence is resolved. If another class appeared, the
            # old class closes and the new class becomes the active bug.
            for key, current in list(entries.items()):
                if route_key(current["client"], current["providerId"], current["fixture"], current["requestType"]) != base:
                    continue
                if current.get("status") != "open":
                    continue
                if current["failureClass"] in failures:
                    continue
                current["status"] = "resolved"
                current["healthyRetests"] = non_negative(current.get("healthyRetests")) + (1 if route["healthy"] else 0)
                current["consecutiveFailures"] = 0
                current["resolvedAt"] = now
                current["lastSeenAt"] = now
                current["lastRunId"] = run_id
                current["lastOutcome"] = "healthy" if route["healthy"] else "failure_class_changed"
                current["lastReason"] = "fresh_native_reader_route_no_longer_reports_this_failure_class"
                entries[key] = current
                resolved += 1

            for failure, count in failures.items():
                key = issue_key(client, provider, fixture, request_type, failure)
                current = entries.get(key)
                cls = classification(failure)
                if current is None:
                    current = {
                        "id": issue_id(key), "client": client, "providerId": provider, "fixture": fixture,
                        "requestType": request_type, "failureClass": failure,
                        "occurrences": 0, "consecutiveFailures": 0, "healthyRetests": 0,
                        "firstSeenAt": now, "resolvedAt": None, "hypotheses": [], "skills": [],
                    }
                    opened += 1
                current.update(cls)
                current["status"] = "open"
                current["occurrences"] = non_negative(current.get("occurrences")) + max(1, count)
                current["consecutiveFailures"] = non_negative(current.get("consecutiveFailures")) + 1
                current["lastSeenAt"] = now
                current["resolvedAt"] = None
                current["lastRunId"] = run_id
                current["lastOutcome"] = "failure"
                current["lastReason"] = failure
                entries[key] = current

        # A provider that previously failed to load but now reaches reader
        # observations has fresh proof that the repository/load defect is gone.
        for key, current in list(entries.items()):
            if current.get("status") != "open" or current.get("requestType") != "repository":
                continue
            triple = (current["client"], current["providerId"], current["fixture"])
            if triple not in providers_seen or key in load_keys:
                continue
            current["status"] = "resolved"
            current["healthyRetests"] = non_negative(current.get("healthyRetests")) + 1
            current["consecutiveFailures"] = 0
            current["resolvedAt"] = now
            current["lastSeenAt"] = now
            current["lastRunId"] = run_id
            current["lastOutcome"] = "provider_loaded"
            current["lastReason"] = "fresh_complete_evidence_reached_reader_after_prior_load_failure"
            entries[key] = current
            resolved += 1

        imported_evidence.append(eid)
        imported_set.add(eid)
        imported_files += 1

    if imported_files:
        imported_runs = [v for v in imported_runs if v != run_id] + [run_id]

    ordered = sorted(
        entries.values(),
        key=lambda row: (
            0 if row.get("status") == "open" else 1,
            -non_negative(row.get("consecutiveFailures")),
            str(row.get("lastSeenAt") or ""),
            str(row.get("providerId") or ""),
        ),
    )[: max(1, int(args.max_entries))]

    backlog = {
        "schemaVersion": 1,
        "updatedAt": now,
        "lastRunId": run_id if imported_files else prior.get("lastRunId"),
        "importedRunIds": imported_runs[-100:],
        "importedEvidenceIds": imported_evidence[-max(1, int(args.max_evidence_ids)):],
        "importedDiagnosisFilesThisRun": imported_files,
        "skippedIncompleteThisRun": skipped_incomplete,
        "skippedDuplicateThisRun": skipped_duplicate,
        "openCount": sum(1 for row in ordered if row.get("status") == "open"),
        "resolvedCount": sum(1 for row in ordered if row.get("status") == "resolved"),
        "externalCandidateOpenCount": sum(1 for row in ordered if row.get("status") == "open" and row.get("externalCandidate")),
        "entries": ordered,
    }
    state["nativeReaderBacklog"] = backlog
    state["privacy"] = "No raw URLs, query tokens, header values, cookies, credentials or private notes are persisted in Brain state. Reader backlog stores only sanitized route identities and aggregate outcomes."

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        base = "# NiakVIO Brain Learning\n"
        if args.markdown_input and args.markdown_input.is_file():
            base = args.markdown_input.read_text(encoding="utf-8")
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(base, backlog), encoding="utf-8")

    print(
        "FIELD_NATIVE_READER_BACKLOG "
        f"run={run_id} imported_files={imported_files} opened={opened} resolved={resolved} "
        f"open={backlog['openCount']} external_candidates={backlog['externalCandidateOpenCount']} "
        f"skipped_incomplete={skipped_incomplete} skipped_duplicate={skipped_duplicate}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
