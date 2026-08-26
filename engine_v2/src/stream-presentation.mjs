const UNKNOWN = /^(?:unknown|inconnue?|n\/a|na|none|null|undefined|-)$/i;

export function presentStreamCandidates(streams, metadata = {}, provider = {}) {
  return (Array.isArray(streams) ? streams : []).map((stream) => presentStreamCandidate(stream, metadata, provider));
}

export function presentStreamCandidate(stream = {}, metadata = {}, provider = {}) {
  const facts = collectFacts(stream, metadata, provider);
  const providerName = providerDisplayName(stream, provider);
  const media = mediaLine(metadata);
  const lines = [];
  if (media) lines.push(`${isSeries(metadata) ? "📺" : "🎬"} ${media}`);
  const timing = durationAgeLine(facts);
  if (timing) lines.push(timing);
  const language = languageLine(facts);
  if (language) lines.push(language);
  const technical = technicalLine(facts);
  if (technical) lines.push(technical);

  return {
    ...stream,
    title: `${providerName}${facts.quality ? ` - ${qualityLabel(facts.quality)}` : ""}`,
    name: providerName,
    description: lines.join("\n") || null,
    quality: facts.quality,
    language: facts.language,
    codec: facts.codec,
    audio: facts.audio,
    duration: facts.duration,
    sourceType: facts.sourceType,
    releaseType: facts.releaseType,
    format: facts.format,
    ageRating: facts.ageRating,
    videoTech: facts.videoTech,
    hdr: facts.hdr,
    bitDepth: facts.bitDepth,
    badgeIds: buildBadgeIds(facts),
    displayBadges: buildBadges(facts),
    presentationFacts: facts,
  };
}

export function collectFacts(stream = {}, metadata = {}, provider = {}) {
  const audio = normalizeAudio(stream.audio ?? stream.audioCodec ?? stream.audio_codec);
  const language = normalizeLanguage(stream, provider);
  const videoTech = normalizeVideoTech(stream.videoTech ?? stream.video_tech ?? stream.visualTags ?? stream.hdr ?? stream.description);
  const sourceType = normalizeSourceType(stream.sourceType ?? stream.source_type ?? stream.description ?? stream.filename);
  const releaseType = normalizeReleaseType(stream.releaseType ?? stream.release_type ?? stream.description ?? stream.filename);
  return {
    quality: normalizeQuality(stream.quality ?? stream.resolution),
    language,
    codec: normalizeCodec(stream.codec ?? stream.videoCodec ?? stream.video_codec),
    audio,
    audioCodec: normalizeAudioCodec(audio),
    audioChannels: normalizeAudioChannels(audio),
    duration: normalizeDuration(
      stream.duration ?? stream.durationMinutes ?? stream.duration_minutes ?? stream.runtime ??
      metadata.duration ?? metadata.durationMinutes ?? metadata.runtime,
    ),
    sourceType,
    releaseType,
    format: normalizeFormat(stream.format ?? stream.container, stream.url),
    ageRating: normalizeAgeRating(
      stream.ageRating ?? stream.age_rating ?? stream.certification ??
      metadata.ageRating ?? metadata.age_rating ?? metadata.certification ?? metadata.contentRating ?? metadata.content_rating,
    ),
    videoTech,
    hdr: normalizeHdr(stream.hdr ?? stream.hdrFormat ?? stream.hdr_format ?? videoTech),
    bitDepth: normalizeBitDepth(stream.bitDepth ?? stream.bit_depth ?? stream.description ?? stream.filename),
    subtitles: normalizeSubtitles(stream),
    edition: useful(stream.edition ?? stream.editions),
    releaseGroup: useful(stream.releaseGroup ?? stream.release_group),
    bitrate: useful(stream.bitrate ?? stream.bitRate ?? stream.bit_rate),
    size: useful(stream.size),
  };
}

