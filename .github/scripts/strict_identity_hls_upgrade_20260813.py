#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected 1 match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) The per-provider output sanitizer must use the same structural HLS
# definition as the health/runtime integrity layers. A bare #EXTM3U header is
# not playable media.
sanitizer = ROOT / "scripts/provider_patches/stream_output_sanitizer.py"
replace_once(sanitizer, '"implementationVersion": 6,', '"implementationVersion": 7,', "sanitizer implementation revision")
replace_once(
    sanitizer,
    r'''  function validHls(text){
    var value=String(text||"").replace(/^\uFEFF/,"").trimStart();
    if(value.indexOf("#EXTM3U")!==0)return false;
    var isVod=/#EXT-X-ENDLIST(?:\r?\n|$)/i.test(value);
    var durations=[],match,re=/#EXTINF:([0-9]+(?:\.[0-9]+)?)/gi;
    while((match=re.exec(value))!==null)durations.push(Number(match[1])||0);
    if(isVod&&durations.length&&config.minVodDurationSeconds>0){
      var total=durations.reduce(function(sum,item){return sum+item},0);
      if(total<config.minVodDurationSeconds)return false;
    }
    return true;
  }
''',
    r'''  function validHls(text){
    var value=String(text||"").replace(/^\uFEFF/,"").trimStart();
    if(value.indexOf("#EXTM3U")!==0)return false;
    var lines=value.split(/\r?\n/),hasVariantTag=false,hasVariantUri=false;
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i].trim()))continue;
      hasVariantTag=true;
      for(var j=i+1;j<lines.length;j++){
        var child=String(lines[j]||"").trim();
        if(!child)continue;
        if(child.charAt(0)==="#")continue;
        hasVariantUri=true;break;
      }
      if(hasVariantUri)break;
    }
    if(hasVariantTag&&!hasVariantUri)return false;
    var hasMedia=/#EXTINF\s*:/i.test(value)||/#EXT-X-PART\s*:/i.test(value)||/#EXT-X-MAP\s*:/i.test(value);
    if(!hasMedia&&!hasVariantUri)return false;
    var isVod=/#EXT-X-ENDLIST(?:\r?\n|$)/i.test(value);
    var durations=[],match,re=/#EXTINF:([0-9]+(?:\.[0-9]+)?)/gi;
    while((match=re.exec(value))!==null)durations.push(Number(match[1])||0);
    if(isVod&&durations.length&&config.minVodDurationSeconds>0){
      var total=durations.reduce(function(sum,item){return sum+item},0);
      if(total<config.minVodDurationSeconds)return false;
    }
    return true;
  }
''',
    "strict HLS structure",
)

# 2) Force migration of the repository-wide HLS runtime wrapper even when its
# timeout/config did not change. Existing content-addressed providers otherwise
# keep an older implementation forever.
hls_guard = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"
replace_once(
    hls_guard,
    '{"timeoutMs": timeout_ms, "maxChildren": max_children},',
    '{"timeoutMs": timeout_ms, "maxChildren": max_children, "implementationRevision": "structural-media-v2"},',
    "HLS implementation revision",
)

# 3) NuvioTV probe had a separate semantic bug: a top-level #EXTM3U-only body
# fell through to playable=true. Keep it aligned with health_check.mjs.
probe = ROOT / "scripts/nuvio_tv_probe_v2.cjs"
replace_once(
    probe,
    """      result.hls_external_audio_count = graph.externalAudio.length;\n      if (result.hls_master) {\n""",
    """      result.hls_external_audio_count = graph.externalAudio.length;\n      const hlsHasMedia = /#EXTINF\\s*:/i.test(text) || /#EXT-X-PART\\s*:/i.test(text) || /#EXT-X-MAP\\s*:/i.test(text);\n      if (!result.hls_master && !hlsHasMedia) {\n        result.error = 'hls_header_only';\n        return result;\n      }\n      if (result.hls_master) {\n""",
    "NuvioTV header-only HLS guard",
)

