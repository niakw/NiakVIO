#!/usr/bin/env python3
"""External identity route V11.1.

Runs the V11 proof/recovery/materializer migrations, but owns the ProviderBase
patch with the redundant Python-only runtime-route anchor removed. `/series/...`
already classifies as a detail route, so adding `{imdbId}` to that unrelated
selector was both unnecessary and the source of the V11 pre-network failure.
"""
from __future__ import annotations

import upgrade_provider_external_identity_route_v11 as v11


def patch_base_fixed() -> bool:
    text = v11.BASE.read_text(encoding="utf-8")
    if v11.BASE_MARKER in text:
        v11.validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V10" not in text:
        raise AssertionError("external identity V11.1 requires Source Plan V10 ProviderBase first")

    text = v11.once(
        text,
        '''        "proofSearchBases": [
            str(value).strip()
            for value in incoming_model.get("proofSearchBases") or []
            if _provider_data_url_is_executable(value)
        ][:6],
        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),
''',
        '''        "proofSearchBases": [
            str(value).strip()
            for value in incoming_model.get("proofSearchBases") or []
            if _provider_data_url_is_executable(value)
        ][:6],
        "proofDetailBases": [
            str(value).strip()
            for value in incoming_model.get("proofDetailBases") or []
            if _provider_data_url_is_executable(value)
        ][:6],
        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),
''',
        "base-data-proof-detail-bases",
    )
    text = v11.once(
        text,
        '''function _runtimeBases() {
  return _uniq([..._searchBases(), ..._apiBases()]);
}''',
        '''function _runtimeBases() {
  return _uniq([
    ...(Array.isArray(NIAKVIO_PROVIDER_MODEL.proofDetailBases) ? NIAKVIO_PROVIDER_MODEL.proofDetailBases : []),
    ..._searchBases(),
    ..._apiBases()
  ].map(_substituteDomain));
}''',
        "base-proof-detail-runtime-priority",
    )
    text = v11.once(
        text,
        '''  const id = _text(meta && meta.tmdbId);
  const title = _text(meta && meta.title);
''',
        '''  const id = _text(meta && meta.tmdbId);
  const imdbId = _text(meta && meta.imdbId);
  const title = _text(meta && meta.title);
''',
        "base-learned-imdb-value",
    )
    text = v11.once(
        text,
        '''  route = route.replace(/\\{tmdb_?id\\}/gi, encodeURIComponent(id));
  // {id} has no universal meaning across providers.
''',
        '''  route = route.replace(/\\{tmdb_?id\\}/gi, encodeURIComponent(id));
  route = route.replace(/\\{imdb_?id\\}/gi, encodeURIComponent(imdbId));
  // {id} has no universal meaning across providers.
''',
        "base-expand-imdb-learned-route",
    )
    text = v11.once(
        text,
        '''  if (/\\{(?:tmdb_?id|id|slug|title)\\}/i.test(value) || /\\/(?:title|movie|film|series|tv|show|watch|media)(?:[/?#]|$)/i.test(value)) return "detail";
''',
        '''  if (/\\{(?:tmdb_?id|imdb_?id|id|slug|title)\\}/i.test(value) || /\\/(?:title|movie|film|series|tv|show|watch|media)(?:[/?#]|$)/i.test(value)) return "detail";
''',
        "base-route-kind-imdb",
    )

    anchor = '''  // Slug-driven catalogues (Sekai and similar) do not expose a search endpoint.
  // Generate only deterministic title slugs from Core metadata.
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
'''
    replacement = '''  // NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11
  // External-ID catalogues may have no title search endpoint. Core already owns
  // TMDB -> IMDb metadata resolution, so execute only routes whose `{imdbId}`
  // placeholder was proof-derived from a prior response.
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
  if (meta && meta.imdbId) {
    for (const route of detailRoutes) {
      if (!/\\{imdb_?id\\}/i.test(route)) continue;
      out.push(..._spv4Expand(route, meta, {}, mediaType, season, episode));
    }
  }
  // Slug-driven catalogues (Sekai and similar) do not expose a search endpoint.
  // Generate only deterministic title slugs from Core metadata.
'''
    text = v11.once(text, anchor, replacement, "base-external-id-detail-plan")
    v11.BASE.write_text(text, encoding="utf-8")
    v11.validate_base(text)
    return True


def main() -> int:
    changed = (
        v11.patch_worker()
        | v11.patch_proof()
        | v11.patch_recovery()
        | v11.patch_materializer()
        | patch_base_fixed()
    )
    v11.validate_worker()
    v11.validate_proof()
    v11.validate_recovery()
    v11.validate_materializer()
    v11.validate_base()
    print(
        f"PROVIDER_EXTERNAL_IDENTITY_ROUTE_V11_1_OK changed={str(changed).lower()} "
        "redundant_anchor_removed=1 imdb_hint=1 generic_imdb_id_reclassified=1 "
        "provider_id_separation=1 literal_imdb_fail_closed=1 imdb_placeholder=1 "
        "proof_detail_base=1 source_plan_external_id=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
