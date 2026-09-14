#!/usr/bin/env python3
"""One-shot repair for anime semantic gating and artificial movie capabilities.

Policy:
- anime-first providers are semantic ``anime`` only;
- ``tv`` is a Nuvio transport alias, never a semantic live-action capability;
- ``movie`` is never manufactured for anime-first providers;
- ambiguous tv/movie transport is canonically classified before provider network.

This migration edits NiakVIO-owned source/data only. It does not bypass provider
anti-bot/authentication controls and does not weaken terminal validation.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
PROBE = ROOT / "scripts/field_priority_probe.py"
OVERRIDES = ROOT / "provider-overrides.json"
CATALOG = ROOT / "provider_catalog.json"
MANIFEST = ROOT / "manifest.json"
TEST = ROOT / "tests/global_media_type_pre_network_gate_test.py"

ANIME_FIRST = {
    "anime-sama", "anikototv", "animekai", "animesalt", "animesama-co",
    "animesultra", "animetsu", "animevostfr", "french-manga", "kurage",
    "mugiwarastream", "neko-sama", "sekai", "voiranime", "voiranime-homes",
    "voiranime-rip", "vostfree", "allanime", "anime-ultime", "animevost-fr",
    "fullanime",
}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one old source shape, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def patch_core() -> bool:
    text = CORE.read_text(encoding="utf-8")
    changed = False
    old_rev = '"revision": "tmdb-data-contract-launch-gate-v33-25s-isolated-failfast",'
    new_rev = '"revision": "tmdb-data-contract-launch-gate-v34-anime-pre-network-semantic-gate",'
    if new_rev not in text:
        if text.count(old_rev) != 1:
            raise AssertionError("Core media revision drifted")
        text = text.replace(old_rev, new_rev, 1)
        changed = True

    anchor = '''function hasResolvedTmdbMetadata(args){
  try{return !!(args&&args.__nuvioContext&&args.__nuvioContext.tmdbMetadata)}catch(_){return false}
}

async function resolve(a){'''
    replacement = '''function hasResolvedTmdbMetadata(args){
  try{return !!(args&&args.__nuvioContext&&args.__nuvioContext.tmdbMetadata)}catch(_){return false}
}
function requiresSemanticPreflight(a){
  var first=a[0],obj=objectRequest(first),q=obj?first:null;
  var input=obj?s(q.mediaType||q.type||q.category||"movie"):s(a[1]||"movie");
  var raw=s(input).toLowerCase(),transport=alias(input);
  var semantic=rows(c.semanticTypes).map(function(x){return s(x).toLowerCase()});
  if(!semantic.length||raw==="anime"||semantic.indexOf("anime")<0)return false;
  var namespace=transport==="movie"?"movie":"tv";
  // Anime is a semantic class carried through movie/tv transport. If anime is
  // the only semantic reason this provider could accept this namespace, classify
  // the work before touching provider network. This stops live-action titles
  // from consuming an anime provider's whole execution budget.
  return semantic.indexOf(namespace)<0;
}

async function resolve(a){'''
    if replacement not in text:
        if text.count(anchor) != 1:
            raise AssertionError("Core preflight insertion anchor drifted")
        text = text.replace(anchor, replacement, 1)
        changed = True

    old = '''      var verified=null,preResolved=null;
      var needsPlanMetadata=providerNeedsTmdbBeforeStreams(o);
      var needsIdNormalization=requestHasExternalIdentity(originalArgs);
      if(needsPlanMetadata||needsIdNormalization){
        preResolved=await resolve(originalArgs);
        if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];
        if(preResolved&&!deadlineExpired(requestDeadline)&&hasResolvedTmdbMetadata(preResolved)){
          verified=preResolved;
          if(verified.__nuvioContext)verified.__nuvioContext.requestToken=requestToken;
          if(g)g.__nuvioMediaContext=verified.__nuvioContext||null;
          a=verified;
        }
      }
'''
    new = '''      var verified=null,preResolved=null;
      var needsPlanMetadata=providerNeedsTmdbBeforeStreams(o);
      var needsIdNormalization=requestHasExternalIdentity(originalArgs);
      var needsSemanticPreflight=requiresSemanticPreflight(originalArgs);
      if(needsPlanMetadata||needsIdNormalization||needsSemanticPreflight){
        preResolved=await resolve(originalArgs);
        if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];
        // Ambiguous anime-via-tv/movie transport is fail-closed before provider
        // network unless canonical metadata positively classifies the work.
        if(needsSemanticPreflight&&(!preResolved||!hasResolvedTmdbMetadata(preResolved)))return [];
        if(preResolved&&!deadlineExpired(requestDeadline)&&hasResolvedTmdbMetadata(preResolved)){
          verified=preResolved;
          if(verified.__nuvioContext)verified.__nuvioContext.requestToken=requestToken;
          if(g)g.__nuvioMediaContext=verified.__nuvioContext||null;
          a=verified;
        }
      }
'''
    if new not in text:
        if text.count(old) != 1:
            raise AssertionError("Core pre-resolution block drifted")
        text = text.replace(old, new, 1)
        changed = True
    CORE.write_text(text, encoding="utf-8")
    return changed


def patch_probe() -> bool:
    old = '''def supports(row: dict[str, Any], fixture: dict[str, Any]) -> bool:
    types = {canonical(value) for value in row.get("supportedTypes") or []}
    media_type = canonical(fixture["mediaType"])
    if media_type == "anime":
        return "anime" in types
    return media_type in types
'''
    new = '''def supports(row: dict[str, Any], fixture: dict[str, Any]) -> bool:
    # canonicalSupportedTypes is semantic authority. supportedTypes may contain
    # Nuvio transport aliases such as anime -> tv and must not schedule an
    # anime-only provider against arbitrary live-action TV.
    semantic = row.get("canonicalSupportedTypes")
    if not isinstance(semantic, list) or not semantic:
        semantic = row.get("supportedTypes") or []
    types = {canonical(value) for value in semantic}
    media_type = canonical(fixture["mediaType"])
    return media_type in types
'''
    return replace_once(PROBE, old, new, "short probe semantic filter")


def prune_anime(values: object) -> list[str]:
    return [str(v) for v in values if cid(v) == "anime"] if isinstance(values, list) else []


def normalize_overrides() -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = data.get("provider_patches") or {}
    missing = sorted(provider_id for provider_id in ANIME_FIRST if provider_id not in patches)
    if missing:
        raise AssertionError("anime-first overrides missing: " + ",".join(missing))
    changed = 0
    for provider_id in sorted(ANIME_FIRST):
        row = patches[provider_id]
        if row.get("published_types") != ["anime"]:
            row["published_types"] = ["anime"]
            changed += 1
        notes = [str(v) for v in row.get("notes") or [] if str(v)]
        note = "Authoritative semantic contract is anime-only; tv is transport compatibility and movie must never be manufactured for anime-first providers."
        if note not in notes:
            notes.append(note)
            row["notes"] = notes
            changed += 1

        # Prune stale lane metadata, but deliberately preserve activation/repair
        # state. A semantic migration is not playback proof.
        disp = row.get("repair_disposition")
        if isinstance(disp, dict):
            if disp.get("requiredLanes") != ["anime"]:
                disp["requiredLanes"] = ["anime"]
                changed += 1
            for key in ("currentVerifiedLanes", "exactLockedLanes", "provenLanes", "missingLanes"):
                values = disp.get(key)
                if isinstance(values, list):
                    wanted = prune_anime(values)
                    if values != wanted:
                        disp[key] = wanted
                        changed += 1
            statuses = disp.get("laneStatuses")
            if isinstance(statuses, dict):
                wanted_statuses = {"anime": statuses.get("anime", [])}
                if statuses != wanted_statuses:
                    disp["laneStatuses"] = wanted_statuses
                    changed += 1

        gate = row.get("live_route_gate")
        if isinstance(gate, dict):
            for key in ("required_types", "validated_types", "missing_types"):
                values = gate.get(key)
                if isinstance(values, list):
                    wanted = ["anime"] if key == "required_types" else prune_anime(values)
                    if values != wanted:
                        gate[key] = wanted
                        changed += 1

        proof = row.get("route_proof")
        if isinstance(proof, dict) and isinstance(proof.get("runtimePlanSemanticLanes"), list):
            values = proof["runtimePlanSemanticLanes"]
            wanted = prune_anime(values)
            if values != wanted:
                proof["runtimePlanSemanticLanes"] = wanted
                changed += 1

    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def normalize_catalog_and_manifest() -> tuple[int, int]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog_changed = 0
    seen: set[str] = set()
    for provider in catalog.get("providers") or []:
        if not isinstance(provider, dict):
            continue
        scraper = provider.get("scraper") if isinstance(provider.get("scraper"), dict) else {}
        provider_id = cid(provider.get("canonicalId") or scraper.get("id"))
        if provider_id not in ANIME_FIRST:
            continue
        if scraper.get("supportedTypes") != ["anime"]:
            scraper["supportedTypes"] = ["anime"]
            catalog_changed += 1
        if "canonicalSupportedTypes" in scraper and scraper.get("canonicalSupportedTypes") != ["anime"]:
            scraper["canonicalSupportedTypes"] = ["anime"]
            catalog_changed += 1
        seen.add(provider_id)
    if seen != ANIME_FIRST:
        raise AssertionError("catalog anime-first scope mismatch missing=" + ",".join(sorted(ANIME_FIRST - seen)))
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_changed = 0
    seen_manifest: set[str] = set()
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = cid(row.get("id"))
        if provider_id not in ANIME_FIRST:
            continue
        if row.get("canonicalSupportedTypes") != ["anime"]:
            row["canonicalSupportedTypes"] = ["anime"]
            manifest_changed += 1
        if row.get("supportedTypes") != ["anime", "tv"]:
            row["supportedTypes"] = ["anime", "tv"]
            manifest_changed += 1
        seen_manifest.add(provider_id)
    if seen_manifest != ANIME_FIRST:
        raise AssertionError("manifest anime-first scope mismatch missing=" + ",".join(sorted(ANIME_FIRST - seen_manifest)))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return catalog_changed, manifest_changed


def patch_test() -> bool:
    text = TEST.read_text(encoding="utf-8")
    changed = False
    old_comment = '''# But a semantic-anime provider must still be allowed to provisionally accept a
# movie transport because an anime work may genuinely live in TMDB movie space.
'''
    new_comment = '''# A semantic-anime provider may accept movie transport only after canonical
# TMDB metadata has positively classified the work as anime. Provider execution
# must happen after that metadata preflight, never before it.
'''
    if old_comment in text:
        text = text.replace(old_comment, new_comment, 1)
        changed = True

    marker = "print('global media fast gate passed: movie<->tv and explicit anime mismatches reject before provider/TMDB network')\n"
    block = r"""
