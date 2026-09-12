#!/usr/bin/env python3
"""Install Core-owned provider runtime dispatch and migrate Vostfree to registration."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APPLY=ROOT/'scripts/apply_provider_overrides.py'
VOST=ROOT/'scripts/provider_patches/vostfree_dle_uqload_runtime_v1.py'
OVERRIDES=ROOT/'provider-overrides.json'
VOST_LEGO='scripts/provider_patches/vostfree_dle_uqload_runtime_v1.py'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old,new,1)


def upgrade_apply() -> None:
    text=APPLY.read_text()
    if 'GLOBAL_PROVIDER_RUNTIME_DISPATCH = "scripts/provider_patches/global_provider_runtime_dispatch_v1.py"' not in text:
        text=replace_once(
            text,
            'GLOBAL_RUNTIME_COMPAT = "scripts/provider_patches/global_runtime_compat_v1.py"\n',
            'GLOBAL_RUNTIME_COMPAT = "scripts/provider_patches/global_runtime_compat_v1.py"\nGLOBAL_PROVIDER_RUNTIME_DISPATCH = "scripts/provider_patches/global_provider_runtime_dispatch_v1.py"\n',
            'dispatch constant',
        )
    if '"NUVIO_GLOBAL_PROVIDER_RUNTIME_DISPATCH_V1",' not in text:
        text=replace_once(
            text,
            '    "NUVIO_GLOBAL_RUNTIME_COMPAT_V1",\n',
            '    "NUVIO_GLOBAL_RUNTIME_COMPAT_V1",\n    "NUVIO_GLOBAL_PROVIDER_RUNTIME_DISPATCH_V1",\n',
            'generated core marker',
        )
    marker='''        # Facts and identity are independent owned Core Lego. Apply each one\n        # explicitly so the v3 ownership guard can prove that a patch only mutates\n        # the block it declares.\n'''
    if 'scope": "global_provider_runtime_dispatch"' not in text:
        block='''        # Provider-specific transport code may register a resolver in Provider Lego,\n        # but the final execution wrapper is Core-owned. Install the dispatcher\n        # before facts/identity so resolver output still traverses every shared Core\n        # output policy; MEDIA_TYPE remains outside it and provides canonical context.\n        if "NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1" in text:\n            before = text\n            text = _apply_patch_script(\n                text,\n                provider_id,\n                GLOBAL_PROVIDER_RUNTIME_DISPATCH,\n                {},\n                None,\n            )\n            if text != before:\n                applied.append({\n                    "type": "patch_script",\n                    "path": GLOBAL_PROVIDER_RUNTIME_DISPATCH,\n                    "phase": phase,\n                    "scope": "global_provider_runtime_dispatch",\n                })\n\n'''
        text=replace_once(text,marker,block+marker,'dispatch composition slot')
    APPLY.write_text(text)


def upgrade_vostfree() -> None:
    text=VOST.read_text()
    text=text.replace('from provider_patch_blocks import replace_managed_fix, strip_managed_fix','from provider_patch_blocks import replace_managed_fix')
    if '/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */' not in text:
        text=replace_once(
            text,
            '/* NIAKVIO_VOSTFREE_DLE_UQLOAD_RUNTIME_V1 */\n',
            '/* NIAKVIO_VOSTFREE_DLE_UQLOAD_RUNTIME_V1 */\n/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */\n',
            'vostfree runtime marker',
        )
    old='''  function install(container,key){\n    try{\n      if(!container||typeof container[key]!=="function"||container[key].__niakvioVostfreeUqV1)return false;\n      var original=container[key];\n      var wrapped=async function(){var r=await resolve(arguments);if(r===null)return await original.apply(this,arguments);return Array.isArray(r)?r:[]};\n      wrapped.__niakvioVostfreeUqV1=true;container[key]=wrapped;return true;\n    }catch(_e){return false}\n  }\n  var exported=false;\n  try{if(typeof module!=="undefined"&&module.exports)exported=install(module.exports,"getStreams")||exported}catch(_e){}\n  try{if(g&&typeof g.getStreams==="function"){if(exported&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e2){}\n'''
    new='''  try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"vostfree",resolve:resolve}}catch(_e){}\n'''
    if old in text:
        text=text.replace(old,new,1)
    elif '__niakvioProviderRuntimeResolverV1={provider:"vostfree"' not in text:
        raise SystemExit('vostfree install block anchor missing')
    old_apply='''    # This runtime must be the final provider-owned getStreams wrapper. Replacing\n    # it in place leaves later generated getStreams assignments able to erase it.\n    # Drop the prior owned rectangle first so v3 inserts it at the provider/Core\n    # boundary, after all provider composition and before Core wrappers.\n    source=strip_managed_fix(text,MANAGED_FIX_ID)\n    return replace_managed_fix(source,MANAGED_FIX_ID,wrapper,data={"site":payload["site"],"search":"dle-post","episode":"buttons_N -> uqload player/content token","playerContract":"anime.js uqload embed prefix","terminal":"packed Uqload HLS + EXTM3U","semanticLane":"anime","fixtureHardcodes":False,"terminalOrdering":True})\n'''
    new_apply='''    return replace_managed_fix(text,MANAGED_FIX_ID,wrapper,data={"site":payload["site"],"search":"dle-post","episode":"buttons_N -> uqload player/content token","playerContract":"anime.js uqload embed prefix","terminal":"packed Uqload HLS + EXTM3U","semanticLane":"anime","fixtureHardcodes":False,"runtimeResolverRegistration":True})\n'''
    if old_apply in text:
        text=text.replace(old_apply,new_apply,1)
    elif 'runtimeResolverRegistration' not in text:
        raise SystemExit('vostfree apply anchor missing')
    VOST.write_text(text)


def upgrade_overrides() -> None:
    cfg=json.loads(OVERRIDES.read_text())
    patches=cfg.setdefault('provider_patches',{})
    row=patches.setdefault('vostfree',{})
    scripts=row.setdefault('provider_lego_scripts',[])
    if VOST_LEGO not in scripts:
        scripts.append(VOST_LEGO)
    opts=row.setdefault('provider_lego_options',{})
    lego=opts.setdefault(VOST_LEGO,{})
    lego.setdefault('site','https://ipv4.vostfree.ws')
    # Preserve whatever durable route/domain DATA was already learned. This change
    # only promotes the already-proven Vostfree resolver into canonical composition.
    OVERRIDES.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')


def main() -> int:
    upgrade_apply(); upgrade_vostfree(); upgrade_overrides()
    print('PROVIDER_RUNTIME_DISPATCH_V1_UPGRADED')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
