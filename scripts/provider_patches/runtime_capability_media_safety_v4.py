#!/usr/bin/env python3
"""Standalone runtime-capability-aware media safety wrapper.

This patch owns the final global media-safety wrapper. It removes any previously
published implementation with the same stable marker before appending the current
one, so engine upgrades propagate to already-published providers.

Runtime policy:
- Official Nuvio native QuickJS runtimes (Desktop, Mobile Android, TV Android)
  expose ``__native_fetch`` through a synchronous host bridge. The safety layer
  must never add a media fetch there because JS AbortSignal cannot reliably
  interrupt that native call.
- Known same-title/release collision fixtures are enforced statically on every
  returned row. Ambiguous rows fail closed rather than being shown as wrong media.
- Explicit season/episode tokens that contradict the requested route are rejected.
- Non-native/web-like runtimes may use bounded media preflight when fetch is
  genuinely asynchronous/abortable.
- Every runtime deterministically rejects obvious web/embed/non-media URLs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COLLISION_FIXTURES = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
SAFETY_PREFIX = "/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:"
SAFETY_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'


def _strip_previous(text: str) -> str:
    cursor = 0
    parts: list[str] = []
    while True:
        start = text.find(SAFETY_PREFIX, cursor)
        if start < 0:
            parts.append(text[cursor:])
            break
        marker_end = text.find("*/", start)
        call = text.find(SAFETY_CALL, marker_end + 2 if marker_end >= 0 else start)
        end = text.find(");", call + len(SAFETY_CALL)) if call >= 0 else -1
        if marker_end < 0 or call < 0 or end < 0:
            raise ValueError("unterminated global runtime media safety wrapper")
        parts.append(text[cursor:start])
        cursor = end + 2
    return "".join(parts)


def _collision_policy() -> dict[str, dict[str, Any]]:
    """Build provider-independent release-collision rules from the Lab corpus."""
    try:
        payload = json.loads(COLLISION_FIXTURES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load native collision fixtures: {COLLISION_FIXTURES}") from exc
    output: dict[str, dict[str, Any]] = {}
    for row in payload.get("fixtures") or []:
        if not isinstance(row, dict):
            continue
        fixture = row.get("fixture") if isinstance(row.get("fixture"), dict) else {}
        tmdb_id = str(fixture.get("tmdbId") or "").strip()
        if not tmdb_id or fixture.get("requireExplicitReleaseDisambiguation") is not True:
            continue
        expected_year = int(fixture.get("year") or 0)
        if expected_year <= 0:
            continue
        aliases = [str(value).strip() for value in fixture.get("aliases") or [] if str(value).strip()]
        title = str(fixture.get("title") or "").strip()
        if title and title not in aliases:
            aliases.insert(0, title)
        output[tmdb_id] = {
            "expectedYear": expected_year,
            "ambiguousReleaseYears": sorted({
                int(value) for value in fixture.get("ambiguousReleaseYears") or []
                if str(value).isdigit()
            }),
            "aliases": aliases,
            "forbiddenAliases": [
                str(value).strip() for value in fixture.get("forbiddenAliases") or []
                if str(value).strip()
            ],
            "releaseDisambiguatingAliases": [
                str(value).strip() for value in fixture.get("releaseDisambiguatingAliases") or []
                if str(value).strip()
            ],
        }
    return output


WRAPPER = r'''
/* SAFETY_MARKER */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function norm(v){var x=s(v);try{if(typeof x.normalize==="function")x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
  function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
  function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
  function requestInfo(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{tmdbId:first,mediaType:a[1],season:a[2],episode:a[3]};q.tmdbId=s(q.tmdbId||q.id||first).replace(/^tmdb:/i,"").split(":")[0];q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;q.year=Number(q.year||q.releaseYear||0)||0;q.title=s(q.title||q.name||"");return q}
  function nativeHost(){try{return typeof g.__native_fetch==="function"}catch(_e){return false}}
  function isTv(){try{var ua=s(g.navigator&&g.navigator.userAgent);return /NuvioTV|Android TV/i.test(ua)||(g&&g.__NUVIO_TV_RUNTIME__===true)}catch(_e){return false}}
  function obviousNonMedia(row){var u=s(row&&row.url);if(!u)return"missing_url";if(!/^https?:\/\//i.test(u))return"invalid_url";var lower=u.toLowerCase();if(/(?:youtube\.com|youtube-nocookie\.com)\/(?:embed|watch)(?:\/|\?|$)/i.test(lower))return"video_page_url";if(/\/embed(?:\/|\?|#|$)/i.test(lower))return"embed_page_url";if(/\.(?:html?|php)(?:[?#]|$)/i.test(lower))return"html_page_url";if(/^https?:\/\/[^/]+\/\/www\./i.test(u))return"malformed_nested_url";return""}
  function identityBlob(row){return[row&&row.title,row&&row.name,row&&row.filename,row&&row.description,row&&row.mediaHint].map(s).filter(Boolean).join(" ")}
  function explicitYears(value){var out=[],seen={},m,re=/(?:^|[^0-9])((?:19|20)\d{2})(?=$|[^0-9])/g,text=s(value);while((m=re.exec(text))!==null){var y=Number(m[1]);if(y>=1900&&y<=2099&&!seen[y]){seen[y]=1;out.push(y)}}return out}
  function containsAny(text,values){for(var i=0;i<(values||[]).length;i++){var needle=norm(values[i]);if(needle&&text.indexOf(needle)>=0)return true}return false}
  function routeIdentity(row,q){var text=identityBlob(row),normalized=norm(text),collision=c.collisionFixtures&&c.collisionFixtures[q.tmdbId];if(q.season>0&&q.episode>0){var re=/(?:^|[^a-z0-9])s(?:eason)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?=$|[^a-z0-9])/ig,m;while((m=re.exec(text))!==null){if(Number(m[1])!==q.season||Number(m[2])!==q.episode)return{keep:false,reason:"season_episode_identity_mismatch"}}}if(!collision)return null;if(containsAny(normalized,collision.forbiddenAliases))return{keep:false,reason:"forbidden_release_alias"};var years=explicitYears(text),expected=Number(collision.expectedYear||0);if(years.length){for(var j=0;j<years.length;j++)if(years[j]===expected)return null;return{keep:false,reason:"wrong_release_year"}}if(containsAny(normalized,collision.releaseDisambiguatingAliases))return null;return{keep:false,reason:"ambiguous_release_identity"}}
  function staticSafety(row,q){if(!row||typeof row!=="object")return{keep:false,reason:"invalid_row"};var obvious=obviousNonMedia(row);if(obvious)return{keep:false,reason:obvious};var identity=routeIdentity(row,q);if(identity&&identity.keep===false)return identity;return{keep:true}}
  function rowHeaders(row,range){var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};Object.keys(src).forEach(function(k){out[k]=s(src[k])});try{var bh=row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request;if(bh&&typeof bh==="object")Object.keys(bh).forEach(function(k){if(!(k in out))out[k]=s(bh[k])})}catch(_e){}if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-65535";if(!Object.keys(out).some(function(k){return k.toLowerCase()==="accept"}))out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*";return out}
  function timeoutSignal(ms){try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)return AbortSignal.timeout(ms)}catch(_e){}return void 0}
  async function responseText(r){if(!r)return"";try{if(typeof r.text==="function")return s(await r.text())}catch(_e){}try{if(typeof r.arrayBuffer==="function"){var ab=await r.arrayBuffer();if(ab&&typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(new Uint8Array(ab)))}}catch(_e){}return""}
  async function fetchText(url,row,range){try{var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:rowHeaders(row,range),signal:timeoutSignal(c.timeoutMs)});if(!r)return{state:"unknown",reason:"no_response"};var st=Number(r.status||0),ct=s(r.headers&&r.headers.get?r.headers.get("content-type"):"").toLowerCase();if(st===401||st===403||st===404||st===410||st>=500)return{state:"dead",status:st,contentType:ct};if(!r.ok)return{state:"unknown",status:st,contentType:ct};return{state:"ok",status:st,url:s(r.url||url),contentType:ct,text:await responseText(r)}}catch(e){return{state:"unknown",reason:e&&e.name==="AbortError"?"timeout":"network_error"}}}
  function playlistKind(text){var body=s(text).replace(/^\uFEFF/,"");if(!/^#EXTM3U(?:\s|$)/i.test(body))return"invalid";if(/#EXT-X-STREAM-INF\s*:/i.test(body))return"master";if(/#EXTINF\s*:/i.test(body))return"media";return"unknown"}
  function firstVariant(text,base){var lines=s(text).split(/\r?\n/);for(var i=0;i<lines.length;i++){if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;for(var j=i+1;j<lines.length;j++){var v=s(lines[j]);if(!v||v.charAt(0)==="#")continue;try{return new URL(v,base).toString()}catch(_e){return""}}}return""}
  function durationSeconds(text){var total=0,count=0,re=/#EXTINF\s*:\s*([0-9]+(?:\.[0-9]+)?)/gi,m;while((m=re.exec(s(text)))!==null){var n=Number(m[1]);if(Number.isFinite(n)&&n>0){total+=n;count++}}return count>=2&&total>=60?total:null}
  async function inspectHls(row,url){var r=await fetchText(url,row,false);if(r.state!=="ok")return r;var kind=playlistKind(r.text);if(kind==="invalid")return{state:"dead",reason:"not_hls",status:r.status};if(kind==="media")return{state:"ok",duration:durationSeconds(r.text)};if(kind==="master"){var child=firstVariant(r.text,r.url||url);if(!child)return{state:"dead",reason:"master_without_variant"};var cr=await fetchText(child,row,false);if(cr.state!=="ok")return cr;var ck=playlistKind(cr.text);if(ck!=="media"&&ck!=="master")return{state:"dead",reason:"invalid_child"};return{state:"ok",duration:durationSeconds(cr.text)}}return{state:"ok",duration:null}}
  function mediaKind(row){var u=s(row&&row.url).toLowerCase(),t=s(row&&(row.type||row.format)).toLowerCase();if(/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(u)||/hls|mpegurl|m3u8/.test(t))return"hls";if(/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(u)||/mp4|matroska|webm|video\//.test(t))return"direct";return"other"}
  async function expectedSeconds(q){if(!c.durationIdentity||!q||!/^\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="anime"||q.mediaType==="series")?"tv":"movie",url;if(kind==="tv"&&q.season>0&&q.episode>0)url="https://api.themoviedb.org/3/tv/"+encodeURIComponent(q.tmdbId)+"/season/"+q.season+"/episode/"+q.episode+"?api_key="+c.tmdbKey;else url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+c.tmdbKey;try{var r=await g.fetch(url,{headers:{Accept:"application/json"},signal:timeoutSignal(c.tmdbTimeoutMs)});if(!r||!r.ok)return null;var d=await r.json(),minutes=Number(d&&d.runtime||0);if(!minutes&&kind==="tv"&&Array.isArray(d&&d.episode_run_time)&&d.episode_run_time.length)minutes=Number(d.episode_run_time[0]||0);return minutes>=5?minutes*60:null}catch(_e){return null}}
  async function directPlayable(row,url){var r=await fetchText(url,row,true);if(r.state!=="ok")return r;if(/text\/html|application\/xhtml/i.test(r.contentType)||/^<!doctype html|^<html/i.test(r.text||""))return{state:"dead",reason:"html_payload"};return{state:"ok"}}
  async function remoteCheck(row,expected,tv){var kind=mediaKind(row),result;if(kind==="hls")result=await inspectHls(row,s(row.url));else if(kind==="direct")result=await directPlayable(row,s(row.url));else return{keep:true};if(result.state==="dead")return{keep:false,reason:result.reason||("http_"+result.status)};if(result.state==="unknown"){if(c.strictPlayback||tv)return{keep:false,reason:result.reason||"unverified_media"};return{keep:true}}if(kind==="hls"&&expected&&result.duration){var ratio=result.duration/expected;if(ratio<c.minDurationRatio||ratio>c.maxDurationRatio)return{keep:false,reason:"duration_identity_mismatch",ratio:ratio}}return{keep:true}}
  function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioRuntimeCapabilitySafetyV4)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var q=requestInfo(arguments),tv=isTv(),nativeRuntime=nativeHost();var staticRows=x.list.filter(function(row){return staticSafety(row,q).keep});if(nativeRuntime)return rebuild(v,x,staticRows);var expected=await expectedSeconds(q),head=staticRows.slice(0,c.maxRows),tail=staticRows.slice(c.maxRows),checks=await Promise.all(head.map(function(row){return remoteCheck(row,expected,tv)})),kept=head.filter(function(_row,i){return checks[i]&&checks[i].keep}).concat(tail);return rebuild(v,x,kept)};wrap.__nuvioRuntimeCapabilitySafetyV4=true;o[k]=wrap;return true}
  var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG);
'''


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    context = kwargs.get("context") if isinstance(kwargs.get("context"), dict) else {}
    provider_id = str(context.get("provider_id") or "").strip().casefold()
    config = {
        "providerId": provider_id,
        "timeoutMs": 6500,
        "tmdbTimeoutMs": 4500,
        "maxRows": 4,
        "minDurationRatio": 0.55,
        "maxDurationRatio": 1.8,
        "durationIdentity": provider_id == "netmirror",
        "strictPlayback": provider_id == "moviebox",
        "collisionFixtures": _collision_policy(),
        "tmdbKey": "1865f43a0549ca50d341dd9ab8b29f49",
        "implementationRevision": "field-safety-v5-native-identity-collisions-all-rows",
    }
    payload = json.dumps(config, separators=(",", ":"), ensure_ascii=False)
    marker = "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:" + hashlib.sha256(payload.encode()).hexdigest()[:12]
    wrapper = WRAPPER.replace("SAFETY_MARKER", marker).replace("CONFIG", payload)
    return _strip_previous(text).rstrip() + "\n" + wrapper.lstrip()
