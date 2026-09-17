#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/kehflix_anime_runtime_v1.py"
REGISTER = ROOT / "scripts/register_kehflix_anime_runtime_v1.py"

text = PATCH.read_text(encoding="utf-8")
for needle in (
    "NIAKVIO_KEHFLIX_ANIME_RUNTIME_V1",
    "NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1",
    'ctx.canonicalMediaType||ctx.mediaType||(obj&&(obj.mediaType||obj.type))||args[1]',
    'raw!=="anime"',
    'return null;',
    '/api/streams/episode?id=',
    'stream-gw',
    'txt(s.type).toLowerCase()==="iframe"',
    "_crawlDirectMedia([url],referer,depth)",
    "async function embeddedPlayerMedia(url,referer,source)",
    "(?:mp4|m3u8)",
    "absRef(raw,page)",
    "direct=await embeddedPlayerMedia(pr.url,titleUrl,pr.source)",
    "__nuvioCorrelatedPlayerFallbackV1={url:url}",
    '__niakvioProviderRuntimeResolverV1={provider:"kehflix",resolve:resolve}',
):
    assert needle in text, needle

runtime = text.split("WRAPPER = r'''", 1)[1].split("'''", 1)[0].casefold()
for forbidden in (
    "95479",
    "jujutsu",
    "4668025",
    "4667514",
    "blink-n3",
    "frederic-ntgm",
    "sibnet.ru",
    "t.me/",
):
    assert forbidden not in runtime, forbidden

spec = importlib.util.spec_from_file_location("register_kehflix", REGISTER)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fixture = {"provider_patches": {"kehflix": {"notes": []}}}
assert module.apply_document(fixture) is True
module.validate_document(fixture)
row = fixture["provider_patches"]["kehflix"]
assert module.LEGO in row["provider_lego_scripts"]
assert row["provider_lego_options"][module.LEGO]["targetStreams"] == 4
assert module.apply_document(fixture) is False

print("KEHFLIX_ANIME_RUNTIME_V1_TEST_OK semantic=anime transport=tv semantic_precedence=core_context embedded_media=generic native_delegate=movie,tv host_hardcodes=0")
