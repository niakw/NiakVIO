#!/usr/bin/env python3
"""V10 terminal sanitizer: preserve bounded network evidence for Stream Score.

V8 remains the strict media-validity authority. V10 does not weaken any verdict.
It records only evidence already produced by the terminal probe:
- elapsed terminal-probe time;
- sampled byte count;
- sampled Mbps only for direct binary media where the byte sample is meaningful;
- success and sample kind.

Manifest byte throughput is deliberately NOT called playback Mbps. HLS/DASH
manifest probes therefore expose latency/success evidence only. The downstream
CORE.STREAM_SCORE.V1 block consumes and removes this private evidence before rows
reach the client.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V8_PATH = ROOT / "stream_output_sanitizer_v8.py"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
MARKER = "NUVIO_STREAM_OUTPUT_NETWORK_EVIDENCE_V10"
MARKER_COMMENT = f"/* {MARKER} */"

BYTES_OLD = "var bytes=await prefixBytes(response,controller),text=ascii(bytes);"
BYTES_NEW = (
    "var bytes=await prefixBytes(response,controller),text=ascii(bytes);"
    "try{if(stream&&typeof stream===\"object\")stream.__nuvioProbeBytesV1=Number(bytes&&bytes.length||0)||0}catch(_e){}"
)
VERDICT_OLD = "var verdict=await probe(item.stream,item.url);\n        return verdict===true?clearPrivateProofs(item.stream):null;"
LEGACY_VERDICT_NEW = """var probeStarted=(typeof Date!==\"undefined\"&&Date.now)?Date.now():0;
        var verdict=await probe(item.stream,item.url);
        var probeEnded=(typeof Date!==\"undefined\"&&Date.now)?Date.now():probeStarted;
        if(verdict===true&&item.stream&&typeof item.stream===\"object\"){
          try{
            var elapsed=Math.max(1,Number(probeEnded-probeStarted)||1);
            var sampleBytes=Math.max(0,Number(item.stream.__nuvioProbeBytesV1||0)||0);
            var sampledUrl=String(item.stream.url||item.url||\"\");
            var hint=String(item.stream.type||item.stream.format||item.stream.mimeType||item.stream.contentType||\"\").toLowerCase();
            var manifest=/(?:\\.m3u8?|\\.mpd)(?:[?#]|$)/i.test(sampledUrl)||/(?:hls|mpegurl|dash)/i.test(hint);
            var sampleMbps=!manifest&&sampleBytes>0?sampleBytes*8/elapsed/1000:null;
            item.stream.__nuvioStreamNetworkEvidenceV1={
              success:true,
              latencyMs:elapsed,
              sampleBytes:sampleBytes,
              sampleMbps:sampleMbps,
              sampleConfidence:sampleMbps!=null?0.55:0,
              sampleKind:manifest?\"manifest\":\"direct-media-prefix\",
              source:\"terminal-media-probe-v10\"
            };
          }catch(_e){}
        }
        try{if(item.stream&&typeof item.stream===\"object\")delete item.stream.__nuvioProbeBytesV1}catch(_e){}
        return verdict===true?clearPrivateProofs(item.stream):null;"""
VERDICT_NEW = """var probeStarted=(typeof Date!==\"undefined\"&&Date.now)?Date.now():0;
        var verdict=await probe(item.stream,item.url);
        var probeEnded=(typeof Date!==\"undefined\"&&Date.now)?Date.now():probeStarted;
        if(verdict===true&&item.stream&&typeof item.stream===\"object\"){
          try{
            var elapsed=Math.max(1,Number(probeEnded-probeStarted)||1);
            var sampleBytes=Math.max(0,Number(item.stream.__nuvioProbeBytesV1||0)||0);
            var sampledUrl=String(item.stream.url||item.url||\"\");
            var hint=String(item.stream.type||item.stream.format||item.stream.mimeType||item.stream.contentType||\"\").toLowerCase();
            var manifest=/(?:\\.m3u8?|\\.mpd)(?:[?#]|$)/i.test(sampledUrl)||/(?:hls|mpegurl|dash)/i.test(hint);
            var sampleMbps=!manifest&&sampleBytes>0?sampleBytes*8/elapsed/1000:null;
            var prior=item.stream.__nuvioStreamNetworkEvidenceV1&&typeof item.stream.__nuvioStreamNetworkEvidenceV1===\"object\"?item.stream.__nuvioStreamNetworkEvidenceV1:null;
            var evidence={
              success:true,
              latencyMs:elapsed,
              sampleBytes:sampleBytes,
              sampleMbps:sampleMbps,
              sampleConfidence:sampleMbps!=null?0.55:0,
              sampleKind:manifest?\"manifest\":\"direct-media-prefix\",
              source:\"terminal-media-probe-v10\",
              terminalProbeLatencyMs:elapsed
            };
            if(prior&&prior.success===true)evidence=Object.assign({},evidence,prior,{success:true,terminalProbeLatencyMs:elapsed});
            item.stream.__nuvioStreamNetworkEvidenceV1=evidence;
          }catch(_e){}
        }
        try{if(item.stream&&typeof item.stream===\"object\")delete item.stream.__nuvioProbeBytesV1}catch(_e){}
        return verdict===true?clearPrivateProofs(item.stream):null;"""
ANCHOR = "  function clearPrivateProofs(stream){\n"


def _load_v8_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v8_for_v10", V8_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V8_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V8_APPLY = _load_v8_apply()


def _restore_v8_source(text: str) -> str:
    source = str(text or "")
    if MARKER_COMMENT in source:
        if source.count(MARKER_COMMENT) != 1:
            raise ValueError(f"stream sanitizer v10 marker count={source.count(MARKER_COMMENT)}")
        source = source.replace(MARKER_COMMENT + "\n", "", 1)
        if BYTES_NEW not in source:
            raise ValueError("stream sanitizer v10 existing byte evidence hook missing")
        source = source.replace(BYTES_NEW, BYTES_OLD, 1)
        if VERDICT_NEW in source:
            source = source.replace(VERDICT_NEW, VERDICT_OLD, 1)
        elif LEGACY_VERDICT_NEW in source:
            source = source.replace(LEGACY_VERDICT_NEW, VERDICT_OLD, 1)
        else:
            raise ValueError("stream sanitizer v10 existing verdict evidence hook missing")
    return source


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    source = _restore_v8_source(text)
    patched = V8_APPLY(source, options=options, **kwargs)
    if patched.count(BYTES_OLD) != 1:
        raise ValueError(f"stream sanitizer v10 byte hook count={patched.count(BYTES_OLD)}")
    if patched.count(VERDICT_OLD) != 1:
        raise ValueError(f"stream sanitizer v10 verdict hook count={patched.count(VERDICT_OLD)}")
    patched = patched.replace(BYTES_OLD, BYTES_NEW, 1)
    patched = patched.replace(VERDICT_OLD, VERDICT_NEW, 1)
    if patched.count(ANCHOR) != 1:
        raise ValueError(f"stream sanitizer v10 marker anchor count={patched.count(ANCHOR)}")
    patched = patched.replace(ANCHOR, f"  {MARKER_COMMENT}\n" + ANCHOR, 1)
    validate(patched)
    return patched


def validate(text: str) -> None:
    if text.count(MARKER) != 1:
        raise ValueError(f"stream sanitizer v10 marker count={text.count(MARKER)}")
    for needle in (
        "__nuvioStreamNetworkEvidenceV1",
        "sampleKind:manifest?\"manifest\":\"direct-media-prefix\"",
        "sampleConfidence:sampleMbps!=null?0.55:0",
        "source:\"terminal-media-probe-v10\"",
        "terminalProbeLatencyMs",
        "Object.assign({},evidence,prior",
        "return verdict===true?clearPrivateProofs(item.stream):null;",
        "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8",
    ):
        if needle not in text:
            raise ValueError(f"stream sanitizer v10 missing {needle}")
    if "__nuvioProbeBytesV1" not in text:
        raise ValueError("stream sanitizer v10 lost bounded byte evidence")
    section = text.split(MARKER_COMMENT, 1)[1].split("function clearPrivateProofs", 1)[0].casefold()
    for forbidden in ("kehflix", "purstream", "animesama", "moviebox", "mallumv"):
        if forbidden in section:
            raise ValueError(f"provider-specific token leaked into V10 policy: {forbidden}")


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
