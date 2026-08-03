#!/usr/bin/env python3
"""Teach StreamZo to read data-embed and preserve the external player.

The upstream resolver may fail to turn a valid third-party iframe into direct
media. Nuvio supports external players, so resolver failure must not erase the
player URL that StreamZo already exposed on its detail page.
"""
from __future__ import annotations


def apply(text: str, **_kwargs) -> str:
    marker = "NUVIO_STREAMZO_DATA_EMBED_V2"
    if marker in text:
        return text
    start = text.find("function k2(t){")
    end = text.find("function pE(t)", start)
    if start < 0 or end < 0:
        # The generic catalogue recovery remains usable when upstream renames
        # its minified extractor. Do not block an otherwise valid release.
        return text
    extractor = r'''function k2(t){/* NUVIO_STREAMZO_DATA_EMBED_V2 */if(!t)return null;let a=t.match(/(?:data-embed|data-src|data-player|data-url)=['\"]([^'\"]+)['\"]/i);if(a)return a[1].replace(/&amp;/gi,"&");let n=t.match(/<iframe[^>]*id=['\"]video-frame['\"][^>]*src=['\"]([^'\"]+)['\"]/i);if(n)return n[1];let i=t.match(/<iframe[^>]*src=['\"]([^'\"]*(?:\/embed\/|\/player\/)[^'\"]*)['\"]/i);if(i)return i[1];let s=t.match(/id=['\"]player['\"][^>]*>[\s\S]*?<iframe[^>]*src=['\"]([^'\"]+)['\"]/i);return s?s[1]:null}'''
    text = text[:start] + extractor + text[end:]

    p_start = text.find("function P2(t,n,i){")
    p_end = text.find("function mE(t,n)", p_start)
    if p_start < 0 or p_end < 0:
        return text
    resolver = r'''function P2(t,n,i){return K(this,null,function*(){let s=t;s.startsWith("/")?s=`${me.BASE_URL}${s}`:t.startsWith("http")||(s=`${me.BASE_URL}/${t}`);let g={name:`Streamzo (${i})`,title:`Streamzo - ${n}`,url:s,quality:n,headers:{Referer:`${me.BASE_URL}/`,Origin:me.BASE_URL},isDirect:/\.(?:m3u8|mp4|mpd)(?:[?#]|$)/i.test(s)};try{let a=yield vu(s,{timeout:mu.EMBED}),c=gE(a);if(c){let f=c;f.startsWith("//")?f="https:"+f:f.startsWith("/")&&(f=`${me.BASE_URL}${f}`);g.url=f,g.isDirect=/\.(?:m3u8|mp4|mpd)(?:[?#]|$)/i.test(f);let h=yield _u(g);return h&&h.url&&h.isDirect?h:g}let h=yield _u(g);return h&&h.url&&h.isDirect?h:g}catch(a){return console.warn(`[Streamzo] Direct resolution unavailable, preserving external player: ${a.message}`),g}})}'''
    return text[:p_start] + resolver + text[p_end:]
