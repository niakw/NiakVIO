const assert = require('node:assert/strict');
const { providerCallNames } = require('../scripts/provider_callsite.cjs');
const file = '/tmp/providers/demo.js';
const stack = 'Error\n at fetch (/private/worker.cjs:1:1)\n at async fetchSitePage (' + file + ':4:2)\n at async siteFallback (' + file + ':8:2)\n at resolve (' + file + ':9:2)\n at resolve (' + file + ':10:2)';
assert.deepEqual(providerCallNames(stack, file), ['fetchSitePage', 'siteFallback', 'resolve']);
assert.deepEqual(providerCallNames(stack, '/other.js'), []);
assert.deepEqual(providerCallNames('https://private.test/?token=secret', file), []);
function providerFixture() { return providerCallNames(new Error().stack, __filename); }
assert(providerFixture().includes('providerFixture'));
assert(!JSON.stringify(providerCallNames(stack, file)).includes('/tmp'));
console.log('Provider callsite names: actual stack, isolation and redaction passed');