# Add generic, conservative identity classification to the probe. Positive
# contradiction is blocking; absence of metadata stays unknown rather than
# becoming an arbitrary false negative.
replace_once(
    probe,
    """async function inspectStream(row) {\n""",
    r'''function normIdentity(value) {
  try { return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim(); }
  catch { return String(value ?? '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim(); }
}

function identityTokens(value) {
  const noise = new Set(['the','a','an','le','la','les','un','une','de','des','du','of','and','et','film','movie','stream','streaming','watch','play','server','serveur','source','mirror','direct','download','telecharger','vcloud','hubcloud','file','video','quality','web','dl','webrip','webdl','bluray','blu','ray','remux','hdr','dv','dolby','atmos','aac','ac3','eac3','ddp','x264','x265','h264','h265','hevc','av1','multi','vf','vff','vostfr','vo','french','english','truefrench','hd','uhd','fhd','sd']);
  return normIdentity(value).split(/\s+/).filter((token) => token.length > 1 && !noise.has(token) && !/^\d{3,4}p$/.test(token) && !/^\d{4}$/.test(token));
}

function streamIdentity(row, fixture) {
  const aliases = [fixture?.title, fixture?.label, ...(Array.isArray(fixture?.aliases) ? fixture.aliases : [])].filter(Boolean);
  const expected = aliases.map(normIdentity).filter(Boolean);
  const expectedTokens = new Set(aliases.flatMap(identityTokens));
  const label = String(row?.title || row?.description || row?.filename || row?.name || '').trim();
  const normalized = normIdentity(label);
  const mediaType = String(fixture?.mediaType || fixture?.type || 'movie').toLowerCase();
  const wantedSeason = Number(fixture?.season || 0);
  const wantedEpisode = Number(fixture?.episode || 0);
  const seasonEpisode = /(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)
    || /(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label);
  if (mediaType === 'movie' && seasonEpisode) return { status: 'contradiction', reason: 'movie_row_is_episode' };
  if (seasonEpisode && (mediaType === 'tv' || mediaType === 'anime')) {
    const season = Number(seasonEpisode[1] || 0), episode = Number(seasonEpisode[2] || 0);
    if ((wantedSeason && season && season !== wantedSeason) || (wantedEpisode && episode && episode !== wantedEpisode)) {
      return { status: 'contradiction', reason: 'wrong_season_episode' };
    }
  }
  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };
  const rowTokens = identityTokens(label);
  if (rowTokens.length >= 2 && expectedTokens.size) {
    const overlap = rowTokens.filter((token) => expectedTokens.has(token));
    if (overlap.length === 0) return { status: 'contradiction', reason: 'strong_title_mismatch' };
  }
  if (seasonEpisode && (mediaType === 'tv' || mediaType === 'anime')) return { status: 'match', reason: 'season_episode_match' };
  return { status: 'unknown', reason: 'insufficient_identity_metadata' };
}

async function inspectStream(row) {
''',
    "probe identity helpers",
)
replace_once(
    probe,
    """  const inspected = rows.map((row, index) => ({ row, media: media[index] }));\n  const playable = inspected.filter((item) => item.media.playable);\n  process.stdout.write(JSON.stringify({\n    ok: !runtimeError && playable.length > 0,\n""",
    """  const inspected = rows.map((row, index) => ({ row, media: media[index], identity: streamIdentity(row, fixture) }));\n  const playable = inspected.filter((item) => item.media.playable);\n  const identityContradictions = playable.filter((item) => item.identity.status === 'contradiction');\n  const identityVerified = playable.filter((item) => item.identity.status === 'match');\n  process.stdout.write(JSON.stringify({\n    ok: !runtimeError && playable.length > 0 && identityContradictions.length === 0,\n""",
    "probe identity counters",
)
replace_once(
    probe,
    """    raw_stream_count: rows.length,\n    playable_stream_count: playable.length,\n    streams: inspected,\n""",
    """    raw_stream_count: rows.length,\n    playable_stream_count: playable.length,\n    identity_verified_count: identityVerified.length,\n    identity_contradiction_count: identityContradictions.length,\n    streams: inspected,\n""",
    "probe identity output",
)
replace_once(
    probe,
    """  process.exitCode = playable.length ? 0 : 2;\n""",
    """  process.exitCode = playable.length && identityContradictions.length === 0 ? 0 : 2;\n""",
    "probe strict exit",
)

