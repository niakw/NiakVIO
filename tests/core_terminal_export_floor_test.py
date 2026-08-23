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


def test_obfuscated_terminal_commonjs_export_is_bounded_by_core_tail() -> None:
    marker = r'''/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:abc */
;(function(g,c){g.__core=c})(globalThis,{});
'''
    text = "const value=1;function getStreams(){};module[_0x(0xc3)]={'getStreams':getStreams};\n" + marker
    floor = provider_export_floor(text)
    assert floor > 0
    assert text[floor:].lstrip().startswith("/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:")


def test_terminal_commonjs_fallback_remains_fail_closed() -> None:
    marker = r'''/* NUVIO_GLOBAL_STREAM_FACTS_V1:abc */
;(function(g){g.__facts=true})(globalThis);
'''
    assert provider_export_floor("module[_x]={foo:1};\n" + marker) == -1
    assert provider_export_floor(
        "module[_x]={'getStreams':getStreams};\nconst providerByte=1;\n" + marker
    ) == -1
    assert provider_export_floor(
        marker + "const providerByte=1;module[_x]={'getStreams':getStreams};\n"
    ) == -1


def test_exact_provider_bridge_remains_authoritative() -> None:
    text = "const value=1;module.exports=__provider;\nconst later=1;"
    assert provider_export_floor(text) == text.index("module.exports=__provider") + len("module.exports=__provider")


if __name__ == "__main__":
    test_obfuscated_terminal_commonjs_export_is_bounded_by_core_tail()
    test_terminal_commonjs_fallback_remains_fail_closed()
    test_exact_provider_bridge_remains_authoritative()
    print("Core terminal export floor regression tests passed")