export function buildBadges(facts = {}) {
  const out = [];
  if (facts.quality) out.push(qualityLabel(facts.quality));
  if (facts.sourceType) out.push(facts.sourceType);
  if (facts.releaseType) out.push(facts.releaseType);
  if (facts.edition) out.push(facts.edition);
  out.push(...(facts.videoTech ?? []));
  if (facts.codec) out.push(facts.codec);
  if (facts.bitDepth) out.push(facts.bitDepth);
  if (facts.audioCodec) out.push(facts.audioCodec);
  if (facts.audioChannels) out.push(facts.audioChannels);
  if (facts.language) out.push(facts.language);
  out.push(...(facts.subtitles ?? []));
  if (facts.ageRating) out.push(facts.ageRating);
  return uniq(out);
}

export function buildBadgeIds(facts = {}) {
  const ids = [];
  const quality = { "2160p": "4k-ultra-hd", "1080p": "1080p-full-hd", "720p": "720p-hd", "480p": "480p-sd" }[facts.quality];
  if (quality) ids.push(quality);
  const source = {
    "ULTRA HD BLU-RAY": "uhd-blu-ray", "BLU-RAY": "blu-ray-disc", "WEB-DL": "webdl",
    WEBRIP: "webrip", HDTV: "hdtv", "DVD RIP": "dvd-rip",
  }[facts.sourceType];
  if (source) ids.push(source);
  if (facts.releaseType === "REMUX") ids.push("remux");
  const videoIds = {
    "Dolby Vision": "dolby-vision", "HDR10+": "hdr10-plus", HDR10: "hdr10",
    "IMAX Enhanced": "imax-enhanced", IMAX: "imax",
  };
  for (const value of facts.videoTech ?? []) if (videoIds[value]) ids.push(videoIds[value]);
  const codec = { HEVC: "hevc", AVC: "avc" }[facts.codec];
  if (codec) ids.push(codec);
  if (facts.bitDepth === "10bit") ids.push("10bit");
  const audioCodec = {
    TrueHD: "truehd", "E-AC3": "dolby-digital-plus", AC3: "dolby-digital",
    "DTS-HD": "dts-hd-master-audio",
  }[facts.audioCodec];
  if (audioCodec) ids.push(audioCodec);
  const channels = { "7.1": "7.1", "5.1": "5.1", "2.0": "2.0", "1.0": "1.0" }[facts.audioChannels];
  if (channels) ids.push(channels);
  const language = {
    "MULTI (VF/VO)": "multi", MULTI: "multi", VF: "vf", VFQ: "vfq", VO: "vo", VOSTFR: "vostfr",
  }[facts.language];
  if (language) ids.push(language);
  const subtitleIds = { VOSTFR: "vostfr", "SUB FR": "sub-fr", "SUB EN": "sub-en", FORCED: "forced", SDH: "sdh-cc" };
  for (const value of facts.subtitles ?? []) if (subtitleIds[value]) ids.push(subtitleIds[value]);
  const age = ageBadgeId(facts.ageRating);
  if (age) ids.push(age);
  return uniq(ids);
}

export function normalizeQuality(value) {
  const text = useful(value);
  if (!text) return null;
  if (/^(?:4k|uhd|2160p?)$/i.test(text)) return "2160p";
  const match = text.match(/(?:^|\b)(2160|1440|1080|720|576|480)p?(?:\b|$)/i);
  return match ? `${match[1]}p` : text;
}

