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
import os
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
            "requestHeaders": safe_request_headers(terminal),
        })
    return out



NETWORK_FAILURE_STAGES = {
    "provider_network_exception",
    "provider_network_http_error",
    "provider_network_timeout",
}
NETWORK_INFRA_HOSTS = {
    "api.themoviedb.org",
    "arm.haglund.dev",
}
SENSITIVE_QUERY_KEY = re.compile(
    r"(?:api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce|hash)",
    re.I,
)
SAFE_REPLAY_HEADERS = {
    "accept", "accept-language", "content-type", "origin", "referer", "referrer",
    "user-agent", "x-requested-with", "x-client-version", "x-app-version",
}


def safe_request_headers(row: dict[str, Any] | None) -> dict[str, str]:
    """Return the bounded non-secret header subset safe for transport replay."""
    raw = (row or {}).get("request_headers")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in list(raw.items())[:32]:
        name = str(key or "").strip().casefold()
        if name not in SAFE_REPLAY_HEADERS or name == "accept-encoding":
            continue
        text = str(value or "").strip()
        if text:
            out[name] = text[:500]
    return out


def extract_network_failure_targets(
    report: dict[str, Any],
    status: dict[str, Any],
) -> list[dict[str, Any]]:
    """Replay only exact provider GET requests that failed on the CI network.

    The raw URL is used only for the in-process request. Persisted probe rows
    contain publicUrl/host/path without query values. This is diagnostic
    transport evidence, never provider playback proof.
    """
    blocked = {
        str(row.get("provider") or "").strip().casefold()
        for row in status.get("providers") or []
        if isinstance(row, dict)
        and str(row.get("status") or "") == "PROVIDER NETWORK BLOCKED"
        and str(row.get("provider") or "").strip()
    }
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in report.get("rows") or []:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider_id") or row.get("provider") or "").strip().casefold()
        lane = str(row.get("semantic_type") or row.get("lane") or "").strip().casefold()
        stage = str(row.get("debug_stage") or "").strip()
        if provider not in blocked or not lane or stage not in NETWORK_FAILURE_STAGES:
            continue
        fetches = row.get("debug_fetches") if isinstance(row.get("debug_fetches"), list) else []
        for item in reversed(fetches):
            if not isinstance(item, dict) or str(item.get("method") or "GET").upper() != "GET":
                continue
            try:
                status_code = int(item.get("status") or 0)
            except (TypeError, ValueError):
                status_code = 0
            if status_code and status_code < 400:
                continue
            raw_url = str(item.get("url") or "").strip()
            if not raw_url or "<redacted>" in raw_url:
                continue
            try:
                parsed = urlsplit(raw_url)
            except ValueError:
                continue
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            if parsed.hostname.casefold() in NETWORK_INFRA_HOSTS:
                continue
            query_parts = []
            unsafe = False
            for part in parsed.query.split("&") if parsed.query else []:
                key = part.split("=", 1)[0]
                if SENSITIVE_QUERY_KEY.search(key):
                    unsafe = True
                    break
                query_parts.append(part)
            if unsafe:
                continue
            public_url = sanitized_url(raw_url)
            key = (provider, lane, public_url)
            if key in seen:
                continue
            seen.add(key)
            error = str(item.get("error") or "").strip()
            challenge = (
                f"network-http-{status_code}"
                if status_code
                else f"network-{error or 'exception'}"
            )[:48]
            out.append({
                "provider": provider,
                "lane": lane,
                "url": raw_url,
                "publicUrl": public_url,
                "host": str(parsed.hostname or ""),
                "path": str(parsed.path or "/"),
                "method": "GET",
                "fetchStatus": status_code,
                "challenge": challenge,
                "seedKind": "network-failure-replay",
                "seedRoute": None,
                "requestHeaders": safe_request_headers(item),
            })
            break
    return out

