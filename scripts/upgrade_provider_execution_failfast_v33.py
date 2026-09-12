#!/usr/bin/env python3
"""V33: isolate provider execution budgets and fail fast on repeated hard failures.

Goals:
- one provider owns one 25 s request budget;
- a single stalled fetch cannot consume that entire budget when timer primitives exist;
- first 403/429/network failure never kills a provider, preserving legitimate fallback;
- repeated hard failures make later fallback fetches fail immediately;
- stale navigation and provider-level deadline remain authoritative;
- QuickJS-like runtimes without global setTimeout/clearTimeout must not crash.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
REVISION = "tmdb-data-contract-launch-gate-v33-25s-isolated-failfast"

RUNTIME_BLOCK = r'''function providerTimeoutError(){var e=new Error("nuvio_provider_timeout");e.name="TimeoutError";e.code="NUVIO_PROVIDER_TIMEOUT";e.__nuvioProviderTimeout=true;return e}
function providerFetchTimeoutError(){var e=new Error("nuvio_provider_fetch_timeout");e.name="TimeoutError";e.code="NUVIO_PROVIDER_FETCH_TIMEOUT";e.__nuvioProviderFetchTimeout=true;return e}
function providerFailFastError(status){var e=new Error("nuvio_provider_fail_fast"+(status?"_http_"+status:""));e.name="NetworkError";e.code="NUVIO_PROVIDER_FAIL_FAST";e.__nuvioProviderFailFast=true;return e}
function providerStaleError(){var e=new Error("nuvio_provider_superseded");e.name="AbortError";e.code="NUVIO_PROVIDER_SUPERSEDED";e.__nuvioProviderStale=true;return e}
function tokenOwns(token){try{return !token||!g||g.__nuvioProviderRequestToken===token}catch(_){return false}}
function abortController(controller){try{if(controller&&typeof controller.abort==="function")controller.abort()}catch(_){}}
function requestAbortPromise(controller,requestToken){
  return new Promise(function(_resolve,reject){
    try{
      var signal=controller&&controller.signal;
      if(!signal)return;
      var fail=function(){reject(tokenOwns(requestToken)?providerTimeoutError():providerStaleError())};
      if(signal.aborted){fail();return}
      if(typeof signal.addEventListener==="function")signal.addEventListener("abort",fail,{once:true});
    }catch(_){}
  });
}
async function settlePrior(promise){if(!promise||typeof promise.then!=="function")return;try{if(typeof setTimeout!=="function"){await Promise.resolve();return}await Promise.race([promise,new Promise(function(resolve){setTimeout(resolve,Number(c.supersedeSettleMs||1200))})])}catch(_){}}
function deadlineExpired(deadline){var n=Number(deadline);return Number.isFinite(n)&&n>0&&Date.now()>=n}
function tvRuntime(){try{var ua=s(g&&g.navigator&&g.navigator.userAgent);return /NuvioTV|Android TV/i.test(ua)||(g&&g.__NUVIO_TV_RUNTIME__===true)}catch(_){return false}}
function providerBudgetMs(){return tvRuntime()?Number(c.tvProviderTimeoutMs||25000):Number(c.providerTimeoutMs||25000)}
function providerFetchSliceMs(){var n=Number(c.fetchSliceMs||7000);return Number.isFinite(n)?Math.max(100,Math.min(n,15000)):7000}
function hardHttpStatus(status){var n=Number(status||0);return n===400||n===401||n===403||n===408||n===410||n===425||n===429||n===451||n>=500}
function budgetedFetch(original,deadline,requestToken,requestController){
  if(typeof original!=="function")return original;
  var base=original.__nuvioProviderExecutionBudgetBase||original;
  var hardFailures=0,lastHardStatus=0,failFast=false;
  function publishState(){try{if(g&&tokenOwns(requestToken))g.__nuvioProviderFailureState={hardFailures:hardFailures,lastStatus:lastHardStatus,failFast:failFast===true}}catch(_){}}
  function noteFailure(status){hardFailures+=1;lastHardStatus=Number(status||0)||0;if(hardFailures>=Number(c.maxHardFailures||3))failFast=true;publishState()}
  function noteAlive(){hardFailures=0;lastHardStatus=0;failFast=false;publishState()}
  var wrapped=async function(){
    if(!tokenOwns(requestToken))throw providerStaleError();
    if(deadlineExpired(deadline))throw providerTimeoutError();
    if(failFast)throw providerFailFastError(lastHardStatus);
    var args=Array.prototype.slice.call(arguments),remaining=deadline>0?Math.max(1,deadline-Date.now()):0;
    var slice=remaining>0?Math.min(remaining,providerFetchSliceMs()):providerFetchSliceMs();
    var init=args[1]&&typeof args[1]==="object"?Object.assign({},args[1]):{};
    var fetchController=null,parentSignal=null,parentAbort=null;
    try{fetchController=typeof AbortController!=="undefined"?new AbortController():null}catch(_){fetchController=null}
    if(requestController&&requestController.signal&&fetchController){
      parentSignal=requestController.signal;
      parentAbort=function(){abortController(fetchController)};
      try{if(parentSignal.aborted)parentAbort();else if(typeof parentSignal.addEventListener==="function")parentSignal.addEventListener("abort",parentAbort,{once:true})}catch(_){}
    }
    if(!init.signal&&fetchController&&fetchController.signal)init.signal=fetchController.signal;
    if(!init.signal&&requestController&&requestController.signal)init.signal=requestController.signal;
    if(!init.signal){try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)init.signal=AbortSignal.timeout(slice)}catch(_){} }
    if(args.length>=1)args[1]=init;
    if(!tokenOwns(requestToken))throw providerStaleError();
    var timer=null;
    var timeoutPromise=new Promise(function(_resolve,reject){
      if(typeof setTimeout!=="function"||slice<=0)return;
      timer=setTimeout(function(){abortController(fetchController);reject(providerFetchTimeoutError())},slice);
    });
    var value,abortPromise=requestAbortPromise(requestController,requestToken);
    try{
      value=(typeof setTimeout==="function"&&slice>0)
        ? await Promise.race([base.apply(this,args),timeoutPromise,abortPromise])
        : await Promise.race([base.apply(this,args),abortPromise]);
    }catch(error){
      if(error&&(error.__nuvioProviderStale||error.__nuvioProviderTimeout))throw error;
      noteFailure(0);
      if(failFast)throw providerFailFastError(lastHardStatus);
      throw error;
    }finally{
      try{if(timer!=null&&typeof clearTimeout==="function")clearTimeout(timer)}catch(_){}
      try{if(parentSignal&&parentAbort&&typeof parentSignal.removeEventListener==="function")parentSignal.removeEventListener("abort",parentAbort)}catch(_){}
    }
    if(!tokenOwns(requestToken))throw providerStaleError();
    if(deadlineExpired(deadline))throw providerTimeoutError();
    var status=Number(value&&value.status||0);
    if(status&&hardHttpStatus(status))noteFailure(status);else if(status>=200&&status<500)noteAlive();
    return value;
  };
  try{
    Object.defineProperty(wrapped,"__nuvioProviderExecutionBudgetV1",{value:true});
    Object.defineProperty(wrapped,"__nuvioProviderExecutionBudgetBase",{value:base});
  }catch(_){
    wrapped.__nuvioProviderExecutionBudgetV1=true;
    wrapped.__nuvioProviderExecutionBudgetBase=base;
  }
  return wrapped;
}
async function invokeNativeWithBudget(native,self,args,requestController,requestToken){
  var pending=native.apply(self,args);
  pending=Promise.resolve(pending);
  if(!requestController)return await pending;
  return await Promise.race([pending,requestAbortPromise(requestController,requestToken)]);
}
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if REVISION in text:
        validate(text)
        return False

    text = text.replace('cfg.get("provider_timeout_ms", 60_000)', 'cfg.get("provider_timeout_ms", 25_000)')
    text = text.replace('cfg.get("tv_provider_timeout_ms", 60_000)', 'cfg.get("tv_provider_timeout_ms", 25_000)')

    supersede = '        "supersedeSettleMs": max(100, min(int(cfg.get("supersede_settle_ms", 1200)), 3000)),\n'
    if '"fetchSliceMs"' not in text:
        text = replace_once(
            text,
            supersede,
            supersede
            + '        "fetchSliceMs": max(100, min(int(cfg.get("fetch_slice_ms", 7_000)), 15_000)),\n'
            + '        "maxHardFailures": max(2, min(int(cfg.get("max_hard_failures", 3)), 8)),\n',
            "budget config",
        )

    for old_revision in (
        "tmdb-data-contract-launch-gate-v31-pre-network-semantic-gate",
        "tmdb-data-contract-launch-gate-v32-25s-navigation-budget",
    ):
        text = text.replace(old_revision, REVISION)

    start = text.index("function providerTimeoutError()")
    end = text.index("function install(o,k){", start)
    text = text[:start] + RUNTIME_BLOCK + text[end:]

    old_vars = '    var requestToken=0,requestDeadline=0,hadFetch=false,previousFetch,fetchBase,budgetFetchInstalled=false;\n    var requestController=null,priorController=null,priorDone=null,resolveDone=null,invocationDone=null;\n'
    new_vars = '    var requestToken=0,requestDeadline=0,hadFetch=false,previousFetch,fetchBase,budgetFetchInstalled=false;\n    var requestController=null,priorController=null,priorDone=null,resolveDone=null,invocationDone=null,requestTimer=null;\n'
    text = replace_once(text, old_vars, new_vars, "request timer vars")

    controller_anchor = '      try{requestController=typeof AbortController!=="undefined"?new AbortController():null}catch(_){requestController=null}\n'
    controller_new = controller_anchor + '      try{if(requestController&&typeof setTimeout==="function")requestTimer=setTimeout(function(){abortController(requestController)},Math.max(1,requestDeadline-Date.now()))}catch(_){}\n'
    text = replace_once(text, controller_anchor, controller_new, "request deadline timer")

    text = replace_once(
        text,
        "      var value=await native.apply(this,a);\n",
        "      var value=await invokeNativeWithBudget(native,this,a,requestController,requestToken);\n",
        "initial native invocation",
    )
    text = replace_once(
        text,
        "        value=await native.apply(this,verified);\n",
        "        value=await invokeNativeWithBudget(native,this,verified,requestController,requestToken);\n",
        "verified native invocation",
    )

    finally_anchor = '    }finally{\n      try{if(typeof resolveDone==="function")resolveDone()}catch(_){}\n'
    finally_new = '    }finally{\n      try{if(requestTimer!=null&&typeof clearTimeout==="function")clearTimeout(requestTimer)}catch(_){}\n      try{if(typeof resolveDone==="function")resolveDone()}catch(_){}\n'
    text = replace_once(text, finally_anchor, finally_new, "request timer cleanup")

    catch_anchor = '    }catch(error){\n      if(error&&(error.__nuvioProviderTimeout||error.__nuvioProviderStale))return [];\n      throw error;\n'
    catch_new = '    }catch(error){\n      if(error&&(error.__nuvioProviderTimeout||error.__nuvioProviderStale||error.__nuvioProviderFailFast||error.__nuvioProviderFetchTimeout))return [];\n      throw error;\n'
    text = replace_once(text, catch_anchor, catch_new, "fail-fast catch")

    cleanup_anchor = '            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderDeadlineMs"))delete g.__nuvioProviderDeadlineMs;\n'
    cleanup_new = cleanup_anchor + '            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderFailureState"))delete g.__nuvioProviderFailureState;\n'
    text = replace_once(text, cleanup_anchor, cleanup_new, "failure-state cleanup")

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        REVISION,
        'cfg.get("provider_timeout_ms", 25_000)',
        'cfg.get("tv_provider_timeout_ms", 25_000)',
        '"fetchSliceMs"',
        '"maxHardFailures"',
        'function providerBudgetMs(){return tvRuntime()?Number(c.tvProviderTimeoutMs||25000):Number(c.providerTimeoutMs||25000)}',
        'function providerFetchSliceMs()',
        'function hardHttpStatus(status)',
        'function providerFailFastError(status)',
        'function invokeNativeWithBudget(native,self,args,requestController,requestToken)',
        'var pending=native.apply(self,args);',
        'pending=Promise.resolve(pending);',
        'requestTimer=setTimeout(function(){abortController(requestController)}',
        'invokeNativeWithBudget(native,this,a,requestController,requestToken)',
        'invokeNativeWithBudget(native,this,verified,requestController,requestToken)',
        'error.__nuvioProviderFailFast',
        'error.__nuvioProviderFetchTimeout',
    ):
        if needle not in value:
            raise AssertionError(f"provider fail-fast V33 missing {needle}")
    if 'c.providerTimeoutMs||60000' in value or 'c.tvProviderTimeoutMs||60000' in value:
        raise AssertionError("60 s provider fallback remains")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_EXECUTION_FAILFAST_V33_OK "
        f"changed={str(changed).lower()} provider_budget_ms=25000 fetch_slice_ms=7000 max_hard_failures=3"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
