#!/usr/bin/env python3
"""Teach the common ProviderBase to replay proof-v5 per-route request specs.

Provider-specific method/header/body values remain structured DATA. The common
reader expands placeholders and executes them. No provider-specific algorithm is
introduced in ProviderBase or provider Lego.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_ROUTE_REQUEST_SPEC_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    old_payload = '''async function _recipePayload(url, recipe, body) {
  const headers = Object.assign({}, recipe.requestHeaders || {});
  if (recipe.referer) headers.Referer = recipe.referer;
  if (recipe.origin) headers.Origin = recipe.origin;
  const options = { headers };
  const requestTimeoutMs = Math.max(0, Number(recipe.requestTimeoutMs || 0) || 0);
  if (requestTimeoutMs > 0) {
    try {
      let timeoutMs = requestTimeoutMs;
      const deadline = Number(globalThis && globalThis.__nuvioProviderDeadlineMs);
      if (Number.isFinite(deadline) && deadline > 0) timeoutMs = Math.max(1, Math.min(timeoutMs, deadline - Date.now()));
      if (typeof AbortSignal !== "undefined" && AbortSignal.timeout) options.signal = AbortSignal.timeout(timeoutMs);
    } catch (_) {}
  }
  if (body != null) {
    options.method = "POST";
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await _fetch(url, options);
  const type = _text(response.headers.get("content-type")).toLowerCase();
  if (type.includes("json")) return { value: await response.json(), base: response.url || url };
  const text = await response.text();
  try { return { value: JSON.parse(text), base: response.url || url }; }
  catch (_) { return { value: text, base: response.url || url }; }
}'''
    new_payload = '''/* NIAKVIO_PROVIDER_BASE_ROUTE_REQUEST_SPEC_V1 */
function _recipeExpandScalar(value, values) {
  if (typeof value !== "string") return value;
  const replacements = {
    query: values.query,
    title: values.query,
    id: values.providerId,
    providerId: values.providerId,
    tmdbId: values.tmdbId,
    tmdb_id: values.tmdbId,
    media: values.media,
    type: values.media,
    season: values.season,
    episode: values.episode,
    source: values.source
  };
  return value.replace(/\\{([^}]+)\\}/g, (match, key) => {
    const replacement = replacements[key];
    return replacement == null ? "" : _text(replacement);
  });
}
function _recipeExpandObject(value, values) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return value;
  const out = {};
  for (const [key, raw] of Object.entries(value)) {
    if (raw && typeof raw === "object" && !Array.isArray(raw)) out[key] = _recipeExpandObject(raw, values);
    else if (Array.isArray(raw)) out[key] = raw.map(item => _recipeExpandScalar(item, values));
    else out[key] = _recipeExpandScalar(raw, values);
  }
  return out;
}
function _recipeRequestSpec(recipe, key, values) {
  const raw = recipe && recipe[key];
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const method = _text(raw.method || "GET").toUpperCase();
  if (!/^(?:GET|POST|PUT|PATCH|DELETE|HEAD)$/.test(method)) return null;
  const spec = { method, headers: _recipeExpandObject(raw.headers || {}, values) || {} };
  const bodyKind = _text(raw.bodyKind || "").toLowerCase();
  const body = _recipeExpandObject(raw.body || {}, values);
  if (bodyKind === "json" && body && typeof body === "object") {
    spec.body = JSON.stringify(body);
    if (!Object.keys(spec.headers).some(key => key.toLowerCase() === "content-type")) spec.headers["Content-Type"] = "application/json";
  } else if (bodyKind === "form" && body && typeof body === "object") {
    spec.body = Object.entries(body).map(([key, value]) => encodeURIComponent(key) + "=" + encodeURIComponent(_text(value))).join("&");
    if (!Object.keys(spec.headers).some(key => key.toLowerCase() === "content-type")) spec.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8";
  }
  return spec;
}
async function _recipePayload(url, recipe, requestSpec, values) {
  const headers = Object.assign({}, recipe.requestHeaders || {}, requestSpec && requestSpec.headers || {});
  if (recipe.referer && !headers.Referer && !headers.referer) headers.Referer = recipe.referer;
  if (recipe.origin && !headers.Origin && !headers.origin) headers.Origin = recipe.origin;
  const options = { headers };
  if (requestSpec && requestSpec.method) options.method = requestSpec.method;
  if (requestSpec && requestSpec.body != null) options.body = requestSpec.body;
  const requestTimeoutMs = Math.max(0, Number(recipe.requestTimeoutMs || 0) || 0);
  if (requestTimeoutMs > 0) {
    try {
      let timeoutMs = requestTimeoutMs;
      const deadline = Number(globalThis && globalThis.__nuvioProviderDeadlineMs);
      if (Number.isFinite(deadline) && deadline > 0) timeoutMs = Math.max(1, Math.min(timeoutMs, deadline - Date.now()));
      if (typeof AbortSignal !== "undefined" && AbortSignal.timeout) options.signal = AbortSignal.timeout(timeoutMs);
    } catch (_) {}
  }
  const response = await _fetch(url, options);
  const type = _text(response.headers.get("content-type")).toLowerCase();
  if (type.includes("json")) return { value: await response.json(), base: response.url || url };
  const text = await response.text();
  try { return { value: JSON.parse(text), base: response.url || url }; }
  catch (_) { return { value: text, base: response.url || url }; }
}'''
    text = once(text, old_payload, new_payload, "route-request-payload")

    text = once(
        text,
        'const payload = await _recipePayload(url, recipe, null);',
        'const payload = await _recipePayload(url, recipe, _recipeRequestSpec(recipe, "directRequest", localValues), localValues);',
        "direct-request-spec",
    )
    # The next two identical legacy calls occur in search and resolveRoute.
    legacy = 'const payload = await _recipePayload(url, recipe, null);'
    if text.count(legacy) != 2:
        raise AssertionError(f"search/resolve payload anchors={text.count(legacy)}")
    text = text.replace(
        legacy,
        'const payload = await _recipePayload(url, recipe, _recipeRequestSpec(recipe, "searchRequest", values), values);',
        1,
    )
    text = text.replace(
        legacy,
        'const requestKey = media === "movie" ? "movieRequest" : "episodeRequest";\n        const payload = await _recipePayload(url, recipe, _recipeRequestSpec(recipe, requestKey, values), values);',
        1,
    )

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"route request marker count={value.count(MARKER)}")
    for needle in (
        '_recipeRequestSpec(recipe, "directRequest", localValues)',
        '_recipeRequestSpec(recipe, "searchRequest", values)',
        'media === "movie" ? "movieRequest" : "episodeRequest"',
        'bodyKind === "json"',
        'bodyKind === "form"',
    ):
        if needle not in value:
            raise AssertionError(f"route request reader missing: {needle}")


def main() -> int:
    changed = patch()
    print(f"PROVIDER_BASE_ROUTE_REQUEST_SPEC_V1_OK changed={str(changed).lower()} data_owned=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
