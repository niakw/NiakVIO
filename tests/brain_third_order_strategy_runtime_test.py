#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

runtime_spec = importlib.util.spec_from_file_location(
    "runtime_repair_third_order",
    ROOT / "scripts/adaptive_runtime/runtime_repair.py",
)
assert runtime_spec and runtime_spec.loader
runtime = importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime)

generator_spec = importlib.util.spec_from_file_location(
    "runtime_recovery_generator_third_order",
    ROOT / "scripts/adaptive_runtime/runtime_recovery_generator.py",
)
assert generator_spec and generator_spec.loader
generator = importlib.util.module_from_spec(generator_spec)
generator_spec.loader.exec_module(generator)

expected = {
    "identity_alias_search_traversal_v1",
    "runtime_response_salvage_v1",
    "document_request_contract_mining_v1",
    "provider_session_bootstrap_replay_v1",
}
for profile in expected:
    assert runtime._is_causal_strategy_profile(profile), profile

config = {
    "provider_patches": {
        "synthetic-third-order": {
            "official_site": "https://provider.example",
            "documented_routes": [
                "/?s={query}",
                "/detail/{slug}",
                "/player/{id}",
                "/api/source/{id}",
            ],
        }
    },
    "provider_capabilities": {
        "synthetic-third-order": {
            "strategy": "html_scraper",
            "catalogue_types": ["movie"],
        }
    },
}

def candidate(profile: str, failure: str, status: str = "ROUTE PROVEN"):
    return {
        "canonical_id": "synthetic-third-order",
        "metadata": {
            "name": "Synthetic",
            "supportedTypes": ["movie"],
            "baseUrl": "https://provider.example",
        },
        "censusPrior": {"status": status},
        "brain_repair_plan": {
            "failureClass": failure,
            "experimentVariant": 4,
            "experimentGeneration": 5,
            "postExhaustionStrategyProfile": profile,
            "postExhaustionStrategyMethod": "third-order-test",
            "negativeMemoryMatches": 20,
        },
    }

alias_options = runtime._adaptive_runtime_options(
    candidate("identity_alias_search_traversal_v1", "route_proven_gap"),
    config,
)
assert alias_options and alias_options["alias_search"] is True, alias_options
assert alias_options["runtime_response_salvage"] is False, alias_options
assert "/?s={query}" in alias_options["search_paths"], alias_options

salvage_options = runtime._adaptive_runtime_options(
    candidate("runtime_response_salvage_v1", "chain_terminal_gap", "CHAIN REACHED"),
    config,
)
assert salvage_options and salvage_options["runtime_response_salvage"] is True, salvage_options

terminal_options = runtime._adaptive_runtime_options(
    candidate("terminal_transition_graph_v1", "chain_terminal_gap", "CHAIN REACHED"),
    {
        "provider_patches": {
            "synthetic-third-order": {
                "official_site": "https://provider.example",
                "documented_routes": [
                    "/search?q={query}",
                    "/movie/{id}/{slug}.xhtml",
                    "/confirm/{id}/{fileId}/{slug}.xhtml",
                    "/internal/{id}/{fileId}/{slug}.xhtml",
                    "/api/file/",
                ],
            }
        },
        "provider_capabilities": config["provider_capabilities"],
    },
)
assert terminal_options and terminal_options["runtime_response_salvage"] is True, terminal_options
assert terminal_options["transition_prefixes"][:2] == ["/confirm/", "/internal/"], terminal_options
assert "/movie/" not in terminal_options["transition_prefixes"], terminal_options

form_options = runtime._adaptive_runtime_options(
    candidate("document_request_contract_mining_v1", "media_extraction_gap", "CHAIN REACHED"),
    config,
)
assert form_options and form_options["document_request_mining"] is True, form_options

session_options = runtime._adaptive_runtime_options(
    candidate("provider_session_bootstrap_replay_v1", "provider_transport_gap", "PROVIDER NETWORK BLOCKED"),
    config,
)
assert session_options and session_options["session_bootstrap"] is True, session_options

planner = (ROOT / "engine_v2/scripts/plan-repairs.mjs").read_text(encoding="utf-8")
for profile in expected:
    assert profile in planner, profile

