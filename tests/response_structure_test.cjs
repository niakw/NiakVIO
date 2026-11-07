'use strict';
const assert = require('node:assert/strict');
const { responseStructure } = require('../scripts/response_structure.cjs');
const payload = JSON.stringify({data: {sources: [{file: 'https://example.test/video?token=PRIVATE', label: 'PRIVATE'}]}, auth: {token: 'PRIVATE'}});
const result = responseStructure(payload);
assert.equal(result.kind, 'json');
assert.ok(result.fields.some(row => row.path === 'data.sources[].file' && row.type === 'string'));
assert.ok(!JSON.stringify(result).includes('PRIVATE'));
assert.doesNotMatch(JSON.stringify(result), /example\.test/i);
assert.ok(!JSON.stringify(result).includes('token'));
const html = responseStructure('<html><iframe data-src="PRIVATE" src="about:blank"></iframe><script>var players = "PRIVATE"; const authToken="PRIVATE";</script></html>');
assert.ok(html.tags.some(row => row.tag === 'iframe' && row.attributes.includes('data-src')));
assert.deepEqual(html.variables, ['players']);
assert.ok(!JSON.stringify(html).includes('PRIVATE'));
const cycle = {}; cycle.data = cycle;
assert.ok(responseStructure(cycle).fields.length <= 48);
assert.ok(JSON.stringify(responseStructure('<script>' + 'var x=1;'.repeat(50000))).length < 2000);
assert.equal(responseStructure(new ArrayBuffer(8)).kind, 'binary');
const markup = responseStructure('<html><a href="/catalogue">PRIVATE</a>' +
  '<iframe src="https://private.test/embed?token=PRIVATE"></iframe>' +
  '<option value="/episode/PRIVATE">PRIVATE</option>' +
  '<button data-code="' + Buffer.from('<iframe src="https://private.test/PRIVATE"></iframe>').toString('base64') +
  '" data-token="PRIVATE"></button><iframe src="https://other.test/embed/PRIVATE"></iframe></html>').player_markup;
assert.deepEqual(markup.rows.find(row => row.tag === 'iframe'), {
  tag: 'iframe', value_kinds: { src: 'absolute_url' }, count: 2, distinct_values: 2,
  value_shapes: { src: { kind: 'embed_route', origin: 'unknown' } },
});
assert.deepEqual(markup.rows.find(row => row.tag === 'option').value_kinds, { value: 'relative_url' });
assert.deepEqual(markup.rows[0].value_kinds, { 'data-code': 'encoded_markup' });
assert.ok(!JSON.stringify(markup).includes('PRIVATE'));
assert.doesNotMatch(JSON.stringify(markup), /private\.test/i);
assert.ok(!JSON.stringify(markup).includes('token'));
const tail = responseStructure('<html>' + ' '.repeat(150000) + '<iframe data-src="/PRIVATE"></iframe></html>').player_markup;
assert.equal(tail.truncated, true);
assert.equal(tail.sampled_chars, 131072);
assert.deepEqual(tail.rows[0].value_kinds, { 'data-src': 'relative_url' });
const flood = responseStructure('<html>' + '<iframe src="/PRIVATE"></iframe>'.repeat(3000)).player_markup;
assert.ok(flood.rows.length <= 8);
assert.equal(flood.rows[0].count, 128);
assert.equal(flood.rows[0].distinct_values, 1);
assert.equal(flood.truncated, true);
const shapes = responseStructure('<html><div data-src="https://cdn.private.test/PRIVATE.jpg?token=PRIVATE"></div>' +
  '<option value="/show/PRIVATE.html">PRIVATE</option><iframe src="/?trembed=PRIVATE"></iframe>' +
  '<source src="//media.private.test/PRIVATE.m3u8?key=PRIVATE">' +
  '<a href="/PRIVATE.js">PRIVATE</a><a href="/PRIVATE.css">PRIVATE</a></html>',
  { baseUrl: 'https://provider.test/show/episode.html' }).player_markup;
