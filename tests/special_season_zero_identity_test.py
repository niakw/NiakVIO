#!/usr/bin/env python3
"""Regression: specials S00 remain distinct from season 1, while unknown stays unknown."""
from __future__ import annotations
import importlib.util
import json
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
    {"title": "Spartacus S00E01", "url": "https://cdn.example/correct-s00.m3u8"},
    {"name": "Spartacus", "seasonNumber": 0, "episodeNumber": 1, "url": "https://cdn.example/correct-structured.m3u8"},
    {"name": "Server 1", "url": "https://cdn.example/opaque-unverified.m3u8"},
    {"name": "Server 2", "sourceUrl": "https://reader.example/watch?season=0&episode=1", "url": "https://cdn.example/correct-source-coordinate.m3u8"},
]
compiled = core.apply(source.replace("ROWS", json.dumps(rows)), context={"provider_id": "example"})
assert 'cross-client-player-page-identity-v18-s00-evidence' in compiled
assert 'function exactSpecialEpisodeEvidence(row,q)' in compiled

runner = compiled + """
(async()=> {
  const assert=require('assert');
  const q=QUERY;
  const rows=await module.exports.getStreams(q);
  assert.deepEqual(rows.map(r=>r.url), [
    'https://cdn.example/correct-s00.m3u8',
    'https://cdn.example/correct-structured.m3u8',
    'https://cdn.example/correct-source-coordinate.m3u8'
  ], JSON.stringify(rows));
  const s1=await module.exports.getStreams({...q,season:1});
  assert(s1.some(r=>r.url==='https://cdn.example/wrong-s1.m3u8'));
  assert(!s1.some(r=>r.url==='https://cdn.example/correct-s00.m3u8'));
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
assert "cross-client-player-page-identity-v18-s00-evidence" in (ROOT / "scripts/provider_patches/global_stream_identity_v1.py").read_text(encoding="utf-8")

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
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
published = [row for row in manifest.get("scrapers", []) if isinstance(row, dict)]
assert published, "empty published provider manifest"
seen_paths = set()
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
        "cross-client-player-page-identity-v17-s00-identity",
        "_spv251SeasonEpisodeScopedValue",
    ):
        assert required in published_js, (filename, required)

v18_published = sum(
    'cross-client-player-page-identity-v18-s00-evidence'
    in (ROOT / str(row['filename'])).read_text(encoding='utf-8')
    for row in published
)
print(
    f"SPECIAL_SEASON_ZERO_IDENTITY_SOURCE_OK published={len(published)} "
    f"v18_published={v18_published} pending_rematerialization={len(published)-v18_published} "
    "source_v18_exact_s00_only; no live terminal playback inferred"
)
