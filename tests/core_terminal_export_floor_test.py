#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core_rebuild_safety import SAFE_EXPORT_FN  # noqa: E402


def provider_export_floor(text: str) -> int:
    namespace: dict[str, object] = {"re": re}
    exec(SAFE_EXPORT_FN, namespace)
    return namespace["_provider_export_floor"](text)  # type: ignore[index,operator]


def marker(name: str = "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2") -> str:
    return f'''/* {name}:abc */
;(function(g,c){{g.__core=c}})(globalThis,{{}});
'''


def test_obfuscated_terminal_commonjs_export_is_bounded_by_core_tail() -> None:
    tail = marker()
    text = "const value=1;function getStreams(){};module[_0x(0xc3)]={'getStreams':getStreams};\n" + tail
    floor = provider_export_floor(text)
    assert floor > 0
    assert text[floor:].lstrip().startswith("/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:")


def test_obfuscated_ternary_export_with_global_fallback_is_bounded() -> None:
    tail = marker("NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1")
    animepahe = (
        "function getStreams(){}function onSettings(){};"
        "typeof module!=='undefined'&&module[_x]?"
        "module[_x]={'getStreams':getStreams,'onSettings':onSettings}:"
        "(global[_g]=getStreams,global[_s]=onSettings);\n" + tail
    )
    floor = provider_export_floor(animepahe)
    assert floor > 0
    assert animepahe[floor:].lstrip().startswith("/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:")

    movieshunt = (
        "function getStreams(){};"
        "typeof module!=='undefined'&&module[_x]?"
        "module['exports']={'getStreams':getStreams}:global['getStreams']=getStreams;\n"
        + marker("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1")
    )
    floor = provider_export_floor(movieshunt)
    assert floor > 0
    assert movieshunt[floor:].lstrip().startswith("/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:")


def test_floated_core_marker_before_obfuscated_export_is_not_an_upper_bound() -> None:
    # Terser may preserve a Core comment while attaching it before the terminal
    # provider export. That stale comment must not hide an otherwise proven
    # obfuscated CommonJS boundary when another owned Core marker follows it.
    floated = marker("NUVIO_GLOBAL_STREAM_FACTS_V1")
    trailing = marker("NUVIO_GLOBAL_STREAM_PRESENTATION_V1")
    text = (
        "const providerByte=1;\n"
        + floated
        + "function getStreams(){};"
        + "module[_decoder(0xc3)]={'getStreams':getStreams};\n"
        + trailing
    )
    floor = provider_export_floor(text)
    assert floor > text.index("module[_decoder")
    assert text[floor:].lstrip().startswith("/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:")

    ternary = (
        "const providerByte=1;\n"
        + marker("NUVIO_GLOBAL_CORE_START_BOUNDARY_V1")
        + "function getStreams(){}function onSettings(){};"
        + "typeof module!=='undefined'&&module[_x]?"
        + "module[_x]={'getStreams':getStreams,'onSettings':onSettings}:"
        + "(global[_g]=getStreams,global[_s]=onSettings);\n"
        + marker("NUVIO_HLS_RUNTIME_INTEGRITY_V1")
    )
    floor = provider_export_floor(ternary)
    assert floor > ternary.index("module[_x]={'getStreams'")
    assert ternary[floor:].lstrip().startswith("/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:")


def test_terminal_commonjs_fallback_remains_fail_closed() -> None:
    tail = marker("NUVIO_GLOBAL_STREAM_FACTS_V1")
    assert provider_export_floor("module[_x]={foo:1};\n" + tail) == -1
    assert provider_export_floor(
        "module[_x]={'getStreams':getStreams};\nconst providerByte=1;\n" + tail
    ) == -1
    assert provider_export_floor(
        tail + "const providerByte=1;module[_x]={'getStreams':getStreams};\n"
    ) == -1
    # A ternary suffix may only expose provider identifiers through a known global
    # bridge. Arbitrary execution after the object export must never be swallowed.
    assert provider_export_floor(
        "module[_x]={'getStreams':getStreams}:dangerousCall();\n" + tail
    ) == -1
    assert provider_export_floor(
        "module[_x]={'getStreams':getStreams}:global[_g]=dangerousCall();\n" + tail
    ) == -1


def test_exact_provider_bridge_remains_authoritative() -> None:
    text = "const value=1;module.exports=__provider;\nconst later=1;"
    assert provider_export_floor(text) == text.index("module.exports=__provider") + len("module.exports=__provider")


if __name__ == "__main__":
    test_obfuscated_terminal_commonjs_export_is_bounded_by_core_tail()
    test_obfuscated_ternary_export_with_global_fallback_is_bounded()
    test_floated_core_marker_before_obfuscated_export_is_not_an_upper_bound()
    test_terminal_commonjs_fallback_remains_fail_closed()
    test_exact_provider_bridge_remains_authoritative()
    print("Core terminal/ternary/floated-marker export floor regression tests passed")
