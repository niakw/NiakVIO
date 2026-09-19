#!/usr/bin/env python3
"""Search Request Plan V14: preserve proof-owned search request semantics.

V13 deliberately rejects flat routes that would lose headers/body/dataflow. Live
multi-hop traces show that a positive search request can therefore be real and
reusable while remaining in routeData only. V14 persists those requests as
structured DATA (base + route + requestSpec) and executes them before generic
flat-route fallback.

V14 also prevents historical domain substitutions from rewriting any hostname
that a current positive trace proved 2xx/3xx. The historical mapping remains
knowledge; it simply loses runtime authority while fresh proof says the source,
player or resolver host is live.

No provider ids, hostnames or fixture titles are encoded here.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MATERIALIZER = ROOT / "scripts" / "materialize_provider_v3_all.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_SEARCH_REQUEST_PLAN_V14"
RECOVERY_MARKER = "ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14"
MATERIALIZER_MARKER = "PROVIDER_SEARCH_REQUEST_PLAN_V14"
BASE_MARKER = "NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False
    if "ROUTE_RECOVERY_STRUCTURED_EXTERNAL_ID_V13" not in text:
        raise AssertionError("Search Request Plan V14 requires Route Plan V13 first")

    anchor = "def apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n"
    helper = r'''# ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14
def _fresh_positive_origin(row: dict[str, Any]) -> str:
    if not isinstance(row, dict) or not _repair_recipe_origin_allowed(row):
        return ""
    if not (int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0):
        return ""
    status = int(row.get("status") or 0)
    if status < 200 or status >= 400:
        return ""
    raw = str(row.get("origin") or "").strip()
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _positive_proof_hosts(route_data: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for row in route_data:
        base = _fresh_positive_origin(row)
        if not base:
            continue
        try:
            host = (urllib.parse.urlsplit(base).hostname or "").casefold()
        except ValueError:
            host = ""
        if host and host not in out:
            out.append(host)
    return out[:24]


def _positive_search_request_plan(route_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in route_data:
        if not isinstance(row, dict) or row.get("requestSpecReusable") is not True:
            continue
        if row.get("role") != "search" and not _record_has_search_query(row):
            continue
        base = _fresh_positive_origin(row)
        route = str(row.get("route") or "").strip()
        spec = request_spec(row)
        if not base or not route or not isinstance(spec, dict):
            continue
        if not _record_has_search_query(row):
            continue
        fingerprint = (
            base,
            route,
            json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        semantic = str(row.get("semanticType") or "").strip().casefold()
        out.append({
            "base": base,
            "route": route,
            "requestSpec": copy.deepcopy(spec),
            "proofModelVersion": PROOF_VERSION,
            "sourceRole": "catalog-search",
            "semanticTypes": [semantic] if semantic in {"movie", "tv", "anime"} else [],
        })
    return out[:6]


'''
    text = once(text, anchor, helper + anchor, "v14-recovery-helpers")

    old = '''        external_identity_plan = _positive_external_identity_plan(route_data, patch)
'''
    new = '''        proof_protected_hosts = _positive_proof_hosts(route_data)
        if proof_protected_hosts:
            patch["proof_protected_hosts"] = proof_protected_hosts
            model["proofProtectedHosts"] = proof_protected_hosts
        else:
            patch.pop("proof_protected_hosts", None)
            model.pop("proofProtectedHosts", None)

        search_request_plan = _positive_search_request_plan(route_data)
        if search_request_plan:
            patch["search_request_plan"] = copy.deepcopy(search_request_plan)
            model["searchRequestPlan"] = copy.deepcopy(search_request_plan)
            patch["identity_input"] = {
                "mode": "catalog_search",
                "requires_tmdb_before_run": True,
                "required_fields": ["title", "mediaType"],
            }
        else:
            patch.pop("search_request_plan", None)
            model.pop("searchRequestPlan", None)

        external_identity_plan = _positive_external_identity_plan(route_data, patch)
'''
    text = once(text, old, new, "v14-persist-structured-search-plan")

    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_materializer() -> bool:
    text = MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER in text:
        validate_materializer(text)
        return False
    if "PROVIDER_STRUCTURED_EXTERNAL_ID_V13" not in text:
        raise AssertionError("Search Request Plan V14 requires V13 materializer first")

    text = once(
        text,
        '''def _runtime_domain_substitutions(patch: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
''',
        '''def _runtime_domain_substitutions(patch: dict[str, Any], static_model: dict[str, Any] | None = None) -> dict[str, str]:
    out: dict[str, str] = {}
    # PROVIDER_SEARCH_REQUEST_PLAN_V14: current positive HTTP proof outranks stale
    # historical replacement knowledge for runtime execution.
    protected = {
        str(value or "").strip().casefold()
        for value in [
            *(patch.get("proof_protected_hosts") or []),
            *((static_model or {}).get("proofProtectedHosts") or []),
        ]
        if str(value or "").strip()
    }
''',
        "v14-runtime-domain-protected-hosts",
    )
    text = once(
        text,
        '''            if old and new:
                out[old] = new
''',
        '''            if old and new and old not in protected:
                out[old] = new
''',
        "v14-runtime-domain-proof-precedence",
    )
    text = once(
        text,
        '        "domainSubstitutions": _runtime_domain_substitutions(patch),\n',
        '        "domainSubstitutions": _runtime_domain_substitutions(patch, static_model),\n',
        "v14-runtime-domain-static-proof-input",
    )

    text = once(
        text,
        '''        # PROVIDER_STRUCTURED_EXTERNAL_ID_V13
        "externalIdentityPlan": [
''',
        '''        # PROVIDER_SEARCH_REQUEST_PLAN_V14
        "proofProtectedHosts": [
            str(value).strip().casefold()
            for value in (patch.get("proof_protected_hosts") or static_model.get("proofProtectedHosts") or [])
            if str(value).strip()
        ][:24],
        "searchRequestPlan": [
            dict(row)
            for row in (patch.get("search_request_plan") or static_model.get("searchRequestPlan") or [])
            if isinstance(row, dict)
        ][:6],
        # PROVIDER_STRUCTURED_EXTERNAL_ID_V13
        "externalIdentityPlan": [
''',
        "v14-materializer-search-plan-data",
    )

    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_BASE_STRUCTURED_EXTERNAL_ID_V13" not in text:
        raise AssertionError("Search Request Plan V14 requires V13 ProviderBase first")

    text = once(
        text,
        '''        "externalIdentityPlan": [
            {
''',
        '''        "proofProtectedHosts": [
            str(value).strip().casefold()
            for value in incoming_model.get("proofProtectedHosts") or []
            if str(value).strip()
        ][:24],
        "searchRequestPlan": [
            {
                "base": str(row.get("base") or "").strip(),
                "route": str(row.get("route") or "").strip(),
                "requestSpec": row.get("requestSpec") if isinstance(row.get("requestSpec"), dict) else {"method": "GET"},
                "proofModelVersion": int(row.get("proofModelVersion") or 0),
                "sourceRole": str(row.get("sourceRole") or "catalog-search"),
                "semanticTypes": [
                    str(value).strip().casefold()
                    for value in row.get("semanticTypes") or []
                    if str(value).strip().casefold() in {"movie", "tv", "anime"}
                ],
            }
            for row in incoming_model.get("searchRequestPlan") or []
            if isinstance(row, dict)
            and _provider_data_url_is_executable(row.get("base"))
            and _provider_data_route_is_executable(row.get("route"))
            and int(row.get("proofModelVersion") or 0) >= 5
        ][:6],
        "externalIdentityPlan": [
            {
''',
        "v14-base-search-plan-data",
    )

    resolver_anchor = "async function _resolveExternalIdentityPlan(meta, mediaType, season, episode) {\n"
    resolver = r'''/* NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14 */
async function _resolveSearchRequestPlan(meta, mediaType, season, episode) {
  const plans = Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan)
    ? NIAKVIO_PROVIDER_MODEL.searchRequestPlan : [];
  if (!plans.length || !meta || !meta.title) return [];
  const media = _mediaNamespace(mediaType);
  const values = {
    query: _text(meta.title),
    providerId: _text(meta.tmdbId),
    tmdbId: _text(meta.tmdbId),
    imdbId: _text(meta.imdbId),
    media,
    season,
    episode,
    source: null
  };
  for (const plan of plans.slice(0, 6)) {
    const lanes = Array.isArray(plan && plan.semanticTypes) ? plan.semanticTypes : [];
    if (lanes.length && !lanes.includes(mediaType) && !(mediaType === "anime" && lanes.includes("tv"))) continue;
    const base = _text(plan && plan.base);
    const route = _text(plan && plan.route);
    if (!/^https?:\/\//i.test(base) || !route) continue;
    const url = _recipeUrl(route, values, base);
    if (!url) continue;
    try {
      const requestSpec = _recipeRequestSpec(
        { searchPlanRequest: plan.requestSpec || { method: "GET" } },
        "searchPlanRequest",
        values
      );
      const payload = await _recipePayload(url, {}, requestSpec, values);
      const directUrls = typeof payload.value === "string"
        ? _extractUrls(payload.value, payload.base).filter(_directMedia)
        : _sourceUrls(payload.value, payload.base).filter(_directMedia);
      if (directUrls.length) return _streams(_uniq(directUrls), payload.base || url).slice(0, 40);

      const details = typeof payload.value === "string"
        ? _spv4HtmlDetails(payload.value, payload.base, meta, mediaType, season)
        : _spv4JsonDetails(
            payload.value,
            payload.base,
            meta,
            mediaType,
            season,
            episode,
            NIAKVIO_PROVIDER_MODEL.sourceRuntimeFamily
          );
      if (details.length) {
        const crawled = await _crawlDirectMedia(_uniq(details).slice(0, 8), payload.base || url, 3);
        if (crawled.length) return crawled.slice(0, 40);
      }
    } catch (_) {}
  }
  return [];
}
'''
    text = once(text, resolver_anchor, resolver + resolver_anchor, "v14-base-search-plan-resolver")

    text = once(
        text,
        '''function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.externalIdentityPlan) && NIAKVIO_PROVIDER_MODEL.externalIdentityPlan.length) return true;
  return (NIAKVIO_PROVIDER_MODEL.routes || []).some(route => ["search","detail","player","api"].includes(_routeKind(route)));
}
''',
        '''function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length) return true;
  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.externalIdentityPlan) && NIAKVIO_PROVIDER_MODEL.externalIdentityPlan.length) return true;
  return (NIAKVIO_PROVIDER_MODEL.routes || []).some(route => ["search","detail","player","api"].includes(_routeKind(route)));
}
''',
        "v14-base-search-plan-runtime-availability",
    )

    text = once(
        text,
        '''  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;

  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.externalIdentityPlan) && NIAKVIO_PROVIDER_MODEL.externalIdentityPlan.length) {
''',
        '''  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;

  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length) {
    const searchMeta = await _tmdb(tmdbId, type) || null;
    const searchStreams = await _resolveSearchRequestPlan(searchMeta, type, season, episode);
    if (searchStreams.length) return searchStreams;
  }

  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.externalIdentityPlan) && NIAKVIO_PROVIDER_MODEL.externalIdentityPlan.length) {
''',
        "v14-base-run-search-plan",
    )

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        "def _positive_search_request_plan",
        "def _positive_proof_hosts",
        'patch["search_request_plan"]',
        'model["searchRequestPlan"]',
        'patch["proof_protected_hosts"]',
        'model["proofProtectedHosts"]',
    ):
        if needle not in value:
            raise AssertionError(f"V14 recovery missing: {needle}")


def validate_materializer(text: str | None = None) -> None:
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    for needle in (
        MATERIALIZER_MARKER,
        '"searchRequestPlan"',
        '"proofProtectedHosts"',
        "old not in protected",
        '"domainSubstitutions": _runtime_domain_substitutions(patch, static_model)',
    ):
        if needle not in value:
            raise AssertionError(f"V14 materializer missing: {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        '"searchRequestPlan"',
        '"proofProtectedHosts"',
        "async function _resolveSearchRequestPlan",
        "searchPlanRequest",
        "_spv4HtmlDetails(payload.value, payload.base, meta, mediaType, season)",
        "_crawlDirectMedia(_uniq(details).slice(0, 8)",
    ):
        if needle not in value:
            raise AssertionError(f"V14 ProviderBase missing: {needle}")


def main() -> int:
    changed = patch_recovery() | patch_materializer() | patch_base()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_SEARCH_REQUEST_PLAN_V14_OK changed={str(changed).lower()} "
        "structured_search_request=1 proof_host_precedence=1 flat_route_boundary_preserved=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
