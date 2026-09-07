#!/usr/bin/env python3
"""Provider Value Plan V18: replay proof-correlated provider identities.

Positive upstream traces can expose a provider-internal catalogue id in a search
response and immediately consume it in a later request. Flattening that route to
`{id}` loses the dataflow and lets unrelated slug/movie routes win the bounded
runtime budget.

V18 keeps only chains that were positive in the same fixture trace:
  structured search request -> identity-scored provider id -> correlated route.
It also completes V17 current-origin preservation for ordinary HTML catalogue
links, not only article-card links. Current response origin is local execution
authority; it is not persisted as a global hub/domain replacement.

No provider ids, hosts, fixture titles or provider-specific selectors are encoded.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MATERIALIZER = ROOT / "scripts" / "materialize_provider_v3_all.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_CORRELATED_VALUE_PLAN_V18"
RECOVERY_MARKER = "ROUTE_RECOVERY_CORRELATED_VALUE_PLAN_V18"
MATERIALIZER_MARKER = "PROVIDER_CORRELATED_VALUE_PLAN_V18"
BASE_MARKER = "NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18"


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
    if "ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14" not in text:
        raise AssertionError("V18 requires Search Request Plan V14 recovery")

    anchor = "def apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n"
    helper = r'''# ROUTE_RECOVERY_CORRELATED_VALUE_PLAN_V18
def _positive_provider_value_plans(route_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only positive same-task search -> provider-value request chains."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in route_data:
        if not isinstance(row, dict):
            continue
        semantic = str(row.get("semanticType") or "").strip().casefold()
        fixture = str(row.get("fixture") or "").strip()
        if semantic not in {"movie", "tv", "anime"} or not fixture:
            continue
        grouped.setdefault((semantic, fixture), []).append(row)

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for (semantic, _fixture), rows in grouped.items():
        if not any(int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0 for row in rows):
            continue
        correlated = [
            row for row in rows
            if row.get("providerValueCorrelation") is True
            and row.get("requestSpecReusable") is True
            and "{id}" in str(row.get("route") or "")
            and _fresh_positive_origin(row)
            and isinstance(request_spec(row), dict)
        ]
        if not correlated:
            continue
        correlated.sort(key=lambda row: int(row.get("requestIndex") or 0))
        first_index = int(correlated[0].get("requestIndex") or 0)
        searches = [
            row for row in rows
            if row.get("requestSpecReusable") is True
            and _record_has_search_query(row)
            and _fresh_positive_origin(row)
            and isinstance(request_spec(row), dict)
            and int(row.get("requestIndex") or 0) < first_index
        ]
        if not searches:
            continue
        searches.sort(key=lambda row: int(row.get("requestIndex") or 0))
        search = searches[-1]
        plan = {
            "searchBase": _fresh_positive_origin(search),
            "searchRoute": str(search.get("route") or "").strip(),
            "searchRequestSpec": copy.deepcopy(request_spec(search)),
            "steps": [
                {
                    "base": _fresh_positive_origin(row),
                    "route": str(row.get("route") or "").strip(),
                    "requestSpec": copy.deepcopy(request_spec(row)),
                    "role": str(row.get("role") or "detail").strip().casefold(),
                }
                for row in correlated[:4]
            ],
            "semanticTypes": [semantic],
            "proofModelVersion": PROOF_VERSION,
            "sourceRole": "provider-value-correlation",
        }
        fingerprint = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        out.append(plan)
    return out[:12]


'''
    text = once(text, anchor, helper + anchor, "v18-recovery-helper")

    old = '''        external_identity_plan = _positive_external_identity_plan(route_data, patch)
'''
    new = '''        provider_value_plan = _positive_provider_value_plans(route_data)
        if provider_value_plan:
            patch["provider_value_plan"] = copy.deepcopy(provider_value_plan)
            model["providerValuePlan"] = copy.deepcopy(provider_value_plan)
        else:
            patch.pop("provider_value_plan", None)
            model.pop("providerValuePlan", None)

        external_identity_plan = _positive_external_identity_plan(route_data, patch)
'''
    text = once(text, old, new, "v18-persist-provider-value-plan")
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_materializer() -> bool:
    text = MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER in text:
        validate_materializer(text)
        return False
    if "PROVIDER_SEARCH_REQUEST_PLAN_V14" not in text:
        raise AssertionError("V18 requires V14 materializer")

    anchor = '''        # PROVIDER_STRUCTURED_EXTERNAL_ID_V13
        "externalIdentityPlan": [
'''
    replacement = '''        # PROVIDER_CORRELATED_VALUE_PLAN_V18
        "providerValuePlan": [
            dict(row)
            for row in (patch.get("provider_value_plan") or static_model.get("providerValuePlan") or [])
            if isinstance(row, dict)
        ][:12],
        # PROVIDER_STRUCTURED_EXTERNAL_ID_V13
        "externalIdentityPlan": [
'''
    text = once(text, anchor, replacement, "v18-materializer-plan-data")
    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False
    for required in (
        "NIAKVIO_PROVIDER_SEARCH_DETAIL_BRIDGE_V17",
        "NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14",
    ):
        if required not in text:
            raise AssertionError(f"V18 requires {required}")

    # Materialize only proof-v5 structured rows with executable exact bases/routes.
    anchor = '''        "externalIdentityPlan": [
            {
'''
    replacement = '''        "providerValuePlan": [
            {
                "searchBase": str(plan.get("searchBase") or "").strip(),
                "searchRoute": str(plan.get("searchRoute") or "").strip(),
                "searchRequestSpec": plan.get("searchRequestSpec") if isinstance(plan.get("searchRequestSpec"), dict) else {"method": "GET"},
                "steps": [
                    {
                        "base": str(step.get("base") or "").strip(),
                        "route": str(step.get("route") or "").strip(),
                        "requestSpec": step.get("requestSpec") if isinstance(step.get("requestSpec"), dict) else {"method": "GET"},
                        "role": str(step.get("role") or "detail").strip().casefold(),
                    }
                    for step in plan.get("steps") or []
                    if isinstance(step, dict)
                    and _provider_data_url_is_executable(step.get("base"))
                    and _provider_data_route_is_executable(step.get("route"))
                    and "{id}" in str(step.get("route") or "")
                ][:4],
                "semanticTypes": [
                    str(value).strip().casefold()
                    for value in plan.get("semanticTypes") or []
                    if str(value).strip().casefold() in {"movie", "tv", "anime"}
                ],
                "proofModelVersion": int(plan.get("proofModelVersion") or 0),
                "sourceRole": str(plan.get("sourceRole") or "provider-value-correlation"),
            }
            for plan in incoming_model.get("providerValuePlan") or []
            if isinstance(plan, dict)
            and _provider_data_url_is_executable(plan.get("searchBase"))
            and _provider_data_route_is_executable(plan.get("searchRoute"))
            and int(plan.get("proofModelVersion") or 0) >= 5
            and isinstance(plan.get("steps"), list)
            and plan.get("steps")
        ][:12],
        "externalIdentityPlan": [
            {
'''
    text = once(text, anchor, replacement, "v18-base-plan-data")

    # V17 preserved exact same-origin links from article cards. Complete that
    # boundary for ordinary anchor/detail extraction as well.
    old_html = '''    .map(url => ({
      url: _substituteDomain(url),
      score: Math.max(
        _spv4UrlScore(url, meta, mediaType, season),
'''
    new_html = '''    .map(url => ({
      url: _spv17CurrentResponseUrl(url, base),
      score: Math.max(
        _spv4UrlScore(url, meta, mediaType, season),
'''
    text = once(text, old_html, new_html, "v18-all-html-current-origin")

    resolver_anchor = "async function _resolveSearchRequestPlan(meta, mediaType, season, episode) {\n"
    resolver = r'''/* NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18 */
function _spv18ProviderIdFromJson(value, meta) {
  const rows = _spv4JsonRows(value, [])
    .map(row => ({
      row,
      score: _spv4TitleScore(
        _spv4Scalar(row.title) || _spv4Scalar(row.name) ||
        _spv4Scalar(row.original_title) || _spv4Scalar(row.post_title) ||
        _spv4Scalar(row.label) || "",
        meta
      )
    }))
    .filter(item => item.score >= 90)
    .sort((a, b) => b.score - a.score)
    .slice(0, 12);
  for (const item of rows) {
    const row = item.row || {};
    for (const key of ["id","ID","_id","media_id","post_id","anime_id","movie_id","series_id","show_id"]) {
      const value = _spv4Scalar(row[key]);
      if (value && value.length <= 160 && /^[A-Za-z0-9._~-]+$/.test(value)) return value;
    }
  }
  return "";
}
function _spv18ProviderIdFromHtml(html, meta) {
  const source = _text(html);
  const anchorRe = /<a\b([^>]*)>([\s\S]*?)<\/a>/gi;
  let match;
  while ((match = anchorRe.exec(source)) !== null) {
    const label = _htmlVisibleText(match[2]).replace(/\s+/g, " ").trim();
    if (_spv4TitleScore(label, meta) < 90) continue;
    const attrs = _text(match[1]);
    const idMatch = attrs.match(/\bdata-(?:id|post-id|media-id|anime-id|movie-id|series-id|show-id)\s*=\s*["']?([A-Za-z0-9._~-]{1,160})/i);
    if (idMatch) return idMatch[1];
  }
  for (const title of _spv4Titles(meta)) {
    const token = _text(title).trim();
    if (!token) continue;
    const at = source.toLowerCase().indexOf(token.toLowerCase());
    if (at < 0) continue;
    const windowText = source.slice(Math.max(0, at - 1400), Math.min(source.length, at + 1400));
    const idMatch = windowText.match(/\bdata-(?:id|post-id|media-id|anime-id|movie-id|series-id|show-id)\s*=\s*["']?([A-Za-z0-9._~-]{1,160})/i);
    if (idMatch) return idMatch[1];
  }
  return "";
}
function _spv18ValueUrls(value, base, out) {
  out = out || [];
  if (Array.isArray(value)) {
    for (const child of value) _spv18ValueUrls(child, base, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  for (const [key, child] of Object.entries(value)) {
    if (typeof child === "string" && /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl|iframe|embed|player|link|href)$/i.test(key)) {
      const absolute = _absolute(child, base);
      if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
    }
    if (child && typeof child === "object") _spv18ValueUrls(child, base, out);
    if (out.length >= 160) break;
  }
  return out;
}
async function _resolveProviderValuePlan(meta, mediaType, season, episode) {
  const plans = Array.isArray(NIAKVIO_PROVIDER_MODEL.providerValuePlan)
    ? NIAKVIO_PROVIDER_MODEL.providerValuePlan : [];
  if (!plans.length || !meta || !meta.title) return [];
  const media = _mediaNamespace(mediaType);
  const baseValues = {
    query: _text(meta.title),
    providerId: "",
    tmdbId: _text(meta.tmdbId),
    imdbId: _text(meta.imdbId),
    media,
    season,
    episode,
    source: null
  };
  for (const plan of plans.slice(0, 12)) {
    const lanes = Array.isArray(plan && plan.semanticTypes) ? plan.semanticTypes : [];
    if (lanes.length && !lanes.includes(mediaType) && !(mediaType === "anime" && lanes.includes("tv"))) continue;
    const searchBase = _text(plan && plan.searchBase);
    const searchRoute = _text(plan && plan.searchRoute);
    if (!/^https?:\/\//i.test(searchBase) || !searchRoute) continue;
    const searchUrl = _recipeUrl(searchRoute, baseValues, searchBase);
    if (!searchUrl) continue;
    try {
      const searchSpec = _recipeRequestSpec(
        { providerValueSearch: plan.searchRequestSpec || { method: "GET" } },
        "providerValueSearch",
        baseValues
      );
      const searchPayload = await _recipePayload(searchUrl, {}, searchSpec, baseValues);
      const providerId = typeof searchPayload.value === "string"
        ? _spv18ProviderIdFromHtml(searchPayload.value, meta)
        : _spv18ProviderIdFromJson(searchPayload.value, meta);
      if (!providerId) continue;
      const values = Object.assign({}, baseValues, { providerId });
      for (const step of (plan.steps || []).slice(0, 4)) {
        const stepBase = _text(step && step.base);
        const stepRoute = _text(step && step.route);
        if (!/^https?:\/\//i.test(stepBase) || !stepRoute || !/\{id\}/i.test(stepRoute)) continue;
        const stepUrl = _recipeUrl(stepRoute, values, stepBase);
        if (!stepUrl) continue;
        const stepSpec = _recipeRequestSpec(
          { providerValueStep: step.requestSpec || { method: "GET" } },
          "providerValueStep",
          values
        );
        const payload = await _recipePayload(stepUrl, {}, stepSpec, values);
        let urls = [];
        if (typeof payload.value === "string") {
          urls = _uniq([
            ..._extractUrls(payload.value, payload.base),
            ..._spv15ExplicitPlayerAttrs(payload.value, payload.base)
          ]);
        } else {
          urls = _uniq([
            ..._jsonUrls(payload.value),
            ..._sourceUrls(payload.value, payload.base),
            ..._spv18ValueUrls(payload.value, payload.base, [])
          ]);
        }
        const direct = urls.filter(_directMedia);
        if (direct.length) return _streams(direct, payload.base || stepUrl).slice(0, 40);
        const crawl = urls.filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a));
        if (crawl.length) {
          const streams = await _crawlDirectMedia(crawl.slice(0, 10), payload.base || stepUrl, 3);
          if (streams.length) return streams.slice(0, 40);
        }
      }
    } catch (_) {}
  }
  return [];
}
'''
    text = once(text, resolver_anchor, resolver + resolver_anchor, "v18-base-resolver")

    old_available = '''function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length) return true;
'''
    new_available = '''function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.providerValuePlan) && NIAKVIO_PROVIDER_MODEL.providerValuePlan.length) return true;
  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length) return true;
'''
    text = once(text, old_available, new_available, "v18-runtime-plan-available")

    old_run = '''  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length) {
    const searchMeta = await _tmdb(tmdbId, type) || null;
'''
    new_run = '''  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.providerValuePlan) && NIAKVIO_PROVIDER_MODEL.providerValuePlan.length) {
    const providerValueMeta = await _tmdb(tmdbId, type) || null;
    const providerValueStreams = await _resolveProviderValuePlan(providerValueMeta, type, season, episode);
    if (providerValueStreams.length) return providerValueStreams;
  }

  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length) {
    const searchMeta = await _tmdb(tmdbId, type) || null;
'''
    text = once(text, old_run, new_run, "v18-run-provider-value-plan")

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        "def _positive_provider_value_plans",
        'row.get("providerValueCorrelation") is True',
        'patch["provider_value_plan"]',
        'model["providerValuePlan"]',
    ):
        if needle not in value:
            raise AssertionError(f"V18 recovery missing: {needle}")


def validate_materializer(text: str | None = None) -> None:
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    for needle in (MATERIALIZER_MARKER, '"providerValuePlan"', 'patch.get("provider_value_plan")'):
        if needle not in value:
            raise AssertionError(f"V18 materializer missing: {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        '"providerValuePlan"',
        "function _spv18ProviderIdFromJson",
        "function _spv18ProviderIdFromHtml",
        "function _spv18ValueUrls",
        "async function _resolveProviderValuePlan",
        "const providerValueStreams = await _resolveProviderValuePlan",
        "url: _spv17CurrentResponseUrl(url, base)",
    ):
        if needle not in value:
            raise AssertionError(f"V18 ProviderBase missing: {needle}")
    forbidden = ("animekai", "movies4u", "frenchstream", "mugiwara", "french-stream.one", "fs23.lol")
    lower = value.lower()
    for token in forbidden:
        if token in lower:
            raise AssertionError(f"V18 introduced provider-specific token: {token}")


def main() -> int:
    changed = patch_recovery() | patch_materializer() | patch_base()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_CORRELATED_VALUE_PLAN_V18_OK changed={str(changed).lower()} "
        "provider_value_dataflow=1 semantic_positive_only=1 exact_proof_base=1 "
        "all_html_current_origin=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
