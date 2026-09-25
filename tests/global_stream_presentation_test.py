#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCHES = ROOT / "scripts" / "provider_patches"
NORMALIZER = ROOT / "scripts" / "normalize_stream_presentation_v12.py"


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


normalizer = load_path(NORMALIZER, "normalize_stream_presentation_v12")
normalizer.normalize(apply=False)
normalizer.assert_contract()
presentation = load_path(PATCHES / "global_stream_presentation_v1.py", "global_stream_presentation_v1")
import re
revision_match = re.search(r"-v(\d+)$", presentation.REVISION)
assert revision_match and int(revision_match.group(1)) >= 25, presentation.REVISION
presentation_source = (PATCHES / "global_stream_presentation_v1.py").read_text(encoding="utf-8")
assert "\\nfunction" not in presentation_source, "raw presentation wrapper contains a literal \\n before function declaration"


def run(source: str, provider_id: str, call: str, fetch_impl: str | None = None, *, return_raw: bool = False):
    patched = presentation.apply(source, context={"provider_id": provider_id})
    assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in patched
    assert presentation.REVISION in patched
    assert patched == presentation.apply(patched, context={"provider_id": provider_id})
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(patched, encoding="utf-8")
        fetch = fetch_impl or "async function(){throw new Error('offline')}"
        # Presentation no longer owns TMDB transport or credentials. When this
        # isolated test supplies a TMDB fixture, expose it through the same Core
        # metadata capability that composed provider bundles expose at runtime.
        core_capability = ""
        if fetch_impl:
            core_capability = r"""
global.__nuvioCoreGetTmdbDataV1=async function(q){
  const kind=(q&&q.tmdbNamespace)==='tv'||(q&&q.mediaType)==='tv'||(q&&q.mediaType)==='series'||(q&&q.mediaType)==='anime'?'tv':'movie';
  const id=String(q&&q.tmdbId||'');
  const response=await global.fetch('https://api.themoviedb.org/3/'+kind+'/'+encodeURIComponent(id));
  if(!response||!response.ok)return {state:'unavailable',tmdbId:id,tmdbNamespace:kind,metadata:null,episodeMetadata:null};
  const metadata=await response.json();
  return {state:'ok',tmdbId:id,tmdbNamespace:kind,metadata,episodeMetadata:null};
};
"""
        runner.write_text(
            "global.fetch=" + fetch + ";\n" + core_capability + "\nconst p=require(" + json.dumps(str(provider)) + ");\n" + call + "\n",
            encoding="utf-8",
        )
        # The contract intentionally contains emoji. Never inherit the Windows
        # runner's cp1252 locale when decoding Node stdout/stderr.
        result = subprocess.run(
            ["node", str(runner)],
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        output = result.stdout.strip()
        return output if return_raw else json.loads(output)


tmdb = r"""async function(url){
  if(!String(url).includes('api.themoviedb.org')) throw new Error('unexpected playback fetch');
  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}})};
}"""

# Legacy French provider tokens remain accepted inputs, but public presentation is universal FR + SUB FR.
source = "module.exports={getStreams:async()=>[{name:'Purstream | 4K | VF',url:'https://media.example/master.m3u8',quality:'4K',language:'VF',subtitles:'VOSTFR',codec:'x265 10bit',audio:'DDP 5.1',duration:169,sourceType:'WEB-DL',format:'m3u8',size:'8.4 GB',headers:{Referer:'https://purstream.example/'}}]};\n"
row = run(source, "purstream", "p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))", tmdb)
assert row["title"] == "Purstream - 4K", row
assert row["name"] == row["title"], row
assert row["quality"] == "2160p"
assert row["language"] == "VF", row
assert row["codec"] == "HEVC"
assert row["duration"] == 169
assert row["sourceType"] == "WEB-DL"
assert row["format"] == "HLS"
assert row["size"] == row["description"], row
assert row["headers"] == {"Referer": "https://purstream.example/"}
assert {"4k-ultra-hd", "webdl", "hevc", "lang-fr", "sub-fr", "age-12"}.issubset(set(row["badgeIds"])), row
assert "multi" not in set(row["badgeIds"]), row
lines = row["description"].splitlines()
assert lines[0] == "🎬 Interstellar • 2014", lines
assert lines[1] == "⏱ 2h49 • 🔞 12+", lines
assert lines[2] == "🌐 French · Dub • 💬 SUB FR", lines
assert lines[3].startswith("🎞️ WEB-DL"), lines
assert "HEVC 10bit" in lines[3] and "HLS" in lines[3] and "💾 8.4 GB" in lines[3]
assert "2160p" not in row["description"] and "4K" not in row["description"]
assert "Unknown" not in row["description"]

# JVM QuickJS bridge safety: final stream-array JSON must cross JNI as ASCII-only
# (supplementary emoji are represented as JSON \uXXXX surrogate escapes), while
# normal JSON decoding restores the original presentation exactly.
raw_stream_json = run(
    source,
    "purstream",
    "p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v)))",
    tmdb,
    return_raw=True,
)
assert raw_stream_json.isascii(), raw_stream_json
assert "\\ud83c\\udfac" in raw_stream_json.lower(), raw_stream_json
roundtrip = json.loads(raw_stream_json)[0]
assert roundtrip["description"].splitlines()[0] == "🎬 Interstellar • 2014", roundtrip
assert "French · Dub" in roundtrip["description"] and "SUB FR" in roundtrip["description"], roundtrip

# Cross-client projection contract: Mobile/Desktop rebuild plugin StreamItem.description
# from quality + size + language; TV maps LocalScraperResult.size -> Stream.description.
# Therefore the complete Core description is tunneled through size on every client so
# media identity and technical tokens survive to each client's regex badge matcher.
tv_row = run(
    source,
    "purstream",
    "global.TMDB_API_KEY='tv-key';global.SCRAPER_ID='purstream';p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))",
    tmdb,
)
assert tv_row["size"] == tv_row["description"], tv_row
assert tv_row["description"].splitlines()[0] == "🎬 Interstellar • 2014"
assert "⏱ 2h49" in tv_row["description"] and "🔞 12+" in tv_row["description"]
assert "French · Dub" in tv_row["description"] and "SUB FR" in tv_row["description"]
assert "🎞️ WEB-DL" in tv_row["description"] and "HEVC 10bit" in tv_row["description"]
assert "💾 8.4 GB" in tv_row["description"]

# Legacy French tokens are accepted as input aliases; public badge IDs are FR / FR-CA.
vf = run("module.exports={getStreams:async()=>[{name:'Coflix',url:'https://x.example/a.mp4',language:'fr',quality:'1080p'}]};\n", "coflix", "p.getStreams({mediaType:'movie',title:'Film',year:2026}).then(v=>console.log(JSON.stringify(v[0])))")
assert vf["language"] == "VF" and "French · Dub" in vf["description"]
assert vf["title"] == "Coflix - 1080p"
assert "1080p" not in vf["description"]
assert "BLU-RAY" not in vf["description"]
assert "lang-fr" in vf["badgeIds"] and "vf" not in vf["badgeIds"]

vfq = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.mp4',language:'fr-CA VFQ'}]};\n", "purstream", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vfq["language"] == "VFQ", vfq
assert vfq["languageTracks"] == [{"code":"fr-ca","tag":"FR-CA","label":"French (Canada)","role":"Dub"}], vfq
assert "French (Canada) · Dub" in vfq["description"], vfq
assert "FR-CA Dub" in vfq["displayBadges"], vfq
assert "lang-fr-ca" in vfq["badgeIds"] and "vfq" not in vfq["badgeIds"]

# VOSTFR is an input alias only; public output is a French subtitle track/badge.
vost = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.m3u8',language:'VOSTFR'}]};\n", "purstream", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vost["language"] == "VOSTFR" and "French · Sub" in vost["description"]
assert "sub-fr" in vost["badgeIds"] and "vostfr" not in vost["badgeIds"]

# VO/MULTI without factual language metadata remain compatibility scalars only and emit no public language badge.
vo = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.m3u8',language:'VO'}]};\n", "cineby", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vo["language"] == "VO" and "🌐 VO" not in vo["description"]
assert not any(str(x).startswith("lang-") for x in vo["badgeIds"])
vo_multi = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.m3u8',language:'MULTI'}]};\n", "cineby", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vo_multi["language"] == "MULTI" and "🌐 MULTI" not in vo_multi["description"]
assert "multi" not in vo_multi["badgeIds"]

# Detailed language evidence may live in provider/source labels even when the
# coarse transport language is only VO. Preserve the specific language instead
# of collapsing Hindi/Tamil/etc. back to generic VO.
source_language_evidence = run(
    "module.exports={getStreams:async()=>[{name:'Moviebox',url:'https://x.example/a.mp4',quality:'1080p',language:'VO',sourceName:'Example 1080P Hindi',sourceTitle:'Example 1080P Hindi'}]};\n",
    "moviebox",
    "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert source_language_evidence["language"] == "Hindi", source_language_evidence
assert "Hindi" in source_language_evidence["description"], source_language_evidence
assert source_language_evidence["presentationFacts"]["language"] == "Hindi", source_language_evidence
assert "Hindi" in source_language_evidence["displayBadges"], source_language_evidence
assert "lang-hi" in source_language_evidence["badgeIds"], source_language_evidence
assert "vo" not in source_language_evidence["badgeIds"], source_language_evidence

# Series/anime identity is title/year/SxxExx; provider-owned layout never survives.
tv = run("module.exports={getStreams:async()=>[{name:'Purstream',url:'https://x.example/a.m3u8',description:'PRIVATE PROVIDER LAYOUT',language:'VF'}]};\n", "purstream", "p.getStreams({mediaType:'tv',title:'Breaking Bad',year:2008,season:1,episode:1}).then(v=>console.log(JSON.stringify(v[0])))")
assert tv["description"].splitlines()[0] == "📺 Breaking Bad • 2008 • S01E01"
assert "PRIVATE PROVIDER LAYOUT" not in tv["description"]

# Sparse provider data keeps safe TMDB/request context but invents no technical facts.
sparse = run("module.exports={getStreams:async()=>[{name:'Cineby',url:'https://x.example/a.mp4',description:'Unknown'}]};\n", "cineby", "p.getStreams({mediaType:'movie',title:'Sinners',year:2025}).then(v=>console.log(JSON.stringify(v[0])))")
assert "🎬 Sinners • 2025" in sparse["description"]
assert "Unknown" not in sparse["description"]
assert "BLU-RAY" not in sparse["description"]

url_quality = run(
    "module.exports={getStreams:async()=>[{name:'Kehflix',url:'https://cdn.example/interstellar/FHD/main.m3u8',quality:'Unknown'}]};\n",
    "kehflix",
    "p.getStreams({mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert url_quality["quality"] == "1080p", url_quality
assert " - 1080p" in url_quality["title"], url_quality
assert "1080p-full-hd" in url_quality["badgeIds"], url_quality

numeric_height = run(
    "module.exports={getStreams:async()=>[{name:'Source',url:'https://cdn.example/master.m3u8',height:2160}]};\n",
    "generic",
    "p.getStreams({mediaType:'movie',title:'Film',year:2026}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert numeric_height["quality"] == "2160p", numeric_height
assert " - 4K" in numeric_height["title"], numeric_height

# Native Desktop bridge: optional TMDB enrichment is skipped when the client does
# not expose a runtime-owned TMDB_API_KEY. Provider streams must return immediately.
desktop_native = run(
    "module.exports={getStreams:async()=>[{name:'Cineby',url:'https://x.example/a.mp4',quality:'1080p',language:'VO'}]};\n",
    "cineby",
    "global.__native_fetch=async()=>{throw new Error('unexpected native TMDB fetch')};let calls=0;global.fetch=async()=>{calls++;throw new Error('TMDB must be skipped')};p.getStreams('157336','movie').then(v=>console.log(JSON.stringify({row:v[0],calls})))",
)
assert desktop_native["calls"] == 0, desktop_native
assert desktop_native["row"]["title"] == "Cineby - 1080p", desktop_native
assert desktop_native["row"]["name"] == desktop_native["row"]["title"], desktop_native
assert desktop_native["row"]["url"] == "https://x.example/a.mp4", desktop_native

# Native composition: media_type has already populated the verified TMDB base
# cache. Presentation may use it, but must not spend another synchronous native
# bridge request on ratings/runtime decoration.
native_cached = run(
    "module.exports={getStreams:async()=>[{name:'Cineby',url:'https://x.example/a.mp4',quality:'1080p',language:'VO'}]};\n",
    "cineby",
    "global.TMDB_API_KEY='native-key';global.__native_fetch=async()=>{throw new Error('unused')};global.__nuvioTmdbMetadataCacheV1={'movie:157336':{state:'ok',metadata:{id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169}}};let calls=0;global.fetch=async()=>{calls++;throw new Error('presentation must use cache on native runtime')};p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify({row:v[0],calls})))",
)
assert native_cached["calls"] == 0, native_cached
assert native_cached["row"]["duration"] == 169, native_cached
assert "Interstellar • 2014" in native_cached["row"]["description"], native_cached

print("global stream presentation V25+ language-role tests passed")
