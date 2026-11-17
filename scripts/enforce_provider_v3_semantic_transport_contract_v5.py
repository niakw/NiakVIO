#!/usr/bin/env python3
"""Enforce the Provider v3 semantic/transport split for anime catalogues.

Canonical provider capability answers *what content the provider serves*.
Published ``supportedTypes`` is a client selection/launch surface: an anime-only
provider may expose ``tv`` there as a compatibility launch alias without changing
the provider runtime media type. Provider runtime transport remains canonical
``movie|tv|anime`` after explicit structured ``requestTypeAliases``; TMDB identity
namespace remains independently ``movie|tv``.
Authoritative TMDB metadata still decides whether the work is anime before the
semantic gate lets an anime catalogue serve a request.

This migration is deliberately idempotent. It patches NiakVIO-owned source,
normalizes current manifest projections from provider_catalog.json semantics,
and validates runtime regression expectations without rewriting the test suite.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from current_provider_scope import projection_visible_provider_ids

from capture_tmdb_core_runtime_credential import main as capture_tmdb_core_credential
from harden_stream_presentation_metadata_fallbacks import main as harden_stream_presentation_metadata
from remove_embedded_tmdb_runtime_key_contract import main as remove_embedded_tmdb_runtime_key

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TYPES = {"movie", "tv", "anime"}


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one old source shape, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def normalized_types(values: object) -> list[str]:
    out: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = str(value or "").strip().casefold()
        if item in CANONICAL_TYPES and item not in out:
            out.append(item)
    return out


def normalized_launch_types(values: object) -> list[str]:
    out: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = str(value or "").strip().casefold()
        if item in {"movie", "tv", "anime"} and item not in out:
            out.append(item)
    return out


def project_launch_types(canonical: list[str]) -> list[str]:
    """Project semantic capability to supportedTypes launch aliases only."""
    wanted = list(canonical)
    if "anime" in canonical and "tv" not in wanted:
        wanted.append("tv")
    return wanted


def catalog_semantic_types() -> dict[str, list[str]]:
    path = ROOT / "provider_catalog.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("sourceOfTruth") is not True:
        raise AssertionError("provider_catalog.json must remain sourceOfTruth")
    result: dict[str, list[str]] = {}
    for provider in value.get("providers") or []:
        if not isinstance(provider, dict):
            continue
        scraper = provider.get("scraper")
        if not isinstance(scraper, dict):
            continue
        provider_id = str(scraper.get("id") or provider.get("canonicalId") or "").strip().casefold()
        if not provider_id:
            continue
        if "canonicalSupportedTypes" in scraper:
            raise AssertionError(
                f"provider_catalog.json:{provider_id}: canonicalSupportedTypes is manifest-only transport metadata"
            )
        canonical = normalized_types(scraper.get("supportedTypes"))
        if not canonical:
            raise AssertionError(f"provider_catalog.json:{provider_id}: missing canonical media types")
        result[provider_id] = canonical
    expected = len(projection_visible_provider_ids())
    if len(result) != expected:
        raise AssertionError(
            f"provider_catalog.json semantic rows={len(result)} expected_visible={expected}"
        )
    return result


def patch_gowaru_route_normalizer() -> bool:
    path = ROOT / "scripts" / "finalize_gowaru_provider_v3_source_plans.py"
    return replace_once(
        path,
        'value = value.strip().rstrip(";,)]}")',
        'value = value.strip().rstrip(";,)]")',
        "Gowaru route placeholder tail",
    )


def patch_media_transport() -> bool:
    """Validate the current canonical provider media ABI; never rewrite it.

    This compatibility entry point is executed by canonical reconstruction.
    Historical V27 behavior mapped canonical anime back to the TMDB movie/tv
    namespace. That is no longer provider ABI authority: Core may use the TMDB
    namespace for identity lookup, but provider transport remains canonical
    anime unless structured DATA declares an explicit requestTypeAlias.
    """
    path = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
    text = path.read_text(encoding="utf-8")
    required = (
        "/* NUVIO_GLOBAL_CANONICAL_ANIME_PROVIDER_ABI_V35 */",
        'if(mapped==="tmdb_namespace")return namespace==="movie"?"movie":"tv";',
        "if(mapped)return alias(mapped);",
        'if(canonical==="anime")return"anime";',
        '"revision": "tmdb-data-contract-launch-gate-v35-canonical-anime-provider-abi",',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"Core canonical anime provider ABI missing: {needle}")

    forbidden = (
        'if(canonical==="anime")return namespace==="movie"?"movie":"tv";',
        'if(canonical==="anime"){',
        'var ns=namespace==="movie"?"movie":"tv";',
        'if(semantic.indexOf(ns)>=0)return ns;',
    )
    provider_transport = text.split("function providerTransport(canonical,namespace){", 1)[1].split(
        "function namespaceCandidates", 1
    )[0]
    for needle in forbidden:
        if needle in provider_transport:
            raise AssertionError(
                f"historical implicit anime/TMDB provider transport returned: {needle}"
            )

    revision_match = re.search(
        r'"revision"\s*:\s*"tmdb-data-contract-launch-gate-v(\d+)-([^"]+)"',
        text,
    )
    if not revision_match or int(revision_match.group(1)) < 35:
        raise AssertionError("Core media revision predates canonical anime provider ABI v35")
    return False

def patch_materializer() -> bool:
    path = ROOT / "scripts" / "materialize_provider_v3_all.py"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"def normalize_anime_transport_compatibility\(entry: dict\[str, Any\]\) -> bool:\n"
        r".*?(?=def base_version\(value: object\) -> str:)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise AssertionError("materializer semantic/transport projector missing")
    current = match.group(0)
    required = (
        'if "anime" in canonical and "tv" not in wanted:',
        'wanted.append("tv")',
        'item in {"movie", "tv", "anime"}',
    )
    forbidden = (
        'wanted.append("series")',
        '"series"',
        'for compatible in ("tv", "movie"):',
        'wanted = ["anime", "tv", "movie"]',
    )
    if any(value not in current for value in required) or any(value in current for value in forbidden):
        raise AssertionError("materializer semantic/transport projector drifted")
    return False


def patch_runtime_regression_expectations() -> bool:
    """Validate the current test contract; never rewrite tests from a migration."""
    path = ROOT / "tests" / "global_media_type_resolution_test.py"
    text = path.read_text(encoding="utf-8")
    required = (
        "global.TMDB_API_KEY='0123456789abcdef0123456789abcdef'",
        "canonical anime provider ABI lost",
        "anime movie must keep canonical provider ABI while TMDB namespace stays movie",
        "declared anime->tv provider alias not honored",
        "non-launch must return []",
        "zero output caused TMDB work",
        "TV-only provider leaked anime",
        "TV fail-open fallback failed",
        "'\"tmdbKeyCipher\":' not in mixed",
        "'\"tmdbKeySalt\":' not in mixed",
        '"function embeddedKey" not in mixed',
        '"NiakVIO/TMDB/v1" not in mixed',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"missing current media runtime assertion: {needle}")
    return False


def normalize_manifest(path: Path, semantics: dict[str, list[str]]) -> int:
    if not path.is_file():
        return 0
    value = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for entry in value.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        canonical = list(semantics.get(provider_id) or [])
        if not canonical:
            raise AssertionError(f"{path}:{provider_id}: missing canonical semantics")
        wanted = project_launch_types(canonical)
        current_launch = normalized_launch_types(entry.get("supportedTypes"))
        current_canonical = normalized_types(entry.get("canonicalSupportedTypes"))
        if current_launch != wanted or (wanted != canonical and current_canonical != canonical):
            entry["supportedTypes"] = wanted
            if wanted != canonical or current_canonical:
                entry["canonicalSupportedTypes"] = canonical
            changed += 1
    if changed:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def embedded_tmdb_contract_already_final() -> bool:
    """Accept the current Core capability without replaying an obsolete migration."""
    path = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "RUNTIME_KEY_PATH",
        "_runtime_key_payload",
        "tmdbKeyCipher",
        "tmdbKeySalt",
        "function embeddedKey",
        "normalizeKey(embeddedKey())",
        "NiakVIO/TMDB/v1",
    )
    required = (
        "g.__nuvioCoreGetTmdbDataV1=coreGetTmdbData",
        "https://api.themoviedb.org/3/",
        "__nuvioTmdbMetadataCacheV1",
        "episode:tv:",
        "release_dates",
        "content_ratings",
    )
    return not any(needle in text for needle in forbidden) and all(needle in text for needle in required)


def main() -> int:
    if embedded_tmdb_contract_already_final():
        runtime_key_removed = True
    else:
        runtime_key_removed = remove_embedded_tmdb_runtime_key() == 0
    runtime_key_captured = capture_tmdb_core_credential() == 0
    presentation_hardened = harden_stream_presentation_metadata() == 0
    changes = {
        "tmdb_runtime_key_removed": runtime_key_removed,
        "tmdb_runtime_key_captured_in_core": runtime_key_captured,
        "stream_presentation_metadata_hardened": presentation_hardened,
        "gowaru_route_tail": patch_gowaru_route_normalizer(),
        "core_anime_transport": patch_media_transport(),
        "materializer_anime_compat": patch_materializer(),
        "runtime_expectations": patch_runtime_regression_expectations(),
    }
    semantics = catalog_semantic_types()
    normalized = {
        "general": normalize_manifest(ROOT / "manifest.json", semantics),
        "vf": normalize_manifest(ROOT / "vf" / "manifest.json", semantics),
    }
    print(
        "PROVIDER_V3_SEMANTIC_TRANSPORT_V5_OK "
        + " ".join(f"{key}={str(value).lower()}" for key, value in changes.items())
        + " manifest_rows_normalized="
        + json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
