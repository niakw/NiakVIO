#!/usr/bin/env python3
"""Diagnose provider WAF challenges with an ordinary local Chrome session.

This is deliberately not a challenge solver:
- no stealth patching;
- no CAPTCHA/Turnstile interaction;
- no cf_clearance fabrication/export;
- no cookie/body persistence.

It answers one bounded question for CI: does normal browser navigation reach
non-challenge content where the Node fetch probe received an explicit WAF page?
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

CHALLENGE_MARKERS = (
    "just a moment",
    "checking your browser",
    "verify you are human",
    "attention required",
    "captcha",
    "challenge-platform",
    "cf-browser-verification",
    "security check",
    "turnstile",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def sanitized_url(value: object) -> str:
    raw = str(value or "").strip()
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


def extract_targets(report: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in report.get("rows") or []:
        if not isinstance(row, dict) or str(row.get("debug_stage") or "") != "provider_waf_challenge":
            continue
        provider = str(row.get("provider_id") or "").strip().casefold()
        lane = str(row.get("semantic_type") or "").strip().casefold()
        fetches = row.get("debug_fetches") if isinstance(row.get("debug_fetches"), list) else []
        challenged = [
            item for item in fetches
            if isinstance(item, dict) and str(item.get("challenge") or "").strip()
        ]
        terminal = challenged[-1] if challenged else (fetches[-1] if fetches else {})
        raw_url = str(terminal.get("url") or "").strip()
        public_url = sanitized_url(raw_url)
        method = str(terminal.get("method") or "GET").upper()
        if not provider or not lane or not public_url:
            continue
        key = (provider, lane, public_url)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "provider": provider,
            "lane": lane,
            "url": raw_url,
            "publicUrl": public_url,
            "host": str(urlsplit(public_url).hostname or ""),
            "path": str(urlsplit(public_url).path or "/"),
            "method": method,
            "fetchStatus": int(terminal.get("status") or 0),
            "challenge": str(terminal.get("challenge") or "unknown")[:32],
        })
    return out


def browser_binary() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def classify_dom(dom: str) -> str:
    lower = str(dom or "").lower()
    if any(marker in lower for marker in CHALLENGE_MARKERS):
        return "browser_challenge_persisted"
    text = re.sub(r"<[^>]+>", " ", lower)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 80:
        return "browser_inconclusive"
    return "browser_content_reached"


def probe_target(target: dict[str, Any], browser: str, *, timeout: int, virtual_time_ms: int) -> dict[str, Any]:
    started = time.monotonic()
    base = {
        key: target.get(key)
        for key in ("provider", "lane", "publicUrl", "host", "path", "method", "fetchStatus", "challenge")
    }
    if str(target.get("method") or "GET").upper() != "GET":
        return {**base, "outcome": "unsupported_method", "durationMs": 0}
    if not browser:
        return {**base, "outcome": "browser_unavailable", "durationMs": 0}
    with tempfile.TemporaryDirectory(prefix="niakvio-waf-browser-") as profile:
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-background-networking",
            "--disable-sync",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile}",
            f"--virtual-time-budget={max(1000, virtual_time_ms)}",
            "--dump-dom",
            str(target.get("url") or ""),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max(5, timeout), check=False)
        except subprocess.TimeoutExpired:
            return {**base, "outcome": "browser_timeout", "durationMs": round((time.monotonic()-started)*1000)}
        except Exception as exc:
            return {**base, "outcome": "browser_error", "error": type(exc).__name__, "durationMs": round((time.monotonic()-started)*1000)}
    if proc.returncode != 0 and not proc.stdout.strip():
        return {
            **base,
            "outcome": "browser_error",
            "exitCode": int(proc.returncode),
            "durationMs": round((time.monotonic()-started)*1000),
        }
    return {
        **base,
        "outcome": classify_dom(proc.stdout),
        "exitCode": int(proc.returncode),
        "durationMs": round((time.monotonic()-started)*1000),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report", type=Path)
    ap.add_argument("--output", type=Path, default=Path("automation/provider-waf-browser-session.json"))
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--virtual-time-ms", type=int, default=7000)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--max-targets", type=int, default=16)
    args = ap.parse_args()

    report = load(args.report)
    targets = extract_targets(report)[: max(1, args.max_targets)]
    browser = browser_binary()
    rows: list[dict[str, Any]] = []
    if targets:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
            futures = [
                pool.submit(
                    probe_target,
                    target,
                    browser,
                    timeout=args.timeout,
                    virtual_time_ms=args.virtual_time_ms,
                )
                for target in targets
            ]
            for future in futures:
                rows.append(future.result())
    rows.sort(key=lambda row: (str(row.get("provider") or ""), str(row.get("lane") or "")))
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("outcome") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    payload = {
        "schemaVersion": 1,
        "mode": "ordinary-headless-browser-session-no-challenge-solver",
        "browserAvailable": bool(browser),
        "browserExecutable": Path(browser).name if browser else None,
        "targetCount": len(targets),
        "counts": dict(sorted(counts.items())),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FIELD_PROVIDER_WAF_BROWSER_SESSION " + json.dumps({
        "targets": len(targets),
        "browserAvailable": bool(browser),
        "counts": payload["counts"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
