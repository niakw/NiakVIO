#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    changed = False
    if "NIAKVIO_PROVIDER_EPISODE_HOP_V24" not in text:
        old = '''  const ep = path.match(/(?:^|[-_/])(?:episode|ep)[-_ ]*0*(\\d{1,4})(?:[-_/.]|$)/i);\n  if (ep) return {\n    marked: true,\n    matches: wantedSeason === 1 && Number(ep[1]) === wantedEpisode,\n    strength: 2\n  };\n  return { marked: false, matches: false, strength: 0 };\n}\n'''
        new = '''  const ep = path.match(/(?:^|[-_/])(?:episode|ep)[-_ ]*0*(\\d{1,4})(?:[-_/.]|$)/i);\n  if (ep) return {\n    marked: true,\n    matches: wantedSeason === 1 && Number(ep[1]) === wantedEpisode,\n    strength: 2\n  };\n  /* NIAKVIO_PROVIDER_EPISODE_HOP_V24 */\n  // Season-1 anime catalogues often expose an exact episode leaf such as\n  // title-01-vostfr. The explicit language suffix is required so a year or\n  // franchise number can never be mistaken for an episode.\n  const languageEpisode = path.match(/(?:^|[-_/])0*(\\d{1,4})[-_](?:vostfr|vf|vff|vfq|vo)(?:[-_/.]|$)/i);\n  if (languageEpisode) return {\n    marked: true,\n    matches: wantedSeason === 1 && Number(languageEpisode[1]) === wantedEpisode,\n    strength: 2\n  };\n  return { marked: false, matches: false, strength: 0 };\n}\n'''
        text = replace_once(text, old, new, "season1 language episode marker")

        old = '''  const base = response.url || detailUrl;\n  if (!_strictHtmlIdentityOk(html, meta)) return [];\n\n  if (family === "dle-full-story") {\n'''
        new = '''  const base = response.url || detailUrl;\n  if (!_strictHtmlIdentityOk(html, meta)) return [];\n\n  // V24: every proof-backed HTML source family gets the same exact episodic\n  // navigation contract before family-specific extraction. This is bounded to\n  // same-origin links carrying the requested season/episode identity.\n  const exactEpisodeHop = await _spv22ResolveEpisodeHop(html, base, mediaType, season, episode);\n  if (exactEpisodeHop.length) return exactEpisodeHop.slice(0, 40);\n\n  if (family === "dle-full-story") {\n'''
        text = replace_once(text, old, new, "source family episode hop")
        changed = True

    if "NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PAYLOAD_V24_1" not in text:
        anchor = '''async function _crawlDirectMedia(seedUrls, referer, maxDepth) {\n'''
        helper = r'''/* NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PAYLOAD_V24_1 */
function _spv241ExplicitPlayerPayloadUrls(text, base) {
  const source = _text(text).slice(0, 524288);
  const out = [];
  // Decode only values explicitly handed to a video/player function. This is
  // not a generic base64 sweep and cannot turn unrelated page data into routes.
  const re = /(?:showVideo|loadVideo|setVideo|playVideo)\s*\(\s*["']([A-Za-z0-9+/_=-]{12,4096})["']\s*\)/gi;
  let match, scanned = 0;
  while ((match = re.exec(source)) !== null && scanned++ < 24) {
    let encoded = _text(match[1]).replace(/-/g, "+").replace(/_/g, "/");
    while (encoded.length % 4) encoded += "=";
    let decoded = "";
    try { decoded = atob(encoded); } catch (_) { continue; }
    if (!decoded || decoded.length > 16384) continue;
    const direct = _absolute(decoded.trim(), base);
    if (/^https?:\/\//i.test(direct)) out.push(direct);
    out.push(..._extractUrls(decoded, base));
    if (out.length >= 48) break;
  }
  return _uniq(out).slice(0, 48);
}
'''
        text = replace_once(text, anchor, helper + anchor, "explicit player payload helper")
        old = '''        const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);\n        urls = _extractUrls(decodedPlayerText, responseUrl);\n'''
        new = '''        const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);\n        urls = _uniq(_extractUrls(decodedPlayerText, responseUrl).concat(\n          _spv241ExplicitPlayerPayloadUrls(decodedPlayerText, responseUrl)\n        ));\n'''
        text = replace_once(text, old, new, "explicit payload crawl")
        changed = True

    if changed:
        BASE.write_text(text, encoding="utf-8")
    return changed


