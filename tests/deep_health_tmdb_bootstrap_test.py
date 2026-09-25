#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
health = (ROOT / "scripts" / "health_check.mjs").read_text(encoding="utf-8")
worker = (ROOT / "scripts" / "provider_worker.cjs").read_text(encoding="utf-8")
invocation = (ROOT / "tests" / "provider_worker_invocation.test.cjs").read_text(encoding="utf-8")

for token in (
    "NIAKVIO_TMDB_BOOTSTRAP_KEY: process.env.TMDB_API_KEY || ''",
    "NIAKVIO_TMDB_BOOTSTRAP_TOKEN: process.env.TMDB_ACCESS_TOKEN || ''",
):
    assert token in health, token

for token in (
    "process.env.NIAKVIO_TMDB_BOOTSTRAP_KEY",
    "process.env.NIAKVIO_TMDB_BOOTSTRAP_TOKEN",
    "clearVisibleTmdbCredentials()",
    "loaded = await loadProvider(providerPath)",
):
    assert token in worker, token

load_at = worker.index("loaded = await loadProvider(providerPath)")
clear_at = worker.index("clearVisibleTmdbCredentials();", load_at)
streams_at = worker.index("const getStreams = findGetStreams(loaded)", clear_at)
assert load_at < clear_at < streams_at

assert "Core did not capture TMDB key at module init" in invocation
assert "TMDB global leaked into getStreams" in invocation
assert "bootstrap env leaked into getStreams" in invocation

print("Deep health TMDB init-only bootstrap contract passed")
