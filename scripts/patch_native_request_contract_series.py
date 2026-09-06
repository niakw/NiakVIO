#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "augment_native_corpus_request_contract.py"
LOADER = ROOT / "scripts" / "augment_native_provider_loading.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "The manifest vocabulary is strictly movie|tv|anime. Catalogue/user aliases are a\nclient input concern. The lab still traverses every staged provider (including\nmanifest-disabled rows), but executes only meaningful media routes.\n",
        "Canonical provider identity is strictly movie|tv|anime, while Nuvio transport\nmetadata may additionally expose aliases such as series. The lab still traverses every\nstaged provider (including manifest-disabled rows), but executes only canonical media routes.\n",
        "request contract documentation",
    )
    text = replace_once(
        text,
        'CANONICAL = {"movie", "tv", "anime"}\n',
        'CANONICAL = {"movie", "tv", "anime"}\nTRANSPORT = CANONICAL | {"series"}\n',
        "request contract transport vocabulary",
    )
    old = '''        raw_types = row.get("supportedTypes")
        if not isinstance(raw_types, list) or not raw_types:
            raise SystemExit(
                f"provider {provider_id}: supportedTypes must be a non-empty list of canonical types"
            )
        types: list[str] = []
        for raw in raw_types:
            typ = str(raw or "").strip().lower()
            if typ not in CANONICAL:
                raise SystemExit(f"provider {provider_id}: non-canonical supportedType {typ!r}")
            if typ not in types:
                types.append(typ)
        out[key] = types
'''
    new = '''        raw_supported = row.get("supportedTypes")
        if not isinstance(raw_supported, list) or not raw_supported:
            raise SystemExit(
                f"provider {provider_id}: supportedTypes must be a non-empty transport list"
            )
        supported: list[str] = []
        for raw in raw_supported:
            typ = str(raw or "").strip().lower()
            if typ not in TRANSPORT:
                raise SystemExit(f"provider {provider_id}: invalid transport supportedType {typ!r}")
            if typ not in supported:
                supported.append(typ)

        raw_canonical = row.get("canonicalSupportedTypes")
        if isinstance(raw_canonical, list) and raw_canonical:
            canonical_source = raw_canonical
        else:
            canonical_source = [value for value in supported if value in CANONICAL]
        types: list[str] = []
        for raw in canonical_source:
            typ = str(raw or "").strip().lower()
            if typ not in CANONICAL:
                raise SystemExit(f"provider {provider_id}: non-canonical canonicalSupportedType {typ!r}")
            if typ not in types:
                types.append(typ)
        if not types:
            raise SystemExit(f"provider {provider_id}: canonicalSupportedTypes must not be empty")
        out[key] = types
'''
    text = replace_once(text, old, new, "request contract manifest type boundary")

    transport_helper = '''\n\ndef manifest_transport_types(path: Path) -> dict[str, list[str]]:\n    data = json.loads(path.read_text(encoding="utf-8"))\n    out: dict[str, list[str]] = {}\n    for row in data.get("scrapers", []):\n        if not isinstance(row, dict):\n            continue\n        provider_id = str(row.get("id") or "").strip()\n        if not provider_id:\n            continue\n        raw_supported = row.get("supportedTypes")\n        if not isinstance(raw_supported, list) or not raw_supported:\n            raise SystemExit(f"provider {provider_id}: supportedTypes must be a non-empty transport list")\n        values: list[str] = []\n        for raw in raw_supported:\n            typ = str(raw or "").strip().lower()\n            if typ not in TRANSPORT:\n                raise SystemExit(f"provider {provider_id}: invalid transport supportedType {typ!r}")\n            if typ not in values:\n                values.append(typ)\n        out[provider_id.casefold()] = values\n    return out\n'''
    text = replace_once(
        text,
        '\n\ndef kotlin_map(values: dict[str, list[str]]) -> str:\n',
        transport_helper + '\n\ndef kotlin_map(values: dict[str, list[str]]) -> str:\n',
        "transport manifest map helper",
    )
    text = replace_once(
        text,
        '    types = manifest_types(manifest)\n',
        '    types = manifest_types(manifest)\n    transport_types = manifest_transport_types(manifest)\n',
        "request contract manifest maps",
    )
    text = replace_once(
        text,
        r'    private val declaredTypesByProvider: Map<String, Set<String>> = {kotlin_map(types)}\n\n    private fun requestRoutesFor',
        r'    private val declaredTypesByProvider: Map<String, Set<String>> = {kotlin_map(types)}\n\n    private val transportTypesByProvider: Map<String, Set<String>> = {kotlin_map(transport_types)}\n\n    private fun requestRoutesFor',
        "generated canonical/transport maps",
    )
    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    loader = LOADER.read_text(encoding="utf-8")
    old_compare = '                    val declaredTypes = declaredTypesByProvider[key].orEmpty().sorted()\n'
    count = loader.count(old_compare)
    if count != 2:
        raise SystemExit(f"loader transport metadata comparison anchors: expected 2, got {count}")
    loader = loader.replace(
        old_compare,
        '                    val declaredTypes = transportTypesByProvider[key].orEmpty().sorted()\n',
    )
    compile(loader, str(LOADER), "exec")
    LOADER.write_text(loader, encoding="utf-8")
    print("NATIVE_REQUEST_CONTRACT_SERIES_ALIAS_OK canonical_routes=true transport_metadata=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
