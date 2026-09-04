#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides  # noqa: E402


def clean_v3_fixture(source: str) -> str:
    return (
        "/* BEGIN NIAKVIO_PROVIDER */\n"
        "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
        + source.rstrip()
        + "\n/* END NIAKVIO_PROVIDER */\n"
    )


def materialize(stream_source: str) -> str:
    payload, _records = apply_overrides(
        "purstream",
        clean_v3_fixture(stream_source).encode("utf-8"),
        phase="discovery",
    )
    return payload.decode("utf-8")


def run_node(output: str, script: str, prefix: str) -> dict:
    with tempfile.TemporaryDirectory(prefix=prefix) as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(output, encoding="utf-8")
        runner.write_text(script.replace("__PROVIDER__", json.dumps(str(provider))), encoding="utf-8")
        completed = subprocess.run(
            ["node", str(runner)],
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=20,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        return json.loads(completed.stdout.strip())


source = (
    "module.exports={getStreams:async()=>[{"
    "name:'Purstream - Inconnue',title:'Unknown',description:'Inconnue',quality:'Unknown',"
    "language:'VF',url:'https://media.example/1080p/master.m3u8'"
    "}]};\n"
)
output = materialize(source)

# Existing UI contract must remain byte-shape compatible.
for needle in (
    '"🎬 "+media',
    '"📺 "+media',
    '"⏱ "+humanDuration',
    '"🔞 "+f.ageRating',
    'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"")',
    'out.description=lines.join("\\n")',
    'out.badgeIds=badgeIds(f)',
    'out.displayBadges=badgeLabels(f)',
):
    assert needle in output, needle

movie = run_node(
    output,
    """
global.__native_fetch=function(){};
let tmdbCalls=0;
let mediaCalls=0;
global.fetch=async function(url){
  url=String(url);
  if(url.includes('api.themoviedb.org/3/movie/157336')){
    tmdbCalls++;
    return {
      ok:true,status:200,url:url,
      headers:{get:function(){return 'application/json';}},
      json:async()=>({
        id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,
        genres:[{id:18,name:'Drama'}],original_language:'en',
        production_countries:[{iso_3166_1:'US'}],keywords:{keywords:[]},
        alternative_titles:{titles:[]},external_ids:{imdb_id:'tt0816692'},
        release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}
      }),
      text:async()=>''
    };
  }
  if(url.includes('media.example/1080p/master.m3u8')){
    mediaCalls++;
    return {
      ok:true,status:200,url:url,
      headers:{get:function(name){return String(name).toLowerCase()==='content-type'?'application/vnd.apple.mpegurl':null;}},
      text:async()=> '#EXTM3U\\n#EXT-X-TARGETDURATION:120\\n#EXTINF:120,\\nhttps://media.example/seg.ts\\n#EXT-X-ENDLIST'
    };
  }
  throw new Error('unexpected fetch '+url);
};
const p=require(__PROVIDER__);
p.getStreams('157336','movie',undefined,undefined).then(function(rows){
  const row=rows[0]||{};
  console.log(JSON.stringify({row:row,tmdbCalls:tmdbCalls,mediaCalls:mediaCalls}));
}).catch(function(error){console.error(error&&error.stack||error);process.exit(1);});
""",
    "niakvio-purstream-movie-metadata-fallback-",
)
row = movie["row"]
rendered = "\n".join(str(row.get(key) or "") for key in ("name", "title", "description", "size"))
assert "unknown" not in rendered.casefold(), rendered
assert "inconnue" not in rendered.casefold(), rendered
assert row["title"].endswith(" - 1080p"), row
assert row["name"] == row["title"], row
assert "Interstellar • 2014" in row["description"], row
assert "⏱ 2h49" in row["description"], row
assert "🔞 -12" in row["description"], row
assert "🇫🇷 VF" in row["description"], row
assert row["duration"] == 169, row
assert row["ageRating"] == "-12", row
assert "1080p-full-hd" in row["badgeIds"], row
assert "vf" in row["badgeIds"], row
assert row["size"] == row["description"], row
assert movie["tmdbCalls"] == 1, movie

# TV/episode path: series metadata provides identity + age, episode metadata
# overrides runtime. The established 📺/⏱/🔞/language layout stays unchanged.
tv_output = materialize(
    "module.exports={getStreams:async()=>[{"
    "name:'Purstream - Unknown',title:'Inconnue',description:'Unknown',quality:'Unknown',"
    "language:'VF',url:'https://media.example/720p/master.m3u8'"
    "}]};\n"
)
tv = run_node(
    tv_output,
    """
global.__native_fetch=function(){};
let tmdbCalls=0;
let mediaCalls=0;
global.fetch=async function(url){
  url=String(url);
  if(url.includes('api.themoviedb.org/3/tv/1396/season/1/episode/1')){
    tmdbCalls++;
    return {
      ok:true,status:200,url:url,
      headers:{get:function(){return 'application/json';}},
      json:async()=>({id:62085,name:'Pilot',air_date:'2008-01-20',runtime:58}),
      text:async()=>''
    };
  }
  if(url.includes('api.themoviedb.org/3/tv/1396')){
    tmdbCalls++;
    return {
      ok:true,status:200,url:url,
      headers:{get:function(){return 'application/json';}},
      json:async()=>({
        id:1396,name:'Breaking Bad',first_air_date:'2008-01-20',episode_run_time:[47],
        genres:[{id:18,name:'Drama'}],original_language:'en',origin_country:['US'],
        keywords:{results:[]},alternative_titles:{results:[]},external_ids:{imdb_id:'tt0903747'},
        content_ratings:{results:[{iso_3166_1:'FR',rating:'-16'}]}
      }),
      text:async()=>''
    };
  }
  if(url.includes('media.example/720p/master.m3u8')){
    mediaCalls++;
    return {
      ok:true,status:200,url:url,
      headers:{get:function(name){return String(name).toLowerCase()==='content-type'?'application/vnd.apple.mpegurl':null;}},
      text:async()=> '#EXTM3U\\n#EXT-X-TARGETDURATION:120\\n#EXTINF:120,\\nhttps://media.example/seg.ts\\n#EXT-X-ENDLIST'
    };
  }
  throw new Error('unexpected fetch '+url);
};
const p=require(__PROVIDER__);
p.getStreams('1396','tv',1,1).then(function(rows){
  const row=rows[0]||{};
  console.log(JSON.stringify({row:row,tmdbCalls:tmdbCalls,mediaCalls:mediaCalls}));
}).catch(function(error){console.error(error&&error.stack||error);process.exit(1);});
""",
    "niakvio-purstream-tv-metadata-fallback-",
)
tv_row = tv["row"]
tv_rendered = "\n".join(str(tv_row.get(key) or "") for key in ("name", "title", "description", "size"))
assert "unknown" not in tv_rendered.casefold(), tv_rendered
assert "inconnue" not in tv_rendered.casefold(), tv_rendered
assert tv_row["title"].endswith(" - 720p"), tv_row
assert tv_row["name"] == tv_row["title"], tv_row
assert "Breaking Bad • 2008 • S01E01" in tv_row["description"], tv_row
assert "⏱ 58min" in tv_row["description"], tv_row
assert "🔞 -16" in tv_row["description"], tv_row
assert "🇫🇷 VF" in tv_row["description"], tv_row
assert tv_row["duration"] == 58, tv_row
assert tv_row["ageRating"] == "-16", tv_row
assert "720p-hd" in tv_row["badgeIds"], tv_row
assert "vf" in tv_row["badgeIds"], tv_row
assert tv_row["size"] == tv_row["description"], tv_row
assert tv["tmdbCalls"] == 2, tv

print("stream presentation metadata fallback preserves existing UI for movie and TV episode")
