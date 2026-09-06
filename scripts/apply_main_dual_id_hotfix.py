#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_media_resolver() -> None:
    rel = "scripts/provider_patches/global_media_type_resolution_v1.py"
    text = read(rel)
    text = one(
        text,
        'metadata capability backed by request context/cache, a credential explicitly\n'
        'supplied by the host runtime/CI, or the trusted native fetch bridge. Provider\n'
        'bundles never embed, receive, recover or decrypt a TMDB credential.\n',
        'metadata capability backed by request context/cache or a credential explicitly\n'
        'supplied by the host runtime/CI. The native fetch bridge is transport only and is\n'
        'never treated as TMDB authentication. Provider bundles never embed, receive,\n'
        'recover or decrypt a TMDB credential.\n',
        "resolver credential contract",
    )
    text = one(
        text,
        '"revision": "tmdb-data-contract-launch-gate-v27-anime-semantic-transport",',
        '"revision": "tmdb-data-contract-launch-gate-v28-dual-id-input",',
        "resolver revision",
    )
    helper = r'''function sourceIdentity(v){
  var raw=s(v),x=raw,kind="unknown";
  x=x.replace(/^https?:\/\/(?:www\.)?imdb\.com\/title\//i,"");
  var prefix=/^(tmdb|imdb|movie|tv|series)[:/]/i.exec(x);
  if(prefix){kind=prefix[1].toLowerCase()==="imdb"?"imdb":"tmdb";x=x.slice(prefix[0].length)}
  x=x.split(/[\/?#]/)[0];
  var episodic=/^(tt\d+|\d+):\d+:\d+$/i.exec(x);if(episodic)x=episodic[1];
  if(/^tt\d+$/i.test(x)){kind="imdb";x=x.toLowerCase()}
  else if(/^\d+$/.test(x))kind="tmdb";
  return{raw:raw,id:x,kind:kind};
}
function metadataImdb(m){
  if(!m||typeof m!=="object")return"";
  var x=s(m.imdb_id||m.imdbId||(m.external_ids&&m.external_ids.imdb_id)||"").toLowerCase();
  return /^tt\d+$/.test(x)?x:"";
}
'''
    anchor = 'function namespaceOf(v){var x=alias(v);return x==="movie"?"movie":"tv"}\n'
    if "function sourceIdentity(v)" not in text:
        text = one(text, anchor, anchor + helper, "source identity helper")

    text = one(
        text,
        'function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_){return false}}\n',
        '',
        "native fetch auth inference",
    )
    text = one(
        text,
        'async function apiJson(url){\n'
        '  var key=coreCredentialKey,token=coreCredentialToken,nativeBridge=nativeFetchBridge();\n'
        '  if(!g||typeof g.fetch!=="function"||(!key&&!token&&!nativeBridge))return{state:"unavailable",value:null};\n',
        'async function apiJson(url){\n'
        '  var key=coreCredentialKey,token=coreCredentialToken;\n'
        '  if(!g||typeof g.fetch!=="function"||(!key&&!token))return{state:"unavailable",value:null};\n',
        "authenticated TMDB gate",
    )

    start = text.index('async function coreGetTmdbData(request){')
    end = text.index('\ntry{if(g)g.__nuvioCoreGetTmdbDataV1=coreGetTmdbData}catch(_){}', start)
    new_core = r'''async function coreGetTmdbData(request){
  var q=request&&typeof request==="object"&&!Array.isArray(request)?request:{};
  var source=sourceIdentity(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id),id="",imdbId="";
  var explicit=s(q.tmdbNamespace||q.namespace).toLowerCase();
  var candidates=explicit==="movie"||explicit==="tv"?[explicit]:namespaceCandidates(q.mediaType||q.type,q.season,q.episode);
  if(source.kind==="imdb"){
    imdbId=source.id;
    var found=await findTmdb(imdbId,candidates);
    if(!found||found.state!=="ok"||!/^\d+$/.test(s(found.tmdbId)))return{state:found&&found.state||"unavailable",tmdbId:"",imdbId:imdbId,tmdbNamespace:"",metadata:null,episodeMetadata:null};
    id=s(found.tmdbId);candidates=[found.namespace];
  }else if(source.kind==="tmdb")id=source.id;
  else return{state:"not_found",tmdbId:"",imdbId:"",tmdbNamespace:"",metadata:null,episodeMetadata:null};
  var unavailable=false;
  for(var i=0;i<candidates.length;i++){
    var namespace=candidates[i]==="movie"?"movie":"tv";
    var probe=await tmdb(namespace,id);
    if(!probe||probe.state==="unavailable"){unavailable=true;continue}
    if(probe.state!=="ok"||!probe.metadata)continue;
    imdbId=imdbId||metadataImdb(probe.metadata);
    var episodeMetadata=null;
    var season=Number(q.season||0)||0,episode=Number(q.episode||0)||0;
    if(namespace==="tv"&&season>0&&episode>0){
      var episodeKey="episode:tv:"+id+":"+season+":"+episode+":fr-FR";
      if(Object.prototype.hasOwnProperty.call(mediaCache,episodeKey)){
        var cachedEpisode=await mediaCache[episodeKey];
        episodeMetadata=cachedEpisode&&cachedEpisode.metadata?cachedEpisode.metadata:cachedEpisode&&cachedEpisode.value?cachedEpisode.value:cachedEpisode||null;
      }else{
        var pendingEpisode=(async function(){
          var row=await apiJson("https://api.themoviedb.org/3/tv/"+encodeURIComponent(id)+"/season/"+encodeURIComponent(season)+"/episode/"+encodeURIComponent(episode)+"?language=fr-FR");
          if(!row||row.state!=="ok")return{state:row&&row.state||"unavailable",metadata:null};
          return{state:"ok",metadata:row.value};
        })();
        mediaCache[episodeKey]=pendingEpisode;
        var episodeResult=await pendingEpisode;
        if(episodeResult&&episodeResult.state==="unavailable")delete mediaCache[episodeKey];else mediaCache[episodeKey]=episodeResult;
        episodeMetadata=episodeResult&&episodeResult.metadata||null;
      }
    }
    return{state:"ok",tmdbId:id,imdbId:imdbId,tmdbNamespace:namespace,metadata:probe.metadata,episodeMetadata:episodeMetadata};
  }
  return{state:unavailable?"unavailable":"not_found",tmdbId:id,imdbId:imdbId,tmdbNamespace:"",metadata:null,episodeMetadata:null};
}'''
    text = text[:start] + new_core + text[end:]

    text = one(
        text,
        '  var rawId=s(id),tmdbId=rawId.replace(/^tmdb:/i,""),imdbId="",seedMetadata=null;\n'
        '  var imdbMatch=/^(?:imdb:)?(tt\\d+)$/i.exec(rawId);\n'
        '  if(imdbMatch){\n'
        '    imdbId=imdbMatch[1].toLowerCase();\n',
        '  var source=sourceIdentity(id),rawId=source.id,tmdbId=source.kind==="tmdb"?source.id:"",imdbId=source.kind==="imdb"?source.id:"",seedMetadata=null;\n'
        '  if(imdbId){\n',
        "canonical source parser",
    )
    text = one(
        text,
        '    var type=animeMeta(metadata)?"anime":namespace;\n'
        '    return{type:type,namespace:namespace,tmdbId:/^\\d+$/.test(tmdbId)?tmdbId:"",imdbId:imdbId,metadata:metadata,authoritative:true,degraded:false};',
        '    imdbId=imdbId||metadataImdb(metadata);\n'
        '    var type=animeMeta(metadata)?"anime":namespace;\n'
        '    return{type:type,namespace:namespace,tmdbId:/^\\d+$/.test(tmdbId)?tmdbId:"",imdbId:imdbId,metadata:metadata,authoritative:true,degraded:false};',
        "metadata IMDb enrichment",
    )
    text = one(
        text,
        '    var m=probe.metadata,type=animeMeta(m)?"anime":namespace;\n'
        '    return{type:type,namespace:namespace,tmdbId:tmdbId,imdbId:imdbId,metadata:m,authoritative:true,degraded:false};',
        '    var m=probe.metadata;imdbId=imdbId||metadataImdb(m);var type=animeMeta(m)?"anime":namespace;\n'
        '    return{type:type,namespace:namespace,tmdbId:tmdbId,imdbId:imdbId,metadata:m,authoritative:true,degraded:false};',
        "resolved IMDb enrichment",
    )

    text = one(
        text,
        '  var id=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first);\n'
        '  var providerType=providerTransport(type,namespace);\n'
        '  var resolvedTmdbId=/^\\d+$/.test(id)?id:"";\n'
        '  var resolvedImdbId=s(obj&&(q.imdbId||q.imdb_id)||(/^tt\\d+$/i.test(id)?id:"")).toLowerCase();\n',
        '  var id=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first),source=sourceIdentity(id);\n'
        '  var providerType=providerTransport(type,namespace);\n'
        '  var resolvedTmdbId=source.kind==="tmdb"?source.id:"";\n'
        '  var resolvedImdbId=s(obj&&(q.imdbId||q.imdb_id)||(source.kind==="imdb"?source.id:"")).toLowerCase();\n',
        "provisional IDs",
    )

    ctx_old = '  var context={\n    tmdbId:resolvedTmdbId,\n    imdbId:resolvedImdbId,\n'
    ctx_new = '  var context={\n    sourceId:source.id,\n    sourceIdType:source.kind,\n    tmdbId:resolvedTmdbId,\n    imdbId:resolvedImdbId,\n'
    if text.count(ctx_old) != 2:
        raise SystemExit(f"context anchors: expected 2 got {text.count(ctx_old)}")
    text = text.replace(ctx_old, ctx_new, 2)

    id_old = '    tmdbIdentity:namespace+":"+(resolvedTmdbId||id),\n'
    id_new = '    tmdbIdentity:namespace+":"+(resolvedTmdbId||resolvedImdbId||source.id),\n'
    if text.count(id_old) != 2:
        raise SystemExit(f"identity anchors: expected 2 got {text.count(id_old)}")
    text = text.replace(id_old, id_new, 2)

    q_old = '    q.nuvioInputMediaType=input;\n'
    q_new = '    q.sourceId=source.id;q.sourceIdType=source.kind;\n    q.nuvioInputMediaType=input;\n'
    if text.count(q_old) != 2:
        raise SystemExit(f"request context anchors: expected 2 got {text.count(q_old)}")
    text = text.replace(q_old, q_new, 2)

    qid_old = '    q.tmdbIdentity=namespace+":"+(resolvedTmdbId||id);\n'
    qid_new = '    q.tmdbIdentity=namespace+":"+(resolvedTmdbId||resolvedImdbId||source.id);\n'
    if text.count(qid_old) != 2:
        raise SystemExit(f"request identity anchors: expected 2 got {text.count(qid_old)}")
    text = text.replace(qid_old, qid_new, 2)

    text = one(
        text,
        '  var out=Array.prototype.slice.call(a);out[1]=providerType;out.__nuvioContext=context;return out;\n',
        '  var out=Array.prototype.slice.call(a);out[0]=resolvedTmdbId||resolvedImdbId||source.id||out[0];out[1]=providerType;out.__nuvioContext=context;return out;\n',
        "provisional positional ID",
    )

    text = one(
        text,
        '  var metadata=obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q);\n'
        '  var id=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first);\n'
        '  var season=obj?q.season:a[2],episode=obj?q.episode:a[3];\n'
        '  var resolved=await canonicalResolution(id,input,metadata,season,episode,semantic);\n',
        '  var metadata=obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q);\n'
        '  var id=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first),source=sourceIdentity(id);\n'
        '  var season=obj?q.season:a[2],episode=obj?q.episode:a[3];\n'
        '  var resolved=await canonicalResolution(id,input,metadata,season,episode,semantic);\n',
        "resolved source parser",
    )
    text = one(
        text,
        '  var resolvedTmdbId=s(resolved.tmdbId||(/^\\d+$/.test(id)?id:""));\n'
        '  var resolvedImdbId=s(resolved.imdbId||obj&&(q.imdbId||q.imdb_id)||(/^tt\\d+$/i.test(id)?id:"")).toLowerCase();\n',
        '  var resolvedTmdbId=s(resolved.tmdbId||(source.kind==="tmdb"?source.id:""));\n'
        '  var resolvedImdbId=s(resolved.imdbId||obj&&(q.imdbId||q.imdb_id)||(source.kind==="imdb"?source.id:"")).toLowerCase();\n',
        "resolved IDs",
    )
    text = one(
        text,
        '  var out=Array.prototype.slice.call(a);if(resolvedTmdbId)out[0]=resolvedTmdbId;out[1]=providerType;out.__nuvioContext=context;return out;\n',
        '  var out=Array.prototype.slice.call(a);out[0]=resolvedTmdbId||resolvedImdbId||source.id||out[0];out[1]=providerType;out.__nuvioContext=context;return out;\n',
        "resolved positional ID",
    )

    marker = 'function providerNeedsTmdbBeforeStreams(container){\n'
    request_helper = r'''function requestHasExternalIdentity(a){
  try{
    var first=a&&a[0],raw=objectRequest(first)?s(first.tmdbId||first.tmdb_id||first.imdbId||first.imdb_id||first.id):s(first);
    return sourceIdentity(raw).kind==="imdb";
  }catch(_){return false}
}
'''
    if "function requestHasExternalIdentity(a)" not in text:
        text = one(text, marker, request_helper + marker, "external identity helper")

    text = one(
        text,
        '      var verified=null;\n'
        '      var tmdbBeforeStreams=providerNeedsTmdbBeforeStreams(o);\n'
        '      if(tmdbBeforeStreams){\n'
        '        verified=await resolve(originalArgs);\n'
        '        if(!verified||deadlineExpired(requestDeadline))return [];\n'
        '        if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];\n'
        '        if(!hasResolvedTmdbMetadata(verified))return [];\n'
        '        if(verified.__nuvioContext)verified.__nuvioContext.requestToken=requestToken;\n'
        '        if(g)g.__nuvioMediaContext=verified.__nuvioContext||null;\n'
        '        a=verified;\n'
        '      }\n',
        '      var verified=null,preResolved=null;\n'
        '      var needsPlanMetadata=providerNeedsTmdbBeforeStreams(o);\n'
        '      var needsIdNormalization=requestHasExternalIdentity(originalArgs);\n'
        '      if(needsPlanMetadata||needsIdNormalization){\n'
        '        preResolved=await resolve(originalArgs);\n'
        '        if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];\n'
        '        if(preResolved&&!deadlineExpired(requestDeadline)&&hasResolvedTmdbMetadata(preResolved)){\n'
        '          verified=preResolved;\n'
        '          if(verified.__nuvioContext)verified.__nuvioContext.requestToken=requestToken;\n'
        '          if(g)g.__nuvioMediaContext=verified.__nuvioContext||null;\n'
        '          a=verified;\n'
        '        }\n'
        '      }\n',
        "pre-provider metadata gate",
    )
    text = one(
        text,
        '      if(!verified){\n        verified=await resolve(originalArgs);\n',
        '      if(!verified){\n        verified=preResolved||await resolve(originalArgs);\n',
        "post-output resolution reuse",
    )
    write(rel, text)


