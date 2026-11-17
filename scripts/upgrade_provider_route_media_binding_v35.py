#!/usr/bin/env python3
"""V35: bind learned ProviderBase routes to canonical media and real player patterns.

The V34 query discriminator protected only API routes. A mixed route plan such
as /play/movie/{tmdbId}, /play/tv/{tmdbId}/{season}/{episode},
and /anime/{tmdbId} could therefore execute the anime detail route for movie/tv
requests, while the real /play/... player routes were ignored by the hard-coded
/player fast path.

V35 is generic and proof-neutral:
- strong path/query media namespaces filter every learned route kind;
- discovered player/play patterns are expanded from Provider DATA;
- the legacy bare /player?id=... fallback remains for providers that actually
  declare a bare /player route;
- no route proof, provider health or publication authority is manufactured.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_ROUTE_MEDIA_BINDING_V35"


def function_span(text: str, name: str) -> tuple[int, int]:
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        raise AssertionError(f"missing JS function {name}")
    start = match.start()
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote = ""
    escaped = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch in "\r\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
        else:
            if ch in "'\"`":
                quote = ch
            elif ch == "/" and nxt == "/":
                line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                block_comment = True
                i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    raise AssertionError(f"unterminated JS function {name}")


def replace_function(text: str, name: str, replacement: str) -> str:
    start, end = function_span(text, name)
    return text[:start] + replacement.strip() + text[end:]


ROUTE_HELPER = r'''
function _spv35RoutePathMedia(route) {
  let path = _text(route).split(/[?#]/, 1)[0];
  try {
    if (/^https?:\/\//i.test(_text(route))) path = new URL(_text(route)).pathname || "";
    path = decodeURIComponent(path);
  } catch (_) {}
  const observed = new Set();
  for (const segment of _text(path).toLowerCase().split("/").filter(Boolean)) {
    if (/^animes?$/.test(segment)) observed.add("anime");
    else if (/^movies?$/.test(segment)) observed.add("movie");
    else if (segment === "tv") observed.add("tv");
  }
  return observed.size === 1 ? Array.from(observed)[0] : "";
}
function _spv34RouteMediaCompatible(route, mediaType) {
  /* NIAKVIO_PROVIDER_ROUTE_MEDIA_BINDING_V35 */
  const desired = _mediaNamespace(mediaType);
  const source = _text(route);
  const queryMatch = source.match(/(?:[?&](?:type|media|m)=)(movie|tv|series|anime)(?=&|#|$)/i);
  if (queryMatch) {
    let actual = _text(queryMatch[1]).toLowerCase();
    if (actual === "series") actual = "tv";
    return actual === desired;
  }

  const actual = _spv35RoutePathMedia(route);
  if (!actual) return true;
  const planTypes = new Set(
    (NIAKVIO_PROVIDER_MODEL.routes || [])
      .map(_spv35RoutePathMedia)
      .filter(Boolean)
  );
  if (planTypes.size < 2) return true;
  return actual === desired;
}
'''

DIRECT_PLAYER = r'''
function _directPlayerUrls(tmdbId, mediaType, season, episode) {
  if (!tmdbId || !_identityUsesTmdbId()) return [];
  const out = _learnedUrls(
    "player",
    { tmdbId: _text(tmdbId), title: "" },
    mediaType,
    season,
    episode
  );

  // Preserve the historical /player?m=...&id=... convention only when the
  // provider explicitly declares the bare /player route. Typed discovered
  // /play/... or /embed/... patterns above are consumed exactly as DATA.
  const hasBarePlayerRoute = (NIAKVIO_PROVIDER_MODEL.routes || []).some(route =>
    /^\/player(?:[?#]|$)/i.test(_text(route))
  );
  if (hasBarePlayerRoute) {
    const transportType = _mediaNamespace(mediaType);
    for (const base of _searchBases()) {
      try {
        const parsed = new URL("/player", base);
        out.push(
          parsed.origin + parsed.pathname
          + "?m=" + encodeURIComponent(transportType)
          + "&id=" + encodeURIComponent(_text(tmdbId))
        );
      } catch (_) {}
    }
  }
  return _uniq(out);
}
'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    before = text
    if MARKER in text:
        validate(text)
        return False

    text = replace_function(text, "_spv34RouteMediaCompatible", ROUTE_HELPER)
    old_gate = 'if (kind === "api" && !_spv34RouteMediaCompatible(route, mediaType)) continue;'
    new_gate = 'if (!_spv34RouteMediaCompatible(route, mediaType)) continue;'
    if text.count(old_gate) != 1:
        raise AssertionError("V35 expected one V34 API-only media gate")
    text = text.replace(old_gate, new_gate, 1)

    text = replace_function(text, "_directPlayerUrls", DIRECT_PLAYER)
    old_known = "const known = _directPlayerUrls(tmdbId, mediaType).slice(0, 2);"
    new_known = "const known = _directPlayerUrls(tmdbId, mediaType, season, episode).slice(0, 2);"
    if text.count(old_known) != 1:
        raise AssertionError("V35 known-player call anchor mismatch")
    text = text.replace(old_known, new_known, 1)

    old_nested = "..._directPlayerUrls(meta.tmdbId, mediaType)"
    new_nested = "..._directPlayerUrls(meta.tmdbId, mediaType, season, episode)"
    if text.count(old_nested) != 1:
        raise AssertionError("V35 nested-player call anchor mismatch")
    text = text.replace(old_nested, new_nested, 1)

    validate(text)
    if text != before:
        TARGET.write_text(text, encoding="utf-8")
        return True
    return False


def validate(text: str | None = None) -> None:
    source = text if text is not None else TARGET.read_text(encoding="utf-8")
    if source.count(MARKER) != 1:
        raise AssertionError(f"V35 marker cardinality invalid: {source.count(MARKER)}")
    if source.count("function _spv34RouteMediaCompatible(route, mediaType) {") != 1:
        raise AssertionError("V35 must strengthen the unique V34 compatibility helper")
    if 'if (!_spv34RouteMediaCompatible(route, mediaType)) continue;' not in source:
        raise AssertionError("V35 media gate must apply to every learned route kind")
    for token in (
        'function _spv35RoutePathMedia(route) {',
        '/^animes?$/',
        '/^movies?$/',
        'segment === "tv"',
        'if (planTypes.size < 2) return true;',
        'const out = _learnedUrls(',
        '"player",',
        'const known = _directPlayerUrls(tmdbId, mediaType, season, episode).slice(0, 2);',
        '..._directPlayerUrls(meta.tmdbId, mediaType, season, episode)',
    ):
        if token not in source:
            raise AssertionError(f"V35 ProviderBase contract missing: {token}")
    if 'if (kind === "api" && !_spv34RouteMediaCompatible(route, mediaType)) continue;' in source:
        raise AssertionError("V35 retained API-only media compatibility")
    if source.count("function _directPlayerUrls(tmdbId, mediaType, season, episode) {") != 1:
        raise AssertionError("V35 direct-player helper signature mismatch")


def main() -> int:
    changed = patch()
    validate()
    print(f"PROVIDER_ROUTE_MEDIA_BINDING_V35_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
