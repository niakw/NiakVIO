#!/usr/bin/env python3
"""Make the iOS Lab consume the three global pools adaptively, one title at a time."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/prepare_native_ios_reader_acceptance.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise AssertionError(f"{label}: anchor count={text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    original = text
    text = replace_once(
        text,
        "from rotating_corpus import select_fixtures\n",
        "from rotating_corpus import rotated_candidates, select_fixtures\n",
        "import rotated candidates",
    )
    text = replace_once(
        text,
        '    println("FIELD_NATIVE_CORPUS_IOS_BEGIN mode=$mode fixtures=${resumedFixtures.size} providers=${iosProviders.size} target=$targetProvider provider_timeout_ms=$providerTimeoutMs player_timeout_ms=$playerTimeoutMs resume_fixture=$resumeFixture resume_after=$resumeAfterProvider")\n\n    resumedFixtures.forEach { fixture ->\n        val selectedBase = iosProviders.filter { provider ->\n            provider.supportedTypes.any { type ->\n                normalizedType(type) == fixture.mediaType\n            }\n        }\n',
        '    println("FIELD_NATIVE_CORPUS_IOS_BEGIN mode=$mode reserve_fixtures=${resumedFixtures.size} initial_per_lane=1 fixed_batch=false providers=${iosProviders.size} target=$targetProvider provider_timeout_ms=$providerTimeoutMs player_timeout_ms=$playerTimeoutMs resume_fixture=$resumeFixture resume_after=$resumeAfterProvider")\n\n    val terminalProviders = mutableSetOf<String>()\n    resumedFixtures.forEach { fixture ->\n        val selectedBase = iosProviders.filter { provider ->\n            val key = provider.id.lowercase() + "|" + fixture.mediaType\n            key !in terminalProviders && provider.supportedTypes.any { type ->\n                normalizedType(type) == fixture.mediaType\n            }\n        }\n        if (selectedBase.isEmpty()) return@forEach\n',
        "terminal provider lane set",
    )
    text = replace_once(
        text,
        '                emit(\n                    "FIELD_NATIVE_IOS_RESULT",\n                    ResultObservation(\n                        fixture = fixture.slug,\n                        provider = info.id,\n                        mediaType = fixture.mediaType,\n                        enabled = info.enabled,\n                        count = rows.size,\n                        durationMs = startedAt.elapsedNow().inWholeMilliseconds,\n                        state = "completed",\n                    ),\n                )\n                rows.firstOrNull()?.let { row ->\n',
        '                emit(\n                    "FIELD_NATIVE_IOS_RESULT",\n                    ResultObservation(\n                        fixture = fixture.slug,\n                        provider = info.id,\n                        mediaType = fixture.mediaType,\n                        enabled = info.enabled,\n                        count = rows.size,\n                        durationMs = startedAt.elapsedNow().inWholeMilliseconds,\n                        state = "completed",\n                    ),\n                )\n                val providerLaneKey = info.id.lowercase() + "|" + fixture.mediaType\n                if (rows.isEmpty()) {\n                    println("FIELD_NATIVE_IOS_CATALOG_MISS fixture=${fixture.slug} provider=${info.id} type=${fixture.mediaType} action=rotate_same_lane")\n                } else {\n                    terminalProviders += providerLaneKey\n                }\n                rows.firstOrNull()?.let { row ->\n',
        "positive vs clean miss",
    )
    text = replace_once(
        text,
        '            } catch (error: Throwable) {\n                println("FIELD_NATIVE_IOS_PROVIDER_END fixture=${fixture.slug} provider=${info.id} state=${if (error is TimeoutCancellationException) "timeout" else "error"} duration_ms=${startedAt.elapsedNow().inWholeMilliseconds}")\n',
        '            } catch (error: Throwable) {\n                terminalProviders += info.id.lowercase() + "|" + fixture.mediaType\n                println("FIELD_NATIVE_IOS_PROVIDER_END fixture=${fixture.slug} provider=${info.id} state=${if (error is TimeoutCancellationException) "timeout" else "error"} duration_ms=${startedAt.elapsedNow().inWholeMilliseconds}")\n',
        "error stops rotation",
    )

    old_fixture_rows = '''def fixture_rows() -> list[dict]:\n    rows = []\n    for kind in ("movie", "tv", "anime"):\n        selected = select_fixtures(kind, count=1, provider="ios-native")\n        if len(selected) != 1:\n            raise SystemExit(f"missing rotating fixture for {kind}")\n        fixture = selected[0]\n        rows.append(\n            {\n                "slug": fixture["slug"],\n                "tmdbId": str(fixture.get("tmdbId") or ""),\n                "mediaType": kind,\n                "season": fixture.get("season"),\n                "episode": fixture.get("episode"),\n            }\n        )\n    return rows\n'''
    new_fixture_rows = '''def fixture_rows() -> list[dict]:\n    # Embed the three global pools as an interleaved reserve. Full iOS execution\n    # starts with one movie/TV/anime candidate and only reaches later candidates\n    # for provider+lane pairs that returned a clean zero. There is no fixed batch.\n    pools = {kind: rotated_candidates(kind, provider="ios-native") for kind in ("movie", "tv", "anime")}\n    if any(not rows for rows in pools.values()):\n        raise SystemExit("missing iOS rotating global fixture pool")\n    rows = []\n    for index in range(max(len(values) for values in pools.values())):\n        for kind in ("movie", "tv", "anime"):\n            if index >= len(pools[kind]):\n                continue\n            fixture = pools[kind][index]\n            rows.append(\n                {\n                    "slug": fixture["slug"],\n                    "tmdbId": str(fixture.get("tmdbId") or ""),\n                    "mediaType": kind,\n                    "season": fixture.get("season"),\n                    "episode": fixture.get("episode"),\n                }\n            )\n    return rows\n'''
    text = replace_once(text, old_fixture_rows, new_fixture_rows, "fixture reserve")

    if text != original:
        PATH.write_text(text, encoding="utf-8")
    print(f"IOS_ADAPTIVE_CATALOG_V1_OK changed={str(text != original).lower()} clean_zero_only=true fixed_batch=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