def patch_manifest_harness() -> None:
    rel = "scripts/augment_native_provider_loading.py"
    text = read(rel)
    text = one(text, 'CANONICAL_TYPES = {"movie", "tv", "anime"}\n', 'CANONICAL_TYPES = {"movie", "tv", "anime"}\nTRANSPORT_TYPES = CANONICAL_TYPES | {"series"}\n', "transport type set")
    old = '''        types = [str(value or "").strip().lower() for value in raw.get("supportedTypes", [])]\n        if not types or any(value not in CANONICAL_TYPES for value in types):\n            raise SystemExit(f"{path}: provider {provider_id} has invalid supportedTypes={types}")\n        rows.append(raw)\n'''
    new = '''        supported = [str(value or "").strip().lower() for value in raw.get("supportedTypes", [])]\n        canonical_raw = raw.get("canonicalSupportedTypes")\n        canonical = (\n            [str(value or "").strip().lower() for value in canonical_raw]\n            if isinstance(canonical_raw, list) and canonical_raw\n            else [value for value in supported if value in CANONICAL_TYPES]\n        )\n        if not supported or any(value not in TRANSPORT_TYPES for value in supported):\n            raise SystemExit(f"{path}: provider {provider_id} has invalid supportedTypes={supported}")\n        if not canonical or any(value not in CANONICAL_TYPES for value in canonical):\n            raise SystemExit(f"{path}: provider {provider_id} has invalid canonicalSupportedTypes={canonical}")\n        if "series" in canonical:\n            raise SystemExit(f"{path}: provider {provider_id} leaked series into canonicalSupportedTypes")\n        rows.append(raw)\n'''
    text = one(text, old, new, "native manifest type validation")
    write(rel, text)


