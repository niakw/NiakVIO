#!/usr/bin/env python3
"""V20.5: dependency-ready provider-value replay and nested runtime URL harvesting.

Live V20.4 proof showed two generic residual losses:
- correlated chains were truncated to four steps, which can drop the response step
  that produces the identity required by earlier deferred player routes;
- the runtime conflated a catalogue slug with an opaque provider id, so {id}
  requests could execute before an actual id was observed;
- proof-backed JSON responses can store player URLs under arbitrary server labels,
  which the key-name-only URL walker ignored.

V20.5 keeps id and slug readiness distinct, replays proof steps in bounded
multi-pass dependency order, preserves up to eight proof-correlated steps, and
harvests bounded HTTP(S) JSON string values at runtime. It remains provider-
agnostic and does not persist response URLs or volatile response values.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20_4 as v204  # noqa: E402

PROOF = v204.PROOF
BASE = v204.BASE
RECOVERY = v204.RECOVERY
MATERIALIZER = v204.v203.v202.legacy.MATERIALIZER
MARKER = "NIAKVIO_PROVIDER_RESPONSE_VALUE_DEPENDENCY_V20_5"
RECOVERY_MARKER = "ROUTE_RECOVERY_PROVIDER_VALUE_CAUSAL_DEPTH_V20_5"
MATERIALIZER_MARKER = "PROVIDER_VALUE_CAUSAL_DEPTH_V20_5"

patch_worker = v204.patch_worker
patch_proof = v204.patch_proof
validate_worker = v204.validate_worker
validate_proof = v204.validate_proof


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_recovery() -> bool:
    v204.patch_recovery()
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False
    old = "                for row in correlated[:4]\n"
    new = "                # ROUTE_RECOVERY_PROVIDER_VALUE_CAUSAL_DEPTH_V20_5\n                for row in correlated[:8]\n"
    text = _once(text, old, new, "v20.5-correlated-step-depth")
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_materializer() -> bool:
    v204.patch_materializer()
    text = MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER in text:
        validate_materializer(text)
        return False
    old = '''        "providerValuePlan": [
            dict(row)
            for row in (patch.get("provider_value_plan") or static_model.get("providerValuePlan") or [])
            if isinstance(row, dict)
        ][:12],
'''
    new = '''        # PROVIDER_VALUE_CAUSAL_DEPTH_V20_5
        "providerValuePlan": [
            dict(row)
            for row in (patch.get("provider_value_plan") or static_model.get("providerValuePlan") or [])
            if isinstance(row, dict)
        ][:12],
'''
    text = _once(text, old, new, "v20.5-materializer-marker")
    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def patch_base() -> bool:
    v204.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    helper_anchor = "function _spv204ResponseProviderValues(value, base, meta) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_RESPONSE_VALUE_DEPENDENCY_V20_5 */
function _spv205SeasonSignal(raw, season) {
  const text = _text(raw).toLowerCase();
  const wanted = Number(season);
  if (!text || !Number.isFinite(wanted) || wanted <= 0) return 0;
  const patterns = [
    /(?:saison|season)[\s._-]*0*(\d{1,3})\b/i,
    /(?:^|[^a-z0-9])s0*(\d{1,3})(?:[^a-z0-9]|$)/i,
    /-(\d{1,3})-episode-/i
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (!match) continue;
    const found = Number(match[1]);
    if (!Number.isFinite(found)) continue;
    return found === wanted ? 80 : -120;
  }
  return 0;
}
function _spv205StrictProviderValues(value, base, meta, season) {
  if (value && typeof value === "object") {
    const id = _spv18ProviderIdFromJson(value, meta) || "";
    let slug = "";
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
      .sort((a,b)=>b.score-a.score)
      .slice(0, 12);
    for (const item of rows) {
      const candidate = _spv4Scalar((item.row || {}).slug);
      if (candidate && candidate.length <= 160 && /^[A-Za-z0-9._~-]+$/.test(candidate)) {
        slug = candidate;
        break;
      }
    }
    return { id, slug };
  }

  const source = _text(value).slice(0, 786432);
  let bestScore = -1e9;
  let best = { id: "", slug: "" };
  const anchorRe = /<a\b([^>]*)>([\s\S]*?)<\/a>/gi;
  let match, scanned = 0;
  while ((match = anchorRe.exec(source)) !== null && scanned++ < 400) {
    const attrs = _text(match[1]);
    const label = _htmlVisibleText(match[2]).replace(/\s+/g, " ").trim();
    const hrefMatch = attrs.match(/\bhref\s*=\s*(["'])([^"']{1,900})\1/i);
    const href = hrefMatch ? hrefMatch[2] : "";
    const score = _spv4TitleScore(label, meta) + _spv205SeasonSignal(label + " " + href, season);
    if (score < 90 || score < bestScore) continue;
    let id = "";
    let slug = "";
    const idMatch = attrs.match(/\bdata-(?:id|post-id|media-id|anime-id|movie-id|series-id|show-id)\s*=\s*["']?([A-Za-z0-9._~-]{1,160})/i);
    if (idMatch) id = idMatch[1];
    if (href) {
      try {
        const parsed = new URL(href, base || "https://invalid.local/");
        const raw = parsed.pathname.split("/").filter(Boolean).pop() || "";
        const segment = decodeURIComponent(raw).replace(/\.html?$/i, "");
        if (/^[A-Za-z0-9._~-]{2,160}$/.test(segment)) {
          slug = segment;
          const numeric = segment.match(/^(\d{2,})[-_.]/);
          if (!id && numeric) id = numeric[1];
        }
      } catch (_) {}
    }
    if (!id && !slug) continue;
    if (score > bestScore) {
      bestScore = score;
      best = { id, slug };
    }
  }

  const pathRe = /(?:https?:\/\/[^\s"'<>]{1,300}\/)?(\d{2,}-[A-Za-z0-9._~-]{2,150})\.html(?:[?#][^\s"'<>]*)?/gi;
  scanned = 0;
  while ((match = pathRe.exec(source)) !== null && scanned++ < 240) {
    const segment = _text(match[1]);
    const numeric = segment.match(/^(\d{2,})[-_.]/);
    if (!numeric) continue;
    const label = segment.replace(/^\d+[-_.]?/, "").replace(/[._-]+/g, " ");
    const score = _spv4TitleScore(label, meta) + _spv205SeasonSignal(segment, season);
    if (score < 90 || score < bestScore) continue;
    bestScore = score;
    best = { id: numeric[1], slug: segment };
  }

  let bestId = "";
  let bestIdCount = 0;
  const counts = new Map();
  const attrRe = /\b(?:href|src|data-src)\s*=\s*(["'])([^"']{1,900})\1/gi;
  scanned = 0;
  while ((match = attrRe.exec(source)) !== null && scanned++ < 320) {
    let parsed;
    try { parsed = new URL(match[2], base || "https://invalid.local/"); }
    catch (_) { continue; }
    for (const [rawKey, rawValue] of [...parsed.searchParams.entries()].slice(0, 24)) {
      const key = _text(rawKey).trim().toLowerCase();
      const candidate = _text(rawValue).trim();
      if (!key || !candidate || candidate.length > 160) continue;
      if (/api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce|hash|expires?|timestamp|^ts$/i.test(key)) continue;
      if (/^(?:tmdb|tmdbid|tmdb_id|imdb|imdbid|imdb_id|season|season_number|episode|episode_number|year)$/i.test(key)) continue;
      if (!/(?:^|[_-])id$|id$/i.test(key)) continue;
      if (!/^[A-Za-z0-9._~-]{1,160}$/.test(candidate)) continue;
      const count = (counts.get(candidate) || 0) + 1;
      counts.set(candidate, count);
      if (count > bestIdCount) {
        bestId = candidate;
        bestIdCount = count;
      }
    }
  }
  const dataIdRe = /\bdata-(?:id|[a-z0-9_-]*[_-]id)\s*=\s*["']?([A-Za-z0-9._~-]{1,160})/gi;
  scanned = 0;
  while ((match = dataIdRe.exec(source)) !== null && scanned++ < 320) {
    const candidate = _text(match[1]).trim();
    if (!candidate) continue;
    const count = (counts.get(candidate) || 0) + 1;
    counts.set(candidate, count);
    if (count > bestIdCount) {
      bestId = candidate;
      bestIdCount = count;
    }
  }
  if (bestId) best.id = bestId;
  return best;
}
function _spv205HttpValues(value, base, out, depth) {
  out = out || [];
  depth = Number(depth) || 0;
  if (out.length >= 160 || depth > 8 || value == null) return out;
  if (typeof value === "string") {
    const raw = _text(value).trim();
    if (!/^https?:\/\//i.test(raw) || raw.length > 4096) return out;
    try {
      const parsed = new URL(raw, base || undefined);
      if (!/^https?:$/i.test(parsed.protocol) || parsed.username || parsed.password) return out;
      if (/\.(?:jpe?g|png|webp|gif|svg|ico)(?:[?#]|$)/i.test(parsed.pathname)) return out;
      out.push(parsed.toString());
    } catch (_) {}
    return out;
  }
  if (Array.isArray(value)) {
    for (const child of value.slice(0, 160)) {
      _spv205HttpValues(child, base, out, depth + 1);
      if (out.length >= 160) break;
    }
    return out;
  }
  if (typeof value !== "object") return out;
  let scannedEntries = 0;
  for (const [rawKey, child] of Object.entries(value)) {
    if (scannedEntries++ >= 160 || out.length >= 160) break;
    const key = _text(rawKey).toLowerCase();
    if (/api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce|hash|expires?|timestamp|^ts$/i.test(key)) continue;
    _spv205HttpValues(child, base, out, depth + 1);
  }
  return out;
}
'''
    text = _once(text, helper_anchor, helper + helper_anchor, "v20.5-runtime-helpers")

    old_depth = '''                ][:4],
                "semanticTypes": [
'''
    new_depth = '''                ][:8],
                "semanticTypes": [
'''
    text = _once(text, old_depth, new_depth, "v20.5-base-materialized-step-depth")

    old_identity_tail = r'''      providerValues = providerValues || { id: "", slug: "" };
      const providerId = providerValues.id || providerValues.slug || "";
      _spv184Trace(providerId ? "identity_hit" : "identity_miss", mediaType, providerId, -1, searchRoute);
      if (!providerId) continue;
      let values = Object.assign({}, baseValues, {
        providerId,
        providerSlug: providerValues.slug || providerValues.id || providerId
      });
      const valueSteps = (plan.steps || []).slice(0, 4);
      for (let stepIndex = 0; stepIndex < valueSteps.length; stepIndex += 1) {
        const step = valueSteps[stepIndex];
        const stepBase = _text(step && step.base);
        const stepRoute = _text(step && step.route);
        if (!/^https?:\/\//i.test(stepBase) || !stepRoute || !/\{(?:id|slug)\}/i.test(stepRoute)) {
          _spv184Trace("step_shape_rejected", mediaType, values.providerId, stepIndex, stepRoute);
          continue;
        }
        const stepUrl = _recipeUrl(stepRoute, values, stepBase);
        if (!stepUrl) {
          _spv184Trace("step_url_empty", mediaType, values.providerId, stepIndex, stepRoute);
          continue;
        }
        _spv184Trace("step_fetch", mediaType, values.providerId, stepIndex, stepRoute);
        const stepSpec = _recipeRequestSpec(
          { providerValueStep: step.requestSpec || { method: "GET" } },
          "providerValueStep",
          values
        );
        const payload = await _recipePayload(stepUrl, {}, stepSpec, values);
        _spv184Trace("step_response", mediaType, values.providerId, stepIndex, stepRoute);
        const nextProviderValues = _spv204ResponseProviderValues(
          payload.value,
          payload.base || stepUrl,
          meta
        ) || { id: "", slug: "" };
        if (nextProviderValues.id || nextProviderValues.slug) {
          values = Object.assign({}, values, {
            providerId: nextProviderValues.id || values.providerId,
            providerSlug: nextProviderValues.slug || values.providerSlug
          });
        }
        let urls = [];
'''
    new_identity_tail = r'''      providerValues = _spv205StrictProviderValues(
        searchPayload.value,
        searchPayload.base || searchUrl,
        meta,
        season
      ) || { id: "", slug: "" };
      const providerTraceId = providerValues.id || providerValues.slug || "";
      _spv184Trace(providerTraceId ? "identity_hit" : "identity_miss", mediaType, providerTraceId, -1, searchRoute);
      if (!providerValues.id && !providerValues.slug) continue;
      let values = Object.assign({}, baseValues, {
        providerId: providerValues.id || "",
        providerSlug: providerValues.slug || ""
      });
      const valueSteps = (plan.steps || []).slice(0, 8);
      const completedSteps = new Set();
      for (let dependencyPass = 0; dependencyPass < valueSteps.length + 1; dependencyPass += 1) {
        let progressed = false;
        for (let stepIndex = 0; stepIndex < valueSteps.length; stepIndex += 1) {
          if (completedSteps.has(stepIndex)) continue;
          const step = valueSteps[stepIndex];
          const stepBase = _text(step && step.base);
          const stepRoute = _text(step && step.route);
          if (!/^https?:\/\//i.test(stepBase) || !stepRoute || !/\{(?:id|slug)\}/i.test(stepRoute)) {
            completedSteps.add(stepIndex);
            _spv184Trace("step_shape_rejected", mediaType, values.providerId, stepIndex, stepRoute);
            continue;
          }
          const needsId = /\{id\}/i.test(stepRoute);
          const needsSlug = /\{slug\}/i.test(stepRoute);
          if ((needsId && !values.providerId) || (needsSlug && !values.providerSlug)) {
            _spv184Trace("step_deferred", mediaType, values.providerId || values.providerSlug, stepIndex, stepRoute);
            continue;
          }
          completedSteps.add(stepIndex);
          progressed = true;
          const stepUrl = _recipeUrl(stepRoute, values, stepBase);
          if (!stepUrl) {
            _spv184Trace("step_url_empty", mediaType, values.providerId, stepIndex, stepRoute);
            continue;
          }
          _spv184Trace("step_fetch", mediaType, values.providerId || values.providerSlug, stepIndex, stepRoute);
          const stepSpec = _recipeRequestSpec(
            { providerValueStep: step.requestSpec || { method: "GET" } },
            "providerValueStep",
            values
          );
          const payload = await _recipePayload(stepUrl, {}, stepSpec, values);
          _spv184Trace("step_response", mediaType, values.providerId || values.providerSlug, stepIndex, stepRoute);
          const nextProviderValues = _spv205StrictProviderValues(
            payload.value,
            payload.base || stepUrl,
            meta,
            season
          ) || { id: "", slug: "" };
          if (nextProviderValues.id || nextProviderValues.slug) {
            values = Object.assign({}, values, {
              providerId: nextProviderValues.id || values.providerId,
              providerSlug: nextProviderValues.slug || values.providerSlug
            });
          }
          let urls = [];
'''
    text = _once(text, old_identity_tail, new_identity_tail, "v20.5-dependency-runtime-loop")

    old_object_urls = '''          urls = _uniq([
            ..._jsonUrls(payload.value),
            ..._sourceUrls(payload.value, payload.base),
            ..._spv18ValueUrls(payload.value, payload.base, [])
          ]);
'''
    new_object_urls = '''          urls = _uniq([
            ..._jsonUrls(payload.value),
            ..._sourceUrls(payload.value, payload.base),
            ..._spv18ValueUrls(payload.value, payload.base, []),
            ..._spv205HttpValues(payload.value, payload.base, [])
          ]);
'''
    text = _once(text, old_object_urls, new_object_urls, "v20.5-arbitrary-json-http-values")

    old_loop_close = '''        if (crawl.length) {
          const streams = await _crawlDirectMedia(crawl.slice(0, 10), payload.base || stepUrl, 3);
          if (streams.length) return streams.slice(0, 40);
        }
      }
    } catch (_) {}
'''
    new_loop_close = '''        if (crawl.length) {
          const streams = await _crawlDirectMedia(crawl.slice(0, 10), payload.base || stepUrl, 3);
          if (streams.length) return streams.slice(0, 40);
        }
        }
        if (!progressed) break;
      }
    } catch (_) {}
'''
    text = _once(text, old_loop_close, new_loop_close, "v20.5-close-dependency-pass")

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_recovery(text: str | None = None) -> None:
    v204.validate_recovery(text)
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER not in value or "for row in correlated[:8]" not in value:
        raise AssertionError("V20.5 recovery causal depth missing")
    if "for row in correlated[:4]" in value:
        raise AssertionError("V20.5 recovery still truncates correlated steps at four")


def validate_materializer(text: str | None = None) -> None:
    v204.validate_materializer(text)
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER not in value:
        raise AssertionError("V20.5 materializer marker missing")


def validate_base(text: str | None = None) -> None:
    v204.validate_base(text)
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "function _spv205StrictProviderValues",
        "function _spv205HttpValues",
        "const valueSteps = (plan.steps || []).slice(0, 8);",
        "const completedSteps = new Set();",
        '"step_deferred"',
        "if (!progressed) break;",
        "providerId: providerValues.id || \"\"",
        "providerSlug: providerValues.slug || \"\"",
        "..._spv205HttpValues(payload.value, payload.base, [])",
    ):
        if needle not in value:
            raise AssertionError(f"V20.5 ProviderBase missing {needle}")
    if '                ][:4],\n                "semanticTypes"' in value:
        raise AssertionError("V20.5 ProviderBase still truncates materialized value steps at four")
    if '                ][:8],\n                "semanticTypes"' not in value:
        raise AssertionError("V20.5 ProviderBase eight-step materialization missing")
    window = value[value.index(MARKER): value.index("async function _resolveSearchRequestPlan", value.index(MARKER))].casefold()
    for forbidden in ("animesama", "animevostfr", "french-manga", "jujutsu", "vidzy", "purstream"):
        if forbidden in window:
            raise AssertionError(f"V20.5 provider-specific token leaked: {forbidden}")


def main() -> int:
    changed = (
        patch_worker()
        | patch_proof()
        | patch_recovery()
        | patch_materializer()
        | patch_base()
    )
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_RESPONSE_VALUE_CORRELATION_V20_5_OK changed={str(changed).lower()} "
        "strict_id_slug_readiness=1 dependency_passes=1 correlated_depth=8 "
        "nested_json_http_values=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
