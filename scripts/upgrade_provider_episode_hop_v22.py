#!/usr/bin/env python3
"""Add a generic catalogue/detail -> requested episode -> player hop to ProviderBase.

Some HTML catalogue families expose the work page first, then the requested
season/episode page, then iframe/player URLs. The generic player crawler must not
follow every episode in a catalogue, so this bridge only follows same-origin URLs
whose path proves the requested S/E (or episode-only when the requested season is
1), then hands the resulting player URLs back to the existing bounded crawler.

No provider, host, title or fixture is encoded here.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_EPISODE_HOP_V22"

HELPER_ANCHOR = 'async function _resolveHtml(meta, mediaType, season, episode) {\n'
HELPERS = r'''/* NIAKVIO_PROVIDER_EPISODE_HOP_V22 */
function _spv22EpisodeMarker(rawUrl, season, episode) {
  let path = "";
  try { path = decodeURIComponent(new URL(_text(rawUrl)).pathname || "").toLowerCase(); }
  catch (_) { return { marked: false, matches: false, strength: 0 }; }
  const wantedSeason = Math.max(1, Number(season) || 1);
  const wantedEpisode = Math.max(1, Number(episode) || 1);
  const patterns = [
    { re: /(?:^|[-_/])s(?:eason|aison)?[-_ ]*0*(\d{1,3})[-_ /]*(?:e|ep|episode)[-_ ]*0*(\d{1,4})(?:[-_/.]|$)/i, strength: 4 },
    { re: /(?:season|saison)[-_ /]*0*(\d{1,3})[^?#]{0,80}?(?:episode|ep)[-_ /]*0*(\d{1,4})(?:[-_/.]|$)/i, strength: 4 },
    { re: /(?:^|[-_/])0*(\d{1,3})x0*(\d{1,4})(?:[-_/.]|$)/i, strength: 4 },
    { re: /(?:^|[-_/])0*(\d{1,3})[-_ ]*episode[-_ ]*0*(\d{1,4})(?:[-_/.]|$)/i, strength: 4 }
  ];
  for (const row of patterns) {
    const match = path.match(row.re);
    if (!match) continue;
    return {
      marked: true,
      matches: Number(match[1]) === wantedSeason && Number(match[2]) === wantedEpisode,
      strength: row.strength
    };
  }
  const ep = path.match(/(?:^|[-_/])(?:episode|ep)[-_ ]*0*(\d{1,4})(?:[-_/.]|$)/i);
  if (ep) return {
    marked: true,
    matches: wantedSeason === 1 && Number(ep[1]) === wantedEpisode,
    strength: 2
  };
  return { marked: false, matches: false, strength: 0 };
}
function _spv22EpisodeLinks(html, base, season, episode) {
  const source = _embeddedText(html).slice(0, 1048576);
  const out = [];
  let baseUrl;
  try { baseUrl = new URL(_text(base)); } catch (_) { return []; }
  const re = /\b(?:href|data-href|data-url|data-link)\s*=\s*(["'])([^"']{1,1200})\1/gi;
  let match, scanned = 0;
  while ((match = re.exec(source)) !== null && scanned++ < 700) {
    const absolute = _absolute(match[2], baseUrl.toString());
    if (!absolute) continue;
    let parsed;
    try { parsed = new URL(absolute); } catch (_) { continue; }
    if (parsed.origin !== baseUrl.origin) continue;
    if (!/^https?:$/i.test(parsed.protocol)) continue;
    if (/\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(parsed.pathname)) continue;
    const marker = _spv22EpisodeMarker(parsed.toString(), season, episode);
    if (!marker.marked || !marker.matches) continue;
    out.push({ url: parsed.toString(), strength: marker.strength });
    if (out.length >= 16) break;
  }
  const seen = new Set();
  return out
    .sort((a,b)=>b.strength-a.strength)
    .filter(row => row.url && !seen.has(row.url) && seen.add(row.url))
    .map(row => row.url)
    .slice(0, 4);
}
async function _spv22ResolveEpisodeHop(html, detailUrl, mediaType, season, episode) {
  if (_text(mediaType).toLowerCase() === "movie" || season == null || episode == null) return [];
  const episodeLinks = _spv22EpisodeLinks(html, detailUrl, season, episode);
  if (!episodeLinks.length) return [];
  const fallbacks = [];
  for (const episodeUrl of episodeLinks.slice(0, 3)) {
    try {
      const response = await _fetch(episodeUrl, { headers: { Referer: _text(detailUrl) } });
      const responseUrl = _text(response.url || episodeUrl);
      const body = await response.text();
      const candidates = _uniq([
        ..._spv15ExplicitPlayerAttrs(body, responseUrl),
        ..._extractUrls(body, responseUrl)
      ]);
      const direct = candidates.filter(_directMedia);
      if (direct.length) return _streams(direct, responseUrl).slice(0, 40);
      const players = candidates
        .filter(_crawlEligible)
        .sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a))
        .slice(0, 10);
      if (!players.length) continue;
      const crawled = await _crawlDirectMedia(players, responseUrl, 3);
      if (crawled.length) return crawled.slice(0, 40);
      for (const candidate of players) {
        if (_directMedia(candidate) || !_spv216PlayerFallbackEligible(candidate)) continue;
        if (!fallbacks.some(row => row.url === candidate)) fallbacks.push({ url: candidate, referer: responseUrl });
      }
    } catch (_) {}
  }
  return _spv216FallbackStreams(fallbacks).slice(0, 12);
}
'''

DETAIL_ANCHOR = '''      const html = await response.text();\n      if (!_strictHtmlIdentityOk(html, meta, mediaType)) continue;\n      const explicitPlayers = _spv15ExplicitPlayerAttrs(html, response.url || detailUrl);\n'''
DETAIL_REPLACEMENT = '''      const html = await response.text();\n      if (!_strictHtmlIdentityOk(html, meta, mediaType)) continue;\n      const episodeHop = await _spv22ResolveEpisodeHop(html, response.url || detailUrl, mediaType, season, episode);\n      if (episodeHop.length) return episodeHop.slice(0, 40);\n      const explicitPlayers = _spv15ExplicitPlayerAttrs(html, response.url || detailUrl);\n'''

PROVIDER_VALUE_ANCHOR = '''        const direct = urls.filter(_directMedia);\n        if (direct.length) return _streams(direct, payload.base || stepUrl).slice(0, 40);\n        const crawl = urls.filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a));\n'''
PROVIDER_VALUE_REPLACEMENT = '''        const direct = urls.filter(_directMedia);\n        if (direct.length) return _streams(direct, payload.base || stepUrl).slice(0, 40);\n        if (typeof scopedPayloadValue === "string") {\n          const episodeHop = await _spv22ResolveEpisodeHop(scopedPayloadValue, payload.base || stepUrl, mediaType, season, episode);\n          if (episodeHop.length) return episodeHop.slice(0, 40);\n        }\n        const crawl = urls.filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a));\n'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def validate(text: str) -> None:
    required = (
        MARKER,
        "function _spv22EpisodeMarker(rawUrl, season, episode)",
        "function _spv22EpisodeLinks(html, base, season, episode)",
        "async function _spv22ResolveEpisodeHop(html, detailUrl, mediaType, season, episode)",
        "parsed.origin !== baseUrl.origin",
        "wantedSeason === 1 && Number(ep[1]) === wantedEpisode",
        "const episodeHop = await _spv22ResolveEpisodeHop(html, response.url || detailUrl, mediaType, season, episode);",
        "const episodeHop = await _spv22ResolveEpisodeHop(scopedPayloadValue, payload.base || stepUrl, mediaType, season, episode);",
        "return _spv216FallbackStreams(fallbacks).slice(0, 12);",
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"episode hop missing: {needle}")
    section = text.split(f"/* {MARKER} */", 1)[1].split("async function _resolveHtml", 1)[0].casefold()
    for forbidden in ("voiranime", "wook", "mugiwara", "jujutsu", "breaking bad", "smoothpre", "lecteurvideo"):
        if forbidden in section:
            raise AssertionError(f"provider/fixture-specific token leaked into episode hop: {forbidden}")


def main() -> int:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        print("PROVIDER_EPISODE_HOP_V22_OK changed=false")
        return 0
    text = replace_once(text, HELPER_ANCHOR, HELPERS + HELPER_ANCHOR, "helper")
    text = replace_once(text, DETAIL_ANCHOR, DETAIL_REPLACEMENT, "detail integration")
    text = replace_once(text, PROVIDER_VALUE_ANCHOR, PROVIDER_VALUE_REPLACEMENT, "provider-value integration")
    validate(text)
    BASE.write_text(text, encoding="utf-8")
    print("PROVIDER_EPISODE_HOP_V22_OK changed=true same_origin=1 exact_episode=1 season_mismatch_rejected=1 provider_specific_rules=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
