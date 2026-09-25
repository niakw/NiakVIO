const UNKNOWN = /^(?:unknown|inconnue?|n\/a|na|none|null|undefined|-)$/i;
const QUALITY_PLACEHOLDER = /^(?:0|auto|automatic|source|original|default|unknown|inconnue?|n\/a|na|none|null|undefined|-)$/i;
const QUALITY_RANK = Object.freeze({ "240p": 240, "360p": 360, "480p": 480, "576p": 576, "720p": 720, "1080p": 1080, "1440p": 1440, "2160p": 2160 });

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

  const streamTitle = `${providerName}${facts.quality ? ` - ${qualityLabel(facts.quality)}` : ""}`;
  return {
    ...stream,
    title: streamTitle,
    name: streamTitle,
    description: lines.join("\n") || null,
    quality: facts.quality,
    language: facts.language,
    originalLanguage: facts.originalLanguage,
    languageTracks: facts.languageTracks,
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
  const originalLanguage = normalizeLanguageCode(metadata.originalLanguage ?? metadata.original_language);
  const languageTracks = normalizeLanguageTracks(stream, metadata, provider);
  const videoTech = normalizeVideoTech(stream.videoTech ?? stream.video_tech ?? stream.visualTags ?? stream.hdr ?? stream.description);
  const sourceType = normalizeSourceType(stream.sourceType ?? stream.source_type ?? stream.description ?? stream.filename);
  const releaseType = normalizeReleaseType(stream.releaseType ?? stream.release_type ?? stream.description ?? stream.filename);
  return {
    quality: inferQuality(stream),
    language,
    originalLanguage,
    languageTracks,
    codec: normalizeCodec(stream.codec ?? stream.codecName ?? stream.videoCodec ?? stream.video_codec),
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
  const trackBadges = (facts.languageTracks ?? []).map(compactTrackLabel).filter(Boolean);
  if (trackBadges.length) out.push(...trackBadges); else {
    const fallbackCode = normalizeLanguageCode(facts.language);
    if (fallbackCode) out.push(fallbackCode.toUpperCase());
  }
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
  const tracks = Array.isArray(facts.languageTracks) ? facts.languageTracks : [];
  for (const track of tracks) {
    const code = normalizeLanguageCode(track?.code ?? track?.tag ?? track?.label);
    if (!code) continue;
    ids.push(String(track?.role ?? "").toLowerCase() === "sub" ? `sub-${code}` : `lang-${code}`);
  }
  if (!tracks.length) {
    const code = normalizeLanguageCode(facts.language);
    if (code) ids.push(`lang-${code}`);
  }
  for (const value of facts.subtitles ?? []) {
    const text = String(value ?? "").trim();
    if (/^VOSTFR$/i.test(text)) { ids.push("sub-fr"); continue; }
    if (/^FORCED$/i.test(text)) { ids.push("forced"); continue; }
    if (/^(?:SDH|CC|SDH\/CC)$/i.test(text)) { ids.push("sdh-cc"); continue; }
    const match = text.match(/^SUB\s+([A-Z]{2,3}(?:-[A-Z0-9]{2,3})?)$/i);
    const code = match ? normalizeLanguageCode(match[1]) : null;
    if (code) ids.push(`sub-${code}`);
  }
  const age = ageBadgeId(facts.ageRating);
  if (age) ids.push(age);
  return uniq(ids);
}

function preciseQuality(value, allowBare = true) {
  if (Array.isArray(value)) {
    const rows = value.map((item) => preciseQuality(item, true)).filter(Boolean);
    return rows.sort((a, b) => (QUALITY_RANK[b] || 0) - (QUALITY_RANK[a] || 0))[0] || null;
  }
  if (typeof value === "number") {
    const height = Math.round(value);
    return [2160, 1440, 1080, 720, 576, 480, 360, 240].includes(height) ? `${height}p` : null;
  }
  const text = useful(value);
  if (!text || QUALITY_PLACEHOLDER.test(text)) return null;
  if (/\b(?:4K|UHD)\b/i.test(text)) return "2160p";
  if (/\b(?:QHD|2K)\b/i.test(text)) return "1440p";
  if (/\b(?:FHD|FULL[ ._-]?HD)\b/i.test(text)) return "1080p";
  const dimensions = text.match(/(?:^|[^0-9])(\d{3,4})\s*[x×]\s*(2160|1440|1080|720|576|480|360|240)(?:[^0-9]|$)/i);
  if (dimensions) return `${dimensions[2]}p`;
  const tagged = text.match(/(?:^|[^0-9])(2160|1440|1080|720|576|480|360|240)\s*p(?:[^0-9]|$)/i);
  if (tagged) return `${tagged[1]}p`;
  if (allowBare) {
    const bare = text.match(/^\s*(2160|1440|1080|720|576|480|360|240)\s*$/i);
    if (bare) return `${bare[1]}p`;
  }
  return null;
}

export function inferQuality(stream = {}) {
  for (const value of [stream.height, stream.videoHeight, stream.video_height, stream.resolution, stream.resolutions]) {
    const exact = preciseQuality(value, true);
    if (exact) return exact;
  }
  const explicit = useful(stream.quality);
  const exactExplicit = preciseQuality(explicit, true);
  if (exactExplicit) return exactExplicit;
  for (const value of [stream.sourceLabel, stream.label, stream.filename, stream.fileName, stream.name, stream.title, stream.description, stream.url]) {
    const exact = preciseQuality(value, false);
    if (exact) return exact;
  }
  if (explicit && /^(?:HD|SD)$/i.test(explicit)) return explicit.toUpperCase();
  return null;
}

export function normalizeQuality(value) {
  const exact = preciseQuality(value, true);
  if (exact) return exact;
  const text = useful(value);
  return text && /^(?:HD|SD)$/i.test(text) ? text.toUpperCase() : null;
}

function naturalLanguageLabel(value) {
  const raw = useful(value);
  if (!raw) return null;
  const aliases = {
    hi: "Hindi", hindi: "Hindi", en: "English", eng: "English", english: "English",
    fr: "French", fre: "French", fra: "French", french: "French", français: "French", francais: "French",
    ja: "Japanese", jpn: "Japanese", japanese: "Japanese", ko: "Korean", kor: "Korean", korean: "Korean",
    es: "Spanish", spa: "Spanish", spanish: "Spanish", de: "German", deu: "German", ger: "German", german: "German",
    it: "Italian", ita: "Italian", italian: "Italian", pt: "Portuguese", por: "Portuguese", portuguese: "Portuguese",
    ar: "Arabic", ara: "Arabic", arabic: "Arabic", tr: "Turkish", tur: "Turkish", turkish: "Turkish",
    ru: "Russian", rus: "Russian", russian: "Russian", zh: "Chinese", zho: "Chinese", chi: "Chinese", chinese: "Chinese",
    ta: "Tamil", tam: "Tamil", tamil: "Tamil", te: "Telugu", tel: "Telugu", telugu: "Telugu",
    ml: "Malayalam", mal: "Malayalam", malayalam: "Malayalam", bn: "Bengali", ben: "Bengali", bengali: "Bengali",
  };
  const parts = raw.split(/\s*(?:\/|,|\+|\||;)\s*/).map((part) => clean(part)).filter(Boolean);
  const mapped = parts.map((part) => aliases[String(part).toLowerCase()] || part);
  return uniq(mapped).join(" / ") || null;
}

const LANGUAGE_CODE_ALIASES = Object.freeze({
  en: "en", eng: "en", english: "en",
  fr: "fr", fra: "fr", fre: "fr", french: "fr", francais: "fr", français: "fr", vf: "fr", vff: "fr",
  de: "de", deu: "de", ger: "de", german: "de",
  es: "es", spa: "es", spanish: "es",
  bn: "bn", ben: "bn", bengali: "bn",
  pt: "pt", por: "pt", portuguese: "pt",
  bg: "bg", bul: "bg", bulgarian: "bg",
  zh: "zh", zho: "zh", chi: "zh", chinese: "zh", mandarin: "zh",
  ko: "ko", kor: "ko", korean: "ko",
  ar: "ar", ara: "ar", arabic: "ar",
  fi: "fi", fin: "fi", finnish: "fi",
  el: "el", ell: "el", gre: "el", greek: "el",
  hu: "hu", hun: "hu", hungarian: "hu",
  hi: "hi", hin: "hi", hindi: "hi",
  id: "id", ind: "id", indonesian: "id",
  fa: "fa", fas: "fa", per: "fa", persian: "fa", farsi: "fa",
  he: "he", heb: "he", hebrew: "he",
  it: "it", ita: "it", italian: "it",
  ja: "ja", jpn: "ja", japanese: "ja",
  ku: "ku", kur: "ku", kurdish: "ku",
  uz: "uz", uzb: "uz", uzbek: "uz",
  fil: "fil", filipino: "fil", tagalog: "fil", tgl: "fil",
  pl: "pl", pol: "pl", polish: "pl",
  ro: "ro", ron: "ro", rum: "ro", romanian: "ro",
  ru: "ru", rus: "ru", russian: "ru",
  sk: "sk", slk: "sk", slo: "sk", slovak: "sk",
  sv: "sv", swe: "sv", swedish: "sv",
  cs: "cs", ces: "cs", cze: "cs", czech: "cs",
  vi: "vi", vie: "vi", vietnamese: "vi",
  tr: "tr", tur: "tr", turkish: "tr",
  ta: "ta", tam: "ta", tamil: "ta",
  te: "te", tel: "te", telugu: "te",
  ml: "ml", mal: "ml", malayalam: "ml",
  kn: "kn", kan: "kn", kannada: "kn",
  pa: "pa", pan: "pa", punjabi: "pa",
  gu: "gu", guj: "gu", gujarati: "gu",
  mr: "mr", mar: "mr", marathi: "mr",
  ur: "ur", urd: "ur", urdu: "ur",
  yue: "yue", cantonese: "yue",
});

const LANGUAGE_LOCALE_ALIASES = Object.freeze({
  "fr-ca": "fr-ca", vfq: "fr-ca", "canadian french": "fr-ca", "french canada": "fr-ca", "french canadian": "fr-ca",
  "fr-ch": "fr-ch", "swiss french": "fr-ch", "french swiss": "fr-ch",
  "pt-br": "pt-br", "brazilian portuguese": "pt-br", "portuguese brazil": "pt-br",
  "pt-pt": "pt-pt", "european portuguese": "pt-pt", "portuguese portugal": "pt-pt",
  "es-419": "es-419", "latin american spanish": "es-419", "latam spanish": "es-419", "spanish latam": "es-419",
  "es-mx": "es-mx", "mexican spanish": "es-mx", "spanish mexico": "es-mx",
  "zh-hk": "zh-hk", "hong kong chinese": "zh-hk",
  "zh-tw": "zh-tw", "traditional chinese": "zh-tw", "taiwanese chinese": "zh-tw", "taiwanese mandarin": "zh-tw",
});

const LANGUAGE_NAMES = Object.freeze({
  en: "English", fr: "French", de: "German", es: "Spanish", bn: "Bengali", pt: "Portuguese",
  bg: "Bulgarian", zh: "Chinese", ko: "Korean", ar: "Arabic", fi: "Finnish", el: "Greek",
  hu: "Hungarian", hi: "Hindi", id: "Indonesian", fa: "Persian", he: "Hebrew", it: "Italian",
  ja: "Japanese", ku: "Kurdish", uz: "Uzbek", fil: "Filipino", pl: "Polish", ro: "Romanian",
  ru: "Russian", sk: "Slovak", sv: "Swedish", cs: "Czech", vi: "Vietnamese", tr: "Turkish",
  ta: "Tamil", te: "Telugu", ml: "Malayalam", kn: "Kannada", pa: "Punjabi", gu: "Gujarati",
  mr: "Marathi", ur: "Urdu", yue: "Cantonese",
  "fr-ca": "French (Canada)", "fr-ch": "French (Switzerland)", "pt-br": "Portuguese (Brazil)",
  "pt-pt": "Portuguese (Portugal)", "es-419": "Spanish (Latin America)", "es-mx": "Spanish (Mexico)",
  "zh-hk": "Chinese (Hong Kong)", "zh-tw": "Chinese (Taiwan)",
});

export function normalizeLanguageCode(value) {
  const raw = useful(value);
  if (!raw) return null;
  const localeKey = raw.toLowerCase().replace(/_/g, "-").replace(/\s+/g, " ").trim();
  if (LANGUAGE_LOCALE_ALIASES[localeKey]) return LANGUAGE_LOCALE_ALIASES[localeKey];
  const normalized = raw.toLowerCase().replace(/[_-]+/g, " ").replace(/\([^)]*\)/g, " ").replace(/\s+/g, " ").trim();
  if (LANGUAGE_LOCALE_ALIASES[normalized]) return LANGUAGE_LOCALE_ALIASES[normalized];
  if (LANGUAGE_CODE_ALIASES[normalized]) return LANGUAGE_CODE_ALIASES[normalized];
  const first = normalized.split(" ")[0];
  if (LANGUAGE_CODE_ALIASES[first]) return LANGUAGE_CODE_ALIASES[first];
  const locale = raw.toLowerCase().replace(/_/g, "-").match(/^([a-z]{2,3})(?:-([a-z0-9]{2,3}))?$/i);
  if (!locale) return null;
  const exact = locale[2] ? `${locale[1]}-${locale[2]}` : locale[1];
  if (LANGUAGE_LOCALE_ALIASES[exact]) return LANGUAGE_LOCALE_ALIASES[exact];
  return LANGUAGE_CODE_ALIASES[locale[1]] ?? null;
}
function roleFrom(value) {
  const text = clean(value)?.toLowerCase() ?? "";
  if (/\b(?:original|original audio|native|vo)\b/.test(text)) return "Original";
  if (/\b(?:dub|dubbed|doublage|vf|vff|vfq)\b/.test(text)) return "Dub";
  if (/\b(?:sub|subtitle|subbed|vostfr|sous[- ]?titre)\b/.test(text)) return "Sub";
  return null;
}