export function normalizeLanguage(stream = {}, provider = {}) {
  const explicit = useful(stream.language ?? stream.lang ?? stream.audioLanguage ?? stream.audio_language);
  const hints = [stream.description, stream.title, stream.sourceLabel, stream.filename].map(clean).filter(Boolean).join(" ").toUpperCase();
  const vfProvider = isVfProvider(provider);
  const upper = explicit?.toUpperCase() ?? "";
  const isMulti = (text) => /\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b|\bDUAL(?:[- ]?AUDIO)?\b/.test(text);
  const isVost = (text) => /\bVOSTFR\b|\bVOST[ ._-]?FR\b|\bVO[ ._-]?ST[ ._-]?FR\b/.test(text);
  const isVfq = (text) => /\bVFQ\b|\bFR[ ._-]?CA\b|\bFRENCH[ ._-]?(?:CANADA|CANADIAN|QUEBEC)\b|\bQU[ÉE]B[ÉE]COIS\b/.test(text);
  const isVf = (text) => /\b(?:VF|VFF|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS|FR[ ._-]?FR)\b/.test(text);
  const isVo = (text) => /\bVO\b|\bORIGINAL(?:[ ._-]?(?:AUDIO|LANG(?:UAGE)?))?\b|\b(?:EN|ENG|ENGLISH)\b/.test(text);

  if (isVost(upper)) return "VOSTFR";
  if (isMulti(upper)) return vfProvider ? "MULTI (VF/VO)" : "MULTI";
  if (isVfq(upper)) return isVost(hints) && vfProvider ? "MULTI (VF/VO)" : "VFQ";
  if (isVf(upper)) return isVost(hints) && vfProvider ? "MULTI (VF/VO)" : "VF";
  if (isVo(upper)) return "VO";

  const hasVost = isVost(hints);
  const hasVf = isVf(hints) || isVfq(hints);
  if (isMulti(hints) || (hasVost && hasVf)) return vfProvider ? "MULTI (VF/VO)" : "MULTI";
  if (hasVost) return "VOSTFR";
  if (isVfq(hints)) return "VFQ";
  if (hasVf) return "VF";
  if (isVo(hints)) return "VO";
  return vfProvider ? "VF" : "VO";
}

export function normalizeSourceType(value) {
  const text = useful(value);
  if (!text) return null;
  const compact = text.toUpperCase().replace(/[._\s]+/g, "-");
  if (/ULTRA-?HD-?BLU-?RAY|UHD-?BLU-?RAY|UHD-?BD/.test(compact)) return "ULTRA HD BLU-RAY";
  if (/BLU-?RAY|BDRIP|BRRIP/.test(compact)) return "BLU-RAY";
  if (/WEB-?DL/.test(compact)) return "WEB-DL";
  if (/WEB-?RIP/.test(compact)) return "WEBRIP";
  if (/HDTV/.test(compact)) return "HDTV";
  if (/DVD-?RIP|DVDRIP/.test(compact)) return "DVD RIP";
  return null;
}

export function normalizeReleaseType(value) {
  const text = useful(value);
  if (!text) return null;
  return /\bREMUX\b/i.test(text) ? "REMUX" : null;
}

export function normalizeCodec(value) {
  const text = useful(value);
  if (!text) return null;
  const upper = text.toUpperCase();
  if (/H\.?265|X265|HEVC/.test(upper)) return "HEVC";
  if (/H\.?264|X264|AVC/.test(upper)) return "AVC";
  if (/AV1/.test(upper)) return "AV1";
  if (/VP9/.test(upper)) return "VP9";
  return text;
}

export function normalizeAudio(value) {
  const text = useful(value);
  if (!text) return null;
  return text.replace(/\bDDP\b/ig, "E-AC3").replace(/\bDD\b/ig, "AC3").replace(/\s+/g, " ").trim();
}

