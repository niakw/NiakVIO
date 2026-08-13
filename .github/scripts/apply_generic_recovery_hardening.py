#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, got {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Domain resolver: historical/previous peers are real recovery candidates,
# not merely sources used after a new route has already been selected.
replace_once(
    "scripts/resolve_provider_hubs.py",
    '''    for url in cfg.get("direct_candidates") or []:\n        values.append(host(str(url)))\n    fallback = cfg.get("direct_fallback")\n''',
    '''    for url in cfg.get("direct_candidates") or []:\n        values.append(host(str(url)))\n    for url in cfg.get("historical_terminal_candidates") or []:\n        values.append(host(str(url)))\n    fallback = cfg.get("direct_fallback")\n''',
)

replace_once(
    "scripts/resolve_provider_hubs.py",
    '''        target["allowed_terminal_hosts"] = sorted(allowed)\n        target.setdefault("sources", [])\n    return merged\n''',
    '''        target["allowed_terminal_hosts"] = sorted(allowed)\n\n        # Previous domains and replacement sources are trusted peer candidates,\n        # but they still have to pass the same runtime terminal validation as a\n        # newly discovered address. This lets the resolver recover automatically\n        # when the current/LKG domain starts returning 403/5xx while an older\n        # same-provider terminal becomes live again.\n        patches = config.get("provider_patches") or {}\n        patch = patches.get(provider_id) if isinstance(patches, dict) else None\n        if not isinstance(patch, dict) and isinstance(patches, dict):\n            patch = next((value for key, value in patches.items() if canonical_provider_id(key) == provider_id and isinstance(value, dict)), {})\n        patch = patch if isinstance(patch, dict) else {}\n        historical_hosts = {str(item).lower().strip(".") for item in target.get("old_site_hosts") or [] if item}\n        for mapping_name in ("replacements", "runtime_domain_replacements"):\n            mapping = patch.get(mapping_name)\n            if isinstance(mapping, dict):\n                historical_hosts.update(str(key).lower().strip(".") for key in mapping if key)\n        previous_site = patch.get("official_site")\n        if previous_site and host(str(previous_site)):\n            historical_hosts.add(host(str(previous_site)))\n        blocked = {str(item).lower().strip(".") for item in target.get("blocked_hosts") or [] if item}\n        historical = []\n        for peer_host in sorted(historical_hosts):\n            if not peer_host or peer_host in blocked or peer_host in SOCIAL_HOST_SUFFIXES + SEARCH_HOST_SUFFIXES + INFRASTRUCTURE_HOST_SUFFIXES:\n                continue\n            candidate = f"https://{peer_host}"\n            if candidate.rstrip("/") not in {url.rstrip("/") for url in target["direct_candidates"]}:\n                historical.append(candidate)\n        target["historical_terminal_candidates"] = historical\n        target.setdefault("sources", [])\n    return merged\n''',
)

replace_once(
    "scripts/resolve_provider_hubs.py",
    '''    for index, url in enumerate(cfg.get("direct_candidates") or []):\n        if is_http_url(url):\n            candidates.append({\n                "url": str(url).rstrip("/"), "label": "curated direct candidate",\n                "score": 72 - min(index, 10), "source_type": "curated_direct", "source": "provider-hubs.json",\n            })\n    current = history_row.get("current") if isinstance(history_row, dict) else None\n''',
    '''    for index, url in enumerate(cfg.get("direct_candidates") or []):\n        if is_http_url(url):\n            candidates.append({\n                "url": str(url).rstrip("/"), "label": "curated direct candidate",\n                "score": 72 - min(index, 10), "source_type": "curated_direct", "source": "provider-hubs.json",\n            })\n    for index, url in enumerate(cfg.get("historical_terminal_candidates") or []):\n        if is_http_url(url):\n            candidates.append({\n                "url": str(url).rstrip("/"), "label": "validated historical peer candidate",\n                "score": 66 - min(index, 12), "source_type": "historical_peer", "source": "provider routing history",\n            })\n    current = history_row.get("current") if isinstance(history_row, dict) else None\n''',
)

