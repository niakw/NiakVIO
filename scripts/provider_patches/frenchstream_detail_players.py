#!/usr/bin/env python3
"""Recover Frenchstream players from the current detail page when film_api is gone."""
from __future__ import annotations


def apply(text: str, **_kwargs) -> str:
    marker = "NUVIO_FRENCHSTREAM_DETAIL_PLAYERS_V1"
    if marker in text:
        return text
    start = text.find("function os(t,n,i){")
    end = text.find("function cx(t,n)", start)
    if start < 0 or end < 0:
        raise ValueError("Frenchstream film resolver function not found")
    replacement = r'''function os(t,n,i,s){return P(this,null,function*(){/* NUVIO_FRENCHSTREAM_DETAIL_PLAYERS_V1 */let a=le+"/engine/ajax/film_api.php?id="+t,_=[];try{let c=yield as(a,{baseUrl:le}),f=c==null?void 0:c.players;if(f&&typeof f==="object")for(let g of Object.keys(f)){let h=f[g];if(!(!h||typeof h!=="object"))for(let m of Object.keys(h)){let A=h[m];typeof A==="string"&&A.startsWith("http")&&_.push(eg("Frenchstream",g,m,A,null,i))}}if(_.length>0)return _}catch(c){console.warn("[Frenchstream] film_api unavailable for "+t+": "+c.message)}if(!s)return null;try{let c=new URL(s,le).toString(),f=yield ss(c,{timeout:kE,baseUrl:le}),g=[],h=new Set,m=(A,D,C)=>{if(!A)return;A=String(A).replace(/&amp;/gi,"&").replace(/\\\//g,"/").trim();try{A=new URL(A,c).toString()}catch(x){return}if(!/^https?:/i.test(A)||h.has(A)||/\.(?:jpg|jpeg|png|webp|gif|svg|css|js|ico)(?:\?|$)/i.test(A))return;let x=(D||"").toLowerCase(),T=x.includes("vostfr")?"vostfr":x.includes("vo")?"vo":"vf",k=(C||A).match(/(?:2160|1080|720|480)p?/i);h.add(A),g.push(eg("Frenchstream",C||"player",T,A,k?k[0]:null,i))},A=[/<(?:iframe|source|video)[^>]+(?:src|data-src|data-embed|data-player|data-url)=["']([^"']+)["'][^>]*>/gi,/\b(?:data-src|data-embed|data-player|data-url|data-video|file|source|url)=["']([^"']+)["']/gi,/["'](?:url|file|src|embedUrl|embed_url)["']\s*:\s*["']([^"']+)["']/gi,/["'](https?:\\?\/\\?\/[^"'<>\s]+(?:\.m3u8|\.mp4|\/embed[^"'<>\s]*|\/player[^"'<>\s]*))["']/gi];for(let D of A){let C;for(;(C=D.exec(f))!==null;){let x=f.slice(Math.max(0,C.index-160),C.index+360),T=(x.match(/(?:data-lang|lang|version)=["']([^"']+)/i)||[])[1]||x,k=(x.match(/(?:data-player|player|server|serveur)=["']([^"']+)/i)||[])[1]||"player";m(C[1],T,k)}}return g.length?(console.log("[Frenchstream] Detail page fallback: "+g.length+" player(s)"),g):null}catch(c){return console.warn("[Frenchstream] Detail page fallback failed for "+t+": "+c.message),null}})}'''
    output = text[:start] + replacement + text[end:]
    output = output.replace("os(G[0].newsId,t,i)", "os(G[0].newsId,t,i,G[0].href)")
    output = output.replace("os(m.newsId,t,i)", "os(m.newsId,t,i,m.href)")
    return output
