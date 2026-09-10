#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return False
        raise AssertionError(f"{label}: old and final source shapes are both absent")
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one old block, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def patch_materializer() -> bool:
    path = ROOT / "scripts" / "materialize_provider_v3_all.py"
    return replace_exact(
        path,
        '''    wanted = list(canonical)\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    if "tv" in wanted and "series" not in wanted:\n        wanted.append("series")\n''',
        '''    wanted = list(canonical)\n    # Anime is a semantic catalogue capability. Nuvio launches episodic anime\n    # through the TV namespace; never invent movie or series manifest types.\n    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n''',
        "materializer anime transport",
    )


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


def patch_reapply_projection() -> bool:
    path = ROOT / "scripts" / "reapply_published_overrides.py"
    return replace_exact(
        path,
        '''    if "anime" in semantic and "tv" not in transport:\n        # Nuvio may surface episodic anime as series/tv. Movie is not a generic\n        # anime alias: only semantic movie capability may select movie transport.\n        transport.append("tv")\n    if "tv" in transport and "series" not in transport:\n        # Some Nuvio client paths request episodic content as `series` before\n        # their local type normalizer runs. Publish it as a transport alias only.\n        transport.append("series")\n    return transport\n''',
        '''    if "anime" in semantic and "tv" not in transport:\n        # Anime is semantically distinct but launches through Nuvio's episodic\n        # TV namespace. Manifest vocabulary remains movie|tv|anime only.\n        # Movie is never invented for anime-only providers.\n        transport.append("tv")\n    return transport\n''',
        "published override transport projection",
    )


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
    changed = False
    changed |= replace_exact(path, 'TRANSPORT = CANONICAL | {"series"}\n', 'TRANSPORT = CANONICAL\n', "anime test transport vocabulary")
    changed |= replace_exact(
        path,
        '''    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    if "tv" in wanted and "series" not in wanted:\n        wanted.append("series")\n    return wanted\n''',
        '''    if "anime" in canonical and "tv" not in wanted:\n        wanted.append("tv")\n    return wanted\n''',
        "anime test projection",
    )
    changed |= replace_exact(
        path,
        '''        if "anime" in canonical or "tv" in canonical:\n            assert "tv" in transport and "series" in transport, (relative, provider_id, transport)\n''',
        '''        if "anime" in canonical:\n            assert "tv" in transport, (relative, provider_id, transport)\n        assert "series" not in transport, (relative, provider_id, transport)\n''',
        "anime test episodic assertion",
    )
    changed |= replace_exact(
        path,
        '''assert 'if "anime" in canonical and "tv" not in wanted:' in materializer\nassert 'wanted.append("series")' in materializer\nassert 'for compatible in ("tv", "movie"):' not in materializer\n''',
        '''assert 'if "anime" in canonical and "tv" not in wanted:' in materializer\nassert 'wanted.append("series")' not in materializer\nassert 'for compatible in ("tv", "movie"):' not in materializer\n''',
        "anime test materializer assertions",
    )
    changed |= replace_exact(
        path,
        '''assert 'if "anime" in canonical and "tv" not in wanted:' in enforcer\nassert 'wanted.append("series")' in enforcer\n''',
        '''assert 'if "anime" in canonical and "tv" not in wanted:' in enforcer\nassert 'wanted.append("series")' not in enforcer\n''',
        "anime test enforcer assertions",
    )
    changed |= replace_exact(path, "assert 'transport.append(\"series\")' in reapply\n", "assert 'transport.append(\"series\")' not in reapply\n", "anime test reapply assertion")
    changed |= replace_exact(
        path,
        'assert machine["media_types"]["anime_only_transport_compatibility"] == ["anime", "tv", "series"]\n',
        'assert machine["media_types"]["anime_only_transport_compatibility"] == ["anime", "tv"]\n',
        "anime test architecture assertion",
    )
    changed |= replace_exact(path, '    "rule=no-artificial-movie+tv-series-alias"\n', '    "rule=no-artificial-movie+tv-transport-only"\n', "anime test summary")
    return changed


def patch_branding_test() -> bool:
    path = ROOT / "tests" / "global_provider_branding_test.py"
    return replace_exact(
        path,
        'assert "post-presentation-name-title-quality-v7" in patched\n',
        'assert "post-presentation-lossless-source-label-v8" in patched\n',
        "branding revision assertion",
    )


def patch_architecture_contract() -> bool:
    path = ROOT / "automation" / "provider-v3-architecture.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    media = payload.setdefault("media_types", {})
    old = media.get("anime_only_transport_compatibility")
    if old == ["anime", "tv"]:
        return False
    if old != ["anime", "tv", "series"]:
        raise AssertionError(f"architecture anime transport drifted: {old!r}")
    media["anime_only_transport_compatibility"] = ["anime", "tv"]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    changes = {
        "materializer": patch_materializer(),
        "enforcer": patch_enforcer(),
        "reapply_projection": patch_reapply_projection(),
        "provider_base": patch_provider_base(),
        "canonical_test": patch_canonical_test(),
        "anime_contract_test": patch_anime_contract_test(),
        "branding_test": patch_branding_test(),
        "architecture_contract": patch_architecture_contract(),
    }
    print("FINAL_PUBLISH_CONTRACT_FIXES " + " ".join(f"{k}={str(v).lower()}" for k, v in changes.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
