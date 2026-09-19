'use strict';
const assert = require('node:assert/strict');
const { isPrivateIp, validateUrl } = require('../scripts/network_guard.cjs');
assert.equal(isPrivateIp('127.0.0.1'), true);
assert.equal(isPrivateIp('192.168.1.1'), true);
assert.equal(isPrivateIp('10.0.0.1'), true);
assert.equal(isPrivateIp('8.8.8.8'), false);
Promise.all([
  assert.rejects(() => validateUrl('file:///etc/passwd'), /blocked protocol/),
  assert.rejects(() => validateUrl('http://127.0.0.1/'), /blocked network destination/),
  assert.rejects(() => validateUrl('http://169.254.169.254/latest/meta-data'), /blocked network destination/),
]).then(() => console.log('network guard tests passed'));
