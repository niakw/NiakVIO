const UNKNOWN = /^(?:unknown|inconnue?|n\/a|na|none|null|undefined|-+)$/i;

export function presentStreamCandidates(streams, metadata = {}, provider = {}) {
  return (Array.isArray(streams) ? streams : []).map((stream) =>
    presentStreamCandidate(stream, metadata, provider),
  );
}

export function presentStreamCandidate(stream = {}, metadata = {}, provider = {}) {
  const facts = collectFacts(stream, metadata);
  const providerName = useful(provider.name) ?? readableProviderId(provider.id) ?? useful(stream.provider) ?? "Source";
  const lines = [];
  const media = mediaLine(metadata);
  if (media) lines.push(media);
  lines.push(...buildTechnicalLines(facts, { includeQuality: true }));
  if (!lines.length) {
    const overview = useful(metadata.overview);
    if (overview) lines.push(`ℹ️ ${brief(overview)}`);
  }
  if (!lines.length) lines.push(`🎬 ${providerName}`);

  return {
    ...stream,
    title: providerName,
    description: lines.join("\n"),
    quality: facts.quality,
    language: facts.language,
    codec: facts.codec,
    audio: facts.audio,
    duration: facts.duration,
    sourceType: facts.sourceType,
    releaseType: facts.releaseType,
    format: facts.format,
    ageRating: facts.ageRating,
    fileSize: facts.fileSize,
    presentationFacts: facts,
    displayBadges: buildBadges(facts),
  };
}

export function collectFacts(stream = {}, metadata = {}) {
  const blob = collectText(stream);
  return {
    quality: normalizeQuality(firstUseful(stream.quality, stream.resolution, stream.qualityLabel, blob)),
    language: normalizeLanguage(firstUseful(stream.language, stream.lang, stream.audioLanguage, blob)),
    codec: normalizeCodec(firstUseful(stream.codec, stream.videoCodec, stream.video_codec, blob)),
    audio: normalizeAudio(firstUseful(stream.audio, stream.audioCodec, stream.audio_codec, blob)),
    duration: normalizeDuration(
      firstUseful(
        stream.duration,
        stream.durationMinutes,
        stream.duration_minutes,
        stream.runtime,
        metadata.duration,
        metadata.durationMinutes,
        metadata.runtime,
        blob,
      ),
    ),
    sourceType: normalizeSourceType(firstUseful(stream.sourceType, stream.source_type, blob)),
    releaseType: /\bREMUX\b/i.test(firstUseful(stream.releaseType, stream.release_type, blob) ?? "") ? "REMUX" : null,
    format: normalizeFormat(firstUseful(stream.format, stream.container), stream.url),
    ageRating: normalizeAgeRating(
      firstUseful(
        stream.ageRating,
        stream.age_rating,
        stream.certification,
        metadata.ageRating,
        metadata.age_rating,
        metadata.certification,
        metadata.contentRating,
        metadata.content_rating,
      ),
    ),
    fileSize: extractFileSize(firstUseful(stream.fileSize, stream.filesize, stream.size)),
  };
}

export function buildBadges(facts = {}) {
  const out = [];
  const quality = normalizeQuality(facts.quality);
  const sourceType = normalizeSourceType(facts.sourceType);
  const language = normalizeLanguage(facts.language);
  const codec = normalizeCodec(facts.codec);
  const audio = normalizeAudio(facts.audio);
  const duration = normalizeDuration(facts.duration);
  const ageRating = normalizeAgeRating(facts.ageRating);

  if (quality) out.push(quality === "2160p" ? "4K" : quality);
  if (sourceType) out.push(sourceType);
  if (facts.releaseType === "REMUX") out.push("REMUX");
  if (codec) out.push(codec);
  if (audio) out.push(audio);
  if (language) out.push(language);
  if (duration) out.push(formatDuration(duration));
  if (ageRating) out.push(ageRating);
  return unique(out);
}

