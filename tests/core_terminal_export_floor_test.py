#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core_rebuild_safety import SAFE_DOMAIN_FN, SAFE_EXPORT_FN  # noqa: E402


def provider_export_floor(text: str) -> int:
    namespace: dict[str, object] = {"re": re}
    exec(SAFE_EXPORT_FN, namespace)
    return namespace["_provider_export_floor"](text)  # type: ignore[index,operator]


def inject_domain_overrides(text: str, replacements: dict[str, str]) -> tuple[str, int]:
    namespace: dict[str, object] = {"re": re, "json": json, "Any": Any}
    exec(SAFE_DOMAIN_FN, namespace)
    return namespace["_inject_runtime_domain_overrides"](text, replacements)  # type: ignore[index,operator]


def runtime_safety_module():
    path = ROOT / "scripts" / "provider_patches" / "runtime_capability_media_safety_v4.py"
    spec = importlib.util.spec_from_file_location("nuvio_runtime_safety_separator_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def portfolio_module():
    path = ROOT / "tests" / "provider_export_floor_portfolio_test.py"
    spec = importlib.util.spec_from_file_location("nuvio_provider_export_floor_portfolio_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_shorthand_commonjs_exports_before_owned_wrappers_are_bounded() -> None:
    sanitizer = (
        "/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:fixture */\n"
        ";(function(g,c){})(globalThis,{});\n"
    )
    direct = "function getStreams(){};module.exports = { getStreams };\n" + sanitizer
    floor = provider_export_floor(direct)
    assert floor > direct.index("module.exports")
    assert direct[floor:].lstrip().startswith("/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:")

    branding = marker("NUVIO_GLOBAL_PROVIDER_BRANDING_V1")
    settings = (
        "function getStreams(){}function onSettings(){};"
        "module.exports={getStreams,onSettings};\n" + branding
    )
    floor = provider_export_floor(settings)
    assert floor > settings.index("module.exports")
    assert settings[floor:].lstrip().startswith("/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1:")

    # Merely using getStreams as another property's value is not an export key.
    assert provider_export_floor(
        "function getStreams(){};module.exports={other:getStreams};\n" + sanitizer
    ) == -1
    # The owned marker must be adjacent to the complete export statement.
    assert provider_export_floor(
        "function getStreams(){};module.exports={getStreams};\ndangerousCall();\n" + sanitizer
    ) == -1


def test_floated_core_marker_before_obfuscated_export_is_not_an_upper_bound() -> None:
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
    assert provider_export_floor(
        "module[_x]={'getStreams':getStreams}:dangerousCall();\n" + tail
    ) == -1
    assert provider_export_floor(
        "module[_x]={'getStreams':getStreams}:global[_g]=dangerousCall();\n" + tail
    ) == -1


def test_exact_provider_bridge_remains_authoritative() -> None:
    text = "const value=1;module.exports=__provider;\nconst later=1;"
    assert provider_export_floor(text) == text.index("module.exports=__provider") + len("module.exports=__provider")


def test_runtime_domain_markerless_bootstrap_reaches_one_copy() -> None:
    rules = {"old.example": "new.example"}
    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\n"
    first, _ = inject_domain_overrides(provider, rules)
    assert first.count("__nuvioDomainOverrideV1") == 1
    assert first.count("NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1") == 1

    markerless = first.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\n", "", 1)
    second, _ = inject_domain_overrides(markerless, rules)
    assert second.count("__nuvioDomainOverrideV1") == 1
    assert second.count("NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1") == 1
    assert second.endswith(provider)

    current = second
    for _ in range(6):
        current = current.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\n", "", 1)
        current, _ = inject_domain_overrides(current, rules)
        assert current.count("__nuvioDomainOverrideV1") == 1
        assert current.count("NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1") == 1


def test_runtime_domain_duplicate_bootstraps_collapse_fail_closed() -> None:
    rules = {"old.example": "new.example"}
    provider = "const providerByte=1;\n"
    canonical, _ = inject_domain_overrides(provider, rules)
    markerless = canonical.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\n", "", 1)
    duplicated = markerless.replace(provider, "", 1) + markerless
    collapsed, _ = inject_domain_overrides(duplicated, rules)
    assert collapsed.count("__nuvioDomainOverrideV1") == 1
    assert collapsed.count("NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1") == 1
    assert collapsed.endswith(provider)

    try:
        inject_domain_overrides('const reserved="__nuvioDomainOverrideV1";\n' + provider, rules)
    except ValueError as exc:
        assert "unowned runtime-domain reserved key" in str(exc)
    else:
        raise AssertionError("unowned runtime-domain reserved key must fail closed")


def test_runtime_safety_owned_wrapper_separator_is_canonical() -> None:
    module = runtime_safety_module()
    wrapper = (
        "/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:fixture */\n"
        ";(function(g,c){})(typeof globalThis!==\"undefined\"?globalThis:this,{});"
    )
    before = (
        "const before=1;\n\n\n"
        + wrapper
        + "\n\n\n/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1:fixture */\nconst after=1;"
    )
    stripped = module._strip_previous(before)
    assert stripped == (
        "const before=1;\n"
        "/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1:fixture */\nconst after=1;"
    )

    current = before
    for _ in range(6):
        base = module._strip_previous(current).rstrip()
        current = base + "\n" + wrapper
        assert "\n\n/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1" not in base
        assert current.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1


def test_real_provider_portfolio_export_boundaries() -> None:
    assert portfolio_module().main() == 0


if __name__ == "__main__":
    test_obfuscated_terminal_commonjs_export_is_bounded_by_core_tail()
    test_obfuscated_ternary_export_with_global_fallback_is_bounded()
    test_shorthand_commonjs_exports_before_owned_wrappers_are_bounded()
    test_floated_core_marker_before_obfuscated_export_is_not_an_upper_bound()
    test_terminal_commonjs_fallback_remains_fail_closed()
    test_exact_provider_bridge_remains_authoritative()
    test_runtime_domain_markerless_bootstrap_reaches_one_copy()
    test_runtime_domain_duplicate_bootstraps_collapse_fail_closed()
    test_runtime_safety_owned_wrapper_separator_is_canonical()
    test_real_provider_portfolio_export_boundaries()
    print("Core export-floor + domain/runtime fixed-point regressions passed across provider portfolio")
