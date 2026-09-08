#!/usr/bin/env python3
"""External identity route V11: prove and replay IMDb-derived provider paths.

Some providers obtain an IMDb identity from TMDB/metadata and then address their
catalogue by `/series/tt...`. Prior route proof either froze that IMDb literal or
classified an IMDb-shaped generic `id` as a provider-internal `{id}`.

V11 is fail-closed and provider-agnostic:
- the proof worker exposes explicit IMDb keys while existing generic id hints remain;
- Python classifies any prior response value shaped `tt<digits>` as external IMDb
  identity, even when the response key is generically `id`;
- IMDb-shaped values are excluded from provider-internal ID correlation;
- an observed tt... segment is reusable only when prior response evidence proved it,
  becoming `{imdbId}`; otherwise the route is rejected as opaque fixture residue;
- the positive provider origin carrying that external-ID detail request becomes a
  proof-owned detail execution base, separate from public hub/site branding;
- ProviderBase recognizes/expands `{imdbId}` and executes those detail routes from
  Core TMDB metadata.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "provider_worker.cjs"
PROOF = ROOT / "scripts" / "provider_route_proof.py"
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MATERIALIZER = ROOT / "scripts" / "materialize_provider_v3_all.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_EXTERNAL_IDENTITY_ROUTE_V11"
WORKER_MARKER = "NUVIO_PROVIDER_WORKER_EXTERNAL_IDENTITY_HINT_V11"
PROOF_MARKER = "PROVIDER_ROUTE_PROOF_EXTERNAL_IDENTITY_V11"
RECOVERY_MARKER = "ROUTE_RECOVERY_EXTERNAL_IDENTITY_BASE_V11"
MATERIALIZER_MARKER = "PROVIDER_EXTERNAL_IDENTITY_BASE_V11"
BASE_MARKER = "NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_worker() -> bool:
    text = WORKER.read_text(encoding="utf-8")
    if WORKER_MARKER in text:
        validate_worker(text)
        return False
    if "NUVIO_PROVIDER_WORKER_ROUTE_PROOF_V1" not in text:
        raise AssertionError("external identity V11 requires route-proof worker first")
    old = '''  'movie_id', 'movieid', 'series_id', 'seriesid', 'show_id', 'showid', 'slug',
]);'''
    new = '''  'movie_id', 'movieid', 'series_id', 'seriesid', 'show_id', 'showid', 'slug',
  // NUVIO_PROVIDER_WORKER_EXTERNAL_IDENTITY_HINT_V11
  'imdb', 'imdb_id', 'imdbid',
]);'''
    text = once(text, old, new, "worker-imdb-hint-keys")
    WORKER.write_text(text, encoding="utf-8")
    validate_worker(text)
    return True


def patch_proof() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if PROOF_MARKER in text:
        validate_proof(text)
        return False

    text = once(
        text,
        '''CONTENT_IDENTITY_QUERY_KEYS = {
    "imdb", "imdbid", "imdb_id", "year", "releaseyear", "release_year",
''',
        '''# PROVIDER_ROUTE_PROOF_EXTERNAL_IDENTITY_V11
EXTERNAL_IDENTITY_HINT_KEYS = {"imdb", "imdbid", "imdb_id"}
CONTENT_IDENTITY_QUERY_KEYS = {
    "imdb", "imdbid", "imdb_id", "year", "releaseyear", "release_year",
''',
        "proof-external-id-keys",
    )

    # Generic `id: tt...` from Cinemeta is an external identity, not a provider id.
    text = once(
        text,
        '''        if key not in PROVIDER_VALUE_KEYS or not value or len(value) < 2 or len(value) > 160:
            continue
        if re.fullmatch(r"[A-Za-z0-9._~-]+", value):
            out.add(value)
''',
        '''        if key not in PROVIDER_VALUE_KEYS or not value or len(value) < 2 or len(value) > 160:
            continue
        if re.fullmatch(r"tt\\d{7,10}", value, re.I):
            continue
        if re.fullmatch(r"[A-Za-z0-9._~-]+", value):
            out.add(value)
''',
        "proof-provider-id-excludes-imdb",
    )

    anchor = "def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:\n"
    helper = '''def _external_identity_hint_values(\n    prior_value_hints: Iterable[dict[str, Any]] | None,\n) -> set[str]:\n    out: set[str] = set()\n    for row in prior_value_hints or []:\n        if not isinstance(row, dict):\n            continue\n        key = canonical(row.get("key"))\n        value = str(row.get("value") or "").strip()\n        if key not in EXTERNAL_IDENTITY_HINT_KEYS and key not in PROVIDER_VALUE_KEYS:\n            continue\n        if re.fullmatch(r"tt\\d{7,10}", value, re.I):\n            out.add(value)\n    return out\n\n\n'''
    text = once(text, anchor, helper + anchor, "proof-external-hint-helper")
    text = once(
        text,
        '''        if key in PROVIDER_VALUE_KEYS and value and len(value) <= 160:
            out.append({"key": key, "value": value})
''',
        '''        if (key in PROVIDER_VALUE_KEYS or key in EXTERNAL_IDENTITY_HINT_KEYS) and value and len(value) <= 160:
            if key in EXTERNAL_IDENTITY_HINT_KEYS and not re.fullmatch(r"tt\\d{7,10}", value, re.I):
                continue
            out.append({"key": key, "value": value})
''',
        "proof-retain-external-hints",
    )

    text = once(
        text,
        '''    provider_values = _provider_hint_values(prior_value_hints)

    tmdb = str(fixture.get("tmdbId") or "").strip()
''',
        '''    provider_values = _provider_hint_values(prior_value_hints)
    imdb_values = _external_identity_hint_values(prior_value_hints)

    tmdb = str(fixture.get("tmdbId") or "").strip()
''',
        "proof-load-imdb-values",
    )
    text = once(
        text,
        '''        if tmdb and decoded == tmdb:
            placeholder = "{tmdbId}"
        elif decoded in provider_values:
            placeholder = "{id}"
''',
        '''        if tmdb and decoded == tmdb:
            placeholder = "{tmdbId}"
        elif decoded in imdb_values:
            placeholder = "{imdbId}"
        elif decoded in provider_values:
            placeholder = "{id}"
''',
        "proof-imdb-path-placeholder",
    )
    text = once(
        text,
        '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:
            placeholder = "{id}"
''',
        '''        elif value in imdb_values and key_l in (EXTERNAL_IDENTITY_HINT_KEYS | PROVIDER_VALUE_KEYS):
            placeholder = "{imdbId}"
        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:
            placeholder = "{id}"
''',
        "proof-imdb-query-placeholder",
    )
    text = once(
        text,
        '''    opaque = [segment for segment in unresolved_segments if re.fullmatch(r"\\d{2,}|[A-Fa-f0-9]{12,}|[A-Za-z0-9_-]{18,}", segment)]
''',
        '''    opaque = [segment for segment in unresolved_segments if re.fullmatch(r"\\d{2,}|tt\\d{7,10}|[A-Fa-f0-9]{12,}|[A-Za-z0-9_-]{18,}", segment, re.I)]
''',
        "proof-imdb-literal-fail-closed",
    )
    text = once(
        text,
        '''        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),
        "reusable": reusable,
''',
        '''        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),
        "externalIdentityCorrelation": bool(imdb_values and any(row.get("placeholder") == "{imdbId}" for row in substitutions)),
        "reusable": reusable,
''',
        "proof-external-correlation",
    )
    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V10" not in text:
        raise AssertionError("external identity V11 requires Source Plan V10 recovery first")

    text = once(
        text,
        '''        "providerValueCorrelation": bool(derivation.get("providerValueCorrelation")),
        "requestSpec": copy.deepcopy(request_spec),
''',
        '''        "providerValueCorrelation": bool(derivation.get("providerValueCorrelation")),
        "externalIdentityCorrelation": bool(derivation.get("externalIdentityCorrelation")),
        "requestSpec": copy.deepcopy(request_spec),
''',
        "recovery-carry-external-correlation",
    )

    anchor = "def apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n"
    helper = '''# ROUTE_RECOVERY_EXTERNAL_IDENTITY_BASE_V11\ndef _positive_external_detail_bases(route_data: list[dict[str, Any]], patch: dict[str, Any]) -> list[str]:\n    out: list[str] = []\n    for row in route_data:\n        if not isinstance(row, dict) or row.get("requestSpecReusable") is not True:\n            continue\n        if not (int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0):\n            continue\n        if not _repair_recipe_origin_allowed(row):\n            continue\n        route = str(row.get("route") or "")\n        if row.get("externalIdentityCorrelation") is not True and "{imdbId}" not in route:\n            continue\n        base = _proof_execution_origin(row.get("origin"), patch)\n        if base and base not in out:\n            out.append(base)\n    return out[:6]\n\n\n'''
    text = once(text, anchor, helper + anchor, "recovery-external-detail-base-helper")

    text = once(
        text,
        '''        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
''',
        '''        proof_detail_bases = _positive_external_detail_bases(route_data, patch)
        if proof_detail_bases:
            patch["proof_detail_bases"] = proof_detail_bases
            model["proofDetailBases"] = proof_detail_bases
        else:
            patch.pop("proof_detail_bases", None)
            model.pop("proofDetailBases", None)
        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
''',
        "recovery-persist-external-detail-bases",
    )
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_materializer() -> bool:
    text = MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER in text:
        validate_materializer(text)
        return False
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V10" not in text:
        raise AssertionError("external identity V11 requires Source Plan V10 materializer first")
    text = once(
        text,
        '''        "proofSearchBases": [
            str(value).strip()
            for value in (patch.get("proof_search_bases") or static_model.get("proofSearchBases") or [])
            if str(value).strip()
        ][:6],
        "sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown"),
''',
        '''        "proofSearchBases": [
            str(value).strip()
            for value in (patch.get("proof_search_bases") or static_model.get("proofSearchBases") or [])
            if str(value).strip()
        ][:6],
        # PROVIDER_EXTERNAL_IDENTITY_BASE_V11
        "proofDetailBases": [
            str(value).strip()
            for value in (patch.get("proof_detail_bases") or static_model.get("proofDetailBases") or [])
            if str(value).strip()
        ][:6],
        "sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown"),
''',
        "materializer-project-proof-detail-bases",
    )
    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V10" not in text:
        raise AssertionError("external identity V11 requires Source Plan V10 ProviderBase first")

    text = once(
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
    text = once(
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
    text = once(
        text,
        '''    if any(token in route for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}")):
''',
        '''    if any(token in route for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}", "{imdbid}", "{imdb_id}")):
''',
        "base-runtime-route-imdb-authority",
    )
    text = once(
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
    text = once(
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
    text = once(
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
    text = once(text, anchor, replacement, "base-external-id-detail-plan")
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_worker(text: str | None = None) -> None:
    value = text if text is not None else WORKER.read_text(encoding="utf-8")
    for needle in (WORKER_MARKER, "'imdb', 'imdb_id', 'imdbid'"):
        if needle not in value:
            raise AssertionError(f"V11 worker missing: {needle}")


def validate_proof(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        PROOF_MARKER,
        "EXTERNAL_IDENTITY_HINT_KEYS",
        "def _external_identity_hint_values",
        'placeholder = "{imdbId}"',
        '"externalIdentityCorrelation"',
        'tt\\d{7,10}',
    ):
        if needle not in value:
            raise AssertionError(f"V11 proof missing: {needle}")


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        '"externalIdentityCorrelation"',
        "def _positive_external_detail_bases",
        'patch["proof_detail_bases"]',
        'model["proofDetailBases"]',
    ):
        if needle not in value:
            raise AssertionError(f"V11 recovery missing: {needle}")


def validate_materializer(text: str | None = None) -> None:
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    for needle in (MATERIALIZER_MARKER, '"proofDetailBases"'):
        if needle not in value:
            raise AssertionError(f"V11 materializer missing: {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        "NIAKVIO_PROVIDER_MODEL.proofDetailBases",
        'const imdbId = _text(meta && meta.imdbId)',
        "imdb_?id",
        "meta && meta.imdbId",
        "External-ID catalogues may have no title search endpoint",
    ):
        if needle not in value:
            raise AssertionError(f"V11 ProviderBase missing: {needle}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_EXTERNAL_IDENTITY_ROUTE_V11_OK changed={str(changed).lower()} "
        "imdb_hint=1 generic_imdb_id_reclassified=1 provider_id_separation=1 "
        "literal_imdb_fail_closed=1 imdb_placeholder=1 proof_detail_base=1 "
        "source_plan_external_id=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
