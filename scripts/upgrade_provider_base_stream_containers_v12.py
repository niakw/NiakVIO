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


def replace_block(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_at = text.find(start)
    if start_at < 0:
        raise AssertionError(f"{label}: start anchor missing")
    end_at = text.find(end, start_at + len(start))
    if end_at < 0:
        raise AssertionError(f"{label}: end anchor missing")
    return text[:start_at] + replacement + text[end_at:]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

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
    text = replace_block(
        text,
        "function _sourceUrls(value, base, out) {",
        "function _rewriteOutputUrl(raw) {",
        new_source,
        "source-url-stream-containers",
    )

    source_helper_start = "function _recipeSourceUrls(value, base, recipe) {"
    source_helper_end = "function _recipeUrl(pattern, values, base) {"
    start_at = text.find(source_helper_start)
    end_at = text.find(source_helper_end, start_at + len(source_helper_start)) if start_at >= 0 else -1
    if start_at < 0 or end_at < 0:
        raise AssertionError("resolver-playback-context-helper: anchors missing")
    existing_source_helper = text[start_at:end_at]
    playback_helper = existing_source_helper + '''function _recipePlaybackContext(recipe, requestSpec, base) {
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
    text = text[:start_at] + playback_helper + text[end_at:]

    resolve_start = text.find("async function resolveRoute(baseList) {")
    resolve_end = text.find("const routeBases = _uniq([providerMatch.base, ...bases]);", resolve_start)
    if resolve_start < 0 or resolve_end < 0:
        raise AssertionError("typed-route-playback-context: resolveRoute anchors missing")
    segment = text[resolve_start:resolve_end]
    segment = replace_once(
        segment,
        'const requestKey = media === "movie" ? "movieRequest" : "episodeRequest";\n      const payload = await _recipePayload(url, recipe, _recipeRequestSpec(recipe, requestKey, values), values);',
        'const requestKey = media === "movie" ? "movieRequest" : "episodeRequest";\n      const requestSpec = _recipeRequestSpec(recipe, requestKey, values);\n      const payload = await _recipePayload(url, recipe, requestSpec, values);\n      const playback = _recipePlaybackContext(recipe, requestSpec, base);',
        "typed-route-request-playback-context",
    )
    old_stream_context = '''recipe.referer || base,
          Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})'''
    count = segment.count(old_stream_context)
    if count != 2:
        raise AssertionError(f"typed-route-stream-context: expected 2 anchors, got {count}")
    segment = segment.replace(old_stream_context, "playback.referer,\n          playback.headers")
    text = text[:resolve_start] + segment + text[resolve_end:]

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