# 4) The global HTML/mixed catalogue wrapper currently trusts *any* non-empty
# native result. Add a generic hard-contradiction filter before that early
# return. If every native row contradicts the requested identity, the existing
# recovery path is allowed to run instead of launching the wrong media.
catalogue = ROOT / "scripts/provider_patches/global_catalogue_alias_recovery_v2.py"
text = catalogue.read_text(encoding="utf-8")
text = text.replace(
    '"languageHint": str(cfg.get("language_hint") or "").strip().lower(),\n    }',
    '"languageHint": str(cfg.get("language_hint") or "").strip().lower(),\n        "implementationRevision": "native-identity-v1",\n    }',
    1,
)
if '"implementationRevision": "native-identity-v1"' not in text:
    raise SystemExit("catalogue implementation revision insertion failed")
old_marker = '''    if marker in text:\n        return _upgrade_existing_search_priority(text)\n\n    js = r\'\'\'\n'''
new_marker = '''    if marker in text:\n        return _upgrade_existing_search_priority(text)\n\n    old = text.find(f"/* {MARKER}:")\n    if old >= 0:\n        call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', old)\n        end = text.find(");", call) if call >= 0 else -1\n        if call < 0 or end < 0:\n            raise ValueError("unterminated global catalogue alias recovery wrapper")\n        text = (text[:old] + text[end + 2 :]).rstrip()\n\n    js = r\'\'\'\n'''
if old_marker not in text:
    raise SystemExit("catalogue marker replacement anchor missing")
text = text.replace(old_marker, new_marker, 1)
old_recover = r'''async function recover(q){if(["movie","tv","anime"].indexOf(q.mediaType)<0)return[];var m=await meta(q);if(!m.titles.length)return[];'''
new_recover = r'''async function recover(q,knownMeta){if(["movie","tv","anime"].indexOf(q.mediaType)<0)return[];var m=knownMeta||await meta(q);if(!m.titles.length)return[];'''
if old_recover not in text:
    raise SystemExit("catalogue recover signature anchor missing")
text = text.replace(old_recover, new_recover, 1)
old_install = r'''function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV2)return false;var native=o[k];var wrap=async function(){var v;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v);if(x&&x.list.length)return v;var recovered=await recover(args(arguments));if(!recovered.length)return v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV2=true;o[k]=wrap;return true}'''
new_install = r'''function identityLabel(row){return s(row&&((row.title||row.description||row.filename||row.name)||""))}
function nativeIdentityReject(row,q,m){var label=identityLabel(row);if(!label)return false;var se=/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label);if(q.mediaType==="movie"&&se)return true;if(se&&(q.mediaType==="tv"||q.mediaType==="anime")){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true}if(aliasScore(label,m)>=90)return false;var tech={server:1,serveur:1,stream:1,streaming:1,source:1,mirror:1,direct:1,download:1,telecharger:1,play:1,player:1,vcloud:1,hubcloud:1,file:1,video:1,quality:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var providerTokens=tokens(c.providerName),expected={};(m.titles||[]).forEach(function(t){tokens(t).forEach(function(x){expected[x]=1})});var words=tokens(label).filter(function(x){return !tech[x]&&providerTokens.indexOf(x)<0&&!/^\d{3,4}p$/.test(x)});if(words.length<2)return false;for(var i=0;i<words.length;i++)if(expected[words[i]])return false;return true}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV2)return false;var native=o[k];var wrap=async function(){var q=args(arguments),v;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v),m=null;if(x&&x.list.length){try{m=await meta(q)}catch(_){m=null}if(!m||!m.titles||!m.titles.length)return v;var kept=x.list.filter(function(row){return !nativeIdentityReject(row,q,m)});if(kept.length)return rebuild(v,x,kept)}var recovered=await recover(q,m);if(!recovered.length)return x?rebuild(v,x,[]):v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV2=true;o[k]=wrap;return true}'''
if old_install not in text:
    raise SystemExit("catalogue native early-return anchor missing")
