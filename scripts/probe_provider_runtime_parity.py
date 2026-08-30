#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def committed_manifest() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "show", "HEAD:manifest.json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise SystemExit("committed manifest is not an object")
    return value


def committed_provider_path(provider_id: str) -> str:
    manifest = committed_manifest()
    for row in manifest.get("scrapers") or []:
        if isinstance(row, dict) and str(row.get("id") or "").casefold() == provider_id.casefold():
            path = str(row.get("filename") or "").strip()
            if path:
                return path
    return ""


def staged_base_path(provider_id: str) -> Path:
    prefix = f"{provider_id.casefold()}--base--"
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", "provider-bases"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    changed: list[Path] = []
    for line in proc.stdout.splitlines():
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        path = ROOT / raw
        if path.name.casefold().startswith(prefix) and path.suffix == ".js" and path.is_file():
            changed.append(path)
    if changed:
        return max(changed, key=lambda path: path.stat().st_mtime_ns)
    candidates = [
        path for path in (ROOT / "provider-bases").glob(f"{provider_id}--base--*.js")
        if path.is_file()
    ]
    if not candidates:
        raise SystemExit(f"no ProviderBase found for {provider_id}")
    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def materialize_committed(path: str, output: Path) -> Path:
    if not path:
        raise SystemExit("committed provider path missing")
    proc = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(proc.stdout)
    return output


def worker_result(provider_path: Path, fixture: dict[str, Any], profile: str) -> dict[str, Any]:
    profiles = {
        "control": {
            "platform": "android",
            "userAgent": "Mozilla/5.0 (Linux; Android 14; Nuvio) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "injectAcceptLanguage": True,
            "languages": ["fr-FR", "fr", "en-US", "en"],
            "maxFetches": 30,
        },
        "onboarding_tv": {
            "platform": "android-tv",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "injectAcceptLanguage": False,
            "languages": ["fr-FR", "fr"],
            "maxFetches": 18,
        },
        "onboarding_compose": {
            "platform": "macos",
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "injectAcceptLanguage": False,
            "languages": ["fr-FR", "fr"],
            "maxFetches": 18,
        },
    }
    selected = profiles[profile]
    context = {
        "fixtureMetadata": fixture,
        "locale": "fr-FR",
        "languages": selected["languages"],
        "platform": selected["platform"],
        "userAgent": selected["userAgent"],
        "injectAcceptLanguage": selected["injectAcceptLanguage"],
        # Deterministic fixture metadata without requiring repository secrets.
        "tmdbApiKey": "niakvio-fixture",
        "maxSettingsProfiles": 1,
        "networkLimits": {
            "maxFetches": selected["maxFetches"],
            "maxResponseBytes": 5 * 1024 * 1024,
            "maxTotalResponseBytes": 20 * 1024 * 1024,
            "maxDistinctHosts": 12 if profile != "control" else 20,
            "maxRedirects": 4 if profile != "control" else 5,
        },
    }
    proc = subprocess.run(
        [
            "node",
            str(ROOT / "scripts/provider_worker.cjs"),
            str(provider_path),
            json.dumps(fixture, separators=(",", ":")),
            json.dumps(context, separators=(",", ":")),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=55,
        check=False,
    )
    result: dict[str, Any] | None = None
    for line in proc.stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            raw = line.split("=", 1)[1]
            candidate = json.loads(raw)
            if isinstance(candidate, dict):
                result = candidate
    if result is None:
        result = {
            "ok": False,
            "stream_count": 0,
            "error_details": {"code": "missing_worker_result"},
            "network_observations": [],
        }
    sanitized = sanitize(result, proc.returncode)
    sanitized["profile"] = profile
    return sanitized


def sanitize(result: dict[str, Any], exit_code: int) -> dict[str, Any]:
    observations = []
    for row in result.get("network_observations") or []:
        if not isinstance(row, dict):
            continue
        observations.append({
            "stage": row.get("stage"),
            "host": row.get("host"),
            "method": row.get("method"),
            "path_pattern": row.get("path_pattern"),
            "status": row.get("status"),
            "ok": row.get("ok"),
            "error_code": row.get("error_code"),
        })
    error = result.get("error_details") if isinstance(result.get("error_details"), dict) else {}
    return {
        "ok": bool(result.get("ok")),
        "worker_exit_code": exit_code,
        "stream_count": int(result.get("stream_count") or 0),
        "disallowed_stream_count": int(result.get("disallowed_stream_count") or 0),
        "disallowed_reasons": [
            str(value)[:120] for value in (result.get("disallowed_reasons") or [])[:10]
        ],
        "error_code": str(error.get("code") or "")[:120] or None,
        "provider_server_accessible": bool(result.get("provider_server_accessible")),
        "provider_server_successful_response": bool(result.get("provider_server_successful_response")),
        "provider_server_hosts": [
            str(value)[:160] for value in (result.get("provider_server_hosts") or [])[:20]
        ],
        "provider_server_http_statuses": [
            int(value) for value in (result.get("provider_server_http_statuses") or [])
            if isinstance(value, int)
        ][:20],
        "network_observations": observations[:80],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    current = load_json(Path(args.current))
    provider_id = str(current.get("id") or "").strip()
    fixture = current.get("fixture") if isinstance(current.get("fixture"), dict) else {}
    if not provider_id or not fixture:
        raise SystemExit("runtime parity probe requires provider id and fixture")

    work = ROOT / ".provider-onboarding" / "runtime-parity"
    base = staged_base_path(provider_id)
    published_rel = committed_provider_path(provider_id)
    published = materialize_committed(published_rel, work / "published.js")

    report = {
        "schema_version": 1,
        "provider_id": provider_id,
        "fixture": {
            "tmdbId": str(fixture.get("tmdbId") or ""),
            "mediaType": str(fixture.get("mediaType") or ""),
            "title": str(fixture.get("title") or ""),
            "season": fixture.get("season"),
            "episode": fixture.get("episode"),
        },
        "base": {
            profile: worker_result(base, fixture, profile)
            for profile in ("control", "onboarding_tv", "onboarding_compose")
        },
        "published": {
            profile: worker_result(published, fixture, profile)
            for profile in ("control", "onboarding_tv", "onboarding_compose")
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_RUNTIME_PARITY "
        f"id={provider_id} "
        f"base_control={report['base']['control']['stream_count']} "
        f"base_tv={report['base']['onboarding_tv']['stream_count']} "
        f"base_compose={report['base']['onboarding_compose']['stream_count']} "
        f"published_control={report['published']['control']['stream_count']} "
        f"published_tv={report['published']['onboarding_tv']['stream_count']} "
        f"published_compose={report['published']['onboarding_compose']['stream_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
