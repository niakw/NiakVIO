#!/usr/bin/env python3
"""V11 terminal sanitizer: prefer HLS masters over child playlists during player recovery.

Nuvio's plugin ABI transports the selected media URL, headers and coarse language,
not NiakVIO's rich audioTracks metadata. The player therefore discovers selectable
audio tracks from the actual media resource. When an HTML/JSON player exposes both
one child media playlist and its richer HLS master, selecting the first playable
candidate can silently collapse a multi-audio stream to one audio language.

V11 keeps V10's fail-closed terminal proof but replaces only the bounded indirect
candidate choice. It inspects at most six already-discovered candidates, preserves
the first playable fallback, prefers an HLS master over a child playlist, and
prefers a master carrying multiple EXT-X-MEDIA AUDIO renditions. It also records
bounded host-only player/terminal provenance for the final branding layer.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V10_PATH = ROOT / "stream_output_sanitizer_v10.py"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
MARKER = "NUVIO_STREAM_OUTPUT_HLS_MASTER_PREFERENCE_V11"
MARKER_COMMENT = f"/* {MARKER} */"

OLD_HLS = r'''        var hls=normalizeHlsText(text,finalUrl);
        if(!hls)return false;
        recoverQuality(stream,hls.text,finalUrl);
        if(hls.repaired){
          stream.url=repairedHlsUrl(hls.text);
          if(!stream.type)stream.type="hls";
          if(!stream.mimeType)stream.mimeType="application/vnd.apple.mpegurl";
          stream.isDirect=true;
        }else markDirect(stream,finalUrl);
        syncPlaybackHeaders(stream);
        return true;'''

NEW_HLS = r'''        var hls=normalizeHlsText(text,finalUrl);
        if(!hls)return false;
        recoverQuality(stream,hls.text,finalUrl);
        var master=/#EXT-X-STREAM-INF\s*:/i.test(hls.text),audioCount=0,am,reAudio=/#EXT-X-MEDIA\s*:[^\r\n]*TYPE\s*=\s*["']?AUDIO["']?[^\r\n]*/gi;
        while((am=reAudio.exec(hls.text))!==null)audioCount++;
        if(depth>0){
          stream.__nuvioHlsMasterV1=master;
          stream.__nuvioHlsMasterAudioCountV1=master?audioCount:0;
        }
        if(depth>0&&referer)try{stream.playerHost=hostOf(referer)}catch(_e){}
        try{stream.terminalHost=hostOf(finalUrl)}catch(_e){}
        if(hls.repaired){
          stream.url=repairedHlsUrl(hls.text);
          if(!stream.type)stream.type="hls";
          if(!stream.mimeType)stream.mimeType="application/vnd.apple.mpegurl";
          stream.isDirect=true;
        }else markDirect(stream,finalUrl);
        syncPlaybackHeaders(stream);
        return true;'''

OLD_CANDIDATES = r'''        if(depth<2&&candidates.length){
          ensurePlaybackHeaders(stream,finalUrl);
          for(var candidateIndex=0;candidateIndex<candidates.length;candidateIndex++){
            if(await probeResolved(stream,candidates[candidateIndex],depth+1,finalUrl))return true;
          }
        }
        return false;'''

NEW_CANDIDATES = r'''        if(depth<2&&candidates.length){
          ensurePlaybackHeaders(stream,finalUrl);
          var bestPlayable=null,bestRank=-1,probeLimit=Math.min(candidates.length,6);
          for(var candidateIndex=0;candidateIndex<probeLimit;candidateIndex++){
            var candidateStream=Object.assign({},stream);
            if(stream&&stream.headers&&typeof stream.headers==="object")candidateStream.headers=Object.assign({},stream.headers);
            if(stream&&stream.behaviorHints&&typeof stream.behaviorHints==="object")candidateStream.behaviorHints=Object.assign({},stream.behaviorHints);
            try{candidateStream.playerHost=hostOf(finalUrl)}catch(_e){}
            if(await probeResolved(candidateStream,candidates[candidateIndex],depth+1,finalUrl)){
              try{candidateStream.terminalHost=hostOf(candidateStream.url)}catch(_e){}
              var candidateRank=Number(candidateStream.__nuvioHlsMasterAudioCountV1||0)>1?3:(candidateStream.__nuvioHlsMasterV1?2:1);
              if(candidateRank>bestRank){bestPlayable=candidateStream;bestRank=candidateRank}
              if(candidateRank>=3)break;
            }
          }
          if(bestPlayable){
            Object.keys(bestPlayable).forEach(function(k){stream[k]=bestPlayable[k]});
            try{delete stream.__nuvioHlsMasterV1}catch(_e){}
            try{delete stream.__nuvioHlsMasterAudioCountV1}catch(_e){}
            return true;
          }
        }
        return false;'''

ANCHOR = "  function validHls(text){\n"


def _load_v10_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v10_for_v11", V10_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V10_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V10_APPLY = _load_v10_apply()


def _restore_v10_source(text: str) -> str:
    source = str(text or "")
    if MARKER_COMMENT not in source:
        return source
    if source.count(MARKER_COMMENT) != 1:
        raise ValueError(f"stream sanitizer v11 marker count={source.count(MARKER_COMMENT)}")
    source = source.replace(MARKER_COMMENT + "\n", "", 1)
    if NEW_HLS not in source or NEW_CANDIDATES not in source:
        raise ValueError("stream sanitizer v11 existing hooks missing")
    source = source.replace(NEW_HLS, OLD_HLS, 1)
    source = source.replace(NEW_CANDIDATES, OLD_CANDIDATES, 1)
    return source


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    source = _restore_v10_source(text)
    patched = V10_APPLY(source, options=options, **kwargs)
    if patched.count(OLD_HLS) != 1:
        raise ValueError(f"stream sanitizer v11 HLS hook count={patched.count(OLD_HLS)}")
    if patched.count(OLD_CANDIDATES) != 1:
        raise ValueError(f"stream sanitizer v11 candidate hook count={patched.count(OLD_CANDIDATES)}")
    patched = patched.replace(OLD_HLS, NEW_HLS, 1)
    patched = patched.replace(OLD_CANDIDATES, NEW_CANDIDATES, 1)
    if patched.count(ANCHOR) != 1:
        raise ValueError(f"stream sanitizer v11 marker anchor count={patched.count(ANCHOR)}")
    patched = patched.replace(ANCHOR, f"  {MARKER_COMMENT}\n" + ANCHOR, 1)
    validate(patched)
    return patched


def validate(text: str) -> None:
    if text.count(MARKER) != 1:
        raise ValueError(f"stream sanitizer v11 marker count={text.count(MARKER)}")
    for needle in (
        "probeLimit=Math.min(candidates.length,6)",
        "__nuvioHlsMasterV1",
        "__nuvioHlsMasterAudioCountV1",
        "candidateRank>=3",
        "playerHost=hostOf(referer)",
        "terminalHost=hostOf(finalUrl)",
        "NUVIO_STREAM_OUTPUT_NETWORK_EVIDENCE_V10",
    ):
        if needle not in text:
            raise ValueError(f"stream sanitizer v11 missing {needle}")
    if OLD_CANDIDATES in text:
        raise ValueError("stream sanitizer v11 retained first-playable candidate exit")


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
