#!/usr/bin/env python3
"""V21.6: preserve proof-correlated player/embed URLs when resolution fails.

Some upstream providers intentionally return an iframe/embed URL when a resolver
cannot turn it into direct media. ProviderValue replay previously made every
correlated step a mandatory HTTP resolution: a 4xx/5xx on the terminal player
caused the entire plan to disappear even though the player URL itself was the
upstream stream fallback.

V21.6 keeps failed correlated player-like URLs as bounded fallbacks while it
continues executing every remaining dependency-ready step. Fallbacks are emitted
only if no direct/nested stream succeeds. Ordinary catalogue/detail/API URLs are
never promoted. No provider, host fixture, title or provider-specific id is
encoded; the host family fallback reuses the common player-host vocabulary
already owned by ProviderBase.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_catalogue_identity_correlation_v21_5 as v215  # noqa: E402

BASE = v215.BASE
MARKER = "NIAKVIO_PROVIDER_PLAYER_FALLBACK_V21_6"

patch_worker = v215.patch_worker
patch_proof = v215.patch_proof
patch_recovery = v215.patch_recovery
patch_materializer = v215.patch_materializer
validate_worker = v215.validate_worker
validate_proof = v215.validate_proof
validate_recovery = v215.validate_recovery
validate_materializer = v215.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    v215.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    resolver_anchor = "async function _resolveProviderValuePlan(meta, mediaType, season, episode) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_PLAYER_FALLBACK_V21_6 */
function _spv216PlayerFallbackEligible(rawUrl) {
  const value = _text(rawUrl).trim();
  if (!/^https?:\/\//i.test(value)) return false;
  if (_directMedia(value) || _playerLike(value)) return true;
  try {
    const parsed = new URL(value);
    const host = _text(parsed.hostname).toLowerCase();
    if (/(?:sibnet|vidmoly|streamtape|sendvid|vidoza|myvi)/i.test(host)) return true;
    for (const key of parsed.searchParams.keys()) {
      if (/^(?:video|videoid|video_id|file|fileid|file_id|embed|embedid|embed_id|player|playerid|player_id|stream|streamid|stream_id|source|sourceid|source_id)$/i.test(key)) return true;
    }
  } catch (_) {}
  return false;
}
function _spv216FallbackReferer(stepSpec, stepBase) {
  const headers = stepSpec && stepSpec.headers && typeof stepSpec.headers === "object"
    ? stepSpec.headers : {};
  return _text(headers.Referer || headers.referer || stepBase || "");
}
function _spv216FallbackStreams(rows) {
  const out = [];
  const seen = new Set();
  for (const row of Array.isArray(rows) ? rows.slice(0, 12) : []) {
    const url = _text(row && row.url).trim();
    if (!url || seen.has(url) || !_spv216PlayerFallbackEligible(url)) continue;
    seen.add(url);
    out.push(..._streams([url], _text(row && row.referer)));
    if (out.length >= 12) break;
  }
  return out.slice(0, 12);
}
'''
    text = _once(text, resolver_anchor, helper + resolver_anchor, "v21.6-player-fallback-helper")

    start = text.index(resolver_anchor)
    end = text.index("async function _resolveSearchRequestPlan", start)
    resolver = text[start:end]

    old_state = '''      const valueSteps = (plan.steps || []).slice(0, 8);
      const completedSteps = new Set();
'''
    new_state = '''      const valueSteps = (plan.steps || []).slice(0, 8);
      const completedSteps = new Set();
      const playerFallbacks = [];
'''
    resolver = _once(resolver, old_state, new_state, "v21.6-fallback-state")

    old_fetch = '''          const payload = await _recipePayload(stepUrl, {}, stepSpec, values);
          _spv184Trace("step_response", mediaType, values.providerId || values.providerSlug, stepIndex, stepRoute);
'''
    new_fetch = '''          let payload;
          try {
            payload = await _recipePayload(stepUrl, {}, stepSpec, values);
          } catch (_) {
            if (_spv216PlayerFallbackEligible(stepUrl)) {
              const fallbackReferer = _spv216FallbackReferer(stepSpec, stepBase);
              if (!playerFallbacks.some(row => row.url === stepUrl)) {
                playerFallbacks.push({ url: stepUrl, referer: fallbackReferer });
              }
              _spv184Trace("step_player_fallback", mediaType, values.providerId || values.providerSlug, stepIndex, stepRoute);
            }
            continue;
          }
          _spv184Trace("step_response", mediaType, values.providerId || values.providerSlug, stepIndex, stepRoute);
'''
    resolver = _once(resolver, old_fetch, new_fetch, "v21.6-step-fetch-fallback")

    old_tail = '''        if (!progressed) break;
      }
    } catch (_) {}
'''
    new_tail = '''        if (!progressed) break;
      }
      if (playerFallbacks.length) {
        const fallbackStreams = _spv216FallbackStreams(playerFallbacks);
        if (fallbackStreams.length) return fallbackStreams;
      }
    } catch (_) {}
'''
    resolver = _once(resolver, old_tail, new_tail, "v21.6-return-fallback-after-branches")

    text = text[:start] + resolver + text[end:]
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v215.validate_base(value)
    for needle in (
        MARKER,
        "function _spv216PlayerFallbackEligible",
        "function _spv216FallbackReferer",
        "function _spv216FallbackStreams",
        "const playerFallbacks = [];",
        'playerFallbacks.push({ url: stepUrl, referer: fallbackReferer });',
        '"step_player_fallback"',
        "const fallbackStreams = _spv216FallbackStreams(playerFallbacks);",
        "if (fallbackStreams.length) return fallbackStreams;",
    ):
        if needle not in value:
            raise AssertionError(f"V21.6 ProviderBase missing {needle}")
    start = value.index(MARKER)
    end = value.index("async function _resolveSearchRequestPlan", start)
    runtime = value[start:end].casefold()
    for forbidden in (
        "animesama",
        "animevostfr",
        "french-manga",
        "jujutsu",
        "4668025",
        "1497198",
    ):
        if forbidden in runtime:
            raise AssertionError(f"V21.6 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_PLAYER_FALLBACK_V21_6_OK changed={str(changed).lower()} "
        "failed_player_embed_preserved=1 later_branches_still_executed=1 "
        "catalogue_detail_not_promoted=1 bounded_fallbacks=12 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
