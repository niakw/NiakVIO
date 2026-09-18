#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'scripts'/'provider_patches'/'anikototv_runtime_v3.py').read_text(encoding='utf-8')

assert 'playerUrl.searchParams.get("s")' in src
assert r'/\/stream\/s-(\d+)\//i.exec(playerUrl.pathname)' in src
assert 'api+="&s="+encodeURIComponent(sv)' in src
assert 'sessionCookie=mergeCookies(cookie,page.cookie)' in src
assert 'playbackCookie=mergeCookies(sessionCookie,sources.cookie)' in src
assert 'headers:megaPlaybackHeaders(direct,page.url||url,playbackCookie)' in src
assert 'async function signMegaMedia(file)' in src
assert 'MpCdnT0k3n!9f2K#xQ7vL5mR8wN1pY4s' in src
assert 'file=await signMegaMedia(file)' in src
assert 'parsedUrl.search=' in src
assert 'searchParams.set(' not in src
assert 'searchParams.delete(' not in src

# Current provider evidence uses player routes such as /stream/s-2/10789/sub.
# The runtime must preserve server selector 2 when calling getSources.
sample='/stream/s-2/10789/sub'
import re
m=re.search(r'/stream/s-(\d+)/', sample, re.I)
assert m and m.group(1)=='2'

print('AniKotoTV v3 MegaPlay server-selector contract passed')
assert 'g.crypto&&g.crypto.subtle' in src
assert '__crypto_aes_decrypt_raw' in src
assert 'await finalSource(sources.body)' in src
assert 'anikoto_megaplay_terminal' in src