def patch_app_selection_diagnostics() -> None:
    rel = "scripts/augment_native_provider_loading_compat.py"
    text = read(rel)
    if "def inject_app_path_diagnostics" not in text:
        anchor = "\ndef normalize_async_provider_skips(path: Path, client: str) -> None:\n"
        fn = r'''
def inject_app_path_diagnostics(path: Path, client: str) -> None:
    if client == "tv":
        print("FIELD_NATIVE_PROVIDER_APP_PATH client=tv injected=false reason=plugin_manager_path")
        return
    if client not in {"desktop", "mobile"}:
        raise SystemExit(f"unsupported app-path diagnostics client: {client}")
    text = path.read_text(encoding="utf-8")
    marker = f"FIELD_NATIVE_REPOSITORY_APP_PATH client={client}"
    if marker in text:
        print(f"FIELD_NATIVE_PROVIDER_APP_PATH client={client} injected=false already=true")
        return
    anchor = "        return byId\n    }\n"
    if text.count(anchor) != 1:
        raise SystemExit(f"provider-loading app-path return anchor client={client} count={text.count(anchor)}")
    diagnostic = f'''        val appMovieScrapers = PluginRepository.getEnabledScrapersForType("movie")
            .filter {{ it.repositoryUrl == repositoryUrl }}
        val appTvScrapers = PluginRepository.getEnabledScrapersForType("tv")
            .filter {{ it.repositoryUrl == repositoryUrl }}
        val appSeriesScrapers = PluginRepository.getEnabledScrapersForType("series")
            .filter {{ it.repositoryUrl == repositoryUrl }}
        val pluginStateForAppPath = PluginRepository.uiState.value
        emit("FIELD_NATIVE_REPOSITORY_APP_PATH client={client} fixture=$fixtureSlugForLoad plugins_enabled=${{pluginStateForAppPath.pluginsEnabled}} group_by_repository=${{pluginStateForAppPath.groupStreamsByRepository}} loaded=${{byId.size}} movie_enabled=${{appMovieScrapers.size}} tv_enabled=${{appTvScrapers.size}} series_enabled=${{appSeriesScrapers.size}}")
        return byId
    }}