const shape = (tag, attribute) => shapes.rows.find(row => row.tag === tag && row.value_shapes[attribute]).value_shapes[attribute];
assert.deepEqual(shape('div', 'data-src'), { kind: 'image_extension', origin: 'cross_origin' });
assert.deepEqual(shape('option', 'value'), { kind: 'page_extension', origin: 'same_origin' });
assert.deepEqual(shape('iframe', 'src'), { kind: 'embed_route', origin: 'same_origin' });
assert.deepEqual(shape('source', 'src'), { kind: 'media_extension', origin: 'cross_origin' });
assert.ok(shapes.rows.some(row => row.value_shapes.href?.kind === 'script_extension'));
assert.ok(shapes.rows.some(row => row.value_shapes.href?.kind === 'style_extension'));
assert.ok(!JSON.stringify(shapes).includes('PRIVATE'));
assert.doesNotMatch(JSON.stringify(shapes), /private\.test/i);
const encoded = responseStructure('<html><iframe data-src="' +
  Buffer.from('https://private.test/embed/PRIVATE').toString('base64') + '"></iframe></html>',
  { baseUrl: 'https://provider.test/episode.html' }).player_markup.rows[0];
assert.equal(encoded.value_kinds['data-src'], 'encoded_url');
assert.deepEqual(encoded.value_shapes['data-src'], { kind: 'embed_route', origin: 'cross_origin' });
assert.ok(!JSON.stringify(encoded).includes('PRIVATE'));

function referenceCollector() {
  const addresses = new Map();
  const calls = [];
  return {
    addresses, calls,
    ref(address) {
      calls.push(address);
      if (!addresses.has(address)) addresses.set(address, 'r' + (addresses.size + 1));
      return addresses.get(address);
    },
  };
}

const queryReferences = referenceCollector();
const queryMarkup = '<html>' + [1, 2, 3].map(index =>
  '<div data-src="?player=PRIVATE_' + index + '&amp;mode=PRIVATE#fragment"></div>').join('') + '</html>';
const queryOptions = { baseUrl: 'https://provider.private.test/episode.html', addressRef: queryReferences.ref };
const queries = responseStructure(queryMarkup, queryOptions).player_markup;
assert.equal(queries.rows.length, 1);
assert.equal(queries.rows[0].count, 3);
assert.equal(queries.rows[0].distinct_values, 3);
assert.deepEqual(queries.rows[0].address_refs, { 'data-src': ['r1', 'r2', 'r3'] });
assert.deepEqual(queryReferences.calls, [1, 2, 3].map(index =>
  'https://provider.private.test/episode.html?player=PRIVATE_' + index + '&mode=PRIVATE'));
assert.equal(queries.truncated, false);
assert.equal(queries.rows[0].address_refs_truncated, false);
assert.ok(!JSON.stringify(queries).includes('PRIVATE'));
assert.doesNotMatch(JSON.stringify(queries), /private\.test/i);
assert.ok(!JSON.stringify(queries).includes('fragment'));

const metadataMarkup = '<html><div data-src="/embed/PRIVATE"></div>' +
  '<source src="//cdn.private.test/PRIVATE.m3u8"></html>';
const metadataCalls = [];
const metadataReferences = referenceCollector();
const withMetadata = responseStructure(metadataMarkup, {
  baseUrl: queryOptions.baseUrl,
  addressRef(address, metadata) {
    metadataCalls.push({ address, metadata });
    return metadataReferences.ref(address);
  },
});
assert.deepEqual(metadataCalls, [
  { address: 'https://cdn.private.test/PRIVATE.m3u8', metadata: { tag: 'source', attribute: 'src' } },
  { address: 'https://provider.private.test/embed/PRIVATE', metadata: { tag: 'div', attribute: 'data-src' } },
]);
const singleArgumentReferences = referenceCollector();
assert.deepEqual(withMetadata, responseStructure(metadataMarkup,
  { baseUrl: queryOptions.baseUrl, addressRef: singleArgumentReferences.ref }));
assert.ok(!JSON.stringify(withMetadata).includes('PRIVATE'));
assert.doesNotMatch(JSON.stringify(withMetadata), /private\.test/i);

const unionReferences = referenceCollector();
const unionMarkup = '<html><iframe src="/embed/PRIVATE#one" data-src="/embed/PRIVATE_A"></iframe>' +
  '<iframe src="/embed/PRIVATE#two" data-src="/embed/PRIVATE_B"></iframe>' +
  '<iframe src="/embed/PRIVATE#two" data-src="/embed/PRIVATE_B"></iframe></html>';
