'use strict';

const CAPTCHA_RESOURCE_HOSTS = new Set([
  'google.com',
  'www.google.com',
  'gstatic.com',
  'www.gstatic.com',
  'www.recaptcha.net',
  'hcaptcha.com',
  'js.hcaptcha.com',
]);

function extractTitleText(source) {
  const text = String(source || '');
  const low = text.toLowerCase();
  const start = low.indexOf('<title');
  if (start < 0) return '';
  const boundary = start + 6;
  if (boundary < text.length && !/[\s/>]/.test(text[boundary])) return '';
  const openEnd = text.indexOf('>', boundary);
  if (openEnd < 0) return '';
  const close = low.indexOf('</title', openEnd + 1);
  if (close < 0) return '';
  const closeBoundary = close + 7;
  if (closeBoundary < text.length && !/[\s/>]/.test(text[closeBoundary])) return '';
  return text.slice(openEnd + 1, close)
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function hasCaptchaResource(source) {
  const text = String(source || '');
  const attr = /\b(?:src|href)\s*=\s*(["'])([^"']{1,2048})\1/gi;
  let match;
  while ((match = attr.exec(text)) !== null) {
    let parsed;
    try {
      parsed = new URL(match[2], 'https://invalid.local/');
    } catch {
      continue;
    }
    if (!['http:', 'https:'].includes(parsed.protocol)) continue;
    const host = parsed.hostname.toLowerCase();
    const path = parsed.pathname.toLowerCase();
    if (!CAPTCHA_RESOURCE_HOSTS.has(host)) continue;
    if (
      ((host === 'google.com' || host === 'www.google.com' || host === 'gstatic.com'
        || host === 'www.gstatic.com' || host === 'www.recaptcha.net')
        && path.startsWith('/recaptcha'))
      || ((host === 'hcaptcha.com' || host === 'js.hcaptcha.com') && path === '/1/api.js')
    ) {
      return true;
    }
  }
  return false;
}

function challengeKind({ body = '', contentType = '', server = '', cfRay = '', cfMitigated = '' } = {}) {
  const type = String(contentType || '').toLowerCase();
  const html = /text\/html/.test(type);
  const script = /(?:application|text)\/(?:javascript|x-javascript|ecmascript)/.test(type);
  if (!html && !script) return '';

  const source = String(body || '').slice(0, 65536);
  const low = source.toLowerCase();
  const mitigated = String(cfMitigated || '').trim().toLowerCase();
  if (mitigated === 'challenge') return 'cloudflare';

  const turnstile = (
    /cf-turnstile-response|challenges\.cloudflare\.com\/turnstile/i.test(source)
    || /\b(?:class|id)\s*=\s*["'][^"']*\bcf-turnstile\b/i.test(source)
    || /\b(?:window\.)?turnstile\s*\.\s*(?:render|execute)\s*\(/i.test(source)
  );
  const cloudflareMarkup = (
    /\bcf-chl-[a-z0-9_-]+\b|\bchallenge-platform\b|\bcf-browser-verification\b/i.test(source)
    || /\b(?:id|name)\s*=\s*["']challenge-form["']/i.test(source)
    || /\/cdn-cgi\/challenge-platform\//i.test(source)
  );
  if (turnstile || cloudflareMarkup) return 'cloudflare';

  if (!html) return '';

  const title = extractTitleText(source);
  const challengeTitle = /^(?:just a moment(?:\.{3})?|checking your browser(?: before accessing .+)?|verify you are human|attention required!?|security check)$/i.test(title);

  const captchaMarkup = (
    /\b(?:class|id)\s*=\s*["'][^"']*\b(?:g-recaptcha|h-captcha)\b/i.test(source)
    || hasCaptchaResource(source)
  );
  if (challengeTitle || captchaMarkup) {
    return (
      String(server || '').toLowerCase().includes('cloudflare')
      || Boolean(String(cfRay || '').trim())
    ) ? 'cloudflare' : 'generic';
  }

  // Ordinary content is allowed to mention security checks, CAPTCHA or
  // Cloudflare. Prose alone is not evidence of an interactive gate.
  void low;
  return '';
}

module.exports = { challengeKind };