text = text.replace(old_install, new_install, 1)
catalogue.write_text(text, encoding="utf-8")

# 5) Make the finite cross-provider publication audit use the user's compact
# representative movie case and make identity contradictions publish-blocking.
audit = ROOT / "scripts/audit_catalogue_identity_media.py"
text = audit.read_text(encoding="utf-8")
text = text.replace(
    '- every movie-capable provider: Interstellar plus an impossible TMDb identity sentinel,',
    '- every movie-capable provider: one strict representative movie plus an impossible TMDb identity sentinel,',
    1,
)
interstellar_fixture = '''    "vf_interstellar": {\n        "label": "Interstellar",\n        "tmdbId": "157336",\n        "mediaType": "movie",\n        "title": "Interstellar",\n        "year": 2014,\n    },\n'''
strict_fixture = '''    "strict_movie_identity": {\n        "label": "Mon ninja et moi 3",\n        "tmdbId": "1215638",\n        "mediaType": "movie",\n        "title": "Mon ninja et moi 3",\n        "aliases": ["Ternet Ninja 3", "Checkered Ninja 3"],\n        "year": 2025,\n        "expectedDurationMinutes": 88,\n    },\n'''
if interstellar_fixture not in text:
    raise SystemExit("audit Interstellar fixture anchor missing")
text = text.replace(interstellar_fixture, strict_fixture, 1)
text = text.replace('fixture_names.extend(["vf_interstellar", "impossible_movie"])', 'fixture_names.extend(["strict_movie_identity", "impossible_movie"])', 1)
text = text.replace('fixture_names.append("vf_interstellar")', 'fixture_names.append("strict_movie_identity")')
old_probe_counts = '''        playable_count = int(probe.get("playable_stream_count") or 0)\n        summary = summarize_media(probe)\n        status = "playable" if playable_count > 0 else ("returned_unplayable" if raw_count > 0 else "no_streams")\n'''
new_probe_counts = '''        playable_count = int(probe.get("playable_stream_count") or 0)\n        identity_verified_count = int(probe.get("identity_verified_count") or 0)\n        identity_contradiction_count = int(probe.get("identity_contradiction_count") or 0)\n        summary = summarize_media(probe)\n        status = "wrong_content" if identity_contradiction_count > 0 else ("playable" if playable_count > 0 else ("returned_unplayable" if raw_count > 0 else "no_streams"))\n'''
if old_probe_counts not in text:
    raise SystemExit("audit probe counts anchor missing")
text = text.replace(old_probe_counts, new_probe_counts, 1)
old_row_counts = '''            "raw_stream_count": raw_count,\n            "playable_stream_count": playable_count,\n            "runtime_error": sanitize(probe.get("runtime_error")),\n'''
new_row_counts = '''            "raw_stream_count": raw_count,\n            "playable_stream_count": playable_count,\n            "identity_verified_count": identity_verified_count,\n            "identity_contradiction_count": identity_contradiction_count,\n            "runtime_error": sanitize(probe.get("runtime_error")),\n'''
if old_row_counts not in text:
    raise SystemExit("audit row counts anchor missing")
