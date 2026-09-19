#!/usr/bin/env python3
"""One-shot source patch for terminal stream labels and abort-ignorant native fetches.

This file is intentionally idempotent. It patches the canonical sources only;
reapply_published_overrides.py subsequently rematerializes all public providers.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text:
        print(f"{label}: already applied")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: anchor count={count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: applied")


replace_once(
    "engine_v2/src/stream-presentation.mjs",
    '''  return {\n    ...stream,\n    title: `${providerName}${facts.quality ? ` - ${qualityLabel(facts.quality)}` : ""}`,\n    name: providerName,\n''',
    '''  const streamTitle = `${providerName}${facts.quality ? ` - ${qualityLabel(facts.quality)}` : ""}`;\n  return {\n    ...stream,\n    title: streamTitle,\n    name: streamTitle,\n''',
    "engine title/name mirror",
)

replace_once(
    "engine_v2/src/stream-presentation.mjs",
    '''function providerDisplayName(stream, provider) {\n  const raw = clean(stream.name);\n''',
    '''function cleanProviderDisplayName(value) {\n  const raw = clean(value);\n  if (!raw) return null;\n  return clean(raw.replace(\n    /\\s*(?:[-|•:])\\s*(?:unknown|inconnu(?:e)?|n\\/?a|na|none|null|undefined|unknown\\s+(?:quality|language)|qualit(?:e|é)\\s+inconnue|langue\\s+inconnue)\\s*$/i,\n    "",\n  ));\n}\n\nfunction providerDisplayName(stream, provider) {\n  const raw = cleanProviderDisplayName(stream.name ?? stream.title);\n''',
    "engine terminal placeholder cleanup",
)

media_path = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
media = media_path.read_text(encoding="utf-8")
if '"revision": "tmdb-data-contract-launch-gate-v29-native-abort-race",' not in media:
    old = '"revision": "tmdb-data-contract-launch-gate-v28-dual-id-input",'
    if media.count(old) != 1:
        raise SystemExit(f"media revision anchor count={media.count(old)}")
    media = media.replace(old, '"revision": "tmdb-data-contract-launch-gate-v29-native-abort-race",', 1)

abort_helper = '''function abortController(controller){try{if(controller&&typeof controller.abort==="function")controller.abort()}catch(_){}}\n'''
abort_insert = '''function abortController(controller){try{if(controller&&typeof controller.abort==="function")controller.abort()}catch(_){}}\nfunction requestAbortPromise(controller,requestToken){\n  return new Promise(function(_resolve,reject){\n    try{\n      var signal=controller&&controller.signal;\n      if(!signal)return;\n      var fail=function(){reject(tokenOwns(requestToken)?providerTimeoutError():providerStaleError())};\n      if(signal.aborted){fail();return}\n      if(typeof signal.addEventListener==="function")signal.addEventListener("abort",fail,{once:true});\n    }catch(_){}\n  });\n}\n'''
if "function requestAbortPromise(controller,requestToken)" not in media:
    if media.count(abort_helper) != 1:
        raise SystemExit(f"abort helper anchor count={media.count(abort_helper)}")
    media = media.replace(abort_helper, abort_insert, 1)

old_race = '''    var value;\n    try{\n      value=(typeof setTimeout==="function"&&remaining>0)\n        ? await Promise.race([base.apply(this,args),timeoutPromise])\n        : await base.apply(this,args);\n    }finally{'''
new_race = '''    var value,abortPromise=requestAbortPromise(requestController,requestToken);\n    try{\n      value=(typeof setTimeout==="function"&&remaining>0)\n        ? await Promise.race([base.apply(this,args),timeoutPromise,abortPromise])\n        : await Promise.race([base.apply(this,args),abortPromise]);\n    }finally{'''
if new_race not in media:
    if media.count(old_race) != 1:
        raise SystemExit(f"native abort race anchor count={media.count(old_race)}")
    media = media.replace(old_race, new_race, 1)

media_path.write_text(media, encoding="utf-8")
print("media type runtime V29: applied")

# Permanent engine regression: placeholders disappear, real qualities remain.
test_path = ROOT / "engine_v2/tests/stream-presentation.test.mjs"
test = test_path.read_text(encoding="utf-8")
anchor = 'assert.equal(normalizeSourceType("some provider label"), null);\n\n'
block = '''const kehflixProvider = { id: "kehflix", name: "Kehflix", languages: ["fr"] };\nfor (const placeholder of ["Inconnue", "Unknown", "N/A"]) {\n  const row = presentStreamCandidate({\n    name: `Kehflix - ${placeholder}`,\n    title: `Kehflix - ${placeholder}`,\n    url: "https://media.example/master.m3u8",\n    quality: placeholder,\n  }, { title: "Interstellar", year: 2014, mediaType: "movie" }, kehflixProvider);\n  assert.equal(row.title, "Kehflix", row.title);\n  assert.equal(row.name, "Kehflix", row.name);\n  assert.equal(row.quality, null, JSON.stringify(row));\n}\nconst kehflix1080 = presentStreamCandidate({ name: "Kehflix", url: "https://media.example/a.mp4", quality: "1080p" }, { mediaType: "movie" }, kehflixProvider);\nassert.equal(kehflix1080.title, "Kehflix - 1080p");\nassert.equal(kehflix1080.name, "Kehflix - 1080p");\nconst kehflix4k = presentStreamCandidate({ name: "Kehflix", url: "https://media.example/a.mp4", quality: "2160p" }, { mediaType: "movie" }, kehflixProvider);\nassert.equal(kehflix4k.title, "Kehflix - 4K");\nassert.equal(kehflix4k.name, "Kehflix - 4K");\n\n'''
if "const kehflixProvider =" not in test:
    if test.count(anchor) != 1:
        raise SystemExit(f"engine test anchor count={test.count(anchor)}")
    test = test.replace(anchor, anchor + block, 1)
    test_path.write_text(test, encoding="utf-8")
    print("engine label regression: added")
else:
    print("engine label regression: already present")

print("one-shot V29 source patch complete")
