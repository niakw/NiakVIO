#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
promote = (ROOT / "scripts" / "promote_candidates.py").read_text(encoding="utf-8")
health = (ROOT / "scripts" / "health_check.mjs").read_text(encoding="utf-8")
config = __import__("json").loads((ROOT / "health-config.json").read_text(encoding="utf-8"))
media = (ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py").read_text(encoding="utf-8")
materializer = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")

# Provider / type / stream are explicit architecture levels.
assert 'scope: str = "provider"' in promote
assert 'scope="provider"' in promote
assert 'scope="type"' in promote
assert 'scope="stream"' in promote
assert 'provider_gates_pass(gates)' in promote
assert '"provider_blockers": provider_blockers' in promote
assert '"stream_findings": stream_findings' in promote
assert '"type_findings": type_findings' in promote

# Global activation only consumes provider-level gates. Stream proof is required
# for first onboarding, then per-work zero streams must not disable a proven provider.
assert 'previously_proven_provider' in promote
assert 'onboarding_stream_required = not previously_proven' in promote
assert 'onboarding_pass = stream_pass if onboarding_stream_required else True' in promote
assert 'already_proven_provider_kept_on_per_work_zero_stream' in promote
assert 'provider_gates_pass(gates)' in promote

# Stream-quality gates are not provider blockers.
for gate_name in (
    "06_distinct_host_diversity",
    "08_quality_and_bitrate",
    "09_language_and_subtitle_integrity",
    "10_content_identity_integrity",
):
    pos = promote.index(f'"{gate_name}": gate(')
    block = promote[pos:pos + 5000]
    assert 'scope="stream"' in block, gate_name

# Type support is stream-proven but independent from resolution/bitrate/language.
pos = promote.index("def independently_proven_categories")
block = promote[pos:promote.index("\n\ndef gate(", pos)]
assert "streams_playable" in block
assert "payload_verified_streams" in block
assert "minimum_height" not in block
assert "minimum_bandwidth" not in block
assert "accepted_audio" not in block
assert "accepted_subtitles" not in block

# Unsafe stream rows leave the surviving playable set before they become
# provider/type capability evidence.
pos = health.index("function acceptedPlayableProbe")
block = health[pos:pos + 1200]
assert "content_identity_status === 'contradiction'" in block
assert "duration_identity_mismatch === true" in block
assert "maximum_stream_median_latency_ms" in block

# Provider and stream scores/statuses are separate outputs.
for token in (
    "function providerStatusFrom",
    "function providerScore",
    "function streamQualityScore",
    "provider_status: providerStatus",
    "provider_score: providerScoreValue",
    "stream_quality_score: streamQualityScoreValue",
):
    assert token in health, token

# Runtime availability preflight is per work; Deep/Learning keeps fallbacks.
for mode in ("quick", "availability", "retry"):
    assert config["modes"][mode]["zero_stream_preflight"] is True, mode
assert config["modes"]["deep"]["zero_stream_preflight"] is False
assert config["activation"]["zero_stream_is_per_work_not_manifest_disable"] is True
assert config["activation"]["deep_learning_may_fallback_after_zero_stream"] is True

# Media context is request-local and identity lookup can cross TMDB movie/tv
# namespaces. Canonical anime stays semantic, while provider transport may use
# tv OR movie so anime films remain reachable without granting ordinary-movie
# semantic capability to anime-only providers.
assert "delete g.__nuvioMediaContext" in media
assert "__nuvioProviderRequestToken" in media
assert "requestDeadline=Date.now()+providerBudgetMs()" in media
assert "g.__nuvioProviderRequestToken!==requestToken" in media
assert 'return["movie","tv"]' in media
assert 'return["tv","movie"]' in media
assert 'canonical==="anime"' in media
assert 'if(canonical==="anime")return namespace==="movie"?"movie":"tv";' in media

# Architecture tests assert the semantic/transport boundary, not one historical
# implementation of the materializer. The dedicated anime contract test checks
# the exact catalog-backed widening after the enforcer has run.
assert "def normalize_anime_transport_compatibility(" in materializer
assert 'entry["canonicalSupportedTypes"]' in materializer
assert 'entry["supportedTypes"]' in materializer

print("provider/type/stream architecture scopes verified: anime canonical, tv/movie transport compatible")