text = text.replace(old_row_counts, new_row_counts, 1)
old_lists = '''    playable_false_positive = [row for row in rows if row.get("playable_identity_false_positive")]\n    hls_failures = [row for row in rows if int(row.get("hls_variant_failures") or 0) or int(row.get("hls_audio_failures") or 0)]\n'''
new_lists = '''    playable_false_positive = [row for row in rows if row.get("playable_identity_false_positive")]\n    wrong_content = [row for row in rows if int(row.get("identity_contradiction_count") or 0) > 0]\n    hls_failures = [row for row in rows if int(row.get("hls_variant_failures") or 0) or int(row.get("hls_audio_failures") or 0)]\n'''
if old_lists not in text:
    raise SystemExit("audit failure lists anchor missing")
text = text.replace(old_lists, new_lists, 1)
text = text.replace('"hls_structural_child_or_external_audio_failure": "broken_media_graph",', '"hls_structural_child_or_external_audio_failure": "broken_media_graph",\n            "playable_identity_contradiction": "wrong_content_publish_blocker",', 1)
text = text.replace('"playable_identity_false_positive_providers": sorted({row["provider_id"] for row in playable_false_positive}),', '"playable_identity_false_positive_providers": sorted({row["provider_id"] for row in playable_false_positive}),\n            "wrong_content_providers": sorted({row["provider_id"] for row in wrong_content}),', 1)
text = text.replace('f"playable_identity_false_positive={len(report[\'summary\'][\'playable_identity_false_positive_providers\'])} "', 'f"playable_identity_false_positive={len(report[\'summary\'][\'playable_identity_false_positive_providers\'])} "\n        f"wrong_content={len(report[\'summary\'][\'wrong_content_providers\'])} "', 1)
text = text.replace('return 1 if playable_false_positive or hls_failures else 0', 'return 1 if playable_false_positive or wrong_content or hls_failures else 0', 1)
audit.write_text(text, encoding="utf-8")

# 6) Update durable policy versions and tests to describe the new semantics.
overrides = ROOT / "provider-overrides.json"
cfg = json.loads(overrides.read_text(encoding="utf-8"))
(cfg.setdefault("catalogue_resolution_policy", {}))["version"] = 3
(cfg.setdefault("playback_integrity_policy", {}))["version"] = 3
overrides.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

coverage = ROOT / "tests/catalogue_audit_coverage_test.py"
replace_once(coverage, 'assert "vf_interstellar" in fixtures, (provider_id, fixtures)', 'assert "strict_movie_identity" in fixtures, (provider_id, fixtures)', "strict movie audit coverage")

policy_test = ROOT / "tests/global_provider_policy_test.py"
replace_once(policy_test, 'assert cat["version"] == 2', 'assert cat["version"] == 3', "catalogue policy version")
replace_once(policy_test, '    "if(x&&x.list.length)return v",', '    "nativeIdentityReject",', "native identity policy token")
replace_once(policy_test, 'assert "Mon ninja et moi 3" not in audit\nassert "1215638" not in audit', 'assert "Mon ninja et moi 3" in audit\nassert "1215638" in audit', "strict movie audit fixture")

playback_test = ROOT / "tests/global_playback_integrity_policy_test.py"
replace_once(playback_test, 'assert policy.get("version") == 2', 'assert policy.get("version") == 3', "playback policy version")

hls_test = ROOT / "tests/hls_playback_integrity_test.py"
text = hls_test.read_text(encoding="utf-8")
needle = '''# A 200 HTML response behind a .m3u8 URL is a conclusive invalid stream and\n# must be removed rather than sent to Nuvio's HLS parser.\n'''
insert = r'''# A syntactically valid HLS header without any variant/media structure is not
# a stream. This is the exact class of false positive that otherwise reaches
# Nuvio and fails at the player with an "EXTM3U header" error.
run_node(r'''
globalThis.fetch=async function(url){return {ok:true,status:200,url:String(url),headers:{get:function(){return "application/vnd.apple.mpegurl"}},text:async function(){return "#EXTM3U\n#EXT-X-VERSION:3\n"}}};
''' + wrapped + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(!Array.isArray(rows)||rows.length!==0)throw new Error("header-only HLS was not rejected")})().catch(function(e){console.error(e);process.exit(1)});
''')

