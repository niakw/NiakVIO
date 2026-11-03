'use strict';

const { randomBytes } = require('node:crypto');

const MAX_REFERENCES = 512;
const MAX_URL_LENGTH = 8192;

function safeAddressReference(value) {
  return typeof value === 'string' && /^r[1-9][0-9]{0,2}$/.test(value)
    && value === 'r' + Number(value.slice(1)) && Number(value.slice(1)) <= MAX_REFERENCES ? value : '';
}

function safeAddressScope(value) {
  return typeof value === 'string' && value.length === 17 && /^s[0-9a-f]{16}$/.test(value) ? value : '';
}

function safeAddressFields(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const scope = safeAddressScope(value.address_scope);
  if (!scope) return {};
  const result = { address_scope: scope,
    address_refs_truncated: value.address_refs_truncated !== false,
    address_trace_truncated: value.address_trace_truncated !== false };
  for (const key of ['request_ref', 'response_ref', 'referer_ref']) {
    const reference = safeAddressReference(value[key]);
    if (reference) result[key] = reference;
    else if (value[key]) result.address_refs_truncated = true;
  }
  return result;
}

function createAddressReferences({ limit = MAX_REFERENCES } = {}) {
  const maximum = Number.isInteger(limit) && limit >= 0 ? Math.min(MAX_REFERENCES, limit) : MAX_REFERENCES;
  const scope = 's' + randomBytes(8).toString('hex');
  const references = new Map();
  let truncated = false;

  function ref(value, base) {
    if (typeof value !== 'string' || !value) return '';
    if (value.length > MAX_URL_LENGTH) { truncated = true; return ''; }
    if (typeof base === 'string' && base.length > MAX_URL_LENGTH) { truncated = true; return ''; }
    let url;
    try { url = base === undefined ? new URL(value) : new URL(value, base); }
    catch (_) { return ''; }
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return '';
    url.hash = '';
    const canonical = url.href;
    if (canonical.length > MAX_URL_LENGTH) { truncated = true; return ''; }
    if (references.has(canonical)) return references.get(canonical);
    if (references.size >= maximum) { truncated = true; return ''; }
    const reference = 'r' + (references.size + 1);
    references.set(canonical, reference);
    return reference;
  }

  // The address table stays in this closure; only scoped opaque labels escape.
  return Object.freeze({ scope, ref, get truncated() { return truncated; } });
}

module.exports = { createAddressReferences, safeAddressReference, safeAddressScope, safeAddressFields };
