#!/usr/bin/env python3
"""Cross-check Deep worker zero-request results against the production-like Nuvio probe.

This is a harness-authority diagnostic, not provider acceptance evidence.
A provider is classified as a harness differential only when:
- Deep tested an exact staged provider artifact and reported no provider request;
- the same artifact SHA is verified locally;
- the same fixture is replayed through nuvio_tv_probe_tmdb_ci.cjs; and
- that production-like probe observes at least one provider-owned request.

No URLs, headers, bodies, credentials or response payloads are persisted.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def fixture_identity(raw: object) -> dict[str, Any]:
    fixture = raw if isinstance(raw, dict) else {}
    return {
        key: fixture.get(key)
        for key in (
            "tmdbId",
            "mediaType",
            "category",
            "title",
            "year",
            "season",
            "episode",
            "animeMovie",
        )
        if fixture.get(key) is not None
    }


def parse_nuvio_probe(stdout: str) -> dict[str, Any] | None:
    for line in reversed(str(stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def worker_zero_request(test: dict[str, Any]) -> bool:
    if str(test.get("failure_class") or "") == "no_provider_request_observed":
        return True
    observations = [
        row
        for row in test.get("network_observations") or []
        if isinstance(row, dict) and row.get("infrastructure") is not True
    ]
    if observations:
        return False
    diagnostics = [
        row
        for row in test.get("invocation_diagnostics") or []
        if isinstance(row, dict)
    ]
    return bool(diagnostics) and all(
        int(row.get("provider_observations") or 0) == 0
        for row in diagnostics
    )


def invocation_summary(test: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": str(row.get("name") or "")[:80],
            "inferredMode": str(row.get("inferred_mode") or "")[:40],
            "result": str(row.get("result") or "")[:40],
            "streamCount": int(row.get("stream_count") or 0),
            "providerObservations": int(row.get("provider_observations") or 0),
            "errorCode": str((row.get("error") or {}).get("code") or "")[:100]
            if isinstance(row.get("error"), dict)
            else "",
        }
        for row in test.get("invocation_diagnostics") or []
        if isinstance(row, dict)
    ][:12]


def candidate_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in registry.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "")
        provider = cid(row.get("canonical_id") or row.get("upstream_id"))
        if key:
            out[key] = row
        if provider:
            out.setdefault(provider, row)
    return out


def exact_stage_sha(stage: Path, candidate: dict[str, Any]) -> tuple[str, str]:
    relative = str(candidate.get("local_path") or "").strip()
    if not relative:
        return "", ""
    path = (stage / relative).resolve()
    try:
        path.relative_to(stage.resolve())
    except ValueError:
        return "", ""
    if not path.is_file():
        return "", ""
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = str(candidate.get("sha256") or "").strip().casefold()
    return actual, expected


def run_nuvio_probe(provider_path: Path, fixture: dict[str, Any], *, timeout: int = 55) -> dict[str, Any]:
    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        return {"available": False, "reason": "missing-tmdb-credential"}
    try:
        proc = subprocess.run(
            [
                "node",
                str(PROBE),
                str(provider_path),
                json.dumps(fixture, ensure_ascii=False, separators=(",", ":")),
                "{}",
            ],
            cwd=ROOT,
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=max(15, min(int(timeout), 90)),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"available": False, "reason": "nuvio-probe-timeout"}
    value = parse_nuvio_probe(proc.stdout)
    if not isinstance(value, dict):
        return {
            "available": False,
            "reason": "invalid-nuvio-probe-output",
            "exitCode": int(proc.returncode),
        }
    debug = value.get("debug") if isinstance(value.get("debug"), dict) else {}
    return {
        "available": True,
        "providerRequestCount": max(0, int(debug.get("provider_fetch_count") or 0)),
        "fetchCount": max(0, int(debug.get("fetch_count") or 0)),
        "debugStage": str(debug.get("stage") or "")[:100],
        "rawStreams": max(0, int(value.get("raw_stream_count") or 0)),
        "playableStreams": max(0, int(value.get("playable_stream_count") or 0)),
        "identityContradictions": max(0, int(value.get("identity_contradiction_count") or 0)),
        "exitCode": int(proc.returncode),
    }


def audit(
    *,
    stage: Path,
    registry: dict[str, Any],
    health: dict[str, Any],
    timeout: int = 55,
) -> dict[str, Any]:
    candidates = candidate_map(registry)
    rows: list[dict[str, Any]] = []
    providers: set[str] = set()

    for result in health.get("results") or []:
        if not isinstance(result, dict):
            continue
        provider = cid(result.get("canonical_id") or result.get("upstream_id"))
        key = str(result.get("key") or "")
        candidate = candidates.get(key) or candidates.get(provider)
        if not provider or not isinstance(candidate, dict):
            continue

        actual_sha, expected_sha = exact_stage_sha(stage, candidate)
        if not actual_sha or not expected_sha or actual_sha != expected_sha:
            continue
        provider_path = (stage / str(candidate.get("local_path") or "")).resolve()

        for test in result.get("tests") or []:
            if not isinstance(test, dict) or not worker_zero_request(test):
                continue
            fixture = fixture_identity(test.get("fixture"))
            if not fixture.get("tmdbId") or not fixture.get("mediaType"):
                continue
            nuvio = run_nuvio_probe(provider_path, fixture, timeout=timeout)
            differential = bool(
                nuvio.get("available") is True
                and int(nuvio.get("providerRequestCount") or 0) > 0
            )
            row = {
                "provider": provider,
                "candidateKey": key,
                "providerSha256": actual_sha,
                "fixture": fixture,
                "deepFailureClass": str(test.get("failure_class") or ""),
                "deepInvocationDiagnostics": invocation_summary(test),
                "nuvioProbe": nuvio,
                "classification": (
                    "harness-differential-worker-zero-nuvio-provider-request"
                    if differential
                    else "not-proven"
                ),
                "providerMutationAuthority": False,
                "learningProviderDebtAuthority": False,
            }
            rows.append(row)
            if differential:
                providers.add(provider)
                break

    return {
        "schemaVersion": 1,
        "providerCount": len(providers),
        "providers": sorted(providers),
        "rows": rows,
        "policy": (
            "same staged bytes + same fixture: production-like Nuvio provider request "
            "with Deep worker zero request is harness debt, never provider mutation/Learning debt"
        ),
        "publicationAuthority": False,
        "providerMutationAuthority": False,
        "proofAuthority": "harness-differential-only",
        "privateContentRetained": False,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=55)
    args = parser.parse_args()

    stage = args.stage.resolve()
    registry_path = (args.registry or (stage / "candidates.json")).resolve()
    payload = audit(
        stage=stage,
        registry=load(registry_path),
        health=load(args.health.resolve()),
        timeout=args.timeout,
    )
    write(args.output.resolve(), payload)
    print(
        "FIELD_BRAIN_HARNESS_DIFFERENTIAL "
        f"providers={payload['providerCount']} "
        f"ids={','.join(payload['providers']) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
