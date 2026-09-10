#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one old block, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def patch_materializer() -> bool:
    path = ROOT / "scripts" / "materialize_provider_v3_all.py"
    changed = False
    changed |= replace_exact(
        path,
        '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    if "tv" in wanted and "series" not in wanted:\n        wanted.append("series")\n''',
        '''    wanted = list(canonical)\n    # Anime is a semantic catalogue capability. Nuvio launches episodic anime\n    # through the TV namespace; never invent movie or series manifest types.\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n''',
        "materializer anime transport",
    )
    changed |= replace_exact(
        path,
        '''        if item in {"movie", "tv", "anime", "series"} and item not in current:\n            current.append(item)\n''',
        '''        if item in {"movie", "tv", "anime", "series"} and item not in current:\n            # Keep legacy series visible here so the comparison below forces a\n            # rewrite to canonical movie|tv|anime vocabulary.\n            current.append(item)\n''',
        "materializer legacy series detector",
    )
    return changed


def patch_enforcer() -> bool:
    path = ROOT / "scripts" / "enforce_provider_v3_semantic_transport_contract_v5.py"
    changed = False
    changed |= replace_exact(
        path,
        '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    if "tv" in wanted and "series" not in wanted:\n        wanted.append("series")\n    return wanted\n''',
        '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    return wanted\n''',
        "enforcer anime transport",
    )
    changed |= replace_exact(
        path,
        '''    required = (\n        'if "anime" in canonical and "tv" not in wanted:',\n        'wanted.append("series")',\n        'item in {"movie", "tv", "anime", "series"}',\n    )\n    forbidden = (\n        'for compatible in ("tv", "movie"):',\n        'wanted = ["anime", "tv", "movie"]',\n    )\n''',
        '''    required = (\n        'if "anime" in canonical and "tv" not in wanted:',\n        'item in {"movie", "tv", "anime", "series"}',\n    )\n    forbidden = (\n        'wanted.append("series")',\n        'for compatible in ("tv", "movie"):',\n        'wanted = ["anime", "tv", "movie"]',\n    )\n''',
        "enforcer materializer contract",
    )
    return changed


def patch_provider_base() -> bool:
    path = ROOT / "scripts" / "provider_base_store.py"
    return replace_exact(
        path,
        '''    const label = _text(match[4])\n      .replace(/<[^>]+>/g, " ")\n      .replace(/&nbsp;/gi, " ")\n      .replace(/&amp;/gi, "&")\n      .replace(/\\s+/g, " ")\n      .trim();\n''',
        '''    const label = _htmlVisibleText(match[4]);\n''',
        "ProviderBase search-card visible label scanner",
    )


def patch_canonical_test() -> bool:
    path = ROOT / "tests" / "canonical_media_types_test.py"
    changed = False
    changed |= replace_exact(
        path,
        '''        expected_transport = list(expected_types)\n        if "anime" in expected_types:\n            for compatible in ("tv", "movie"):\n                if compatible not in expected_transport:\n                    expected_transport.append(compatible)\n''',
        '''        expected_transport = list(expected_types)\n        if "anime" in expected_types and "tv" not in expected_transport:\n            expected_transport.append("tv")\n''',
        "canonical test anime transport",
    )
    changed |= replace_exact(
        path,
        '    "anime_transport=anime+tv+movie"\n',
        '    "anime_transport=anime+tv movie_only_when_canonical"\n',
        "canonical test summary",
    )
    return changed


def patch_anime_contract_test() -> bool:
    path = ROOT / "tests" / "provider_anime_semantic_transport_contract_test.py"
    text = path.read_text(encoding="utf-8")
    old = '''assert 'for compatible in ("tv", "movie"):' in materializer\n'''
    new = '''assert 'if "anime" in canonical and "tv" not in wanted:' in materializer\nassert 'wanted.append("series")' not in materializer\nassert 'for compatible in ("tv", "movie"):' not in materializer\n'''
    if new in text:
        return False
    if old not in text:
        raise AssertionError("anime contract test source shape drifted")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return True


def patch_branding_test() -> bool:
    path = ROOT / "tests" / "global_provider_branding_test.py"
    return replace_exact(
        path,
        'assert "post-presentation-name-title-quality-v7" in patched\n',
        'assert "post-presentation-lossless-source-label-v8" in patched\n',
        "branding revision assertion",
    )


def main() -> int:
    changes = {
        "materializer": patch_materializer(),
        "enforcer": patch_enforcer(),
        "provider_base": patch_provider_base(),
        "canonical_test": patch_canonical_test(),
        "anime_contract_test": patch_anime_contract_test(),
        "branding_test": patch_branding_test(),
    }
    print("FINAL_PUBLISH_CONTRACT_FIXES " + " ".join(f"{k}={str(v).lower()}" for k, v in changes.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