'''
if needle not in text:
    raise SystemExit("HLS test insertion anchor missing")
text = text.replace(needle, insert + needle, 1)
hls_test.write_text(text, encoding="utf-8")

# Add a permanent synthetic runtime test for the generic native identity gate.
identity_test = ROOT / "tests/strict_native_identity_guard_test.py"
identity_test.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_catalogue_alias_recovery_v2.py"
spec = importlib.util.spec_from_file_location("global_alias_identity", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
options = {"base_url":"https://catalog.example","provider_name":"example","max_aliases":8,"max_candidates":8,"max_players":8,"timeout_ms":5000}
base = "module.exports={getStreams:async function(){return [{title:'House of the Dragon - S03 E01',url:'https://wrong.example/video.m3u8'}];}};"
patched = module.apply(base, options)
assert "nativeIdentityReject" in patched
assert "implementationRevision" in patched
# Same config must be idempotent, while an implementation-revision upgrade must
# have stripped the previous V2 block instead of stacking it.
assert module.apply(patched, options) == patched
assert patched.count("NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:") == 1
runner = r'''
const assert=require('assert');
function response(body,status=200,type='application/json',url=''){return {ok:status>=200&&status<400,status,url,headers:{get(n){return String(n).toLowerCase()==='content-type'?type:null}},async json(){return JSON.parse(body)},async text(){return body}}}
global.fetch=async function(url){url=String(url);
 if(url.includes('/movie/424242?')&&url.includes('language=fr-FR'))return response(JSON.stringify({id:424242,title:'Mon ninja et moi 3',original_title:'Ternet Ninja 3',release_date:'2025-08-21'}),200,'application/json',url);
 if(url.includes('/movie/424242?')&&url.includes('language=en-US'))return response(JSON.stringify({id:424242,title:'Checkered Ninja 3',original_title:'Ternet Ninja 3',release_date:'2025-08-21'}),200,'application/json',url);
 if(url.includes('/movie/424242/alternative_titles?'))return response(JSON.stringify({titles:[]}),200,'application/json',url);
 if(url.startsWith('https://catalog.example/?s=')||url.startsWith('https://catalog.example/search?'))return response('<a href="/ternet-ninja-3-2025">Ternet Ninja 3 (2025)</a>',200,'text/html',url);
 if(url==='https://catalog.example/ternet-ninja-3-2025')return response('<h1>Ternet Ninja 3 (2025)</h1><iframe src="https://player.example/e/correct"></iframe>',200,'text/html',url);
 return response('',404,'text/plain',url);
};
PATCHED
(async()=>{const rows=await module.exports.getStreams({id:'tmdb:424242',mediaType:'movie',title:'Mon ninja et moi 3',year:2025});assert.strictEqual(rows.length,1,JSON.stringify(rows));assert.strictEqual(rows[0].url,'https://player.example/e/correct');console.log('strict native identity guard runtime test passed')})().catch(e=>{console.error(e);process.exit(1)});
'''.replace('PATCHED', patched)
with tempfile.NamedTemporaryFile('w', suffix='.cjs', dir=ROOT, delete=False, encoding='utf-8') as handle:
    handle.write(runner); path=Path(handle.name)
try:
    proc=subprocess.run(['node',str(path)],cwd=ROOT,capture_output=True,text=True,timeout=30)
    if proc.returncode: raise AssertionError(proc.stdout+'\n'+proc.stderr)
finally:
    path.unlink(missing_ok=True)
print('strict native identity guard tests passed')
''', encoding="utf-8")

package = ROOT / "package.json"
pkg = json.loads(package.read_text(encoding="utf-8"))
cmd = pkg["scripts"]["test"]
new_test = "python3 tests/strict_native_identity_guard_test.py"
if new_test not in cmd:
    cmd += " && " + new_test
pkg["scripts"]["test"] = cmd
package.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("strict HLS and native identity upgrade applied")