const union = responseStructure(unionMarkup, { baseUrl: queryOptions.baseUrl, addressRef: unionReferences.ref }).player_markup;
assert.equal(union.rows[0].count, 3);
assert.equal(union.rows[0].distinct_values, 2);
assert.deepEqual(union.rows[0].address_refs, { 'data-src': ['r1', 'r2'], src: ['r3'] });
assert.equal(unionReferences.calls.length, 3);
assert.ok(unionReferences.calls.every(address => !address.includes('#')));
const unionWithoutRefs = responseStructure(unionMarkup, { baseUrl: queryOptions.baseUrl }).player_markup;
const { address_refs: unionRefs, address_refs_truncated: unionTruncated, ...unionStructure } = union.rows[0];
assert.deepEqual(unionStructure, unionWithoutRefs.rows[0]);
assert.equal(unionTruncated, false);

const encodedReferences = referenceCollector();
const encodedAddress = 'https://cdn.private.test/embed/PRIVATE?player=PRIVATE&amp;mode=PRIVATE#fragment';
const encodedMarkup = '<html><iframe data-src="' + Buffer.from(encodedAddress).toString('base64') + '"></iframe>' +
  '<iframe data-src="' + encodeURIComponent(encodedAddress) + '"></iframe></html>';
const encodedRefs = responseStructure(encodedMarkup, { addressRef: encodedReferences.ref }).player_markup;
assert.deepEqual(encodedRefs.rows[0].address_refs, { 'data-src': ['r1'] });
assert.equal(encodedRefs.rows[0].count, 2);
assert.equal(encodedRefs.rows[0].distinct_values, 2);
assert.deepEqual(encodedReferences.calls, ['https://cdn.private.test/embed/PRIVATE?player=PRIVATE&mode=PRIVATE']);
assert.equal(encodedRefs.truncated, false);

const cappedReferences = referenceCollector();
const cappedMarkup = '<html>' + Array.from({ length: 17 }, (_, index) =>
  '<div data-src="/embed/PRIVATE_' + index + '"></div>').join('') + '</html>';
const capped = responseStructure(cappedMarkup, { baseUrl: queryOptions.baseUrl, addressRef: cappedReferences.ref }).player_markup;
assert.equal(capped.rows[0].count, 17);
assert.equal(capped.rows[0].distinct_values, 17);
assert.equal(capped.rows[0].address_refs['data-src'].length, 16);
assert.equal(cappedReferences.calls.length, 16);
assert.equal(capped.rows[0].address_refs_truncated, true);
assert.equal(capped.truncated, true);
assert.ok(!JSON.stringify(capped).includes('PRIVATE'));
const atCap = responseStructure(cappedMarkup.replace('<div data-src="/embed/PRIVATE_16"></div>', ''),
  { baseUrl: queryOptions.baseUrl, addressRef: () => 'r1' }).player_markup;
assert.equal(atCap.truncated, false);
assert.deepEqual(atCap.rows[0].address_refs, { 'data-src': ['r1'] });

const selectedReferences = referenceCollector();
const decorativeMarkup = '<html><a href="/PRIVATE.jpg"></a><a href="/PRIVATE.js"></a>' +
  '<a href="/PRIVATE.css"></a><a href="/PRIVATE.m3u8"></a><a href="/embed/PRIVATE"></a>' +
  '<a href="/PRIVATE.html"></a><a href="/PRIVATE"></a><a href="https://other.private.test/PRIVATE"></a>' +
  '<iframe src="/embed/PRIVATE_PLAYER"></iframe></html>';
const selected = responseStructure(decorativeMarkup, { baseUrl: queryOptions.baseUrl, addressRef: selectedReferences.ref }).player_markup;
assert.equal(selected.rows.length, 8);
assert.equal(selected.rows[0].tag, 'iframe');
assert.deepEqual(selected.rows[0].address_refs, { src: ['r1'] });
assert.equal(selectedReferences.calls.length, 8);
// The selected hosts must match the fixture's trusted origin exactly.
// Negating one blocked host is not an allowlist (CodeQL #2531).
assert.deepEqual(selectedReferences.calls.map(address => new URL(address).origin),
  Array(8).fill(new URL(queryOptions.baseUrl).origin));

