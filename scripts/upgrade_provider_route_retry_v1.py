#!/usr/bin/env python3
"""Add bounded, evidence-aware retries to provider route recognition.

Retries are for transient execution/network failures only. Deterministic source or
runtime defects such as MODULE_NOT_FOUND and source-policy blocks are never retried.
The best attempt is kept, and a positive attempt stops immediately.
"""
from __future__ import annotations

from pathlib import Path

import upgrade_provider_worker_dependency_resolution_v1 as worker_deps

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MARKER = "ROUTE_RECOVERY_ADAPTIVE_RETRY_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    helper_anchor = 'def recover_one(\n'
    helper = '''# ROUTE_RECOVERY_ADAPTIVE_RETRY_V1
_TRANSIENT_HTTP_STATUSES = {408, 425, 429, 500, 502, 503, 504}
_TRANSIENT_ERROR_TOKENS = (
    "timeout", "timed out", "etimedout", "econnreset", "econnrefused",
    "eai_again", "temporary failure", "socket hang up", "network error",
    "network_exception", "fetch failed", "worker_no_result",
)
_NON_RETRYABLE_ERROR_TOKENS = (
    "module_not_found", "provider module blocked by source policy",
)


def _worker_success_fetch_count(result: dict[str, Any]) -> int:
    total = 0
    for observation in result.get("network") or []:
        fetch = observation_fetch(observation)
        if fetch is not None and success(fetch):
            total += 1
    return total


def _worker_retry_reason(result: dict[str, Any]) -> str:
    if int(result.get("streams") or 0) > 0 or int(result.get("rawStreams") or 0) > 0:
        return ""
    status = str(result.get("status") or "").casefold()
    error = str(result.get("error") or "").casefold()
    combined = status + " " + error
    if any(token in combined for token in _NON_RETRYABLE_ERROR_TOKENS):
        return ""
    if status in {"runtime_error"}:
        return ""
    if status in {"worker_no_result", "timeout", "network_error", "network_exception"}:
        return status
    if any(token in combined for token in _TRANSIENT_ERROR_TOKENS):
        return next(token for token in _TRANSIENT_ERROR_TOKENS if token in combined)
    for observation in result.get("network") or []:
        fetch = observation_fetch(observation)
        if fetch is None:
            continue
        code = int(fetch.get("status") or 0)
        if code in _TRANSIENT_HTTP_STATUSES:
            return f"http-{code}"
        fetch_error = str(fetch.get("error") or "").casefold()
        if any(token in fetch_error for token in _TRANSIENT_ERROR_TOKENS):
            return next(token for token in _TRANSIENT_ERROR_TOKENS if token in fetch_error)
    return ""


def _run_worker_adaptive(
    provider_id: str,
    source_path: Path,
    fixture: dict[str, Any],
    *,
    upstream: bool,
    timeout: int,
    attempts: int,
) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    best_score: tuple[int, int, int, int, int] = (-1, -1, -1, -1, -1)
    used = 0
    for attempt in range(1, max(1, attempts) + 1):
        used = attempt
        try:
            result = run_worker(source_path, fixture, upstream=upstream, timeout=timeout)
        except Exception as exc:
            result = {
                "status": "worker_no_result",
                "error": type(exc).__name__,
                "streams": 0,
                "rawStreams": 0,
                "network": [],
                "serverAccessible": False,
                "serverSuccess": False,
            }
        score = (
            1 if int(result.get("streams") or 0) > 0 else 0,
            int(result.get("rawStreams") or 0),
            1 if result.get("serverSuccess") else 0,
            _worker_success_fetch_count(result),
            len(result.get("network") or []),
        )
        if best is None or score > best_score:
            best = result
            best_score = score
        reason = _worker_retry_reason(result)
        if not reason or attempt >= max(1, attempts):
            break
        print(
            "FIELD_ROUTE_RECOVERY_RETRY "
            f"provider={provider_id} fixture={fixture.get('slug')} "
            f"attempt={attempt + 1}/{max(1, attempts)} reason={reason}",
            flush=True,
        )
    assert best is not None
    best = dict(best)
    best["repairAttempts"] = used
    return best


'''
    text = once(text, helper_anchor, helper + helper_anchor, "adaptive-retry-helper")

    text = once(
        text,
        '    timeout: int,\n) -> dict[str, Any]:\n',
        '    timeout: int,\n    attempts: int,\n) -> dict[str, Any]:\n',
        "recover-one-attempts-signature",
    )

    text = once(
        text,
        '            result = run_worker(source_path, fixture, upstream=bool(source_id), timeout=timeout)\n',
        '''            result = _run_worker_adaptive(
                provider_id,
                source_path,
                fixture,
                upstream=bool(source_id),
                timeout=timeout,
                attempts=attempts,
            )
''',
        "recover-one-adaptive-call",
    )

    text = once(
        text,
        '    parser.add_argument("--timeout", type=int, default=int(os.environ.get("NIAKVIO_ROUTE_RECOVERY_TIMEOUT", "55")))\n',
        '    parser.add_argument("--timeout", type=int, default=int(os.environ.get("NIAKVIO_ROUTE_RECOVERY_TIMEOUT", "55")))\n    parser.add_argument("--attempts", type=int, default=int(os.environ.get("NIAKVIO_ROUTE_RECOVERY_ATTEMPTS", "3")))\n',
        "adaptive-retry-argparse",
    )

    text = once(
        text,
        '    timeout = max(15, min(120, int(args.timeout)))\n',
        '    timeout = max(15, min(120, int(args.timeout)))\n    attempts = max(1, min(4, int(args.attempts)))\n',
        "adaptive-retry-clamp",
    )

    text = once(
        text,
        '''                    tmp,
                    timeout,
                ): provider_id
''',
        '''                    tmp,
                    timeout,
                    attempts,
                ): provider_id
''',
        "adaptive-retry-pool-submit",
    )

    text = once(
        text,
        '        "durationMs": round((time.monotonic() - started) * 1000),\n',
        '        "durationMs": round((time.monotonic() - started) * 1000),\n        "maxAttemptsPerTask": attempts,\n',
        "adaptive-retry-report",
    )

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        'NIAKVIO_ROUTE_RECOVERY_ATTEMPTS',
        '_run_worker_adaptive(',
        '_worker_retry_reason(',
        '_NON_RETRYABLE_ERROR_TOKENS',
        '"module_not_found"',
        'FIELD_ROUTE_RECOVERY_RETRY',
        '"maxAttemptsPerTask": attempts',
    ):
        if needle not in value:
            raise AssertionError(f"adaptive route retry missing: {needle}")


def main() -> int:
    changed = patch() | worker_deps.patch()
    validate()
    worker_deps.validate()
    print(
        f"PROVIDER_ROUTE_RETRY_V1_OK changed={str(changed).lower()} "
        "max_attempts=4 default_attempts=3 deterministic_errors_retried=0 project_dep_resolution=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
