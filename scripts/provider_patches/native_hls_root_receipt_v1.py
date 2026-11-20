#!/usr/bin/env python3
"""Candidate-only Core/ProviderBase HLS root receipt (V30).

The official TV trace 200 -> 403 can occur when a signed HLS root is fetched
successfully during player traversal, then fetched again by final validation.
For one *ephemeral*, Brain-selected candidate, preserve only the same in-memory
successful playlist body and existing playback headers; later shared HLS guards
must still validate child playlists/segments and clear private proof fields.

This module NEVER changes production bytes unless a separately authorized
workspace candidate explicitly applies it. It does not make any HTTP request.
"""
from __future__ import annotations

MARKER = "NIAKVIO_PROVIDER_NATIVE_HLS_ROOT_RECEIPT_V30"
OLD = """      if (_directMedia(responseUrl) || /(?:mpegurl|dash\\+xml|video\\/)/i.test(contentType)) {
        streams.push(..._streams([responseUrl], row.referer || referer || ""));
        continue;
      }
"""
NEW = """      /* NIAKVIO_PROVIDER_NATIVE_HLS_ROOT_RECEIPT_V30 */
      if (_directMedia(responseUrl) || /(?:mpegurl|dash\\+xml|video\\/)/i.test(contentType)) {
        const directRows = _streams([responseUrl], row.referer || referer || "");
        // A GET already succeeded: retain the bounded body locally rather
        // than force a second signed-root GET, which may return 403. Never
        // cache errors, arbitrary HTML, non-HLS media or a rewritten URL.
        const hlsRoot = /\\.m3u8(?:[?#]|$)/i.test(responseUrl) ||
          /(?:mpegurl|vnd\\.apple)/i.test(contentType);
        if (hlsRoot && typeof globalThis.__native_fetch === "function" &&\n            response && typeof response.text === "function") {
          let allowed = true;
          try {
            const size = Number(response.headers && response.headers.get
              ? response.headers.get("content-length") || 0 : 0);
            if (Number.isFinite(size) && size > 131072) allowed = false;
          } catch (_) {}
          if (allowed) {
            try {
              const body = String(await response.text()).replace(/^\\uFEFF/, "");
              if (body.length > 0 && body.length <= 131072 &&
                  /^#EXTM3U(?:\\r?\\n|$)/.test(body) &&
                  /#EXT-(?:X-STREAM-INF|X-TARGETDURATION|INF)\\b/.test(body)) {
                for (const stream of directRows) {
                  if (stream && stream.url === responseUrl) {
                    stream.__nuvioCoreMediaProofV1 = {url: stream.url, kind: "hls", body};
                  }
                }
              }
            } catch (_) {}
          }
        }
        streams.push(...directRows);
        continue;
      }
"""


def apply(base: bytes) -> bytes:
    """Compile one generic Core-owned change into isolated ProviderBase bytes."""
    source = base.decode("utf-8", errors="strict")
    if MARKER in source:
        raise ValueError("V30 receipt already installed; no production/duplicate mutation")
    if source.count(OLD) != 1:
        raise ValueError("ProviderBase V30 direct-media anchor drift")
    if "function _crawlDirectMedia(" not in source:
        raise ValueError("ProviderBase crawler missing")
    return source.replace(OLD, NEW, 1).encode("utf-8")


def validate(source: bytes) -> None:
    text = source.decode("utf-8", errors="strict")
    if text.count(MARKER) != 1 or OLD in text:
        raise ValueError("candidate V30 not fully materialized")
    for guard in (
        "body.length <= 131072",
        "stream.url === responseUrl",
        "stream.__nuvioCoreMediaProofV1",
        "kind: \"hls\"",
    ):
        if guard not in text:
            raise ValueError(f"candidate V30 missing {guard}")