for (const address of ['/embed/PRIVATE', '//private.test/embed/PRIVATE', 'https://']) {
  let called = false;
  const unresolved = responseStructure('<html><iframe src="' + address + '"></iframe></html>',
    { addressRef: () => { called = true; return 'r1'; } }).player_markup;
  assert.equal(called, false);
  assert.equal(unresolved.rows[0].address_refs_truncated, true);
  assert.equal(unresolved.truncated, true);
  assert.ok(!Object.hasOwn(unresolved.rows[0], 'address_refs'));
}

const nestedMarkup = '<html><button data-code="<iframe"></button>' +
  '<button data-code="&lt;iframe src=&quot;/PRIVATE&quot;&gt;"></button>' +
  '<button data-code="' + Buffer.from('<iframe src="/PRIVATE"></iframe>').toString('base64') + '"></button></html>';
let nestedCalls = 0;
const nested = responseStructure(nestedMarkup, { addressRef: () => { nestedCalls++; return 'r1'; } }).player_markup;
assert.deepEqual(nested.rows.map(row => row.value_kinds['data-code']), ['inline_markup', 'escaped_markup', 'encoded_markup']);
assert.ok(nested.rows.every(row => row.address_refs_truncated === true));
assert.equal(nestedCalls, 0);
assert.equal(nested.truncated, true);
assert.equal(responseStructure(nestedMarkup).player_markup.truncated, false);

let ignoredCalls = 0;
const ignored = responseStructure('<html><a href="#PRIVATE"></a><a href="ftp://private.test/PRIVATE"></a>' +
  '<a href="javascript:PRIVATE"></a><a href="about:blank"></a><a href="PRIVATE"></a></html>',
  { baseUrl: queryOptions.baseUrl, addressRef: () => { ignoredCalls++; return 'r1'; } }).player_markup;
assert.equal(ignoredCalls, 0);
assert.equal(ignored.truncated, false);
assert.ok(ignored.rows.every(row => !Object.hasOwn(row, 'address_refs') && row.address_refs_truncated === false));

const hostileMarkup = '<html><iframe src="https://private.test/embed/PRIVATE"></iframe></html>';
for (const invalid of [undefined, null, '', 1, {}, [], new String('r1'), 'r0', 'r01', 'r513', 'r999', 'r1000',
  'R1', 'r1\n', 'r1\r', 'r1\r\n', 'r1\u2028', 'r1 PRIVATE']) {
  const hostile = responseStructure(hostileMarkup, { addressRef: () => invalid }).player_markup;
  assert.equal(hostile.rows[0].address_refs_truncated, true);
  assert.equal(hostile.truncated, true);
  assert.ok(!Object.hasOwn(hostile.rows[0], 'address_refs'));
  assert.ok(!JSON.stringify(hostile).includes('PRIVATE'));
}
const thrown = responseStructure(hostileMarkup, { addressRef: () => { throw new Error('PRIVATE'); } }).player_markup;
assert.equal(thrown.rows[0].address_refs_truncated, true);
assert.ok(!JSON.stringify(thrown).includes('PRIVATE'));
const lastReference = responseStructure(hostileMarkup, { addressRef: () => 'r512' }).player_markup;
assert.deepEqual(lastReference.rows[0].address_refs, { src: ['r512'] });
assert.equal(lastReference.truncated, false);
const partial = responseStructure('<html><iframe src="/embed/PRIVATE" data-src="//cdn.private.test/embed/PRIVATE"></iframe></html>',
  { baseUrl: queryOptions.baseUrl, addressRef: address => {
    if (new URL(address).origin === 'https://cdn.private.test') throw new Error('PRIVATE');
    return 'r1';
  } }).player_markup;
assert.deepEqual(partial.rows[0].address_refs, { src: ['r1'] });
assert.equal(partial.rows[0].address_refs_truncated, true);
assert.equal(partial.truncated, true);
assert.deepEqual(responseStructure(queryMarkup, { baseUrl: queryOptions.baseUrl, addressRef: 'PRIVATE' }),
  responseStructure(queryMarkup, { baseUrl: queryOptions.baseUrl }));
console.log('Response diagnostics preserve parser structure without response scalar values');
const entityAddresses = [];
const entityRefs = responseStructure('<div data-src="/embed?a=1&#038;b=PRIVATE"></div>' +
  '<div data-src="/embed?a=1&#x26;b=PRIVATE"></div>', {
    baseUrl: 'https://provider.test/', addressRef: value => { entityAddresses.push(value); return 'r42'; },
  }).player_markup;