export function normalizeDuration(value) {
  if (value == null || value === "") return null;
  if (typeof value === "number" && Number.isFinite(value) && value > 0) return value > 600 ? Math.round(value / 60) : Math.round(value);
  const text = useful(value);
  if (!text) return null;
  const hm = text.match(/(?:(\d+)\s*h(?:ours?|eures?)?)?\s*(?:(\d+)\s*m(?:in(?:utes?)?)?)?/i);
  if (hm && (hm[1] || hm[2])) return Number(hm[1] || 0) * 60 + Number(hm[2] || 0);
  const number = Number(text);
  return Number.isFinite(number) && number > 0 ? (number > 600 ? Math.round(number / 60) : Math.round(number)) : null;
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

function normalizeAudioCodec(value) {
  const upper = useful(value)?.toUpperCase() ?? "";
  if (/TRUE[ ._-]?HD/.test(upper)) return "TrueHD";
  if (/E-?AC-?3|DDP|DD\+/.test(upper)) return "E-AC3";
  if (/AC-?3/.test(upper)) return "AC3";
  if (/DTS[- ]?HD/.test(upper)) return "DTS-HD";
  if (/\bDTS\b/.test(upper)) return "DTS";
  if (/AAC/.test(upper)) return "AAC";
  if (/FLAC/.test(upper)) return "FLAC";
  if (/OPUS/.test(upper)) return "Opus";
  return null;
}

function normalizeAudioChannels(value) {
  return useful(value)?.match(/\b(7\.1|5\.1|2\.1|2\.0|1\.0)\b/)?.[1] ?? null;
}

function normalizeVideoTech(value) {
  const upper = Array.isArray(value) ? value.join(" ").toUpperCase() : (useful(value)?.toUpperCase() ?? "");
  const out = [];
  if (/DOLBY VISION|DOVI/.test(upper)) out.push("Dolby Vision");
  if (/HDR10\+|HDR10 PLUS/.test(upper)) out.push("HDR10+"); else if (/HDR10/.test(upper)) out.push("HDR10"); else if (/\bHDR\b/.test(upper)) out.push("HDR");
  if (/IMAX[ ._-]?ENHANCED/.test(upper)) out.push("IMAX Enhanced"); else if (/\bIMAX\b/.test(upper)) out.push("IMAX");
  return uniq(out);
}

function normalizeHdr(value) {
  const text = Array.isArray(value) ? value.join(" ") : useful(value);
  if (!text) return null;
  if (/DOLBY VISION|DOVI/i.test(text)) return "Dolby Vision";
  if (/HDR10\+|HDR10 PLUS/i.test(text)) return "HDR10+";
  if (/HDR10/i.test(text)) return "HDR10";
  if (/\bHDR\b/i.test(text)) return "HDR";
  return null;
}

function normalizeBitDepth(value) {
  const text = useful(value);
  if (!text) return null;
  if (/\b10[ ._-]?BIT\b|\bHI10P\b/i.test(text)) return "10bit";
  if (/\b8[ ._-]?BIT\b/i.test(text)) return "8bit";
  return null;
}

function normalizeFormat(value, url) {
  const text = useful(value)?.toUpperCase() ?? "";
  if (/M3U8|HLS/.test(text)) return "HLS";
  if (/MPD|DASH/.test(text)) return "DASH";
  if (/MKV/.test(text)) return "MKV";
  if (/MP4/.test(text)) return "MP4";
  const path = clean(typeof url === "object" ? url?.url : url)?.split(/[?#]/)[0].toLowerCase() ?? "";
  if (path.endsWith(".m3u8")) return "HLS";
  if (path.endsWith(".mpd")) return "DASH";
  if (path.endsWith(".mkv")) return "MKV";
  if (path.endsWith(".mp4")) return "MP4";
  return null;
}

function normalizeSubtitles(stream) {
  const text = [stream.description, stream.title, stream.filename].map(clean).filter(Boolean).join(" ").toUpperCase();
  const out = [];
  if (/\bVOSTFR\b/.test(text)) out.push("VOSTFR");
  if (/\bSUB[ ._-]?FR\b/.test(text)) out.push("SUB FR");
  if (/\bSUB[ ._-]?EN\b/.test(text)) out.push("SUB EN");
  if (/\bFORCED\b/.test(text)) out.push("FORCED");
  if (/\bSDH\b|\bCLOSED[ ]?CAPTION\b/.test(text)) out.push("SDH");
  return uniq(out);
}

function providerDisplayName(stream, provider) {
  const raw = clean(stream.name);
  const technical = raw && /(?:\b4K\b|\b(?:2160|1440|1080|720|576|480)P?\b|\b(?:VF|VFF|VFQ|VOSTFR|VO|MULTI)\b|\b(?:HEVC|AVC|AV1|VP9|WEB[ ._-]?DL|BLU[ ._-]?RAY|REMUX|HDR|DOLBY|DTS)\b)/i.test(raw);
  return (!technical && raw) || clean(provider.name) || clean(provider.id) || clean(stream.provider) || "Source";
}

function mediaLine(metadata) {
  const title = useful(metadata.title ?? metadata.name ?? metadata.originalTitle ?? metadata.original_name);
  const year = positiveInt(metadata.year ?? yearFromDate(metadata.releaseDate ?? metadata.release_date ?? metadata.firstAirDate ?? metadata.first_air_date));
  const parts = [title, year].filter(Boolean).map(String);
  if (isSeries(metadata) && (positiveInt(metadata.season) || positiveInt(metadata.episode))) {
    parts.push(`S${String(positiveInt(metadata.season) ?? 0).padStart(2, "0")}E${String(positiveInt(metadata.episode) ?? 0).padStart(2, "0")}`);
  }
  return parts.join(" • ");
}

function durationAgeLine(facts) {
  return [facts.duration ? `⏱ ${formatDuration(facts.duration)}` : null, facts.ageRating ? `🔞 ${facts.ageRating}` : null].filter(Boolean).join(" • ");
}

function languageLine(facts) {
  if (!facts.language) return "";
  const prefix = ["VF", "VFQ", "MULTI (VF/VO)"].includes(facts.language) ? "🇫🇷" : facts.language === "VOSTFR" ? "🌐🇫🇷" : "🌐";
  const subtitles = (facts.subtitles ?? []).filter((value) => value !== "VOSTFR");
  return `${prefix} ${facts.language}${subtitles.length ? ` • 💬 ${subtitles.join(" • ")}` : ""}`;
}

function technicalLine(facts) {
  const groups = [];
  const video = [];
  const source = [facts.sourceType, facts.releaseType].filter(Boolean).join(" ");
  if (source) video.push(source);
  if (facts.edition) video.push(facts.edition);
  if (facts.codec) video.push(`${facts.codec}${facts.bitDepth ? ` ${facts.bitDepth}` : ""}`); else if (facts.bitDepth) video.push(facts.bitDepth);
  video.push(...(facts.videoTech ?? []));
  if (facts.format) video.push(facts.format);
  if (video.length) groups.push(`🎞️ ${uniq(video).join(" • ")}`);
  if (facts.audio) groups.push(`🔊 ${facts.audio}`);
  const misc = [];
  if (facts.size) misc.push(`💾 ${facts.size}`);
  if (facts.bitrate) misc.push(`📶 ${facts.bitrate}`);
  if (facts.releaseGroup) misc.push(`🏷️ ${facts.releaseGroup}`);
  if (misc.length) groups.push(misc.join(" • "));
  return groups.join("  |  ");
}

function ageBadgeId(value) {
  const upper = useful(value)?.toUpperCase() ?? "";
  if (/^(?:U|G|TOUS|TOUS PUBLICS)$/.test(upper)) return "age-all";
  if (/^-?12$|^12\+$/.test(upper)) return "age-12";
  if (/^-?16$|^16\+$/.test(upper)) return "age-16";
  if (/^-?18$|^18\+$|^NC-17$/.test(upper)) return "age-18";
  if (/^PG-?13$/.test(upper)) return "pg-13";
  if (/^TV-?MA$/.test(upper)) return "tv-ma";
  return null;
}

function isVfProvider(provider) {
  if (String(provider.languageMode ?? "").toLowerCase() === "vf") return true;
  if (provider.projections?.vf === true) return true;
  const languages = [...(provider.languages ?? []), ...(provider.contentLanguage ?? []), ...(provider.scraper?.contentLanguage ?? [])].map((value) => String(value).toLowerCase());
  return languages.includes("fr");
}

function isSeries(metadata) {
  return ["tv", "series", "anime"].includes(String(metadata.mediaType ?? metadata.type ?? "movie").toLowerCase());
}

function qualityLabel(value) { return value === "2160p" ? "4K" : clean(value); }

function formatDuration(minutes) {
  const total = Math.max(1, Math.round(Number(minutes)));
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (!hours) return `${rest}min`;
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

function uniq(values) { return [...new Set((values ?? []).filter(Boolean))]; }

function useful(value) {
  const text = clean(value);
  return text && !UNKNOWN.test(text) ? text : null;
}

function clean(value) {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}