replace_once(
    "scripts/resolve_provider_hubs.py",
    '''    old_hosts = {str(item).lower().strip(".") for item in hub_cfg.get("old_site_hosts") or [] if item}\n    previous_site = patch.get("official_site")\n''',
    '''    old_hosts = {str(item).lower().strip(".") for item in hub_cfg.get("old_site_hosts") or [] if item}\n    old_hosts.update(str(item).lower().strip(".") for item in replacements if item)\n    old_hosts.update(str(item).lower().strip(".") for item in runtime if item)\n    for candidate in hub_cfg.get("historical_terminal_candidates") or []:\n        if host(str(candidate)):\n            old_hosts.add(host(str(candidate)))\n    previous_site = patch.get("official_site")\n''',
)

# 2) Runtime domain failover: 403/rate limit/transient upstream failures are
# legitimate reasons to try an explicitly configured peer origin.
replace_once(
    "scripts/provider_patches/adaptive_domain_recovery.py",
    '''  function obsolete(status){return status===404||status===410||status===451||status===521||status===522||status===523;}\n''',
    '''  function obsolete(status){return status===403||status===404||status===408||status===410||status===425||status===429||status===451||status===500||status===502||status===503||status===504||(status>=520&&status<=524);}\n''',
)

# 3) Feed observed/source endpoint origins into adaptive V4. The JS layer only
# replays a route across origins that belong to the same endpoint family.
replace_once(
    "scripts/adaptive_runtime/runtime_repair.py",
    '''    return {\n        "provider_name": str(metadata.get("name") or provider_id or "Provider"),\n        "base_url": base_url,\n        "types": types,\n''',
    '''    endpoint_origins: list[str] = []\n    for raw in observed:\n        peer = _origin(raw)\n        if not peer:\n            continue\n        peer_host = (urlparse(peer).hostname or "").casefold()\n        if peer_host in INFRASTRUCTURE_HOSTS or any(peer_host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):\n            continue\n        if peer not in endpoint_origins:\n            endpoint_origins.append(peer)\n\n    return {\n        "provider_name": str(metadata.get("name") or provider_id or "Provider"),\n        "base_url": base_url,\n        "endpoint_origins": endpoint_origins[:32],\n        "types": types,\n''',
)

replace_once(
    "scripts/adaptive_runtime/runtime_repair.py",
    '''def _apply_adaptive(parent_data: bytes, candidate: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:\n    options = _adaptive_runtime_options(candidate, load_overrides())\n    if options is None:\n        return parent_data, []\n    script = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py"\n''',
    '''def _source_endpoint_origins(source_text: str) -> list[str]:\n    output: list[str] = []\n    for raw in re.findall(r"https?://[A-Za-z0-9.-]+(?::\\d+)?", source_text):\n        peer = _origin(raw)\n        if not peer:\n            continue\n        peer_host = (urlparse(peer).hostname or "").casefold()\n        if peer_host in INFRASTRUCTURE_HOSTS or any(peer_host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):\n            continue\n        if peer not in output:\n            output.append(peer)\n        if len(output) >= 32:\n            break\n    return output\n\n\ndef _apply_adaptive(parent_data: bytes, candidate: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:\n    options = _adaptive_runtime_options(candidate, load_overrides())\n    if options is None:\n        return parent_data, []\n    source_text = parent_data.decode("utf-8", errors="strict")\n    options = dict(options)\n    peers = list(options.get("endpoint_origins") or [])\n    for peer in _source_endpoint_origins(source_text):\n        if peer not in peers:\n            peers.append(peer)\n    options["endpoint_origins"] = peers[:32]\n    script = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py"\n''',
)