export function buildTechnicalLines(facts = {}, { includeQuality = true } = {}) {
  const lines = [];
  const video = [];
  const audio = [];
  const languages = [];
  const misc = [];

  if (includeQuality && facts.quality) video.push(facts.quality);
  if (facts.sourceType) video.push(facts.sourceType);
  if (facts.releaseType) video.push(facts.releaseType);
  if (facts.codec) video.push(facts.codec);
  if (facts.format) video.push(facts.format);
  if (video.length) lines.push(`🎞️ ${unique(video).join(" • ")}`);

  if (facts.audio) audio.push(facts.audio);
  if (audio.length) lines.push(`🔊 ${unique(audio).join(" • ")}`);

  if (facts.language) languages.push(facts.language);
  if (languages.length) lines.push(`🌐 ${unique(languages).join(" • ")}`);

  if (facts.duration) misc.push(`⏱ ${formatDuration(facts.duration)}`);
  if (facts.fileSize) misc.push(`💾 ${facts.fileSize}`);
  if (facts.ageRating) misc.push(`🔞 ${facts.ageRating}`);
  if (misc.length) lines.push(misc.join(" • "));

  return lines;
}

export function normalizeQuality(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  if (/(?:\b4K\b|\bUHD\b|\b2160P?\b)/.test(upper)) return "2160p";
  const match = upper.match(/\b(1440|1080|720|576|540|480|360)P?\b/);
  return match ? `${match[1]}p` : null;
}

export function normalizeLanguage(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  if (/\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b/.test(upper)) return "Multi";
  if (/\bDUAL(?:[- ]?AUDIO)?\b/.test(upper)) return "Multi";
  if (/\bVOSTFR\b/.test(upper)) return "VOSTFR";
  if (/\bVFQ\b/.test(upper)) return "VFQ";
  if (/\bVFF\b/.test(upper)) return "VFF";
  if (/\bVF\b/.test(upper)) return "VF";
  if (/\bVO\b/.test(upper)) return "VO";
  return null;
}

export function normalizeSourceType(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  if (/\b(?:ULTRA[ ._-]?HD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BD)\b/.test(upper)) return "ULTRA HD BLU-RAY";
  if (/\b(?:BLU[- ]?RAY|BLURAY|BDRIP|BRRIP|BDREMUX)\b/.test(upper)) return "BLU-RAY";
  if (/\bWEB[- .]?DL\b/.test(upper)) return "WEB-DL";
  if (/\bWEB[- .]?RIP\b/.test(upper)) return "WEBRIP";
  if (/\bHDTV\b/.test(upper)) return "HDTV";
  if (/\bDVD[- .]?RIP\b/.test(upper)) return "DVD RIP";
  if (/\bCAM\b|\bTELESYNC\b/.test(upper)) return "CAM";
  return null;
}

export function normalizeCodec(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  if (/\b(?:H[ ._-]?265|X265|HEVC)\b/.test(upper)) return "HEVC";
  if (/\bAV1\b/.test(upper)) return "AV1";
  if (/\bVP9\b/.test(upper)) return "VP9";
  if (/\b(?:H[ ._-]?264|X264|AVC)\b/.test(upper)) return "AVC";
  return null;
}