'''
    path.write_text(text.replace(anchor, diagnostic, 1), encoding="utf-8")
    print(f"FIELD_NATIVE_PROVIDER_APP_PATH client={client} injected=true already=false")
'''
        text = one(text, anchor, "\n" + fn + anchor, "app path diagnostics insertion")
    if "inject_app_path_diagnostics(source, client)" not in text:
        text = one(text, "    run_canonical()\n    normalize_async_provider_skips(source, client)\n", "    run_canonical()\n    inject_app_path_diagnostics(source, client)\n    normalize_async_provider_skips(source, client)\n", "app diagnostics call")
    write(rel, text)

    gate = ROOT / "scripts/gate_native_app_provider_selection.py"
    gate.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse,re
from pathlib import Path
MARKER="FIELD_NATIVE_REPOSITORY_APP_PATH"
FIELD_RE=re.compile(r"([a-z_]+)=([^\s]+)")
def parse(line):
    if MARKER not in line:return None
    return {k:v for k,v in FIELD_RE.findall(line)}
def b(v,n):
    x=v.strip().casefold()
    if x=="true":return True
    if x=="false":return False
    raise ValueError(f"invalid {n}={v!r}")
def n(v,name):
    x=int(v)
    if x<0:raise ValueError(f"invalid {name}={v!r}")
    return x
