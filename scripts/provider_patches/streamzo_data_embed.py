#!/usr/bin/env python3
"""Teach the bundled StreamZo provider to read the current data-embed player."""
from __future__ import annotations


def apply(text: str, **_kwargs) -> str:
    marker = "NUVIO_STREAMZO_DATA_EMBED_V1"
    if marker in text:
        return text
    start = text.find("function k2(t){")
    end = text.find("function pE(t)", start)
    if start < 0 or end < 0:
        raise ValueError("StreamZo player extractor not found")
    replacement = r'''function k2(t){/* NUVIO_STREAMZO_DATA_EMBED_V1 */if(!t)return null;let a=t.match(/(?:data-embed|data-src|data-player|data-url)=["']([^"']+)["']/i);if(a)return a[1].replace(/&amp;/gi,"&");let n=t.match(/<iframe[^>]*id=["']video-frame["'][^>]*src=["']([^"']+)["']/i);if(n)return n[1];let i=t.match(/<iframe[^>]*src=["']([^"']*(?:\/embed\/|\/player\/)[^"']*)["']/i);if(i)return i[1];let s=t.match(/id=["']player["'][^>]*>[\s\S]*?<iframe[^>]*src=["']([^"']+)["']/i);return s?s[1]:null}'''
    return text[:start] + replacement + text[end:]
