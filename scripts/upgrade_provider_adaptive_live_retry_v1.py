#!/usr/bin/env python3
"""Make Provider v3 live retries adaptive instead of unconditional.

Every active semantic lane still receives a current-run live probe. Additional
attempts are reserved for genuinely transient transport/probe failures such as
rate limiting, timeouts, status 0 and selected gateway/server errors. Deterministic
failures and successful responses move immediately to the next fixture/type.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCT = ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py"
MARKER = "PROVIDER_V3_ADAPTIVE_LIVE_RETRY_V1"

HELPER = '''\n\n# PROVIDER_V3_ADAPTIVE_LIVE_RETRY_V1\nTRANSIENT_LIVE_HTTP_STATUSES = {0, 408, 425, 429, 500, 502, 503, 504, 522, 524}\n\n\ndef should_retry_live_probe(result: dict[str, Any]) -> bool:\n    """Retry only when the current attempt looks transient rather than deterministic."""\n    task_status = str(result.get("status") or "").strip().casefold()\n    if task_status == "probe_error" or "timeout" in task_status:\n        return True\n    provider_statuses = [\n        int(fetch.get("status") or 0)\n        for fetch in result.get("fetches") or []\n        if isinstance(fetch, dict) and provider_fetch(fetch)\n    ]\n    if not provider_statuses:\n        return False\n    return any(status in TRANSIENT_LIVE_HTTP_STATUSES for status in provider_statuses)\n'''


def patch() -> bool:
    text = RECONSTRUCT.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    helper_anchor = "LIVE_PROBE_ATTEMPTS = _live_probe_attempts()\n"
    if text.count(helper_anchor) != 1:
        raise AssertionError("adaptive retry helper anchor missing")
    text = text.replace(helper_anchor, helper_anchor + HELPER, 1)

    candidate_break = '''            if is_qualified(evaluation) or semantic_type in {\n                str(value or "").strip().casefold() for value in evaluation.get("validatedTypes") or []\n            }:\n                break\n'''
    candidate_replacement = '''            if is_qualified(evaluation) or semantic_type in {\n                str(value or "").strip().casefold() for value in evaluation.get("validatedTypes") or []\n            }:\n                break\n            if attempt < LIVE_PROBE_ATTEMPTS and not should_retry_live_probe(result):\n                print(\n                    "FIELD_PROVIDER_RETRY_SKIPPED_DETERMINISTIC "\n                    f"provider={provider['provider_id']} fixture={task.get('fixture_slug')} "\n                    f"attempt={attempt} task_status={result.get('status')}",\n                    flush=True,\n                )\n                break\n'''
    if text.count(candidate_break) != 1:
        raise AssertionError("adaptive retry candidate anchor missing")
    text = text.replace(candidate_break, candidate_replacement, 1)

    final_break = '''            if semantic_type in validated and not bad_status:\n                break\n'''
    final_replacement = '''            if semantic_type in validated and not bad_status:\n                break\n            if attempt < LIVE_PROBE_ATTEMPTS and not should_retry_live_probe(result):\n                print(\n                    "FIELD_PROVIDER_FINAL_RETRY_SKIPPED_DETERMINISTIC "\n                    f"provider={provider['provider_id']} fixture={final_task.get('fixture_slug')} "\n                    f"attempt={attempt} task_status={result.get('status')}",\n                    flush=True,\n                )\n                break\n'''
    if text.count(final_break) != 1:
        raise AssertionError("adaptive retry final anchor missing")
    text = text.replace(final_break, final_replacement, 1)

    RECONSTRUCT.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else RECONSTRUCT.read_text(encoding="utf-8")
    required = (
        MARKER,
        "TRANSIENT_LIVE_HTTP_STATUSES",
        "def should_retry_live_probe(",
        "FIELD_PROVIDER_RETRY_SKIPPED_DETERMINISTIC",
        "FIELD_PROVIDER_FINAL_RETRY_SKIPPED_DETERMINISTIC",
        "not should_retry_live_probe(result)",
    )
    missing = [needle for needle in required if needle not in value]
    if missing:
        raise AssertionError("adaptive live retry markers missing: " + ",".join(missing))
    # The original contract owns the candidate and selected-final retry guards.
    # Later strict transient fallbacks may reuse the same helper, so additional
    # guarded call-sites are valid as long as both original guards remain.
    if value.count("not should_retry_live_probe(result)") < 2:
        raise AssertionError("adaptive retry must guard candidate and final proof loops")


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_ADAPTIVE_LIVE_RETRY_V1_OK "
        f"changed={str(changed).lower()} first_probe_mandatory=1 transient_retries=1 "
        "deterministic_duplicate_retries=0 max_attempts_unchanged=3"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