def _demote_nonterminal_tmdb_helper(patch: dict, model: dict) -> bool:
    recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else None
    if recipe is None and isinstance(model.get("apiRecipe"), dict):
        recipe = model.get("apiRecipe")
    if not isinstance(recipe, dict):
        return False
    base = str(recipe.get("base") or "").lower()
    route = str(recipe.get("directRoute") or recipe.get("searchRoute") or "").lower()
    if "arm.haglund.dev" not in base or "/api/v2/themoviedb" not in route:
        return False
    # This endpoint is metadata/helper authority, not stream authority. Retain it
    # only as candidate knowledge so the real HTML source family can execute.
    patch.setdefault("candidate_api_recipe", json.loads(json.dumps(recipe)))
    model.setdefault("candidateApiRecipe", json.loads(json.dumps(recipe)))
    patch.pop("api_recipe", None)
    model.pop("apiRecipe", None)
    return True


def patch_provider_authority(provider_id: str, site: str, aliases: list[str], *, demote_tmdb_helper: bool = False) -> bool:
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = overrides.setdefault("provider_patches", {})
    patch = patches.get(provider_id)
    if not isinstance(patch, dict):
        raise SystemExit(f"missing provider patch: {provider_id}")
    patch["official_site"] = site
    substitutions = patch.get("domain_substitutions") if isinstance(patch.get("domain_substitutions"), dict) else {}
    target_host = site.split("//", 1)[-1].split("/", 1)[0].lower()
    for alias in aliases:
        substitutions[alias.lower()] = target_host
    patch["domain_substitutions"] = substitutions
    runtime = patch.get("runtime_domain_replacements") if isinstance(patch.get("runtime_domain_replacements"), dict) else {}
    for alias in aliases:
        runtime[alias.lower()] = target_host
    patch["runtime_domain_replacements"] = runtime
    patch["proof_search_bases"] = [site]

    knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    row = (knowledge.get("providers") or {}).get(provider_id)
    if not isinstance(row, dict) or not isinstance(row.get("model"), dict):
        raise SystemExit(f"missing static model: {provider_id}")
    model = row["model"]
    model["officialSite"] = site
    model["knownSite"] = site
    model["proofSearchBases"] = [site]
    dsubs = model.get("domainSubstitutions") if isinstance(model.get("domainSubstitutions"), dict) else {}
    for alias in aliases:
        dsubs[alias.lower()] = target_host
    model["domainSubstitutions"] = dsubs
    demoted = _demote_nonterminal_tmdb_helper(patch, model) if demote_tmdb_helper else False

    patches[provider_id] = patch
    overrides["provider_patches"] = patches
    OVERRIDES.write_text(json.dumps(overrides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    row["model"] = model
    knowledge["providers"][provider_id] = row
    KNOWLEDGE.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return demoted


def main() -> int:
    changed = patch_base()
    demoted = patch_provider_authority(
        "voiranime", "https://voir-anime.to",
        ["voiranime.homes", "voiranime.store", "voiranime.com"],
        demote_tmdb_helper=True,
    )
    patch_provider_authority("wookafr", "https://wookafr.boston", ["wookafr.blog", "wookafr.center", "wookafr.app"])
    print(
        f"PROVIDER_EPISODE_HOP_V24_OK changed={str(changed).lower()} "
        f"explicit_player_payload_v24_1=true voiranime_helper_demoted={str(demoted).lower()} "
        "authorities=voiranime:voir-anime.to,wookafr:wookafr.boston"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