# Ambiguous anime-via-TV/movie transport must classify before provider network.
# Live-action metadata therefore stops an anime-only provider at the Core gate.
def assert_live_action_stops_anime_provider(media_type: str, tmdb_id: str, label: str) -> None:
    patched = mod.apply(BASE, options={"semantic_types": ["anime"]})
    endpoint = "/movie/" if media_type == "movie" else "/tv/"
    run_case(
        patched,
        f'''
let fetchCalls=0;
global.__providerCalls=0;
global.fetch=async(url)=>{{
  fetchCalls++;
  if(!String(url).includes('{endpoint}{tmdb_id}?'))throw new Error('{label}: expected TMDB semantic preflight, got '+url);
  return {{ok:true,status:200,json:async()=>({{
    id:Number('{tmdb_id}'),genres:[{{id:18,name:'Drama'}}],original_language:'en',
    origin_country:['US'],production_countries:[{{iso_3166_1:'US'}}],keywords:{{results:[]}}
  }})}};
}};
const provider=require(process.argv[2]);
(async()=>{{
  const value=await provider.getStreams('{tmdb_id}','{media_type}',1,1);
  if(!Array.isArray(value)||value.length!==0)throw new Error('{label}: live-action must return []');
  if(global.__providerCalls!==0)throw new Error('{label}: anime provider touched live-action network path: '+global.__providerCalls);
  if(fetchCalls!==1)throw new Error('{label}: expected exactly one TMDB preflight: '+fetchCalls);
}})().catch(e=>{{console.error(e);process.exit(1)}});
''',
    )


assert_live_action_stops_anime_provider("movie", "157336", "Interstellar")
assert_live_action_stops_anime_provider("tv", "94997", "House of the Dragon")

print('global media fast gate passed: semantic anime preflight blocks live-action before provider network')
"""
    if "assert_live_action_stops_anime_provider" not in text:
        if marker not in text:
            raise AssertionError("global media test footer drifted")
        text = text.replace(marker, block, 1)
        changed = True
    TEST.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    result = {
        "core": patch_core(),
        "probe": patch_probe(),
        "overrides": normalize_overrides(),
        "catalog_manifest": normalize_catalog_and_manifest(),
        "test": patch_test(),
    }
    print("ANIME_SEMANTIC_GATE_REPAIR_OK " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