def validate(path,client):
    rows=[x for line in path.read_text(encoding="utf-8",errors="replace").splitlines() if (x:=parse(line)) and x.get("client")==client]
    if not rows:raise ValueError(f"{path}: missing {MARKER} client={client}")
    r=rows[-1];enabled=b(r.get("plugins_enabled",""),"plugins_enabled");loaded=n(r.get("loaded",""),"loaded");movie=n(r.get("movie_enabled",""),"movie_enabled");tv=n(r.get("tv_enabled",""),"tv_enabled");series=n(r.get("series_enabled",""),"series_enabled")
    if not enabled:raise ValueError(f"{path}: production plugin selection globally disabled")
    if loaded<=0 or movie<=0 or tv<=0 or series<=0:raise ValueError(f"{path}: zero app selection loaded={loaded} movie={movie} tv={tv} series={series}")
    if max(movie,tv,series)>loaded:raise ValueError(f"{path}: impossible app selection loaded={loaded} movie={movie} tv={tv} series={series}")
    return loaded,movie,tv,series
def main():
    p=argparse.ArgumentParser();p.add_argument("--client",choices=("desktop","mobile"),required=True);p.add_argument("logs",nargs="+");a=p.parse_args();mins=None
    for raw in a.logs:
        vals=validate(Path(raw),a.client);mins=vals if mins is None else tuple(min(x,y) for x,y in zip(mins,vals))
    print(f"native app provider selection gate passed: client={a.client} logs={len(a.logs)} min_loaded={mins[0]} min_movie_enabled={mins[1]} min_tv_enabled={mins[2]} min_series_enabled={mins[3]}")
    return 0