# The generated runtime must contain materially different executable algorithms,
# not merely a different planner label.
generated = generator.apply(
    "module.exports={getStreams:async function(){return []}};",
    {
        "provider_name": "Synthetic",
        "base_url": "https://provider.example",
        "types": ["movie"],
        "search_paths": ["/?s={query}"],
        "direct_paths": [],
        "request_recipes": [],
        "new_strategy_id": "identity_alias_search_traversal_v1",
        "alias_search": True,
        "runtime_response_salvage": True,
        "document_request_mining": True,
        "session_bootstrap": True,
        "max_pages": 8,
        "max_embeds": 4,
        "max_depth": 3,
        "max_recipe_passes": 2,
        "timeout_ms": 3000,
    },
)
for marker in (
    '"aliasSearch":true',
    '"runtimeResponseSalvage":true',
    '"transitionPrefixes":',
    "function transitionUrls(",
    "function transitionMatch(",
    '"documentRequestMining":true',
    '"sessionBootstrap":true',
    "function documentForms(",
    "async function salvageRuntimeResponses(",
    "searchTitles=c.aliasSearch",
    "if(c.sessionBootstrap)",
):
    assert marker in generated, marker

# Real execution proof 1: localized FR metadata misses, original/alternate title
# hits the provider catalogue, and the alias strategy reaches terminal media.
base_alias = "module.exports={getStreams:async function(){return []}};"
alias_js = generator.apply(
    base_alias,
    {
        "provider_name": "AliasProvider",
        "base_url": "https://provider.example",
        "types": ["movie"],
        "search_paths": ["/?s={query}"],
        "direct_paths": [],
        "request_recipes": [],
        "new_strategy_id": "identity_alias_search_traversal_v1",
        "alias_search": True,
        "max_pages": 8,
        "max_embeds": 4,
        "max_depth": 3,
        "max_recipe_passes": 2,
        "timeout_ms": 3000,
    },
)

# Real execution proof 2: the provider itself gets a successful JSON response
# containing terminal media but still returns []; salvage must recover that
# already-observed response without inventing a provider-specific route.
base_salvage = (
    'module.exports={getStreams:async function(){'
    'await fetch("https://provider.example/api/current");return []}};'
)
salvage_js = generator.apply(
    base_salvage,
    {
        "provider_name": "SalvageProvider",
        "base_url": "https://provider.example",
        "types": ["movie"],
        "search_paths": [],
        "direct_paths": [],
        "request_recipes": [],
        "new_strategy_id": "runtime_response_salvage_v1",
        "runtime_response_salvage": True,
        "max_pages": 8,
        "max_embeds": 4,
        "max_depth": 3,
        "max_recipe_passes": 2,
        "timeout_ms": 3000,
    },
)

