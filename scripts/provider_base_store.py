#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides, _strip_generated_core_tail
from provider_purification import split_owned_prefix_bootstraps

ROOT = Path(__file__).resolve().parents[1]
BASES = ROOT / "provider-bases"
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
QUARANTINE_PATCH = "scripts/provider_patches/quarantine_provider_v1.py"
DYNAMIC_DOMAIN_PATCH = "scripts/provider_patches/runtime_repository_domain_materializer_v1.py"
DERIVED_PATCH_SCRIPTS = {
    QUARANTINE_PATCH,
    DYNAMIC_DOMAIN_PATCH,
    "scripts/provider_patches/adaptive_domain_recovery.py",
    "scripts/provider_patches/adaptive_runtime_recovery.py",
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    "scripts/provider_patches/adaptive_runtime_recovery_v5.py",
}

# ProviderBase owns durable provider logic. Everything below is derived publication
# state and must never become an input to the next Core build.
DERIVED_BASE_MARKERS = (
    "NUVIO_PROVIDER_QUARANTINE_V1",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_RUNTIME_COMPAT_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
    "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",
    "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1",
    "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
    "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
    "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
    "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
    "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
    "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
    "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
    "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5",
    "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1",
    "NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1",
    "NUVIO_RUNTIME_REPOSITORY_DOMAIN_MATERIALIZER_V1",
)

CLEAN_RECONSTRUCTION_SOURCE = "niakvio-clean-reconstruction-v2"
CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE = "niakvio-clean-reconstruction-v2-candidate"
CLEAN_RECONSTRUCTION_AUTHORING_VERSION = 2


def is_clean_reconstructed(provenance_row: dict[str, Any] | None) -> bool:
    row = provenance_row if isinstance(provenance_row, dict) else {}
    return (
        str(row.get("base_source") or "") == CLEAN_RECONSTRUCTION_SOURCE
        and row.get("clean_reconstruction_verified") is True
        and int(row.get("clean_reconstruction_authoring_version") or 0)
        >= CLEAN_RECONSTRUCTION_AUTHORING_VERSION
    )


def requires_clean_reconstruction(provenance_row: dict[str, Any] | None) -> bool:
    return not is_clean_reconstructed(provenance_row)


def is_clean_reconstruction_candidate(provenance_row: dict[str, Any] | None) -> bool:
    row = provenance_row if isinstance(provenance_row, dict) else {}
    return (
        str(row.get("base_source") or "") == CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE
        and row.get("clean_reconstruction_candidate") is True
        and row.get("clean_reconstruction_verified") is not True
        and int(row.get("clean_reconstruction_authoring_version") or 0)
        >= CLEAN_RECONSTRUCTION_AUTHORING_VERSION
    )


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_relative(provider_id: str, digest: str) -> str:
    return f"provider-bases/{safe_fragment(provider_id.casefold())}--base--{digest[:16]}.js"


def safe_base_path(relative: str) -> Path | None:
    if not isinstance(relative, str) or not relative.startswith("provider-bases/"):
        return None
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(BASES.resolve())
    except ValueError:
        return None
    return path


def forbidden_base_markers(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="strict")
    return [marker for marker in DERIVED_BASE_MARKERS if marker in text]


def assert_base_layering(data: bytes, provider_id: str) -> None:
    markers = forbidden_base_markers(data)
    if markers:
        raise ValueError(
            f"{provider_id}: ProviderBase contains derived publication layer(s): "
            + ",".join(markers)
        )


def strip_adaptive_runtime_wrappers(text: str) -> tuple[str, int]:
    """Remove only owned adaptive runtime wrappers from legacy provider bytes."""
    markers = (
        "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
        "/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5:",
    )
    call = '})(typeof globalThis!=="undefined"?globalThis:this,'
    removed = 0
    while True:
        starts = [text.find(marker) for marker in markers]
        starts = [value for value in starts if value >= 0]
        if not starts:
            break
        start = min(starts)
        call_at = text.find(call, start)
        end = text.find(");", call_at) if call_at >= 0 else -1
        if call_at < 0 or end < 0:
            raise ValueError("unterminated adaptive runtime recovery wrapper in ProviderBase")
        end += 2
        if text[end:end + 2] == "\r\n":
            end += 2
        elif text[end:end + 1] in ("\r", "\n"):
            end += 1
        text = text[:start] + text[end:]
        removed += 1
    return text.rstrip(), removed


