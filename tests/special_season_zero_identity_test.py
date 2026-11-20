#!/usr/bin/env python3
"""Regression: specials S00 remain distinct from season 1, while unknown stays unknown."""
from __future__ import annotations
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("specials_core", ROOT / "scripts/provider_patches/global_stream_identity_v1.py")
assert spec and spec.loader
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

source = "module.exports={getStreams:async()=>ROWS};"
# 129261 is the TheTVDB series ID, not a TMDB TV ID. The real canonical
# TMDB series ID for Spartacus (2010) is 46296. Never conflate namespaces.
TMDB_SPARTACUS = "46296"
TVDB_SPARTACUS = "129261"
assert TMDB_SPARTACUS != TVDB_SPARTACUS
query = {"tmdbId": TMDB_SPARTACUS, "mediaType": "tv", "title": "Spartacus", "season": 0, "episode": 1}
rows = [
    {"title": "Spartacus S01E01", "url": "https://cdn.example/wrong-s1.m3u8"},
    {"title": "Spartacus S02E01", "url": "https://cdn.example/unverified-alternate-s2.m3u8"},
    {"name": "Spartacus", "season": 1, "episode": 1, "url": "https://cdn.example/wrong-structured.m3u8"},
    {"name": "Spartacus", "sourceUrl": "https://reader.example/watch?season=2&episode=1", "url": "https://cdn.example/wrong-reader.m3u8"},
    {"title": "Spartacus S00E01", "url": "https://cdn.example/Spartacus.S00E01.m3u8",
     "subtitles": [
         {"url": "https://subs.example/Spartacus.S00E01.fr.vtt", "language": "fr"},
         {"url": "https://subs.example/Spartacus.S03E01.fr.vtt", "language": "fr"},
         {"url": "https://subs.example/opaque-episode-attached.vtt", "language": "fr"},
         {"url": "https://subs.example/generic.vtt", "seasonNumber": 2, "episodeNumber": 1},
     ]},
    {"name": "Spartacus", "seasonNumber": 0, "episodeNumber": 1, "url": "https://cdn.example/correct-structured.m3u8"},
    {"name": "Spartacus S00E01", "seasonNumber": 0, "episodeNumber": 1, "url": "https://cdn.example/Spartacus.S03E01.m3u8"},
    {"name": "Spartacus S00E01", "seasonNumber": 0, "episodeNumber": 1, "url": "https://cdn.example/media.m3u8?season=3&episode=1"},
    {"name": "Spartacus S00E01", "seasonNumber": 0, "episodeNumber": 1, "sourceUrl": "https://reader.example/watch/S03E01", "url": "https://cdn.example/opaque-labelled.mp4"},
    {"name": "Spartacus S01E01", "seasonNumber": 1, "episodeNumber": 1, "url": "https://cdn.example/Spartacus.S02E01.m3u8"},
    {"title": "Spartacus S00E01", "url": "https://cdn.example/opaque-season3-mislabeled.m3u8"},
    {"name": "Server 1", "url": "https://cdn.example/opaque-unverified.m3u8"},
    {"name": "Server 2", "sourceUrl": "https://reader.example/watch?season=0&episode=1", "url": "https://cdn.example/correct-source-coordinate.m3u8"},
]
compiled = core.apply(source.replace("ROWS", json.dumps(rows)), context={"provider_id": "example"})
assert 'cross-client-player-page-identity-v20-url-path-consistency' in compiled
assert 'function exactSpecialEpisodeEvidence(row,q)' in compiled

