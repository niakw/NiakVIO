#!/usr/bin/env python3
"""Diagnose provider WAF challenges with an ordinary local Chrome session.

This is deliberately not a challenge solver:
- no stealth patching;
- no CAPTCHA/Turnstile interaction;
- no browser-challenge clearance-cookie fabrication/export;
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
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

NUVIO_TV_WINDOWS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

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
        if not isinstance(row, dict):
            continue

        # Fresh quick-yield rows are the primary authority. Persisted ordinary
        # browser diagnostics are also accepted as bounded re-probe seeds so a
        # WAF-only lane can evolve independently from the full provider census.
        prior_browser_row = (
            str(row.get("outcome") or "").startswith("browser_")
            and bool(str(row.get("publicUrl") or "").strip())
        )
        if str(row.get("debug_stage") or "") != "provider_waf_challenge" and not prior_browser_row:
            continue
        provider = str(row.get("provider_id") or row.get("provider") or "").strip().casefold()
        lane = str(row.get("semantic_type") or row.get("lane") or "").strip().casefold()
        if prior_browser_row:
            public_url = sanitized_url(row.get("publicUrl"))
            seed_kind = str(row.get("seedKind") or "").strip()
            seed_route = str(row.get("seedRoute") or "").strip()
            raw_url = public_url
            if seed_kind == "metadata-search" and seed_route:
                raw_url = urljoin(public_url, seed_route.replace("{query}", quote("niakvio")))
            method = str(row.get("method") or "GET").upper()
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
                "fetchStatus": int(row.get("fetchStatus") or 0),
                "challenge": str(row.get("challenge") or "unknown")[:32],
                "seedKind": seed_kind or None,
                "seedRoute": seed_route or None,
            })
            continue

        fetches = row.get("debug_fetches") if isinstance(row.get("debug_fetches"), list) else []
        challenged = [
            item for item in fetches
            if isinstance(item, dict) and str(item.get("challenge") or "").strip()
        ]
        browser_navigable = [
            item for item in challenged
            if str(item.get("method") or "GET").upper() == "GET"
        ]
        terminal = browser_navigable[-1] if browser_navigable else (
            challenged[-1] if challenged else (fetches[-1] if fetches else {})
        )
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


def extract_status_targets(
    status: dict[str, Any],
    overrides: dict[str, Any],
    existing: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Seed newly-classified WAF providers from current provider metadata.

    Prefer a provider-owned GET search route when metadata exposes one; otherwise
    fall back to the homepage. Metadata seeds are diagnostic only and never
    equivalent to observed challenged requests or playback proof.
    """
    existing_by_pair = {
        (str(row.get("provider") or "").casefold(), str(row.get("lane") or "").casefold()): row
        for row in existing
        if isinstance(row, dict)
    }
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    out: list[dict[str, Any]] = []
    for row in status.get("providers") or []:
        if not isinstance(row, dict) or str(row.get("status") or "") not in {"HARNESS MISMATCH", "HARNESS/ENV BLOCKED", "PROVIDER WAF/ANTIBOT"}:
            continue
        provider = str(row.get("provider") or "").strip().casefold()
        if not provider:
            continue
        patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
        base_url = str(
            patch.get("official_site")
            or patch.get("known_site")
            or patch.get("officialSite")
            or patch.get("knownSite")
            or ""
        ).strip()
        public_base = sanitized_url(base_url)
        if not public_base:
            continue
        learned_routes = [
            str(value).strip()
            for value in [
                *(patch.get("learned_routes") or []),
                *(patch.get("candidate_learned_routes") or []),
            ]
            if isinstance(value, str) and str(value).strip()
        ]
        search_route = next(
            (
                route for route in learned_routes
                if "{query}" in route and route.startswith("/") and "{" not in route.replace("{query}", "")
            ),
            "",
        )
        lanes = [
            str(value).strip().casefold()
            for value in row.get("declaredLanes") or []
            if str(value).strip()
        ] or ["unknown"]
        for lane in lanes:
            existing_row = existing_by_pair.get((provider, lane))
            existing_seed = str((existing_row or {}).get("seedKind") or "")
            if existing_row and not (existing_seed == "metadata-homepage" and search_route):
                continue
            seed_kind = "metadata-search" if search_route else "metadata-homepage"
            raw_url = (
                urljoin(public_base, search_route.replace("{query}", quote("niakvio")))
                if search_route else base_url
            )
            public_url = sanitized_url(raw_url)
            out.append({
                "provider": provider,
                "lane": lane,
                "url": raw_url,
                "publicUrl": public_url,
                "host": str(urlsplit(public_url).hostname or ""),
                "path": str(urlsplit(public_url).path or "/"),
                "method": "GET",
                "fetchStatus": 0,
                "challenge": f"{seed_kind}-seed",
                "seedKind": seed_kind,
                "seedRoute": search_route or None,
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


def probe_tv_okhttp_jvm(
    target: dict[str, Any],
    *,
    timeout: int,
    attempts: int,
    classpath: str | None,
) -> dict[str, Any]:
    """Exercise NuvioTV's audited PluginRuntime transport policy via JVM OkHttp.

    This reproduces the HTTP stack/policy much more closely than Chromium or
    libcurl, but GitHub JVM TLS and runner IP reputation still differ from an
    Android TV device. It remains harness evidence, never playback authority.
    """
    java = shutil.which("java")
    cp = str(classpath or "").strip()
    base = {
        "profile": "nuvio-tv-okhttp-jvm",
        "transportApproximation": (
            "GitHub JVM OkHttp 4.12.0 with NuvioTV PluginRuntime policy; "
            "not Android device TLS/IP"
        ),
        "userAgent": NUVIO_TV_WINDOWS_UA,
        "nativeContractApproximation": {
            "httpStack": "OkHttp 4.12.0",
            "proxyPolicy": "Proxy.NO_PROXY",
            "dnsPolicy": "IPv4FirstDns",
            "redirects": "HTTP+SSL enabled",
            "timeouts": "bounded by WAF diagnostic",
            "tlsRuntime": "GitHub JVM, not Android device",
        },
    }
    if not java or not cp:
        return {
            **base,
            "outcome": "okhttp_jvm_unavailable",
            "attemptCount": 0,
            "attempts": [],
        }
    cmd = [
        java,
        "-cp", cp,
        "WafOkHttpProbe",
        str(target.get("url") or ""),
        str(max(1, min(int(attempts), 3))),
        str(max(2, min(int(timeout), 60))),
        NUVIO_TV_WINDOWS_UA,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(8, int(timeout) * max(1, min(int(attempts), 3)) + 8),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            **base,
            "outcome": "okhttp_jvm_timeout",
            "attemptCount": 0,
            "attempts": [],
        }
    except Exception as exc:
        return {
            **base,
            "outcome": "okhttp_jvm_error",
            "attemptCount": 0,
            "attempts": [],
            "error": type(exc).__name__,
        }
    marker = "NIAKVIO_WAF_OKHTTP="
    rows = [
        line[len(marker):]
        for line in str(proc.stdout or "").splitlines()
        if line.startswith(marker)
    ]
    if not rows:
        return {
            **base,
            "outcome": "okhttp_jvm_error",
            "attemptCount": 0,
            "attempts": [],
            "exitCode": int(proc.returncode),
            "error": "missing_protocol_result",
        }
    try:
        payload = json.loads(rows[-1])
    except json.JSONDecodeError:
        return {
            **base,
            "outcome": "okhttp_jvm_error",
            "attemptCount": 0,
            "attempts": [],
            "exitCode": int(proc.returncode),
            "error": "invalid_protocol_result",
        }
    if not isinstance(payload, dict):
        payload = {}
    return {
        **base,
        **payload,
        "exitCode": int(proc.returncode),
    }


def probe_tv_direct_http(
    target: dict[str, Any],
    *,
    timeout: int,
    attempts: int,
) -> dict[str, Any]:
    """Approximate audited NuvioTV transport properties without claiming OkHttp.

    Uses GitHub-hosted libcurl with IPv4, no proxy, redirects and the audited
    NuvioTV UA. Cookie state exists only inside one ephemeral temp directory.
    TLS/client fingerprint and runner IP still differ from a real TV client.
    """
    curl = shutil.which("curl")
    if not curl:
        return {
            "profile": "nuvio-tv-direct-http-approx",
            "transportApproximation": "GitHub libcurl; native OkHttp not reproduced",
            "userAgent": NUVIO_TV_WINDOWS_UA,
            "outcome": "direct_http_unavailable",
            "attemptCount": 0,
            "attempts": [],
            "ordinarySessionReused": False,
        }
    attempt_rows: list[dict[str, Any]] = []
    attempt_limit = max(1, min(int(attempts), 3))
    with tempfile.TemporaryDirectory(prefix="niakvio-waf-direct-") as tmp:
        root = Path(tmp)
        cookie_jar = root / "cookies.txt"
        for attempt in range(1, attempt_limit + 1):
            body_path = root / f"body-{attempt}.txt"
            cmd = [
                curl,
                "--ipv4",
                "--noproxy", "*",
                "--location",
                "--max-redirs", "5",
                "--connect-timeout", str(max(2, min(int(timeout), 15))),
                "--max-time", str(max(5, int(timeout))),
                "--user-agent", NUVIO_TV_WINDOWS_UA,
                "--cookie", str(cookie_jar),
                "--cookie-jar", str(cookie_jar),
                "--compressed",
                "--silent",
                "--show-error",
                "--output", str(body_path),
                "--write-out", "%{http_code}",
                str(target.get("url") or ""),
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=max(6, int(timeout) + 3),
                    check=False,
                )
            except subprocess.TimeoutExpired:
                attempt_rows.append({"attempt": attempt, "outcome": "direct_http_timeout"})
                continue
            except Exception as exc:
                attempt_rows.append({
                    "attempt": attempt,
                    "outcome": "direct_http_error",
                    "error": type(exc).__name__,
                })
                continue
            try:
                body = body_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                body = ""
            status_text = str(proc.stdout or "").strip()
            status = int(status_text) if status_text.isdigit() else 0
            classified = classify_dom(body)
            if classified == "browser_content_reached":
                outcome = "direct_http_content_reached"
            elif classified == "browser_challenge_persisted":
                outcome = "direct_http_challenge_persisted"
            elif proc.returncode != 0:
                outcome = "direct_http_error"
            else:
                outcome = "direct_http_inconclusive"
            attempt_rows.append({
                "attempt": attempt,
                "outcome": outcome,
                "status": status,
                "exitCode": int(proc.returncode),
            })
            if outcome == "direct_http_content_reached":
                break

    outcomes = [str(row.get("outcome") or "") for row in attempt_rows]
    if "direct_http_content_reached" in outcomes:
        final = "direct_http_content_reached"
    elif "direct_http_challenge_persisted" in outcomes:
        final = "direct_http_challenge_persisted"
    elif outcomes and all(value == "direct_http_timeout" for value in outcomes):
        final = "direct_http_timeout"
    elif "direct_http_inconclusive" in outcomes:
        final = "direct_http_inconclusive"
    else:
        final = outcomes[-1] if outcomes else "direct_http_error"
    return {
        "profile": "nuvio-tv-direct-http-approx",
        "transportApproximation": "GitHub libcurl IPv4+NO_PROXY+redirects with audited NuvioTV UA",
        "userAgent": NUVIO_TV_WINDOWS_UA,
        "nativeContractApproximation": {
            "ipv4First": True,
            "proxyPolicy": "NO_PROXY",
            "redirects": "enabled",
            "httpStack": "libcurl-not-OkHttp",
        },
        "outcome": final,
        "attemptCount": len(attempt_rows),
        "attempts": attempt_rows,
        "ordinarySessionReused": attempt_limit > 1,
    }


def probe_target(
    target: dict[str, Any],
    browser: str,
    *,
    timeout: int,
    virtual_time_ms: int,
    attempts: int = 2,
    client_profile_matrix: bool = False,
    okhttp_classpath: str | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    base = {
        key: target.get(key)
        for key in ("provider", "lane", "publicUrl", "host", "path", "method", "fetchStatus", "challenge", "seedKind", "seedRoute")
    }
    if str(target.get("method") or "GET").upper() != "GET":
        return {**base, "outcome": "unsupported_method", "durationMs": 0}
    if not browser:
        return {**base, "outcome": "browser_unavailable", "durationMs": 0}
    attempt_limit = max(1, min(int(attempts), 3))
    profiles: list[tuple[str, str | None]] = [("github-default-browser", None)]
    if client_profile_matrix:
        profiles.append(("nuvio-tv-ua-browser", NUVIO_TV_WINDOWS_UA))

    profile_rows: list[dict[str, Any]] = []
    for profile_name, user_agent in profiles:
        attempt_rows: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory(prefix="niakvio-waf-browser-", ignore_cleanup_errors=True) as profile:
            for attempt in range(1, attempt_limit + 1):
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
                ]
                if user_agent:
                    cmd.append(f"--user-agent={user_agent}")
                cmd.extend(["--dump-dom", str(target.get("url") or "")])
                try:
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=max(5, timeout),
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    attempt_rows.append({"attempt": attempt, "outcome": "browser_timeout"})
                    continue
                except Exception as exc:
                    attempt_rows.append({
                        "attempt": attempt,
                        "outcome": "browser_error",
                        "error": type(exc).__name__,
                    })
                    continue
                if proc.returncode != 0 and not proc.stdout.strip():
                    attempt_rows.append({
                        "attempt": attempt,
                        "outcome": "browser_error",
                        "exitCode": int(proc.returncode),
                    })
                    continue
                outcome = classify_dom(proc.stdout)
                attempt_rows.append({
                    "attempt": attempt,
                    "outcome": outcome,
                    "exitCode": int(proc.returncode),
                })
                if outcome == "browser_content_reached":
                    break

        outcomes = [str(row.get("outcome") or "") for row in attempt_rows]
        if "browser_content_reached" in outcomes:
            profile_outcome = "browser_content_reached"
        elif "browser_challenge_persisted" in outcomes:
            profile_outcome = "browser_challenge_persisted"
        elif outcomes and all(value == "browser_timeout" for value in outcomes):
            profile_outcome = "browser_timeout"
        elif "browser_inconclusive" in outcomes:
            profile_outcome = "browser_inconclusive"
        else:
            profile_outcome = outcomes[-1] if outcomes else "browser_error"
        profile_rows.append({
            "profile": profile_name,
            "userAgent": user_agent,
            "outcome": profile_outcome,
            "attemptCount": len(attempt_rows),
            "attempts": attempt_rows,
            "ordinarySessionReused": attempt_limit > 1,
        })

    direct_profile: dict[str, Any] | None = None
    okhttp_profile: dict[str, Any] | None = None
    if client_profile_matrix:
        direct_profile = probe_tv_direct_http(
            target,
            timeout=timeout,
            attempts=attempt_limit,
        )
        okhttp_profile = probe_tv_okhttp_jvm(
            target,
            timeout=timeout,
            attempts=attempt_limit,
            classpath=okhttp_classpath,
        )

    content_profiles = [
        str(row.get("profile") or "")
        for row in profile_rows
        if str(row.get("outcome") or "") == "browser_content_reached"
    ]
    direct_content_reached = (
        isinstance(direct_profile, dict)
        and str(direct_profile.get("outcome") or "") == "direct_http_content_reached"
    )
    if direct_content_reached:
        content_profiles.append("nuvio-tv-direct-http-approx")
    okhttp_content_reached = (
        isinstance(okhttp_profile, dict)
        and str(okhttp_profile.get("outcome") or "") == "okhttp_jvm_content_reached"
    )
    if okhttp_content_reached:
        content_profiles.append("nuvio-tv-okhttp-jvm")
    profile_outcomes = [str(row.get("outcome") or "") for row in profile_rows]
    if content_profiles:
        final_outcome = "browser_content_reached"
    elif "browser_challenge_persisted" in profile_outcomes:
        final_outcome = "browser_challenge_persisted"
    elif profile_outcomes and all(value == "browser_timeout" for value in profile_outcomes):
        final_outcome = "browser_timeout"
    elif "browser_inconclusive" in profile_outcomes:
        final_outcome = "browser_inconclusive"
    else:
        final_outcome = profile_outcomes[-1] if profile_outcomes else "browser_error"

    default_profile = profile_rows[0] if profile_rows else {"attempts": [], "attemptCount": 0}
    return {
        **base,
        "outcome": final_outcome,
        "attemptCount": int(default_profile.get("attemptCount") or 0),
        "attempts": default_profile.get("attempts") or [],
        "ordinarySessionReused": attempt_limit > 1,
        "clientProfileMatrix": profile_rows,
        "directHttpProfile": direct_profile,
        "okHttpJvmProfile": okhttp_profile,
        "contentProfiles": content_profiles,
        "nativeTvTransportStillUnproven": True,
        "durationMs": round((time.monotonic()-started)*1000),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report", type=Path)
    ap.add_argument("--output", type=Path, default=Path("automation/provider-waf-browser-session.json"))
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--virtual-time-ms", type=int, default=7000)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--client-profile-matrix", action="store_true")
    ap.add_argument("--okhttp-classpath")
    ap.add_argument("--status", type=Path)
    ap.add_argument("--overrides", type=Path)
    ap.add_argument("--max-targets", type=int, default=16)
    args = ap.parse_args()

    report = load(args.report)
    targets = extract_targets(report)
    if args.status and args.overrides and args.status.is_file() and args.overrides.is_file():
        supplemental = extract_status_targets(load(args.status), load(args.overrides), targets)
        upgraded_pairs = {
            (str(row.get("provider") or ""), str(row.get("lane") or ""))
            for row in supplemental
            if str(row.get("seedKind") or "") == "metadata-search"
        }
        targets = [
            row for row in targets
            if not (
                str(row.get("seedKind") or "") == "metadata-homepage"
                and (str(row.get("provider") or ""), str(row.get("lane") or "")) in upgraded_pairs
            )
        ]
        targets.extend(supplemental)
    targets = targets[: max(1, args.max_targets)]
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
                    attempts=args.attempts,
                    client_profile_matrix=args.client_profile_matrix,
                    okhttp_classpath=args.okhttp_classpath,
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
        "attemptsPerTarget": max(1, min(int(args.attempts), 3)),
        "clientProfileMatrixEnabled": bool(args.client_profile_matrix),
        "clientProfiles": [
            {
                "id": "github-default-browser",
                "transportApproximation": "GitHub-hosted Chromium",
                "userAgent": "browser-default",
            },
            *([{
                "id": "nuvio-tv-ua-browser",
                "transportApproximation": "GitHub-hosted Chromium with audited NuvioTV default UA only",
                "userAgent": NUVIO_TV_WINDOWS_UA,
                "nativeContract": {
                    "httpStack": "OkHttp",
                    "proxyPolicy": "Proxy.NO_PROXY",
                    "dnsPolicy": "IPv4FirstDns",
                    "redirects": "HTTP+SSL enabled",
                },
            }, {
                "id": "nuvio-tv-okhttp-jvm",
                "transportApproximation": "GitHub JVM OkHttp 4.12.0 with audited NuvioTV PluginRuntime policy",
                "userAgent": NUVIO_TV_WINDOWS_UA,
                "nativeContractApproximation": {
                    "httpStack": "OkHttp 4.12.0",
                    "proxyPolicy": "Proxy.NO_PROXY",
                    "dnsPolicy": "IPv4FirstDns",
                    "redirects": "HTTP+SSL enabled",
                    "tlsRuntime": "GitHub JVM, not Android device",
                },
            }, {
                "id": "nuvio-tv-direct-http-approx",
                "transportApproximation": "GitHub libcurl with IPv4, NO_PROXY, redirects and audited NuvioTV UA",
                "userAgent": NUVIO_TV_WINDOWS_UA,
                "nativeContractApproximation": {
                    "httpStack": "libcurl-not-OkHttp",
                    "proxyPolicy": "NO_PROXY",
                    "dnsPolicy": "IPv4 only",
                    "redirects": "enabled",
                },
            }] if args.client_profile_matrix else []),
        ],
        "limitations": [
            "GitHub JVM OkHttp reproduces NuvioTV HTTP policy but not Android device TLS/IP reputation",
            "GitHub Chromium/libcurl remain secondary harness comparisons",
            "GitHub runner IP reputation differs from a real TV/mobile client",
            "browser challenge persistence is harness/environment evidence, not provider-code failure",
        ],
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
