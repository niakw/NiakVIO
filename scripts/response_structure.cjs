'use strict';

// Diagnostic schema only: never retain response scalar values, URLs or text.
const SENSITIVE = /key|token|auth|signature|secret|password|cookie|session|nonce/i;
const IDENTIFIER = /^[A-Za-z_$][\w$-]{0,47}$/;
const PLAYER_ATTRIBUTES = new Set([
  'src', 'data-src', 'href', 'value', 'data-url', 'data-link', 'data-player',
  'data-embed', 'data-video', 'data-code', 'data-iframe', 'data-source',
  'data-player-id', 'data-index', 'data-server',
]);

function decodedAddress(value) {
  if (value.length <= 4096) {
    let decoded = '';
    const encoded = value.replace(/^data:text\/html;base64,/i, '');
    if (encoded.length >= 16 && /^[A-Za-z0-9+/_-]+={0,2}$/.test(encoded)) {
      decoded = Buffer.from(encoded, 'base64').toString('utf8').trim();
    }
    if (!decoded && /%(?:3c|3a|2f)/i.test(value)) {
      try { decoded = decodeURIComponent(value).trim(); } catch {}
    }
    return decoded;
  }
  return '';
}

function addressKind(raw) {
  const value = raw.trim();
  if (!value) return 'empty';
  if (/^(?:https?:)?\/\//i.test(value)) return 'absolute_url';
  if (/^<(?:iframe|video|source)\b/i.test(value)) return 'inline_markup';
  if (/^&lt;(?:iframe|video|source)\b/i.test(value)) return 'escaped_markup';
  if (/^(?:\/(?!\/)|\.\.?\/|\?)/.test(value)) return 'relative_url';
  if (/^#/.test(value)) return 'fragment';
  const decoded = decodedAddress(value);
  if (/^<(?:iframe|video|source)\b/i.test(decoded)) return 'encoded_markup';
  if (/^(?:https?:)?\/\//i.test(decoded)) return 'encoded_url';
  return 'other';
}

function addressShape(raw, valueKind, baseUrl) {
  const unknown = { kind: 'unknown', origin: 'unknown' };
  if (!['absolute_url', 'relative_url', 'encoded_url'].includes(valueKind)) return unknown;
  try {
    const value = valueKind === 'encoded_url' ? decodedAddress(raw.trim()) : raw.trim();
    const url = new URL(value.replace(/&(?:amp|#0*38|#x0*26);/gi, '&'), baseUrl || undefined);
    if (!/^https?:$/.test(url.protocol)) return unknown;
    let origin = 'unknown';
    try { origin = url.origin === new URL(baseUrl).origin ? 'same_origin' : 'cross_origin'; } catch {}
    const path = url.pathname.toLowerCase();
    let kind = 'other';
    if (/\.(?:jpe?g|png|gif|webp|avif|svg|ico)$/.test(path)) kind = 'image_extension';
    else if (/\.(?:js|mjs|cjs)$/.test(path)) kind = 'script_extension';
    else if (/\.css$/.test(path)) kind = 'style_extension';
    else if (/\.(?:m3u8|mpd|mp4|mkv|webm|m4v)$/.test(path)) kind = 'media_extension';
    else if (/\/(?:e|embed|player|watch|play|video|stream|server|source)(?:[/.\-]|$)/.test(path)
             || [...url.searchParams.keys()].slice(0, 16).some(key =>
               /(?:^|[_-])(?:embed|player|server|source)(?:$|[_-])|^(?:trembed|embedId|playerId|serverId|sourceId)$/i.test(key))) kind = 'embed_route';
    else if (/\.(?:html?|php)$/.test(path)) kind = 'page_extension';
    return { kind, origin };
  } catch { return unknown; }
}

function safeAddressReference(value) {
  return typeof value === 'string' && /^r[1-9][0-9]{0,2}$/.test(value)
    && value === 'r' + Number(value.slice(1))
    && Number(value.slice(1)) <= 512 ? value : '';
}

function playerMarkup(value, baseUrl, addressRef) {
  // Independent head/tail samples avoid inventing tags at a joined boundary.
  const samples = value.length > 131072
    ? [value.slice(0, 65536), value.slice(-65536)] : [value];
  const groups = new Map();
  const collectAddresses = typeof addressRef === 'function';
  let examined = 0;
  for (const sample of samples) {
    const tags = /<(iframe|video|source|a|button|option|div|li|input)\b([^>]{0,8192})>/gi;
    for (const match of sample.matchAll(tags)) {
      if (++examined > 1024) break;
      const kinds = new Map();
      const shapes = new Map();
      const values = [];
      const attributes = /\s([A-Za-z_:][\w:.-]{0,47})\s*=\s*(?:"([^"]{0,4096})"|'([^']{0,4096})'|([^\s"'<>`=]{1,4096}))/g;
      for (const attr of match[2].matchAll(attributes)) {
        const name = attr[1].toLowerCase();
        if (PLAYER_ATTRIBUTES.has(name) && kinds.size < 8) {
          const raw = attr[2] ?? attr[3] ?? attr[4] ?? '';
          const kind = addressKind(raw);
          kinds.set(name, kind);
          shapes.set(name, addressShape(raw, kind, baseUrl));
          values.push([name, raw]);
        }
      }
      if (!kinds.size) continue;
      const row = { tag: match[1].toLowerCase(), value_kinds: Object.fromEntries([...kinds].sort()),
        value_shapes: Object.fromEntries([...shapes].sort()), count: 1, distinct_values: 1 };
      const key = JSON.stringify([row.tag, row.value_kinds, row.value_shapes]);
      let group = groups.get(key);
      const signature = JSON.stringify(values.sort());
      if (group) {
        group.row.count = Math.min(128, group.row.count + 1);
        if (group.values.size < 128) group.values.add(signature);
        group.row.distinct_values = group.values.size;
      } else {
        group = { row, values: new Set([signature]) };
        groups.set(key, group);
      }
      if (collectAddresses) {
        for (const [name, raw] of values) {
          const kind = addressKind(raw);
          if (['inline_markup', 'escaped_markup', 'encoded_markup'].includes(kind)) {
            group.addressRefsTruncated = true;
            continue;
          }
          if (!['absolute_url', 'relative_url', 'encoded_url'].includes(kind)) continue;
          let canonical;
          try {
            const address = kind === 'encoded_url' ? decodedAddress(raw.trim()) : raw.trim();
            const url = new URL(address.replace(/&(?:amp|#0*38|#x0*26);/gi, '&'), baseUrl || undefined);
            if (!/^https?:$/.test(url.protocol)) continue;
            url.hash = '';
            canonical = url.href;
          } catch {
            group.addressRefsTruncated = true;
            continue;
          }
          group.addresses ||= new Map();
          let addresses = group.addresses.get(name);
          if (!addresses) group.addresses.set(name, addresses = new Set());
          if (addresses.has(canonical)) continue;
          if (addresses.size >= 16) { group.addressRefsTruncated = true; continue; }
          addresses.add(canonical);
        }
      }
    }
  }
  function priority(row) {
    if (Object.values(row.value_kinds).some(kind => /^(?:encoded|escaped|inline)_/.test(kind))) return 0;
    if (/^(?:iframe|video|source)$/.test(row.tag)) return 1;
    if (Object.keys(row.value_kinds).some(name => /^data-(?:src|player|embed|video|code|iframe|source|server)/.test(name))) return 2;
    return row.tag === 'option' ? 3 : 4;
  }
  const selected = [...groups.values()].sort((a, b) => priority(a.row) - priority(b.row)).slice(0, 8);
  let addressRefsTruncated = false;
  if (collectAddresses) {
    for (const group of selected) {
      const refs = {};
      for (const [name, addresses] of group.addresses || []) {
        const references = new Set();
        for (const address of addresses) {
          let reference;
          try { reference = safeAddressReference(addressRef(address, { tag: group.row.tag, attribute: name })); } catch {}
          if (reference) references.add(reference);
          else group.addressRefsTruncated = true;
        }
        if (references.size) refs[name] = [...references];
      }
      if (Object.keys(refs).length) group.row.address_refs = refs;
      group.row.address_refs_truncated = group.addressRefsTruncated === true;
      addressRefsTruncated ||= group.row.address_refs_truncated;
    }
  }
  return {
    rows: selected.map(group => group.row),
    sampled_chars: samples.reduce((sum, sample) => sum + sample.length, 0),
    truncated: value.length > 131072 || examined > 1024 || groups.size > 8 || addressRefsTruncated,
  };
}

function scriptTokens(source) {
  // This is a bounded syntax sampler, not an evaluator. Strings and regexes
  // stay opaque so their contents cannot invent object keys or imports.
  const tokens = [];
  const parentheses = [];
  let offset = 0;
  while (offset < source.length && tokens.length < 16384) {
    const ch = source[offset], next = source[offset + 1];
    if (/\s/.test(ch)) { offset++; continue; }
    if (ch === '/' && next === '/') {
      const end = source.indexOf('\n', offset + 2);
      offset = end < 0 ? source.length : end + 1;
      continue;
    }
    if (ch === '/' && next === '*') {
      const end = source.indexOf('*/', offset + 2);
      offset = end < 0 ? source.length : end + 2;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      const quote = ch;
      let value = '', closed = false;
      offset++;
      while (offset < source.length) {
        const current = source[offset++];
        if (current === quote) { closed = true; break; }
        if (current !== '\\') { value += current; continue; }
        const escaped = source[offset++];
        if (escaped === undefined) break;
        if (escaped === '\n') continue;
        if (escaped === '\r') { if (source[offset] === '\n') offset++; continue; }
        const width = escaped === 'x' ? 2 : escaped === 'u' ? 4 : 0;
        const hex = source.slice(offset, offset + width);
        if (width && new RegExp('^[0-9a-f]{' + width + '}$', 'i').test(hex)) {
          value += String.fromCharCode(parseInt(hex, 16));
          offset += width;
        } else {
          value += ({ n: '\n', r: '\r', t: '\t', b: '\b', f: '\f', v: '\v' })[escaped] ?? escaped;
        }
      }
      if (closed) tokens.push({ type: 'string', value, quote });
      continue;
    }
    const previous = tokens[tokens.length - 1];
    const regexPrefix = !previous || previous.closesControl
      || previous.type === 'punctuation' && ['=', '(', ':', ',', '[', '!', '&', '|', '?', ';', '{', '}'].includes(previous.value)
      || previous.type === 'identifier' && ['return', 'throw', 'case', 'yield', 'void', 'typeof', 'else', 'do'].includes(previous.value);
    if (ch === '/' && regexPrefix) {
      let inClass = false;
      offset++;
      while (offset < source.length) {
        const current = source[offset++];
        if (current === '\\') { offset++; continue; }
        if (current === '[') inClass = true;
        else if (current === ']') inClass = false;
        else if (current === '/' && !inClass) break;
        else if (current === '\n' || current === '\r') break;
      }
      while (/[A-Za-z]/.test(source[offset] || '') && offset < source.length) offset++;
      tokens.push({ type: 'opaque', value: 'regex' });
      continue;
    }
    const name = source.slice(offset, offset + 256).match(/^[A-Za-z_$][\w$]*/);
    if (name) {
      tokens.push({ type: 'identifier', value: name[0] });
      offset += name[0].length;
      continue;
    }
    const number = source.slice(offset, offset + 256).match(/^(?:0[xX][\da-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|(?:\d[\d_]*(?:\.[\d_]*)?|\.[\d_]+)(?:[eE][+-]?[\d_]+)?)(?:n)?/);
    if (number) {
      tokens.push({ type: number[0].endsWith('n') ? 'opaque' : 'number', value: 'number' });
      offset += number[0].length;
      continue;
    }
    if (ch === '(') parentheses.push(previous?.type === 'identifier'
      && ['if', 'while', 'for', 'switch', 'catch', 'with'].includes(previous.value));
    const closesControl = ch === ')' && parentheses.pop() === true;
    tokens.push({ type: 'punctuation', value: ch, ...(closesControl ? { closesControl: true } : {}) });
    offset++;
  }
  return tokens;
}

function inlineScriptFacts(text) {
  const fields = new Map(), resources = new Map();
  function resource(raw, location) {
    if (typeof raw !== 'string' || !raw || raw.length > 4096 || /\s/.test(raw)) return;
    let kind;
    if (/^https?:\/\//i.test(raw)) kind = 'absolute_url';
    else if (/^\/\//.test(raw)) kind = 'protocol_relative_url';
    else if (/^\//.test(raw)) kind = 'root_relative_url';
    else if (/^[a-z][a-z0-9+.-]*:/i.test(raw) || /^[#?]/.test(raw)) return;
    else kind = 'relative_path';
    let pathname;
    try { pathname = new URL(raw, 'https://diagnostic.invalid/').pathname; } catch { return; }
    let role = 'other_script';
    if (/(?:^|\/)_app\/immutable\/entry\/app\.[A-Za-z0-9_.-]+\.js$/.test(pathname)) role = 'app_entry';
    else if (/(?:^|\/)_app\/immutable\/entry\/start\.[A-Za-z0-9_.-]+\.js$/.test(pathname)) role = 'start_entry';
    else if (/(?:^|\/)(?:_app\/immutable\/)?chunks\/[A-Za-z0-9_.-]+\.js$/.test(pathname)) role = 'chunk';
    const row = { kind, role, location };
    resources.set(JSON.stringify(row), row);
  }
  const scripts = /<!--[\s\S]*?(?:-->|$)|<script\b((?:"[^"]*"|'[^']*'|[^'">]){0,8192})>([\s\S]*?)(?:<\/script\s*>|$)/gi;
  let examined = 0;
  for (const script of text.matchAll(scripts)) {
    if (script[1] === undefined) continue;
    if (++examined > 256) break;
    const attributes = [...script[1].matchAll(/\s([A-Za-z_:][\w:.-]{0,47})\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'<>`=]+))/g)];
    const src = attributes.find(row => row[1].toLowerCase() === 'src');
    if (src) { resource(src[2] ?? src[3] ?? src[4], 'src_attribute'); continue; }
    const tokens = scriptTokens(script[2]), stack = [];
    for (let index = 0; index < tokens.length; index++) {
      const token = tokens[index], previous = tokens[index - 1], parent = stack[stack.length - 1];
      if (token.type === 'identifier' && token.value === 'import' && previous?.value !== '.') {
        if (tokens[index + 1]?.type === 'string') resource(tokens[index + 1].value, 'inline_import');
        else if (tokens[index + 1]?.value === '(' && tokens[index + 2]?.type === 'string') {
          resource(tokens[index + 2].value, 'inline_import');
        } else if (tokens[index + 1]?.value !== '.') {
          for (let next = index + 1; next < Math.min(tokens.length, index + 65); next++) {
            if (tokens[next].value === ';') break;
            if (tokens[next].value === 'from' && tokens[next + 1]?.type === 'string') {
              resource(tokens[next + 1].value, 'inline_import'); break;
            }
          }
        }
      }
      if (token.type === 'punctuation' && ['{', '[', '('].includes(token.value)) {
        const object = token.value === '{' && (!previous && tokens[index + 1]?.type === 'string'
          || previous && (/^(?:=|\(|\[|return|yield|\?)$/.test(previous.value)
            || previous.value === ',' && ['object', 'array'].includes(parent?.kind)
            || previous.value === ':' && parent?.kind === 'object'));
        const key = previous?.value === ':' ? tokens[index - 2] : null;
        const sensitive = parent?.sensitive || (key && SENSITIVE.test(key.value));
        stack.push({ open: token.value, kind: object ? 'object' : token.value === '[' ? 'array' : 'other', sensitive });
        continue;
      }
      if (token.type === 'punctuation' && ['}', ']', ')'].includes(token.value)) { stack.pop(); continue; }
      if (fields.size >= 12 || parent?.kind !== 'object' || parent.sensitive
          || previous?.type !== 'punctuation' || !['{', ','].includes(previous.value) || tokens[index + 1]?.value !== ':'
          || !['identifier', 'string'].includes(token.type) || token.quote === '`'
          || !/^[A-Za-z_$][\w$]{0,47}$/.test(token.value) || SENSITIVE.test(token.value)) continue;
      let value = tokens[index + 2], type;
      if (value?.value === '-' || value?.value === '+') value = tokens[index + 3];
      if (value?.type === 'string') type = 'string';
      else if (value?.type === 'number') type = 'number';
      else if (value?.value === 'true' || value?.value === 'false') type = 'boolean';
      else if (value?.value === 'null') type = 'null';
      else if (value?.value === '{') type = 'object';
      else if (value?.value === '[') type = 'array';
      if (!type) continue;
      const row = { name: token.value, type, key_syntax: token.type === 'string' ? 'quoted' : 'bare' };
      fields.set(JSON.stringify(row), row);
    }
  }
  const priority = { app_entry: 0, start_entry: 1, chunk: 2, other_script: 3 };
  return { inline_fields: [...fields.values()], script_resources: [...resources.values()]
    .sort((a, b) => priority[a.role] - priority[b.role]).slice(0, 8) };
}

function responseStructure(value, options = {}) {
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
      variables, player_markup: playerMarkup(value, options?.baseUrl, options?.addressRef),
      ...inlineScriptFacts(text) };
  }
  return { kind: text ? 'text' : 'binary' };
}

module.exports = { responseStructure };
