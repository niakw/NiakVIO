'use strict';

// Diagnostic schema only: never retain response scalar values, URLs or text.
const SENSITIVE = /key|token|auth|signature|secret|password|cookie|session|nonce/i;
const IDENTIFIER = /^[A-Za-z_$][\w$-]{0,47}$/;
const PLAYER_ATTRIBUTES = new Set([
  'src', 'data-src', 'href', 'value', 'data-url', 'data-link', 'data-player',
  'data-embed', 'data-video', 'data-code', 'data-iframe', 'data-source',
  'data-player-id', 'data-index', 'data-server',
]);

function addressKind(raw) {
  const value = raw.trim();
  if (!value) return 'empty';
  if (/^(?:https?:)?\/\//i.test(value)) return 'absolute_url';
  if (/^<(?:iframe|video|source)\b/i.test(value)) return 'inline_markup';
  if (/^&lt;(?:iframe|video|source)\b/i.test(value)) return 'escaped_markup';
  if (/^(?:\/(?!\/)|\.\.?\/|\?)/.test(value)) return 'relative_url';
  if (/^#/.test(value)) return 'fragment';
  if (value.length <= 4096) {
    let decoded = '';
    const encoded = value.replace(/^data:text\/html;base64,/i, '');
    if (encoded.length >= 16 && /^[A-Za-z0-9+/_-]+={0,2}$/.test(encoded)) {
      decoded = Buffer.from(encoded, 'base64').toString('utf8').trim();
    }
    if (!decoded && /%(?:3c|3a|2f)/i.test(value)) {
      try { decoded = decodeURIComponent(value).trim(); } catch {}
    }
    if (/^<(?:iframe|video|source)\b/i.test(decoded)) return 'encoded_markup';
    if (/^(?:https?:)?\/\//i.test(decoded)) return 'encoded_url';
  }
  return 'other';
}

function playerMarkup(value) {
  // Independent head/tail samples avoid inventing tags at a joined boundary.
  const samples = value.length > 131072
    ? [value.slice(0, 65536), value.slice(-65536)] : [value];
  const groups = new Map();
  let examined = 0;
  for (const sample of samples) {
    const tags = /<(iframe|video|source|a|button|option|div|li|input)\b([^>]{0,8192})>/gi;
    for (const match of sample.matchAll(tags)) {
      if (++examined > 1024) break;
      const kinds = new Map();
      const values = [];
      const attributes = /\s([A-Za-z_:][\w:.-]{0,47})\s*=\s*(?:"([^"]{0,4096})"|'([^']{0,4096})'|([^\s"'<>`=]{1,4096}))/g;
      for (const attr of match[2].matchAll(attributes)) {
        const name = attr[1].toLowerCase();
        if (PLAYER_ATTRIBUTES.has(name) && kinds.size < 8) {
          kinds.set(name, addressKind(attr[2] ?? attr[3] ?? attr[4] ?? ''));
          values.push([name, attr[2] ?? attr[3] ?? attr[4] ?? '']);
        }
      }
      if (!kinds.size) continue;
      const row = { tag: match[1].toLowerCase(), value_kinds: Object.fromEntries([...kinds].sort()), count: 1, distinct_values: 1 };
      const key = JSON.stringify([row.tag, row.value_kinds]);
      const previous = groups.get(key);
      const signature = JSON.stringify(values.sort());
      if (previous) {
        previous.row.count = Math.min(128, previous.row.count + 1);
        if (previous.values.size < 128) previous.values.add(signature);
        previous.row.distinct_values = previous.values.size;
      } else groups.set(key, { row, values: new Set([signature]) });
    }
  }
  function priority(row) {
    if (Object.values(row.value_kinds).some(kind => /^(?:encoded|escaped|inline)_/.test(kind))) return 0;
    if (/^(?:iframe|video|source)$/.test(row.tag)) return 1;
    if (Object.keys(row.value_kinds).some(name => /^data-(?:player|embed|video|code|iframe|source|server)/.test(name))) return 2;
    return row.tag === 'option' ? 3 : 4;
  }
  return {
    rows: [...groups.values()].map(group => group.row).sort((a, b) => priority(a) - priority(b)).slice(0, 8),
    sampled_chars: samples.reduce((sum, sample) => sum + sample.length, 0),
    truncated: value.length > 131072 || examined > 1024 || groups.size > 8,
  };
}

function responseStructure(value) {
  let root = value;
  const text = typeof value === 'string' ? value.slice(0, 131072) : '';
  if (text && /^[\s]*[\[{]/.test(text)) {
    try { root = JSON.parse(text); } catch {}
  }
  if (root && typeof root === 'object' && !ArrayBuffer.isView(root)
      && !(root instanceof ArrayBuffer) && !(typeof Blob !== 'undefined' && root instanceof Blob)) {
    const fields = [];
    const seen = new Set();
    function walk(node, path, depth) {
      if (depth > 5 || fields.length >= 48 || node == null) return;
      if (Array.isArray(node)) {
        for (const item of node.slice(0, 2)) walk(item, path + '[]', depth + 1);
      } else if (typeof node === 'object') {
        for (const [name, item] of Object.entries(node).slice(0, 64)) {
          if (!IDENTIFIER.test(name) || SENSITIVE.test(name)) continue;
          const next = path ? path + '.' + name : name;
          if (next.length > 160 || seen.has(next) || fields.length >= 48) continue;
          seen.add(next);
          fields.push({ path: next, type: item === null ? 'null' : Array.isArray(item) ? 'array' : typeof item });
          walk(item, next, depth + 1);
        }
      }
    }
    walk(root, '', 0);
    return { kind: 'json', fields };
  }
  if (text && /<(?:html|body|iframe|script|video|source|a|div)\b/i.test(text)) {
    const tags = new Map();
    const pattern = /<(iframe|script|video|source|a|button|select|option)\b([^>]{0,1800})>/gi;
    for (const match of text.matchAll(pattern)) {
      const tag = match[1].toLowerCase();
      const attrs = tags.get(tag) || new Set();
      for (const attr of match[2].matchAll(/\s([A-Za-z_:][\w:.-]{0,47})\s*=/g)) {
        const name = attr[1].toLowerCase();
        if (!SENSITIVE.test(name) && attrs.size < 16) attrs.add(name);
      }
      tags.set(tag, attrs);
    }
    const variables = [...new Set([...text.matchAll(/\b(?:var|let|const)\s+([A-Za-z_$][\w$]{0,47})\s*=/g)]
      .map(row => row[1]).filter(name => !SENSITIVE.test(name)))].slice(0, 16);
    return { kind: 'html', tags: [...tags].map(([tag, attrs]) => ({ tag, attributes: [...attrs].sort() })),
      variables, player_markup: playerMarkup(value) };
  }
  return { kind: text ? 'text' : 'binary' };
}

module.exports = { responseStructure };
