#!/usr/bin/env python3
"""External identity route V11.1.

Runs the V11 proof/recovery/materializer migrations, but owns two corrected
portfolio boundaries:
- ProviderBase patching uses stable runtime anchors only;
- metadata helper hosts remain route evidence but can never enter executionRoutes.

`/series/...` already classifies as a detail route, so adding `{imdbId}` to an
unrelated Python selector was unnecessary and caused the original V11 pre-network
failure.
"""
from __future__ import annotations

import upgrade_provider_external_identity_route_v11 as v11

EXECUTION_MARKER = "ROUTE_RECOVERY_HELPER_EVIDENCE_ONLY_V11_1"


def patch_execution_boundary() -> bool:
    text = v11.RECOVERY.read_text(encoding="utf-8")
    if EXECUTION_MARKER in text:
        validate_execution_boundary(text)
        return False
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V10" not in text:
        raise AssertionError("V11.1 helper boundary requires Source Plan V10 recovery")
    old = '''    execution_routes = unique([row.get("route") for row in deduped if generic_execution_route(row)], 192)
'''
    new = '''    # ROUTE_RECOVERY_HELPER_EVIDENCE_ONLY_V11_1
    # TMDB/Cinemeta helper calls may carry critical identity evidence (IMDb, title,
    # aliases), but they are not provider execution routes. Keep them in routeData
    # and proven routes for causality while excluding them from the runtime plan.
    execution_routes = unique([
        row.get("route") for row in deduped
        if _repair_recipe_origin_allowed(row) and generic_execution_route(row)
    ], 192)
'''
    text = v11.once(text, old, new, "helper-evidence-execution-boundary")
    v11.RECOVERY.write_text(text, encoding="utf-8")
    validate_execution_boundary(text)
    return True


def validate_execution_boundary(text: str | None = None) -> None:
    value = text if text is not None else v11.RECOVERY.read_text(encoding="utf-8")
    for needle in (
        EXECUTION_MARKER,
        "if _repair_recipe_origin_allowed(row) and generic_execution_route(row)",
    ):
        if needle not in value:
            raise AssertionError(f"V11.1 execution boundary missing: {needle}")


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
''',
        '''  route = route.replace(/\\{tmdb_?id\\}/gi, encodeURIComponent(id));
  route = route.replace(/\\{imdb_?id\\}/gi, encodeURIComponent(imdbId));
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
    changed = v11.patch_worker() | v11.patch_proof() | v11.patch_recovery()
    changed |= patch_execution_boundary()
    changed |= v11.patch_materializer() | patch_base_fixed()
    v11.validate_worker()
    v11.validate_proof()
    v11.validate_recovery()
    validate_execution_boundary()
    v11.validate_materializer()
    v11.validate_base()
    print(
        f"PROVIDER_EXTERNAL_IDENTITY_ROUTE_V11_1_OK changed={str(changed).lower()} "
        "redundant_anchor_removed=1 helper_routes_evidence_only=1 imdb_hint=1 "
        "generic_imdb_id_reclassified=1 provider_id_separation=1 "
        "literal_imdb_fail_closed=1 imdb_placeholder=1 proof_detail_base=1 "
        "source_plan_external_id=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
