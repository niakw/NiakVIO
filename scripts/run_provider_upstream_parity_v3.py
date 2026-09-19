#!/usr/bin/env python3
"""Rotating upstream-vs-NiakVIO parity for the active Hub-46 campaign.

A title is a catalogue sample, never a provider-health verdict. For each declared
semantic lane this harness rotates through the recent global pool and stops early
as soon as it gets useful positive evidence. Clean zero/zero samples are reported
as catalogue misses and never promoted to repair regressions.

A returned HTTP URL is *not* media proof. Many upstream providers return HTML
player pages (Sibnet shell.php, Sendvid/Uqload embeds, etc.) as if they were
streams. V3 therefore performs a tiny bounded terminal probe on every candidate
and counts it positive only when the response is demonstrably media: HLS, a
video/audio content type, an MP4 signature, or an MPEG-TS segment. This keeps the
regression ledger fail-closed and prevents player-page false positives.

The only certain NiakVIO regression class is ``upstream_ok_niakvio_ko``: the
reference upstream returned terminal-verified media for the exact same work/lane
while the local provider did not. The diagnostic reserve can span the complete
32-title global lane, but it remains adaptive: it never consumes the remaining
candidates after a useful positive/negative parity proof has been obtained.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import run_provider_upstream_parity as parity
import run_provider_upstream_parity_v2 as parity_v2
from rotating_corpus import default_seed, select_fixtures
from parity_hls_terminal_probe import verify_hls_terminal

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "automation/evidence/hub-lab-matrix-46.json"
DEFAULT_OUT = ROOT / "automation/provider-upstream-parity-v3.json"
LANES = ("movie", "tv", "anime")
MAX_SAMPLES_PER_LANE = 32
PROBE_BYTES = 4096
MAX_TERMINAL_CANDIDATES = 4
DEFAULT_PROBE_TIMEOUT = 12
MIN_TERMINAL_VOD_SECONDS = 60


def cid(value: object) -> str:
    return parity.cid(value)


def scope_ids(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = {
        cid(row.get("manifestId") or row.get("provider"))
        for row in rows if isinstance(row, dict)
        if cid(row.get("manifestId") or row.get("provider"))
    }
    expected = int(data.get("hubCount") or data.get("providerCount") or len(ids))
    if not ids or len(ids) != expected:
        raise SystemExit(f"parity scope invalid: ids={len(ids)} expected={expected} path={path}")
    return ids


def canonical_lanes(local_row: dict[str, Any], upstream_row: dict[str, Any]) -> list[str]:
    local = parity.semantic_types(local_row)
    upstream = parity.semantic_types(upstream_row)
    chosen = [lane for lane in LANES if lane in local]
    if not chosen:
        chosen = [lane for lane in LANES if lane in upstream]
    return chosen or ["movie"]


def fixture_payload(row: dict[str, Any], lane: str, *, upstream: bool) -> dict[str, Any]:
    fixture = {
        key: value for key, value in row.items()
        if key not in {"slug", "lane"}
    }
    fixture["mediaType"] = lane
    if lane == "anime":
        fixture["category"] = "anime"
        if upstream:
            fixture["mediaType"] = "tv"
            fixture["type"] = "tv"
            fixture.pop("category", None)
    return fixture


def _worker_raw(path: Path, fixture: dict[str, Any], timeout: int) -> dict[str, Any]:
    """Run the hardened worker while retaining stream candidates in memory.

    URLs are never copied into the persisted parity report. They exist only long
    enough to perform the bounded terminal media probe below.
    """
    cmd = [
        "node",
        str(parity.WORKER),
        str(path),
        json.dumps(fixture, separators=(",", ":")),
        json.dumps(parity.context_for(fixture), separators=(",", ":")),
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stream_count": 0, "timeout": True, "error_class": "timeout", "streams": []}

    result: dict[str, Any] | None = None
    for line in completed.stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            try:
                value = json.loads(line.split("=", 1)[1])
                if isinstance(value, dict):
                    result = value
            except json.JSONDecodeError:
                pass
    if not isinstance(result, dict):
        return {"ok": False, "stream_count": 0, "timeout": False, "error_class": "worker_no_result", "streams": []}
    return result


def _safe_headers(value: object) -> dict[str, str]:
    headers: dict[str, str] = {}
    if isinstance(value, dict):
        for raw_key, raw_value in list(value.items())[:30]:
            key = str(raw_key or "").strip()
            if not key or raw_value is None:
                continue
            # Transport-controlled headers are intentionally not inherited.
            if key.casefold() in {"host", "content-length", "connection", "transfer-encoding", "cookie"}:
                continue
            headers[key] = str(raw_value)[:2000]
    headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    )
    headers.setdefault("Accept", "*/*")
    headers.setdefault("Accept-Language", "en-US,en;q=0.8")
    headers["Range"] = f"bytes=0-{PROBE_BYTES - 1}"
    return headers


def _media_kind(url: str, content_type: str, body: bytes) -> str | None:
    ctype = str(content_type or "").split(";", 1)[0].strip().casefold()
    lower_url = str(url or "").casefold()
    sample = body[:PROBE_BYTES]
    text_head = sample.lstrip()[:64].upper()

    if b"#EXTM3U" in sample[:PROBE_BYTES].upper():
        return "hls"
    if ctype in {
        "application/vnd.apple.mpegurl",
        "application/x-mpegurl",
        "audio/mpegurl",
        "audio/x-mpegurl",
    }:
        return "hls"
    if ctype.startswith("video/"):
        return "video"
    if ctype.startswith("audio/") and not ctype.startswith("audio/mpegurl"):
        return "audio"
    if b"ftyp" in sample[:128]:
        return "mp4"
    # MPEG-TS packets start with 0x47 every 188 bytes. Two sync bytes are enough
    # for this tiny diagnostic range; it is deliberately conservative.
    if len(sample) >= 189 and sample[0] == 0x47 and sample[188] == 0x47:
        return "mpegts"
    # Extension alone is never sufficient for HLS: a WAF can return HTML under
    # a .m3u8 URL. For direct MP4, accept extension only with a non-text body.
    if urllib.parse.urlsplit(lower_url).path.endswith(".mp4") and ctype and not ctype.startswith("text/"):
        return "mp4"
    if text_head.startswith(b"<HTML") or text_head.startswith(b"<!DOCTYPE"):
        return None
    return None


def _short_finite_hls_seconds(body: bytes) -> float | None:
    """Return a conclusive short finite media-playlist duration, otherwise None.

    The probe body is intentionally bounded. Therefore duration is authoritative
    only when ENDLIST is present in the sampled body, proving that the complete
    finite playlist fit inside the sample. Master playlists are never judged by
    EXTINF duration here.
    """
    # PARITY_SHORT_FINITE_VOD_V1
    try:
        text = body.decode("utf-8", errors="replace").lstrip("\ufeffï»¿")
    except Exception:
        return None
    upper = text.upper()
    if "#EXTM3U" not in upper or "#EXT-X-ENDLIST" not in upper:
        return None
    if "#EXT-X-STREAM-INF" in upper:
        return None
    durations: list[float] = []
    for line in text.splitlines():
        value = line.strip()
        if not value.upper().startswith("#EXTINF:"):
            continue
        try:
            duration = float(value.split(":", 1)[1].split(",", 1)[0].strip())
        except (TypeError, ValueError):
            continue
        if duration >= 0:
            durations.append(duration)
    if not durations:
        return None
    total = float(sum(durations))
    if 0 < total < MIN_TERMINAL_VOD_SECONDS:
        return round(total, 3)
    return None


def _probe_terminal(stream: dict[str, Any], timeout: int) -> dict[str, Any]:
    url = str(stream.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"verified": False, "kind": None, "status": None, "reason": "invalid_url"}

    request = urllib.request.Request(url, headers=_safe_headers(stream.get("headers")), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=max(3, min(DEFAULT_PROBE_TIMEOUT, timeout))) as response:
            status = int(response.getcode() or 0)
            final_url = str(response.geturl() or url)
            content_type = str(response.headers.get("content-type") or "")
            body = response.read(PROBE_BYTES)
        kind = _media_kind(final_url, content_type, body)
        if kind == "hls":
            # PARITY_DEEP_HLS_TERMINAL_V2
            proof = verify_hls_terminal(
                body,
                final_url,
                _safe_headers(stream.get("headers")),
                timeout,
                min_vod_seconds=MIN_TERMINAL_VOD_SECONDS,
            )
            if not isinstance(proof.get("status"), int):
                proof["status"] = status
            return proof
        return {
            "verified": bool(kind and 200 <= status < 400),
            "kind": kind,
            "status": status,
            "reason": "media" if kind else "non_media_response",
        }
    except urllib.error.HTTPError as exc:
        return {"verified": False, "kind": None, "status": int(exc.code), "reason": "http_error"}
    except Exception as exc:
        return {"verified": False, "kind": None, "status": None, "reason": type(exc).__name__[:80]}


def _run_verified(path: Path, fixture: dict[str, Any], timeout: int) -> dict[str, Any]:
    raw = _worker_raw(path, fixture, timeout)
    if raw.get("timeout"):
        return {"ok": False, "stream_count": 0, "candidate_stream_count": 0, "raw_stream_count": 0, "timeout": True, "error_class": "timeout"}

    candidates = [row for row in raw.get("streams") or [] if isinstance(row, dict)]
    terminal_rows: list[dict[str, Any]] = []
    for stream in candidates[:MAX_TERMINAL_CANDIDATES]:
        terminal_rows.append(_probe_terminal(stream, timeout))
        if terminal_rows[-1].get("verified"):
            # One terminal-verified media candidate is sufficient for parity.
            break

    verified = [row for row in terminal_rows if row.get("verified")]
    error_details = raw.get("error_details") if isinstance(raw.get("error_details"), dict) else {}
    return {
        "ok": bool(raw.get("ok")),
        "stream_count": len(verified),
        "candidate_stream_count": int(raw.get("stream_count") or 0),
        "raw_stream_count": int(raw.get("raw_stream_count") or 0),
        "timeout": False,
        "server_accessible": bool(raw.get("provider_server_accessible")),
        "server_success": bool(raw.get("provider_server_successful_response")),
        "http_statuses": [
            int(value) for value in raw.get("provider_server_http_statuses") or []
            if isinstance(value, int)
        ][:12],
        "terminal_verified": bool(verified),
        "terminal_kinds": sorted({str(row.get("kind")) for row in verified if row.get("kind")}),
        "terminal_statuses": sorted({int(row["status"]) for row in terminal_rows if isinstance(row.get("status"), int)}),
        "terminal_reasons": sorted({str(row.get("reason")) for row in terminal_rows if row.get("reason")}),
        "terminal_short_vod_seconds": sorted({float(row["short_vod_seconds"]) for row in terminal_rows if isinstance(row.get("short_vod_seconds"), (int, float))}),
        "terminal_media_duration_seconds": sorted({float(row["media_duration_seconds"]) for row in terminal_rows if isinstance(row.get("media_duration_seconds"), (int, float))}),
        "error_class": str(error_details.get("code") or error_details.get("name") or "")[:120] or None,
    }


def technical(result: dict[str, Any]) -> bool:
    if result.get("timeout"):
        return True
    if str(result.get("error_class") or "").strip():
        return True
    statuses = [int(value) for value in result.get("http_statuses") or []]
    return bool(statuses) and not any(200 <= status < 400 for status in statuses)


def classify_pair(upstream: dict[str, Any], local: dict[str, Any]) -> str:
    up = int(upstream.get("stream_count") or 0) > 0
    lo = int(local.get("stream_count") or 0) > 0
    if up and lo:
        return "both_ok"
    if up and not lo:
        return "upstream_ok_niakvio_ko"
    if not up and lo:
        return "niakvio_ok_upstream_ko"

    # A provider returning player/embed candidates without terminal media proof
    # is not a positive upstream authority and therefore cannot create a certain
    # NiakVIO regression.
    up_candidates = int(upstream.get("candidate_stream_count") or 0) > 0
    lo_candidates = int(local.get("candidate_stream_count") or 0) > 0
    if up_candidates and not up:
        return "upstream_candidate_unverified"
    if lo_candidates and not lo:
        return "niakvio_candidate_unverified"

    up_technical = technical(upstream)
    lo_technical = technical(local)
    if not up_technical and not lo_technical:
        return "catalog_miss_both"
    if lo_technical and not up_technical:
        return "niakvio_technical_upstream_no_stream"
    if up_technical and not lo_technical:
        return "upstream_technical_niakvio_no_stream"
    return "both_technical"


def run_lane(
    provider_id: str,
    lane: str,
    local_path: Path,
    upstream_path: Path,
    *,
    timeout: int,
    sample_count: int,
    seed: str,
) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    candidates = select_fixtures(
        lane,
        count=sample_count,
        seed=seed,
        provider=provider_id,
    )
    for candidate in candidates:
        up_fixture = fixture_payload(candidate, lane, upstream=True)
        local_fixture = fixture_payload(candidate, lane, upstream=False)
        # Never give the upstream a systematic first-request advantage. Some
        # services are cold-start/rate-limit sensitive (PersianStremio is a
        # proven example: identical requests alternated 200/503). Pick the first
        # order deterministically per sample, then reverse-confirm every
        # asymmetric positive before it can become a certain regression.
        identity = f"{provider_id}:{lane}:{candidate['slug']}"
        local_first = bool(hashlib.sha256(identity.encode("utf-8")).digest()[0] & 1)

        def ordered_pair(first_local: bool) -> tuple[dict[str, Any], dict[str, Any]]:
            if first_local:
                local_result = _run_verified(local_path, local_fixture, timeout)
                upstream_result = _run_verified(upstream_path, up_fixture, timeout)
            else:
                upstream_result = _run_verified(upstream_path, up_fixture, timeout)
                local_result = _run_verified(local_path, local_fixture, timeout)
            return upstream_result, local_result

        upstream, local = ordered_pair(local_first)
        classification = classify_pair(upstream, local)
        confirmation = None
        confirmation_classification = None

        if classification in {"upstream_ok_niakvio_ko", "niakvio_ok_upstream_ko"}:
            upstream_confirm, local_confirm = ordered_pair(not local_first)
            confirmation_classification = classify_pair(upstream_confirm, local_confirm)
            confirmation = {
                "executionOrder": "upstream_first" if local_first else "niakvio_first",
                "classification": confirmation_classification,
                "upstream": upstream_confirm,
                "niakvio": local_confirm,
            }
            upstream_positive_count = sum(
                int(row.get("stream_count") or 0) > 0 for row in (upstream, upstream_confirm)
            )
            local_positive_count = sum(
                int(row.get("stream_count") or 0) > 0 for row in (local, local_confirm)
            )
            if upstream_positive_count and local_positive_count:
                classification = "both_ok_flaky"
            elif upstream_positive_count == 2 and local_positive_count == 0:
                classification = "upstream_ok_niakvio_ko"
            elif local_positive_count and upstream_positive_count == 0:
                classification = "niakvio_ok_upstream_ko"
            elif upstream_positive_count and local_positive_count == 0:
                classification = "upstream_advantage_unconfirmed"
            else:
                classification = "order_sensitive_resample"

        sample = {
            "fixture": candidate["slug"],
            "tmdbId": str(candidate.get("tmdbId") or ""),
            "executionOrder": "niakvio_first" if local_first else "upstream_first",
            "classification": classification,
            "upstream": upstream,
            "niakvio": local,
        }
        if confirmation is not None:
            sample["confirmation"] = confirmation
            sample["confirmationClassification"] = confirmation_classification
        samples.append(sample)
        if classification in {
            "both_ok",
            "upstream_ok_niakvio_ko",
            "niakvio_ok_upstream_ko",
        }:
            break

    classes = [str(row.get("classification") or "") for row in samples]
    if "upstream_ok_niakvio_ko" in classes:
        status = "REGRESSION"
    elif any(value in {"both_ok", "both_ok_flaky", "niakvio_ok_upstream_ko"} for value in classes):
        status = "POSITIVE"
    elif classes and all(value in {
        "catalog_miss_both",
        "upstream_candidate_unverified",
        "niakvio_candidate_unverified",
        "upstream_advantage_unconfirmed",
        "order_sensitive_resample",
    } for value in classes):
        status = "RESAMPLE"
    else:
        status = "TECHNICAL_UNRESOLVED"
    return {
        "lane": lane,
        "status": status,
        "samples": samples,
        "sampleCount": len(samples),
        "candidateCount": len(candidates),
    }


def run_local_only_lane(
    provider_id: str,
    lane: str,
    local_path: Path,
    *,
    timeout: int,
    sample_count: int,
    seed: str,
) -> dict[str, Any]:
    # PARITY_LOCAL_ONLY_UNMATCHED_V1
    samples: list[dict[str, Any]] = []
    candidates = select_fixtures(
        lane,
        count=sample_count,
        seed=seed,
        provider=provider_id,
    )
    for candidate in candidates:
        local = _run_verified(local_path, fixture_payload(candidate, lane, upstream=False), timeout)
        positive = int(local.get("stream_count") or 0) > 0 and bool(local.get("terminal_verified"))
        samples.append({
            "fixture": candidate["slug"],
            "tmdbId": str(candidate.get("tmdbId") or ""),
            "classification": "local_terminal_positive" if positive else (
                "local_technical_unresolved" if technical(local) else (
                    "local_candidate_unverified" if int(local.get("candidate_stream_count") or 0) > 0 else "local_catalog_miss"
                )
            ),
            "niakvio": local,
        })
        if positive:
            break
    if any(row["classification"] == "local_terminal_positive" for row in samples):
        status = "POSITIVE"
    elif samples and all(row["classification"] in {"local_catalog_miss", "local_candidate_unverified"} for row in samples):
        status = "RESAMPLE"
    else:
        status = "TECHNICAL_UNRESOLVED"
    return {
        "lane": lane,
        "status": status,
        "samples": samples,
        "sampleCount": len(samples),
        "candidateCount": len(candidates),
    }


def one_unmatched_provider(
    provider_id: str,
    local: dict[str, Any],
    *,
    timeout: int,
    sample_count: int,
    seed: str,
) -> dict[str, Any]:
    lanes = canonical_lanes(local["entry"], {})
    lane_rows = [
        run_local_only_lane(
            provider_id, lane, local["path"],
            timeout=timeout, sample_count=sample_count, seed=seed,
        )
        for lane in lanes
    ]
    states = [row["status"] for row in lane_rows]
    if states and all(value == "POSITIVE" for value in states):
        status = "UNMATCHED_FULL"
    elif "POSITIVE" in states:
        status = "UNMATCHED_PARTIAL"
    elif states and all(value == "RESAMPLE" for value in states):
        status = "UNMATCHED_RESAMPLE"
    else:
        status = "UNMATCHED_ZERO"
    return {
        "providerId": provider_id,
        "upstreamSource": None,
        "comparisonMode": "local-only-no-upstream",
        "status": status,
        "lanes": lane_rows,
    }


def one_provider(
    provider_id: str,
    local: dict[str, Any],
    upstream: dict[str, Any],
    upstream_path: Path,
    *,
    timeout: int,
    sample_count: int,
    seed: str,
) -> dict[str, Any]:
    lanes = canonical_lanes(local["entry"], upstream["entry"])
    lane_rows = [
        run_lane(
            provider_id,
            lane,
            local["path"],
            upstream_path,
            timeout=timeout,
            sample_count=sample_count,
            seed=seed,
        )
        for lane in lanes
    ]
    lane_states = [row["status"] for row in lane_rows]
    if "REGRESSION" in lane_states:
        status = "REGRESSION"
    elif lane_states and all(value == "POSITIVE" for value in lane_states):
        status = "FULL"
    elif "POSITIVE" in lane_states:
        unresolved = [value for value in lane_states if value != "POSITIVE"]
        status = "RESAMPLE" if unresolved and all(value == "RESAMPLE" for value in unresolved) else "PARTIAL"
    elif lane_states and all(value == "RESAMPLE" for value in lane_states):
        status = "RESAMPLE"
    else:
        status = "ZERO"
    return {
        "providerId": provider_id,
        "upstreamSource": upstream["source"],
        "status": status,
        "lanes": lane_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("NIAKVIO_PARITY_WORKERS", "8")))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("NIAKVIO_PARITY_TIMEOUT", "25")))
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--samples-per-lane", type=int, default=int(os.environ.get("NIAKVIO_PARITY_SAMPLES_PER_LANE", "3")))
    parser.add_argument(
        "--scope-matrix",
        type=Path,
        default=Path(os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", str(DEFAULT_SCOPE))),
    )
    parser.add_argument("--seed", default=None)
    args = parser.parse_args()

    scope_path = args.scope_matrix
    if not scope_path.is_absolute():
        scope_path = ROOT / scope_path
    scoped = scope_ids(scope_path)
    local_all = parity.local_catalog()
    local = {pid: row for pid, row in local_all.items() if pid in scoped}
    missing_local = sorted(scoped - set(local))
    if missing_local or len(local) != len(scoped):
        raise SystemExit(
            f"Hub-46 parity local scope mismatch local={len(local)} expected={len(scoped)} missing={','.join(missing_local)}"
        )

    upstreams, source_errors = parity_v2.upstream_catalog()
    requested = {cid(value) for value in args.provider if cid(value)}
    accounting_scope = [pid for pid in sorted(local) if not requested or pid in requested]
    provider_ids = [
        pid for pid in accounting_scope
        if pid in upstreams
    ]
    missing_upstream = sorted(
        pid for pid in accounting_scope
        if pid not in upstreams
    )
    seed = str(args.seed if args.seed is not None else default_seed())
    sample_count = max(1, min(MAX_SAMPLES_PER_LANE, int(args.samples_per_lane)))
    rows: list[dict[str, Any]] = []
    download_errors: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="niakvio-upstream-parity-v3-") as tmp_name:
        tmp = Path(tmp_name)
        tasks = []
        for provider_id in provider_ids:
            upstream = upstreams[provider_id]
            try:
                data = parity.get_bytes(upstream["url"])
                path = tmp / f"{provider_id}.js"
                path.write_bytes(data)
            except Exception as exc:
                download_errors.append({
                    "providerId": provider_id,
                    "source": upstream["source"],
                    "error": str(exc)[:240],
                })
                continue
            tasks.append((provider_id, local[provider_id], upstream, path))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(16, args.workers))) as pool:
            future_map = {
                pool.submit(
                    one_provider,
                    provider_id,
                    local_row,
                    upstream,
                    path,
                    timeout=max(5, args.timeout),
                    sample_count=sample_count,
                    seed=seed,
                ): provider_id
                for provider_id, local_row, upstream, path in tasks
            }
            for future in concurrent.futures.as_completed(future_map):
                provider_id = future_map[future]
                try:
                    rows.append(future.result())
                except Exception as exc:
                    rows.append({
                        "providerId": provider_id,
                        "status": "HARNESS_ERROR",
                        "error": f"{type(exc).__name__}: {exc}"[:240],
                        "lanes": [],
                    })

    # Every selected provider must have an auditable row. Providers without an
    # upstream authority are evaluated locally instead of disappearing from the
    # status denominator (Kehflix exposed this blind spot).
    for provider_id in missing_upstream:
        try:
            rows.append(one_unmatched_provider(
                provider_id,
                local[provider_id],
                timeout=max(5, args.timeout),
                sample_count=sample_count,
                seed=seed,
            ))
        except Exception as exc:
            rows.append({
                "providerId": provider_id,
                "upstreamSource": None,
                "comparisonMode": "local-only-no-upstream",
                "status": "HARNESS_ERROR",
                "error": f"{type(exc).__name__}: {exc}"[:240],
                "lanes": [],
            })

    rows.sort(key=lambda row: str(row.get("providerId") or ""))
    counts = Counter(str(row.get("status") or "UNKNOWN") for row in rows)
    regressions = [row["providerId"] for row in rows if row.get("status") == "REGRESSION"]
    resample = [row["providerId"] for row in rows if row.get("status") == "RESAMPLE"]
    payload = {
        "schemaVersion": 4,
        "method": "rotating-hub46-upstream-parity-terminal-verified",
        "terminalMediaRequired": True,
        "scopeProviderCount": len(scoped),
        "selectedProviderCount": len(accounting_scope),
        "matchedUpstreamProviders": len(provider_ids),
        "testedProviders": len(rows),
        "accountedProviders": len(rows),
        "localOnlyProviders": len(missing_upstream),
        "allSelectedProvidersAccounted": len(rows) == len(accounting_scope),
        "allScopedProvidersAccounted": (not requested) and len(rows) == len(scoped),
        "samplesPerLane": sample_count,
        "seed": seed,
        "statusCounts": dict(sorted(counts.items())),
        "certainRegressions": regressions,
        "resampleProviders": resample,
        "missingUpstreamProviders": missing_upstream,
        "upstreamManifestErrors": source_errors,
        "providerDownloadErrors": download_errors,
        "providers": rows,
    }
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "PROVIDER_UPSTREAM_PARITY_V3 "
        + " ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    )
    print(
        "PROVIDER_UPSTREAM_PARITY_V3_COVERAGE "
        f"scope={len(scoped)} selected={len(accounting_scope)} matched={len(provider_ids)} "
        f"accounted={len(rows)} tested={len(rows)} missing_upstream={len(missing_upstream)} "
        f"local_only={len(missing_upstream)} downloads_failed={len(download_errors)} samples_per_lane={sample_count}"
    )
    print("PROVIDER_UPSTREAM_PARITY_V3_REGRESSIONS " + (",".join(regressions) if regressions else "none"))
    print("PROVIDER_UPSTREAM_PARITY_V3_RESAMPLE " + (",".join(resample) if resample else "none"))
    if len(rows) != len(accounting_scope):
        raise SystemExit(
            f"Provider parity accounting failure accounted={len(rows)} expected={len(accounting_scope)}"
        )
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
