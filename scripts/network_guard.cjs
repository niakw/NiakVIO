'use strict';
// SPDX-License-Identifier: GPL-3.0-only
const dns = require('node:dns').promises;
const net = require('node:net');

const BLOCKED_HOSTS = new Set(['localhost','localhost.localdomain','metadata.google.internal']);
const CLOUD_METADATA = new Set(['169.254.169.254','100.100.100.200']);

function normalizeHost(host) { return String(host || '').trim().replace(/^\[|\]$/g, '').toLowerCase(); }
function isPrivateIp(address) {
  const ip = normalizeHost(address);
  if (!net.isIP(ip)) return false;
  if (net.isIPv4(ip)) {
    const [a,b] = ip.split('.').map(Number);
    return a === 10 || a === 127 || a === 0 || (a === 169 && b === 254)
      || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168)
      || (a === 100 && b >= 64 && b <= 127)
      || (a === 192 && b === 0)
      || (a === 198 && (b === 18 || b === 19))
      || (a === 198 && b === 51 && Number(ip.split('.')[2]) === 100)
      || (a === 203 && b === 0 && Number(ip.split('.')[2]) === 113)
      || a >= 224;
  }
  const mapped = ip.match(/^::ffff:(\d+\.\d+\.\d+\.\d+)$/i);
  if (mapped) return isPrivateIp(mapped[1]);
  return ip === '::1' || ip === '::' || ip.startsWith('fc') || ip.startsWith('fd')
    || ip.startsWith('fe8') || ip.startsWith('fe9') || ip.startsWith('fea') || ip.startsWith('feb')
    || ip.startsWith('ff') || ip.startsWith('2001:db8:');
}
async function validateUrl(input) {
  const url = input instanceof URL ? input : new URL(typeof input === 'string' ? input : input?.url);
  if (!['http:','https:'].includes(url.protocol)) throw new Error(`blocked protocol: ${url.protocol}`);
  if (url.username || url.password) throw new Error('credentialed URLs are blocked');
  const host = normalizeHost(url.hostname);
  if (!host || BLOCKED_HOSTS.has(host) || host.endsWith('.localhost') || CLOUD_METADATA.has(host) || isPrivateIp(host)) {
    throw new Error(`blocked network destination: ${host || 'unknown'}`);
  }
  const records = await dns.lookup(host, { all: true, verbatim: true });
  if (!records.length) throw new Error(`DNS returned no address for ${host}`);
  const blocked = records.find((record) => isPrivateIp(record.address) || CLOUD_METADATA.has(record.address));
  if (blocked) throw new Error(`DNS rebinding/private address blocked for ${host}`);
  return { url, host, addresses: records.map((record) => record.address) };
}
async function guardedFetch(nativeFetch, input, init = {}, options = {}) {
  const maxRedirects = Number(options.maxRedirects ?? 5);
  let current = input instanceof Request ? new URL(input.url) : new URL(typeof input === 'string' ? input : input.url);
  let method = String(init.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
  for (let redirectCount = 0; redirectCount <= maxRedirects; redirectCount += 1) {
    await validateUrl(current);
    const response = await nativeFetch(current, { ...init, method, redirect: 'manual' });
    if (![301,302,303,307,308].includes(response.status)) return response;
    if (redirectCount === maxRedirects) throw new Error(`redirect limit exceeded (${maxRedirects})`);
    const location = response.headers.get('location');
    if (!location) return response;
    current = new URL(location, current);
    if (response.status === 303 || ((response.status === 301 || response.status === 302) && method === 'POST')) method = 'GET';
  }
  throw new Error('unreachable redirect state');
}
module.exports = { isPrivateIp, validateUrl, guardedFetch };
