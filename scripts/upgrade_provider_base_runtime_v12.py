#!/usr/bin/env python3
"""Preserve typed-resolver response shapes and playback request context.

Proof-v5 resolver APIs may return media URLs as arrays under explicit source
containers (for example `data.stream_urls`). ProviderBase previously ignored
scalar strings nested in such arrays, so a proven HTTP 200 resolver response could
still collapse to zero reconstructed streams.

This migration adds only bounded source-container extraction and reuses a small,
safe subset of the already-proven request headers (Origin/Referer/User-Agent/
Accept-Language) as playback context. It does not scan arbitrary JSON strings and
does not expose sensitive headers.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_RESOLVER_RESPONSE_V12"


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

    source_anchor = '''  for (const [key, child] of Object.entries(value)) {
    if (typeof child === "string" && /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key)) {
'''
    source_replacement = '''  for (const [key, child] of Object.entries(value)) {
    /* NIAKVIO_PROVIDER_BASE_RESOLVER_RESPONSE_V12 */
    if (Array.isArray(child) && /^(?:streams?|stream_urls?|streamUrls?|sources?|source_urls?|sourceUrls?)$/i.test(key)) {
      for (const item of child.slice(0, 80)) {
        if (typeof item === "string") {
          const absolute = _absolute(item, base);
          if (absolute && /^https?:/i.test(absolute) &&
              !/\\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) {
            out.push(absolute);
          }
        } else if (item && typeof item === "object") {
          _sourceUrls(item, base, out);
        }
      }
    }
    if (typeof child === "string" && /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key)) {
'''
    text = once(text, source_anchor, source_replacement, "plural-source-container")

    playback_anchor = '''function _recipeSourceUrls(value, base, recipe) {
  const urls = _sourceUrls(value, base);
  if (!recipe || !recipe.directSourcesOnly) return urls;
  return urls.filter(_directMedia);
}
'''
    playback_replacement = playback_anchor + '''function _recipePlaybackContext(recipe, requestSpec, base) {
  const raw = requestSpec && requestSpec.headers && typeof requestSpec.headers === "object"
    ? requestSpec.headers
    : {};
  const lower = {};
  for (const [key, value] of Object.entries(raw)) lower[_text(key).toLowerCase()] = _text(value);
  const headers = {};
  if (lower["origin"]) headers.Origin = lower["origin"];
  if (lower["user-agent"]) headers["User-Agent"] = lower["user-agent"];
  if (lower["accept-language"]) headers["Accept-Language"] = lower["accept-language"];
  const explicit = recipe && recipe.playbackHeaders && typeof recipe.playbackHeaders === "object"
    ? recipe.playbackHeaders
    : {};
  for (const [key, value] of Object.entries(explicit)) {
    if (!/^(?:origin|referer|referrer|user-agent|accept-language)$/i.test(_text(key))) continue;
    if (/^(?:referer|referrer)$/i.test(_text(key))) continue;
    headers[key] = _text(value);
  }
  if (recipe && recipe.origin) headers.Origin = _text(recipe.origin);
  const referer = _text(
    (recipe && recipe.referer)
    || lower["referer"]
    || lower["referrer"]
    || base
  );
  return { referer, headers };
}
'''
    text = once(text, playback_anchor, playback_replacement, "playback-context-helper")

    old_resolve = '''        const requestKey = media === "movie" ? "movieRequest" : "episodeRequest";
        const payload = await _recipePayload(url, recipe, _recipeRequestSpec(recipe, requestKey, values), values);
        if (typeof payload.value === "string") {
          const urls = _extractUrls(payload.value, payload.base).filter(_directMedia);
          if (urls.length) return _streams(
            urls,
            recipe.referer || base,
            Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
          );
        } else {
          const urls = _recipeSourceUrls(payload.value, payload.base, recipe);
          if (urls.length) return _streams(
            urls,
            recipe.referer || base,
            Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
          );
        }
'''
    new_resolve = '''        const requestKey = media === "movie" ? "movieRequest" : "episodeRequest";
        const requestSpec = _recipeRequestSpec(recipe, requestKey, values);
        const payload = await _recipePayload(url, recipe, requestSpec, values);
        const playback = _recipePlaybackContext(recipe, requestSpec, base);
        if (typeof payload.value === "string") {
          const urls = _extractUrls(payload.value, payload.base).filter(_directMedia);
          if (urls.length) return _streams(
            urls,
            playback.referer,
            playback.headers
          );
        } else {
          const urls = _recipeSourceUrls(payload.value, payload.base, recipe);
          if (urls.length) return _streams(
            urls,
            playback.referer,
            playback.headers
          );
        }
'''
    text = once(text, old_resolve, new_resolve, "typed-route-playback-context")

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"resolver response marker count={value.count(MARKER)}")
    required = (
        'Array.isArray(child) && /^(?:streams?|stream_urls?|streamUrls?|sources?|source_urls?|sourceUrls?)$/i.test(key)',
        'child.slice(0, 80)',
        'function _recipePlaybackContext(recipe, requestSpec, base)',
        'lower["origin"]',
        'lower["referer"]',
        'lower["user-agent"]',
        'lower["accept-language"]',
        'const requestSpec = _recipeRequestSpec(recipe, requestKey, values);',
        'const playback = _recipePlaybackContext(recipe, requestSpec, base);',
        'playback.referer',
        'playback.headers',
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"resolver response runtime missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_BASE_RUNTIME_V12_OK changed={str(changed).lower()} "
        "plural_source_arrays=1 bounded_items=80 arbitrary_json_strings=0 "
        "playback_request_context=origin,referer,user-agent,accept-language"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
