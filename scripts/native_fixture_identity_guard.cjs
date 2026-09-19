'use strict';

// Native-reader identity evidence must not accept a same-title remake/older release
// merely because the title and episode number happen to match. This module is kept
// provider-agnostic and only uses sanitized stream labels already emitted by the Labs.

function normalize(value) {
  try {
    return String(value ?? '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  } catch {
    return String(value ?? '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  }
}

function explicitYears(value) {
  const years = new Set();
  const text = String(value ?? '');
  for (const match of text.matchAll(/(?:^|[^0-9])((?:19|20)\d{2})(?=$|[^0-9])/g)) {
    const year = Number(match[1]);
    // Common video dimensions are outside 1900-2099 anyway; retain only plausible
    // release years so codec/resolution labels cannot become identity evidence.
    if (year >= 1900 && year <= 2099) years.add(year);
  }
  return [...years].sort((a, b) => a - b);
}

function releaseIdentityGuard(stream = {}, fixture = {}) {
  const expectedYear = Number(fixture.year || 0);
  const ambiguousYears = [...new Set((fixture.ambiguousReleaseYears || []).map(Number).filter(Boolean))];
  const requiresDisambiguation = fixture.requireExplicitReleaseDisambiguation === true || ambiguousYears.length > 1;
  if (!expectedYear || !requiresDisambiguation) return null;

  const labels = [stream.title, stream.name, stream.filename, stream.description, stream.mediaHint]
    .map((value) => String(value || '').trim())
    .filter(Boolean);
  const combined = labels.join(' ');
  const years = explicitYears(combined);

  if (years.length > 0) {
    if (years.includes(expectedYear)) return null;
    return {
      status: 'contradiction',
      reason: 'wrong_release_year',
      expectedYear,
      observedYears: years,
      preventDurationPromotion: true,
    };
  }

  const normalized = normalize(combined);
  const releaseAliases = (fixture.releaseDisambiguatingAliases || []).map(normalize).filter(Boolean);
  if (normalized && releaseAliases.some((alias) => normalized.includes(alias))) return null;

  // With a known same-title collision, absence of a release discriminator is not
  // proof of wrong content, but it is also not proof of the requested work. Keep it
  // unknown and explicitly prevent duration-only promotion (critical for remakes
  // such as Nube 1996/2025 that share ~23 minute episode durations).
  return {
    status: 'unknown',
    reason: 'ambiguous_same_title_release',
    expectedYear,
    ambiguousReleaseYears: ambiguousYears,
    preventDurationPromotion: true,
  };
}

module.exports = { explicitYears, releaseIdentityGuard };