replace_once(
    "scripts/adaptive_runtime/runtime_repair.py",
    '''    patched = module.apply(parent_data.decode("utf-8", errors="strict"), options=options).encode("utf-8")\n''',
    '''    patched = module.apply(source_text, options=options).encode("utf-8")\n''',
)

# 4) Adaptive V4: sibling endpoint failover, native fetch/player capture and
# fail-closed native fallback for blocked fake media.
replace_once(
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    '''        "runtimeRevision": "bounded-binary-v1",\n        "types": [\n''',
    '''        "runtimeRevision": "generic-core-v2",\n        "endpointOrigins": [str(value).rstrip("/") for value in cfg.get("endpoint_origins", []) if str(value).startswith(("http://", "https://"))][:32],\n        "types": [\n''',
)

replace_once(
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    '''function origin(v){try{return new URL(v).origin}catch(_){return""}}\nfunction bad(u){''',
    '''function origin(v){try{return new URL(v).origin}catch(_){return""}}\nfunction inputUrl(v){try{return typeof v==="string"?v:s(v&&v.url||v)}catch(_){return""}}\nfunction suffix2(h){var p=s(h).toLowerCase().split(".").filter(Boolean);return p.length>=2?p.slice(-2).join("."):p.join(".")}\nfunction alphaStem(h){var p=s(h).toLowerCase().split(".").filter(Boolean);if(p.length>2)p=p.slice(0,-2);return p.join("").replace(/[^a-z]/g,"")}\nfunction commonPrefix(a,b){var n=Math.min(a.length,b.length),i=0;while(i<n&&a[i]===b[i])i++;return i}\nfunction endpointFamily(a,b){try{var ah=new URL(a).hostname.toLowerCase(),bh=new URL(b).hostname.toLowerCase(),as=suffix2(ah),bs=suffix2(bh);if(!as||as!==bs)return false;if(!/^(?:workers\\.dev|pages\\.dev|vercel\\.app|onrender\\.com|railway\\.app|hf\\.space)$/.test(as))return true;var ap=alphaStem(ah),bp=alphaStem(bh);return commonPrefix(ap,bp)>=6||(ap.length>=6&&bp.indexOf(ap)>=0)||(bp.length>=6&&ap.indexOf(bp)>=0)}catch(_){return false}}\nfunction peerUrls(u){var out=[],seen={};try{var src=new URL(u);for(var i=0;i<c.endpointOrigins.length;i++){var o=s(c.endpointOrigins[i]);if(!o||o===src.origin||!endpointFamily(src.origin,o))continue;try{var target=new URL(o);target.pathname=src.pathname;target.search=src.search;target.hash=src.hash;var v=target.toString();if(!seen[v]){seen[v]=1;out.push(v)}}catch(_e){}}}catch(_e){}return out}\nfunction bad(u){''',
)

replace_once(
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    '''var doc=await req(requested,false,ref);if(!doc)return[];var page=doc.url||requested;''',
    '''var doc=await req(requested,false,ref);if(!doc){var peerFallback=[],peers=peerUrls(requested);for(var pi=0;pi<peers.length&&peerFallback.length<c.maxEmbeds;pi++)peerFallback=peerFallback.concat(await resolve(peers[pi],ref,depth+1,seen));return unique(peerFallback).slice(0,c.maxEmbeds)}var page=doc.url||requested;''',
)

replace_once(
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    '''for(var i=0;i<xs.length&&i<c.maxEmbeds&&out.length<c.maxEmbeds;i++){if(media(xs[i],"",""))continue;var ps=playerScore(xs[i],page);if(ps<80)continue;var r=await resolve(xs[i],page,depth+1,seen);out=out.concat(r)}return unique(out).slice(0,c.maxEmbeds)}\n''',
    '''for(var i=0;i<xs.length&&i<c.maxEmbeds&&out.length<c.maxEmbeds;i++){if(media(xs[i],"",""))continue;var ps=playerScore(xs[i],page);if(ps<80)continue;var r=await resolve(xs[i],page,depth+1,seen);out=out.concat(r)}if(!out.length){var peers=peerUrls(requested);for(var pi=0;pi<peers.length&&out.length<c.maxEmbeds;pi++)out=out.concat(await resolve(peers[pi],ref,depth+1,seen))}return unique(out).slice(0,c.maxEmbeds)}\n''',
)