def extract_status_targets(
    status: dict[str, Any],
    overrides: dict[str, Any],
    existing: list[dict[str, Any]],
    explicit_providers: set[str] | None = None,
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
    explicit = {
        str(value or "").strip().casefold()
        for value in (explicit_providers or set())
        if str(value or "").strip()
    }
    transport_statuses = {
        "HARNESS MISMATCH",
        "CLIENT TRANSPORT GAP",
        "HARNESS/ENV BLOCKED",
        "PROVIDER WAF/ANTIBOT",
    }
    out: list[dict[str, Any]] = []
    for row in status.get("providers") or []:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip().casefold()
        if not provider:
            continue
        status_name = str(row.get("status") or "")
        explicit_target = provider in explicit
        if status_name not in transport_statuses and not explicit_target:
            continue
        # Explicit transport qualification may inspect a nominally green
        # provider, but never resurrect a provider whose current address/backend
        # authority is explicitly blocked.
        if explicit_target and row.get("authorityRepairEligible") is False:
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
    for name in (
        "brave-browser",
        "brave",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        found = shutil.which(name)
        if found:
            return found

    # Homebrew casks and ordinary macOS application installs do not normally
    # expose a browser binary on PATH. Prefer Brave when the user has it
    # installed, then Chrome/Chromium. Safari is intentionally excluded:
    # this diagnostic uses Chromium headless flags and must not pretend that
    # Safari exercised the same browser path.
    mac_candidates = (
        Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        Path.home() / "Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
        Path.home() / "Applications/Chromium.app/Contents/MacOS/Chromium",
    )
    for candidate in mac_candidates:
        if candidate.is_file():
            return str(candidate)
    return ""


def classify_dom(dom: str) -> str:
    """Ignore challenge marker words embedded in scripts or styles."""
    lower = str(dom or "").lower()
    clean = re.sub(r"<!--[\s\S]*?-->", " ", lower)
    clean = re.sub(
        r"<(script|style|noscript|template)\b[^>]*>[\s\S]*?</\1\s*>",
        " ", clean,
    )
    title_match = re.search(r"<title\b[^>]*>([\s\S]*?)</title\s*>", clean)
    title = re.sub(r"<[^>]+>", " ", title_match.group(1)) if title_match else ""
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", clean)).strip()
    title_challenge = any(
        word in title for word in (
            "just a moment", "checking your browser", "verify you are human", "attention required"
        )
    )
    visible_challenge = len(text) < 2000 and any(
        word in text for word in (
            "checking your browser", "verify you are human",
            "checking if the site connection is secure",
        )
    )
    structural_challenge = len(text) < 500 and any(
        word in clean for word in ("challenge-platform", "cf-browser-verification")
    )
    if title_challenge or visible_challenge or structural_challenge:
        return "browser_challenge_persisted"
    if len(text) < 80:
        return "browser_inconclusive"
    return "browser_content_reached"


def _probe_okhttp_jvm(
    target: dict[str, Any],
    *,
    timeout: int,
    attempts: int,
    classpath: str | None,
    profile: str,
    proxy_mode: str,
    max_timeout: int,
    transport_approximation: str,
    tls_runtime: str,
) -> dict[str, Any]:
    """Exercise an audited Nuvio JVM/OkHttp transport profile.

    The Java helper independently reapplies the strict non-secret header allowlist.
    This is transport evidence only: it is not target-device TLS or playback proof.
    """
    java = shutil.which("java")
    cp = str(classpath or "").strip()
    request_headers = safe_request_headers({"request_headers": target.get("requestHeaders")})
    effective_user_agent = request_headers.get("user-agent", NUVIO_TV_WINDOWS_UA)
    max_timeout = max(2, min(int(max_timeout), 60))
    effective_timeout = max(2, min(int(timeout), max_timeout))
    proxy_label = "Proxy.NO_PROXY" if proxy_mode == "no-proxy" else "JVM/system default"
    base = {
        "profile": profile,
        "transportApproximation": transport_approximation,
        "userAgent": effective_user_agent,
        "requestHeaderNames": sorted(request_headers),
        "nativeContractApproximation": {
            "httpStack": "OkHttp 4.12.0",
            "proxyPolicy": proxy_label,
            "dnsPolicy": "IPv4FirstDns",
            "redirects": "HTTP+SSL enabled",
            "timeouts": f"{max_timeout}s profile maximum",
            "tlsRuntime": tls_runtime,
        },
    }
    if not java or not cp:
        return {**base, "outcome": "okhttp_jvm_unavailable", "attemptCount": 0, "attempts": []}
    cmd = [
        java, "-cp", cp, "WafOkHttpProbe",
        str(target.get("url") or ""),
        str(max(1, min(int(attempts), 3))),
        str(effective_timeout),
        NUVIO_TV_WINDOWS_UA,
    ]
    for name, value in sorted(request_headers.items()):
        cmd.append(f"{name}: {value}")
    child_env = os.environ.copy()
    child_env.update({
        "NIAKVIO_WAF_OKHTTP_PROFILE": profile,
        "NIAKVIO_WAF_PROXY_MODE": proxy_mode,
        "NIAKVIO_WAF_MAX_TIMEOUT_SECONDS": str(max_timeout),
    })
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=max(8, effective_timeout * max(1, min(int(attempts), 3)) + 8),
            check=False, env=child_env,
        )
    except subprocess.TimeoutExpired:
        return {**base, "outcome": "okhttp_jvm_timeout", "attemptCount": 0, "attempts": []}
    except Exception as exc:
        return {**base, "outcome": "okhttp_jvm_error", "attemptCount": 0, "attempts": [], "error": type(exc).__name__}
    marker = "NIAKVIO_WAF_OKHTTP="
    rows = [line[len(marker):] for line in str(proc.stdout or "").splitlines() if line.startswith(marker)]
    if not rows:
        return {**base, "outcome": "okhttp_jvm_error", "attemptCount": 0, "attempts": [], "exitCode": int(proc.returncode), "error": "missing_protocol_result"}
    try:
        payload = json.loads(rows[-1])
    except json.JSONDecodeError:
        return {**base, "outcome": "okhttp_jvm_error", "attemptCount": 0, "attempts": [], "exitCode": int(proc.returncode), "error": "invalid_protocol_result"}
    if not isinstance(payload, dict):
        payload = {}
    return {**base, **payload, "exitCode": int(proc.returncode)}


def probe_tv_okhttp_jvm(
    target: dict[str, Any],
    *,
    timeout: int,
    attempts: int,
    classpath: str | None,
) -> dict[str, Any]:
    return _probe_okhttp_jvm(
        target, timeout=timeout, attempts=attempts, classpath=classpath,
        profile="nuvio-tv-okhttp-jvm", proxy_mode="no-proxy", max_timeout=30,
        transport_approximation=(
            "GitHub JVM OkHttp 4.12.0 with audited NuvioTV PluginRuntime policy; "
            "not Android device TLS/IP"
        ),
        tls_runtime="GitHub JVM, not Android device",
    )


def probe_desktop_okhttp_jvm(
    target: dict[str, Any],
    *,
    timeout: int,
    attempts: int,
    classpath: str | None,
) -> dict[str, Any]:
    return _probe_okhttp_jvm(
        target, timeout=timeout, attempts=attempts, classpath=classpath,
        profile="nuvio-desktop-okhttp-jvm", proxy_mode="system", max_timeout=60,
        transport_approximation=(
            "GitHub JVM OkHttp 4.12.0 with audited Nuvio Desktop JVM transport policy; "
            "not target OS/device network environment"
        ),
        tls_runtime="GitHub JVM; same JVM transport family, not target OS/device TLS",
    )

def probe_tv_direct_http(
    target: dict[str, Any],
    *,
    timeout: int,
    attempts: int,
) -> dict[str, Any]:
    """Approximate the audited native request with libcurl.

    Safe provider headers are replayed so this profile and the JVM profile probe
    the same HTTP request contract. Cookie state remains ephemeral and libcurl
    is still not OkHttp/Android TLS.
    """
    curl = shutil.which("curl")
    request_headers = safe_request_headers({"request_headers": target.get("requestHeaders")})
    effective_user_agent = request_headers.get("user-agent", NUVIO_TV_WINDOWS_UA)
    if not curl:
        return {
            "profile": "nuvio-tv-direct-http-approx",
            "transportApproximation": "GitHub libcurl; native OkHttp not reproduced",
            "userAgent": effective_user_agent,
            "requestHeaderNames": sorted(request_headers),
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
                "--max-time", str(max(5, min(int(timeout), 30))),
                "--user-agent", effective_user_agent,
                "--cookie", str(cookie_jar),
                "--cookie-jar", str(cookie_jar),
                "--compressed",
                "--silent",
                "--show-error",
                "--output", str(body_path),
                "--write-out", "%{http_code}",
            ]
            for name, value in sorted(request_headers.items()):
                if name != "user-agent":
                    cmd.extend(["--header", f"{name}: {value}"])
            cmd.append(str(target.get("url") or ""))
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=max(6, min(int(timeout), 30) + 3),
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
            if classified == "browser_challenge_persisted":
                outcome = "direct_http_challenge_persisted"
            elif proc.returncode != 0 or not 200 <= status < 400:
                outcome = "direct_http_http_error" if status >= 400 else "direct_http_error"
            elif classified == "browser_content_reached":
                outcome = "direct_http_content_reached"
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
        "transportApproximation": "GitHub libcurl IPv4+NO_PROXY+redirects with audited NuvioTV request headers",
        "userAgent": effective_user_agent,
        "requestHeaderNames": sorted(request_headers),
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

def diagnose_transport_profiles(
    browser_profiles: list[dict[str, Any]],
    direct_profile: dict[str, Any] | None,
    okhttp_profile: dict[str, Any] | None,
    desktop_okhttp_profile: dict[str, Any] | None = None,
) -> str:
    """Classify client/network differentials without promoting them to playback proof."""
    browser_outcomes = {str(row.get("outcome") or "") for row in browser_profiles if isinstance(row, dict)}
    browser_content = "browser_content_reached" in browser_outcomes
    browser_challenge = "browser_challenge_persisted" in browser_outcomes
    direct_outcome = str((direct_profile or {}).get("outcome") or "")
    tv_outcome = str((okhttp_profile or {}).get("outcome") or "")
    desktop_outcome = str((desktop_okhttp_profile or {}).get("outcome") or "")
    def errors(profile: dict[str, Any] | None) -> set[str]:
        return {
            str((profile or {}).get("error") or ""),
            *{str(row.get("error") or "") for row in (profile or {}).get("attempts") or [] if isinstance(row, dict)},
        }
    tls_markers = ("SSLHandshakeException", "SSLProtocolException", "CertPathValidatorException")
    tv_tls = any(marker in value for value in errors(okhttp_profile) for marker in tls_markers)
    desktop_tls = any(marker in value for value in errors(desktop_okhttp_profile) for marker in tls_markers)
    if desktop_outcome == "okhttp_jvm_content_reached" and tv_outcome == "okhttp_jvm_challenge_persisted":
        return "tv_waf_desktop_content_differential"
    if tv_outcome == "okhttp_jvm_content_reached" and desktop_outcome == "okhttp_jvm_challenge_persisted":
        return "desktop_waf_tv_content_differential"
    if desktop_outcome == "okhttp_jvm_content_reached" and tv_outcome in {"okhttp_jvm_error","okhttp_jvm_timeout","okhttp_jvm_http_error"}:
        return "tv_transport_desktop_content_differential"
    if tv_outcome == "okhttp_jvm_content_reached" and desktop_outcome in {"okhttp_jvm_error","okhttp_jvm_timeout","okhttp_jvm_http_error"}:
        return "desktop_transport_tv_content_differential"
    if browser_content and (tv_tls or desktop_tls):
        return "native_client_tls_differential"
    if browser_content and tv_outcome == "okhttp_jvm_challenge_persisted" and (not desktop_outcome or desktop_outcome == "okhttp_jvm_challenge_persisted"):
        return "native_client_waf_differential"
    native_content = "okhttp_jvm_content_reached" in {tv_outcome, desktop_outcome}
    if browser_content and native_content:
        return "content_reached_cross_transport" if direct_outcome == "direct_http_content_reached" else "browser_and_okhttp_content_reached"
    if browser_content and (tv_outcome in {"okhttp_jvm_error","okhttp_jvm_timeout","okhttp_jvm_http_error"} or desktop_outcome in {"okhttp_jvm_error","okhttp_jvm_timeout","okhttp_jvm_http_error"}):
        return "native_client_transport_differential"
    if browser_content:
        return "browser_content_native_unproven"
    if browser_challenge and tv_outcome == "okhttp_jvm_challenge_persisted" and (not desktop_outcome or desktop_outcome == "okhttp_jvm_challenge_persisted"):
        return "waf_persisted_cross_transport"
    if native_content:
        return "okhttp_content_browser_unproven"
    if browser_challenge:
        return "browser_waf_persisted"
    return "transport_inconclusive"


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
    desktop_okhttp_profile: dict[str, Any] | None = None
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
        desktop_okhttp_profile = probe_desktop_okhttp_jvm(
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
    desktop_okhttp_content_reached = (
        isinstance(desktop_okhttp_profile, dict)
        and str(desktop_okhttp_profile.get("outcome") or "") == "okhttp_jvm_content_reached"
    )
    if desktop_okhttp_content_reached:
        content_profiles.append("nuvio-desktop-okhttp-jvm")
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
        "desktopOkHttpJvmProfile": desktop_okhttp_profile,
        "contentProfiles": content_profiles,
        "transportDiagnosis": diagnose_transport_profiles(
            profile_rows,
            direct_profile,
            okhttp_profile,
            desktop_okhttp_profile,
        ),
        "nativeTvTransportStillUnproven": True,
        "durationMs": round((time.monotonic()-started)*1000),
    }


def filter_targets_by_provider(
    targets: list[dict[str, Any]],
    providers: set[str],
) -> list[dict[str, Any]]:
    if not providers:
        return targets
    wanted = {str(value or "").strip().casefold() for value in providers if str(value or "").strip()}
    return [
        row for row in targets
        if str(row.get("provider") or "").strip().casefold() in wanted
    ]


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
    ap.add_argument("--network-report", type=Path)
    ap.add_argument("--max-targets", type=int, default=16)
    ap.add_argument("--provider", action="append", default=[])
    ap.add_argument("--providers", default="")
    args = ap.parse_args()

    requested = {
        str(value or "").strip().casefold()
        for value in [
            *args.provider,
            *str(args.providers or "").split(","),
        ]
        if str(value or "").strip()
    }
    report = load(args.report)
    targets = extract_targets(report)
    if args.status and args.overrides and args.status.is_file() and args.overrides.is_file():
        supplemental = extract_status_targets(
            load(args.status),
            load(args.overrides),
            targets,
            explicit_providers=requested,
        )
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
    if args.network_report and args.status and args.network_report.is_file() and args.status.is_file():
        network_targets = extract_network_failure_targets(load(args.network_report), load(args.status))
        network_pairs = {
            (str(row.get("provider") or ""), str(row.get("lane") or ""))
            for row in network_targets
        }
        targets = [
            row for row in targets
            if not (
                str(row.get("seedKind") or "") == "network-failure-replay"
                and (str(row.get("provider") or ""), str(row.get("lane") or "")) in network_pairs
            )
        ]
        targets.extend(network_targets)
    targets = filter_targets_by_provider(targets, requested)
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
        "providerFilter": sorted(requested),
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
            "exact failed provider GET replay is transport differential evidence only; it cannot grant playback proof",
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