assert.deepEqual(entityAddresses, ['https://provider.test/embed?a=1&b=PRIVATE']);
assert.deepEqual(entityRefs.rows[0].address_refs, { 'data-src': ['r42'] });
assert.ok(!JSON.stringify(entityRefs).includes('PRIVATE'));

const bootstrap = responseStructure('<html><script>const config = {' +
  'epoch: 123, partB: "PRIVATE_CONFIG_VALUE", ready: true, disabled: false, missing: null,' +
  'data: { nested: "PRIVATE_NESTED_VALUE" }, items: [], negative: -42, hex: 0xff,' +
  'auth: { doNotExpose: "PRIVATE_AUTH" }, apiKey: "PRIVATE_KEY"};' +
  'import("./_app/immutable/entry/app.PRIVATE_HASH.js?token=PRIVATE_QUERY");</script></html>');
assert.deepEqual(bootstrap.inline_fields, [
  { name: 'epoch', type: 'number', key_syntax: 'bare' },
  { name: 'partB', type: 'string', key_syntax: 'bare' },
  { name: 'ready', type: 'boolean', key_syntax: 'bare' },
  { name: 'disabled', type: 'boolean', key_syntax: 'bare' },
  { name: 'missing', type: 'null', key_syntax: 'bare' },
  { name: 'data', type: 'object', key_syntax: 'bare' },
  { name: 'nested', type: 'string', key_syntax: 'bare' },
  { name: 'items', type: 'array', key_syntax: 'bare' },
  { name: 'negative', type: 'number', key_syntax: 'bare' },
  { name: 'hex', type: 'number', key_syntax: 'bare' },
]);
assert.deepEqual(bootstrap.script_resources, [{ kind: 'relative_path', role: 'app_entry', location: 'inline_import' }]);
assert.ok(!JSON.stringify(bootstrap).includes('PRIVATE'));
assert.ok(!JSON.stringify(bootstrap.inline_fields).includes('doNotExpose'));

const quotedConfig = responseStructure('<script>const a={epoch:1}; const b={"epoch":2,' +
  "'partB':'PRIVATE', \"\\u0063ount\": 3, 'not-an-identifier': 4};</script>");
assert.deepEqual(quotedConfig.inline_fields, [
  { name: 'epoch', type: 'number', key_syntax: 'bare' },
  { name: 'epoch', type: 'number', key_syntax: 'quoted' },
  { name: 'partB', type: 'string', key_syntax: 'quoted' },
  { name: 'count', type: 'number', key_syntax: 'quoted' },
]);
assert.ok(!JSON.stringify(quotedConfig).includes('PRIVATE'));

const scripts = responseStructure('<html>' +
  '<script src="https://cdn.private.test/_app/immutable/entry/app.PRIVATE.js?secret=PRIVATE"></script>' +
  '<script src="//cdn.private.test/_app/immutable/entry/start.PRIVATE.js"></script>' +
  '<script src="/_app/immutable/chunks/PRIVATE.js"></script>' +
  '<script src="./PRIVATE-other.js">const ignored={notExecuted:1}</script>' +
  '<script>import "../chunks/PRIVATE.js"; import { part } from "/_app/immutable/entry/app.PRIVATE.js";' +
  'import("//cdn.private.test/_app/immutable/entry/start.PRIVATE.js");</script></html>');
assert.deepEqual(scripts.script_resources, [
  { kind: 'absolute_url', role: 'app_entry', location: 'src_attribute' },
  { kind: 'root_relative_url', role: 'app_entry', location: 'inline_import' },
  { kind: 'protocol_relative_url', role: 'start_entry', location: 'src_attribute' },
  { kind: 'protocol_relative_url', role: 'start_entry', location: 'inline_import' },
  { kind: 'root_relative_url', role: 'chunk', location: 'src_attribute' },
  { kind: 'relative_path', role: 'chunk', location: 'inline_import' },
  { kind: 'relative_path', role: 'other_script', location: 'src_attribute' },
]);
assert.deepEqual(scripts.inline_fields, []);
assert.ok(!JSON.stringify(scripts).includes('PRIVATE'));
assert.doesNotMatch(JSON.stringify(scripts), /private\.test/i);

