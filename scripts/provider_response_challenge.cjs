'use strict';

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

  const titleMatch = /<title\b[^>]*>([\s\S]{0,160}?)<\/title\s*>/i.exec(source);
  const title = String(titleMatch?.[1] || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
  const challengeTitle = /^(?:just a moment(?:\.{3})?|checking your browser(?: before accessing .+)?|verify you are human|attention required!?|security check)$/i.test(title);

  const captchaMarkup = (
    /\b(?:class|id)\s*=\s*["'][^"']*\b(?:g-recaptcha|h-captcha)\b/i.test(source)
    || /(?:google\.com\/recaptcha|gstatic\.com\/recaptcha|hcaptcha\.com\/1\/api\.js)/i.test(source)
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
