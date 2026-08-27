#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

EXTINF = re.compile(r"^#EXTINF:([0-9.]+)", re.I)
STREAM_INF = re.compile(r"^#EXT-X-STREAM-INF", re.I)
MINUTES = re.compile(r"\b(\d{1,3})\s*min(?:ute)?s?\b", re.I)


def fetch_text(url: str, headers: dict[str, str]) -> tuple[str, str]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read(2_000_000).decode("utf-8", "replace").lstrip("\ufeff\ufeff\ufeff \t\r\n")
        return body, response.geturl()


def media_playlist(url: str, headers: dict[str, str], depth: int = 0) -> tuple[str, str]:
    if depth > 2:
        raise RuntimeError("nested HLS master depth exceeded")
    text, final_url = fetch_text(url, headers)
    if not text.startswith("#EXTM3U"):
        raise RuntimeError("not an HLS playlist")
    lines = [line.strip() for line in text.splitlines()]
    if any(STREAM_INF.match(line) for line in lines):
        for index, line in enumerate(lines):
            if not STREAM_INF.match(line):
                continue
            for child in lines[index + 1:]:
                if not child or child.startswith("#"):
                    continue
                return media_playlist(urljoin(final_url, child), headers, depth + 1)
        raise RuntimeError("HLS master has no variant URI")
    return text, final_url


def duration_seconds(text: str) -> float | None:
    total = 0.0
    count = 0
    for raw in text.splitlines():
        match = EXTINF.match(raw.strip())
        if not match:
            continue
        total += float(match.group(1))
        count += 1
    return total if count else None


def expected_from_row(row: dict) -> int | None:
    blob = " ".join(str(row.get(key) or "") for key in ("name", "title", "description"))
    values = [int(match.group(1)) for match in MINUTES.finditer(blob)]
    return max(values) * 60 if values else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("probe_json")
    parser.add_argument("--tolerance", type=float, default=0.35)
    parser.add_argument("--require-expected", action="store_true")
    args = parser.parse_args()
    payload = json.loads(Path(args.probe_json).read_text(encoding="utf-8"))
    findings = []
    failures = []
    for index, item in enumerate(payload.get("streams") or []):
        if not isinstance(item, dict):
            continue
        row = item.get("row") if isinstance(item.get("row"), dict) else {}
        media = item.get("media") if isinstance(item.get("media"), dict) else {}
        if not media.get("playable") or media.get("kind") != "hls":
            continue
        expected = expected_from_row(row)
        if expected is None:
            if args.require_expected:
                failures.append({"index": index, "reason": "expected_duration_missing"})
            continue
        headers = {str(k): str(v) for k, v in (row.get("headers") or {}).items()} if isinstance(row.get("headers"), dict) else {}
        headers.setdefault("User-Agent", "Mozilla/5.0 (Linux; Android 14; Android TV) NuvioTV")
        headers.setdefault("Accept", "*/*")
        try:
            playlist, final_url = media_playlist(str(row.get("url") or ""), headers)
            actual = duration_seconds(playlist)
        except Exception as exc:
            findings.append({"index": index, "expected_seconds": expected, "actual_seconds": None, "error": str(exc)})
            continue
        ratio = (actual / expected) if actual else None
        ok = ratio is not None and (1.0 - args.tolerance) <= ratio <= (1.0 + args.tolerance)
        finding = {
            "index": index,
            "expected_seconds": expected,
            "actual_seconds": round(actual, 3) if actual is not None else None,
            "ratio": round(ratio, 4) if ratio is not None else None,
            "ok": ok,
            "playlist_host": urlparse(final_url).hostname,
        }
        findings.append(finding)
        if not ok:
            failures.append(finding)
    result = {"findings": findings, "failures": failures, "ok": not failures}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 3


if __name__ == "__main__":
    raise SystemExit(main())
