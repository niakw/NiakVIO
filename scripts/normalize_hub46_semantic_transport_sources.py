#!/usr/bin/env python3
"""Normalize the current Hub46 source contracts before release validation.

Current semantic/transport contract:
- canonical capability: movie | tv | anime
- anime-only launch compatibility: add tv
- never synthesize `series`
- never synthesize `movie`

Current Domain Refresh contract:
- only provider IDs present in the current manifest may be resolved/mutated;
- archived provider-hubs/history rows remain historical knowledge only;
- CONFIG rebuild/materialization must be exactly the current Hub46.

This migration is intentionally narrow and idempotent. It edits only exact
legacy source shapes that could otherwise reintroduce retired transport aliases
or historical providers during reconstruction/publication/domain refresh.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        return False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one legacy block, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def patch_materializer() -> bool:
    path = ROOT / "scripts" / "materialize_provider_v3_all.py"
    old = '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    if "tv" in wanted and "series" not in wanted:\n        wanted.append("series")\n\n    current = []\n    for value in entry.get("supportedTypes") or []:\n        item = str(value or "").strip().casefold()\n        if item in {"movie", "tv", "anime", "series"} and item not in current:\n            current.append(item)\n'''
    new = '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n\n    current = []\n    for value in entry.get("supportedTypes") or []:\n        item = str(value or "").strip().casefold()\n        if item in {"movie", "tv", "anime"} and item not in current:\n            current.append(item)\n'''
    return replace_exact(path, old, new, "materializer anime transport")


def patch_reapply() -> bool:
    path = ROOT / "scripts" / "reapply_published_overrides.py"
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        'if item in {"movie", "tv", "anime", "series"} and item not in result:',
        'if item in {"movie", "tv", "anime"} and item not in result:',
        1,
    )
    old = '''    if "anime" in semantic and "tv" not in transport:\n        # Nuvio may surface episodic anime as series/tv. Movie is not a generic\n        # anime alias: only semantic movie capability may select movie transport.\n        transport.append("tv")\n    if "tv" in transport and "series" not in transport:\n        # Some Nuvio client paths request episodic content as `series` before\n        # their local type normalizer runs. Publish it as a transport alias only.\n        transport.append("series")\n    return transport\n'''
    new = '''    if "anime" in semantic and "tv" not in transport:\n        # Nuvio launches episodic anime through its TV namespace. Movie is not a\n        # generic anime alias: only semantic movie capability may select movie.\n        transport.append("tv")\n    return transport\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError("reapply anime transport block drifted")
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def patch_enforcer() -> bool:
    path = ROOT / "scripts" / "enforce_provider_v3_semantic_transport_contract_v5.py"
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        "capability while accepting Nuvio episodic TV/series transport aliases.",
        "capability while accepting the Nuvio episodic TV transport alias.",
        1,
    )
    text = text.replace(
        'if item in {"movie", "tv", "anime", "series"} and item not in out:',
        'if item in {"movie", "tv", "anime"} and item not in out:',
        1,
    )
    old_transport = '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    if "tv" in wanted and "series" not in wanted:\n        wanted.append("series")\n    return wanted\n'''
    new_transport = '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    return wanted\n'''
    if old_transport in text:
        text = text.replace(old_transport, new_transport, 1)
    elif new_transport not in text:
        raise AssertionError("enforcer anime transport block drifted")
    text = text.replace(
        '    if len(result) != 96:\n        raise AssertionError(f"provider_catalog.json semantic rows={len(result)} expected=96")',
        '    if len(result) != 46:\n        raise AssertionError(f"provider_catalog.json semantic rows={len(result)} expected=46")',
        1,
    )

    pattern = re.compile(
        r"def patch_materializer\(\) -> bool:\n.*?(?=def patch_runtime_regression_expectations\(\) -> bool:)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise AssertionError("enforcer patch_materializer function missing")
    new_function = '''def patch_materializer() -> bool:\n    path = ROOT / "scripts" / "materialize_provider_v3_all.py"\n    text = path.read_text(encoding="utf-8")\n    pattern = re.compile(\n        r"def normalize_anime_transport_compatibility\\(entry: dict\\[str, Any\\]\\) -> bool:\\n"\n        r".*?(?=def base_version\\(value: object\\) -> str:)",\n        re.S,\n    )\n    match = pattern.search(text)\n    if not match:\n        raise AssertionError("materializer semantic/transport projector missing")\n    current = match.group(0)\n    required = (\n        'if "anime" in canonical and "tv" not in wanted:',\n        'wanted.append("tv")',\n        'item in {"movie", "tv", "anime"}',\n    )\n    forbidden = (\n        'wanted.append("series")',\n        '"series"',\n        'for compatible in ("tv", "movie"):',\n        'wanted = ["anime", "tv", "movie"]',\n    )\n    if any(value not in current for value in required) or any(value in current for value in forbidden):\n        raise AssertionError("materializer semantic/transport projector drifted")\n    return False\n\n\n'''
    if match.group(0) != new_function:
        text = text[: match.start()] + new_function + text[match.end() :]

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def patch_finalizer() -> bool:
    path = ROOT / "scripts" / "finalize_publish_contracts.py"
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        "Nuvio transport surface: episodic tv/anime additionally exposes tv+series.",
        "Nuvio transport surface: anime-only additionally exposes the tv launch alias.",
        1,
    )
    text = text.replace(
        '''        for needle in (\n            'if "anime" in canonical and "tv" not in wanted:',\n            'wanted.append("tv")',\n            'wanted.append("series")',\n        ):\n''',
        '''        for needle in (\n            'if "anime" in canonical and "tv" not in wanted:',\n            'wanted.append("tv")',\n        ):\n''',
        1,
    )
    text = text.replace(
        '''    for needle in (\n        'transport.append("tv")',\n        'transport.append("series")',\n        'Movie is not a generic',\n    ):\n''',
        '''    for needle in (\n        'transport.append("tv")',\n        'Movie is not a generic',\n    ):\n''',
        1,
    )
    text = text.replace(
        'if media.get("anime_only_transport_compatibility") != ["anime", "tv", "series"]:\n        raise AssertionError("architecture anime transport must remain anime+tv+series")',
        'if media.get("anime_only_transport_compatibility") != ["anime", "tv"]:\n        raise AssertionError("architecture anime transport must remain anime+tv")',
        1,
    )
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def patch_domain_refresh() -> bool:
    path = ROOT / "scripts" / "domain_refresh_transaction_v2.py"
    text = path.read_text(encoding="utf-8")
    original = text

    if "CURRENT_PROVIDER_COUNT = 46" not in text:
        marker = 'PROVIDERS_DIR = ROOT / "providers"\n'
        if marker not in text:
            raise AssertionError("domain refresh providers-dir marker drifted")
        text = text.replace(marker, marker + "CURRENT_PROVIDER_COUNT = 46\n", 1)

    old_guard = '''    manifest_rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]\n    material_rows = [row for row in materialization.get("providers") or [] if isinstance(row, dict)]\n    if len(manifest_rows) != 96 or len(material_rows) != 96:\n        raise RuntimeError(\n            f"domain publication requires 96/96 state: manifest={len(manifest_rows)} materialization={len(material_rows)}"\n        )\n\n    manifest_by_id = {canonical(row.get("id")): row for row in manifest_rows}\n    material_by_id = {canonical(row.get("provider")): row for row in material_rows}\n'''
    new_guard = '''    manifest_rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]\n    material_rows = [row for row in materialization.get("providers") or [] if isinstance(row, dict)]\n    manifest_ids = {canonical(row.get("id")) for row in manifest_rows if canonical(row.get("id"))}\n    material_ids = {canonical(row.get("provider")) for row in material_rows if canonical(row.get("provider"))}\n    if len(manifest_rows) != CURRENT_PROVIDER_COUNT or len(material_rows) != CURRENT_PROVIDER_COUNT:\n        raise RuntimeError(\n            f"domain publication requires current Hub{CURRENT_PROVIDER_COUNT} state: "\n            f"manifest={len(manifest_rows)} materialization={len(material_rows)}"\n        )\n    if len(manifest_ids) != CURRENT_PROVIDER_COUNT or material_ids != manifest_ids:\n        raise RuntimeError(\n            "domain publication current provider identity mismatch: "\n            f"manifest={len(manifest_ids)} materialization={len(material_ids)}"\n        )\n\n    manifest_by_id = {canonical(row.get("id")): row for row in manifest_rows}\n    material_by_id = {canonical(row.get("provider")): row for row in material_rows}\n'''
    if old_guard in text:
        text = text.replace(old_guard, new_guard, 1)
    elif new_guard not in text:
        raise AssertionError("domain refresh 96/96 rebuild guard drifted")

    text = text.replace(
        '    materialization["providerCount"] = 96\n    materialization["expectedProviderCount"] = 96\n',
        '    materialization["providerCount"] = CURRENT_PROVIDER_COUNT\n    materialization["expectedProviderCount"] = CURRENT_PROVIDER_COUNT\n',
        1,
    )

    old_scope = '''    hubs = _authoritative_hub_configs(config)\n    selected = {canonical(value) for value in args.provider if canonical(value)}\n    work: list[tuple[str, dict[str, Any], dict[str, Any]]] = []\n    for provider_id, cfg in sorted(hubs.items()):\n        if selected and provider_id not in selected:\n            continue\n'''
    new_scope = '''    manifest_scope = load(MANIFEST_PATH)\n    current_provider_ids = {\n        canonical(row.get("id"))\n        for row in manifest_scope.get("scrapers") or []\n        if isinstance(row, dict) and canonical(row.get("id"))\n    }\n    if len(current_provider_ids) != CURRENT_PROVIDER_COUNT:\n        raise SystemExit(\n            f"domain refresh requires current Hub{CURRENT_PROVIDER_COUNT} manifest scope; "\n            f"got {len(current_provider_ids)}"\n        )\n\n    hubs = _authoritative_hub_configs(config)\n    selected = {canonical(value) for value in args.provider if canonical(value)}\n    outside_scope = selected - current_provider_ids\n    if outside_scope:\n        raise SystemExit(\n            "domain refresh refuses historical/non-current provider selection: "\n            + ",".join(sorted(outside_scope))\n        )\n    work: list[tuple[str, dict[str, Any], dict[str, Any]]] = []\n    for provider_id, cfg in sorted(hubs.items()):\n        if provider_id not in current_provider_ids:\n            continue\n        if selected and provider_id not in selected:\n            continue\n'''
    if old_scope in text:
        text = text.replace(old_scope, new_scope, 1)
    elif new_scope not in text:
        raise AssertionError("domain refresh current-manifest work scope drifted")

    old_report = '''        "authority": "provider-hubs-authoritative-terminal",\n        "terminal_validation_required": False,\n        "providers": {},\n'''
    new_report = '''        "authority": "provider-hubs-authoritative-terminal",\n        "terminal_validation_required": False,\n        "scope_provider_count": len(current_provider_ids),\n        "providers": {},\n'''
    if old_report in text:
        text = text.replace(old_report, new_report, 1)
    elif new_report not in text:
        raise AssertionError("domain refresh report scope marker drifted")

    old_print = '''        f"resolved={resolved} unresolved={unresolved} applied={len(set(changed_provider_ids))} "\n        f"registry={len(set(registry_changed_ids))} bundles={len(bundle_updates)} "\n'''
    new_print = '''        f"scope={len(current_provider_ids)} resolved={resolved} unresolved={unresolved} "\n        f"applied={len(set(changed_provider_ids))} "\n        f"registry={len(set(registry_changed_ids))} bundles={len(bundle_updates)} "\n'''
    if old_print in text:
        text = text.replace(old_print, new_print, 1)
    elif new_print not in text:
        raise AssertionError("domain refresh summary scope marker drifted")

    if "requires 96/96 state" in text:
        raise AssertionError("domain refresh still contains active 96/96 publication guard")

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    changes = {
        "materializer": patch_materializer(),
        "reapply": patch_reapply(),
        "enforcer": patch_enforcer(),
        "finalizer": patch_finalizer(),
        "domain_refresh": patch_domain_refresh(),
    }
    print("HUB46_SOURCE_NORMALIZE " + " ".join(f"{k}={int(v)}" for k, v in changes.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
