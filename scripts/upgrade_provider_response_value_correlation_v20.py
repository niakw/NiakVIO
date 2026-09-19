#!/usr/bin/env python3
"""V20: preserve response-value dataflow across HTML catalogue hops.

The route proof engine already correlates JSON id/slug values with later provider
requests. HTML catalogues can expose the same provider-owned identity only inside
an href/src attribute, for example a numeric id embedded in a composite slug.
Dropping that value makes a live-positive search impossible to replay safely.

V20 extends the same proof rule without adding any provider rule:
- bounded HTML response hints extract safe href/src path identities and query values;
- exact prior-response slug values become {slug}; other exact safe response values
  become {id} when consumed by a later request;
- volatile/auth/session/signature values remain non-reusable;
- correlated ProviderValuePlan steps may contain {id}, {slug}, or both;
- ProviderBase selects id+slug from the same title-scored search result;
- episodic detail crawling recognizes the generic /episode/<slug>-S-episode-E form.

Static response text never becomes execution authority by itself: a value is useful
only when the provider subsequently issues a successful HTTP request containing it.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "provider_worker.cjs"
PROOF = ROOT / "scripts" / "provider_route_proof.py"
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MATERIALIZER = ROOT / "scripts" / "materialize_provider_v3_all.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_worker() -> bool:
    text = WORKER.read_text(encoding="utf-8")
    marker = "NUVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20"
    if marker in text:
        validate_worker(text)
        return False
    old = r'''    if (!out.length && /(html|text)/.test(type)) {
      const re = /(?:data[-_])?(id|media[-_]id|post[-_]id|content[-_]id|movie[-_]id|series[-_]id|show[-_]id|slug)[\s"'=:\-]+([A-Za-z0-9._~-]{2,160})/gi;
      let match;
      while ((match = re.exec(text)) !== null && out.length < 100) {
        out.push({ key: String(match[1]).toLowerCase().replace(/-/g, '_'), value: String(match[2]) });
      }
    }
'''
    new = r'''    if (/(html|text)/.test(type)) {
      /* NUVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20 */
      const re = /(?:data[-_])?(id|media[-_]id|post[-_]id|content[-_]id|movie[-_]id|series[-_]id|show[-_]id|slug)[\s"'=:\-]+([A-Za-z0-9._~-]{2,160})/gi;
      let match;
      while ((match = re.exec(text)) !== null && out.length < 100) {
        out.push({ key: String(match[1]).toLowerCase().replace(/-/g, '_'), value: String(match[2]) });
      }

      // Catalogue identities are frequently encoded only in href/src paths.
      // Record bounded safe values as hints; they acquire authority only if a
      // later provider request consumes the exact same value.
      const attrRe = /\b(?:href|src|data-src)\s*=\s*(["'])([^"']{1,900})\1/gi;
      let attrMatch, scanned = 0;
      while ((attrMatch = attrRe.exec(text)) !== null && scanned++ < 240 && out.length < 100) {
        let parsed;
        try { parsed = new URL(attrMatch[2], response?.url || 'https://invalid.local/'); }
        catch { continue; }
        for (const rawPart of parsed.pathname.split('/').filter(Boolean).slice(-4)) {
          let part = rawPart;
          try { part = decodeURIComponent(rawPart); } catch {}
          const withoutExt = part.replace(/\.html?$/i, '');
          const composite = withoutExt.match(/^(\d{2,})[-_.]([A-Za-z0-9._~-]{2,150})$/);
          if (composite) {
            out.push({ key: 'id', value: composite[1] });
            if (out.length < 100 && withoutExt.length <= 160) out.push({ key: 'slug', value: withoutExt });
          }
        }
        for (const [rawKey, rawValue] of [...parsed.searchParams.entries()].slice(0, 20)) {
          const key = String(rawKey || '').toLowerCase();
          const value = String(rawValue || '').trim();
          if (!key || ROUTE_PROOF_SENSITIVE_KEY.test(key) || value.length < 3 || value.length > 160) continue;
          if (!/^[A-Za-z0-9._~-]+$/.test(value)) continue;
          out.push({ key, value });
          if (out.length >= 100) break;
        }
      }
    }
'''
    text = once(text, old, new, "v20-worker-html-response-hints")
    WORKER.write_text(text, encoding="utf-8")
    validate_worker(text)
    return True


def patch_proof() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if MARKER in text:
        validate_proof(text)
        return False

    old_hints = r'''def _provider_hint_values(prior_value_hints: Iterable[dict[str, Any]] | None) -> set[str]:
    out: set[str] = set()
    for row in prior_value_hints or []:
        if not isinstance(row, dict):
            continue
        key = canonical(row.get("key"))
        value = str(row.get("value") or "").strip()
        if key not in PROVIDER_VALUE_KEYS or not value or len(value) < 2 or len(value) > 160:
            continue
        if re.fullmatch(r"[A-Za-z0-9._~-]+", value):
            out.add(value)
    return out


def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:
    rows = fetch.get("response_value_hints")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = canonical(row.get("key"))
        value = str(row.get("value") or "").strip()
        if key in PROVIDER_VALUE_KEYS and value and len(value) <= 160:
            out.append({"key": key, "value": value})
    return out[:80]
'''
    new_hints = r'''# NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20
_PROVIDER_HINT_SENSITIVE_KEY = re.compile(
    r"api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce",
    re.I,
)


def _provider_hint_rows(prior_value_hints: Iterable[dict[str, Any]] | None) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in prior_value_hints or []:
        if not isinstance(row, dict):
            continue
        key = canonical(row.get("key"))
        value = str(row.get("value") or "").strip()
        if not key or not value or len(value) < 2 or len(value) > 160:
            continue
        if _PROVIDER_HINT_SENSITIVE_KEY.search(key) or key in VOLATILE_QUERY_KEYS:
            continue
        if not re.fullmatch(r"[A-Za-z0-9._~-]+", value):
            continue
        fp = (key, value)
        if fp in seen:
            continue
        seen.add(fp)
        out.append({"key": key, "value": value})
    return out[:160]


def _provider_hint_values(prior_value_hints: Iterable[dict[str, Any]] | None) -> set[str]:
    return {row["value"] for row in _provider_hint_rows(prior_value_hints)}


def _provider_hint_values_for_keys(
    prior_value_hints: Iterable[dict[str, Any]] | None,
    keys: set[str],
) -> set[str]:
    wanted = {canonical(value) for value in keys}
    return {row["value"] for row in _provider_hint_rows(prior_value_hints) if row["key"] in wanted}


def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:
    rows = fetch.get("response_value_hints")
    if not isinstance(rows, list):
        return []
    return _provider_hint_rows(rows)[:80]
'''
    text = once(text, old_hints, new_hints, "v20-proof-hint-dataflow")

    text = once(
        text,
        "    provider_values = _provider_hint_values(prior_value_hints)\n\n    tmdb = str(fixture.get(\"tmdbId\") or \"\").strip()\n",
        "    provider_values = _provider_hint_values(prior_value_hints)\n    provider_slugs = _provider_hint_values_for_keys(prior_value_hints, {\"slug\"})\n\n    tmdb = str(fixture.get(\"tmdbId\") or \"\").strip()\n",
        "v20-proof-provider-slug-values",
    )
    text = once(
        text,
        '''        elif decoded in provider_values:\n            placeholder = "{id}"\n        else:\n''',
        '''        elif decoded in provider_slugs:\n            placeholder = "{slug}"\n        elif decoded in provider_values:\n            placeholder = "{id}"\n        else:\n''',
        "v20-proof-path-slug-before-id",
    )
    text = once(
        text,
        '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:\n            placeholder = "{id}"\n''',
        '''        elif value in provider_values and key_l not in VOLATILE_QUERY_KEYS | CONTENT_IDENTITY_QUERY_KEYS:\n            placeholder = "{id}"\n''',
        "v20-proof-query-response-value",
    )
    text = once(
        text,
        '''        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),\n''',
        '''        "providerValueCorrelation": bool(\n            provider_values and any(row.get("placeholder") in {"{id}", "{slug}"} for row in substitutions)\n        ),\n''',
        "v20-proof-correlation-id-or-slug",
    )
    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    marker = "ROUTE_RECOVERY_RESPONSE_VALUE_CORRELATION_V20"
    if marker in text:
        validate_recovery(text)
        return False
    old = '''            and "{id}" in str(row.get("route") or "")\n'''
    new = '''            # ROUTE_RECOVERY_RESPONSE_VALUE_CORRELATION_V20\n            and ("{id}" in str(row.get("route") or "") or "{slug}" in str(row.get("route") or ""))\n'''
    text = once(text, old, new, "v20-recovery-correlated-id-or-slug")
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_materializer() -> bool:
    text = MATERIALIZER.read_text(encoding="utf-8")
    marker = "PROVIDER_RESPONSE_VALUE_CORRELATION_V20"
    if marker in text:
        validate_materializer(text)
        return False
    old = '''                    and "{id}" in str(step.get("route") or "")\n'''
    new = '''                    # PROVIDER_RESPONSE_VALUE_CORRELATION_V20\n                    and ("{id}" in str(step.get("route") or "") or "{slug}" in str(step.get("route") or ""))\n'''
    text = once(text, old, new, "v20-materializer-correlated-id-or-slug")
    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    text = once(
        text,
        '''    id: values.providerId,\n    providerId: values.providerId,\n    tmdbId: values.tmdbId,\n''',
        '''    id: values.providerId,\n    providerId: values.providerId,\n    slug: values.providerSlug,\n    providerSlug: values.providerSlug,\n    tmdbId: values.tmdbId,\n''',
        "v20-base-recipe-url-slug",
    )
    # _recipeExpandScalar has the same mapping, so patch its remaining occurrence.
    text = once(
        text,
        '''    id: values.providerId,\n    providerId: values.providerId,\n    tmdbId: values.tmdbId,\n''',
        '''    id: values.providerId,\n    providerId: values.providerId,\n    slug: values.providerSlug,\n    providerSlug: values.providerSlug,\n    tmdbId: values.tmdbId,\n''',
        "v20-base-recipe-scalar-slug",
    )

    html_anchor = "function _spv18ProviderIdFromHtml(html, meta) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20 */
function _spv20ProviderValuesFromHtml(html, meta) {
  const source = _text(html).slice(0, 786432);
  const anchorRe = /<a\b([^>]*)>([\s\S]*?)<\/a>/gi;
  let match, scanned = 0;
  let bestScore = -1;
  let best = { id: "", slug: "" };
  while ((match = anchorRe.exec(source)) !== null && scanned++ < 400) {
    const label = _htmlVisibleText(match[2]).replace(/\s+/g, " ").trim();
    const score = _spv4TitleScore(label, meta);
    if (score < 90 || score < bestScore) continue;
    const attrs = _text(match[1]);
    let id = "";
    let slug = "";
    const idMatch = attrs.match(/\bdata-(?:id|post-id|media-id|anime-id|movie-id|series-id|show-id)\s*=\s*["']?([A-Za-z0-9._~-]{1,160})/i);
    if (idMatch) id = idMatch[1];
    const hrefMatch = attrs.match(/\bhref\s*=\s*(["'])([^"']{1,900})\1/i);
    if (hrefMatch) {
      try {
        const parsed = new URL(hrefMatch[2], "https://invalid.local/");
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
  if (!best.id) best.id = _spv18ProviderIdFromHtml(source, meta);
  if (!best.slug) best.slug = best.id;
  if (!best.id) best.id = best.slug;
  return best;
}
function _spv20ProviderValuesFromJson(value, meta) {
  const identity = _spv18ProviderIdFromJson(value, meta);
  return { id: identity, slug: identity };
}
'''
    text = once(text, html_anchor, helper + html_anchor, "v20-base-html-provider-values")

    old_resolver = '''      const providerId = typeof searchPayload.value === "string"\n        ? _spv18ProviderIdFromHtml(searchPayload.value, meta)\n        : _spv18ProviderIdFromJson(searchPayload.value, meta);\n      if (!providerId) continue;\n      const values = Object.assign({}, baseValues, { providerId });\n'''
    new_resolver = '''      const providerValues = typeof searchPayload.value === "string"\n        ? _spv20ProviderValuesFromHtml(searchPayload.value, meta)\n        : _spv20ProviderValuesFromJson(searchPayload.value, meta);\n      if (!providerValues || (!providerValues.id && !providerValues.slug)) continue;\n      const values = Object.assign({}, baseValues, {\n        providerId: providerValues.id || providerValues.slug,\n        providerSlug: providerValues.slug || providerValues.id\n      });\n'''
    text = once(text, old_resolver, new_resolver, "v20-base-provider-value-pair")
    text = once(
        text,
        '''        if (!/^https?:\\/\\//i.test(stepBase) || !stepRoute || !/\\{id\\}/i.test(stepRoute)) continue;\n''',
        '''        if (!/^https?:\\/\\//i.test(stepBase) || !stepRoute || !/\\{(?:id|slug)\\}/i.test(stepRoute)) continue;\n''',
        "v20-base-provider-step-id-or-slug",
    )

    old_patterns = r'''    const patterns = [
      new RegExp("/saison[-_/]?0*" + s + "[^?#]*episode[-_/]?0*" + e + "(?:[./?#]|$)", "i"),
      new RegExp("/0*" + s + "-saison/0*" + e + "-episode(?:[./?#]|$)", "i"),
      new RegExp("/episode[-_/]?0*" + e + "(?:[./?#]|$)", "i")
    ];
'''
    new_patterns = r'''    const patterns = [
      new RegExp("/saison[-_/]?0*" + s + "[^?#]*episode[-_/]?0*" + e + "(?:[./?#]|$)", "i"),
      new RegExp("/0*" + s + "-saison/0*" + e + "-episode(?:[./?#]|$)", "i"),
      new RegExp("/episode/[^?#/]*-(?:saison-)?0*" + s + "-episode-0*" + e + "(?:[./?#-]|$)", "i"),
      new RegExp("/[^?#/]*-(?:saison-)?0*" + s + "-episode-0*" + e + "(?:[./?#-]|$)", "i"),
      new RegExp("/episode[-_/]?0*" + e + "(?:[./?#]|$)", "i")
    ];
'''
    text = once(text, old_patterns, new_patterns, "v20-base-generic-episode-slug-pattern")

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_worker(text: str | None = None) -> None:
    value = text if text is not None else WORKER.read_text(encoding="utf-8")
    for needle in (
        "NUVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20",
        "const attrRe = /\\b(?:href|src|data-src)",
        "out.push({ key: 'id', value: composite[1] });",
        "out.push({ key: 'slug', value: withoutExt });",
        "ROUTE_PROOF_SENSITIVE_KEY.test(key)",
    ):
        if needle not in value:
            raise AssertionError(f"V20 worker missing {needle}")


def validate_proof(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "def _provider_hint_rows",
        "def _provider_hint_values_for_keys",
        'provider_slugs = _provider_hint_values_for_keys(prior_value_hints, {"slug"})',
        'placeholder = "{slug}"',
        'key_l not in VOLATILE_QUERY_KEYS | CONTENT_IDENTITY_QUERY_KEYS',
        'row.get("placeholder") in {"{id}", "{slug}"}',
    ):
        if needle not in value:
            raise AssertionError(f"V20 proof missing {needle}")


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    if "ROUTE_RECOVERY_RESPONSE_VALUE_CORRELATION_V20" not in value or '"{slug}" in str(row.get("route")' not in value:
        raise AssertionError("V20 recovery id/slug correlation missing")


def validate_materializer(text: str | None = None) -> None:
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    if "PROVIDER_RESPONSE_VALUE_CORRELATION_V20" not in value or '"{slug}" in str(step.get("route")' not in value:
        raise AssertionError("V20 materializer id/slug projection missing")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "function _spv20ProviderValuesFromHtml",
        "function _spv20ProviderValuesFromJson",
        "providerSlug: values.providerSlug",
        "providerSlug: providerValues.slug || providerValues.id",
        r"/\{(?:id|slug)\}/i.test(stepRoute)",
        'new RegExp("/episode/[^?#/]*-(?:saison-)?0*" + s + "-episode-0*" + e',
    ):
        if needle not in value:
            raise AssertionError(f"V20 ProviderBase missing {needle}")

    lower = value[value.index(MARKER): value.index("function _spv18ProviderIdFromHtml", value.index(MARKER))].casefold()
    for forbidden in ("animesama", "animevostfr", "french-manga", "jujutsu"):
        if forbidden in lower:
            raise AssertionError(f"V20 provider-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_RESPONSE_VALUE_CORRELATION_V20_OK changed={str(changed).lower()} "
        "html_href_hints=1 exact_response_dataflow=1 id_slug_pair=1 volatile_fail_closed=1 "
        "generic_episode_slug=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
