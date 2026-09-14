#!/usr/bin/env python3
"""Upgrade Core stream presentation to structured language + role facts.

`Original`/`Dub`/`Sub` are roles, not languages. Keep the legacy scalar
`language` field for client compatibility while adding `originalLanguage` and
`languageTracks` as factual structured presentation data.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine_v2/src/stream-presentation.mjs"
GLOBAL = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
TEST = ROOT / "engine_v2/tests/stream-presentation.test.mjs"


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if new in text:
        return text, False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one source shape, got {count}")
    return text.replace(old, new, 1), True


ENGINE_HELPERS = r'''
const LANGUAGE_CODE_ALIASES = Object.freeze({
  en: "en", eng: "en", english: "en",
  fr: "fr", fra: "fr", fre: "fr", french: "fr", francais: "fr", français: "fr",
  hi: "hi", hin: "hi", hindi: "hi",
  ja: "ja", jpn: "ja", japanese: "ja",
  ta: "ta", tam: "ta", tamil: "ta",
  te: "te", tel: "te", telugu: "te",
  bn: "bn", ben: "bn", bengali: "bn",
  ml: "ml", mal: "ml", malayalam: "ml",
  kn: "kn", kan: "kn", kannada: "kn",
  pa: "pa", pan: "pa", punjabi: "pa",
  gu: "gu", guj: "gu", gujarati: "gu",
  mr: "mr", mar: "mr", marathi: "mr",
  ur: "ur", urd: "ur", urdu: "ur",
  ko: "ko", kor: "ko", korean: "ko",
  es: "es", spa: "es", spanish: "es",
  de: "de", deu: "de", ger: "de", german: "de",
  it: "it", ita: "it", italian: "it",
  pt: "pt", por: "pt", portuguese: "pt",
  ar: "ar", ara: "ar", arabic: "ar",
  tr: "tr", tur: "tr", turkish: "tr",
  ru: "ru", rus: "ru", russian: "ru",
  zh: "zh", zho: "zh", chi: "zh", chinese: "zh",
});

const LANGUAGE_NAMES = Object.freeze({
  en: "English", fr: "French", hi: "Hindi", ja: "Japanese", ta: "Tamil", te: "Telugu",
  bn: "Bengali", ml: "Malayalam", kn: "Kannada", pa: "Punjabi", gu: "Gujarati", mr: "Marathi",
  ur: "Urdu", ko: "Korean", es: "Spanish", de: "German", it: "Italian", pt: "Portuguese",
  ar: "Arabic", tr: "Turkish", ru: "Russian", zh: "Chinese",
});

export function normalizeLanguageCode(value) {
  const raw = useful(value);
  if (!raw) return null;
  const normalized = raw.toLowerCase().replace(/[_-]+/g, " ").replace(/\([^)]*\)/g, " ").replace(/\s+/g, " ").trim();
  if (LANGUAGE_CODE_ALIASES[normalized]) return LANGUAGE_CODE_ALIASES[normalized];
  const first = normalized.split(" ")[0];
  if (LANGUAGE_CODE_ALIASES[first]) return LANGUAGE_CODE_ALIASES[first];
  const locale = raw.toLowerCase().replace(/_/g, "-").match(/^([a-z]{2,3})(?:-[a-z]{2,4})?$/i)?.[1];
  return locale && LANGUAGE_CODE_ALIASES[locale] ? LANGUAGE_CODE_ALIASES[locale] : null;
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
    } else if (/^(?:VF|VFF|VFQ|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS|FR-CA)$/i.test(explicit)) {
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
'''.strip()

GLOBAL_HELPERS = r'''
function languageCode(v){var x=s(v).toLowerCase().replace(/[_-]+/g," ").replace(/\([^)]*\)/g," ").replace(/\s+/g," ").trim(),a={en:"en",eng:"en",english:"en",fr:"fr",fra:"fr",fre:"fr",french:"fr",francais:"fr",français:"fr",hi:"hi",hin:"hi",hindi:"hi",ja:"ja",jpn:"ja",japanese:"ja",ta:"ta",tam:"ta",tamil:"ta",te:"te",tel:"te",telugu:"te",bn:"bn",ben:"bn",bengali:"bn",ml:"ml",mal:"ml",malayalam:"ml",kn:"kn",kan:"kn",kannada:"kn",pa:"pa",pan:"pa",punjabi:"pa",gu:"gu",guj:"gu",gujarati:"gu",mr:"mr",mar:"mr",marathi:"mr",ur:"ur",urd:"ur",urdu:"ur",ko:"ko",kor:"ko",korean:"ko",es:"es",spa:"es",spanish:"es",de:"de",deu:"de",ger:"de",german:"de",it:"it",ita:"it",italian:"it",pt:"pt",por:"pt",portuguese:"pt",ar:"ar",ara:"ar",arabic:"ar",tr:"tr",tur:"tr",turkish:"tr",ru:"ru",rus:"ru",russian:"ru",zh:"zh",zho:"zh",chi:"zh",chinese:"zh"};if(a[x])return a[x];var first=x.split(" ")[0];return a[first]||""}
function languageName(code){return({en:"English",fr:"French",hi:"Hindi",ja:"Japanese",ta:"Tamil",te:"Telugu",bn:"Bengali",ml:"Malayalam",kn:"Kannada",pa:"Punjabi",gu:"Gujarati",mr:"Marathi",ur:"Urdu",ko:"Korean",es:"Spanish",de:"German",it:"Italian",pt:"Portuguese",ar:"Arabic",tr:"Turkish",ru:"Russian",zh:"Chinese"})[code]||String(code||"").toUpperCase()}
function languageRole(v){var x=s(v).toLowerCase();if(/\b(?:original|original audio|native|vo)\b/.test(x))return"Original";if(/\b(?:dub|dubbed|doublage|vf|vff|vfq)\b/.test(x))return"Dub";if(/\b(?:sub|subtitle|subbed|vostfr|sous[- ]?titre)\b/.test(x))return"Sub";return""}
function languageTracks(r,meta){var original=languageCode(meta&&meta.originalLanguage),out=[];function add(code,role){if(!code)return;var row={code:code,tag:code.toUpperCase(),label:languageName(code),role:role||null};for(var z=0;z<out.length;z++)if(out[z].code===row.code&&out[z].role===row.role)return;out.push(row)}var candidates=[r&&r.audioTracks,r&&r.audio_tracks,r&&r.audioLanguages,r&&r.audio_languages,r&&r.availableAudioTracks,r&&r.available_audio_tracks,r&&r.languages],rows=[];for(var ci=0;ci<candidates.length;ci++)if(Array.isArray(candidates[ci])&&candidates[ci].length){rows=candidates[ci];break}for(var i=0;i<rows.length;i++){var row=rows[i],value=typeof row==="string"?row:(row&& (row.language||row.lang||row.code||row.name||row.label||row.title)),code=languageCode(value),role=languageRole(typeof row==="string"?row:(row&&(row.role||row.kind||row.type||row.name||row.label)));if(code)add(code,role||(original?(code===original?"Original":"Dub"):""))}var explicit=meaningful(r&&r.language)?s(r.language):"",u=explicit.toUpperCase();if(!rows.length&&explicit){if(/\bVOSTFR\b/.test(u)){if(original)add(original,"Original");add("fr","Sub")}else if(/^(?:VO|ORIGINAL(?:[ ._-]?(?:AUDIO|LANG(?:UAGE)?))?)$/i.test(explicit)){if(original)add(original,"Original")}else if(/^(?:VF|VFF|VFQ|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS|FR-CA)$/i.test(explicit)){add("fr",original==="fr"?"Original":"Dub")}else if(/\bMULTI\b|\bDUAL(?:[- ]?AUDIO)?\b/i.test(explicit)){if(original)add(original,"Original");if(s(c.providerLanguageMode).toLowerCase()==="vf"&&original!=="fr")add("fr","Dub")}else{explicit.split(/\s*(?:\/|,|\+|\||;)\s*/).forEach(function(part){var code=languageCode(part);if(code)add(code,languageRole(part)||(original?(code===original?"Original":"Dub"):""))})}}var subs=Array.isArray(r&&r.subtitles)?r.subtitles:(Array.isArray(r&&r.extCaptions)?r.extCaptions:(Array.isArray(r&&r.captions)?r.captions:[]));for(var j=0;j<subs.length;j++){var sr=subs[j],sv=typeof sr==="string"?sr:(sr&&(sr.language||sr.lanName||sr.langName||sr.lan||sr.lang||sr.name||sr.label)),sc=languageCode(sv);if(sc)add(sc,"Sub")}if(/\bVOSTFR\b/i.test([r&&r.language,r&&r.description,r&&r.title].map(s).join(" ")))add("fr","Sub");return out}
function compactTrack(t){return t&&t.tag?t.tag+(t.role?" "+t.role:""):""}
function fullTrack(t){return t&&t.label?t.label+(t.role?" · "+t.role:""):""}
'''.strip()


def patch_engine() -> bool:
    text = ENGINE.read_text(encoding="utf-8")
    changed = False
    anchor = "export function normalizeLanguage(stream = {}, provider = {}) {"
    if "export function normalizeLanguageTracks" not in text:
        if text.count(anchor) != 1:
            raise AssertionError("engine language helper anchor drifted")
        text = text.replace(anchor, ENGINE_HELPERS + "\n\n" + anchor, 1)
        changed = True

    old = """export function collectFacts(stream = {}, metadata = {}, provider = {}) {
  const audio = normalizeAudio(stream.audio ?? stream.audioCodec ?? stream.audio_codec);
  const language = normalizeLanguage(stream, provider);
  const videoTech = normalizeVideoTech(stream.videoTech ?? stream.video_tech ?? stream.visualTags ?? stream.hdr ?? stream.description);
"""
    new = """export function collectFacts(stream = {}, metadata = {}, provider = {}) {
  const audio = normalizeAudio(stream.audio ?? stream.audioCodec ?? stream.audio_codec);
  const language = normalizeLanguage(stream, provider);
  const originalLanguage = normalizeLanguageCode(metadata.originalLanguage ?? metadata.original_language);
  const languageTracks = normalizeLanguageTracks(stream, metadata, provider);
  const videoTech = normalizeVideoTech(stream.videoTech ?? stream.video_tech ?? stream.visualTags ?? stream.hdr ?? stream.description);
"""
    text, did = replace_once(text, old, new, "engine collectFacts prelude")
    changed |= did
    old = """    quality: inferQuality(stream),
    language,
    codec: normalizeCodec(stream.codec ?? stream.codecName ?? stream.videoCodec ?? stream.video_codec),
"""
    new = """    quality: inferQuality(stream),
    language,
    originalLanguage,
    languageTracks,
    codec: normalizeCodec(stream.codec ?? stream.codecName ?? stream.videoCodec ?? stream.video_codec),
"""
    text, did = replace_once(text, old, new, "engine collectFacts language fields")
    changed |= did

    old = """    quality: facts.quality,
    language: facts.language,
    codec: facts.codec,
"""
    new = """    quality: facts.quality,
    language: facts.language,
    originalLanguage: facts.originalLanguage,
    languageTracks: facts.languageTracks,
    codec: facts.codec,
"""
    text, did = replace_once(text, old, new, "engine presentation output fields")
    changed |= did

    old = """  if (facts.audioChannels) out.push(facts.audioChannels);
  if (facts.language) out.push(facts.language);
  out.push(...(facts.subtitles ?? []));
"""
    new = """  if (facts.audioChannels) out.push(facts.audioChannels);
  const trackBadges = (facts.languageTracks ?? []).map(compactTrackLabel).filter(Boolean);
  if (trackBadges.length) out.push(...trackBadges); else if (facts.language) out.push(facts.language);
  out.push(...(facts.subtitles ?? []));
"""
    text, did = replace_once(text, old, new, "engine display badge language roles")
    changed |= did

    old = """function languageLine(facts) {
  if (!facts.language) return "";
  const prefix = ["VF", "VFQ", "MULTI (VF/VO)"].includes(facts.language) ? "🇫🇷" : facts.language === "VOSTFR" ? "🌐🇫🇷" : "🌐";
  const subtitles = (facts.subtitles ?? []).filter((value) => value !== "VOSTFR");
  return `${prefix} ${facts.language}${subtitles.length ? ` • 💬 ${subtitles.join(" • ")}` : ""}`;
}
"""
    new = """function languageLine(facts) {
  const tracks = (facts.languageTracks ?? []).map(fullTrackLabel).filter(Boolean);
  if (tracks.length) return `🌐 ${tracks.join(" • ")}`;
  if (!facts.language) return "";
  const prefix = ["VF", "VFQ", "MULTI (VF/VO)"].includes(facts.language) ? "🇫🇷" : facts.language === "VOSTFR" ? "🌐🇫🇷" : "🌐";
  const subtitles = (facts.subtitles ?? []).filter((value) => value !== "VOSTFR");
  return `${prefix} ${facts.language}${subtitles.length ? ` • 💬 ${subtitles.join(" • ")}` : ""}`;
}
"""
    text, did = replace_once(text, old, new, "engine language line")
    changed |= did

    ENGINE.write_text(text, encoding="utf-8")
    return changed


def patch_global() -> bool:
    text = GLOBAL.read_text(encoding="utf-8")
    changed = False
    old_revision = 'REVISION = "all-providers-client-projection-strongest-evidence-v22"'
    new_revision = 'REVISION = "all-providers-client-projection-language-roles-v23"'
    text, did = replace_once(text, old_revision, new_revision, "global presentation revision")
    changed |= did

    anchor = 'function codec(r){var v=meaningful(r&&r.codec)?s(r.codec):blob(r),u=v.toUpperCase();'
    if "function languageTracks(r,meta)" not in text:
        if text.count(anchor) != 1:
            raise AssertionError("global language helper anchor drifted")
        text = text.replace(anchor, GLOBAL_HELPERS + "\n" + anchor, 1)
        changed = True

    old = 'function badgeLabels(f){var out=[];if(f.quality)out.push(qualityLabel(f.quality));if(f.sourceType)out.push(f.sourceType);if(f.releaseType)out.push(f.releaseType);out=out.concat(f.videoTech);if(f.codec)out.push(f.codec);if(f.bitDepth)out.push(f.bitDepth);out=out.concat(f.audioTech||[]);if(f.audioCodec)out.push(f.audioCodec);if(f.audioChannels)out.push(f.audioChannels);if(f.language)out.push(f.language);if(f.duration)out.push(humanDuration(f.duration));if(f.ageRating)out.push(f.ageRating);return uniq(out)}'
    new = 'function badgeLabels(f){var out=[];if(f.quality)out.push(qualityLabel(f.quality));if(f.sourceType)out.push(f.sourceType);if(f.releaseType)out.push(f.releaseType);out=out.concat(f.videoTech);if(f.codec)out.push(f.codec);if(f.bitDepth)out.push(f.bitDepth);out=out.concat(f.audioTech||[]);if(f.audioCodec)out.push(f.audioCodec);if(f.audioChannels)out.push(f.audioChannels);var tb=(f.languageTracks||[]).map(compactTrack).filter(Boolean);if(tb.length)out=out.concat(tb);else if(f.language)out.push(f.language);if(f.duration)out.push(humanDuration(f.duration));if(f.ageRating)out.push(f.ageRating);return uniq(out)}'
    text, did = replace_once(text, old, new, "global badge labels")
    changed |= did

    old = 'function languageLine(f){if(!f.language)return"";var prefix=(f.language==="VF"||f.language==="VFQ"||f.language==="MULTI (VF/VO)")?"🇫🇷 ":(f.language==="VOSTFR"?"🌐🇫🇷 ":"🌐 ");var subs=(f.subtitles||[]).filter(function(v){return v&&v!=="VOSTFR"});return prefix+f.language+(subs.length?" • 💬 "+subs.join(" • "):"")}'
    new = 'function languageLine(f){var tracks=(f.languageTracks||[]).map(fullTrack).filter(Boolean);if(tracks.length)return"🌐 "+tracks.join(" • ");if(!f.language)return"";var prefix=(f.language==="VF"||f.language==="VFQ"||f.language==="MULTI (VF/VO)")?"🇫🇷 ":(f.language==="VOSTFR"?"🌐🇫🇷 ":"🌐 ");var subs=(f.subtitles||[]).filter(function(v){return v&&v!=="VOSTFR"});return prefix+f.language+(subs.length?" • 💬 "+subs.join(" • "):"")}'
    text, did = replace_once(text, old, new, "global language line")
    changed |= did

    old = 'return{title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind)}}'
    new = 'return{title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind),originalLanguage:s(d.original_language||d.originalLanguage)}}'
    text, did = replace_once(text, old, new, "global tmdb original language")
    changed |= did

    old = 'var out=Object.assign({},r),au=audioFacts(r),so=source(r),vf=videoFacts(r),f={quality:quality(r),language:language(r),codec:codec(r),audioTech:au.tech,audioCodec:au.codec,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||"",edition:meaningful(r&&r.edition)?s(r.edition):"",releaseGroup:meaningful(r&&(r.releaseGroup||r.release_group))?s(r.releaseGroup||r.release_group):"",bitrate:meaningful(r&&r.bitrate)?s(r.bitrate):""};'
    new = 'var out=Object.assign({},r),au=audioFacts(r),so=source(r),vf=videoFacts(r),f={quality:quality(r),language:language(r),originalLanguage:languageCode(meta&&meta.originalLanguage),languageTracks:languageTracks(r,meta),codec:codec(r),audioTech:au.tech,audioCodec:au.codec,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||"",edition:meaningful(r&&r.edition)?s(r.edition):"",releaseGroup:meaningful(r&&(r.releaseGroup||r.release_group))?s(r.releaseGroup||r.release_group):"",bitrate:meaningful(r&&r.bitrate)?s(r.bitrate):""};'
    text, did = replace_once(text, old, new, "global presentation facts")
    changed |= did

    old = 'if(languageDetailValue)out.language=languageDetailValue;else if(f.language)out.language=f.language;if(f.codec)out.codec=f.codec;'
    new = 'if(languageDetailValue)out.language=languageDetailValue;else if(f.language)out.language=f.language;out.originalLanguage=f.originalLanguage||null;out.languageTracks=f.languageTracks||[];if(f.codec)out.codec=f.codec;'
    text, did = replace_once(text, old, new, "global presentation structured language output")
    changed |= did

    old = 'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"")+(languageDetailValue?" - "+languageDetailValue:"");out.name=out.title;'
    new = 'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"");out.name=out.title;'
    text, did = replace_once(text, old, new, "global uniform title")
    changed |= did

    GLOBAL.write_text(text, encoding="utf-8")
    return changed


def patch_tests() -> bool:
    text = TEST.read_text(encoding="utf-8")
    changed = False
    old = '  normalizeLanguage,\n  normalizeSourceType,\n'
    new = '  normalizeLanguage,\n  normalizeLanguageTracks,\n  normalizeSourceType,\n'
    text, did = replace_once(text, old, new, "presentation test import")
    changed |= did
    marker = 'const normalizedMovie = normalizeTmdbPayload({\n'
    block = r'''
const indianTracks = presentStreamCandidate({
  name: "HindMoviez",
  url: "https://media.example/india.m3u8",
  language: "Hindi/English",
}, { title: "Example", year: 2026, mediaType: "movie", originalLanguage: "en" }, { id: "hindmoviez", name: "HindMoviez", languages: ["hi", "en"] });
assert.deepEqual(indianTracks.languageTracks, [
  { code: "hi", tag: "HI", label: "Hindi", role: "Dub" },
  { code: "en", tag: "EN", label: "English", role: "Original" },
]);
assert.match(indianTracks.description, /Hindi · Dub • English · Original/);
assert.ok(indianTracks.displayBadges.includes("HI Dub"));
assert.ok(indianTracks.displayBadges.includes("EN Original"));

const castleHindi = presentStreamCandidate({
  name: "Castle",
  url: "https://media.example/castle-hi.m3u8",
  language: "Hindi",
}, { title: "Example", year: 2026, mediaType: "movie", originalLanguage: "en" }, { id: "castle", name: "Castle", languages: ["hi", "en"] });
assert.deepEqual(castleHindi.languageTracks, [{ code: "hi", tag: "HI", label: "Hindi", role: "Dub" }]);
assert.match(castleHindi.description, /Hindi · Dub/);

const animeSub = presentStreamCandidate({
  name: "Anime-Sama",
  url: "https://media.example/anime.m3u8",
  language: "VOSTFR",
}, { title: "Anime", year: 2026, mediaType: "anime", originalLanguage: "ja" }, { id: "anime-sama", name: "Anime-Sama", languages: ["fr", "ja"] });
assert.deepEqual(animeSub.languageTracks, [
  { code: "ja", tag: "JA", label: "Japanese", role: "Original" },
  { code: "fr", tag: "FR", label: "French", role: "Sub" },
]);
assert.match(animeSub.description, /Japanese · Original • French · Sub/);

const hlsTracks = normalizeLanguageTracks({
  audioTracks: [{ language: "en", name: "English" }, { language: "fr", name: "French" }],
}, { originalLanguage: "en" }, vfProvider);
assert.deepEqual(hlsTracks, [
  { code: "en", tag: "EN", label: "English", role: "Original" },
  { code: "fr", tag: "FR", label: "French", role: "Dub" },
]);

'''
    if "const indianTracks = presentStreamCandidate" not in text:
        if text.count(marker) != 1:
            raise AssertionError("presentation test insertion marker drifted")
        text = text.replace(marker, block + marker, 1)
        changed = True
    TEST.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    changes = {"engine": patch_engine(), "global": patch_global(), "tests": patch_tests()}
    print("STREAM_LANGUAGE_ROLES_V1_OK", changes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
