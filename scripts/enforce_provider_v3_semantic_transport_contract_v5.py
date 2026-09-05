#!/usr/bin/env python3
"""Enforce the Provider v3 semantic/transport split for anime catalogues.

Canonical provider capability answers *what content the provider serves*.
Transport capability answers *which Nuvio/TMDB namespace can launch it*.
Every provider whose canonical catalogue includes ``anime`` keeps that semantic
capability while accepting the real TV/movie transport namespace needed by Nuvio.
Authoritative TMDB metadata still decides whether the work is anime before the
semantic gate lets an anime-only catalogue serve a TV/movie-shaped request.

This migration is deliberately idempotent. It patches NiakVIO-owned source,
normalizes current manifest projections from provider_catalog.json semantics,
and validates runtime regression expectations without rewriting the test suite.
"""
from __future__ import annotations

import json
from pathlib import Path

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


def anime_transport(canonical: list[str]) -> list[str]:
    wanted = list(canonical)
    if "anime" not in wanted:
        return wanted
    for compatible in ("tv", "movie"):
        if compatible not in wanted:
            wanted.append(compatible)
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
        canonical = normalized_types(
            scraper.get("canonicalSupportedTypes") or scraper.get("supportedTypes")
        )
        if not canonical:
            raise AssertionError(f"provider_catalog.json:{provider_id}: missing canonical media types")
        result[provider_id] = canonical
    if len(result) != 96:
        raise AssertionError(f"provider_catalog.json semantic rows={len(result)} expected=96")
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
    path = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
    text = path.read_text(encoding="utf-8")
    changed = False
    old = '''function providerTransport(canonical,namespace){
  var map=c.requestTypeAliases&&typeof c.requestTypeAliases==="object"?c.requestTypeAliases:{};
  var mapped=s(map[canonical]).toLowerCase();
  if(mapped==="tmdb_namespace")return namespace==="movie"?"movie":"tv";
  if(mapped)return alias(mapped);
  var semantic=rows(c.semanticTypes).map(function(x){return s(x).toLowerCase()});
  if(canonical==="anime"){
    var ns=namespace==="movie"?"movie":"tv";
    if(semantic.indexOf(ns)>=0)return ns;
    return"anime";
  }
  return canonical==="movie"?"movie":"tv";
}'''
    new = '''function providerTransport(canonical,namespace){
  var map=c.requestTypeAliases&&typeof c.requestTypeAliases==="object"?c.requestTypeAliases:{};
  var mapped=s(map[canonical]).toLowerCase();
  if(mapped==="tmdb_namespace")return namespace==="movie"?"movie":"tv";
  if(mapped)return alias(mapped);
  // Anime is semantic, not a TMDB namespace. Once authoritative metadata has
  // classified the work as anime, preserve its real TV/movie namespace for the
  // provider API. The semantic capability gate still rejects non-anime works.
  if(canonical==="anime")return namespace==="movie"?"movie":"tv";
  return canonical==="movie"?"movie":"tv";
}'''
    if new not in text:
        if text.count(old) != 1:
            raise AssertionError("Core anime transport source shape drifted")
        text = text.replace(old, new, 1)
        changed = True
    old_revision = '"revision": "tmdb-data-contract-launch-gate-v26-authoritative-context-reconcile",'
    new_revision = '"revision": "tmdb-data-contract-launch-gate-v27-anime-semantic-transport",'
    if new_revision not in text:
        if text.count(old_revision) != 1:
            raise AssertionError("Core media revision source shape drifted")
        text = text.replace(old_revision, new_revision, 1)
        changed = True
    path.write_text(text, encoding="utf-8")
    return changed


def patch_materializer() -> bool:
    path = ROOT / "scripts" / "materialize_provider_v3_all.py"
    text = path.read_text(encoding="utf-8")
    changed = False
    old_marker = '''def normalize_anime_transport_compatibility(entry: dict[str, Any]) -> bool:
    """Keep anime semantic identity while exposing Nuvio TV/movie launch lanes."""
    canonical = []
    for value in entry.get("canonicalSupportedTypes") or []:
        item = str(value or "").strip().casefold()
        if item in {"movie", "tv", "anime"} and item not in canonical:
            canonical.append(item)
    if set(canonical) != {"anime"}:
        return False
    wanted = ["anime", "tv", "movie"]
    current = [str(value or "").strip().casefold() for value in entry.get("supportedTypes") or []]
    if current == wanted and canonical == ["anime"]:
        return False
    entry["canonicalSupportedTypes"] = ["anime"]
    entry["supportedTypes"] = wanted
    return True


'''
    marker = '''def normalize_anime_transport_compatibility(entry: dict[str, Any]) -> bool:
    """Preserve explicit anime semantics while exposing Nuvio TV/movie launch lanes."""
    canonical = []
    for value in entry.get("canonicalSupportedTypes") or []:
        item = str(value or "").strip().casefold()
        if item in {"movie", "tv", "anime"} and item not in canonical:
            canonical.append(item)
    if "anime" not in canonical:
        return False
    wanted = list(canonical)
    for compatible in ("tv", "movie"):
        if compatible not in wanted:
            wanted.append(compatible)
    current = [
        str(value or "").strip().casefold()
        for value in entry.get("supportedTypes") or []
        if str(value or "").strip().casefold() in {"movie", "tv", "anime"}
    ]
    if current == wanted and entry.get("canonicalSupportedTypes") == canonical:
        return False
    entry["canonicalSupportedTypes"] = canonical
    entry["supportedTypes"] = wanted
    return True


'''
    anchor = 'def base_version(value: object) -> str:\n'
    if marker not in text:
        if old_marker in text:
            text = text.replace(old_marker, marker, 1)
            changed = True
        else:
            if text.count(anchor) != 1:
                raise AssertionError("materializer anime compatibility anchor drifted")
            text = text.replace(anchor, marker + anchor, 1)
            changed = True
    call = '''        normalize_anime_transport_compatibility(entry)
        provider_id = canonical_id(str(entry.get("id") or ""))
'''
    old_call = '        provider_id = canonical_id(str(entry.get("id") or ""))\n'
    if call not in text:
        if text.count(old_call) != 1:
            raise AssertionError("materializer provider loop source shape drifted")
        text = text.replace(old_call, call, 1)
        changed = True
    path.write_text(text, encoding="utf-8")
    return changed


def patch_runtime_regression_expectations() -> bool:
    """Validate the current test contract; never rewrite tests from a migration."""
    path = ROOT / "tests" / "global_media_type_resolution_test.py"
    text = path.read_text(encoding="utf-8")
    required = (
        "global.TMDB_API_KEY='0123456789abcdef0123456789abcdef'",
        "anime semantic/TV transport split failed",
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
        if "anime" not in canonical:
            continue
        wanted = anime_transport(canonical)
        current_transport = normalized_types(entry.get("supportedTypes"))
        current_canonical = normalized_types(entry.get("canonicalSupportedTypes"))
        if current_transport != wanted or current_canonical != canonical:
            entry["canonicalSupportedTypes"] = canonical
            entry["supportedTypes"] = wanted
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
        + " manifest_anime_rows_normalized="
        + json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
