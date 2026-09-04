#!/usr/bin/env python3
"""Enforce the Provider v3 semantic/transport split for anime catalogues.

Canonical provider capability answers *what content the provider serves*.
Transport capability answers *which Nuvio/TMDB namespace can launch it*.
An anime-only provider therefore remains canonically ``anime`` while accepting
both TV and movie transport. Authoritative TMDB metadata is still required to
prove that a TV/movie work is anime before the semantic gate lets it through.

This migration is deliberately idempotent. It patches NiakVIO-owned source,
normalizes the current manifest, and then becomes a no-op on later rebuilds.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one old source shape, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


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
    marker = '''def normalize_anime_transport_compatibility(entry: dict[str, Any]) -> bool:
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
    anchor = 'def base_version(value: object) -> str:\n'
    if marker not in text:
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
    path = ROOT / "tests" / "global_media_type_resolution_test.py"
    text = path.read_text(encoding="utf-8")
    changes = {
        'value[0].canonicalMediaType!=="anime"||value[0].mediaType!=="anime"||value[0].degraded!==true':
            'value[0].canonicalMediaType!=="anime"||value[0].mediaType!=="tv"||value[0].degraded!==true',
        "value[0].canonicalMediaType!=='anime'||value[0].mediaType!=='anime'":
            "value[0].canonicalMediaType!=='anime'||value[0].mediaType!=='tv'",
    }
    changed = False
    for old, new in changes.items():
        if new in text:
            continue
        if text.count(old) != 1:
            raise AssertionError(f"runtime anime transport expectation drifted: {old[:48]}")
        text = text.replace(old, new, 1)
        changed = True
    path.write_text(text, encoding="utf-8")
    return changed


def normalize_manifest() -> int:
    path = ROOT / "manifest.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for entry in value.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        canonical = {
            str(item or "").strip().casefold()
            for item in entry.get("canonicalSupportedTypes") or []
            if str(item or "").strip()
        }
        if canonical != {"anime"}:
            continue
        wanted = ["anime", "tv", "movie"]
        current = [str(item or "").strip().casefold() for item in entry.get("supportedTypes") or []]
        if current != wanted or entry.get("canonicalSupportedTypes") != ["anime"]:
            entry["canonicalSupportedTypes"] = ["anime"]
            entry["supportedTypes"] = wanted
            changed += 1
    if changed:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    changes = {
        "gowaru_route_tail": patch_gowaru_route_normalizer(),
        "core_anime_transport": patch_media_transport(),
        "materializer_anime_compat": patch_materializer(),
        "runtime_expectations": patch_runtime_regression_expectations(),
    }
    normalized = normalize_manifest()
    print(
        "PROVIDER_V3_SEMANTIC_TRANSPORT_V5_OK "
        + " ".join(f"{key}={str(value).lower()}" for key, value in changes.items())
        + f" manifest_anime_rows_normalized={normalized}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
