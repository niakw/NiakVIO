#!/usr/bin/env python3
"""Normalize the current Hub46 semantic/transport source contract.

Current contract:
- canonical capability: movie | tv | anime
- anime-only launch compatibility: add tv
- never synthesize `series`
- never synthesize `movie`

This migration is intentionally narrow and idempotent. It edits only exact
legacy source shapes that could otherwise reintroduce the retired `series`
transport alias during reconstruction/publication.
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


def main() -> int:
    changes = {
        "materializer": patch_materializer(),
        "reapply": patch_reapply(),
        "enforcer": patch_enforcer(),
        "finalizer": patch_finalizer(),
    }
    print("HUB46_SEMANTIC_TRANSPORT_SOURCE_NORMALIZE " + " ".join(f"{k}={int(v)}" for k, v in changes.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