def validate_base(data: bytes, provider_id: str) -> None:
    # A ProviderBase must remain an independently valid provider implementation.
    assert_base_layering(data, provider_id)
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    try:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), "--provider-base", str(temporary)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            detail = "\n".join(v.strip() for v in (result.stdout, result.stderr) if v.strip())
            raise ValueError(f"{provider_id}: ProviderBase rejected: {detail or 'no diagnostic'}")
    finally:
        temporary.unlink(missing_ok=True)


def write_base(provider_id: str, data: bytes) -> tuple[str, str]:
    digest = sha256(data)
    relative = base_relative(provider_id, digest)
    path = safe_base_path(relative)
    if path is None:
        raise ValueError(f"{provider_id}: unsafe ProviderBase path")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return relative, digest


def resolve_base(provider_id: str, provenance_row: dict[str, Any], *, require: bool = True) -> tuple[Path | None, str | None]:
    relative = str(provenance_row.get("base_filename") or "").strip()
    digest = str(provenance_row.get("base_sha256") or "").strip().casefold()
    path = safe_base_path(relative)
    if path is None or not path.is_file():
        if require:
            raise ValueError(f"{provider_id}: missing durable ProviderBase")
        return None, None
    actual = sha256(path.read_bytes())
    if not digest or actual != digest:
        raise ValueError(f"{provider_id}: ProviderBase SHA mismatch expected={digest or 'missing'} actual={actual}")
    return path, actual


def clean_base_from_published(provider_id: str, published_data: bytes) -> tuple[bytes, bool]:
    """Remove every owned derived layer while preserving durable provider logic."""
    published_text = published_data.decode("utf-8", errors="strict")
    base_text, stripped_core = _strip_generated_core_tail(published_text)
    base_text, stripped_adaptive = strip_adaptive_runtime_wrappers(base_text)
    base_data = base_text.encode("utf-8")
    prefix, body = split_owned_prefix_bootstraps(base_data)
    if prefix:
        base_data = body
    assert_base_layering(base_data, provider_id)
    return base_data, bool(stripped_core or stripped_adaptive or prefix)


def persist_base_from_published(provider_id: str, published_data: bytes) -> tuple[str, str, bool]:
    """Persist provider logic only; generated Core/routing layers are always derived."""
    base_data, stripped = clean_base_from_published(provider_id, published_data)
    validate_base(base_data, provider_id)
    relative, digest = write_base(provider_id, base_data)
    return relative, digest, stripped


def build_base_from_seed(
    provider_id: str,
    seed_data: bytes,
    *,
    overrides_path: Path | None = None,
) -> tuple[bytes, bool]:
    """Return clean ProviderBase bytes without writing repository state."""
    rebuilt, _records = apply_overrides(
        provider_id,
        seed_data,
        phase="discovery",
        excluded_patch_scripts=DERIVED_PATCH_SCRIPTS,
        include_global_core=False,
        config_path=overrides_path,
    )
    base_data, stripped = clean_base_from_published(provider_id, rebuilt)
    validate_base(base_data, provider_id)
    return base_data, stripped


def persist_base_from_seed(
    provider_id: str,
    seed_data: bytes,
    *,
    overrides_path: Path | None = None,
) -> tuple[str, str, bool]:
    """Rebuild durable provider logic from a clean provider seed.

    Publication-only quarantine, dynamic domain materialization and adaptive
    runtime/domain recovery are deliberately excluded. They remain derived state
    and are regenerated later by the finalizer from current policy/evidence.
    """
    base_data, stripped = build_base_from_seed(
        provider_id,
        seed_data,
        overrides_path=overrides_path,
    )
    relative, digest = write_base(provider_id, base_data)
    return relative, digest, stripped


