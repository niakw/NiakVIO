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

materialization = json.loads((ROOT / "provider-v3-materialization.json").read_text(encoding="utf-8"))
rows = [row for row in materialization.get("providers") or [] if isinstance(row, dict)]
assert materialization.get("providerCount") == 96, materialization.get("providerCount")
assert len(rows) == 96, len(rows)
required_core = {
    "CORE.STREAM_FACTS.V1",
    "CORE.STREAM_IDENTITY.V1",
    "CORE.MEDIA_TYPE_RESOLUTION.V1",
    "CORE.STREAM_PRESENTATION.V1",
    "CORE.STREAM_SANITIZER.V6",
}
for row in rows:
    missing = required_core - set(row.get("fixIds") or [])
    assert not missing, (row.get("provider"), sorted(missing))

facts_source = (ROOT / "scripts/provider_patches/global_stream_facts_v1.py").read_text(encoding="utf-8")
for token in (
    "NUVIO_STREAM_SOURCE_METADATA_PRESERVATION_V2",
    'keep(out,"sourceName",row.name,512)',
    'keep(out,"sourceTitle",row.title,512)',
    'keep(out,"sourceDescription",row.description,4096)',
    'keep(out,"sourceSize",row.size,256)',
    'keep(out,"sourceQuality",row.quality,128)',
    'keep(out,"sourceResolution",row.resolution,128)',
    'keep(out,"sourceLanguage",row.language,128)',
    'keep(out,"sourceCodec",row.codec,128)',
    'keep(out,"sourceAudio",row.audio,256)',
    'keep(out,"sourceTypeRaw",row.sourceType,128)',
    'keep(out,"releaseTypeRaw",row.releaseType,128)',
    'keep(out,"sourceFormat",row.format,128)',
):
    assert token in facts_source, token

source = r'''
/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
module.exports={getStreams:async()=>[{
  name:'Provider Original Name',
  title:'Provider Original Title',
  description:'Provider original technical description',
  size:'9.8 GB',
  quality:'4K',
  resolution:'3840x2160',
  height:2160,
  width:3840,
  language:'VFF',
  codec:'HEVC',
  audio:'E-AC3 5.1',
  sourceType:'WEB-DL',
  releaseType:'REMUX',
  format:'HLS',
  url:'https://media.example/master.m3u8',
  headers:{Referer:'https://provider.example/watch/42','User-Agent':'Neutral-UA'},
  opaqueProviderField:'keep-me'
}]};
/* END NIAKVIO_PROVIDER */
'''
patched, _records = apply_overrides(
    "generic-core-test",
    source.encode("utf-8"),
    phase="discovery",
)

with tempfile.TemporaryDirectory(prefix="niakvio-metadata-preservation-") as raw:
    root = Path(raw)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_bytes(patched)
    runner.write_text(
        """
global.TMDB_API_KEY='0123456789abcdef0123456789abcdef';
global.__native_fetch=function(){};
global.fetch=async function(url,options){
  url=String(url);
  if(url.includes('api.themoviedb.org/3/movie/157336')){
    return {ok:true,status:200,url:url,headers:{get:function(){return 'application/json';}},json:async()=>({
      id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,
      genres:[{id:18,name:'Drama'}],original_language:'en',production_countries:[{iso_3166_1:'US'}],
      keywords:{keywords:[]},release_dates:{results:[]}
    }),text:async()=>''};
  }
  if(url.includes('media.example/master.m3u8')){
    return {ok:true,status:200,url:url,headers:{get:function(name){return String(name).toLowerCase()==='content-type'?'application/vnd.apple.mpegurl':null;}},text:async()=> '#EXTM3U\\n#EXT-X-TARGETDURATION:120\\n#EXTINF:120,\\nhttps://media.example/seg.ts\\n#EXT-X-ENDLIST'};
  }
  throw new Error('unexpected fetch '+url);
};
const p=require(""" + json.dumps(str(provider)) + """);
p.getStreams('157336','movie').then(function(rows){console.log(JSON.stringify(rows[0]||{}));}).catch(function(error){console.error(error&&error.stack||error);process.exit(1);});
""",
        encoding="utf-8",
    )
    completed = subprocess.run(
        ["node", str(runner)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    row = json.loads(completed.stdout.strip())

assert row["sourceName"] == "Provider Original Name", row
assert row["sourceTitle"] == "Provider Original Title", row
assert row["sourceDescription"] == "Provider original technical description", row
assert row["sourceSize"] == "9.8 GB", row
assert row["sourceQuality"] == "4K", row
assert row["sourceResolution"] == "3840x2160", row
assert row["sourceLanguage"] == "VFF", row
assert row["sourceCodec"] == "HEVC", row
assert row["sourceAudio"] == "E-AC3 5.1", row
assert row["sourceTypeRaw"] == "WEB-DL", row
assert row["releaseTypeRaw"] == "REMUX", row
assert row["sourceFormat"] == "HLS", row

# Canonical facts may normalize presentation values, but they may not disappear.
assert row.get("quality") == "2160p", row
assert row.get("resolution") == "3840x2160", row
assert row.get("height") == 2160 and row.get("width") == 3840, row
assert row.get("language") in {"VF", "VFF"}, row
assert row.get("codec") == "HEVC", row
assert "E-AC3" in str(row.get("audio") or ""), row
assert row.get("sourceType") == "WEB-DL", row
assert row.get("releaseType") == "REMUX", row
assert row.get("format") == "HLS", row
assert row.get("url") == "https://media.example/master.m3u8", row
assert row.get("headers", {}).get("Referer") == "https://provider.example/watch/42", row
assert row.get("headers", {}).get("User-Agent") == "Neutral-UA", row
assert row.get("opaqueProviderField") == "keep-me", row

print("global stream metadata preservation contract passed for shared 96-provider Core")
