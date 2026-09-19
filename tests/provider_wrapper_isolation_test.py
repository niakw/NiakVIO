#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_engine_normalizer import strip_foreign_provider_wrappers  # noqa: E402


def config() -> dict:
    return {
        "provider_patches": {
            "anime-sama": {"official_site": "https://anime-sama.store"},
            "foreign-provider": {"official_site": "https://foreign.example"},
        }
    }


def test_exact_foreign_wrapper_removed_without_provider_bytes() -> None:
    text = r'''/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */
;(function(g,rules){if(g){g.__bad="https://foreign.example/api";}})(typeof globalThis!=="undefined"?globalThis:this,[]);
var __provider=(()=>({getStreams:async()=>[{url:"https://foreign.example/media.m3u8"}]}))();
if(typeof module!=="undefined"&&module.exports){module.exports=__provider;}
if(__provider&&__provider.getStreams){globalThis.getStreams=__provider.getStreams;}
/* NUVIO_GLOBAL_STREAM_FACTS_V1:abc */
;(function(g,c){if(g){g.__facts=c;}})(typeof globalThis!=="undefined"?globalThis:this,{"ok":true});
'''
    output, removed = strip_foreign_provider_wrappers(text, "anime-sama", config())
    assert len(removed) == 1, removed
    assert removed[0]["marker"] == "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1", removed
    assert "g.__bad" not in output
    assert "var __provider=" in output
    assert "module.exports=__provider" in output
    assert "https://foreign.example/media.m3u8" in output
    assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in output


def test_foreign_url_in_provider_body_never_expands_wrapper_span() -> None:
    text = r'''/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */
;(function(g,rules){if(g){g.__safe=rules.length;}})(typeof globalThis!=="undefined"?globalThis:this,[]);
var __provider=(()=>({getStreams:async()=>[{url:"https://foreign.example/media.m3u8"}]}))();
if(typeof module!=="undefined"&&module.exports){module.exports=__provider;}
'''
    output, removed = strip_foreign_provider_wrappers(text, "anime-sama", config())
    assert removed == [], removed
    assert output == text
    assert "var __provider=" in output


def test_relocated_marker_can_never_consume_provider_bridge() -> None:
    # A minifier is allowed to preserve a comment while attaching it to another
    # AST node. If a NUVIO marker floats in front of provider-derived bytes, the
    # next IIFE terminator is not proof that those bytes belong to the wrapper.
    text = r'''/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */
var __provider=(()=>({getStreams:async()=>[{url:"https://foreign.example/media.m3u8"}]}))();
if(typeof module!=="undefined"&&module.exports){module.exports=__provider;}
if(__provider&&__provider.getStreams){globalThis.getStreams=__provider.getStreams;}
;(function(g,rules){if(g){g.__later=rules.length;}})(typeof globalThis!=="undefined"?globalThis:this,[]);
'''
    output, removed = strip_foreign_provider_wrappers(text, "anime-sama", config())
    assert removed == [], removed
    assert output == text
    assert "var __provider=" in output
    assert "module.exports=__provider" in output


def test_unknown_wrapper_shape_is_fail_closed() -> None:
    text = r'''/* NUVIO_UNKNOWN_WRAPPER_V1 */
customRuntimeBootstrap("https://foreign.example/api");
var __provider={getStreams:async()=>[]};
module.exports=__provider;
'''
    output, removed = strip_foreign_provider_wrappers(text, "anime-sama", config())
    assert removed == [], removed
    assert output == text


if __name__ == "__main__":
    test_exact_foreign_wrapper_removed_without_provider_bytes()
    test_foreign_url_in_provider_body_never_expands_wrapper_span()
    test_relocated_marker_can_never_consume_provider_bridge()
    test_unknown_wrapper_shape_is_fail_closed()
    print("provider wrapper isolation span tests passed")