const inert = responseStructure('<html><!-- <script>const x={commented:1};import("./_app/immutable/entry/app.PRIVATE.js")</script> -->' +
  '<script>const text="{fake: 123} import(\"./_app/immutable/entry/app.PRIVATE.js\")";' +
  'const pattern=/{regexField:123}/; if(ready) /({controlRegexField:123})/.test(text);' +
  'if(ready) /import(".\\/_app\\/immutable\\/entry\\/app.PRIVATE.js")/.test(text);' +
  'loader.import("./_app/immutable/entry/app.PRIVATE.js");' +
  '/* const obj={blockComment:1}; import("./_app/immutable/entry/app.PRIVATE.js") */' +
  '// const obj={lineComment:1}; import("./_app/immutable/entry/app.PRIVATE.js")\n' +
  'if(ready){label:123;} function sample(){anotherLabel:123;}</script></html>');
assert.deepEqual(inert.inline_fields, []);
assert.deepEqual(inert.script_resources, []);
const falseSrc = responseStructure('<script data-text=\' src="./_app/immutable/entry/app.PRIVATE.js"\'></script>');
assert.deepEqual(falseSrc.script_resources, []);

const repeatedBootstrap = responseStructure('<script>const config={' +
  Array.from({ length: 40 }, (_, index) => 'field' + index + ': "PRIVATE"').join(',') + '};' +
  'const duplicate={field0:"PRIVATE"};' + 'import("./_app/immutable/entry/app.PRIVATE.js");'.repeat(30) + '</script>');
assert.equal(repeatedBootstrap.inline_fields.length, 12);
assert.equal(repeatedBootstrap.script_resources.length, 1);
assert.ok(repeatedBootstrap.inline_fields.every(row => Object.keys(row).sort().join(',') === 'key_syntax,name,type'));
assert.ok(!JSON.stringify(repeatedBootstrap).includes('PRIVATE'));
const resourceFlood = responseStructure('<html>' + [
  'https://cdn.private.test/', '//cdn.private.test/', '/', './',
].flatMap(prefix => ['_app/immutable/entry/app.PRIVATE.js', '_app/immutable/entry/start.PRIVATE.js',
  '_app/immutable/chunks/PRIVATE.js', 'PRIVATE-other.js'].flatMap(path => [
    '<script src="' + prefix + path + '"></script>', '<script>import("' + prefix + path + '")</script>',
  ])).join('') + '</html>');
assert.equal(resourceFlood.script_resources.length, 8);
assert.ok(resourceFlood.script_resources.some(row => row.role === 'app_entry'));
assert.ok(!JSON.stringify(resourceFlood).includes('PRIVATE'));
assert.deepEqual(responseStructure('<script type="application/json">{"epoch":1,"partB":"PRIVATE"}</script>').inline_fields,
  [{ name: 'epoch', type: 'number', key_syntax: 'quoted' }, { name: 'partB', type: 'string', key_syntax: 'quoted' }]);
const graphql = responseStructure({
  errors: [{
    message: 'Cannot query field PRIVATE with https://secret.test/PRIVATE?token=PRIVATE',
    extensions: { code: 'GRAPHQL_VALIDATION_FAILED', privateValue: 'PRIVATE' },
  }],
  data: null,
});
assert.deepEqual(graphql.graphql, {
  errorCount: 1, codes: ['GRAPHQL_VALIDATION_FAILED'],
  kinds: ['schema_mismatch'], dataState: 'null', nullRoots: [],
});
assert.ok(graphql.fields.some(row => row.path === 'errors[].extensions.code'));
assert.doesNotMatch(JSON.stringify(graphql), /PRIVATE|secret\\.test|token=/);
const graphqlNull = responseStructure({ data: { episode: null, title: 'PRIVATE' } });
assert.deepEqual(graphqlNull.graphql, {
  errorCount: 0, codes: [], kinds: [], dataState: 'object', nullRoots: ['episode'],
});
assert.doesNotMatch(JSON.stringify(graphqlNull), /PRIVATE/);
assert.equal(responseStructure({ errors: [{
  message: 'PRIVATE', extensions: { code: 'PRIVATE' },
}], data: null }).graphql.kinds[0], 'unknown');
assert.deepEqual(responseStructure({ foo: { bar: 1 } }).graphql, undefined);

console.log('Inline script diagnostics preserve bounded field syntax and resource roles without values');
