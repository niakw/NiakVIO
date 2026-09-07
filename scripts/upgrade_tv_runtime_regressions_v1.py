#!/usr/bin/env python3
"""Fix shared TV stale-request cancellation and quality recovery regressions.

Shared/Core-only migration:
- latest provider invocation owns execution; prior in-flight request is aborted and
  given a short settlement grace before the newer invocation installs its fetch
  wrapper, preventing stale catch/retry chains from borrowing the newer wrapper;
- every budgeted fetch is token-bound and rejects before/after native I/O when its
  invocation was superseded;
- stream facts derive quality from the full provider fact surface and drop only
  meaningless placeholders;
- the terminal HLS probe reuses the already-fetched master manifest to recover a
  real quality from RESOLUTION=WxH when upstream provider rows omitted it.

No provider-specific algorithm is introduced.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
FACTS = ROOT / "scripts/provider_patches/global_stream_facts_v1.py"
SANITIZER = ROOT / "scripts/provider_patches/stream_output_sanitizer_v5.py"
MARKER_MEDIA = "NUVIO_PROVIDER_LATEST_REQUEST_OWNS_FETCH_V2"
MARKER_QUALITY = "NUVIO_STREAM_QUALITY_RECOVERY_V2"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_media() -> bool:
    text = MEDIA.read_text(encoding="utf-8")
    if MARKER_MEDIA in text:
        return False

    text = once(
        text,
        '        "tvProviderTimeoutMs": max(5_000, min(int(cfg.get("tv_provider_timeout_ms", 25_000)), 30_000)),\n',
        '        "tvProviderTimeoutMs": max(5_000, min(int(cfg.get("tv_provider_timeout_ms", 25_000)), 30_000)),\n'
        '        "supersedeSettleMs": max(100, min(int(cfg.get("supersede_settle_ms", 1200)), 3000)),\n',
        "media-config-settle",
    )
    text = once(
        text,
        'var requestSerial=0;\nfunction providerTimeoutError(){var e=new Error("nuvio_provider_timeout");e.name="TimeoutError";e.code="NUVIO_PROVIDER_TIMEOUT";e.__nuvioProviderTimeout=true;return e}\n',
        '/* NUVIO_PROVIDER_LATEST_REQUEST_OWNS_FETCH_V2 */\n'
        'var requestSerial=0;\n'
        'function providerTimeoutError(){var e=new Error("nuvio_provider_timeout");e.name="TimeoutError";e.code="NUVIO_PROVIDER_TIMEOUT";e.__nuvioProviderTimeout=true;return e}\n'
        'function providerStaleError(){var e=new Error("nuvio_provider_superseded");e.name="AbortError";e.code="NUVIO_PROVIDER_SUPERSEDED";e.__nuvioProviderStale=true;return e}\n'
        'function tokenOwns(token){try{return !token||!g||g.__nuvioProviderRequestToken===token}catch(_){return false}}\n'
        'function abortController(controller){try{if(controller&&typeof controller.abort==="function")controller.abort()}catch(_){}}\n'
        'async function settlePrior(promise){if(!promise||typeof promise.then!=="function")return;try{if(typeof setTimeout!=="function"){await Promise.resolve();return}await Promise.race([promise,new Promise(function(resolve){setTimeout(resolve,Number(c.supersedeSettleMs||1200))})])}catch(_){}}\n',
        "media-stale-helpers",
    )

    old_fetch = '''function budgetedFetch(original,deadline){
  if(typeof original!=="function")return original;
  var base=original.__nuvioProviderExecutionBudgetBase||original;
  var wrapped=async function(){
    if(deadlineExpired(deadline))throw providerTimeoutError();
    var args=Array.prototype.slice.call(arguments),remaining=deadline>0?Math.max(1,deadline-Date.now()):0;
    if(remaining>0&&args.length>=1){
      var init=args[1]&&typeof args[1]==="object"?Object.assign({},args[1]):{};
      if(!init.signal){try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)init.signal=AbortSignal.timeout(remaining)}catch(_){}}
      args[1]=init;
    }
    if(remaining<=0)return await base.apply(this,args);
    var timer=null;
    var timeoutPromise=new Promise(function(_resolve,reject){
      if(typeof setTimeout!=="function")return;
      timer=setTimeout(function(){reject(providerTimeoutError())},remaining);
    });
    var value;
    try{
      value=typeof setTimeout==="function"
        ? await Promise.race([base.apply(this,args),timeoutPromise])
        : await base.apply(this,args);
    }finally{
      try{if(timer!=null&&typeof clearTimeout==="function")clearTimeout(timer)}catch(_){}
    }
    if(deadlineExpired(deadline))throw providerTimeoutError();
    return value;
  };
'''
    new_fetch = '''function budgetedFetch(original,deadline,requestToken,requestController){
  if(typeof original!=="function")return original;
  var base=original.__nuvioProviderExecutionBudgetBase||original;
  var wrapped=async function(){
    if(!tokenOwns(requestToken))throw providerStaleError();
    if(deadlineExpired(deadline))throw providerTimeoutError();
    var args=Array.prototype.slice.call(arguments),remaining=deadline>0?Math.max(1,deadline-Date.now()):0;
    if(remaining>0&&args.length>=1){
      var init=args[1]&&typeof args[1]==="object"?Object.assign({},args[1]):{};
      if(!init.signal&&requestController&&requestController.signal)init.signal=requestController.signal;
      if(!init.signal){try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)init.signal=AbortSignal.timeout(remaining)}catch(_){}}
      args[1]=init;
    }
    if(!tokenOwns(requestToken))throw providerStaleError();
    var timer=null;
    var timeoutPromise=new Promise(function(_resolve,reject){
      if(typeof setTimeout!=="function"||remaining<=0)return;
      timer=setTimeout(function(){abortController(requestController);reject(providerTimeoutError())},remaining);
    });
    var value;
    try{
      value=(typeof setTimeout==="function"&&remaining>0)
        ? await Promise.race([base.apply(this,args),timeoutPromise])
        : await base.apply(this,args);
    }finally{
      try{if(timer!=null&&typeof clearTimeout==="function")clearTimeout(timer)}catch(_){}
    }
    if(!tokenOwns(requestToken))throw providerStaleError();
    if(deadlineExpired(deadline))throw providerTimeoutError();
    return value;
  };
'''
    text = once(text, old_fetch, new_fetch, "media-token-bound-fetch")

    old_start = '''    var requestToken=0,requestDeadline=0,hadFetch=false,previousFetch,fetchBase,budgetFetchInstalled=false;
    try{
      // Hard-reset media context at every provider invocation. This prevents
      // tv/anime/movie (including anime movies transported as movie) from
      // becoming sticky for the lifetime of a native QuickJS instance.
      if(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"))delete g.__nuvioMediaContext;
      if(g){
        var priorSerial=Number(g.__nuvioProviderRequestSerial||requestSerial);
        requestToken=(Number.isFinite(priorSerial)&&priorSerial>=0?priorSerial:requestSerial)+1;
        requestSerial=requestToken;
        g.__nuvioProviderRequestSerial=requestToken;
        g.__nuvioProviderRequestToken=requestToken;
      }
      hadFetch=!!(g&&Object.prototype.hasOwnProperty.call(g,"fetch"));
      previousFetch=g&&g.fetch;
      fetchBase=previousFetch&&previousFetch.__nuvioProviderExecutionBudgetBase||previousFetch;
    }catch(_){}
    try{
      requestDeadline=Date.now()+providerBudgetMs();
      if(g){
        g.__nuvioProviderDeadlineMs=requestDeadline;
        if(typeof fetchBase==="function"){g.fetch=budgetedFetch(fetchBase,requestDeadline);budgetFetchInstalled=g.fetch!==fetchBase;}
      }
'''
    new_start = '''    var requestToken=0,requestDeadline=0,hadFetch=false,previousFetch,fetchBase,budgetFetchInstalled=false;
    var requestController=null,priorController=null,priorDone=null,resolveDone=null,invocationDone=null;
    try{
      // Capture the prior invocation before claiming the global token/fetch slot.
      // The previous fetch wrapper stays installed during settlement grace, so a
      // stale catch/retry still hits its token-bound wrapper and is rejected.
      if(g){priorController=g.__nuvioProviderAbortController||null;priorDone=g.__nuvioProviderInvocationDone||null}
      if(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"))delete g.__nuvioMediaContext;
      if(g){
        var priorSerial=Number(g.__nuvioProviderRequestSerial||requestSerial);
        requestToken=(Number.isFinite(priorSerial)&&priorSerial>=0?priorSerial:requestSerial)+1;
        requestSerial=requestToken;
        g.__nuvioProviderRequestSerial=requestToken;
        g.__nuvioProviderRequestToken=requestToken;
      }
      invocationDone=new Promise(function(resolve){resolveDone=resolve});
      if(g)g.__nuvioProviderInvocationDone=invocationDone;
      abortController(priorController);
      hadFetch=!!(g&&Object.prototype.hasOwnProperty.call(g,"fetch"));
      previousFetch=g&&g.fetch;
      fetchBase=previousFetch&&previousFetch.__nuvioProviderExecutionBudgetBase||previousFetch;
    }catch(_){}
    try{
      await settlePrior(priorDone);
      if(!tokenOwns(requestToken))return [];
      requestDeadline=Date.now()+providerBudgetMs();
      try{requestController=typeof AbortController!=="undefined"?new AbortController():null}catch(_){requestController=null}
      if(g){
        g.__nuvioProviderDeadlineMs=requestDeadline;
        g.__nuvioProviderAbortController=requestController;
        if(typeof fetchBase==="function"){g.fetch=budgetedFetch(fetchBase,requestDeadline,requestToken,requestController);budgetFetchInstalled=g.fetch!==fetchBase;}
      }
'''
    text = once(text, old_start, new_start, "media-invocation-ownership")

    text = once(
        text,
        '    }catch(error){\n      if(error&&error.__nuvioProviderTimeout)return [];\n      throw error;\n    }finally{\n',
        '    }catch(error){\n      if(error&&(error.__nuvioProviderTimeout||error.__nuvioProviderStale))return [];\n      throw error;\n    }finally{\n      try{if(typeof resolveDone==="function")resolveDone()}catch(_){}\n',
        "media-stale-catch-done",
    )
    text = once(
        text,
        '            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderDeadlineMs"))delete g.__nuvioProviderDeadlineMs;\n            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderRequestToken"))delete g.__nuvioProviderRequestToken;\n',
        '            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderDeadlineMs"))delete g.__nuvioProviderDeadlineMs;\n'
        '            if(g.__nuvioProviderAbortController===requestController)delete g.__nuvioProviderAbortController;\n'
        '            if(g.__nuvioProviderInvocationDone===invocationDone)delete g.__nuvioProviderInvocationDone;\n'
        '            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderRequestToken"))delete g.__nuvioProviderRequestToken;\n',
        "media-cleanup-owned-state",
    )
    MEDIA.write_text(text, encoding="utf-8")
    return True


def patch_facts() -> bool:
    text = FACTS.read_text(encoding="utf-8")
    if MARKER_QUALITY in text:
        return False
    text = once(
        text,
        'function blob(r){return [r&&r.name,r&&r.title,r&&r.size,r&&r.description,r&&r.quality,r&&r.language,r&&r.codec,r&&r.audio,r&&r.sourceType,r&&r.releaseType,r&&r.format,r&&r.hdr,r&&r.videoTech,r&&r.bitDepth,r&&r.subtitles].map(s).join(" ")}',
        '/* NUVIO_STREAM_QUALITY_RECOVERY_V2 */\nfunction urlFacts(r){var u=s(r&&r.url);if(!u)return"";try{u=decodeURIComponent(u)}catch(_e){}return u.replace(/[?#&=/_\\\\.\\-]+/g," ")}\nfunction blob(r){return [r&&r.name,r&&r.title,r&&r.size,r&&r.description,r&&r.quality,r&&r.resolution,r&&r.height,r&&r.width,r&&r.label,r&&r.language,r&&r.codec,r&&r.audio,r&&r.sourceType,r&&r.releaseType,r&&r.format,r&&r.hdr,r&&r.videoTech,r&&r.bitDepth,r&&r.subtitles,r&&r.sourceLabel,r&&r.filename,urlFacts(r)].map(s).join(" ")}',
        "facts-rich-quality-blob",
    )
    text = once(
        text,
        'var q=quality(r,b);if(q)out.quality=q;',
        'var q=quality(r,b);if(q)out.quality=q;else if("quality" in out&&!meaningful(out.quality))delete out.quality;',
        "facts-placeholder-clean-after-derive",
    )
    FACTS.write_text(text, encoding="utf-8")
    return True


def patch_sanitizer() -> bool:
    text = SANITIZER.read_text(encoding="utf-8")
    if MARKER_QUALITY in text:
        return False
    anchor = '''  function repairedHlsUrl(text){
    return "data:application/vnd.apple.mpegurl;charset=utf-8,"+encodeURIComponent(String(text||""));
  }
'''
    helper = '''  /* NUVIO_STREAM_QUALITY_RECOVERY_V2 */
  function meaningfulQuality(value){return !/^(?:|unknown|inconnue?|n\\/?a|null|undefined|none|-+)$/i.test(String(value==null?"":value).trim())}
  function qualityFromHeight(height){var h=Number(height||0);if(h>=2000)return"2160p";if(h>=1350)return"1440p";if(h>=900)return"1080p";if(h>=650)return"720p";if(h>=450)return"480p";if(h>=300)return"360p";return""}
  function qualityFromHls(text,url){
    var value=String(text||""),match,re=/RESOLUTION\\s*=\\s*(\\d{2,5})x(\\d{2,5})/gi,best=0;
    while((match=re.exec(value))!==null)best=Math.max(best,Number(match[2]||0));
    var q=qualityFromHeight(best);if(q)return q;
    var source=String(url||"").toUpperCase();
    if(/(?:\\b4K\\b|\\b2160P?\\b|\\bUHD\\b)/.test(source))return"2160p";
    var m=source.match(/\\b(1440|1080|720|576|540|480|360)P?\\b/);return m?m[1]+"p":"";
  }
  function recoverQuality(stream,text,url){if(!stream||typeof stream!=="object"||meaningfulQuality(stream.quality))return;var q=qualityFromHls(text,url);if(q)stream.quality=q;else try{delete stream.quality}catch(_e){}}
  function repairedHlsUrl(text){
    return "data:application/vnd.apple.mpegurl;charset=utf-8,"+encodeURIComponent(String(text||""));
  }
'''
    text = once(text, anchor, helper, "sanitizer-quality-helper")
    text = once(
        text,
        '        var hls=normalizeHlsText(text,finalUrl);\n        if(!hls)return false;\n        if(hls.repaired){',
        '        var hls=normalizeHlsText(text,finalUrl);\n        if(!hls)return false;\n        recoverQuality(stream,hls.text,finalUrl);\n        if(hls.repaired){',
        "sanitizer-master-quality",
    )
    SANITIZER.write_text(text, encoding="utf-8")
    return True


def validate() -> None:
    media = MEDIA.read_text(encoding="utf-8")
    facts = FACTS.read_text(encoding="utf-8")
    sanitizer = SANITIZER.read_text(encoding="utf-8")
    for needle in (
        MARKER_MEDIA,
        "budgetedFetch(original,deadline,requestToken,requestController)",
        "abortController(priorController)",
        "await settlePrior(priorDone)",
        "if(!tokenOwns(requestToken))throw providerStaleError()",
        "__nuvioProviderInvocationDone",
    ):
        if needle not in media:
            raise AssertionError(f"media cancellation missing {needle}")
    for needle in (MARKER_QUALITY, "r&&r.resolution", "r&&r.height", "urlFacts(r)"):
        if needle not in facts:
            raise AssertionError(f"facts quality recovery missing {needle}")
    for needle in (MARKER_QUALITY, "qualityFromHls", "RESOLUTION", "recoverQuality(stream,hls.text,finalUrl)"):
        if needle not in sanitizer:
            raise AssertionError(f"sanitizer quality recovery missing {needle}")


def main() -> int:
    changed = [patch_media(), patch_facts(), patch_sanitizer()]
    validate()
    print(f"TV_RUNTIME_REGRESSIONS_V1_OK changed={str(any(changed)).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