replace_once(
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    '''function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioAdaptive)return false;var old=o[k];var w=async function(){var native=[];try{native=await old.apply(this,arguments)}catch(_){}var normalized=await normalizeNative(native);if(normalized.length)return normalized;var r=await recover(args(arguments));var safeNative=Array.isArray(native)?native.filter(function(row){return row&&s(row.url)&&!U[s(row.url)]}):[];return r.length?r:safeNative};w.__nuvioAdaptive=true;o[k]=w;return true}\n''',
    '''function captureCandidate(u){if(!u||bad(u))return false;return playerScore(u,c.baseUrl+"/")>=120}\nfunction capturedRows(rows){return unique(rows).slice(0,c.maxEmbeds).map(function(row,i){return{name:c.providerName+" Captured"+(i?" #"+(i+1):""),title:c.providerName+" Captured Player",url:row.url,quality:"HD",headers:hdr(row.referer||c.baseUrl+"/",row.url),isDirect:row.direct===true||media(row.url,"","")}})}\nfunction install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioAdaptive)return false;var old=o[k];var w=async function(){var native=[],captured=[],capturedSeen={},originalFetch=g.fetch,self=this,callArgs=arguments;if(typeof originalFetch==="function")g.fetch=async function(input,init){var u=inputUrl(input);if(captureCandidate(u)&&!capturedSeen[u]){capturedSeen[u]=1;captured.push(u)}return originalFetch.apply(this,arguments)};try{native=await old.apply(self,callArgs)}catch(_){}finally{if(typeof originalFetch==="function")g.fetch=originalFetch}var normalized=await normalizeNative(native);if(normalized.length)return normalized;if(captured.length){var resolved=[];for(var ci=0;ci<captured.length&&resolved.length<c.maxEmbeds;ci++)resolved=resolved.concat(await resolve(captured[ci],c.baseUrl+"/",0,{}));if(resolved.length)return capturedRows(resolved)}var r=await recover(args(callArgs));var safeNative=Array.isArray(native)?native.filter(function(row){var u=row&&s(row.url);return !!u&&!U[u]&&!bad(u)}):[];return r.length?r:safeNative};w.__nuvioAdaptive=true;o[k]=w;return true}\n''',
)

