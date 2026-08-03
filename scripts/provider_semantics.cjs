// SPDX-License-Identifier: GPL-3.0-only
'use strict';

function normalizedText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function normalizeSupportedType(value) {
  const text = normalizedText(value).trim();
  if (/^(movie|movies|film|films|cinema)$/.test(text)) return 'movie';
  if (/^(tv|series|serie|show|shows|television)$/.test(text)) return 'tv';
  if (/^(anime|animes|manga|mangas)$/.test(text)) return 'anime';
  return null;
}

function descriptionTypeSignals(textValue) {
  const text = normalizedText(textValue);
  const movie = /\b(?:movie|movies|film|films|cinema|cinematic)\b/.test(text);
  const tv = /\b(?:tv|television|serie|series|show|shows)\b/.test(text);
  const anime = /\b(?:anime|animes|manga|mangas)\b/.test(text);
  return { movie, tv, anime };
}

/**
 * Infer the catalogue coverage of one manifest entry.
 *
 * Anime catalogues expose both anime episodes and anime films. Therefore an
 * anime-only description maps to the anime and movie request types, but never
 * to general TV unless series/TV coverage is explicitly declared. Mixed
 * catalogues such as Movix preserve all three categories.
 */
function inferSupportedTypes(candidate) {
  const metadata = candidate?.metadata || {};
  const canonicalMetadata = candidate?.canonical_metadata || {};
  const declaredValues = [
    ...(Array.isArray(metadata.supportedTypes) ? metadata.supportedTypes : []),
    ...(Array.isArray(canonicalMetadata.supportedTypes) ? canonicalMetadata.supportedTypes : []),
  ];
  const declared = new Set(
    declaredValues.map(normalizeSupportedType).filter(Boolean),
  );
  const haystack = [
    candidate?.canonical_id,
    metadata.id,
    metadata.name,
    metadata.description,
    ...(Array.isArray(canonicalMetadata.descriptions) ? canonicalMetadata.descriptions : []),
  ].filter(Boolean).join(' ');
  const signals = descriptionTypeSignals(haystack);
  const inferred = new Set();
  if (signals.movie) inferred.add('movie');
  if (signals.tv) inferred.add('tv');
  if (signals.anime) inferred.add('anime');

  if (signals.anime && !signals.movie && !signals.tv) return ['movie', 'anime'];

  const combined = new Set([...declared, ...inferred]);
  if (!combined.size) {
    combined.add('movie');
    combined.add('tv');
  }
  return ['movie', 'tv', 'anime'].filter((value) => combined.has(value));
}

function roundRobin(groups) {
  const output = [];
  const maxLength = Math.max(0, ...groups.map((group) => group.length));
  for (let index = 0; index < maxLength; index += 1) {
    for (const group of groups) {
      if (index < group.length) output.push(group[index]);
    }
  }
  return output;
}

module.exports = {
  descriptionTypeSignals,
  inferSupportedTypes,
  normalizeSupportedType,
  normalizedText,
  roundRobin,
};
