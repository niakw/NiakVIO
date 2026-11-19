#!/usr/bin/env python3
"""Parse transient Android logcat into strictly enumerated Brain diagnostics.

Do NOT save or echo raw logcat, provider console strings, signed stream URLs,
cookies, script source, headers, names or exception messages. Only the
source-pinned official native runner may produce this bounded observation.
"""
from __future__ import annotations

import argparse
import base64
import re
import sys

PHASE_PATTERNS = (
    ("call", re.compile(r"\bCalling getStreams with tmdbId=", re.I)),
    ("result", re.compile(r"\bgetStreams returned:\s*\d+\s*streams", re.I)),
    ("error", re.compile(r"\bgetStreams error\s*:", re.I)),
    ("missing_export", re.compile(r"\bgetStreams function not found\b", re.I)),
)
ERROR_KINDS = (
    ("reference_error", re.compile(r"ReferenceError|not defined", re.I)),
    ("type_error", re.compile(r"TypeError", re.I)),
    ("syntax_error", re.compile(r"SyntaxError", re.I)),
    ("timeout", re.compile(r"TimeoutError|timed out", re.I)),
    ("network_error", re.compile(r"NetworkError|Failed to fetch", re.I)),
    ("http_error", re.compile(r"\bHTTP[ _-]?(?:401|403|404|429|500|503)\b", re.I)),
)
TAG = re.compile(r"\b[VDIWEF]/Plugin:([^\s(]+)\s*\(\s*\d+\):\s*(.*)$")


def field(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", value))


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def extract_line(line: str, provider: str, fixture: str) -> dict[str, str] | None:
    match = TAG.search(line)
    if not match:
        return None
    tag, message = match.groups()
    # Tags may have the official repository UUID before the provider ID; a
    # source from a different scraper cannot be assigned to this provider.
    if normalize(provider) not in normalize(tag):
        return None
    phase = next((name for name, pattern in PHASE_PATTERNS if pattern.search(message)), "")
    if not phase:
        return None
    result = {
        "phase": phase,
        "category": "none",
        "requestType": "unknown",
        "count": "0",
        "fixture": fixture,
        "provider": provider,
    }
    if phase == "call":
        media = re.search(r"\btype=(movie|anime|tv)\b", message, re.I)
        if media:
            result["requestType"] = media.group(1).lower()
    if phase == "result":
        count = re.search(r"\bgetStreams returned:\s*(\d+)\s*streams", message, re.I)
        if count:
            result["count"] = str(min(100, int(count.group(1))))
    if phase == "error":
        result["category"] = next(
            (name for name, pattern in ERROR_KINDS if pattern.search(message)),
            "unspecified_js_exception",
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--client", choices=("tv", "mobile", "desktop"), required=True)
    args = parser.parse_args()
    provider, fixture = args.provider.casefold(), args.fixture.casefold()
    if not field(provider) or not field(fixture):
        parser.error("target provider and fixture must be canonical identifiers")
    provider64 = base64.urlsafe_b64encode(provider.encode("ascii")).decode("ascii").rstrip("=")
    count = 0
    for line in sys.stdin:
        result = extract_line(line, provider, fixture)
        if not result:
            continue
        # Format is intentionally fixed and contains only short enum/numeric
        # values. The raw message is never copied, including error stacks.
        print(
            "FIELD_NATIVE_QUICKJS_DIAGNOSTIC"
            f" client={args.client} fixture={fixture} provider64={provider64}"
            f" phase={result['phase']} category={result['category']}"
            f" request_type={result['requestType']} count={result['count']}",
            flush=True,
        )
        count += 1
        if count >= 100:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