def build_clean_provider_seed(
    provider_id: str,
    manifest_entry: dict[str, Any] | None = None,
    *,
    known_site: str | None = None,
    provider_model: dict[str, Any] | None = None,
) -> bytes:
    """Build a fresh NiakVIO-owned provider implementation from structured knowledge.

    The structured model may contain observed routes/domains/capability metadata,
    but never executable upstream source. The generated JavaScript is authored by
    NiakVIO and uses one common deterministic resolver skeleton. Learning may then
    specialize the model/runtime and must prove the resulting ProviderBase before
    publication.
    """
    entry = manifest_entry if isinstance(manifest_entry, dict) else {}
    supported = [
        str(value).strip().casefold()
        for value in entry.get("supportedTypes") or []
        if str(value).strip().casefold() in {"movie", "tv", "anime"}
    ]
    supported = list(dict.fromkeys(supported))
    display_name = str(entry.get("name") or provider_id).strip() or provider_id
    incoming_model = provider_model if isinstance(provider_model, dict) else {}
    model = {
        "providerId": canonical_id(provider_id),
        "displayName": display_name,
        "knownSite": str(known_site or incoming_model.get("knownSite") or "").strip() or None,
        "supportedTypes": supported,
        "strategy": str(incoming_model.get("strategy") or "unknown").strip().casefold(),
        "officialSite": str(incoming_model.get("officialSite") or "").strip() or None,
        "officialHub": str(incoming_model.get("officialHub") or "").strip() or None,
        "officialApi": str(incoming_model.get("officialApi") or "").strip() or None,
        "fixedApi": str(incoming_model.get("fixedApi") or "").strip() or None,
        "origins": [
            str(value).strip()
            for value in incoming_model.get("origins") or []
            if str(value).strip()
        ][:24],
        "observedUrls": [
            str(value).strip()
            for value in incoming_model.get("observedUrls") or []
            if str(value).strip()
        ][:32],
        "routes": [
            str(value).strip()
            for value in incoming_model.get("routes") or []
            if str(value).strip()
        ][:32],
        "reconstructionState": "learning-clean-seed",
        "authoring": "niakvio-owned-v2",
        "upstreamCodeEmbedded": False,
        "upstreamCodeExecuted": False,
    }
    payload = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    template = r'''"use strict";

/* NIAKVIO_PROVIDER_BASE_OWNED_V2 */
const NIAKVIO_PROVIDER_MODEL = Object.freeze(__MODEL_JSON__);

function _uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}
function _origin(value) {
  try { return new URL(value).origin; } catch (_) { return ""; }
}
function _absolute(value, base) {
  try { return new URL(value, base).toString(); } catch (_) { return ""; }
}
function _text(value) {
  return String(value == null ? "" : value);
}
function _embeddedText(value) {
  return _text(value)
    .replace(/\\u002[fF]/g, "/")
    .replace(/\\u003[aA]/g, ":")
    .replace(/\\u0026/g, "&")
    .replace(/\\u003[dD]/g, "=")
    .replace(/\\\//g, "/")
    .replace(/\\"/g, '"')
    .replace(/&quot;|&#34;/gi, '"')
    .replace(/&amp;/gi, "&");
}
function _slug(value) {
  return _text(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
function _directMedia(url) {
  return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/(?:hls|dash|stream)(?:\/|[?#]|$)/i.test(_text(url));
}
function _extractUrls(text, base) {
  const out = [];
  const normalized = _embeddedText(text);
  const patterns = [
    /(?:src|href|file|url|pathname|permalink|embedUrl|embed_url|contentUrl)\s*["']?\s*[:=]\s*["']([^"'<>\s]+)["']/gi,
    /https?:\\?\/\\?\/[^"'<>\s]+/gi
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(normalized))) {
      const raw = (match[1] || match[0] || "").replace(/\\\//g, "/").replace(/&amp;/g, "&");
      const absolute = _absolute(raw, base);
      if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
      if (out.length >= 240) break;
    }
  }
  return _uniq(out);
}
function _candidateScore(url, meta) {
  let parsed;
  try { parsed = new URL(url); } catch (_) { return -1; }
  const path = decodeURIComponent(parsed.pathname || "").toLowerCase();
  if (!path || path === "/" || /\/(?:_next|static|assets?|images?|icons?|fonts?)(?:\/|$)/i.test(path)) return -1;
  const slug = _slug(meta && meta.title);
  const tokens = slug.split("-").filter(token => token.length >= 3);
  let score = 0;
  if (slug && path.includes(slug)) score += 120;
  for (const token of tokens) if (path.includes(token)) score += 18;
  if (meta && meta.year && path.includes(String(meta.year))) score += 20;
  if (meta && meta.tmdbId && path.includes(String(meta.tmdbId))) score += 45;
  if (/\/(?:movie|movies|film|films|series|tv|show|watch|title|media)\//i.test(path)) score += 12;
  return score;
}
function _detailGuesses(meta, mediaType) {
  const out = [];
  const slug = _slug(meta && meta.title);
  const id = _text(meta && meta.tmdbId);
  const titleKind = mediaType === "movie" ? "movie" : "tv";
  const routes = mediaType === "movie"
    ? ["movie", "movies", "film", "films", "watch", "title"]
    : ["series", "tv", "show", "watch", "title"];
  for (const base of _searchBases()) {
    if (id && slug) {
      // Common modern catalogue convention, including Next/RSC apps:
      // /title/movie/157336-interstellar or /title/tv/1399-game-of-thrones
      out.push(_absolute("/title/" + titleKind + "/" + encodeURIComponent(id) + "-" + slug, base));
    }
    if (id) {
      out.push(_absolute("/title/" + titleKind + "/" + encodeURIComponent(id), base));
    }
    if (slug) {
      out.push(_absolute("/" + slug, base));
      for (const route of routes) out.push(_absolute("/" + route + "/" + slug, base));
    }
    if (id) {
      out.push(_absolute("/" + id, base));
      for (const route of routes) out.push(_absolute("/" + route + "/" + encodeURIComponent(id), base));
    }
  }
  return _uniq(out);
}
async function _fetch(url, options) {
  const response = await fetch(url, {
    redirect: "follow",
    headers: Object.assign({
      "Accept": "application/json,text/html,application/xhtml+xml,text/plain,*/*",
      "User-Agent": "Mozilla/5.0 NiakVIO/2"
    }, (options && options.headers) || {})
  });
  if (!response.ok) throw new Error("provider_http_" + response.status);
  return response;
}
async function _tmdb(tmdbId, mediaType) {
  const key = typeof globalThis !== "undefined" ? globalThis.TMDB_API_KEY : null;
  if (!key || !tmdbId) return null;
  const type = String(mediaType || "movie").toLowerCase() === "movie" ? "movie" : "tv";
  try {
    const response = await _fetch(
      "https://api.themoviedb.org/3/" + type + "/" + encodeURIComponent(tmdbId) +
      "?api_key=" + encodeURIComponent(key) + "&language=en-US"
    );
    const row = await response.json();
    return {
      title: row.title || row.name || row.original_title || row.original_name || "",
      year: String(row.release_date || row.first_air_date || "").slice(0, 4),
      tmdbId: String(tmdbId || "")
    };
  } catch (_) {
    return null;
  }
}
function _searchBases() {
  return _uniq([
    NIAKVIO_PROVIDER_MODEL.officialSite,
    NIAKVIO_PROVIDER_MODEL.knownSite,
    NIAKVIO_PROVIDER_MODEL.officialHub,
    ...(NIAKVIO_PROVIDER_MODEL.origins || [])
  ]).filter(value => /^https?:/i.test(value));
}
function _searchUrls(title) {
  const query = encodeURIComponent(title || "");
  const out = [];
  for (const base of _searchBases()) {
    out.push(_absolute("/?s=" + query, base));
    out.push(_absolute("/search?q=" + query, base));
    out.push(_absolute("/search/" + query, base));
  }
  return _uniq(out);
}
function _apiUrls(tmdbId, mediaType, season, episode) {
  const bases = _uniq([
    NIAKVIO_PROVIDER_MODEL.fixedApi,
    NIAKVIO_PROVIDER_MODEL.officialApi,
    ...(NIAKVIO_PROVIDER_MODEL.observedUrls || []).filter(value => /api|stream|source|embed|player/i.test(value))
  ]);
  const out = [];
  for (const base of bases) {
    if (!/^https?:/i.test(base)) continue;
    let url = base
      .replace(/\{(?:tmdb_?id|id)\}/gi, encodeURIComponent(tmdbId || ""))
      .replace(/\{(?:media_?type|type)\}/gi, encodeURIComponent(mediaType || "movie"))
      .replace(/\{season\}/gi, encodeURIComponent(season == null ? "" : season))
      .replace(/\{episode\}/gi, encodeURIComponent(episode == null ? "" : episode));
    out.push(url);
    try {
      const parsed = new URL(url);
      if (!parsed.searchParams.size) {
        parsed.searchParams.set("tmdbId", tmdbId || "");
        parsed.searchParams.set("type", mediaType || "movie");
        if (season != null) parsed.searchParams.set("season", String(season));
        if (episode != null) parsed.searchParams.set("episode", String(episode));
        out.push(parsed.toString());
      }
    } catch (_) {}
  }
  return _uniq(out);
}
function _jsonUrls(value, out) {
  out = out || [];
  if (typeof value === "string") {
    if (/^https?:/i.test(value)) out.push(value);
    return out;
  }
  if (Array.isArray(value)) {
    for (const child of value) _jsonUrls(child, out);
    return out;
  }
  if (value && typeof value === "object") {
    for (const child of Object.values(value)) _jsonUrls(child, out);
  }
  return out;
}
function _streams(urls, referer) {
  return _uniq(urls).slice(0, 40).map((url, index) => ({
    name: NIAKVIO_PROVIDER_MODEL.displayName,
    title: NIAKVIO_PROVIDER_MODEL.displayName + (index ? " #" + (index + 1) : ""),
    url,
    headers: referer ? { Referer: referer } : undefined
  }));
}
async function _resolveApi(tmdbId, mediaType, season, episode) {
  const streams = [];
  for (const url of _apiUrls(tmdbId, mediaType, season, episode).slice(0, 12)) {
    try {
      const response = await _fetch(url);
      const type = _text(response.headers.get("content-type")).toLowerCase();
      if (type.includes("json")) {
        const value = await response.json();
        streams.push(..._jsonUrls(value).filter(_directMedia));
      } else {
        const text = await response.text();
        streams.push(..._extractUrls(text, response.url || url).filter(_directMedia));
      }
    } catch (_) {}
    if (streams.length) break;
  }
  return _streams(streams, _searchBases()[0] || "");
}
async function _resolveHtml(meta, mediaType, season, episode) {
  if (!meta || !meta.title) return [];
  const candidates = [];
  for (const searchUrl of _searchUrls(meta.title).slice(0, 9)) {
    try {
      const response = await _fetch(searchUrl);
      const html = await response.text();
      const urls = _extractUrls(html, response.url || searchUrl)
        .filter(value => {
          const host = _origin(value);
          return host && _searchBases().some(base => _origin(base) === host);
        })
        .map(value => ({ url: value, score: _candidateScore(value, meta) }))
        .filter(row => row.score >= 18)
        .sort((a, b) => b.score - a.score)
        .map(row => row.url);
      candidates.push(...urls);
    } catch (_) {}
    if (candidates.length) break;
  }
  candidates.push(..._detailGuesses(meta, mediaType));
  const streams = [];
  for (const detailUrl of _uniq(candidates).slice(0, 24)) {
    try {
      const response = await _fetch(detailUrl);
      const html = await response.text();
      let urls = _extractUrls(html, response.url || detailUrl);
      if (mediaType !== "movie" && season != null && episode != null) {
        const token = new RegExp("(?:s(?:eason)?\\s*0*" + Number(season) + "[^\\n]{0,80}e(?:pisode)?\\s*0*" + Number(episode) + "|0*" + Number(season) + "x0*" + Number(episode) + ")", "i");
        const episodeLinks = urls.filter(value => token.test(value));
        if (episodeLinks.length) {
          for (const episodeUrl of episodeLinks.slice(0, 4)) {
            try {
              const episodeResponse = await _fetch(episodeUrl);
              const episodeHtml = await episodeResponse.text();
              urls = urls.concat(_extractUrls(episodeHtml, episodeResponse.url || episodeUrl));
            } catch (_) {}
          }
        }
      }
      const direct = urls.filter(_directMedia);
      if (direct.length) streams.push(..._streams(direct, response.url || detailUrl));
      if (!direct.length && /iframe|mixed_embed|html_scraper/i.test(NIAKVIO_PROVIDER_MODEL.strategy)) {
        const embeds = urls.filter(value => /embed|player|watch|iframe/i.test(value));
        streams.push(..._streams(embeds, response.url || detailUrl));
      }
    } catch (_) {}
    if (streams.length >= 12) break;
  }
  return streams.slice(0, 40);
}
async function getStreams(tmdbId, mediaType, season, episode) {
  const type = String(mediaType || "movie").toLowerCase();
  if (NIAKVIO_PROVIDER_MODEL.supportedTypes.length &&
      !NIAKVIO_PROVIDER_MODEL.supportedTypes.includes(type) &&
      !(type === "tv" && NIAKVIO_PROVIDER_MODEL.supportedTypes.includes("anime"))) {
    return [];
  }
  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;
  if (/api_stream_resolver|direct_media/i.test(strategy)) {
    const api = await _resolveApi(tmdbId, type, season, episode);
    if (api.length) return api;
  }
  const meta = await _tmdb(tmdbId, type);
  const html = await _resolveHtml(meta, type, season, episode);
  if (html.length) return html;
  if (!/api_stream_resolver|direct_media/i.test(strategy)) {
    return _resolveApi(tmdbId, type, season, episode);
  }
  return [];
}
module.exports = { getStreams, __niakvioProviderBase: NIAKVIO_PROVIDER_MODEL };
'''
    source = template.replace("__MODEL_JSON__", payload)
    return source.encode("utf-8")

