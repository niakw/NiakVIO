'use strict';
const assert = require('node:assert/strict');
const { createAddressReferences, safeAddressReference, safeAddressScope, safeAddressFields } = require('../scripts/address_reference.cjs');

const PRIVATE = 'PRIVATE_URL_TOKEN_COOKIE';
const references = createAddressReferences();
assert.match(references.scope, /^s[0-9a-f]{16}$/);
assert.equal(references.ref('https://reader.test:443/embed?id=' + PRIVATE + '#one'), 'r1');
assert.equal(references.ref('https://reader.test/embed?id=' + PRIVATE + '#two'), 'r1');
assert.equal(references.ref('https://reader.test/embed?id=OTHER'), 'r2');
assert.equal(references.ref('/embed?id=OTHER#three', 'https://reader.test/wrapper'), 'r2');
assert.equal(references.ref('../embed?id=OTHER', 'https://reader.test/pages/wrapper'), 'r2');
assert.equal(references.ref('http://reader.test:80/embed?id=OTHER'), 'r3');
assert.equal(references.ref('http://reader.test/embed?id=OTHER#four'), 'r3');
assert.equal(references.ref('https://reader.test/embed?a=1&b=2'), 'r4');
assert.equal(references.ref('https://reader.test/embed?b=2&a=1'), 'r5');
assert.equal(references.ref('https://reader.test/embed?a=1&amp;b=2'), 'r6', 'factory must not decode HTML entities');
assert.equal(references.ref('https://reader.test/embed?a=1&a=2'), 'r7');
assert.equal(references.ref('https://reader.test/embed?a=1&a=3'), 'r8');
assert.equal(references.truncated, false);

const invalid = createAddressReferences();
for (const value of ['', null, 42, {}, 'not a URL', '/relative-without-base',
  'file:///tmp/private', 'data:text/html,' + PRIVATE, 'javascript:alert(1)',
  'https://user:' + PRIVATE + '@reader.test/embed', 'https://' + PRIVATE + '@reader.test/embed']) {
  assert.equal(invalid.ref(value), '', String(value));
}
assert.equal(invalid.ref('/relative', 'https://user:secret@reader.test/'), '');
assert.equal(invalid.truncated, false, 'malformed and disallowed URLs do not consume capacity');
assert.equal(invalid.ref('https://reader.test/first'), 'r1');

const overflow = createAddressReferences({ limit: 2 });
assert.equal(overflow.ref('https://reader.test/one'), 'r1');
assert.equal(overflow.ref('https://reader.test/two'), 'r2');
assert.equal(overflow.truncated, false);
assert.equal(overflow.ref('https://reader.test/three'), '');
assert.equal(overflow.truncated, true);
assert.equal(overflow.ref('https://reader.test/one#still-known'), 'r1', 'known labels survive capacity exhaustion');
assert.equal(overflow.ref('https://reader.test/four'), '');
const zero = createAddressReferences({ limit: 0 });
assert.equal(zero.ref('https://reader.test/'), '');
assert.equal(zero.truncated, true);

const maximum = createAddressReferences({ limit: 999999 });
for (let i = 1; i <= 512; i++) assert.equal(maximum.ref('https://reader.test/?id=' + i), 'r' + i);
assert.equal(maximum.truncated, false);
assert.equal(maximum.ref('https://reader.test/?id=513'), '');
assert.equal(maximum.truncated, true);
assert.equal(maximum.ref('https://reader.test/?id=512'), 'r512');

const lengthy = createAddressReferences();
const prefix = 'https://reader.test/';
assert.equal(lengthy.ref(prefix + 'a'.repeat(8192 - prefix.length)), 'r1');
assert.equal(lengthy.ref(prefix + 'a'.repeat(8193 - prefix.length)), '');
assert.equal(lengthy.truncated, true);
const expanded = createAddressReferences();
assert.equal(expanded.ref(prefix + 'é'.repeat(1500)), '', 'canonical URL expansion is also bounded');
assert.equal(expanded.truncated, true);
assert.equal(expanded.ref(prefix + 'short'), 'r1');
const longBase = createAddressReferences();
assert.equal(longBase.ref('relative', prefix + 'a'.repeat(8192)), '');
assert.equal(longBase.truncated, true);

const independent = createAddressReferences({ scope: references.scope });
assert.notEqual(independent.scope, references.scope, 'public options cannot choose a scope');
assert.equal(independent.ref('https://different.test/' + PRIVATE), 'r1');
assert.equal(references.ref('https://reader.test/embed?id=' + PRIVATE), 'r1');
assert.throws(() => { independent.scope = references.scope; }, TypeError);
assert.deepEqual(Object.keys(independent).sort(), ['ref', 'scope', 'truncated']);
assert.ok(!JSON.stringify(references).includes(PRIVATE));
assert.ok(!JSON.stringify(references).includes('reader.test'));
assert.equal(references.references, undefined);
assert.equal(references.map, undefined);

for (const value of ['r1', 'r9', 'r10', 'r100', 'r512']) assert.equal(safeAddressReference(value), value);
for (const value of ['', 'r0', 'r01', 'r513', 'r9999', 'R1', ' r1', 'r1\n', 1, null, {}, PRIVATE]) {
  assert.equal(safeAddressReference(value), '');
}
assert.equal(safeAddressScope(references.scope), references.scope);
for (const value of ['', 's1234', 's' + 'A'.repeat(16), 's' + '0'.repeat(17), 's' + '0'.repeat(16) + '\n',
  123, null, {}, PRIVATE]) assert.equal(safeAddressScope(value), '');

const projected = safeAddressFields({ address_scope: references.scope, request_ref: 'r1', response_ref: 'r512',
  referer_ref: 'r2', address_refs_truncated: true, address_trace_truncated: false,
  url: prefix + PRIVATE, headers: { Cookie: PRIVATE }, raw_map: PRIVATE });
assert.deepEqual(projected, { address_scope: references.scope, address_refs_truncated: true,
  address_trace_truncated: false, request_ref: 'r1', response_ref: 'r512', referer_ref: 'r2' });
assert.deepEqual(safeAddressFields(projected), projected);
assert.ok(!JSON.stringify(projected).includes(PRIVATE));
assert.deepEqual(safeAddressFields({ address_scope: references.scope, request_ref: 'r513', response_ref: 2,
  referer_ref: '', address_refs_truncated: 'true' }), { address_scope: references.scope,
    address_refs_truncated: true, address_trace_truncated: true });
for (const value of [null, [], {}, { request_ref: 'r1' }, { address_scope: PRIVATE, request_ref: 'r1' }]) {
  assert.deepEqual(safeAddressFields(value), {});
}
console.log('Address references: scoped opaque labels, exact query preservation, limits and public projection passed');
