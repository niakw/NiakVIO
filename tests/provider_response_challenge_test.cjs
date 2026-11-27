#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const { challengeKind } = require('../scripts/provider_response_challenge.cjs');

assert.equal(challengeKind({
  contentType: 'text/html',
  body: '<html><head><title>CorsFlix</title></head><body><p>Our security check and captcha policy protects viewers using Cloudflare.</p></body></html>',
  server: 'cloudflare',
  cfRay: 'abc',
}), '');

assert.equal(challengeKind({
  contentType: 'text/html',
  body: '<html><head><title>Security Check</title></head><body>Please continue</body></html>',
}), 'generic');

assert.equal(challengeKind({
  contentType: 'text/html',
  body: '<html><body><form id="challenge-form" action="/cdn-cgi/challenge-platform/x"></form></body></html>',
}), 'cloudflare');

assert.equal(challengeKind({
  contentType: 'application/javascript',
  body: 'window.turnstile.render("#gate", {sitekey:"redacted"});',
}), 'cloudflare');

assert.equal(challengeKind({
  contentType: 'text/html',
  body: '<div class="g-recaptcha"></div>',
}), 'generic');

assert.equal(challengeKind({
  contentType: 'text/html',
  body: '<html><title>Normal page</title><p>checking your browser compatibility is optional</p></html>',
  cfMitigated: 'challenge',
}), 'cloudflare');

assert.equal(challengeKind({
  contentType: 'application/json',
  body: '{"message":"security check"}',
}), '');

console.log('Provider response challenge classifier: prose ignored, structural/title/header gates preserved');
