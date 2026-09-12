#!/usr/bin/env python3
"""V22.1: fail closed when an episodic catalogue page points at another episode.

The common ProviderBase already prefers explicit episode hops, but a page containing
an episode table could fall through to generic player/embed extraction when the
requested episode was absent or the exact hop failed. That can surface streams from
another episode. This upgrade keeps the rule provider-agnostic: explicit season /
episode evidence in the detail URL or same-origin episode links is authoritative.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_EPISODE_IDENTITY_GUARD_V22_1"

HELPER = r'''/* NIAKVIO_PROVIDER_EPISODE_IDENTITY_GUARD_V22_1 */
function _spv221EpisodeTableState(html, base, season, episode) {
  const source = _embeddedText(html).slice(0, 1048576);
  let baseUrl;
  try { baseUrl = new URL(_text(base)); } catch (_) { return { marked: false, matches: false }; }
  const re = /\b(?:href|data-href|data-url|data-link)\s*=\s*(["'])([^"']{1,1200})\1/gi;
  let match, scanned = 0, marked = false, matches = false;
  while ((match = re.exec(source)) !== null && scanned++ < 700) {
    const absolute = _absolute(match[2], baseUrl.toString());
    if (!absolute) continue;
    let parsed;
    try { parsed = new URL(absolute); } catch (_) { continue; }
    if (parsed.origin !== baseUrl.origin || !/^https?:$/i.test(parsed.protocol)) continue;
    const marker = _spv22EpisodeMarker(parsed.toString(), season, episode);
    if (!marker.marked) continue;
    marked = true;
    if (marker.matches) matches = true;
    if (matches) break;
  }
  return { marked, matches };
}
'''


def patch() -> bool:
    text = BASE.read_text(encoding="utf-8")
    changed = False

    old_path = '  try { path = decodeURIComponent(new URL(_text(rawUrl)).pathname || "").toLowerCase(); }\n'
    new_path = '  try { const parsed = new URL(_text(rawUrl)); path = decodeURIComponent((parsed.pathname || "") + (parsed.search || "")).toLowerCase(); }\n'
    if new_path not in text:
        if text.count(old_path) != 1:
            raise AssertionError(f"episode marker URL anchor count={text.count(old_path)}")
        text = text.replace(old_path, new_path, 1)
        changed = True

    first_pattern = '  const patterns = [\n    { re: /(?:^|[-_/])s(?:eason|aison)?[-_ ]*0*(\\d{1,3})[-_ /]*(?:e|ep|episode)[-_ ]*0*(\\d{1,4})(?:[-_/.]|$)/i, strength: 4 },\n'
    query_patterns = '  const patterns = [\n    { re: /[?&](?:season|s)=0*(\\d{1,3})[^#]{0,120}?[&](?:episode|ep|e)=0*(\\d{1,4})(?:[&#]|$)/i, strength: 5 },\n    { re: /[?&](?:episode|ep|e)=0*(\\d{1,4})[^#]{0,120}?[&](?:season|s)=0*(\\d{1,3})(?:[&#]|$)/i, strength: 5, reversed: true },\n    { re: /(?:^|[-_/])s(?:eason|aison)?[-_ ]*0*(\\d{1,3})[-_ /]*(?:e|ep|episode)[-_ ]*0*(\\d{1,4})(?:[-_/.]|$)/i, strength: 4 },\n'
    if query_patterns not in text:
        if text.count(first_pattern) != 1:
            raise AssertionError(f"episode marker patterns anchor count={text.count(first_pattern)}")
        text = text.replace(first_pattern, query_patterns, 1)
        changed = True

    old_compare = '''    return {
      marked: true,
      matches: Number(match[1]) === wantedSeason && Number(match[2]) === wantedEpisode,
      strength: row.strength
    };
'''
    new_compare = '''    const actualSeason = row.reversed ? Number(match[2]) : Number(match[1]);
    const actualEpisode = row.reversed ? Number(match[1]) : Number(match[2]);
    return {
      marked: true,
      matches: actualSeason === wantedSeason && actualEpisode === wantedEpisode,
      strength: row.strength
    };
'''
    if new_compare not in text:
        if text.count(old_compare) != 1:
            raise AssertionError(f"episode marker comparison anchor count={text.count(old_compare)}")
        text = text.replace(old_compare, new_compare, 1)
        changed = True

    episode_links_anchor = "function _spv22EpisodeLinks(html, base, season, episode) {\n"
    if MARKER not in text:
        if text.count(episode_links_anchor) != 1:
            raise AssertionError(f"episode links anchor count={text.count(episode_links_anchor)}")
        text = text.replace(episode_links_anchor, HELPER + episode_links_anchor, 1)
        changed = True

    old_flow = '''      const episodeHop = await _spv22ResolveEpisodeHop(html, response.url || detailUrl, mediaType, season, episode);
      if (episodeHop.length) return episodeHop.slice(0, 40);
      const explicitPlayers = _spv15ExplicitPlayerAttrs(html, response.url || detailUrl);
'''
    new_flow = '''      const resolvedDetailUrl = response.url || detailUrl;
      const detailEpisodeMarker = _spv22EpisodeMarker(resolvedDetailUrl, season, episode);
      if (mediaType !== "movie" && season != null && episode != null && detailEpisodeMarker.marked && !detailEpisodeMarker.matches) continue;
      const episodeTableState = mediaType !== "movie" && season != null && episode != null
        ? _spv221EpisodeTableState(html, resolvedDetailUrl, season, episode)
        : { marked: false, matches: false };
      if (episodeTableState.marked && !episodeTableState.matches && !(detailEpisodeMarker.marked && detailEpisodeMarker.matches)) continue;
      const episodeHop = await _spv22ResolveEpisodeHop(html, resolvedDetailUrl, mediaType, season, episode);
      if (episodeHop.length) return episodeHop.slice(0, 40);
      if (episodeTableState.marked && !(detailEpisodeMarker.marked && detailEpisodeMarker.matches)) continue;
      const explicitPlayers = _spv15ExplicitPlayerAttrs(html, resolvedDetailUrl);
'''
    if new_flow not in text:
        if text.count(old_flow) != 1:
            raise AssertionError(f"resolveHtml episode flow anchor count={text.count(old_flow)}")
        text = text.replace(old_flow, new_flow, 1)
        changed = True

    if changed:
        BASE.write_text(text, encoding="utf-8")
    validate(text)
    return changed


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    required = (
        MARKER,
        "function _spv221EpisodeTableState(html, base, season, episode)",
        "detailEpisodeMarker.marked && !detailEpisodeMarker.matches",
        "episodeTableState.marked && !episodeTableState.matches",
        "episodeTableState.marked && !(detailEpisodeMarker.marked && detailEpisodeMarker.matches)",
        "(parsed.pathname || \"\") + (parsed.search || \"\")",
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"episode identity guard missing {needle}")
    window = value[value.index(MARKER):value.index("async function _resolveApiRecipe", value.index(MARKER))]
    lowered = window.casefold()
    for forbidden in ("mugiwara", "hellmode", "mushoku", "streamzo", "interstellar"):
        if forbidden in lowered:
            raise AssertionError(f"provider/fixture-specific token leaked into generic episode guard: {forbidden}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_EPISODE_IDENTITY_GUARD_V22_1_OK "
        f"changed={str(changed).lower()} query_episode_markers=1 fail_closed_table=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