def run_node(module_source: str, scenario: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        module_path = td / "provider.cjs"
        runner_path = td / "runner.cjs"
        module_path.write_text(module_source, encoding="utf-8")
        runner_path.write_text(
            r'''
globalThis.TMDB_API_KEY="test";
const scenario=process.argv[2];
function response(body,type="text/html",status=200){
  const headers={
    get:(name)=>String(name||"").toLowerCase()==="content-type"?type:null,
    getSetCookie:()=>[],
  };
  return {
    ok:status>=200&&status<300,
    status,
    url:"",
    headers,
    text:async()=>String(body),
    json:async()=>JSON.parse(String(body)),
    clone(){return response(body,type,status)},
  };
}
globalThis.fetch=async function(url,init){
  url=String(url);
  if(url.includes("api.themoviedb.org")){
    return response(JSON.stringify({
      title:"La Colonie",
      original_title:"The Colony",
      release_date:"2021-08-27",
      alternative_titles:{titles:[{title:"The Colony"}]},
      external_ids:{imdb_id:"tt6506264"}
    }),"application/json");
  }
  if(scenario==="alias"){
    if(url.includes("%3Fs=")) throw new Error("unexpected encoded path");
    if(url.includes("?s=La%20Colonie")) return response("<html>aucun résultat</html>");
    if(url.includes("?s=The%20Colony")) return response('<a href="/the-colony-2021/">The Colony 2021</a>');
    if(url.includes("/the-colony-2021/")) return response('<a href="https://cdn.example/the-colony.m3u8">Play</a>');
  }
  if(scenario==="salvage"&&url.includes("/api/current")){
    return response(JSON.stringify({title:"Interstellar",source:"https://cdn.example/interstellar.m3u8"}),"application/json");
  }
  return response("not found","text/plain",404);
};
(async()=>{
  const provider=require(process.argv[3]);
  const rows=await provider.getStreams({tmdbId:"157336",mediaType:"movie",title:scenario==="salvage"?"Interstellar":"",year:scenario==="salvage"?2014:0});
  process.stdout.write(JSON.stringify(rows));
})().catch(e=>{console.error(e&&e.stack||e);process.exit(1)});
''',
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["node", str(runner_path), scenario, str(module_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        rows = json.loads(proc.stdout or "[]")
        assert isinstance(rows, list), rows
        return {"rows": rows, "stderr": proc.stderr}

alias_result = run_node(alias_js, "alias")
assert any(str(row.get("url") or "").endswith("/the-colony.m3u8") for row in alias_result["rows"]), alias_result

salvage_result = run_node(salvage_js, "salvage")
assert any(str(row.get("url") or "").endswith("/interstellar.m3u8") for row in salvage_result["rows"]), salvage_result

# Real execution proof 3: a CHAIN REACHED provider stops after a valid detail
# response. The Brain must use provider-owned route templates as recognition
# hints, mine neutral same-origin transitions from the already-observed document,
# and traverse them without any provider-specific repair code.
v5_spec = importlib.util.spec_from_file_location(
    "adaptive_v5_transition_test",
    ROOT / "scripts/provider_patches/adaptive_runtime_recovery_v5.py",
)
assert v5_spec and v5_spec.loader
v5 = importlib.util.module_from_spec(v5_spec)
v5_spec.loader.exec_module(v5)
base_transition = (
    'module.exports={getStreams:async function(){'
    'await fetch("https://provider.example/search?q=Interstellar");'
    'await fetch("https://provider.example/movie/42/interstellar.xhtml");'
    'return []}};'
)
transition_js = v5.apply(base_transition, options=terminal_options)

def run_transition(module_source: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        module_path = td / "provider.cjs"
        runner_path = td / "runner.cjs"
        module_path.write_text(module_source, encoding="utf-8")
        runner_path.write_text(
            r'''
globalThis.TMDB_API_KEY="test";
function response(body,type="text/html",status=200,url=""){
  const headers={get:(name)=>String(name||"").toLowerCase()==="content-type"?type:null,getSetCookie:()=>[]};
  return {ok:status>=200&&status<300,status,url,headers,text:async()=>String(body),json:async()=>JSON.parse(String(body)),clone(){return response(body,type,status,url)}};
}
globalThis.fetch=async function(url){
  url=String(url);
  if(url.includes("api.themoviedb.org")) return response(JSON.stringify({title:"Interstellar",release_date:"2014-11-05"}),"application/json",200,url);
  if(url==="https://provider.example/search?q=Interstellar") return response('<a href="/movie/42/interstellar.xhtml">Interstellar 2014</a>',"text/html",200,url);
  if(url==="https://provider.example/movie/42/interstellar.xhtml") return response('<script>window.next="\\/confirm\\/42\\/9\\/interstellar.xhtml"</script>',"text/html",200,url);
  if(url==="https://provider.example/confirm/42/9/interstellar.xhtml") return response('<div data-next="internal/42/9/interstellar.xhtml">continue</div>',"text/html",200,url);
  if(url==="https://provider.example/internal/42/9/interstellar.xhtml") return response('<script>var file="https://cdn.example/interstellar/master.m3u8"</script>',"text/html",200,url);
  if(url==="https://cdn.example/interstellar/master.m3u8") return response("#EXTM3U\n#EXT-X-VERSION:3\n","application/vnd.apple.mpegurl",200,url);
  return response("not found","text/plain",404,url);
};
(async()=>{
  const provider=require(process.argv[2]);
  const rows=await provider.getStreams({tmdbId:"157336",mediaType:"movie",title:"Interstellar",year:2014});
  process.stdout.write(JSON.stringify(rows));
})().catch(e=>{console.error(e&&e.stack||e);process.exit(1)});
''',
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["node", str(runner_path), str(module_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        rows = json.loads(proc.stdout or "[]")
        assert isinstance(rows, list), rows
        return rows

transition_rows = run_transition(transition_js)
assert any(str(row.get("url") or "") == "https://cdn.example/interstellar/master.m3u8" for row in transition_rows), transition_rows

print("Brain third-order runtime strategy execution passed")
