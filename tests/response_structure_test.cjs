'use strict';
const assert = require('node:assert/strict');
const { responseStructure } = require('../scripts/response_structure.cjs');
const payload = JSON.stringify({data: {sources: [{file: 'https://example.test/video?token=PRIVATE', label: 'PRIVATE'}]}, auth: {token: 'PRIVATE'}});
const result = responseStructure(payload);
assert.equal(result.kind, 'json');
assert.ok(result.fields.some(row => row.path === 'data.sources[].file' && row.type === 'string'));
assert.ok(!JSON.stringify(result).includes('PRIVATE'));
assert.ok(!JSON.stringify(result).includes('example.test'));
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
  '" data-token="PRIVATE"></button><iframe src="https://other.test/PRIVATE"></iframe></html>').player_markup;
assert.deepEqual(markup.rows.find(row => row.tag === 'iframe'), {
  tag: 'iframe', value_kinds: { src: 'absolute_url' }, count: 2, distinct_values: 2,
});
assert.deepEqual(markup.rows.find(row => row.tag === 'option').value_kinds, { value: 'relative_url' });
assert.deepEqual(markup.rows[0].value_kinds, { 'data-code': 'encoded_markup' });
assert.ok(!JSON.stringify(markup).includes('PRIVATE'));
assert.ok(!JSON.stringify(markup).includes('private.test'));
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
console.log('Response diagnostics preserve parser structure without response scalar values');
