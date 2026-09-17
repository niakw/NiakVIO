#!/usr/bin/env python3
"""Adapt AniKotoTV V2 to MegaPlay's current encrypted-source contract.

MegaPlay now returns ``enc`` instead of a plaintext ``sources`` array. When that
happens, preserve the already identity-correlated, HTTP-verified MegaPlay player
URL as an embed row. Core's correlated-player policy remains responsible for
allowing that embed through; this patch never fabricates a direct media URL.
"""
from __future__ import annotations

from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIKOTOTV.MEGAPLAY_EMBED_FALLBACK.V3"
MARKER = "NIAKVIO_ANIKOTOTV_MEGAPLAY_EMBED_FALLBACK_V3"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    old_resolver = '''async function resolveMega(url,referer,cookie){if(!/^https?:\\/\\/(?:www\\.)?megaplay\\.buzz\\//i.test(s(url)))return"";var page=await get(url,referer,false,cookie,"https://megaplay.buzz"),fid=megaFileId(page.body);if(!fid)return"";var sources=await get("https://megaplay.buzz/stream/getSources?id="+encodeURIComponent(fid),url,true,page.cookie||cookie,"https://megaplay.buzz");return finalSource(sources.body)}'''
    new_resolver = '''async function resolveMega(url,referer,cookie){if(!/^https?:\\/\\/(?:www\\.)?megaplay\\.buzz\\//i.test(s(url)))return"";var page=await get(url,referer,false,cookie,"https://megaplay.buzz"),fid=megaFileId(page.body);if(!fid)return"";var sources=await get("https://megaplay.buzz/stream/getSources?id="+encodeURIComponent(fid),url,true,page.cookie||cookie,"https://megaplay.buzz"),direct=finalSource(sources.body);if(direct)return direct;var data=parsed(sources.body);return data&&typeof data==="object"&&s(data.enc)?url:""}'''
    if old_resolver not in text:
        raise ValueError(f"{MANAGED_FIX_ID}: AniKotoTV V2 resolveMega contract not found")
    text = text.replace(old_resolver, new_resolver, 1)

    old_row = '''var row={name:c.name,title:c.name,url:media,provider:c.provider,headers:headers};if(ql)row.quality=ql;return[row]'''
    new_row = '''var row={name:c.name,title:c.name,url:media,provider:c.provider,headers:headers};if(isMega&&media===u){row.isDirect=false;row.__nuvioCorrelatedPlayerFallbackV1={url:u}}else row.isDirect=true;if(ql)row.quality=ql;return[row]'''
    if old_row not in text:
        raise ValueError(f"{MANAGED_FIX_ID}: AniKotoTV V2 output row contract not found")
    text = text.replace(old_row, new_row, 1)

    marker = r'''
/* NIAKVIO_ANIKOTOTV_MEGAPLAY_EMBED_FALLBACK_V3 */
'''
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        marker.lstrip(),
        data={
            "runtimeFamily": "anikoto-megaplay-encrypted-source-embed-fallback-v3",
            "sourceContract": "getSources plaintext sources OR encrypted enc",
            "encryptedFallback": "correlated verified embed only",
            "fabricatesDirectMedia": False,
            "coreFinalOutputOwnership": True,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
