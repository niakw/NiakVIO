#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core_rebuild_safety import SAFE_EXPORT_FN  # noqa: E402

CORE_MARKERS = (
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "NUVIO_STREAM_OUTPUT_SANITIZER_V",
    "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",
    "NUVIO_DESKTOP_RUNTIME_COMPAT_V1",
    "NUVIO_TV_DIRECT_MEDIA_V2",
    "NUVIO_ANIMEZEY_STREAM_HOST_V1",
    "NUVIO_TV_PLAYABLE_FIRST_V1",
    "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
    "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
    "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
    "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
    "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
    "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
)


def provider_export_floor(text: str) -> int:
    namespace: dict[str, object] = {"re": re}
    exec(SAFE_EXPORT_FN, namespace)
    return namespace["_provider_export_floor"](text)  # type: ignore[index,operator]


def _regressions() -> None:
    core = "/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:fixture */\n;(function(){})();\n"
    kurage = (
        "function getStreams(){};"
        "module['exports']={'getStreams':getStreams};"
        "function _decoder(){const table=['a'];_decoder=function(){return table;};return _decoder();}\n"
        + core
    )
    floor = provider_export_floor(kurage)
    assert floor > kurage.index("function _decoder")
    assert kurage[floor:].lstrip().startswith("/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:")

    assert provider_export_floor(
        "module.exports={getStreams};dangerousCall();\n" + core
    ) == -1
    assert provider_export_floor(
        "module.exports={getStreams};const decoder=function(){};\n" + core
    ) == -1

    tv = "/* NUVIO_TV_PLAYABLE_FIRST_V1 */\n;(function(){})();\n"
    vegamovies = (
        "function getStreams(){};"
        "typeof module!=='undefined'&&module.exports?"
        "module.exports={'getStreams':getStreams}:global.getStreams=getStreams;\n"
        + tv
    )
    floor = provider_export_floor(vegamovies)
    assert floor > vegamovies.index("module.exports")
    assert vegamovies[floor:].lstrip().startswith("/* NUVIO_TV_PLAYABLE_FIRST_V1")

    wrapped = (
        "function getStreams(){};"
        "typeof module!=='undefined'&&module.exports&&("
        "module['exports']={'getStreams':getStreams,'scrape':scrape});\n" + core
    )
    floor = provider_export_floor(wrapped)
    assert floor > wrapped.index("module['exports']")
    assert wrapped[floor:].lstrip().startswith("/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:")
    assert provider_export_floor(
        "module.exports={getStreams});dangerousCall();\n" + core
    ) == -1

    braced = (
        "function getStreams(){};"
        "if(typeof module!=='undefined'&&module.exports){"
        "module.exports={getStreams};}else{global.getStreams=getStreams;}\n" + core
    )
    floor = provider_export_floor(braced)
    assert floor > braced.index("module.exports")
    assert braced[floor:].lstrip().startswith("/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:")

    cinevibe = (
        "function getStreams(){};"
        "if(typeof module!=='undefined'&&module.exports){module.exports={getStreams};}else{"
        "// React Native compatibility\n"
        "global.CinevibeScraperModule={getStreams};}\n" + core
    )
    floor = provider_export_floor(cinevibe)
    assert floor > cinevibe.index("module.exports")

    moonflix = (
        "function mGetStreams(){};function mOnSettings(){};"
        "if(x)module.exports={'getStreams':mGetStreams,'onSettings':mOnSettings};"
        "else typeof global!=='undefined'&&(global.getStreams=mGetStreams,global.onSettings=mOnSettings);\n"
        + core
    )
    floor = provider_export_floor(moonflix)
    assert floor > moonflix.index("module.exports")

    animekai = (
        "function getStreams(){};x?module['exports']={'getStreams':getStreams}:"
        "global['AnimeKai']={'getStreams':getStreams};\n" + core
    )
    floor = provider_export_floor(animekai)
    assert floor > animekai.index("module['exports']")

    # DooFlix has no CommonJS export. Its real obfuscated signature contains a
    # nested call in a default argument; balanced signature parsing must retain it.
    dooflix = (
        "const __async=(a,b,c)=>Promise.resolve();"
        "function helper(){};"
        "function getStreams(id,type=_decode(0x130),season=null,episode=null){return __async(this,null,function*(){return [];});}\n"
        + core
    )
    floor = provider_export_floor(dooflix)
    assert floor > dooflix.index("function getStreams")
    assert dooflix[floor:].lstrip().startswith("/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:")
    assert provider_export_floor(
        "function getStreams(id,type=_decode(0x130)){return [];}dangerousCall();\n" + core
    ) == -1

    for unsafe in (
        "if(x){module.exports={getStreams};}else{global.getStreams=dangerousCall();}\n",
        "if(x){module.exports={getStreams};}else{global.box={getStreams:dangerousCall()};}\n",
        "x?module.exports={getStreams}:global.box={other:getStreams};\n",
        "if(x){module.exports={getStreams};}else{global.getStreams=getStreams;}dangerousCall();\n",
    ):
        assert provider_export_floor(unsafe + core) == -1


def _shape_excerpt(text: str, marker_positions: list[int]) -> str:
    marker = min(marker_positions) if marker_positions else len(text)
    start = max(0, marker - 1800)
    excerpt = re.sub(r"\s+", " ", text[start:min(len(text), marker + 100)]).strip()
    return excerpt[-1800:]


def main() -> int:
    _regressions()
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    rows = manifest.get("scrapers") or []
    unresolved: list[str] = []
    no_post_core: list[str] = []
    checked = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        relative = str(row.get("filename") or "").strip()
        if not provider_id or not relative.startswith("providers/"):
            continue
        path = ROOT / relative
        if not path.is_file():
            raise AssertionError(f"missing provider bundle: {provider_id} {relative}")
        text = path.read_text(encoding="utf-8", errors="strict")
        marker_positions = sorted({
            match.start()
            for marker in CORE_MARKERS
            for match in re.finditer(re.escape(f"/* {marker}"), text)
        })
        if not marker_positions:
            continue
        checked += 1
        floor = provider_export_floor(text)
        if floor < 0:
            unresolved.append(provider_id)
            print(
                "FIELD_PROVIDER_EXPORT_SHAPE "
                f"provider={provider_id} excerpt={json.dumps(_shape_excerpt(text, marker_positions), ensure_ascii=True)}"
            )
            continue
        if not any(position > floor for position in marker_positions):
            no_post_core.append(provider_id)

    if unresolved or no_post_core:
        raise AssertionError(
            "provider export/Core boundary unresolved: "
            f"unknown_floor={','.join(sorted(unresolved)) or '-'} "
            f"no_post_export_core={','.join(sorted(no_post_core)) or '-'}"
        )
    if checked < 1:
        raise AssertionError("portfolio contains no provider with a Core tail")

    print(
        "FIELD_PROVIDER_EXPORT_FLOOR_PORTFOLIO "
        f"providers={len(rows)} core_tailed={checked} unknown_floor=0 no_post_export_core=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
