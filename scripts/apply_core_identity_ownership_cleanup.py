#!/usr/bin/env python3
"""One-shot deterministic migration for the Provider v3 identity ownership cleanup.

This script is intentionally removed by the publication workflow after success.
It changes source contracts only; provider bytes are rebuilt later by the same
transaction from ProviderBase + DATA/CONFIG + managed Lego.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def remove_block(text: str, start_marker: str, end_marker: str, label: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise AssertionError(f"{label}: start marker missing")
    end = text.find(end_marker, start)
    if end < 0:
        raise AssertionError(f"{label}: end marker missing")
    return text[:start] + text[end:]


def patch_engine_policy() -> None:
    path = "engine_v2/src/catalogue-identity-policy.mjs"
    text = read(path)
    anchor = "export function providerMedia(value) {"
    helper = '''export function scoreCatalogueItem(item = {}, metadata = {}, targetType = "") {\n  return scoreCatalogueIdentity({\n    title: item.title,\n    expectedTitles: [metadata?.title, ...(metadata?.aliases ?? [])].filter(Boolean),\n    actualMedia: item.type,\n    expectedMedia: targetType,\n    year: item.year,\n    expectedYear: metadata?.year,\n    providerId: item.id,\n    strictIdentity: true,\n    requireProviderTypeEvidence: false,\n  });\n}\n\n'''
    if "export function scoreCatalogueItem(" not in text:
        text = replace_once(text, anchor, helper + anchor, "engine shared catalogue item helper")
    write(path, text)


def patch_purstream_adapter() -> None:
    path = "engine_v2/providers/purstream.mjs"
    text = read(path)
    text = replace_once(
        text,
        'import { normalizeTitle, scoreCatalogueIdentity } from "../src/catalogue-identity-policy.mjs";',
        'import { normalizeTitle, scoreCatalogueItem } from "../src/catalogue-identity-policy.mjs";',
        "Purstream shared identity import",
    )
    call_old = "strictIdentityScore(item, metadata, providerMediaType(ctx.request.mediaType))"
    call_new = "scoreCatalogueItem({ id: providerId(item), title: itemTitle(item), type: itemType(item), year: itemYear(item) }, metadata, providerMediaType(ctx.request.mediaType))"
    count = text.count(call_old)
    if count != 1:
        raise AssertionError(f"Purstream search identity call count={count}")
    text = text.replace(call_old, call_new)
    rank_old = "strictIdentityScore(item, metadata, targetType)"
    rank_new = "scoreCatalogueItem({ id: providerId(item), title: itemTitle(item), type: itemType(item), year: itemYear(item) }, metadata, targetType)"
    count = text.count(rank_old)
    if count != 1:
        raise AssertionError(f"Purstream rank identity call count={count}")
    text = text.replace(rank_old, rank_new)
    start = "export function strictIdentityScore(item, metadata, targetType) {\n"
    end = "export function collectSearchItems(payload) {\n"
    text = remove_block(text, start, end, "remove Purstream local identity wrapper")
    if "strictIdentityScore" in text:
        raise AssertionError("Purstream still contains strictIdentityScore")
    write(path, text)


def patch_purstream_test() -> None:
    path = "engine_v2/tests/purstream-adapter.test.mjs"
    text = read(path)
    text = replace_once(
        text,
        'import { createPurstreamAdapter, derivePurstreamEndpoint, strictIdentityScore } from "../providers/purstream.mjs";',
        'import { createPurstreamAdapter, derivePurstreamEndpoint } from "../providers/purstream.mjs";',
        "Purstream test import",
    )
    first = 'assert.equal(strictIdentityScore({ id: 1, title: "Breaking Bad", type: "movie", year: 2008 }, { title: "Breaking Bad", year: 2008 }, "tv"), -1);\n'
    last = 'assert.equal(strictIdentityScore({ id: 88, title: "House of the Dragon", type: "movie", year: 2026 }, { title: "House of the Dragon", year: 2022 }, "movie"), -1);\n'
    start = text.find(first)
    end = text.find(last, start)
    if start < 0 or end < 0:
        raise AssertionError("Purstream direct local score assertions missing")
    end += len(last)
    text = text[:start] + text[end:]
    if "strictIdentityScore" in text:
        raise AssertionError("Purstream test still references local identity score")
    write(path, text)


def patch_purstream_contract() -> None:
    path = "tests/purstream_original_bug_matrix_contract_test.py"
    text = read(path)
    text = replace_once(
        text,
        'assert "expectedTitles.includes(title)" in base_store\nassert "Math.abs(Number(year) - Number(expectedYear)) > 1" in base_store\n',
        'assert "__nuvioIdentityPolicyV1" in base_store\nassert "Math.abs(Number(year) - Number(expectedYear)) > 1" not in base_store\n',
        "Purstream ProviderBase identity ownership contract",
    )
    text = replace_once(
        text,
        'assert "strictIdentityScore" in engine\n',
        'assert "strictIdentityScore" not in engine\nassert "scoreCatalogueItem" in engine\n',
        "Purstream engine identity ownership contract",
    )
    write(path, text)


def patch_identity_input_contracts() -> None:
    # Catalogue metadata requires title/type. Year is optional evidence consumed
    # only by the Core when the actual request is a movie.
    for path in ("scripts/materialize_provider_v3_all.py", "scripts/provider_base_store.py"):
        text = read(path)
        old = '["title", "year", "mediaType"]'
        count = text.count(old)
        if count < 1:
            raise AssertionError(f"{path}: no legacy catalogue requiredFields")
        text = text.replace(old, '["title", "mediaType"]')
        write(path, text)


def patch_runtime_media_safety() -> None:
    path = "scripts/provider_patches/runtime_capability_media_safety_v4.py"
    text = read(path)
    text = text.replace(
        "- Known same-title/release collision fixtures are enforced statically on every\n  returned row. Ambiguous rows fail closed rather than being shown as wrong media.\n- Explicit season/episode tokens that contradict the requested route are rejected.\n",
        "- Identity acceptance is not owned here. Title/type/IDs/year/season/episode\n  contradictions are exclusively owned by CORE.STREAM_IDENTITY.V1.\n",
    )
    text = replace_once(
        text,
        'COLLISION_FIXTURES = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"\n',
        "",
        "remove media safety collision fixture path",
    )
    start = 'def _collision_policy() -> dict[str, dict[str, Any]]:\n'
    end = "WRAPPER = r'''\n"
    text = remove_block(text, start, end, "remove media safety collision policy")
    text = replace_once(
        text,
        '  function norm(v){var x=s(v);try{if(typeof x.normalize==="function")x=x.normalize("NFD").replace(/[\\u0300-\\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}\n',
        "",
        "remove media safety identity normalizer",
    )
    text = replace_once(
        text,
        'q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;q.year=Number(q.year||q.releaseYear||0)||0;q.title=s(q.title||q.name||"");return q}',
        'q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}',
        "media safety request context excludes identity year/title",
    )
    identity_blob = '  function identityBlob(row){return[row&&row.title,row&&row.name,row&&row.filename,row&&row.description,row&&row.mediaHint].map(s).filter(Boolean).join(" ")}\n'
    static_start = text.find(identity_blob)
    static_end_marker = '  function rowHeaders(row,range){'
    static_end = text.find(static_end_marker, static_start)
    if static_start < 0 or static_end < 0:
        raise AssertionError("media safety local identity block missing")
    replacement = '  function staticSafety(row){if(!row||typeof row!=="object")return{keep:false,reason:"invalid_row"};var obvious=obviousNonMedia(row);if(obvious)return{keep:false,reason:obvious};return{keep:true}}\n'
    text = text[:static_start] + replacement + text[static_end:]
    text = replace_once(
        text,
        'var staticRows=x.list.filter(function(row){return staticSafety(row,q).keep});',
        'var staticRows=x.list.filter(function(row){return staticSafety(row).keep});',
        "media safety static filter media-only",
    )
    text = replace_once(
        text,
        '        "collisionFixtures": _collision_policy(),\n',
        "",
        "remove media safety collision config",
    )
    text = replace_once(
        text,
        '        "implementationRevision": "field-safety-v7-stream-scoped-p2p-vod-duration",',
        '        "implementationRevision": "field-safety-v8-media-only-p2p-vod-duration",',
        "media safety revision v8",
    )
    for forbidden in (
        "routeIdentity(", "identityBlob(", "explicitYears(", "wrong_release_year",
        "season_episode_identity_mismatch", "collisionFixtures",
    ):
        if forbidden in text:
            raise AssertionError(f"runtime media safety retained identity policy: {forbidden}")
    write(path, text)

    overrides_path = ROOT / "provider-overrides.json"
    data = json.loads(overrides_path.read_text(encoding="utf-8"))
    policy = data.get("runtime_capability_media_safety")
    if not isinstance(policy, dict):
        raise AssertionError("runtime_capability_media_safety policy missing")
    policy["version"] = 8
    policy["identity_owner"] = "CORE.STREAM_IDENTITY.V1"
    policy["scope"] = "all_published_providers_media_playability_only"
    overrides_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_runtime_media_safety_test() -> None:
    path = "tests/runtime_capability_media_safety_v4_test.py"
    text = read(path)
    text = text.replace('"field-safety-v7-stream-scoped-p2p-vod-duration"', '"field-safety-v8-media-only-p2p-vod-duration"')
    # Remove obsolete collision-policy assertions.
    policy_start = 'policy = module._collision_policy()\n'
    legacy_comment = '# Any old published wrapper is replaced, never stacked.\n'
    text = remove_block(text, policy_start, legacy_comment, "remove media safety collision assertions")
    # Remove old year/episode identity tests; these belong to STREAM_IDENTITY.
    collision_start = '# 5.20.70 regression: known same-title remakes/collisions are now fail-closed in\n'
    remote_start = '# Non-native/web-like runtime keeps bounded remote validation.\n'
    text = remove_block(text, collision_start, remote_start, "move collision/episode identity tests out of media safety")
    # Add explicit ownership assertions after revision assertion.
    anchor = 'assert \'"implementationRevision":"field-safety-v8-media-only-p2p-vod-duration"\' in streamzo\n'
    ownership = '''assert "routeIdentity(" not in streamzo\nassert "wrong_release_year" not in streamzo\nassert "season_episode_identity_mismatch" not in streamzo\nassert "collisionFixtures" not in streamzo\n'''
    text = replace_once(text, anchor, anchor + ownership, "media safety ownership assertions")
    write(path, text)


def patch_workflow_gate() -> None:
    path = ".github/workflows/github-actions-gate.yml"
    text = read(path)
    anchor = "          python3 tests/priority_tv_year_domain_refresh_test.py\n"
    addition = "          python3 tests/provider_js_lego_ownership_test.py\n"
    if addition not in text:
        text = replace_once(text, anchor, anchor + addition, "Workflow Gate Lego ownership test")
    write(path, text)


def validate_source_state() -> None:
    purstream = read("engine_v2/providers/purstream.mjs")
    safety = read("scripts/provider_patches/runtime_capability_media_safety_v4.py")
    base = read("scripts/provider_base_store.py")
    materializer = read("scripts/materialize_provider_v3_all.py")
    assert "strictIdentityScore" not in purstream
    assert "scoreCatalogueItem" in purstream
    for forbidden in ("routeIdentity(", "wrong_release_year", "season_episode_identity_mismatch", "collisionFixtures"):
        assert forbidden not in safety, forbidden
    assert '["title", "year", "mediaType"]' not in base
    assert '["title", "year", "mediaType"]' not in materializer
    assert '["title", "mediaType"]' in base
    assert '["title", "mediaType"]' in materializer


def main() -> int:
    patch_engine_policy()
    patch_purstream_adapter()
    patch_purstream_test()
    patch_purstream_contract()
    patch_identity_input_contracts()
    patch_runtime_media_safety()
    patch_runtime_media_safety_test()
    patch_workflow_gate()
    validate_source_state()
    print("CORE_IDENTITY_OWNERSHIP_CLEANUP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
