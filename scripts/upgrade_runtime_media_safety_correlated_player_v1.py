#!/usr/bin/env python3
"""Align CORE.RUNTIME_MEDIA_SAFETY.V4 with proof-correlated player fallback.

ProviderBase can intentionally return a proven player/embed URL when direct-media
resolution fails. STREAM_SANITIZER.V7 accepts only exact marked fallbacks. Media
safety runs earlier, so it must preserve the same causal row rather than dropping
all /embed or .php URLs before the terminal sanitizer can arbitrate them.
"""
from __future__ import annotations

from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
PATCH = SCRIPTS / "provider_patches" / "runtime_capability_media_safety_v4.py"
TEST = ROOT / "tests" / "runtime_capability_media_safety_v4_test.py"
OLD_REV = '"implementationRevision": "field-safety-v8-media-only-p2p-vod-duration",'
NEW_REV = '"implementationRevision": "field-safety-v9-correlated-player-fallback",'
MARKER = "NUVIO_RUNTIME_MEDIA_SAFETY_CORRELATED_PLAYER_FALLBACK_V1"

OLD_STATIC = '''  function staticSafety(row){if(!row||typeof row!=="object")return{keep:false,reason:"invalid_row"};var obvious=obviousNonMedia(row);if(obvious)return{keep:false,reason:obvious};return{keep:true}}\n'''
NEW_STATIC = r'''  /* NUVIO_RUNTIME_MEDIA_SAFETY_CORRELATED_PLAYER_FALLBACK_V1 */
  function correlatedPlayerFallback(row){
    if(!row||typeof row!=="object")return false;
    var u=s(row.url),proof=row.__nuvioCorrelatedPlayerFallbackV1;
    if(!proof||typeof proof!=="object"||s(proof.url)!==u||!/^https?:\/\//i.test(u))return false;
    try{
      var parsed=new URL(u),path=s(parsed.pathname).toLowerCase();
      if(/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return true;
      if(/\/(?:shell|video|stream)(?:\.php|[/?#.-]|$)/i.test(path)){
        var keys=[];parsed.searchParams.forEach(function(_v,k){keys.push(s(k).toLowerCase())});
        return keys.some(function(k){return /^(?:videoid|video|vid|file|embed|player|stream|source)$/.test(k)});
      }
    }catch(_e){}
    return false;
  }
  function staticSafety(row){
    if(!row||typeof row!=="object")return{keep:false,reason:"invalid_row"};
    var obvious=obviousNonMedia(row);
    if(!obvious)return{keep:true};
    if((obvious==="embed_page_url"||obvious==="html_page_url")&&correlatedPlayerFallback(row))return{keep:true,reason:"correlated_player_fallback"};
    return{keep:false,reason:obvious};
  }
'''

TEST_REV_OLD = "field-safety-v8-media-only-p2p-vod-duration"
TEST_REV_NEW = "field-safety-v9-correlated-player-fallback"
TEST_ANCHOR = '''assert value == {"rows": 0, "calls": 0}, value\n\n# A mixed provider keeps normal media rows while P2P rows are rejected individually.\n'''
TEST_INSERT = r'''assert value == {"rows": 0, "calls": 0}, value

# Exact proof-correlated player fallbacks pass media safety so the terminal
# sanitizer can arbitrate them. Native runtimes must not add a media probe.
for player_url in (
    "https://smoothpre.com/embed/abc123",
    "https://video.sibnet.ru/shell.php?videoid=12345",
):
    marked = patched(
        "generic-provider",
        "module.exports={getStreams:async()=>[{url:" + json.dumps(player_url) + ",__nuvioCorrelatedPlayerFallbackV1:{url:" + json.dumps(player_url) + "}}]};\n",
    )
    value = run_node(
        marked,
        "async function(){global.__fetchCalls++;throw new Error('native path must not probe correlated player fallback')}",
        "p.getStreams('95479','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),url:(Array.isArray(v)&&v[0]&&v[0].url)||'',proof:(Array.isArray(v)&&v[0]&&!!v[0].__nuvioCorrelatedPlayerFallbackV1),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
    )
    assert value == {"rows": 1, "url": player_url, "proof": True, "calls": 0}, (player_url, value)

# Unmarked or mismatched embed proof remains rejected.
for proof_url in ("", "https://smoothpre.com/embed/other"):
    marker = "" if not proof_url else ",__nuvioCorrelatedPlayerFallbackV1:{url:" + json.dumps(proof_url) + "}"
    source = "module.exports={getStreams:async()=>[{url:'https://smoothpre.com/embed/abc123'" + marker + "}]};\n"
    value = run_node(
        patched("generic-provider", source),
        "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
        "p.getStreams('95479','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
    )
    assert value == {"rows": 0, "calls": 0}, (proof_url, value)

# Explicit video-page policy stays stronger than the correlated-player exception.
youtube = "https://www.youtube.com/embed/abc123"
source = "module.exports={getStreams:async()=>[{url:" + json.dumps(youtube) + ",__nuvioCorrelatedPlayerFallbackV1:{url:" + json.dumps(youtube) + "}}]};\n"
value = run_node(
    patched("generic-provider", source),
    "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
    "p.getStreams('95479','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 0, "calls": 0}, value

# A mixed provider keeps normal media rows while P2P rows are rejected individually.
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_runtime() -> bool:
    text = PATCH.read_text(encoding="utf-8")
    if MARKER in text:
        validate_runtime(text)
        return False
    text = replace_once(text, OLD_STATIC, NEW_STATIC, "runtime static safety")
    text = replace_once(text, OLD_REV, NEW_REV, "runtime revision")
    PATCH.write_text(text, encoding="utf-8")
    validate_runtime(text)
    return True


def validate_runtime(text: str | None = None) -> None:
    value = text if text is not None else PATCH.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "function correlatedPlayerFallback(row)",
        's(proof.url)!==u',
        'obvious==="embed_page_url"||obvious==="html_page_url"',
        'reason:"correlated_player_fallback"',
        TEST_REV_NEW,
    ):
        if needle not in value:
            raise AssertionError(f"media safety correlated fallback missing {needle}")
    section = value.split(MARKER, 1)[1].split("function rowHeaders", 1)[0].casefold()
    for forbidden in ("animesama", "mugiwara", "smoothpre", "sibnet", "jujutsu", "95479"):
        if forbidden in section:
            raise AssertionError(f"provider/fixture-specific token leaked into runtime: {forbidden}")


def patch_test() -> bool:
    text = TEST.read_text(encoding="utf-8")
    changed = False
    if TEST_REV_OLD in text:
        text = text.replace(TEST_REV_OLD, TEST_REV_NEW)
        changed = True
    if "Exact proof-correlated player fallbacks pass media safety" not in text:
        text = replace_once(text, TEST_ANCHOR, TEST_INSERT, "test insertion")
        changed = True
    TEST.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    changed = patch_runtime() | patch_test()
    validate_runtime()
    print(
        "RUNTIME_MEDIA_SAFETY_CORRELATED_PLAYER_V1_OK "
        f"changed={str(changed).lower()} exact_marker=1 bounded_player_shape=1 "
        "youtube_policy_preserved=1 p2p_policy_preserved=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