if __name__=="__main__":raise SystemExit(main())
''', encoding="utf-8")

    test = ROOT / "tests/native_app_provider_selection_gate_test.py"
    test.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("gate",ROOT/"scripts/gate_native_app_provider_selection.py");mod=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"ok.log";p.write_text("FIELD_NATIVE_REPOSITORY_APP_PATH client=mobile fixture=x plugins_enabled=true group_by_repository=true loaded=12 movie_enabled=8 tv_enabled=9 series_enabled=9\n",encoding="utf-8")
    assert mod.validate(p,"mobile")== (12,8,9,9)
    p.write_text("FIELD_NATIVE_REPOSITORY_APP_PATH client=desktop fixture=x plugins_enabled=true group_by_repository=true loaded=12 movie_enabled=8 tv_enabled=9 series_enabled=0\n",encoding="utf-8")
    try:mod.validate(p,"desktop")
    except ValueError as e:assert "series=0" in str(e)
    else:raise AssertionError("series=0 must fail")
print("native app provider selection series gate tests passed")
''', encoding="utf-8")


def patch_suite_scripts() -> None:
    for rel, client in (("scripts/run_native_corpus_mobile_suite.sh", "mobile"),("scripts/run_native_corpus_desktop_suite.sh","desktop")):
        text=read(rel)
        if 'APP_SELECTION_GATE="${NIAKVIO}/scripts/gate_native_app_provider_selection.py"' not in text:
            text=one(text,'SMOKE_GATE="${NIAKVIO}/scripts/gate_native_player_reached.cjs"\n','SMOKE_GATE="${NIAKVIO}/scripts/gate_native_player_reached.cjs"\nAPP_SELECTION_GATE="${NIAKVIO}/scripts/gate_native_app_provider_selection.py"\n',f"{client} app gate variable")
        if f'python3 "$APP_SELECTION_GATE" --client {client}' not in text:
            text=one(text,'SMOKE_STATUS=0\nnode "$SMOKE_GATE" "${LOGS[@]}" || SMOKE_STATUS=$?\nFINAL_STATUS=$SMOKE_STATUS\nif [[ "$MATRIX_STATUS" -ne 0 ]]; then FINAL_STATUS=2; fi\n',f'APP_SELECTION_STATUS=0\npython3 "$APP_SELECTION_GATE" --client {client} "${{LOGS[@]}}" || APP_SELECTION_STATUS=$?\nSMOKE_STATUS=0\nnode "$SMOKE_GATE" "${{LOGS[@]}}" || SMOKE_STATUS=$?\nFINAL_STATUS=$SMOKE_STATUS\nif [[ "$MATRIX_STATUS" -ne 0 || "$APP_SELECTION_STATUS" -ne 0 ]]; then FINAL_STATUS=2; fi\n',f"{client} app gate execution")
        write(rel,text)


