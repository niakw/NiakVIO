#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_provider_quick_yield.py"
PIPELINE = ROOT / "scripts" / "run_provider_repair_pipeline_v6.py"
CONTRACT = ROOT / "tests" / "provider_repair_pipeline_v6_contract_test.py"


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    if old not in text:
        raise SystemExit(f"{label}: source anchor missing in {path.relative_to(ROOT)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> int:
    changed: list[str] = []

    old = '''    fixture_rows = {\n        str(row.get("slug") or ""): row.get("fixture")\n        for row in corpus.get("fixtures") or []\n        if isinstance(row, dict) and isinstance(row.get("fixture"), dict)\n    }\n    fixtures: dict[str, dict[str, Any]] = {}\n    for media_type, slug in REPRESENTATIVE.items():\n        fixture = fixture_rows.get(slug)\n        if not isinstance(fixture, dict):\n            raise RuntimeError(f"missing representative fixture {slug}")\n        fixtures[media_type] = fixture\n\n    tasks: list[dict[str, Any]] = []\n'''
    new = '''    fixture_records = {\n        str(row.get("slug") or ""): row\n        for row in corpus.get("fixtures") or []\n        if isinstance(row, dict) and isinstance(row.get("fixture"), dict)\n    }\n    fixture_rows = {slug: row["fixture"] for slug, row in fixture_records.items()}\n    fixtures: dict[str, dict[str, Any]] = {}\n    for media_type, slug in REPRESENTATIVE.items():\n        fixture = fixture_rows.get(slug)\n        if not isinstance(fixture, dict):\n            raise RuntimeError(f"missing representative fixture {slug}")\n        fixtures[media_type] = fixture\n\n    # Anime catalogues may legitimately expose a movie lane for anime films.\n    # That lane must be proven with the corpus-owned animeMovie fixture rather\n    # than a generic movie such as Interstellar; otherwise semantic/transport\n    # separation is violated and healthy anime-film lanes are false-negative.\n    anime_movie_records = [\n        row for row in fixture_records.values()\n        if isinstance(row.get("fixture"), dict) and row["fixture"].get("animeMovie") is True\n    ]\n    if len(anime_movie_records) != 1:\n        raise RuntimeError(f"expected exactly one animeMovie representative fixture, got {len(anime_movie_records)}")\n    anime_movie_record = anime_movie_records[0]\n    anime_movie_fixture = anime_movie_record["fixture"]\n    anime_movie_providers = {\n        str(value or "").strip().casefold()\n        for value in (anime_movie_record.get("providers") or [])\n        if str(value or "").strip()\n    }\n\n    tasks: list[dict[str, Any]] = []\n'''
    if replace_once(AUDIT, old, new, "fixture record selection"):
        changed.append(str(AUDIT.relative_to(ROOT)))

    old = '''        for media_type in semantic_types(row):\n            tasks.append({\n                "provider_id": provider_id,\n                "provider_name": str(row.get("name") or row.get("id") or provider_id),\n                "filename": filename,\n                "semantic_type": media_type,\n                "fixture": fixtures[media_type],\n            })\n'''
    new = '''        for media_type in semantic_types(row):\n            fixture = (\n                anime_movie_fixture\n                if media_type == "movie" and provider_id in anime_movie_providers\n                else fixtures[media_type]\n            )\n            tasks.append({\n                "provider_id": provider_id,\n                "provider_name": str(row.get("name") or row.get("id") or provider_id),\n                "filename": filename,\n                "semantic_type": media_type,\n                "fixture": fixture,\n            })\n'''
    replace_once(AUDIT, old, new, "per-provider fixture selection")

    old = '''        "tests/provider_native_abort_ignorant_cancellation_test.py",\n    ):\n'''
    new = '''        "tests/provider_native_abort_ignorant_cancellation_test.py",\n        "tests/provider_quick_yield_fixture_selection_test.py",\n    ):\n'''
    if replace_once(PIPELINE, old, new, "repair fixture-selection ownership"):
        changed.append(str(PIPELINE.relative_to(ROOT)))

    old = '''yield_audit = (ROOT / 'scripts/audit_provider_repair_yield_v6.py').read_text(encoding='utf-8')\nportfolio_compare ='''
    new = '''yield_audit = (ROOT / 'scripts/audit_provider_repair_yield_v6.py').read_text(encoding='utf-8')\nquick_yield = (ROOT / 'scripts/audit_provider_quick_yield.py').read_text(encoding='utf-8')\nportfolio_compare ='''
    if replace_once(CONTRACT, old, new, "quick-yield contract ownership"):
        changed.append(str(CONTRACT.relative_to(ROOT)))

    old = '''assert 'tests/provider_repair_v6_recipe_regression_test.py' in pipeline\nassert 'scripts/audit_provider_repair_yield_v6.py' in pipeline\n'''
    new = '''assert 'tests/provider_repair_v6_recipe_regression_test.py' in pipeline\nassert 'tests/provider_quick_yield_fixture_selection_test.py' in pipeline\nassert 'scripts/audit_provider_repair_yield_v6.py' in pipeline\nfor marker in (\n    'animeMovie',\n    'anime_movie_providers',\n    'anime_movie_fixture',\n    'media_type == "movie" and provider_id in anime_movie_providers',\n):\n    assert marker in quick_yield, marker\n'''
    replace_once(CONTRACT, old, new, "anime movie fixture static guard")

    print("QUICK_YIELD_ANIME_MOVIE_FIXTURE_V1 changed=" + (",".join(changed) if changed else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