def persist_clean_provider_seed(
    provider_id: str,
    manifest_entry: dict[str, Any] | None = None,
    *,
    known_site: str | None = None,
    provider_model: dict[str, Any] | None = None,
    overrides_path: Path | None = None,
) -> tuple[str, str, bool]:
    return persist_base_from_seed(
        provider_id,
        build_clean_provider_seed(
            provider_id,
            manifest_entry,
            known_site=known_site,
            provider_model=provider_model,
        ),
        overrides_path=overrides_path,
    )


def repair_legacy_bases() -> dict[str, Any]:
    """Mark every pre-v2 ProviderBase as compatibility-only legacy state.

    This command deliberately does *not* reconstruct ProviderBase bytes. The
    currently published implementation may remain available to existing clients
    and may be observed as LKG evidence, but it is never an executable seed for
    the new NiakVIO-owned ProviderBase.

    A provider leaves this queue only after a clean NiakVIO seed has been
    reconstructed independently, validated in Learning/Lab, materialized as a
    ProviderBase, and recorded with CLEAN_RECONSTRUCTION_SOURCE.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")

    provider_count = 0
    reconstruction_required = 0
    clean_reconstructed = 0
    marked_at = datetime.now(timezone.utc).isoformat()

    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = canonical_id(str(entry.get("id") or ""))
        if not provider_id:
            continue
        provider_count += 1
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")

        path, _digest = resolve_base(provider_id, row, require=True)
        assert path is not None
        assert_base_layering(path.read_bytes(), provider_id)

        if requires_clean_reconstruction(row):
            reconstruction_required += 1
            row["clean_reconstruction_required"] = True
            if is_clean_reconstruction_candidate(row):
                row["legacy_provider_base_role"] = "superseded-by-clean-candidate"
                row["clean_reconstruction_candidate_role"] = "pending-pipeline-proof"
            else:
                row["legacy_provider_base_role"] = "compatibility-lkg-only"
                row.pop("clean_reconstruction_candidate_role", None)
            row["legacy_provider_js_role"] = "knowledge-only-for-reconstruction"
            row["legacy_provider_js_executed_for_reconstruction"] = False
            row.setdefault("clean_reconstruction_marked_at", marked_at)
        else:
            clean_reconstructed += 1
            row["clean_reconstruction_required"] = False
            row.pop("legacy_provider_base_role", None)
            row.pop("legacy_provider_js_role", None)
            row.pop("legacy_provider_js_executed_for_reconstruction", None)
            row.pop("clean_reconstruction_candidate_role", None)

    store = provenance.get("provider_base_store")
    if not isinstance(store, dict):
        store = {}
        provenance["provider_base_store"] = store
    store.update({
        "schema_version": max(4, int(store.get("schema_version") or 0)),
        "provider_count": provider_count,
        "unique_base_count": provider_count,
        "initial_reconstruction_scope": int(store.get("initial_reconstruction_scope") or provider_count),
        "migration_scope": "all-current-providers",
        "owner": "provider_pipeline",
        "future_source": "provider_pipeline_only",
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": reconstruction_required,
        "authoring_version": CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        "authoring_policy": "niakvio-owned-clean-reconstruction-only",
        "clean_source": CLEAN_RECONSTRUCTION_SOURCE,
        "legacy_provider_role": "compatibility-lkg-and-knowledge-only",
        "upstream_code_role": "knowledge-only",
        "upstream_code_executed": False,
        "published_legacy_code_may_seed_new_base": False,
        "upstream_code_may_seed_new_base": False,
        "git_history_code_may_seed_new_base": False,
        "core_may_create_or_mutate_base": False,
        "semantic_validation": "on_base_creation_or_change",
        "core_integrity_validation": "coverage_and_sha_only",
        "derived_layers_forbidden": list(DERIVED_BASE_MARKERS),
    })
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "providers": provider_count,
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": reconstruction_required,
    }

def migrate_existing() -> dict[str, Any]:
    """Disabled legacy migration entry point.

    Published, upstream, snapshot and Git-history JavaScript are knowledge only;
    none of them may be transformed into a durable ProviderBase.
    """
    raise ValueError(
        "migrate-existing is disabled: legacy/upstream/public JavaScript may not seed ProviderBase; "
        "use NiakVIO clean reconstruction through Learning"
    )

def validate_all(*, validate_artifacts: bool = False) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers") or {}
    checked = 0
    bases: set[str] = set()
    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")
        path, _digest = resolve_base(provider_id, row, require=True)
        assert path is not None
        data = path.read_bytes()
        assert_base_layering(data, provider_id)
        if validate_artifacts:
            validate_base(data, provider_id)
        bases.add(path.relative_to(ROOT).as_posix())
        checked += 1
    if checked != len(manifest.get("scrapers") or []):
        raise ValueError(f"ProviderBase coverage mismatch checked={checked} manifest={len(manifest.get('scrapers') or [])}")
    clean_reconstructed = sum(
        1
        for entry in manifest.get("scrapers") or []
        if isinstance(entry, dict)
        and is_clean_reconstructed(rows.get(canonical_id(str(entry.get("id") or ""))))
    )
    return {
        "checked": checked,
        "unique_bases": len(bases),
        "artifact_validation": bool(validate_artifacts),
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": checked - clean_reconstructed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate-existing")
    sub.add_parser("repair-legacy")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument(
        "--artifacts",
        action="store_true",
        help="Also run the expensive Node provider validator for every base.",
    )
    args = parser.parse_args()
    if args.command == "migrate-existing":
        result = migrate_existing()
        print(
            f"FIELD_PROVIDER_BASE_MIGRATION providers={result['providers']} "
            f"migrated={result['migrated']} reused={result['reused']}"
        )
    elif args.command == "repair-legacy":
        result = repair_legacy_bases()
        print(
            f"FIELD_PROVIDER_BASE_REPAIR providers={result['providers']} "
            f"clean={result['clean_reconstructed']} required={result['reconstruction_required']}"
        )
    else:
        result = validate_all(validate_artifacts=bool(args.artifacts))
        print(
            f"FIELD_PROVIDER_BASE_COVERAGE checked={result['checked']} "
            f"unique_bases={result['unique_bases']} "
            f"clean={result['clean_reconstructed']} required={result['reconstruction_required']} "
            f"artifact_validation={str(result['artifact_validation']).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