function trackObject(code, role) {
  if (!code) return null;
  return { code, tag: code.toUpperCase(), label: LANGUAGE_NAMES[code] ?? code.toUpperCase(), role: role ?? null };
}

function rawTrackRows(stream) {
  for (const value of [stream.audioTracks, stream.audio_tracks, stream.audioLanguages, stream.audio_languages, stream.availableAudioTracks, stream.available_audio_tracks, stream.languages]) {
    if (Array.isArray(value) && value.length) return value;
  }
  return [];
}

function subtitleTrackRows(stream) {
  for (const value of [stream.subtitles, stream.extCaptions, stream.captions]) {
    if (Array.isArray(value) && value.length) return value;
  }
  return [];
}

export function normalizeLanguageTracks(stream = {}, metadata = {}, provider = {}) {
  const original = normalizeLanguageCode(metadata.originalLanguage ?? metadata.original_language);
  const out = [];
  const add = (code, role) => {
    const row = trackObject(code, role);
    if (!row) return;
    if (!out.some((item) => item.code === row.code && item.role === row.role)) out.push(row);
  };

  const rows = rawTrackRows(stream);
  for (const row of rows) {
    const value = typeof row === "string" ? row : row?.language ?? row?.lang ?? row?.code ?? row?.name ?? row?.label ?? row?.title;
    const code = normalizeLanguageCode(value);
    if (!code) continue;
    const explicitRole = roleFrom(typeof row === "string" ? row : row?.role ?? row?.kind ?? row?.type ?? row?.name ?? row?.label ?? "");
    add(code, explicitRole ?? (original ? (code === original ? "Original" : "Dub") : null));
  }

  const explicit = useful(
    stream.language ?? stream.lang ?? stream.audioLanguage ?? stream.audio_language ??
    stream.audioTrack ?? stream.audio_track ?? stream.playerLanguage ?? stream.player_language ?? stream.dub,
  );
  const upper = explicit?.toUpperCase() ?? "";
  if (!rows.length && explicit) {
    if (/\bVOSTFR\b/.test(upper)) {
      if (original) add(original, "Original");
      add("fr", "Sub");
    } else if (/^(?:VO|ORIGINAL(?:[ ._-]?(?:AUDIO|LANG(?:UAGE)?))?)$/i.test(explicit)) {
      if (original) add(original, "Original");
    } else if (/^(?:VFQ|FR[ ._-]?CA)$/i.test(explicit)) {
      add("fr-ca", original === "fr-ca" ? "Original" : "Dub");
    } else if (/^(?:VF|VFF|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS)$/i.test(explicit)) {
      add("fr", original === "fr" ? "Original" : "Dub");
    } else if (/\bMULTI\b|\bDUAL(?:[- ]?AUDIO)?\b/i.test(explicit)) {
      if (original) add(original, "Original");
      if (isVfProvider(provider) && original !== "fr") add("fr", "Dub");
    } else {
      const parts = explicit.split(/\s*(?:\/|,|\+|\||;)\s*/).map((value) => value.trim()).filter(Boolean);
      for (const part of parts) {
        const code = normalizeLanguageCode(part);
        if (code) add(code, roleFrom(part) ?? (original ? (code === original ? "Original" : "Dub") : null));
      }
    }
  }

  for (const row of subtitleTrackRows(stream)) {
    const value = typeof row === "string" ? row : row?.language ?? row?.lanName ?? row?.langName ?? row?.lan ?? row?.lang ?? row?.name ?? row?.label;
    const code = normalizeLanguageCode(value);
    if (code) add(code, "Sub");
  }
  if (/\bVOSTFR\b/i.test([stream.language, stream.description, stream.title].map(clean).filter(Boolean).join(" "))) add("fr", "Sub");
  return out;
}