def patch_domain_refresh() -> None:
    rel="scripts/refresh_authoritative_hub_domains.py";text=read(rel)
    if "def _reconcile_domain_derivatives" not in text:
        anchor='\ndef _update_history_on_change(history_row: dict[str, Any], item: dict[str, Any]) -> None:\n'
        helper=r'''
def _domain_host(value: str) -> str:
    raw=str(value or "").strip()
    if not raw:return ""
    return hubresolver.host(raw if "://" in raw else "https://"+raw)


def _reconcile_domain_derivatives(patch: dict[str, Any], before_site: str, next_site: str) -> list[dict[str, str]]:
    changes=[];before_host=_domain_host(before_site);next_host=_domain_host(next_site)
    if not next_host:return changes
    maps=[]
    for name in ("domain_substitutions","replacements","runtime_domain_replacements"):
        row=patch.get(name)
        if isinstance(row,dict):maps.append((name,row))
    edges={}
    for _name,row in maps:
        for source,target in row.items():
            sh,th=_domain_host(source),_domain_host(target)
            if sh and th:edges[sh]=th
    if before_host and before_host!=next_host:edges[before_host]=next_host
    def canonical(hostname):
        seen=set();current=hostname
        while current and current not in seen and current in edges:seen.add(current);current=edges[current]
        return current
    for name,row in maps:
        for source,target in list(row.items()):
            th=_domain_host(target)
            if th and canonical(th)==next_host and th!=next_host:
                row[source]=next_host;changes.append({"from":str(target),"to":next_host,"kind":name})
        if before_host and before_host!=next_host and row.get(before_host)!=next_host:
            row[before_host]=next_host;changes.append({"from":before_host,"to":next_host,"kind":name})
    manifest=patch.get("manifest_overrides")
    if isinstance(manifest,dict):
        for field in ("logo","icon","favicon"):
            value=manifest.get(field);vh=_domain_host(value)
            if value and vh and canonical(vh)==next_host and vh!=next_host:
                manifest[field]=str(value).replace(vh,next_host);changes.append({"from":str(value),"to":str(manifest[field]),"kind":f"manifest_overrides.{field}"})
    notes=patch.get("notes")
    if isinstance(notes,list) and before_host and before_host!=next_host:
        patch["notes"]=[str(v).replace(before_host,next_host) for v in notes]
    elif isinstance(notes,str) and before_host and before_host!=next_host:
        patch["notes"]=notes.replace(before_host,next_host)
    return changes
'''
        text=one(text,anchor,"\n"+helper+anchor,"domain derivative helper")
        text=one(text,'                        _update_history_on_change(history_row, item)\n                    item["applied_changes"] = changes\n','                        _update_history_on_change(history_row, item)\n                    if next_site:\n                        changes.extend(_reconcile_domain_derivatives(patch, before_site, next_site))\n                    item["applied_changes"] = changes\n',"domain derivative application")
    write(rel,text)

    cfg_path=ROOT/"provider-overrides.json";cfg=json.loads(cfg_path.read_text(encoding="utf-8"));f=cfg["provider_patches"]["flemmix"]
    f["official_site"]="https://flemmix.kim"
    mo=f.setdefault("manifest_overrides",{});logo=str(mo.get("logo") or "");mo["logo"]=logo.replace("flemmix.men","flemmix.kim") if logo else "https://flemmix.kim/favicon.ico"
    for name in ("domain_substitutions","replacements","runtime_domain_replacements"):
        row=f.setdefault(name,{})
        for k,v in list(row.items()):
            row[k]=str(v).replace("flemmix.men","flemmix.kim")
        row["flemmix.men"]="flemmix.kim"
    notes=f.get("notes")
    if isinstance(notes,list):f["notes"]=[str(v).replace("flemmix.men","flemmix.kim") for v in notes]
    elif isinstance(notes,str):f["notes"]=notes.replace("flemmix.men","flemmix.kim")
    cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def add_regression_test() -> None:
    p=ROOT/"tests/native_dual_id_identity_test.py"
    p.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,subprocess,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("resolver",ROOT/"scripts/provider_patches/global_media_type_resolution_v1.py");mod=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(mod)
BASE=r'''\n"use strict";\nasync function getStreams(id,type,season,episode){const c=globalThis.__nuvioMediaContext||{};return [{url:"https://media.example/ok.m3u8",receivedId:String(id),receivedType:String(type),season,episode,tmdbId:c.tmdbId||"",imdbId:c.imdbId||"",sourceId:c.sourceId||"",sourceIdType:c.sourceIdType||"",degraded:c.tmdbResolutionDegraded===true}]}\nmodule.exports={getStreams,__niakvioProviderBase:{identityInput:{mode:"catalog_search",requiresTmdbBeforeRun:true}}};\n'''
SOURCE=mod.apply(BASE,options={"semantic_types":["movie","tv"]})
def run(js):
  with tempfile.TemporaryDirectory() as td:
    d=Path(td);(d/"p.cjs").write_text(SOURCE,encoding="utf-8");(d/"t.cjs").write_text(js,encoding="utf-8");r=subprocess.run(["node",str(d/"t.cjs"),str(d/"p.cjs")],text=True,capture_output=True);assert r.returncode==0,r.stdout+r.stderr
