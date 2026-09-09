#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "build_provider_history_matrix_v3.py"

OLD_FN = '''def semantic_types(row: dict[str, Any] | None) -> set[str]:
    if not row:
        return set()
    canonical = row.get("canonicalSupportedTypes")
    source = canonical if isinstance(canonical, list) and canonical else row.get("supportedTypes")
    return {
        canon(value)
        for value in (source or [])
        if canon(value) in {"movie", "tv", "anime"}
    }
'''

NEW_FN = '''def semantic_types(row: dict[str, Any] | None, *, allow_supported_fallback: bool = True) -> set[str]:
    if not row:
        return set()
    canonical = row.get("canonicalSupportedTypes")
    if isinstance(canonical, list) and canonical:
        source = canonical
    elif allow_supported_fallback:
        source = row.get("supportedTypes")
    else:
        source = []
    return {
        canon(value)
        for value in (source or [])
        if canon(value) in {"movie", "tv", "anime"}
    }
'''

OLD_LOOP = '''        historical_types: dict[str, list[str]] = {}
        for version in HISTORY:
            values = semantic_types(manifests[version].get(pid))
            if version == "5.21.0":
                floor = fixture0_rows.get(pid) if isinstance(fixture0_rows, dict) else None
                if isinstance(floor, dict):
                    explicit = {
                        canon(value)
                        for value in (floor.get("semanticTypes") or [])
                        if canon(value) in {"movie", "tv", "anime"}
                    }
                    legacy = {
                        canon(value)
                        for value in (floor.get("types") or [])
                        if canon(value) in {"movie", "tv", "anime"}
                    }
                    values = explicit or legacy or values
            historical_types[version] = sorted(values)

        type_floor = set().union(*(set(values) for values in historical_types.values()))
'''

NEW_LOOP = '''        historical_types: dict[str, list[str]] = {}
        ambiguous_transport_types: dict[str, list[str]] = {}
        for version in HISTORY:
            manifest_row = manifests[version].get(pid)
            # 5.21.16 predates the canonical semantic/transport split for a number
            # of providers. Its supportedTypes can be movie/tv transport aliases
            # even when the same provider is canonically anime in 5.21.0, 5.21.36
            # and current. Preserve that evidence, but never make it a blocking
            # semantic capability floor unless canonicalSupportedTypes exists.
            allow_supported = version != "5.21.16"
            values = semantic_types(manifest_row, allow_supported_fallback=allow_supported)
            if version == "5.21.16" and not values:
                ambiguous = semantic_types(manifest_row, allow_supported_fallback=True)
                if ambiguous:
                    ambiguous_transport_types[version] = sorted(ambiguous)
            if version == "5.21.0":
                floor = fixture0_rows.get(pid) if isinstance(fixture0_rows, dict) else None
                if isinstance(floor, dict):
                    explicit = {
                        canon(value)
                        for value in (floor.get("semanticTypes") or [])
                        if canon(value) in {"movie", "tv", "anime"}
                    }
                    legacy = {
                        canon(value)
                        for value in (floor.get("types") or [])
                        if canon(value) in {"movie", "tv", "anime"}
                    }
                    values = explicit or legacy or values
            historical_types[version] = sorted(values)

        type_floor = set().union(*(set(values) for values in historical_types.values()))
'''

OLD_CONTRACT = '''            "historicalSemanticTypes": historical_types,
            "semanticTypeFloor": sorted(type_floor),
'''
NEW_CONTRACT = '''            "historicalSemanticTypes": historical_types,
            "historicalAmbiguousTransportTypes": ambiguous_transport_types,
            "semanticTypeFloor": sorted(type_floor),
'''

OLD_POLICY = '''        "semanticCapabilityLossAllowedSilently": False,
        "historicalHlsLossAllowedSilently": False,
'''
NEW_POLICY = '''        "semanticCapabilityLossAllowedSilently": False,
        "legacy52116SupportedTypesAreBlockingSemanticProof": False,
        "historicalHlsLossAllowedSilently": False,
'''


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if old in text:
        return text.replace(old, new, 1), True
    if new in text:
        return text, False
    raise SystemExit(f"history v3 migration pattern not found: {label}")


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = False
    for old, new, label in (
        (OLD_FN, NEW_FN, "semantic_types"),
        (OLD_LOOP, NEW_LOOP, "historical type floor"),
        (OLD_CONTRACT, NEW_CONTRACT, "contract payload"),
        (OLD_POLICY, NEW_POLICY, "policy payload"),
    ):
        text, did = replace_once(text, old, new, label)
        changed = changed or did
    if changed:
        TARGET.write_text(text, encoding="utf-8")
    print(f"HISTORY_V3_SEMANTIC_MIGRATION changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
