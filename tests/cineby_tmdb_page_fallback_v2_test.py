#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "provider_patches" / "cineby_runtime_v1.py"

spec = importlib.util.spec_from_file_location("cineby_runtime", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load Cineby runtime Lego")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fallback = module.render_cineby_page_fallback(
    site_base="https://cineby.top",
    user_agent="NiakVIO-Cineby-Test",
)

# Downstream players are intentionally absent from persisted runtime code. They
# must be discovered from the current Cineby page on every request.
for forbidden in (
    "peachify.top",
    "superflixapi.buzz",
    "embedmaster.link",
    "embdmstrplayer.com",
    "vidflix.club",
):
    assert forbidden not in fallback, forbidden

node = f'''
const requests=[];
globalThis.getStreams=async function(){{return [];}};
function response(url, body, status=200){{return {{ok:status>=200&&status<400,status,url,text:async()=>body,json:async()=>JSON.parse(body)}};}}
globalThis.fetch=async function(url, options){{
  url=String(url);requests.push({{url,headers:(options&&options.headers)||{{}}}});
  if(url==='https://cineby.top/film/1386315') return response(url,'<iframe id="player" src="https://peachify.top/?type=movie&amp;id=1386315"></iframe>');
  if(url==='https://peachify.top/?type=movie&id=1386315') return response(url,'<video><source src="https://cdn.example.test/movie/1386315/master.m3u8"></video>');
  if(url==='https://cineby.top/series/95350') return response(url,
    '<iframe src="https://wrong-player.example/tv/95350/1/1"></iframe>'+
    '<iframe src="https://embedmaster.link/tv/95350/1/2"></iframe>');
  if(url==='https://wrong-player.example/tv/95350/1/1') return response(url,'<source src="https://cdn.example.test/tv/95350/1/1/master.m3u8">');
  if(url==='https://embedmaster.link/tv/95350/1/2') return response('https://embdmstrplayer.com/v2/ephemeral-token-abc','<script>var file="https://cdn.example.test/tv/95350/1/2/master.m3u8";</script>');
  return response(url,'',404);
}};
{fallback}
(async()=>{{
  const movie=await globalThis.getStreams('1386315','movie',1,1);
  const tv=await globalThis.getStreams('95350','tv',1,2);
  process.stdout.write(JSON.stringify({{movie,tv,requests}}));
}})().catch(e=>{{console.error(e);process.exit(1)}});
'''
proc = subprocess.run(
    ["node", "-e", node],
    cwd=ROOT,
    capture_output=True,
    text=True,
    timeout=20,
    check=False,
)
if proc.returncode != 0:
    raise AssertionError(proc.stderr or proc.stdout)
result = json.loads(proc.stdout)

assert [row["url"] for row in result["movie"]] == [
    "https://cdn.example.test/movie/1386315/master.m3u8"
], result
assert [row["url"] for row in result["tv"]] == [
    "https://cdn.example.test/tv/95350/1/2/master.m3u8"
], result
urls = [row["url"] for row in result["requests"]]
assert "https://cineby.top/film/1386315" in urls, urls
assert "https://cineby.top/series/95350" in urls, urls
assert "https://peachify.top/?type=movie&id=1386315" in urls, urls
assert "https://embedmaster.link/tv/95350/1/2" in urls, urls
assert "https://wrong-player.example/tv/95350/1/1" not in urls, urls

# Playback headers refer to the dynamically resolved player page, while Cineby
# remains the provider origin. The signed redirect itself is runtime-only.
assert result["tv"][0]["headers"]["Referer"] == "https://embdmstrplayer.com/v2/ephemeral-token-abc", result
assert result["tv"][0]["headers"]["Origin"] == "https://cineby.top", result

print("CINEBY_TMDB_PAGE_FALLBACK_V2_OK movie_entry=1 tv_entry=1 episode_root_guard=1 dynamic_player_crawl=1 persisted_player_hosts=0")
