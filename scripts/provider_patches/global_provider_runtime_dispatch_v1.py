#!/usr/bin/env python3
"""Core-owned dispatch for provider-registered runtime resolvers.

A Provider Lego may register one transport resolver on
``globalThis.__niakvioProviderRuntimeResolverV1``. The provider never owns the
final exported getStreams wrapper: this Core brick installs the dispatcher after
provider composition/runtime compatibility and before stream facts/identity.

The hook receives ``(arguments, context)``. ``context.native`` is the exact
pre-dispatch provider runtime and ``context.receiver`` is its receiver. This lets
a provider Lego make a narrowly scoped transport adaptation (for example a
request fingerprint) while Core still owns the final wrapper and all output
policy. Returning ``null``/``undefined`` delegates to the native runtime.
"""
from __future__ import annotations

from typing import Any

from provider_patch_blocks import has_managed_fix, replace_managed_fix, strip_legacy_iife

MARKER = "NUVIO_GLOBAL_PROVIDER_RUNTIME_DISPATCH_V1"
MANAGED_FIX_ID = "CORE.PROVIDER_RUNTIME_DISPATCH.V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if not has_managed_fix(text, MANAGED_FIX_ID):
        text = strip_legacy_iife(text, f"/* {MARKER} */")
    wrapper = r'''
/* NUVIO_GLOBAL_PROVIDER_RUNTIME_DISPATCH_V1 */
;(function(g){"use strict";
function install(o,k){
  if(!o||typeof o[k]!=="function"||o[k].__nuvioProviderRuntimeDispatchV1)return false;
  var native=o[k];
  var wrap=async function(){
    var hook=null;
    try{hook=g&&g.__niakvioProviderRuntimeResolverV1}catch(_e){}
    if(hook&&typeof hook.resolve==="function"){
      try{
        var value=await hook.resolve(arguments,{native:native,receiver:this});
        if(value!==null&&value!==undefined)return value;
      }catch(_hookError){}
    }
    return await native.apply(this,arguments);
  };
  wrap.__nuvioProviderRuntimeDispatchV1=true;
  o[k]=wrap;
  return true;
}
var ok=false;
try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}
try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e2){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={"revision": "provider-runtime-dispatch-v1", "fallback": "native-on-null-or-error", "hookContext": "native+receiver"},
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
