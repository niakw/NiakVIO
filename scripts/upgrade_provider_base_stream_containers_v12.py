#!/usr/bin/env python3
"""Preserve explicit resolver stream containers and proven playback context.

Some resolver APIs return media URLs under plural source containers such as
`stream_urls`, `streams`, or `sources`. ProviderBase previously understood only
singular scalar stream/url/source fields, so a proven HTTP 200 resolver response
could still collapse to zero reconstructed streams.

This migration adds only bounded, explicitly named source containers; it does not
scan arbitrary HTTP strings from JSON. For typed movie/episode resolver routes it
also reuses a small safe subset of the already-proven request headers as playback
context: Origin, Referer, User-Agent and Accept-Language. Sensitive headers are not
captured or exposed.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_STREAM_CONTAINERS_V12"


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

    old_source = '''function _sourceUrls(value, base, out) {
  out = out || [];
  if (Array.isArray(value)) {
    for (const child of value) _sourceUrls(child, base, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  for (const [key, child] of Object.entries(value)) {
    if (typeof child === "string" && /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key)) {
      const absolute = _absolute(child, base);
      if (absolute && /^https?:/i.test(absolute) &&
          !/\\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) {
        out.push(absolute);
      }
    }
    if (child && typeof child === "object") _sourceUrls(child, base, out);
  }
  return out;
}
'''
    new_source = '''/* NIAKVIO_PROVIDER_BASE_STREAM_CONTAINERS_V12 */
function _sourceUrls(value, base, out, streamContainer) {
  out = out || [];
  if (typeof value === "string") {
    if (streamContainer) {
      const absolute = _absolute(value, base);
      if (absolute && /^https?:/i.test(absolute) &&
          !/\\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) out.push(absolute);
    }
    return out;
  }
  if (Array.isArray(value)) {
    for (const child of value.slice(0, 80)) _sourceUrls(child, base, out, streamContainer);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  for (const [key, child] of Object.entries(value)) {
    const directField = /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key);
    const pluralStreamContainer = /^(?:streams?|stream_urls?|streamUrls?|sources?|source_urls?|sourceUrls?)$/i.test(key);
    if (typeof child === "string" && directField) {
      const absolute = _absolute(child, base);
      if (absolute && /^https?:/i.test(absolute) &&
          !/\\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) {
        out.push(absolute);
      }
    }
    if (child && typeof child === "object") {
      _sourceUrls(child, base, out, Boolean(streamContainer || pluralStreamContainer));
    }
  }
  return out;
}
'''
    text = once(text, old_source, new_source, "source-url-stream-containers")

    playback_anchor = '''function _recipeSourceUrls(value, base, recipe) {
  const urls = _sourceUrls(value, base);
  if (!recipe || !recipe.directSourcesOnly) return urls;
  return urls.filter(_directMedia);
}
'''
    playback_helper = playback_anchor + '''function _recipePlaybackContext(recipe, requestSpec, base) {
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
    text = once(text, playback_anchor, playback_helper, "resolver-playback-context-helper")

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
        raise AssertionError(f"stream container marker count={value.count(MARKER)}")
    for needle in (
        "function _sourceUrls(value, base, out, streamContainer)",
        "value.slice(0, 80)",
        "pluralStreamContainer",
        "/^(?:streams?|stream_urls?|streamUrls?|sources?|source_urls?|sourceUrls?)$/i",
        "Boolean(streamContainer || pluralStreamContainer)",
        "function _recipePlaybackContext(recipe, requestSpec, base)",
        'lower["origin"]',
        'lower["referer"]',
        'lower["user-agent"]',
        'lower["accept-language"]',
        "const requestSpec = _recipeRequestSpec(recipe, requestKey, values);",
        "const playback = _recipePlaybackContext(recipe, requestSpec, base);",
        "playback.referer",
        "playback.headers",
    ):
        if needle not in value:
            raise AssertionError(f"stream container runtime missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_BASE_STREAM_CONTAINERS_V12_OK changed={str(changed).lower()} "
        "plural_stream_containers=1 bounded_items=80 arbitrary_http_strings=0 "
        "playback_context=origin,referer,user-agent,accept-language"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