# Permanent provider-agnostic regression test.
(ROOT / "tests" / "generic_recovery_hardening_test.py").write_text(r'''#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


# Historical peer domains must participate in generic candidate selection.
hubs = load("hubs", ROOT / "scripts" / "resolve_provider_hubs.py")
candidates, _ = hubs.gather_candidates(
    "demo",
    {
        "direct_candidates": ["https://demo.current"],
        "historical_terminal_candidates": ["https://demo.backup"],
        "sources": [],
        "manifest_status": "Actif",
    },
    {},
    "quick",
    0.1,
)
assert any(row.get("url") == "https://demo.backup" and row.get("source_type") == "historical_peer" for row in candidates)

# Runtime domain failover must retry a configured peer on HTTP 403.
domain = load("domain", ROOT / "scripts" / "provider_patches" / "adaptive_domain_recovery.py")
source = 'module.exports={getStreams:async()=>{var r=await fetch("https://old.example/api/x");return [{url:r.url,status:r.status}]}};'
patched = domain.apply(source, options={"groups": [{"hosts": ["old.example"], "candidates": ["https://new.example"]}]})
runner = r'''
const vm=require("vm");
const src=process.argv[2], calls=[];
function response(url,status){return {url,status,ok:status>=200&&status<300,headers:{get:()=>"application/json"},text:async()=>"{}",json:async()=>({})};}
const box={module:{exports:{}},exports:{},URL,fetch:async function(u){u=String(u);calls.push(u);return response(u,u.includes("old.example")?403:200)}};
box.globalThis=box; vm.runInNewContext(src,box);
box.module.exports.getStreams().then(v=>console.log(JSON.stringify({calls,v}))).catch(e=>{console.error(e);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"run.cjs"; p.write_text(runner,encoding="utf-8")
    cp=subprocess.run(["node",str(p),patched],capture_output=True,text=True,timeout=10,check=True)
    data=json.loads(cp.stdout.strip().splitlines()[-1])
assert data["calls"][:2] == ["https://new.example/api/x"] or "https://new.example/api/x" in data["calls"]
assert data["v"][0]["status"] == 200

# Adaptive V4 must: capture a player/API URL visited by native code, replay the
# same token across a sibling endpoint family, and never fall back to a blocked
# fake-media URL.
v4 = load("v4", ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py")
base = '''module.exports={getStreams:async function(q){await fetch("https://old.demo123.workers.dev/token/abc");return [{url:"https://cdn.invalid/troll/master.m3u8"}]}};'''
out = v4.apply(base, options={
    "provider_name":"Demo",
    "base_url":"https://demo.example",
    "endpoint_origins":["https://old.demo123.workers.dev","https://new.demo123.workers.dev"],
    "types":["movie"],
    "search_paths":[],
    "direct_paths":[],
    "blocked_path_patterns":["/troll/"],
    "timeout_ms":3000,
})
assert '"runtimeRevision":"generic-core-v2"' in out
runner2 = r'''
const vm=require("vm"); const src=process.argv[2], calls=[];
function headers(type){return {get:(k)=>String(k).toLowerCase()==="content-type"?type:null,getSetCookie:()=>[]};}
function res(url,status,type){return {url,status,ok:status>=200&&status<300,headers:headers(type),body:null,text:async()=>"",json:async()=>({}),arrayBuffer:async()=>new ArrayBuffer(0)};}
const box={module:{exports:{}},exports:{},URL,AbortController,fetch:async function(input){let u=typeof input==="string"?input:String(input&&input.url||input);calls.push(u);if(u.includes("old.demo123.workers.dev"))return res(u,500,"text/plain");if(u.includes("new.demo123.workers.dev"))return res(u,200,"video/mp4");if(u.includes("api.themoviedb.org"))return res(u,404,"application/json");return res(u,404,"text/plain")}};
box.globalThis=box; vm.runInNewContext(src,box);
box.module.exports.getStreams({tmdbId:"157336",mediaType:"movie",title:"Demo",year:2024}).then(v=>console.log(JSON.stringify({calls,v}))).catch(e=>{console.error(e);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"run.cjs"; p.write_text(runner2,encoding="utf-8")
    cp=subprocess.run(["node",str(p),out],capture_output=True,text=True,timeout=15,check=True)
    data=json.loads(cp.stdout.strip().splitlines()[-1])
assert any("new.demo123.workers.dev/token/abc" in u for u in data["calls"]), data
assert data["v"], data
assert data["v"][0]["url"].startswith("https://new.demo123.workers.dev/token/abc"), data
assert all("/troll/" not in row.get("url","") for row in data["v"]), data
print("generic recovery hardening test passed")
''', encoding="utf-8")

# Wire the regression into the normal suite.
pkg_path = ROOT / "package.json"
pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
test = pkg["scripts"]["test"]
needle = "python3 tests/adaptive_domain_recovery_test.py"
addition = needle + " && python3 tests/generic_recovery_hardening_test.py"
if "generic_recovery_hardening_test.py" not in test:
    if needle not in test:
        raise SystemExit("package.json adaptive domain test anchor missing")
    pkg["scripts"]["test"] = test.replace(needle, addition, 1)
pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("generic recovery hardening migration applied")
