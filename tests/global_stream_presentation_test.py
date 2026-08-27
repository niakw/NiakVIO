#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / "scripts" / "provider_patches"
NORMALIZER = ROOT / "scripts" / "normalize_stream_presentation_v12.py"


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


normalizer = load_path(NORMALIZER, "normalize_stream_presentation_v12")
normalizer.normalize(apply=True)
normalizer.assert_contract()
presentation = load_path(PATCHES / "global_stream_presentation_v1.py", "global_stream_presentation_v1")
assert presentation.REVISION == "all-providers-title-quality-ordered-description-native-tmdb-fail-open-v15-jvm-json-utf8"


def run(source: str, provider_id: str, call: str, fetch_impl: str | None = None):
    patched = presentation.apply(source, context={"provider_id": provider_id})
    assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in patched
    assert "all-providers-title-quality-ordered-description-native-tmdb-fail-open-v15-jvm-json-utf8" in patched
    assert patched == presentation.apply(patched, context={"provider_id": provider_id})
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(patched, encoding="utf-8")
        fetch = fetch_impl or "async function(){throw new Error('offline')}"
        runner.write_text(
            "global.fetch=" + fetch + ";\nconst p=require(" + json.dumps(str(provider)) + ");\n" + call + "\n",
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
        return json.loads(result.stdout.strip())


tmdb = r"""async function(url){
  if(!String(url).includes('api.themoviedb.org')) throw new Error('unexpected playback fetch');
  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}})};
}"""

# Provider VF: VF + VOSTFR evidence is one normalized MULTI VF/VO presentation.
source = "module.exports={getStreams:async()=>[{name:'Purstream | 4K | VF',url:'https://media.example/master.m3u8',quality:'4K',language:'VF',subtitles:'VOSTFR',codec:'x265 10bit',audio:'DDP 5.1',duration:169,sourceType:'WEB-DL',format:'m3u8',size:'8.4 GB',headers:{Referer:'https://purstream.example/'}}]};\n"
row = run(source, "purstream", "p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))", tmdb)
assert row["title"] == "Purstream - 4K", row
assert row["quality"] == "2160p"
assert row["language"] == "MULTI (VF/VO)", row
assert row["codec"] == "HEVC"
assert row["duration"] == 169
assert row["sourceType"] == "WEB-DL"
assert row["format"] == "HLS"
assert row["size"] == "8.4 GB"
assert row["headers"] == {"Referer": "https://purstream.example/"}
assert {"4k-ultra-hd", "webdl", "hevc", "multi"}.issubset(set(row["badgeIds"])), row
lines = row["description"].splitlines()
assert lines[0] == "🎬 Interstellar • 2014", lines
assert lines[1] == "⏱ 2h49 • 🔞 -12", lines
assert lines[2] == "🇫🇷 MULTI (VF/VO)", lines
assert lines[3].startswith("🎞️ WEB-DL"), lines
assert "HEVC 10bit" in lines[3] and "HLS" in lines[3] and "💾 8.4 GB" in lines[3]
assert "2160p" not in row["description"] and "4K" not in row["description"]
assert "Unknown" not in row["description"]

# NuvioTV's official local-plugin model discards provider description and maps
# LocalScraperResult.size -> Stream.description. On TV only, tunnel the complete
# Core description through size so emojis/technical facts and regex badge tokens survive.
tv_row = run(
    source,
    "purstream",
    "global.TMDB_API_KEY='tv-key';global.SCRAPER_ID='purstream';p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))",
    tmdb,
)
assert tv_row["size"] == tv_row["description"], tv_row
assert tv_row["description"].splitlines()[0] == "🎬 Interstellar • 2014"
assert "⏱ 2h49" in tv_row["description"] and "🔞 -12" in tv_row["description"]
assert "🇫🇷 MULTI (VF/VO)" in tv_row["description"]
assert "🎞️ WEB-DL" in tv_row["description"] and "HEVC 10bit" in tv_row["description"]
assert "💾 8.4 GB" in tv_row["description"]

# Generic French tokens normalize to VF; explicit Canadian French stays VFQ.
vf = run("module.exports={getStreams:async()=>[{name:'Movix',url:'https://x.example/a.mp4',language:'fr',quality:'1080p'}]};\n", "movix", "p.getStreams({mediaType:'movie',title:'Film',year:2026}).then(v=>console.log(JSON.stringify(v[0])))")
assert vf["language"] == "VF" and "🇫🇷 VF" in vf["description"]
assert vf["title"] == "Movix - 1080p"
assert "1080p" not in vf["description"]
assert "BLU-RAY" not in vf["description"]
assert "vf" in vf["badgeIds"]

vfq = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.mp4',language:'fr-CA VFQ'}]};\n", "purstream", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vfq["language"] == "VFQ" and "🇫🇷 VFQ" in vfq["description"]
assert "vfq" in vfq["badgeIds"]

# VOSTFR alone keeps the world+France marker, it is not promoted to VF/MULTI.
vost = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.m3u8',language:'VOSTFR'}]};\n", "purstream", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vost["language"] == "VOSTFR" and "🌐🇫🇷 VOSTFR" in vost["description"]

# A VO-catalog provider keeps world VO/MULTI semantics and never gets a French flag.
vo = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.m3u8',language:'VO'}]};\n", "cineby", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vo["language"] == "VO" and "🌐 VO" in vo["description"] and "🇫🇷" not in vo["description"]
vo_multi = run("module.exports={getStreams:async()=>[{name:'Test',url:'https://x.example/a.m3u8',language:'MULTI'}]};\n", "cineby", "p.getStreams({mediaType:'movie',title:'Film'}).then(v=>console.log(JSON.stringify(v[0])))")
assert vo_multi["language"] == "MULTI" and "🌐 MULTI" in vo_multi["description"]

# Series/anime identity is title/year/SxxExx; provider-owned layout never survives.
tv = run("module.exports={getStreams:async()=>[{name:'Purstream',url:'https://x.example/a.m3u8',description:'PRIVATE PROVIDER LAYOUT',language:'VF'}]};\n", "purstream", "p.getStreams({mediaType:'tv',title:'Breaking Bad',year:2008,season:1,episode:1}).then(v=>console.log(JSON.stringify(v[0])))")
assert tv["description"].splitlines()[0] == "📺 Breaking Bad • 2008 • S01E01"
assert "PRIVATE PROVIDER LAYOUT" not in tv["description"]

# Sparse provider data keeps safe TMDB/request context but invents no technical facts.
sparse = run("module.exports={getStreams:async()=>[{name:'Cineby',url:'https://x.example/a.mp4',description:'Unknown'}]};\n", "cineby", "p.getStreams({mediaType:'movie',title:'Sinners',year:2025}).then(v=>console.log(JSON.stringify(v[0])))")
assert "🎬 Sinners • 2025" in sparse["description"]
assert "Unknown" not in sparse["description"]
assert "BLU-RAY" not in sparse["description"]

# Native Desktop bridge: optional TMDB enrichment is skipped when the client does
# not expose a runtime-owned TMDB_API_KEY. Provider streams must return immediately.
desktop_native = run(
    "module.exports={getStreams:async()=>[{name:'Cineby',url:'https://x.example/a.mp4',quality:'1080p',language:'VO'}]};\n",
    "cineby",
    "global.__native_fetch=async()=>{throw new Error('unexpected native TMDB fetch')};let calls=0;global.fetch=async()=>{calls++;throw new Error('TMDB must be skipped')};p.getStreams('157336','movie').then(v=>console.log(JSON.stringify({row:v[0],calls})))",
)
assert desktop_native["calls"] == 0, desktop_native
assert desktop_native["row"]["title"] == "Cineby - 1080p", desktop_native
assert desktop_native["row"]["url"] == "https://x.example/a.mp4", desktop_native

print("global stream presentation V15 JVM-safe JSON contract tests passed")