function compactTrackLabel(track) {
  return track?.tag ? `${track.tag}${track.role ? ` ${track.role}` : ""}` : null;
}

function fullTrackLabel(track) {
  return track?.label ? `${track.label}${track.role ? ` · ${track.role}` : ""}` : null;
}

export function normalizeLanguage(stream = {}, provider = {}) {
  const explicit = useful(
    stream.language ?? stream.lang ?? stream.audioLanguage ?? stream.audio_language ??
    stream.audioTrack ?? stream.audio_track ?? stream.playerLanguage ?? stream.player_language ?? stream.dub,
  );
  const hints = [stream.language, stream.languages, stream.languageTracks, stream.audioLanguage, stream.audio_languages, stream.audioTracks].map(clean).filter(Boolean).join(" ").toUpperCase();
  const vfProvider = isVfProvider(provider);
  const upper = explicit?.toUpperCase() ?? "";
  const isMulti = (text) => /\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b|\bDUAL(?:[- ]?AUDIO)?\b/.test(text);
  const isVost = (text) => /\bVOSTFR\b|\bVOST[ ._-]?FR\b|\bVO[ ._-]?ST[ ._-]?FR\b/.test(text);
  const isVfq = (text) => /\bVFQ\b|\bFR[ ._-]?CA\b|\bFRENCH[ ._-]?(?:CANADA|CANADIAN|QUEBEC)\b|\bQU[ÉE]B[ÉE]COIS\b/.test(text);
  const isVf = (text) => /\b(?:VF|VFF|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS|FR[ ._-]?FR)\b/.test(text);
  const isVo = (text) => /\bVO\b|\bORIGINAL(?:[ ._-]?(?:AUDIO|LANG(?:UAGE)?))?\b/.test(text);
  const combined = `${upper} ${hints}`.trim();

  // Do not let a precise explicit label hide a complementary track advertised
  // by the provider metadata. VF + VOSTFR is multi-audio evidence, not plain VF.
  if (isVost(combined) && (isVf(combined) || isVfq(combined) || isMulti(combined))) {
    return vfProvider ? "MULTI (VF/VO)" : "MULTI";
  }
  if (isVost(upper)) return "VOSTFR";
  if (isMulti(upper)) return vfProvider ? "MULTI (VF/VO)" : "MULTI";
  if (/^(?:VFQ|FR[ ._-]?CA)$/i.test(explicit || "")) return "VFQ";
  if (/^(?:VF|VFF|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS)$/i.test(explicit || "")) return "VF";
  if (/^(?:VO|ORIGINAL(?:[ ._-]?(?:AUDIO|LANG(?:UAGE)?))?)$/i.test(explicit || "")) return "VO";
  const natural = naturalLanguageLabel(explicit);
  if (natural) return natural;

  const hasVost = isVost(hints);
  const hasVf = isVf(hints) || isVfq(hints);
  if (isMulti(hints) || (hasVost && hasVf)) return vfProvider ? "MULTI (VF/VO)" : "MULTI";
  if (hasVost) return "VOSTFR";
  if (isVfq(hints)) return "VFQ";
  if (hasVf) return "VF";
  if (isVo(hints)) return "VO";
  return null;
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
  const upper = text.toUpperCase().replace(/\s+/g, " ").trim();
  const frenchRestricted = upper.match(/(?:^-|INTERDIT\s+(?:AUX\s+)?MOINS\s+DE\s+)(10|12|16|18)\b/);
  if (frenchRestricted) return `${frenchRestricted[1]}+`;
  const numeric = upper.match(/^(?:AGE[ ._-]*)?(0|6|7|10|12|13|14|15|16|17|18|19|21)\+?$/);
  if (numeric) return `${numeric[1]}+`;
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
  const explicit = Array.isArray(stream.subtitles) ? stream.subtitles : Array.isArray(stream.extCaptions) ? stream.extCaptions : Array.isArray(stream.captions) ? stream.captions : [];
  const text = [stream.description, stream.title, stream.filename, typeof stream.subtitles === "string" ? stream.subtitles : null].map(clean).filter(Boolean).join(" ");
  const out = [];
  const addCode = (value) => {
    const code = normalizeLanguageCode(value);
    if (code) out.push(`SUB ${code.toUpperCase()}`);
  };
  for (const row of explicit) addCode(row?.language ?? row?.lanName ?? row?.langName ?? row?.lan ?? row?.lang ?? row?.code ?? row?.name ?? row?.label ?? row);
  if (/\bVOSTFR\b/i.test(text)) out.push("SUB FR");
  for (const match of text.matchAll(/\bSUB(?:TITLE)?S?[ ._-]?([A-Z]{2,3}(?:-[A-Z0-9]{2,3})?)\b/gi)) addCode(match[1]);
  if (/\bFORCED\b/i.test(text)) out.push("FORCED");
  if (/\bSDH\b|\bCLOSED[ ]?CAPTION\b|\bCC\b/i.test(text)) out.push("SDH");
  return uniq(out);
}
function cleanProviderDisplayName(value) {
  const raw = clean(value);
  if (!raw) return null;
  return clean(raw.replace(
    /\s*(?:[-|•:])\s*(?:unknown|inconnu(?:e)?|n\/?a|na|none|null|undefined|unknown\s+(?:quality|language)|qualit(?:e|é)\s+inconnue|langue\s+inconnue)\s*$/i,
    "",
  ));
}

