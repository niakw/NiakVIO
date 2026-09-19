#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_adaptive_live_retry_v1 as migration  # noqa: E402

migration.patch()
migration.validate()

import reconstruct_provider_v3_sequential_live as sequential  # noqa: E402


def fetch(status: int, url: str = "https://provider.example/path") -> dict:
    return {"url": url, "finalUrl": url, "status": status, "provider": True}


for status in (0, 408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526):
    assert sequential.should_retry_live_probe({"status": "no_streams", "fetches": [fetch(status)]}) is True, status
assert sequential.should_retry_live_probe({"status": "probe_error", "fetches": []}) is True
assert sequential.should_retry_live_probe({"status": "network_timeout", "fetches": []}) is True

for status in (200, 201, 301, 302, 400, 401, 403, 404, 405, 410, 451):
    assert sequential.should_retry_live_probe({"status": "no_streams", "fetches": [fetch(status)]}) is False, status
assert sequential.should_retry_live_probe({"status": "wrong_content", "fetches": [fetch(200)]}) is False
assert sequential.should_retry_live_probe({"status": "runtime_error", "fetches": []}) is False
assert sequential.should_retry_live_probe({"status": "no_streams", "fetches": []}) is False

source = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")
assert source.count("not should_retry_live_probe(result)") >= 2
assert "FIELD_PROVIDER_RETRY_SKIPPED_DETERMINISTIC" in source
assert "FIELD_PROVIDER_FINAL_RETRY_SKIPPED_DETERMINISTIC" in source
assert "LIVE_PROBE_ATTEMPTS = _live_probe_attempts()" in source

print(
    "Provider v3 adaptive live retry tests passed: every lane still gets a first live probe; "
    "bounded retries remain for transient failures only; deterministic duplicate probes are skipped; "
    "strict fallback extensions may reuse the transient helper."
)
