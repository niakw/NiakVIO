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
    changed = False

    replacements = (
        (
            "value[0].canonicalMediaType!=='anime'||value[0].mediaType!=='anime'",
            "value[0].canonicalMediaType!=='anime'||value[0].mediaType!=='tv'",
        ),
        (
            'value[0].mediaType!=="anime"||value[0].degraded!==true',
            'value[0].mediaType!=="tv"||value[0].degraded!==true',
        ),
        (
            'throw new Error("Anime-only provider must preserve anime transport on metadata outage")',
            'throw new Error("Anime-only series fallback must preserve TV transport on metadata outage")',
        ),
        (
            'assert \'"revision":"tmdb-data-contract-launch-gate-v26-authoritative-context-reconcile"\' in default_budget',
            'assert \'"revision":"tmdb-data-contract-launch-gate-v27-anime-semantic-transport"\' in default_budget',
        ),
    )
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
            changed = True

    movie_marker = "anime movie semantic/transport split failed"
    if movie_marker not in text:
        anchor = 'anime_only = mod.apply(BASE, options={"semantic_types": ["anime"]})\n'
        if text.count(anchor) != 1:
            raise AssertionError("anime-only runtime test anchor drifted")
        block = r'''# Anime is a semantic catalogue family. An animated TMDB movie must therefore
# launch an anime-only provider through the real movie namespace rather than
# being filtered out by client/provider capability plumbing.
anime_movie = mod.apply(BASE, options={"semantic_types": ["anime"]})
run_case(anime_movie, r"""
let calls=0;
global.fetch=async(url)=>{
  calls++;
  if(!String(url).includes('/movie/900001?'))throw new Error('unexpected TMDB endpoint '+url);
  return{ok:true,status:200,json:async()=>({
    id:900001,title:'Synthetic Anime Movie',genres:[{id:16,name:'Animation'}],
    original_language:'ja',production_countries:[{iso_3166_1:'JP'}],keywords:{keywords:[{name:'anime'}]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('900001','movie',null,null);
  if(!Array.isArray(value)||!value.length)throw new Error('anime movie result lost');
  if(value[0].canonicalMediaType!=='anime'||value[0].mediaType!=='movie')
    throw new Error('anime movie semantic/transport split failed: '+JSON.stringify(value));
  if(calls!==1)throw new Error('anime movie must be TMDB-verified exactly once');
})().catch(e=>{console.error(e);process.exit(1)});
""")

'''
        text = text.replace(anchor, block + anchor, 1)
        changed = True

    required = (
        "value[0].canonicalMediaType!=='anime'||value[0].mediaType!=='tv'",
        'value[0].mediaType!=="tv"||value[0].degraded!==true',
        '"revision":"tmdb-data-contract-launch-gate-v27-anime-semantic-transport"',
        movie_marker,
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"missing anime semantic/transport runtime assertion: {needle}")

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