runner = compiled + """
(async()=> {
  const assert=require('assert');
  const q=QUERY;
  const rows=await module.exports.getStreams(q);
  assert.deepEqual(rows.map(r=>r.url), [
    'https://cdn.example/Spartacus.S00E01.m3u8',
    'https://cdn.example/correct-structured.m3u8',
    'https://cdn.example/correct-source-coordinate.m3u8'
  ], JSON.stringify(rows));
  const s1=await module.exports.getStreams({...q,season:1});
  assert(s1.some(r=>r.url==='https://cdn.example/wrong-s1.m3u8'));
  assert(!s1.some(r=>r.url==='https://cdn.example/Spartacus.S00E01.m3u8'));
  const special=rows.find(r=>r.url==='https://cdn.example/Spartacus.S00E01.m3u8');
  assert.deepEqual(special.subtitles.map(r=>r.url),[
    'https://subs.example/Spartacus.S00E01.fr.vtt'
  ],'S00 special requires explicit caption season/episode identity; opaque or S03 must be rejected');
  assert(!rows.some(r=>r.url==='https://cdn.example/opaque-season3-mislabeled.m3u8'),
    'caller-derived S00 title must not authenticate an opaque S03 URL');
  for(const forbidden of [
    'https://cdn.example/Spartacus.S03E01.m3u8',
    'https://cdn.example/media.m3u8?season=3&episode=1',
    'https://cdn.example/opaque-labelled.mp4',
    'https://cdn.example/Spartacus.S02E01.m3u8'
  ])assert(!rows.some(r=>r.url===forbidden),
      'provider-declared S00 metadata must not override an explicit contrary media URL: '+forbidden);
  assert(!s1.some(r=>r.url==='https://cdn.example/Spartacus.S02E01.m3u8'),
    'S01 must also reject a file explicitly marked S02E01');
  const pos=await module.exports.getStreams(q.tmdbId,q.mediaType,0,1);
  assert.deepEqual(pos.map(r=>r.url), rows.map(r=>r.url));
})().catch(e=>{console.error(e);process.exit(1)});
""".replace("QUERY", json.dumps(query))
base = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
marker = base[base.index("function _spv22EpisodeMarker"):base.index("function _spv221EpisodeTableState")]
external = base[base.index("function _externalEpisodeMarker"):base.index("function _externalPlaybackHeaders")]
scoped = base[base.index("function _spv251SeasonNumber"):base.index("function _spv214EpisodeNumber")]
runner += """
function _text(value){return String(value==null?'':value);}
""" + marker + external + scoped + """
const assert=require('assert');
assert(_spv22EpisodeMarker('https://example.test/?season=0&episode=1',0,1).matches);
assert(!_spv22EpisodeMarker('https://example.test/?season=1&episode=1',0,1).matches);
assert(_spv22EpisodeMarker('https://example.test/s00e01',0,1).matches);
assert(!_spv22EpisodeMarker('https://example.test/s01e01',0,1).matches);
assert(_externalEpisodeMarker('https://example.test/s00e01',0,1).matches);
assert(!_externalEpisodeMarker('https://example.test/s01e01',0,1).matches);
const all=[{season:0,episodes:['special']},{season:1,episodes:['normal']},{season:2,episodes:['alternate']}];
const s0=_spv251SeasonEpisodeScopedValue(all,'tv',0,1,0);
assert.deepEqual(s0,[{season:0,episodes:['special']}]);
const s1=_spv251SeasonEpisodeScopedValue(all,'tv',1,1,0);
assert.deepEqual(s1,[{season:1,episodes:['normal']}]);
assert.deepEqual(_spv251SeasonEpisodeScopedValue(all,'tv',3,1,0),[]);
"""
assert "if (!chosen && wantedSeason === 0) continue;" in base, "missing S00-safe catalogue selection"
assert "cross-client-player-page-identity-v20-url-path-consistency" in (ROOT / "scripts/provider_patches/global_stream_identity_v1.py").read_text(encoding="utf-8")

with tempfile.TemporaryDirectory() as td:
    script = Path(td) / "specials.cjs"
    script.write_text(runner, encoding="utf-8")
    out = subprocess.run(["node", str(script)], text=True, capture_output=True, timeout=25)
    assert out.returncode == 0, out.stdout + out.stderr

# The generated Core wrapper rejects S00 streams with no exact episode evidence.
# Strict source tests above do not prove that old published bytes were rebuilt.
# A separate release gate must block shipping stale v17 wrappers until remat.

