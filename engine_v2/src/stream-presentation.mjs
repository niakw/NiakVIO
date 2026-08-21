const UNKNOWN = /^(?:unknown|n\/a|na|none|null|undefined|-)$/i;

export function presentStreamCandidates(streams, metadata = {}, provider = {}) {
  return (Array.isArray(streams) ? streams : []).map((stream) => presentStreamCandidate(stream, metadata, provider));
}

export function presentStreamCandidate(stream = {}, metadata = {}, provider = {}) {
  const facts = collectFacts(stream, metadata);
  const providerName = clean(stream.name) ?? clean(provider.name) ?? clean(provider.id) ?? clean(stream.provider) ?? "Source";
  const originalDescription = useful(stream.description);
  const badges = buildBadges(facts);
  const descriptionParts = [];

  if (badges.length) descriptionParts.push(badges.join("  •  "));
  if (originalDescription && !descriptionParts.some((part) => part.includes(originalDescription))) {
    descriptionParts.push(originalDescription);
  }

  // TMDB (or another shared factual metadata resolver) fills sparse/Unknown provider
  // descriptions. It supplements facts only; it never invents stream provenance.
  const tmdbTitle = useful(metadata.title ?? metadata.name ?? metadata.originalTitle ?? metadata.original_name);
  const tmdbYear = positiveInt(metadata.year ?? yearFromDate(metadata.releaseDate ?? metadata.release_date ?? metadata.firstAirDate ?? metadata.first_air_date));
  if (!originalDescription && (tmdbTitle || tmdbYear)) {
    descriptionParts.push([tmdbTitle, tmdbYear].filter(Boolean).join(" • "));
  }

  return {
    ...stream,
    title: providerName,
    description: descriptionParts.join("\n") || null,
    quality: facts.quality,
    language: facts.language,
    codec: facts.codec,
    audio: facts.audio,
    duration: facts.duration,
    sourceType: facts.sourceType,
    ageRating: facts.ageRating,
    displayBadges: badges,
  };
}

export function collectFacts(stream = {}, metadata = {}) {
  return {
    quality: normalizeQuality(stream.quality ?? stream.resolution),
    language: useful(stream.language ?? stream.lang ?? stream.audioLanguage),
    codec: normalizeCodec(stream.codec ?? stream.videoCodec ?? stream.video_codec),
    audio: normalizeAudio(stream.audio ?? stream.audioCodec ?? stream.audio_codec),
    duration: normalizeDuration(
      stream.duration ?? stream.durationMinutes ?? stream.runtime ??
      metadata.duration ?? metadata.durationMinutes ?? metadata.runtime,
    ),
    sourceType: normalizeSourceType(stream.sourceType ?? stream.source_type ?? stream.releaseType ?? stream.release_type),
    ageRating: normalizeAgeRating(
      stream.ageRating ?? stream.age_rating ?? stream.certification ??
      metadata.ageRating ?? metadata.age_rating ?? metadata.certification ?? metadata.contentRating ?? metadata.content_rating,
    ),
  };
}

export function buildBadges(facts = {}) {
  const out = [];
  const quality = normalizeQuality(facts.quality);
  const sourceType = normalizeSourceType(facts.sourceType);
  const language = useful(facts.language);
  const codec = normalizeCodec(facts.codec);
  const audio = normalizeAudio(facts.audio);
  const duration = normalizeDuration(facts.duration);
  const ageRating = normalizeAgeRating(facts.ageRating);

  if (quality) out.push(quality === "2160p" ? "【4K】" : `【${quality.toUpperCase()}】`);
  if (sourceType) out.push(`【${sourceType}】`);
  if (language) out.push(`🌐 ${language.toUpperCase()}`);
  if (codec) out.push(`🎞 ${codec}`);
  if (audio) out.push(`🔊 ${audio}`);
  if (duration) out.push(`⏱ ${formatDuration(duration)}`);
  if (ageRating) out.push(`🔞 ${ageRating}`);
  return out;
}

export function normalizeQuality(value) {
  const text = useful(value);
  if (!text) return null;
  if (/^(?:4k|uhd|2160p?)$/i.test(text)) return "2160p";
  const match = text.match(/(?:^|\b)(2160|1440|1080|720|576|480)p?(?:\b|$)/i);
  return match ? `${match[1]}p` : text;
}

export function normalizeSourceType(value) {
  const text = useful(value);
  if (!text) return null;
  const compact = text.toUpperCase().replace(/[._\s]+/g, "-");
  if (/BLU-?RAY|BDRIP|BRRIP/.test(compact)) return "BLU-RAY";
  if (/WEB-?DL/.test(compact)) return "WEB-DL";
  if (/WEB-?RIP/.test(compact)) return "WEBRIP";
  if (/HDTV/.test(compact)) return "HDTV";
  if (/DVDRIP|DVD/.test(compact)) return "DVD";
  if (/(?:^|-)CAM(?:-|$)|TELESYNC/.test(compact)) return "CAM";
  // Unknown strings are not provenance. In particular, a quality such as 1080p
  // must never be converted into a source badge or used to imply Blu-ray/Web-DL.
  return null;
}

export function normalizeCodec(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  if (/H\.?265|X265|HEVC/.test(upper)) return "HEVC";
  if (/H\.?264|X264|AVC/.test(upper)) return "H.264";
  if (/AV1/.test(upper)) return "AV1";
  if (/VP9/.test(upper)) return "VP9";
  return text;
}

export function normalizeAudio(value) {
  const text = useful(value);
  if (!text) return null;
  return text
    .replace(/\bDDP\b/ig, "E-AC3")
    .replace(/\bDD\b/ig, "AC3")
    .replace(/\s+/g, " ")
    .trim();
}

export function normalizeDuration(value) {
  if (value == null || value === "") return null;
  if (typeof value === "number" && Number.isFinite(value) && value > 0) {
    return value > 600 ? Math.round(value / 60) : Math.round(value);
  }
  const text = useful(value);
  if (!text) return null;
  const hm = text.match(/(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:in(?:utes?)?)?)?/i);
  if (hm && (hm[1] || hm[2])) {
    const minutes = Number(hm[1] || 0) * 60 + Number(hm[2] || 0);
    return minutes > 0 ? minutes : null;
  }
  const number = Number(text);
  if (Number.isFinite(number) && number > 0) return number > 600 ? Math.round(number / 60) : Math.round(number);
  return null;
}

export function normalizeAgeRating(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  const france = upper.match(/(?:-|INTERDIT\s+MOINS\s+DE\s+)(10|12|16|18)\b/);
  if (france) return `-${france[1]}`;
  const plus = upper.match(/(?:^|\b)(7|10|12|13|14|15|16|17|18)\+(?:$|\s)/);
  if (plus) return `${plus[1]}+`;
  if (/^(?:U|G|PG|PG-13|R|NC-17|TV-Y|TV-Y7|TV-G|TV-PG|TV-14|TV-MA)$/i.test(text)) return upper;
  return text;
}

function formatDuration(minutes) {
  const total = Math.max(1, Math.round(Number(minutes)));
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (!hours) return `${rest} min`;
  return rest ? `${hours}h${String(rest).padStart(2, "0")}` : `${hours}h`;
}

function yearFromDate(value) {
  const text = useful(value);
  const match = text?.match(/(?:19|20)\d{2}/);
  return match ? Number(match[0]) : null;
}

function positiveInt(value) {
  const number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : null;
}

function useful(value) {
  const text = clean(value);
  return text && !UNKNOWN.test(text) ? text : null;
}

function clean(value) {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}