export function normalizeAudio(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  const channelMatch = upper.match(/\b(7\.1|5\.1|2\.1|2\.0|1\.0)\b/);
  const channels = channelMatch?.[1] ?? "";
  let codec = null;
  if (/\b(?:ATMOS|DOLBY ATMOS)\b/.test(upper)) codec = "Dolby Atmos";
  else if (/\bTRUE[ ._-]?HD\b/.test(upper)) codec = "TrueHD";
  else if (/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(upper)) codec = "E-AC3";
  else if (/\bAC-?3\b/.test(upper)) codec = "AC3";
  else if (/\bDTS[: ._-]?X\b/.test(upper)) codec = "DTS:X";
  else if (/\bDTS[- ]?HD\b/.test(upper)) codec = "DTS-HD";
  else if (/\bDTS\b/.test(upper)) codec = "DTS";
  else if (/\bAAC\b/.test(upper)) codec = "AAC";
  else if (/\bFLAC\b/.test(upper)) codec = "FLAC";
  else if (/\bOPUS\b/.test(upper)) codec = "Opus";
  if (!codec) return null;
  return channels ? `${codec} ${channels}` : codec;
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
  const minuteMatch = text.match(/\b(\d{1,4})\s*(?:min|minutes?)\b/i);
  if (minuteMatch) return Number(minuteMatch[1]);
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

function normalizeFormat(value, url) {
  const direct = useful(value);
  const upper = direct?.toUpperCase() ?? "";
  if (/M3U8|HLS/.test(upper)) return "HLS";
  if (/MPD|DASH/.test(upper)) return "DASH";
  if (/\bMP4\b/.test(upper)) return "MP4";
  if (/\bMKV\b|MATROSKA/.test(upper)) return "MKV";
  const path = String(url ?? "").split(/[?#]/)[0].toLowerCase();
  if (path.endsWith(".m3u8")) return "HLS";
  if (path.endsWith(".mpd")) return "DASH";
  if (path.endsWith(".mp4") || path.endsWith(".m4v")) return "MP4";
  if (path.endsWith(".mkv")) return "MKV";
  return null;
}

function extractFileSize(value) {
  const text = useful(value);
  if (!text) return null;
  const match = text.match(/\b\d+(?:[.,]\d+)?\s*(?:KB|MB|GB|TB)\b/i);
  return match?.[0]?.replace(/\s+/g, " ") ?? null;
}

function collectText(stream = {}) {
  const values = [
    stream.name,
    stream.title,
    stream.description,
    stream.size,
    stream.quality,
    stream.resolution,
    stream.qualityLabel,
    stream.language,
    stream.lang,
    stream.audioLanguage,
    stream.codec,
    stream.videoCodec,
    stream.video_codec,
    stream.audio,
    stream.audioCodec,
    stream.audio_codec,
    stream.sourceType,
    stream.source_type,
    stream.releaseType,
    stream.release_type,
    stream.format,
    stream.hdr,
    stream.videoTech,
    stream.bitDepth,
    stream.subtitles,
    stream.sourceLabel,
    stream.sourceName,
    stream.source_name,
    stream.label,
    stream.filename,
    stream.fileName,
    stream.releaseName,
    stream.release_name,
    stream.behaviorHints?.filename,
  ];
  return values.map((value) => clean(value) ?? "").join(" ");
}

function mediaLine(metadata = {}) {
  const title = useful(metadata.title ?? metadata.name ?? metadata.originalTitle ?? metadata.original_name);
  const year = positiveInt(metadata.year ?? yearFromDate(metadata.releaseDate ?? metadata.release_date ?? metadata.firstAirDate ?? metadata.first_air_date));
  const genres = Array.isArray(metadata.genres)
    ? metadata.genres.map((value) => useful(value?.name ?? value)).filter(Boolean).slice(0, 3)
    : [];
  const parts = [];
  if (title) parts.push(title);
  if (year) parts.push(String(year));
  if (genres.length) parts.push(genres.join(", "));
  return parts.length ? `🎬 ${parts.join(" • ")}` : null;
}

function formatDuration(minutes) {
  const total = Math.max(1, Math.round(Number(minutes)));
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (!hours) return `${rest}min`;
  return rest ? `${hours}h${String(rest).padStart(2, "0")}` : `${hours}h`;
}

function readableProviderId(value) {
  const text = useful(value);
  if (!text) return null;
  return text
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
    .join(" ");
}

function firstUseful(...values) {
  for (const value of values) {
    const candidate = useful(value);
    if (candidate) return candidate;
  }
  return null;
}

function unique(values) {
  return [...new Set((values ?? []).filter(Boolean))];
}

function brief(value) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > 180 ? `${text.slice(0, 177).replace(/\s+\S*$/, "")}…` : text;
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
  if (Array.isArray(value)) return value.map((item) => String(item ?? "").trim()).filter(Boolean).join(" ") || null;
  const text = String(value).trim();
  return text || null;
}
