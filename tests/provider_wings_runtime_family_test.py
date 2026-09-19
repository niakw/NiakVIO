#!/usr/bin/env python3
"""Deterministic runtime test for the shared Wings/speedracelight v3 family."""
from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_wings_runtime_common import render_wings_runtime  # noqa: E402

K = [
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5,
    0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
    0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
    0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
]
GOLD = 0x9E3779B9
MASK = 0xFFFFFFFF


def u32(value: int) -> int:
    return value & MASK


def fmix(value: int) -> int:
    value = u32(value)
    value ^= value >> 16
    value = u32(value * 0x85EBCA6B)
    value ^= value >> 13
    value = u32(value * 0xC2B2AE35)
    value ^= value >> 16
    return u32(value)


def rot(value: int, count: int) -> int:
    value = u32(value)
    count &= 31
    if not count:
        return value
    return u32((value << count) | (value >> (32 - count)))


def fnv(text: str) -> int:
    value = 0x811C9DC5
    for char in text:
        value = u32((value ^ ord(char)) * 0x1000193)
    return fmix(value)


def keystream(seed: str, media_id: int, length: int) -> bytes:
    slots: dict[int, int] = {}
    acc = fmix(fnv(seed) ^ fmix(u32(media_id) ^ GOLD))
    for index in range(8):
        slot_index = acc % 61
        acc = rot(u32(acc + GOLD), 7 + (index & 7))
        slots[slot_index] = u32(acc ^ fmix(acc))
        acc = fmix(u32(acc + slot_index))
    acc = fmix(acc ^ 0xA5A5A5A5)

    output = bytearray()
    word_index = 0
    while len(output) < length:
        slot_index = acc % 61
        exists = slot_index in slots
        slot = slots.get(slot_index, 0)
        mix = u32(GOLD * (word_index + 1))
        word_index += 1
        b = u32(slot ^ mix)
        mask = MASK if exists else 0
        value = u32(u32(acc ^ b) | u32(acc & b & mask))
        value = u32(
            rot(u32(value + acc), slot_index & 31)
            ^ rot(acc, u32(slot_index * 7) & 31)
        )
        acc = fmix(u32(value + GOLD))
        slots[slot_index] = acc
        word = acc
        output.extend(
            (word & 0xFF, (word >> 8) & 0xFF, (word >> 16) & 0xFF, (word >> 24) & 0xFF)
        )
    return bytes(output[:length])


def encrypted_fixture(seed: str, media_id: int, payload: dict) -> str:
    plain = b"mvm1" + json.dumps(payload, separators=(",", ":")).encode("utf-8")
    stream = keystream(seed, media_id, len(plain))
    encrypted = bytes(left ^ right for left, right in zip(plain, stream))
    return base64.urlsafe_b64encode(encrypted).decode("ascii").rstrip("=")


def main() -> int:
    seed = "niakvio-wings-seed-v1"
    media_id = 157336
    expected_url = "https://media.example.test/master.m3u8"
    fixture = encrypted_fixture(
        seed,
        media_id,
        {
            "sources": [{"url": expected_url, "quality": "1080p", "language": "French"}],
            "subtitles": [{"url": "https://media.example.test/fr.vtt", "lang": "fr"}],
        },
    )
    wrapper = render_wings_runtime(
        marker="NIAKVIO_WINGS_RUNTIME_TEST",
        config={
            "apiBase": "https://api.speedracelight.test",
            "origin": "https://client.example.test",
            "referer": "https://client.example.test/",
            "userAgent": "NiakVIO-Test",
            "providerId": "wings-test",
            "providerName": "Wings Test",
            "installMarker": "__niakvioWingsTest",
            "endpoints": [{"label": "CDN", "path": "cdn/sources-with-title"}],
        },
    )
    node = f"""
globalThis.__nuvioMediaContext = {{
  tmdbId: {json.dumps(str(media_id))},
  canonicalMediaType: "movie",
  tmdbMetadata: {{
    title: "Interstellar",
    release_date: "2014-11-05",
    external_ids: {{imdb_id: "tt0816692"}}
  }}
}};
globalThis.getStreams = async function(){{ return []; }};
const seed = {json.dumps(seed)};
const encrypted = {json.dumps(fixture)};
globalThis.fetch = async function(url, options) {{
  if (String(url).includes("/seed?mediaId=")) {{
    return {{ok:true,status:200,url:String(url),json:async()=>({{seed}})}};
  }}
  if (String(url).includes("/cdn/sources-with-title?")) {{
    if (!String(url).includes("title=Interstellar") || !String(url).includes("tmdbId={media_id}")) {{
      return {{ok:false,status:400,url:String(url),text:async()=>""}};
    }}
    return {{ok:true,status:200,url:String(url),text:async()=>encrypted}};
  }}
  return {{ok:false,status:404,url:String(url),text:async()=>""}};
}};
{wrapper}
(async()=>{{
  const rows = await globalThis.getStreams(String({media_id}), "movie");
  process.stdout.write(JSON.stringify(rows));
}})().catch(error=>{{console.error(error);process.exit(1)}});
"""
    completed = subprocess.run(
        ["node", "-e", node],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    rows = json.loads(completed.stdout)
    assert len(rows) == 1, rows
    assert rows[0]["url"] == expected_url, rows
    assert rows[0]["quality"] == "1080p", rows
    assert rows[0]["language"] == "French", rows
    assert rows[0]["subtitles"][0]["lang"] == "fr", rows
    print("PROVIDER_WINGS_RUNTIME_OK seed_endpoint=1 encrypted_endpoint=1 streams=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
