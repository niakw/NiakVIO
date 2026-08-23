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

    # Only classic named declarations are provider-owned after the export. Calls,
    # assignments and anonymous declarations must never be swallowed as provider bytes.
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


def _shape_excerpt(text: str, marker_positions: list[int]) -> str:
    """Return a compact diagnostic immediately before the first generated layer."""
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
