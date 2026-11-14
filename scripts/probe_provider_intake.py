#!/usr/bin/env python3
"""Read-only fast intake: probe pinned Nuvio upstream scripts without publication.

Evidence levels: source syntax -> sandbox candidate -> terminal media probe.
A terminal media response is NOT verified content identity, client playback,
1080p/4K quality, or authorization to enable a provider. Only the NiakVIO
Provider v3 onboarding/Brain/native acceptance may promote sources.

No stream URL, token, header value or downloaded JavaScript enters the report.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rotating_corpus import select_fixtures  # noqa: E402
import run_provider_upstream_parity_v3 as parity3  # noqa: E402

INPUT = ROOT / "automation/provider-intake-top-global-france.json"
OUTPUT = ROOT / "automation/provider-intake-probe-result.json"
ALLOWED_REPOS = {
    "NuvioPlugin/All-in-One-Nuvio",
    "Gowaru/gowaru-nuvio-providers",
}
LANES = {"movie", "tv", "anime"}
REGIONS = {"global", "france"}


def read_candidates(path: Path) -> list[dict[str, Any]]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schemaVersion") != 1:
        raise ValueError("unsupported candidate inventory schema")
    entries = config.get("providers")
    if not isinstance(entries, list) or not entries:
        raise ValueError("candidates must be a nonempty list")
    seen: set[str] = set()
    valid: list[dict[str, Any]] = []
    for row in entries:
        if not isinstance(row, dict):
            raise ValueError("invalid candidate row")
        pid = str(row.get("id") or "").casefold().strip()
        region = str(row.get("region") or "").strip()
        lanes = row.get("lanes")
        source = row.get("source") if isinstance(row.get("source"), dict) else {}
        repository = str(source.get("repository") or "")
        ref = str(source.get("sha") or "")
        filename = str(source.get("file") or "")
        if (not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pid)
                or pid in seen or region not in REGIONS):
            raise ValueError(f"invalid / duplicate / cross-region provider ID: {pid}")
        if not isinstance(lanes, list) or not lanes or len(lanes) != len(set(lanes)) or not set(lanes) <= LANES:
            raise ValueError(f"invalid semantic lanes: {pid}")
        if repository not in ALLOWED_REPOS:
            raise ValueError(f"unknown upstream repository: {pid}")
        if not re.fullmatch(r"[a-f0-9]{40}", ref):
            raise ValueError(f"upstream commit is not immutably pinned: {pid}")
        if not re.fullmatch(r"providers/[a-z0-9][a-z0-9-]*[.]js", filename):
            raise ValueError(f"unsafe source path: {pid}")
        if filename != f"providers/{pid}.js":
            raise ValueError(f"source filename mismatches candidate ID: {pid}")
        seen.add(pid)
        valid.append(row)
    return valid


def sanitized(result: dict[str, Any]) -> dict[str, Any]:
    """Allowlist-only fields: never persist URLs, response bodies or headers."""
    return {
        "ok": bool(result.get("ok")),
        "terminalVerified": bool(result.get("terminal_verified")),
        "terminalCount": max(0, int(result.get("stream_count") or 0)),
        "candidateCount": max(0, int(result.get("candidate_stream_count") or 0)),
        "mediaKinds": [str(k)[:24] for k in result.get("terminal_kinds") or []][:6],
        "errorClass": str(result.get("error_class") or "")[:80] or None,
        "timeout": bool(result.get("timeout")),
        "serverAccessible": bool(result.get("server_accessible")),
        "serverSuccessfulResponse": bool(result.get("server_success")),
        "httpStatuses": [int(v) for v in result.get("http_statuses") or [] if isinstance(v, int)][:8],
    }


def probe_one(row: dict[str, Any], tmp: Path, samples: int, timeout: int, seed: str) -> dict[str, Any]:
    pid = str(row["id"])
    src = row["source"]
    report: dict[str, Any] = {
        "id": pid,
        "region": row["region"],
        "lanes": row["lanes"],
        "sourceRepository": src["repository"],
        "sourceSha": src["sha"],
        "inventoryRank": row["inventoryRank"],
        "classification": "unproven",
        "tasks": [],
    }
    url = f"https://raw.githubusercontent.com/{src['repository']}/{src['sha']}/{src['file']}"
    path = tmp / f"{pid}.js"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "NiakVIO-Intake-Probe/1"})
        with urllib.request.urlopen(request, timeout=20) as response:
            source = response.read(900_001)
            if len(source) > 900_000:
                raise ValueError("upstream script exceeds safe intake size")
        path.write_bytes(source)
        checked = subprocess.run(
            ["node", "--check", str(path)],
            cwd=ROOT, capture_output=True, text=True, timeout=12, check=False,
        )
        if checked.returncode != 0:
            report["classification"] = "script_syntax_error"
            return report
        report["sourceChecked"] = True
    except Exception as exc:
        report["classification"] = "source_unavailable"
        report["sourceError"] = type(exc).__name__[:90]
        return report

    positives = 0
    for lane in row["lanes"]:
        fixtures = select_fixtures(lane, count=samples, seed=seed, provider=pid)
        for sample in fixtures:
            fixture = parity3.fixture_payload(sample, lane, upstream=True)
            try:
                result = sanitized(parity3._run_verified(path, fixture, timeout))
            except Exception as exc:
                result = sanitized({"ok": False, "error_class": type(exc).__name__})
            positives += int(result["terminalVerified"])
            report["tasks"].append({
                "lane": lane,
                "fixture": str(sample.get("slug") or "")[:90],
                "result": result,
            })
    report["terminalPositiveTasks"] = positives
    reports = [x["result"] for x in report["tasks"]]
    if positives:
        report["classification"] = "terminal_media_observed_identity_unverified"
    elif any(x.get("candidateCount", 0) > 0 for x in reports):
        report["classification"] = "candidate_urls_nonterminal"
    elif any(x.get("timeout") for x in reports):
        report["classification"] = "inconclusive_timeout"
    else:
        report["classification"] = "no_terminal_media_observed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--region", choices=["all", "global", "france"], default="all")
    parser.add_argument("--samples-per-lane", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rows = read_candidates(args.input)
    selected = [x for x in rows if args.region == "all" or x["region"] == args.region]
    if not selected:
        raise SystemExit("empty regional batch")
    if args.dry_run:
        print("FIELD_PROVIDER_INTAKE_PREFLIGHT ids=" + ",".join(x["id"] for x in selected)
              + " regions=" + ",".join(sorted({x["region"] for x in selected})))
        return 0
    with tempfile.TemporaryDirectory(prefix="niakvio-intake-") as directory:
        workspace = Path(directory)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, max(1, args.max_workers))) as pool:
            pending = {
                pool.submit(
                    probe_one, row, workspace,
                    min(6, max(1, args.samples_per_lane)),
                    min(55, max(10, args.timeout)),
                    "2026-11-14-intake",
                ): row["id"]
                for row in selected
            }
            results = []
            for future in concurrent.futures.as_completed(pending):
                pid = pending[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"id": pid, "classification": "harness_error", "error": type(exc).__name__[:80]}
                results.append(result)
                print(
                    f"FIELD_PROVIDER_INTAKE id={pid} region={result.get('region', '?')} "
                    f"status={result['classification']} terminal_tasks={result.get('terminalPositiveTasks', 0)} "
                    f"total_tasks={len(result.get('tasks') or [])}",
                    flush=True,
                )
    results.sort(key=lambda x: (x.get("region") or "", x.get("id") or ""))
    counts = Counter(x["classification"] for x in results)
    document = {
        "schemaVersion": 1,
        "authority": "read-only-upstream-worker-and-terminal-probe",
        "commitPinned": True,
        "identityVerified": False,
        "nativeClientPlaybackVerified": False,
        "promotions": 0,
        "requestedRegion": args.region,
        "sampleCountPerLane": min(6, max(1, args.samples_per_lane)),
        "candidateCount": len(results),
        "statusCounts": dict(sorted(counts.items())),
        "providers": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"FIELD_PROVIDER_INTAKE_DONE providers={len(results)} "
          f"terminal_observed={counts['terminal_media_observed_identity_unverified']} "
          f"promoted=0 output={args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