run(r'''\nlet calls=0;global.__native_fetch=()=>{};global.fetch=async u=>{calls++;throw new Error("unexpected "+u)};const p=require(process.argv[2]);(async()=>{let v=await p.getStreams("tt11198330:3:1","series",3,1),x=v[0];if(!x||x.receivedId!=="tt11198330"||x.receivedType!=="tv"||x.imdbId!=="tt11198330"||x.sourceIdType!=="imdb")throw new Error(JSON.stringify(v));let y=(await p.getStreams("tmdb:94997:3:1","series",3,1))[0];if(!y||y.receivedId!=="94997"||y.tmdbId!=="94997"||y.sourceIdType!=="tmdb")throw new Error(JSON.stringify(y));if(calls!==0)throw new Error("credentialless native runtime touched TMDB "+calls)})().catch(e=>{console.error(e);process.exit(1)});\n''')
run(r'''\nglobal.TMDB_API_KEY="0123456789abcdef0123456789abcdef";let calls=0;global.fetch=async u=>{u=String(u);calls++;if(u.includes("/find/tt11198330"))return{ok:true,status:200,json:async()=>({movie_results:[],tv_results:[{id:94997,name:"House of the Dragon"}]})};if(u.includes("/tv/94997/season/3/episode/1"))return{ok:true,status:200,json:async()=>({id:1})};if(u.includes("/tv/94997?"))return{ok:true,status:200,json:async()=>({id:94997,name:"House of the Dragon",genres:[{id:18}],original_language:"en",external_ids:{imdb_id:"tt11198330"}})};throw new Error(u)};const p=require(process.argv[2]);(async()=>{const x=(await p.getStreams("tt11198330:3:1","series",3,1))[0];if(!x||x.receivedId!=="94997"||x.tmdbId!=="94997"||x.imdbId!=="tt11198330"||x.degraded!==false)throw new Error(JSON.stringify(x));const m=await global.__nuvioCoreGetTmdbDataV1({id:"tt11198330:3:1",mediaType:"series",season:3,episode:1});if(!m||m.state!=="ok"||m.tmdbId!=="94997"||m.imdbId!=="tt11198330")throw new Error(JSON.stringify(m))})().catch(e=>{console.error(e);process.exit(1)});\n''')
print("native dual IMDb/TMDB identity tests passed")
''',encoding="utf-8")


def update_docs() -> None:
    memory=ROOT/"MEMORY.md";text=memory.read_text(encoding="utf-8");marker="## 2026-09-06 — Canonical dual-ID input contract"
    if marker not in text:
        text += f'''\n\n{marker}\n- NiakVIO historically accepts provider work identity as either TMDB or IMDb. This is a permanent Core contract, not a provider exception.\n- Regression identified in 5.21.33: stronger TMDB title/category/year verification left early Core gates TMDB-only, so a valid IMDb request could be converted into an empty provider result before provider execution.\n- Input forms must accept numeric/prefixed TMDB and IMDb (`tt...`), including episodic transport suffixes such as `tt11198330:3:1`; season/episode are preserved separately.\n- TMDB metadata remains the authoritative enrichment/classification source when available, but failure/unavailability of enrichment must not make a syntactically valid IMDb/TMDB identity invalid.\n- `series` is a Nuvio transport alias for canonical `tv`; it belongs in `supportedTypes`, never in `canonicalSupportedTypes`.\n- Native Labs must test production selection for both `tv` and `series`, not only direct provider execution.\n- Domain Refresh owns terminal-domain derivatives (domain substitution/replacement maps and provider-owned manifest icon URLs) as well as `official_site`; historical alias keys are retained while their destination is reconciled to the authoritative terminal.\n'''
        memory.write_text(text,encoding="utf-8")
    contract=ROOT/"automation/PLATFORM-RUNTIME-CONTRACTS.md";text=contract.read_text(encoding="utf-8");marker="### Dual-ID provider input (TMDB / IMDb)"
    if marker not in text:
        text += f'''\n\n{marker}\n- Provider input identity MUST accept both TMDB and IMDb identifiers.\n- Accepted episodic shapes include client transport IDs such as `tt11198330:3:1`; Core separates the base ID from season/episode before provider gates.\n- TMDB enrichment/classification may normalize IMDb -> TMDB when available, but metadata failure MUST fail open for a valid source identity and MUST NOT suppress provider execution globally.\n- `series` is transport-only and normalizes to canonical `tv`; `canonicalSupportedTypes` remains limited to `movie`, `tv`, `anime`.\n- Mobile/Desktop native app-path gates MUST verify non-zero provider selection for `series` as well as `tv`; direct `executeScraper` evidence alone is insufficient.\n'''
        contract.write_text(text,encoding="utf-8")


def main() -> int:
    patch_media_resolver();patch_manifest_harness();patch_app_selection_diagnostics();patch_suite_scripts();patch_domain_refresh();add_regression_test();update_docs()
    print("MAIN_DUAL_ID_PATCH_APPLIED")
    return 0

if __name__=="__main__":raise SystemExit(main())
