#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / "scripts" / "health_check.mjs"
CONFIG = ROOT / "health-config.json"
PACKAGE = ROOT / "package.json"
TEST = ROOT / "tests" / "adaptive_category_fallback_test.py"


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    config["schema_version"] = max(68, int(config.get("schema_version") or 0))
    deep = config.setdefault("modes", {}).setdefault("deep", {})
    deep["fallback_fixture_limit_per_category"] = 2
    movies = config.setdefault("fixtures", {}).setdefault("movie", [])
    ninja = {
        "label": "Mon ninja et moi 3",
        "tmdbId": "1215638",
        "mediaType": "movie",
        "title": "Mon ninja et moi 3",
        "year": 2025,
        "expectedDurationMinutes": 88,
    }
    movies = [row for row in movies if str(row.get("tmdbId")) != "1215638"]
    insert_at = 1 if movies else 0
    movies.insert(insert_at, ninja)
    config["fixtures"]["movie"] = movies
    dump(CONFIG, config)

    source = HEALTH.read_text(encoding="utf-8")
    old = '''  const fallbackToRun = requestedMode === 'deep'\n    ? fallbackFixtures.filter((fixture) => categoriesNeedingFallback.has(fixture.category))\n    : [];\n  const useFallback = fallbackToRun.length > 0;\n  if (useFallback) {\n    for (const fixture of fallbackToRun) await executeFixture(fixture, 'fallback');\n  }\n'''
    new = '''  // Deep fallback is a bounded cascade per catalogue category.  Stop as soon\n  // as one alternate title proves healthy, instead of probing every fallback\n  // or declaring a provider dead because one blockbuster is absent.\n  if (requestedMode === 'deep') {\n    for (const category of categoriesNeedingFallback) {\n      const categoryFallbacks = fallbackFixtures.filter((fixture) => fixture.category === category);\n      for (const fixture of categoryFallbacks) {\n        await executeFixture(fixture, 'fallback');\n        const latest = fixtureResults[fixtureResults.length - 1];\n        if (latest?.fixture?.category === category && latest.status === 'healthy') break;\n        if (latest?.status === 'excluded') break;\n      }\n    }\n  }\n'''
    if new not in source:
        if old not in source:
            raise SystemExit("health_check fallback execution anchor missing")
        source = source.replace(old, new, 1)

    old_activation = '''    const fallback = fixtureResults.filter((item) => item.fixture_phase === 'fallback' && item.fixture?.category === category);\n    return fallback.length ? fallback : primary;\n'''
    new_activation = '''    const fallback = fixtureResults.filter((item) => item.fixture_phase === 'fallback' && item.fixture?.category === category);\n    const healthyFallback = fallback.find((item) => item.status === 'healthy');\n    // One verified alternate establishes current category capability. Earlier\n    // catalogue misses are diagnostics, not negative coverage votes.\n    return healthyFallback ? [healthyFallback] : (fallback.length ? fallback : primary);\n'''
    if new_activation not in source:
        if old_activation not in source:
            raise SystemExit("health_check activation fallback anchor missing")
        source = source.replace(old_activation, new_activation, 1)
    HEALTH.write_text(source, encoding="utf-8")

    TEST.write_text('''#!/usr/bin/env python3\nimport json\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nsource = (ROOT / "scripts" / "health_check.mjs").read_text(encoding="utf-8")\nconfig = json.loads((ROOT / "health-config.json").read_text(encoding="utf-8"))\n\nmovies = config["fixtures"]["movie"]\nassert movies[0]["tmdbId"] == "157336", movies[:3]\nassert movies[1]["tmdbId"] == "1215638", movies[:3]\nassert movies[1]["mediaType"] == "movie"\nassert movies[1]["expectedDurationMinutes"] == 88\nassert config["modes"]["deep"]["fallback_fixture_limit_per_category"] == 2\nassert "for (const category of categoriesNeedingFallback)" in source\nassert "if (latest?.fixture?.category === category && latest.status === 'healthy') break;" in source\nassert "if (latest?.status === 'excluded') break;" in source\nassert "const healthyFallback = fallback.find((item) => item.status === 'healthy');" in source\nassert "return healthyFallback ? [healthyFallback] : (fallback.length ? fallback : primary);" in source\nprint("adaptive per-category fallback cascade tests passed")\n''', encoding="utf-8")

    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    command = package["scripts"]["test"]
    test_cmd = "python3 tests/adaptive_category_fallback_test.py"
    if test_cmd not in command:
        command += " && " + test_cmd
    package["scripts"]["test"] = command
    dump(PACKAGE, package)

    print("adaptive per-category fallback migration applied: Interstellar -> Mon ninja et moi 3 -> Tenet, stop on proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
