#!/usr/bin/env python3
"""Route Plan V13: fail-closed flat routes + structured external-ID execution.

V13 fixes a dataflow boundary exposed by live multi-hop traces:
- a GET observation is not a reusable route merely because it returned 2xx;
- flat `routes[]` require an abstracted dynamic identity and a reusable request spec;
- fixture-static/player/file URLs stay evidence only and cannot become durable
  relative routes after losing their origin;
- positive external-ID detail requests are persisted as structured DATA
  (`externalIdentityPlan`) with origin and sanitized request spec;
- ProviderBase executes that plan as Core metadata -> external ID -> detail page,
  then selects episodic direct media by requested season/episode.

No provider IDs, hostnames or fixture titles are encoded in this migration.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MATERIALIZER = ROOT / "scripts" / "materialize_provider_v3_all.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_ROUTE_PLAN_V13"
RECOVERY_MARKER = "ROUTE_RECOVERY_STRUCTURED_EXTERNAL_ID_V13"
MATERIALIZER_MARKER = "PROVIDER_STRUCTURED_EXTERNAL_ID_V13"
BASE_MARKER = "NIAKVIO_PROVIDER_BASE_STRUCTURED_EXTERNAL_ID_V13"


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
    if "ROUTE_RECOVERY_EXTERNAL_IDENTITY_BASE_V11" not in text:
        raise AssertionError("Route Plan V13 requires external identity V11 first")

    old_generic = '''def generic_execution_route(record: dict[str, Any]) -> bool:
    """Whether routes[] may replay this call without losing HTTP/dataflow semantics."""
    spec = request_spec(record) or {"method": str(record.get("method") or "GET").upper()}
    if str(spec.get("method") or "GET").upper() != "GET":
        return False
    if spec.get("body"):
        return False
    headers = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
    nontrivial = {
        str(key).casefold() for key in headers
        if str(key).casefold() not in {"accept", "accept-language", "user-agent"}
    }
    if nontrivial:
        return False
    route = str(record.get("route") or "").strip()
    try:
        query = urllib.parse.parse_qsl(urllib.parse.urlsplit(route).query, keep_blank_values=True)
    except ValueError:
        return False
    if any(str(key).casefold() in _BLANK_DYNAMIC_QUERY_KEYS and value == "" for key, value in query):
        return False
    return True
'''
    new_generic = '''# ROUTE_RECOVERY_STRUCTURED_EXTERNAL_ID_V13
_FLAT_ROUTE_DYNAMIC_TOKENS = (
    "{query}", "{title}", "{slug}", "{id}", "{tmdbId}", "{tmdb_id}",
    "{imdbId}", "{imdb_id}", "{season}", "{episode}",
)


def generic_execution_route(record: dict[str, Any]) -> bool:
    """Whether routes[] may replay this call without losing HTTP/dataflow semantics.

    A flat route is deliberately stricter than an observed HTTP request. It must
    carry a reusable request spec *and* at least one proof-derived dynamic token.
    Static fixture/player/file paths remain routeData evidence only.
    """
    if record.get("requestSpecReusable") is not True:
        return False
    route = str(record.get("route") or "").strip()
    if not route or not any(token.casefold() in route.casefold() for token in _FLAT_ROUTE_DYNAMIC_TOKENS):
        return False
    spec = request_spec(record)
    if not isinstance(spec, dict):
        return False
    if str(spec.get("method") or "GET").upper() != "GET":
        return False
    if spec.get("body"):
        return False
    headers = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
    nontrivial = {
        str(key).casefold() for key in headers
        if str(key).casefold() not in {"accept", "accept-language", "user-agent"}
    }
    if nontrivial:
        return False
    try:
        query = urllib.parse.parse_qsl(urllib.parse.urlsplit(route).query, keep_blank_values=True)
    except ValueError:
        return False
    if any(str(key).casefold() in _BLANK_DYNAMIC_QUERY_KEYS and value == "" for key, value in query):
        return False
    return True


def _flat_route_blocklist(route_data: list[dict[str, Any]]) -> set[str]:
    """Freshly observed non-flat routes cannot keep an obsolete flat baseline alive."""
    blocked: set[str] = set()
    for row in route_data:
        if not isinstance(row, dict):
            continue
        route = str(row.get("route") or "").strip()
        if route and not generic_execution_route(row):
            blocked.add(route)
    return blocked
'''
    text = once(text, old_generic, new_generic, "strict-flat-route-boundary")

    text = once(
        text,
        '''    if any(token in route for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}")):
''',
        '''    if any(token in route for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}", "{imdbid}", "{imdb_id}")):
''',
        "runtime-route-external-id-identity",
    )

    old_select = '''def select_runtime_routes(
    existing_routes: list[str],
    candidate_routes: list[str],
    execution_routes: list[str],
) -> tuple[list[str], bool]:
    """Do not demote a richer published runtime plan to weak observations."""
    execution = unique(execution_routes, 192)
    if any(_identity_bearing_runtime_route(route) for route in execution):
        return execution, False
    for baseline in (existing_routes, candidate_routes):
        current = unique(baseline, 192)
        if any(_identity_bearing_runtime_route(route) for route in current):
            return current, True
    return execution, False
'''
    new_select = '''def select_runtime_routes(
    existing_routes: list[str],
    candidate_routes: list[str],
    execution_routes: list[str],
    blocked_routes: set[str] | None = None,
) -> tuple[list[str], bool]:
    """Prefer fresh executable proof and never preserve freshly disproven flat DATA."""
    blocked = blocked_routes or set()
    execution = unique([route for route in execution_routes if route not in blocked], 192)
    if any(_identity_bearing_runtime_route(route) for route in execution):
        return execution, False
    for baseline in (existing_routes, candidate_routes):
        current = unique([route for route in baseline if route not in blocked], 192)
        if any(_identity_bearing_runtime_route(route) for route in current):
            return current, True
    return execution, False
'''
    text = once(text, old_select, new_select, "fresh-proof-baseline-sanitizer")

    anchor = "def apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n"
    helper = '''def _looks_direct_media_route(route: object) -> bool:\n    value = str(route or "").strip().casefold()\n    return bool(re.search(r"\\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|/(?:hls|dash|stream)(?:/|[?#]|$)", value))\n\n\ndef _positive_external_identity_plan(route_data: list[dict[str, Any]], patch: dict[str, Any]) -> list[dict[str, Any]]:\n    """Persist only reusable detail-page requests, never fixture HLS/player output."""\n    out: list[dict[str, Any]] = []\n    seen: set[tuple[str, str, str]] = set()\n    for row in route_data:\n        if not isinstance(row, dict) or row.get("requestSpecReusable") is not True:\n            continue\n        if row.get("externalIdentityCorrelation") is not True:\n            continue\n        if not (int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0):\n            continue\n        if not _repair_recipe_origin_allowed(row):\n            continue\n        route = str(row.get("route") or "").strip()\n        if "{imdbid}" not in route.casefold() or row.get("role") != "detail":\n            continue\n        if _looks_direct_media_route(route):\n            continue\n        base = _proof_execution_origin(row.get("origin"), patch)\n        if not base:\n            continue\n        spec = request_spec(row) or {"method": str(row.get("method") or "GET").upper()}\n        fingerprint = (base, route, json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")))\n        if fingerprint in seen:\n            continue\n        seen.add(fingerprint)\n        out.append({\n            "base": base,\n            "route": route,\n            "requestSpec": copy.deepcopy(spec),\n            "proofModelVersion": PROOF_VERSION,\n            "sourceRole": "external-identity-detail",\n        })\n    return out[:4]\n\n\n'''
    text = once(text, anchor, helper + anchor, "structured-external-plan-helper")

    text = once(
        text,
        '''        runtime_routes, preserved_baseline_plan = select_runtime_routes(
            existing_routes, candidate_routes, execution_routes
        )
''',
        '''        blocked_flat_routes = _flat_route_blocklist(route_data)
        runtime_routes, preserved_baseline_plan = select_runtime_routes(
            existing_routes, candidate_routes, execution_routes, blocked_flat_routes
        )
''',
        "apply-flat-route-blocklist",
    )

    # V11 inserts its proofDetailBases handling immediately before recipe lookup.
    text = once(
        text,
        '''        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
''',
        '''        external_identity_plan = _positive_external_identity_plan(route_data, patch)
        if external_identity_plan:
            patch["external_identity_plan"] = copy.deepcopy(external_identity_plan)
            model["externalIdentityPlan"] = copy.deepcopy(external_identity_plan)
            patch["identity_input"] = {
                "mode": "external_id",
                "requires_tmdb_before_run": True,
                "required_fields": ["tmdbId", "mediaType"],
            }
        else:
            patch.pop("external_identity_plan", None)
            model.pop("externalIdentityPlan", None)
        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
''',
        "persist-structured-external-plan",
    )

    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_materializer() -> bool:
    text = MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER in text:
        validate_materializer(text)
        return False
    if "PROVIDER_EXTERNAL_IDENTITY_BASE_V11" not in text:
        raise AssertionError("Route Plan V13 requires V11 materializer first")

    text = once(
        text,
        '''        "proofDetailBases": [
            str(value).strip()
            for value in (patch.get("proof_detail_bases") or static_model.get("proofDetailBases") or [])
            if str(value).strip()
        ][:6],
        "sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown"),
''',
        '''        "proofDetailBases": [
            str(value).strip()
            for value in (patch.get("proof_detail_bases") or static_model.get("proofDetailBases") or [])
            if str(value).strip()
        ][:6],
        # PROVIDER_STRUCTURED_EXTERNAL_ID_V13
        "externalIdentityPlan": [
            dict(row)
            for row in (patch.get("external_identity_plan") or static_model.get("externalIdentityPlan") or [])
            if isinstance(row, dict)
        ][:4],
        "sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown"),
''',
        "materializer-external-plan-projection",
    )
    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11" not in text:
        raise AssertionError("Route Plan V13 requires V11 ProviderBase first")
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V12" not in text:
        raise AssertionError("Route Plan V13 requires Source Plan V12 first")

    text = once(
        text,
        '''        "proofDetailBases": [
            str(value).strip()
            for value in incoming_model.get("proofDetailBases") or []
            if _provider_data_url_is_executable(value)
        ][:6],
        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),
''',
        '''        "proofDetailBases": [
            str(value).strip()
            for value in incoming_model.get("proofDetailBases") or []
            if _provider_data_url_is_executable(value)
        ][:6],
        "externalIdentityPlan": [
            {
                "base": str(row.get("base") or "").strip(),
                "route": str(row.get("route") or "").strip(),
                "requestSpec": row.get("requestSpec") if isinstance(row.get("requestSpec"), dict) else {"method": "GET"},
                "proofModelVersion": int(row.get("proofModelVersion") or 0),
                "sourceRole": str(row.get("sourceRole") or "external-identity-detail"),
            }
            for row in incoming_model.get("externalIdentityPlan") or []
            if isinstance(row, dict)
            and _provider_data_url_is_executable(row.get("base"))
            and _provider_data_route_is_executable(row.get("route"))
            and "{imdbid}" in str(row.get("route") or "").casefold()
        ][:4],
        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),
''',
        "base-external-plan-data",
    )

    # Relative HLS/DASH links embedded as quoted strings must be discoverable from
    # an external-ID detail page. They are still output only after _directMedia().
    text = once(
        text,
        '''    /["'](\\/(?:api|watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|manifest|action)(?:[^"'<>\\\\\\s]{0,500}))["']/gi,
''',
        '''    /["'](\\/(?:api|watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|manifest|hls|dash|action)(?:[^"'<>\\\\\\s]{0,500}))["']/gi,
''',
        "extract-relative-hls",
    )

    # The generic placeholder expander is reused by structured request specs.
    text = once(
        text,
        '''    tmdb_id: values.tmdbId,
    media: values.media,
''',
        '''    tmdb_id: values.tmdbId,
    imdbId: values.imdbId,
    imdb_id: values.imdbId,
    media: values.media,
''',
        "recipe-url-imdb-placeholder",
    )
    # Same replacement map appears once more in _recipeExpandScalar.
    text = once(
        text,
        '''    tmdb_id: values.tmdbId,
    media: values.media,
''',
        '''    tmdb_id: values.tmdbId,
    imdbId: values.imdbId,
    imdb_id: values.imdbId,
    media: values.media,
''',
        "recipe-scalar-imdb-placeholder",
    )

    anchor = "async function getStreams(tmdbId, mediaType, season, episode) {\n"
    resolver = r'''/* NIAKVIO_PROVIDER_BASE_STRUCTURED_EXTERNAL_ID_V13 */
function _externalEpisodeMarker(url, season, episode) {
  let path = "";
  try { path = decodeURIComponent(new URL(url).pathname || "").toLowerCase(); }
  catch (_) { return { marked: false, matches: false }; }
  const wantedSeason = Math.max(1, Number(season) || 1);
  const wantedEpisode = Math.max(1, Number(episode) || 1);
  let match = path.match(/\/(\d{1,3})\/(\d{1,4})\/[^/]*(?:playlist\.m3u8|manifest\.mpd|[^/]+\.(?:mp4|mkv|webm))(?:$|[?#])/i);
  if (match) return {
    marked: true,
    matches: Number(match[1]) === wantedSeason && Number(match[2]) === wantedEpisode
  };
  match = path.match(/(?:^|[-_/])s(?:eason)?[-_ ]*0*(\d{1,3})[-_ ]*e(?:pisode)?[-_ ]*0*(\d{1,4})(?:[-_/]|$)/i);
  if (match) return {
    marked: true,
    matches: Number(match[1]) === wantedSeason && Number(match[2]) === wantedEpisode
  };
  match = path.match(/(?:^|[-_/])0*(\d{1,3})x0*(\d{1,4})(?:[-_/]|$)/i);
  if (match) return {
    marked: true,
    matches: Number(match[1]) === wantedSeason && Number(match[2]) === wantedEpisode
  };
  return { marked: false, matches: false };
}
function _externalPlaybackHeaders(requestSpec) {
  const source = requestSpec && requestSpec.headers && typeof requestSpec.headers === "object"
    ? requestSpec.headers : {};
  const out = {};
  for (const [key, value] of Object.entries(source)) {
    if (/^(?:origin|referer|referrer|user-agent)$/i.test(key) && value != null && value !== "") out[key] = value;
  }
  return out;
}
async function _resolveExternalIdentityPlan(meta, mediaType, season, episode) {
  const plans = Array.isArray(NIAKVIO_PROVIDER_MODEL.externalIdentityPlan)
    ? NIAKVIO_PROVIDER_MODEL.externalIdentityPlan : [];
  if (!plans.length || !meta || !meta.imdbId) return [];
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
  for (const plan of plans.slice(0, 4)) {
    const base = _substituteDomain(_text(plan && plan.base));
    const route = _text(plan && plan.route);
    if (!base || !route || !/\{imdb_?id\}/i.test(route)) continue;
    const url = _recipeUrl(route, values, base);
    if (!url) continue;
    try {
      const requestSpec = _recipeRequestSpec(
        { externalIdentityRequest: plan.requestSpec || { method: "GET" } },
        "externalIdentityRequest",
        values
      );
      const payload = await _recipePayload(url, {}, requestSpec, values);
      const urls = typeof payload.value === "string"
        ? _extractUrls(payload.value, payload.base)
        : _sourceUrls(payload.value, payload.base);
      const direct = _uniq(urls.filter(_directMedia));
      if (direct.length) {
        let selected = direct;
        if (media !== "movie" && season != null && episode != null) {
          const classified = direct.map(value => ({ value, marker: _externalEpisodeMarker(value, season, episode) }));
          const marked = classified.filter(row => row.marker.marked);
          selected = marked.filter(row => row.marker.matches).map(row => row.value);
          if (!marked.length) selected = [];
        }
        if (selected.length) {
          return _streams(selected, payload.base || url, _externalPlaybackHeaders(requestSpec)).slice(0, 40);
        }
      }
      const nested = _uniq(urls.filter(_crawlEligible)).slice(0, 10);
      if (nested.length) {
        const crawled = await _crawlDirectMedia(nested, payload.base || url, 2);
        if (crawled.length) return crawled;
      }
    } catch (_) {}
  }
  return [];
}
'''
    text = once(text, anchor, resolver + anchor, "base-structured-external-resolver")

    # Structured external-ID DATA is an executable plan even when flat routes were
    # correctly removed by the fail-closed V13 route boundary.
    text = once(
        text,
        '''function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  return (NIAKVIO_PROVIDER_MODEL.routes || []).some(route => ["search","detail","player","api"].includes(_routeKind(route)));
}
''',
        '''function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.externalIdentityPlan) && NIAKVIO_PROVIDER_MODEL.externalIdentityPlan.length) return true;
  return (NIAKVIO_PROVIDER_MODEL.routes || []).some(route => ["search","detail","player","api"].includes(_routeKind(route)));
}
''',
        "base-external-plan-runtime-availability",
    )

    # Execute the structured plan before generic flat-route/API fallback. Core TMDB
    # metadata already contains external_ids/imdb_id, so no provider-side TMDB call
    # is needed.
    text = once(
        text,
        '''  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;

  // Declarative ProviderBase recipe: a clean reconstruction may need a bounded
''',
        '''  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;

  if (Array.isArray(NIAKVIO_PROVIDER_MODEL.externalIdentityPlan) && NIAKVIO_PROVIDER_MODEL.externalIdentityPlan.length) {
    const externalMeta = await _tmdb(tmdbId, type) || null;
    const externalStreams = await _resolveExternalIdentityPlan(externalMeta, type, season, episode);
    if (externalStreams.length) return externalStreams;
  }

  // Declarative ProviderBase recipe: a clean reconstruction may need a bounded
''',
        "base-run-structured-external-plan",
    )

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        "_FLAT_ROUTE_DYNAMIC_TOKENS",
        'record.get("requestSpecReusable") is not True',
        "def _flat_route_blocklist",
        "blocked_routes: set[str] | None = None",
        "def _positive_external_identity_plan",
        'patch["external_identity_plan"]',
        'model["externalIdentityPlan"]',
    ):
        if needle not in value:
            raise AssertionError(f"V13 recovery missing: {needle}")


def validate_materializer(text: str | None = None) -> None:
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    for needle in (MATERIALIZER_MARKER, '"externalIdentityPlan"', 'patch.get("external_identity_plan")'):
        if needle not in value:
            raise AssertionError(f"V13 materializer missing: {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        '"externalIdentityPlan"',
        "async function _resolveExternalIdentityPlan",
        "function _externalEpisodeMarker",
        "externalIdentityRequest",
        "imdbId: values.imdbId",
        "manifest|hls|dash|action",
    ):
        if needle not in value:
            raise AssertionError(f"V13 ProviderBase missing: {needle}")


def main() -> int:
    changed = patch_recovery() | patch_materializer() | patch_base()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_ROUTE_PLAN_V13_OK changed={str(changed).lower()} "
        "flat_requires_reusable_dynamic_identity=1 stale_flat_blocked_by_fresh_proof=1 "
        "structured_external_identity_plan=1 episodic_hls_selection=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
