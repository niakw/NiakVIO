#!/usr/bin/env python3
"""V12 terminal sanitizer: widen bounded indirect-player multi-audio discovery.

V11 established the correct playback authority: when an indirect player exposes
both HLS child playlists and a richer HLS master, preserve the master so Nuvio's
production player can enumerate every audio rendition. V11 inspected only the
first six discovered candidates, while current ProviderBase may legitimately
surface a larger bounded player/source frontier.

V12 keeps V11's ranking, proof, headers and fail-closed semantics unchanged and
widens only that indirect candidate comparison to sixteen entries. It still
stops immediately after a proven multi-audio master and remains well below the
shared 40 playback-identity ceiling.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V11_PATH = ROOT / "stream_output_sanitizer_v11.py"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
MARKER = "NUVIO_STREAM_OUTPUT_MULTI_AUDIO_FRONTIER_V12"
MARKER_COMMENT = f"/* {MARKER} */"
FRONTIER_V11 = "probeLimit=Math.min(candidates.length,6)"
FRONTIER_V12 = "probeLimit=Math.min(candidates.length,16)"
ANCHOR = "  function coreMediaProof(stream,url){\n"


def _load_v11_module():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v11_for_v12", V11_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load stream_output_sanitizer_v11")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V11 = _load_v11_module()


def _restore_v11_source(text: str) -> str:
    source = str(text or "")
    if MARKER_COMMENT not in source:
        return source
    if source.count(MARKER_COMMENT) != 1:
        raise ValueError(f"stream sanitizer v12 marker count={source.count(MARKER_COMMENT)}")
    source = source.replace(MARKER_COMMENT + "\n", "", 1)
    if source.count(FRONTIER_V12) != 1:
        raise ValueError("stream sanitizer v12 existing frontier hook missing")
    return source.replace(FRONTIER_V12, FRONTIER_V11, 1)


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    source = _restore_v11_source(text)
    patched = V11.apply(source, options=options, **kwargs)
    if patched.count(FRONTIER_V11) != 1:
        raise ValueError(f"stream sanitizer v12 frontier hook count={patched.count(FRONTIER_V11)}")
    patched = patched.replace(FRONTIER_V11, FRONTIER_V12, 1)
    if patched.count(ANCHOR) != 1:
        raise ValueError(f"stream sanitizer v12 marker anchor count={patched.count(ANCHOR)}")
    patched = patched.replace(ANCHOR, f"  {MARKER_COMMENT}\n" + ANCHOR, 1)
    validate(patched)
    return patched


def validate(text: str) -> None:
    if text.count(MARKER) != 1:
        raise ValueError(f"stream sanitizer v12 marker count={text.count(MARKER)}")
    for needle in (
        FRONTIER_V12,
        "NUVIO_STREAM_OUTPUT_HLS_MASTER_PREFERENCE_V11",
        "__nuvioHlsMasterAudioCountV1",
        "candidateRank>=3",
        "stream.audioTracks=masterAudioTracks",
        "NUVIO_STREAM_OUTPUT_NETWORK_EVIDENCE_V10",
    ):
        if needle not in text:
            raise ValueError(f"stream sanitizer v12 missing {needle}")
    if FRONTIER_V11 in text:
        raise ValueError("stream sanitizer v12 retained six-candidate frontier")


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
