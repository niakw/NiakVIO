#!/usr/bin/env python3
"""Add opt-in proof-grade HTTP tracing to the hardened provider worker.

Normal health/parity output stays unchanged.  When context.routeProofTrace is true,
network observations additionally contain sanitized exact request structure and
bounded response identity hints.  These fields are evidence only; promotion into
runtime DATA is handled by provider_route_proof.py.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_worker.cjs"
MARKER = "NUVIO_PROVIDER_WORKER_ROUTE_PROOF_V1"

HELPERS = r'''
/* NUVIO_PROVIDER_WORKER_ROUTE_PROOF_V1 */
const ROUTE_PROOF_SENSITIVE_KEY = /api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce/i;
const ROUTE_PROOF_SAFE_HEADER = new Set([
  'accept', 'accept-language', 'content-type', 'origin', 'referer', 'referrer',
  'user-agent', 'x-requested-with', 'x-client-version', 'x-app-version',
]);
const ROUTE_PROOF_ID_KEYS = new Set([
  'id', '_id', 'media_id', 'mediaid', 'post_id', 'postid', 'content_id', 'contentid',
  'movie_id', 'movieid', 'series_id', 'seriesid', 'show_id', 'showid', 'slug',
]);

function routeProofSanitizedUrl(input) {
  try {
    const raw = typeof input === 'string' ? input : input?.url;
    const url = new URL(String(raw || ''));
    for (const key of [...url.searchParams.keys()]) {
      if (ROUTE_PROOF_SENSITIVE_KEY.test(key)) url.searchParams.set(key, '<redacted>');
    }
    return url.toString().slice(0, 1600);
  } catch {
    return null;
  }
}

function routeProofHeaders(headers) {
  const out = {};
  try {
    headers?.forEach?.((value, key) => {
      const name = String(key || '').toLowerCase();
      if (!ROUTE_PROOF_SAFE_HEADER.has(name) || ROUTE_PROOF_SENSITIVE_KEY.test(name)) return;
      out[name] = String(value || '').slice(0, 500);
    });
  } catch {}
  return out;
}

function routeProofSafeScalar(key, value) {
  if (ROUTE_PROOF_SENSITIVE_KEY.test(String(key || ''))) return '<redacted>';
  if (!['string', 'number', 'boolean'].includes(typeof value)) return undefined;
  const text = String(value);
  return text.length <= 300 ? value : '{value}';
}

function routeProofBody(body) {
  if (body == null) return { body_kind: 'none', body_fields: [], body_values: {} };
  const out = { body_kind: typeof body, body_fields: [], body_values: {} };
  try {
    if (typeof URLSearchParams !== 'undefined' && body instanceof URLSearchParams) {
      out.body_kind = 'form';
      for (const [key, value] of [...body.entries()].slice(0, 40)) {
        out.body_fields.push(String(key));
        out.body_values[String(key)] = ROUTE_PROOF_SENSITIVE_KEY.test(String(key)) ? '<redacted>' : String(value).slice(0, 300);
      }
      return out;
    }
  } catch {}
  if (typeof body !== 'string') return out;
  const text = body.trim();
  if (!text) return { body_kind: 'empty', body_fields: [], body_values: {} };
  try {
    const value = JSON.parse(text);
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      out.body_kind = 'json';
      for (const [key, raw] of Object.entries(value).slice(0, 40)) {
        out.body_fields.push(String(key));
        const safe = routeProofSafeScalar(key, raw);
        if (safe !== undefined) out.body_values[String(key)] = safe;
      }
      return out;
    }
  } catch {}
  if (text.includes('=')) {
    try {
      const params = new URLSearchParams(text);
      out.body_kind = 'form';
      for (const [key, value] of [...params.entries()].slice(0, 40)) {
        out.body_fields.push(String(key));
        out.body_values[String(key)] = ROUTE_PROOF_SENSITIVE_KEY.test(String(key)) ? '<redacted>' : String(value).slice(0, 300);
      }
      return out;
    } catch {}
  }
  out.body_kind = 'text';
  return out;
}

function routeProofRequestMetadata(input, init, headers) {
  const body = routeProofBody(init?.body);
  return {
    proof_url: routeProofSanitizedUrl(input),
    proof_headers: routeProofHeaders(headers),
    proof_body_kind: body.body_kind,
    proof_body_fields: [...new Set(body.body_fields)].slice(0, 40),
    proof_body_values: body.body_values,
  };
}

function routeProofCollectJsonHints(value, out, depth = 0) {
  if (depth > 5 || out.length >= 100 || value == null) return;
  if (Array.isArray(value)) {
    for (const item of value.slice(0, 40)) routeProofCollectJsonHints(item, out, depth + 1);
    return;
  }
  if (typeof value !== 'object') return;
  for (const [rawKey, child] of Object.entries(value).slice(0, 80)) {
    const key = String(rawKey || '').toLowerCase();
    if (ROUTE_PROOF_ID_KEYS.has(key) && ['string', 'number'].includes(typeof child)) {
      const text = String(child).trim();
      if (text && text.length <= 160 && !ROUTE_PROOF_SENSITIVE_KEY.test(key)) out.push({ key, value: text });
    }
    if (child && typeof child === 'object') routeProofCollectJsonHints(child, out, depth + 1);
    if (out.length >= 100) return;
  }
}

async function routeProofResponseHints(response) {
  const out = [];
  try {
    const type = String(response?.headers?.get?.('content-type') || '').toLowerCase();
    const declared = Number(response?.headers?.get?.('content-length') || 0);
    if (declared > 512 * 1024) return out;
    if (!/(json|html|text)/.test(type)) return out;
    const text = await response.clone().text();
    if (Buffer.byteLength(text) > 512 * 1024) return out;
    if (type.includes('json') || /^[\s]*[\[{]/.test(text)) {
      try {
        const parsed = JSON.parse(text);
        routeProofCollectJsonHints(parsed, out, 0);
      } catch {}
    }
    if (!out.length && /(html|text)/.test(type)) {
      const re = /(?:data[-_])?(id|media[-_]id|post[-_]id|content[-_]id|movie[-_]id|series[-_]id|show[-_]id|slug)[\s"'=:\-]+([A-Za-z0-9._~-]{2,160})/gi;
      let match;
      while ((match = re.exec(text)) !== null && out.length < 100) {
        out.push({ key: String(match[1]).toLowerCase().replace(/-/g, '_'), value: String(match[2]) });
      }
    }
  } catch {}
  const seen = new Set();
  return out.filter((row) => {
    const fp = `${row.key}:${row.value}`;
    if (seen.has(fp)) return false;
    seen.add(fp);
    return true;
  }).slice(0, 80);
}
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    text = replace_once(
        text,
        "\nfunction inferRequestStage(pathPattern) {",
        "\n" + HELPERS + "\nfunction inferRequestStage(pathPattern) {",
        "route-proof-helper-anchor",
    )
    text = replace_once(
        text,
        "      const requestMeta = safeRequestMetadata(input, init);\n      const rawRequestUrl = (() => {",
        "      const requestMeta = safeRequestMetadata(input, init);\n"
        "      const routeProofEnabled = context.routeProofTrace === true;\n"
        "      const routeProofRequest = routeProofEnabled ? routeProofRequestMetadata(input, init, headers) : {};\n"
        "      const rawRequestUrl = (() => {",
        "route-proof-request-metadata",
    )

    legacy_success = "        networkObservations.push({ stage: requestStage, host, method: requestMeta.method, path_pattern: requestMeta.path_pattern, status: response.status, ok: response.ok, duration_ms: Date.now() - started, infrastructure: isInfrastructureHost(host), synthetic_fixture_fallback: synthetic, invocation: activeInvocation, settings_profile: activeSettingsProfile, error_code: null });\n        return wrapLimitedResponse(response, maxResponseBytes, (bytes) => {"
    proof_success = "        const routeProofHints = routeProofEnabled ? await routeProofResponseHints(response) : [];\n        networkObservations.push({\n          stage: requestStage, host, method: requestMeta.method, path_pattern: requestMeta.path_pattern,\n          status: response.status, ok: response.ok, duration_ms: Date.now() - started,\n          infrastructure: isInfrastructureHost(host), synthetic_fixture_fallback: synthetic,\n          invocation: activeInvocation, settings_profile: activeSettingsProfile, error_code: null,\n          ...routeProofRequest,\n          response_value_hints: routeProofHints,\n          content_type: String(response.headers.get('content-type') || '').slice(0, 160) || null,\n          route_proof_trace: routeProofEnabled,\n        });\n        return wrapLimitedResponse(response, maxResponseBytes, (bytes) => {"
    text = replace_once(text, legacy_success, proof_success, "route-proof-success-observation")

    legacy_failure = "        networkObservations.push({ stage: requestStage, host, method: requestMeta.method, path_pattern: requestMeta.path_pattern, status: null, ok: false, duration_ms: Date.now() - started, infrastructure: isInfrastructureHost(host), invocation: activeInvocation, settings_profile: activeSettingsProfile, error_code: error?.code ? String(error.code).slice(0, 120) : null, error: sanitizeDiagnosticText(error?.message || error, 300) });\n        throw error;"
    proof_failure = "        networkObservations.push({\n          stage: requestStage, host, method: requestMeta.method, path_pattern: requestMeta.path_pattern,\n          status: null, ok: false, duration_ms: Date.now() - started, infrastructure: isInfrastructureHost(host),\n          invocation: activeInvocation, settings_profile: activeSettingsProfile,\n          error_code: error?.code ? String(error.code).slice(0, 120) : null,\n          error: sanitizeDiagnosticText(error?.message || error, 300),\n          ...routeProofRequest, response_value_hints: [], route_proof_trace: routeProofEnabled,\n        });\n        throw error;"
    text = replace_once(text, legacy_failure, proof_failure, "route-proof-failure-observation")

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"worker route proof marker count={value.count(MARKER)}")
    for needle in (
        "context.routeProofTrace === true",
        "proof_url:",
        "proof_headers:",
        "proof_body_values:",
        "response_value_hints: routeProofHints",
        "routeProofResponseHints(response)",
    ):
        if needle not in value:
            raise AssertionError(f"worker route proof missing: {needle}")


def main() -> int:
    changed = patch()
    print(f"PROVIDER_WORKER_ROUTE_PROOF_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