function providerDisplayName(stream, provider) {
  const raw = cleanProviderDisplayName(stream.name ?? stream.title);
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
  const rawTracks = facts.languageTracks ?? [];
  const tracks = rawTracks.map(fullTrackLabel).filter(Boolean);
  const representedSubCodes = new Set(
    rawTracks
      .filter((track) => String(track?.role ?? "").toLowerCase() === "sub")
      .map((track) => normalizeLanguageCode(track?.code ?? track?.tag ?? track?.label))
      .filter(Boolean),
  );
  const subtitles = (facts.subtitles ?? []).filter((value) => {
    const match = String(value ?? "").match(/^SUB\s+([A-Z]{2,3}(?:-[A-Z0-9]{2,3})?)$/i);
    const code = match ? normalizeLanguageCode(match[1]) : null;
    return !code || !representedSubCodes.has(code);
  });
  if (tracks.length) return `🌐 ${tracks.join(" • ")}${subtitles.length ? ` • 💬 ${subtitles.join(" • ")}` : ""}`;
  const code = normalizeLanguageCode(facts.language);
  const language = code ? (LANGUAGE_NAMES[code] ?? code.toUpperCase()) : null;
  if (!language && !subtitles.length) return "";
  return `🌐 ${[language, subtitles.length ? `💬 ${subtitles.join(" • ")}` : null].filter(Boolean).join(" • ")}`;
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
  const upper = useful(value)?.toUpperCase().replace(/\s+/g, " ").trim() ?? "";
  if (/^(?:ALL|ALL AGES|UNRESTRICTED|U|G)$/.test(upper)) return "age-all";
  const numeric = upper.match(/^(0|6|7|10|12|13|14|15|16|17|18|19|21)\+?$/);
  if (numeric) return `age-${numeric[1]}`;
  const named = {
    "PG-13": "age-us-pg13", "PG13": "age-us-pg13", "TV-Y": "age-us-tv-y", "TV-Y7": "age-us-tv-y7",
    "TV-G": "age-us-tv-g", "TV-PG": "age-us-tv-pg", "TV-14": "age-us-tv14", "TV-MA": "age-us-tv-ma",
    "NC-17": "age-us-nc17", "R15+": "age-jp-r15", "R18+": "age-jp-r18", "PG12": "age-jp-pg12",
  }[upper];
  if (named) return named;
  let match = upper.match(/^FSK[ .:_-]?(0|6|12|16|18)$/); if (match) return `age-de-fsk${match[1]}`;
  match = upper.match(/^KR[ .:_-]?(12|15|19)$/); if (match) return `age-kr${match[1]}`;
  if (/^KR[ .:_-]?(?:ALL|0)$/.test(upper)) return "age-kr-all";
  match = upper.match(/^UA[ ._-]?(7|13|16)\+?$/); if (match) return `age-in-ua${match[1]}`;
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
