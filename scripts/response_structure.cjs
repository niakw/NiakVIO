'use strict';

// Diagnostic schema only: never retain response scalar values, URLs or text.
const SENSITIVE = /key|token|auth|signature|secret|password|cookie|session|nonce/i;
const IDENTIFIER = /^[A-Za-z_$][\w$-]{0,47}$/;
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
    return { kind: 'html', tags: [...tags].map(([tag, attrs]) => ({ tag, attributes: [...attrs].sort() })), variables };
  }
  return { kind: text ? 'text' : 'binary' };
}

module.exports = { responseStructure };
