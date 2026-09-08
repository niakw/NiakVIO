#!/usr/bin/env python3
"""V20.4: preserve proof-backed form DATA and propagate response identity state.

This migration owns the remaining generic response-dataflow gaps exposed by live
replay after V20.3:

- small static form constants must not become fixture residue just because their
  value equals a season/episode number;
- bounded title+season search expressions must remain reusable;
- response-owned id/slug values must evolve after every proven step;
- response-correlated composite path segments such as
  ``slug-1-episode-1`` must remain executable instead of being discarded merely
  because the whole path segment is not equal to one scalar placeholder.

All rules remain provider-agnostic. Volatile/auth/session values stay fail-closed.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20_3 as v203  # noqa: E402

PROOF = v203.PROOF
BASE = v203.BASE
RECOVERY = v203.v202.legacy.RECOVERY
MARKER = "PROVIDER_RESPONSE_VALUE_CORRELATION_V20_4"
BASE_MARKER = "NIAKVIO_PROVIDER_RESPONSE_VALUE_STATEFUL_V20_4"
RECOVERY_MARKER = "ROUTE_RECOVERY_RESPONSE_VALUE_DIAGNOSTICS_V20_4"

patch_worker = v203.patch_worker
patch_materializer = v203.patch_materializer
validate_worker = v203.validate_worker
validate_materializer = v203.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_proof() -> bool:
    v203.patch_proof()
    text = PROOF.read_text(encoding="utf-8")
    if MARKER in text:
        validate_proof(text)
        return False

    helper_anchor = "def _urlencoded_text_body_spec(\n"
    helper = r'''# PROVIDER_RESPONSE_VALUE_CORRELATION_V20_4
def _urlencoded_search_query_template(
    key: object,
    raw_value: object,
    fixture: dict[str, Any],
) -> str | None:
    """Recognize a bounded title + season search expression without provider rules."""
    if canonical(key) not in BODY_TITLE_KEYS:
        return None
    value = str(raw_value if raw_value is not None else "").strip()
    season = str(fixture.get("season") or "").strip()
    if not value or not season or not season.isdigit():
        return None
    titles = unique([fixture.get("title"), *(fixture.get("aliases") or [])], 24)
    for raw_title in titles:
        title = str(raw_title or "").strip()
        if not title:
            continue
        pattern = re.compile(
            r"^" + re.escape(title) + r"\s*(?:[-–—:]\s*)?"
            r"(saison|season|s)\s*0*" + re.escape(season) + r"$",
            re.I,
        )
        match = pattern.match(value)
        if match:
            keyword = match.group(1)
            return "{query} " + keyword + " {season}"
    return None


def _composite_provider_path_segment_template(
    decoded: object,
    fixture: dict[str, Any],
    provider_values: set[str],
    provider_slugs: set[str],
) -> str | None:
    """Abstract only bounded episode-shaped path segments backed by current DATA.

    The runtime already owns ``{slug}``, ``{season}``, and ``{episode}``.
    This helper deliberately does not generalize arbitrary mixed path strings.
    """
    value = str(decoded or "").strip()
    season = str(fixture.get("season") or "").strip()
    episode = str(fixture.get("episode") or "").strip()
    if not value or not season or not episode or not season.isdigit() or not episode.isdigit():
        return None

    lower = value.casefold()
    trusted_slugs = []
    for slug in [*sorted(provider_slugs, key=len, reverse=True), *_slug_candidates(fixture)]:
        slug_text = str(slug or "").strip().casefold()
        if slug_text and slug_text not in trusted_slugs:
            trusted_slugs.append(slug_text)

    templates = (
        ("-{season}-episode-{episode}", "-{season}-episode-{episode}"),
        ("-saison-{season}-episode-{episode}", "-saison-{season}-episode-{episode}"),
        ("-season-{season}-episode-{episode}", "-season-{season}-episode-{episode}"),
    )
    for slug in trusted_slugs:
        for observed_suffix, template_suffix in templates:
            observed = slug + observed_suffix.format(season=season, episode=episode)
            if lower == observed:
                return "{slug}" + template_suffix

    for provider_id in sorted((str(v) for v in provider_values if v), key=len, reverse=True):
        pid = provider_id.casefold()
        for observed_suffix, template_suffix in templates:
            observed = pid + observed_suffix.format(season=season, episode=episode)
            if lower == observed:
                return "{id}" + template_suffix
    return None


'''
    text = _once(text, helper_anchor, helper + helper_anchor, "v20.4-proof-helpers")

    old_tokens = '''    fixture_tokens = unique([
        fixture.get("tmdbId"), fixture.get("title"), fixture.get("year"),
        fixture.get("season"), fixture.get("episode"), *provider_values,
    ], 32)
'''
    new_tokens = '''    # V20.4: semantic season/episode/year values are dynamic only on their
    # own semantic keys. Do not classify unrelated tiny literals (for example a
    # pagination constant) as fixture residue merely because they equal "1".
    fixture_tokens = [
        str(token)
        for token in unique([
            fixture.get("tmdbId"), fixture.get("title"), *(fixture.get("aliases") or []),
            *provider_values,
        ], 32)
        if len(str(token or "").strip()) >= 4
    ]
'''
    count = text.count(old_tokens)
    if count != 2:
        raise AssertionError(f"v20.4-static-token-scope: expected two anchors, got {count}")
    text = text.replace(old_tokens, new_tokens)

    old_placeholder = '''        placeholder = _request_scalar_placeholder(key, value, fixture, provider_values)
        if placeholder:
'''
    new_placeholder = '''        placeholder = _request_scalar_placeholder(key, value, fixture, provider_values)
        if not placeholder:
            placeholder = _urlencoded_search_query_template(key, value, fixture)
        if placeholder:
'''
    count = text.count(old_placeholder)
    if count != 2:
        raise AssertionError(f"v20.4-search-query-template: expected two anchors, got {count}")
    text = text.replace(old_placeholder, new_placeholder)

    old_path = '''        elif decoded in provider_values:
            placeholder = "{id}"
        else:
            for slug in _slug_candidates(fixture):
                if canonical(decoded) == canonical(slug):
                    placeholder = "{slug}"
                    break
'''
    new_path = '''        elif decoded in provider_values:
            placeholder = "{id}"
        else:
            for slug in _slug_candidates(fixture):
                if canonical(decoded) == canonical(slug):
                    placeholder = "{slug}"
                    break
            if not placeholder:
                placeholder = _composite_provider_path_segment_template(
                    decoded, fixture, provider_values, provider_slugs
                )
'''
    text = _once(text, old_path, new_path, "v20.4-composite-provider-path")

    old_correlation = '''        "providerValueCorrelation": bool(
            provider_values and any(row.get("placeholder") in {"{id}", "{slug}"} for row in substitutions)
        ),
'''
    new_correlation = '''        "providerValueCorrelation": bool(
            provider_values and any(
                "{id}" in str(row.get("placeholder") or "")
                or "{slug}" in str(row.get("placeholder") or "")
                for row in substitutions
            )
        ),
'''
    text = _once(text, old_correlation, new_correlation, "v20.4-composite-correlation")

    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def patch_recovery() -> bool:
    v203.patch_recovery()
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False
    old = '''        "requestSpec": copy.deepcopy(request_spec),
        "requestSpecReusable": bool(derivation.get("requestSpecReusable")),
        "status": int(fetch.get("status") or 0),
'''
    new = '''        "requestSpec": copy.deepcopy(request_spec),
        "requestSpecReusable": bool(derivation.get("requestSpecReusable")),
        # ROUTE_RECOVERY_RESPONSE_VALUE_DIAGNOSTICS_V20_4
        # proof_body_values is already redacted by the worker for sensitive keys.
        "requestSpecSubstitutions": copy.deepcopy(derivation.get("requestSpecSubstitutions") or []),
        "requestSpecResidue": copy.deepcopy(derivation.get("requestSpecResidue") or []),
        "proofBodyKind": fetch.get("body_kind"),
        "proofBodyValues": copy.deepcopy(fetch.get("body_values") or {}),
        "status": int(fetch.get("status") or 0),
'''
    text = _once(text, old, new, "v20.4-recovery-diagnostics")
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_base() -> bool:
    v203.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False

    resolver_anchor = "async function _resolveProviderValuePlan(meta, mediaType, season, episode) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_RESPONSE_VALUE_STATEFUL_V20_4 */
function _spv204ResponseProviderValues(value, base, meta) {
  if (value && typeof value === "object") {
    return _spv20ProviderValuesFromJson(value, meta) || { id: "", slug: "" };
  }
  const source = _text(value).slice(0, 786432);
  let pair = _spv20ProviderValuesFromHtml(source, meta) || { id: "", slug: "" };
  let bestId = "";
  let bestIdCount = 0;
  const idCounts = new Map();

  const attrRe = /\b(?:href|src|data-src)\s*=\s*(["'])([^"']{1,900})\1/gi;
  let match, scanned = 0;
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
      const count = (idCounts.get(candidate) || 0) + 1;
      idCounts.set(candidate, count);
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
    const count = (idCounts.get(candidate) || 0) + 1;
    idCounts.set(candidate, count);
    if (count > bestIdCount) {
      bestId = candidate;
      bestIdCount = count;
    }
  }

  if (bestId) pair.id = bestId;
  if (!pair.slug) pair.slug = pair.id || "";
  return pair;
}
'''
    text = _once(text, resolver_anchor, helper + resolver_anchor, "v20.4-stateful-response-helper")

    old_values = '''      const values = Object.assign({}, baseValues, {
        providerId,
        providerSlug: providerValues.slug || providerValues.id || providerId
      });
'''
    new_values = '''      let values = Object.assign({}, baseValues, {
        providerId,
        providerSlug: providerValues.slug || providerValues.id || providerId
      });
'''
    text = _once(text, old_values, new_values, "v20.4-mutable-provider-values")

    for stage in ("step_shape_rejected", "step_url_empty", "step_fetch", "step_response"):
        text = _once(
            text,
            f'_spv184Trace("{stage}", mediaType, providerId, stepIndex, stepRoute);',
            f'_spv184Trace("{stage}", mediaType, values.providerId, stepIndex, stepRoute);',
            f"v20.4-trace-current-id-{stage}",
        )

    old_payload = '''        const payload = await _recipePayload(stepUrl, {}, stepSpec, values);
        _spv184Trace("step_response", mediaType, values.providerId, stepIndex, stepRoute);
        let urls = [];
'''
    new_payload = '''        const payload = await _recipePayload(stepUrl, {}, stepSpec, values);
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
    text = _once(text, old_payload, new_payload, "v20.4-step-response-state-propagation")
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_proof(text: str | None = None) -> None:
    v203.validate_proof(text)
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "def _urlencoded_search_query_template",
        "def _composite_provider_path_segment_template",
        'return "{query} " + keyword + " {season}"',
        'if len(str(token or "").strip()) >= 4',
        "placeholder = _urlencoded_search_query_template(key, value, fixture)",
        "placeholder = _composite_provider_path_segment_template(",
        '"{slug}" in str(row.get("placeholder") or "")',
    ):
        if needle not in value:
            raise AssertionError(f"V20.4 proof missing {needle}")
    if value.count("placeholder = _urlencoded_search_query_template(key, value, fixture)") != 2:
        raise AssertionError("V20.4 must cover both form and urlencoded-text body paths")


def validate_recovery(text: str | None = None) -> None:
    v203.validate_recovery(text)
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        '"requestSpecResidue": copy.deepcopy',
        '"proofBodyValues": copy.deepcopy(fetch.get("body_values") or {})',
    ):
        if needle not in value:
            raise AssertionError(f"V20.4 recovery diagnostics missing {needle}")


def validate_base(text: str | None = None) -> None:
    v203.validate_base(text)
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        "function _spv204ResponseProviderValues",
        "let values = Object.assign({}, baseValues",
        "const nextProviderValues = _spv204ResponseProviderValues(",
        "providerId: nextProviderValues.id || values.providerId",
        "providerSlug: nextProviderValues.slug || values.providerSlug",
        "const idCounts = new Map();",
        '_spv184Trace("step_fetch", mediaType, values.providerId, stepIndex, stepRoute);',
    ):
        if needle not in value:
            raise AssertionError(f"V20.4 ProviderBase missing {needle}")
    resolver = value[value.index(BASE_MARKER):]
    if "const values = Object.assign({}, baseValues" in resolver:
        raise AssertionError("V20.4 provider values remain immutable")
    lower = resolver[:12000].casefold()
    for forbidden in ("animesama", "animevostfr", "french-manga", "jujutsu", "purstream"):
        if forbidden in lower:
            raise AssertionError(f"V20.4 provider-specific token leaked: {forbidden}")


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
        f"PROVIDER_RESPONSE_VALUE_CORRELATION_V20_4_OK changed={str(changed).lower()} "
        "static_form_constants=1 form_and_text_paths=1 composite_title_season_query=1 "
        "composite_response_path=1 stateful_response_identity=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
