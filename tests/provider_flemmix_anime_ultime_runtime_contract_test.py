#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]
hubs=json.loads((ROOT/"provider-hubs.json").read_text(encoding="utf-8"))["providers"]

flemmix=(ROOT/"scripts/provider_patches/flemmix_runtime_v1.py").read_text(encoding="utf-8")
anime=(ROOT/"scripts/provider_patches/anime_ultime_runtime_v1.py").read_text(encoding="utf-8")

assert "NIAKVIO_FLEMMIX_RUNTIME_V1" in flemmix
assert "function runtimeBase()" in flemmix
assert 'm&&(m.officialSite||m.knownSite)||c.base' in flemmix
assert '"/search?q="' in flemmix
assert "video-server-tab" in flemmix and "episode-server-tab" in flemmix
assert "saison-" in flemmix and "_crawlDirectMedia" in flemmix
assert "arm.haglund.dev" not in flemmix

assert "NIAKVIO_ANIME_ULTIME_RUNTIME_V1" in anime
assert "/MenuSearch.html" in anime
assert "/VideoPlayer.html" in anime
assert "data-serie" in anime and "data-focus" in anime
assert "arm.haglund.dev" not in anime

assert ov["flemmix"]["provider_lego_scripts"] == ["scripts/provider_patches/flemmix_runtime_v1.py"]
assert "api_recipe" not in ov["flemmix"]
assert ov["flemmix"]["learned_routes"]==["/search?q={query}"]
assert ov["flemmix"]["search_request_plan"][0]["route"]=="/search?q={query}"
assert ov["flemmix"]["provider_lego_options"]["scripts/provider_patches/flemmix_runtime_v1.py"]["base"] == "https://flemmix.me"
assert '"base": "https://flemmix.me"' in flemmix
assert ov["flemmix"]["official_site"] == "https://flemmix.me"
assert hubs["flemmix"]["direct"] == "https://flemmix.me/"
assert hubs["flemmix"]["direct_authority"] == "explicit_current"
flemmix_js=flemmix.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
assert flemmix_js.count("c.base")==2, "only runtimeBase fallback may reference the configured Flemmix base"
assert ov["flemmix"]["domain_substitutions"]["flemmix.cloud"] == "flemmix.me"
assert "flemmix.me" not in ov["flemmix"]["domain_substitutions"]
compiled=flemmix_js.replace("CONFIG_PLACEHOLDER",json.dumps({"base":"https://flemmix.me","userAgent":"Mozilla/5.0"}))
subprocess.run(["node","-e","new Function(process.argv[1]);",compiled],check=True)
behavior=r'''
global.fetch=async function(url){
  url=String(url);
  function R(body){return {ok:true,status:200,async text(){return body},async json(){return JSON.parse(body)},headers:{get(){return "text/html"}}}}
  if(url.includes("/search?q=Interstellar")) return R('<a href="/film-en-streaming/interstellar">Interstellar</a>');
  if(url.endsWith("/film-en-streaming/interstellar")) return R('<button class="video-server-tab" data-url="https://player.example/e/abc"><span class="lang-pill">VF</span><span class="quality-pill">1080p</span></button>');
  return {ok:false,status:404,async text(){return ""},headers:{get(){return "text/html"}}};
};
global.__nuvioCoreGetTmdbDataV1=async()=>({state:"ok",metadata:{title:"Interstellar",original_title:"Interstellar"}});
global._crawlDirectMedia=async()=>[{url:"https://cdn.example/interstellar.m3u8",quality:"1080p"}];
''' + compiled + r'''
(async()=>{
  const hook=global.__niakvioProviderRuntimeResolverV1;
  if(!hook) throw new Error("hook missing");
  const out=await hook.resolve(["157336","movie"]);
  if(!Array.isArray(out)||out.length!==1||out[0].url!=="https://cdn.example/interstellar.m3u8") throw new Error(JSON.stringify(out));
  console.log("FLEMMIX_CURRENT_SEARCH_BEHAVIOR_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",behavior],check=True)
assert ov["anime-ultime"]["provider_lego_scripts"] == ["scripts/provider_patches/anime_ultime_runtime_v1.py"]
assert "api_recipe" not in ov["anime-ultime"]
assert "candidate_api_recipe" not in ov["anime-ultime"]
assert ov["anime-ultime"]["learned_routes"] == ["/MenuSearch.html", "/VideoPlayer.html"]
assert ov["anime-ultime"]["source_runtime_family"] == "menu-search-series-focus-player"

print("Flemmix and Anime-Ultime provider runtime contracts passed")
