#!/usr/bin/env python3
"""Teach the common ProviderBase how to execute signed-player-api families.

The family contract is data-driven: a deterministic detail route is addressed by
TMDB id + slug, the detail page exposes a short-lived signed /player URL, and that
exact player dataflow owns the downstream /api/streams request. No provider-specific
secret or upstream JavaScript is embedded here.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_SIGNED_PLAYER_API_RUNTIME_V1"


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

    old_details = '''    for (const route of detailRoutes) {
      if (!/\\{slug\\}/i.test(route) || /\\{id\\}/i.test(route)) continue;
      out.push(..._spv4Expand(route, Object.assign({}, meta, { title }), { slug }, mediaType, season, episode));
    }
'''
    new_details = '''    for (const route of detailRoutes) {
      const signedTmdbDetail = family === "signed-player-api" &&
        /\\{slug\\}/i.test(route) && /\\{id\\}/i.test(route) &&
        /\\/title\\/(?:movie|tv)\\//i.test(route);
      if (signedTmdbDetail) {
        const wantsMovie = /\\/title\\/movie\\//i.test(route);
        if ((mediaType === "movie") !== wantsMovie) continue;
        const tmdbId = _text(meta && meta.tmdbId).trim();
        if (!tmdbId) continue;
        out.push(..._spv4Expand(
          route,
          Object.assign({}, meta, { title }),
          { slug, providerId: tmdbId },
          mediaType,
          season,
          episode
        ));
        continue;
      }
      if (!/\\{slug\\}/i.test(route) || /\\{id\\}/i.test(route)) continue;
      out.push(..._spv4Expand(route, Object.assign({}, meta, { title }), { slug }, mediaType, season, episode));
    }
'''
    text = once(text, old_details, new_details, "signed-detail-tmdb-id")

    old_resolve = '''  if (family === "dle-film-api") {
    const special = await _spv5DleFilmApi(base, html, meta, mediaType, season, episode);
    if (special.length) return special;
  }

  let urls = _spv4AttrUrls(html, base);
'''
    new_resolve = '''  if (family === "dle-film-api") {
    const special = await _spv5DleFilmApi(base, html, meta, mediaType, season, episode);
    if (special.length) return special;
  }
  /* NIAKVIO_SIGNED_PLAYER_API_RUNTIME_V1 */
  if (family === "signed-player-api") {
    const signedPlayers = _spv4AttrUrls(html, base)
      .filter(_spv4SameProviderOrigin)
      .filter(url => {
        try {
          const parsed = new URL(url);
          if (!/\\/player(?:[/?#.-]|$)/i.test(parsed.pathname)) return false;
          const id = _text(parsed.searchParams && parsed.searchParams.get("id")).trim();
          const key = _text(parsed.searchParams && (parsed.searchParams.get("k") || parsed.searchParams.get("key"))).trim();
          return !!id && !!key;
        } catch (_) { return false; }
      });
    if (signedPlayers.length) {
      const runtime = await _resolveRuntimeApi(
        signedPlayers.slice(0, 4),
        mediaType,
        meta && meta.tmdbId,
        season,
        episode
      );
      if (runtime.length) return runtime;
    }
  }

  let urls = _spv4AttrUrls(html, base);
'''
    text = once(text, old_resolve, new_resolve, "signed-player-runtime-api")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"signed-player runtime marker count={value.count(MARKER)}")
    for needle in (
        'family === "signed-player-api"',
        'const signedTmdbDetail = family === "signed-player-api"',
        '{ slug, providerId: tmdbId }',
        'const signedPlayers = _spv4AttrUrls(html, base)',
        'const runtime = await _resolveRuntimeApi(',
        'parsed.searchParams.get("k")',
    ):
        if needle not in value:
            raise AssertionError(f"signed-player runtime missing: {needle}")


def main() -> int:
    changed = patch()
    print(f"SIGNED_PLAYER_API_RUNTIME_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