# The shared fix must exist in every *published* provider bundle, not just
# the source compiler or a hand-picked fixture. This is a static check only:
# alternate-catalogue episode equivalence and terminal playback need live proof.
def projection_rows(path: Path, nested: bool) -> list[dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for raw in doc.get("scrapers", []):
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        filename = str(row.get("filename") or "")
        if nested and filename.startswith("../"):
            filename = filename[3:]
        row["filename"] = filename
        out.append(row)
    return out

visible_by_id: dict[str, dict] = {}
for manifest_path, nested in ((ROOT / "manifest.json", False), (ROOT / "vf/manifest.json", True)):
    for row in projection_rows(manifest_path, nested):
        provider_id = str(row.get("id") or "").strip().casefold().replace("_", "-")
        assert provider_id
        previous = visible_by_id.get(provider_id)
        if previous is not None:
            assert previous == row, ("Global/VF S00 projection drift", provider_id)
        else:
            visible_by_id[provider_id] = row

visible = list(visible_by_id.values())
published = [row for row in visible if row.get("enabled") is not False]
disabled = [row for row in visible if row.get("enabled") is False]
assert published, "no active published providers"
seen_paths = set()
for row in disabled:
    filename = str(row.get("filename") or "")
    assert filename.startswith("provider-disabled/") and ".." not in Path(filename).parts, (row.get("id"), filename)
    assert (ROOT / filename).is_file(), ("retained disabled artifact missing", filename)
    # A shared Global/VF identity was collapsed above; distinct IDs must never
    # share one managed artifact.
    assert filename not in seen_paths, ("duplicate disabled provider", filename)
    seen_paths.add(filename)
for row in published:
    filename = str(row.get("filename") or "")
    assert filename.startswith("providers/") and ".." not in Path(filename).parts, (row.get("id"), filename)
    assert filename not in seen_paths, "duplicate published bundle: " + filename
    seen_paths.add(filename)
    published_path = ROOT / filename
    assert published_path.is_file(), "missing published provider: " + filename
    published_js = published_path.read_text(encoding="utf-8")
    for required in (
        "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
        "_spv251SeasonEpisodeScopedValue",
    ):
        assert required in published_js, (filename, required)
    assert any(
        revision in published_js for revision in (
            "cross-client-player-page-identity-v17-s00-identity",
            "cross-client-player-page-identity-v18-s00-evidence",
            "cross-client-player-page-identity-v19-s00-source-proof",
            "cross-client-player-page-identity-v20-url-path-consistency",
        )
    ), (filename, "identity Core revision missing")

v20_published = sum(
    'cross-client-player-page-identity-v20-url-path-consistency'
    in (ROOT / str(row['filename'])).read_text(encoding='utf-8')
    for row in published
)

# Provider-owned episodic runtimes must not undo the Core's S00 contract by
# using JavaScript truthiness (0 || 1). Scan every declared Bloc used by an
# active canonical TV or anime provider in either Global or France. Anime must
# be included because its provider ABI is canonical anime, not an implicit TV
# rewrite, while specials/season-zero coordinates remain valid.
overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
active_episodic: set[str] = set()
for manifest_path in (ROOT / "manifest.json", ROOT / "vf/manifest.json"):
    projection = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in projection.get("scrapers", []):
        if not isinstance(row, dict) or row.get("enabled") is False:
            continue
        types = {
            str(value).strip().casefold()
            for value in (row.get("canonicalSupportedTypes") or row.get("supportedTypes") or [])
        }
        if "tv" in types or "anime" in types:
            active_episodic.add(str(row.get("id") or row.get("name") or "").strip().casefold())

unsafe_patterns = (
    re.compile(r"season\s*:\s*Number\([^\n;]*\)\s*\|\|\s*1"),
    re.compile(r"\bq\.season\s*\|\|\s*1\b"),
    re.compile(r"\b(?:row|x)\.season\s*=\s*Number\([^\n;]*\)\s*\|\|\s*1"),
)
checked_episodic_legos: list[str] = []
for provider_id, patch in (overrides.get("provider_patches") or {}).items():
    if str(provider_id).casefold() not in active_episodic or not isinstance(patch, dict):
        continue
    for relative in patch.get("provider_lego_scripts") or []:
        lego_path = ROOT / str(relative)
        assert lego_path.is_file(), (provider_id, "missing episodic Bloc", relative)
        lego = lego_path.read_text(encoding="utf-8")
        for pattern in unsafe_patterns:
            assert not pattern.search(lego), (
                provider_id,
                relative,
                "TV season zero is still collapsed to season one",
                pattern.pattern,
            )
        checked_episodic_legos.append(str(relative))
assert checked_episodic_legos, "no active episodic provider Bloc checked for season-zero preservation"
print(
    f"SPECIAL_SEASON_ZERO_IDENTITY_SOURCE_OK published={len(published)} retained_disabled={len(disabled)} "
    f"v20_published={v20_published} pending_rematerialization={len(published)-v20_published} "
    f"episodic_blocs_s00_safe={len(checked_episodic_legos)} "
    "source_v20_media_url_consistency_only; no live terminal playback inferred"
)

# Execute the actual declared Anime-Sama Lego request normalizer, not just
# static regex checks. The provider-specific wrapper is NiakVIO-owned and
# requests are synthetic (no network or player bypass).
anime_lego_spec = importlib.util.spec_from_file_location(
    "anime_sama_runtime_v1",
    ROOT / "scripts/provider_patches/anime_sama_runtime_v1.py",
)
assert anime_lego_spec and anime_lego_spec.loader
anime_lego = importlib.util.module_from_spec(anime_lego_spec)
anime_lego_spec.loader.exec_module(anime_lego)
anime_js = anime_lego.WRAPPER.replace(
    "CONFIG_PLACEHOLDER",
    json.dumps({
        "base": "https://anime-sama.to",
        "fallbackBases": [],
        "languages": ["vf"],
        "targetStreams": 3,
    }),
)
runtime_export = 'try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"anime-sama",resolve:resolve}}catch(_e){}'
assert anime_js.count(runtime_export) == 1
anime_js = anime_js.replace(
    runtime_export,
    'try{if(g)g.__niakvioAnimeSamaRequestContractV1=request}catch(_e){}' + runtime_export,
)
anime_js += r"""
const request = globalThis.__niakvioAnimeSamaRequestContractV1;
if (typeof request !== "function") throw new Error("Anime-Sama request ABI not exported in fixture");
const object = request([{tmdbId:"46296", mediaType:"anime", season:0, episode:1}]);
const positional = request(["46296", "anime", 0, 1]);
const stringZero = request([{tmdbId:"46296", mediaType:"tv", season:"0", episode:"1"}]);
const missing = request([{tmdbId:"46296", mediaType:"anime", episode:1}]);
const wrong = request([{tmdbId:"46296", mediaType:"tv", season:-1, episode:0}]);
const fraction = request([{tmdbId:"46296", mediaType:"tv", season:0.5, episode:1}]);
if (!(object.season===0 && object.episode===1 && object.transport==="tv"
      && positional.season===0 && positional.episode===1
      && stringZero.season===0 && stringZero.episode===1
      && missing.season===1 && wrong.season===1 && wrong.episode===1
      && fraction.season===1)) {
  throw new Error("Anime-Sama Lego S00/unknown/invalid season identity regression");
}
console.log("ANIME_SAMA_S00_RUNTIME_ABI_OK");
"""
anime_check = subprocess.run(
    ["node", "-e", anime_js], cwd=ROOT, text=True,
    capture_output=True, check=True, timeout=30,
)
assert "ANIME_SAMA_S00_RUNTIME_ABI_OK" in anime_check.stdout
print("Anime-Sama owned Lego preserves explicit season zero in real Node runtime")
