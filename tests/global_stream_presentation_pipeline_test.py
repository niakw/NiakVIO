#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import (  # noqa: E402
    apply_overrides,
    GLOBAL_MEDIA_TYPE_RESOLUTION,
    GLOBAL_STREAM_PRESENTATION,
)


def clean_v3_fixture(source: str) -> str:
    if "/* BEGIN NIAKVIO_PROVIDER */" in source:
        assert "NIAKVIO_PROVIDER_BASE_OWNED_V3" in source
        return source
    return (
        "/* BEGIN NIAKVIO_PROVIDER */\n"
        "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
        + source.rstrip()
        + "\n/* END NIAKVIO_PROVIDER */\n"
    )


def apply(provider: str, source: str) -> tuple[str, list[dict]]:
    source = clean_v3_fixture(source)
    payload, records = apply_overrides(provider, source.encode("utf-8"), phase="discovery")
    return payload.decode("utf-8"), records


# Facts and presentation are Core-wide layers, never provider-specific adapters.
for provider in ("purstream", "movix", "cineby", "animepahe", "goated"):
    source = "module.exports={getStreams:async()=>[{name:'X 4K VFF HEVC E-AC3 5.1 WEB-DL',url:'https://media.example/a.m3u8'}]};\n"
    output, records = apply(provider, source)
    assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in output, provider
    assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in output, provider
    assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in output, provider
    assert output.index("NUVIO_GLOBAL_STREAM_FACTS_V1") < output.index("NUVIO_GLOBAL_STREAM_IDENTITY_V1"), provider
    assert output.index("NUVIO_GLOBAL_STREAM_IDENTITY_V1") < output.index("NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1"), provider
    assert output.index("NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1") < output.index("NUVIO_GLOBAL_STREAM_PRESENTATION_V1"), provider
    assert any(
        row.get("path") == GLOBAL_MEDIA_TYPE_RESOLUTION
        and row.get("scope") == "global_media_type_resolution"
        for row in records
    ), (provider, records)
    assert any(
        row.get("path") == GLOBAL_STREAM_PRESENTATION
        and row.get("scope") == "global_stream_presentation"
        for row in records
    ), (provider, records)


# Native scalar contract: presentation is output-only and must run after deferred
# positive-result TMDB verification. This reproduces the official 4-argument
# getStreams(tmdbId, mediaType, season, episode) clients.
native_source, _ = apply(
    "generic-core-test",
    "module.exports={getStreams:async()=>[{name:'Source 1080p WEB-DL HEVC E-AC3 5.1',url:'https://media.example/master.m3u8'}]};\n",
)
with tempfile.TemporaryDirectory(prefix="niakvio-presentation-order-") as raw:
    root = Path(raw)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(native_source, encoding="utf-8")
    runner.write_text(
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
        release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}
      }),
      text:async()=>''
    };
  }
  if(url.includes('media.example/master.m3u8')){
    mediaCalls++;
    return {
      ok:true,status:200,url:url,
      headers:{get:function(name){return String(name).toLowerCase()==='content-type'?'application/vnd.apple.mpegurl':null;}},
      text:async()=> '#EXTM3U\\n#EXT-X-TARGETDURATION:6\\n#EXTINF:6,\\nhttps://media.example/seg.ts\\n#EXT-X-ENDLIST'
    };
  }
  throw new Error('unexpected fetch '+url);
};
const p=require(""" + json.dumps(str(provider)) + """);
p.getStreams('157336','movie',undefined,undefined).then(function(rows){
  const row=rows[0]||{};
  console.log(JSON.stringify({row:row,tmdbCalls:tmdbCalls,mediaCalls:mediaCalls}));
}).catch(function(error){console.error(error&&error.stack||error);process.exit(1);});
""",
        encoding="utf-8",
    )
    completed = subprocess.run(
        ["node", str(runner)],
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    native = json.loads(completed.stdout.strip())
    assert native["tmdbCalls"] == 1, native
    assert native["row"]["title"].endswith(" - 1080p"), native
    assert native["row"]["duration"] == 169, native
    assert "Interstellar • 2014" in native["row"]["description"], native
    assert "⏱ 2h49" in native["row"]["description"], native
    assert "🔞 -12" in native["row"]["description"], native
    assert {"1080p-full-hd", "webdl", "hevc", "dolby-digital-plus", "5.1"}.issubset(
        set(native["row"]["badgeIds"])
    ), native

# Reapplication is idempotent: global Core wrappers are replaced/reused, never stacked.
first, _ = apply("cineby", "module.exports={getStreams:async()=>[]};\n")
second, _ = apply("cineby", first)
assert second.count("NUVIO_GLOBAL_STREAM_FACTS_V1") == 1
assert second.count("NUVIO_GLOBAL_STREAM_IDENTITY_V1") == 1
assert second.count("NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1") == 1
assert second.count("NUVIO_GLOBAL_STREAM_PRESENTATION_V1") == 1

apply_source = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
presentation_source = (ROOT / "scripts/provider_patches/global_stream_presentation_v1.py").read_text(encoding="utf-8")
assert "GLOBAL_STREAM_PRESENTATION" in apply_source
assert '"scope": "global_stream_presentation"' in apply_source
assert "FACTS_PATH" in presentation_source
assert "global_stream_facts_v1.py" in presentation_source
assert "purstream_stream_facts_v1.py" not in presentation_source
assert not (ROOT / "scripts/provider_patches/purstream_stream_facts_v1.py").exists()

print("global stream facts/presentation pipeline tests passed")
