#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage every non-P2P provider declared by configured upstream manifests.

Upstream JavaScript is knowledge input only: it may reveal metadata, routes,
domains and exclusion signals, but it is never executed, patched into a runtime
candidate, persisted as ProviderBase, or published. Executable candidates are
always built from an existing NiakVIO ProviderBase or a fresh NiakVIO-owned
clean seed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides
from provider_base_store import (
    CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS,
    build_clean_provider_seed,
    is_clean_reconstruction_candidate,
    requires_clean_reconstruction,
    resolve_base,
    resolve_runtime_base,
)
from upstream_lkg import (
    create_pending, load_manifest_snapshot, load_provider_snapshot, load_registry,
    record_pending_source, validate_manifest_quality, write_pending,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "sources.json"
DEFAULT_STAGE = ROOT / "staging"
LKG_PATH = ROOT / "provider-lkg.json"
PROVENANCE_PATH = ROOT / "PROVENANCE.json"
OVERRIDES_PATH = ROOT / "provider-overrides.json"
USER_AGENT = "Nuvio-Curated-Discovery/5.13 (+GitHub Actions)"
URL_RE = re.compile(r"""https?://[^\s"\'`<>)]+""", re.I)
INFRASTRUCTURE_HOSTS = {
    "api.themoviedb.org", "www.themoviedb.org", "image.tmdb.org", "api.jikan.moe",
    "graphql.anilist.co", "api.tvmaze.com", "api.github.com",
    "raw.githubusercontent.com", "github.com", "www.github.com",
}
CUSTOM_B64_ALPHABET_RE = re.compile(r"""["']([A-Za-z]{52}0123456789\+/=)["']""")
CUSTOM_B64_TOKEN_RE = re.compile(r"""["']([A-Za-z0-9+/=]{4,256})["']""")
ROUTE_LITERAL_RE = re.compile(
    r"""(?:^|["'])(/(?:api|search|recherche|watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|movie|movies|media|sheet|film|films|tv|series|show|episode|season|wp-json|wp-admin|index\.php)[^"'<>\\\s]{0,500})""",
    re.I,
)
RESERVED_HOST_SUFFIXES = {".invalid", ".example", ".test", ".localhost"}


def decode_static_obfuscated_strings(text: str) -> list[str]:
    """Decode bounded string-table literals without executing upstream JavaScript."""
    alphabets = list(dict.fromkeys(CUSTOM_B64_ALPHABET_RE.findall(text)))
    if not alphabets:
        return []
    tokens = list(dict.fromkeys(CUSTOM_B64_TOKEN_RE.findall(text)))
    decoded: list[str] = []
    for alphabet in alphabets[:4]:
        for token in tokens[:4000]:
            raw = bytearray()
            bit_count = 0
            accumulator = 0
            valid = True
            for char in token:
                value = alphabet.find(char)
                if value < 0:
                    valid = False
                    break
                accumulator = accumulator * 64 + value if bit_count % 4 else value
                bit_count += 1
                if (bit_count - 1) % 4:
                    raw.append(0xFF & (accumulator >> ((-2 * bit_count) & 6)))
            if not valid or not raw:
                continue
            try:
                value = bytes(raw).decode("utf-8")
            except UnicodeDecodeError:
                continue
            value = value.strip()
            if not value or len(value) > 500:
                continue
            printable = sum(ch.isprintable() or ch in "\r\n\t" for ch in value)
            if printable / max(1, len(value)) < 0.95:
                continue
            if not re.search(
                r"https?://|/(?:api|search|watch|embed|player|play|video|stream|source|movie|tv|series|episode|season|wp-)|"
                r"\b(?:tmdb|imdb|referer|origin|worker|download|query|title|sources?)\b",
                value,
                re.I,
            ):
                continue
            if value not in decoded:
                decoded.append(value)
            if len(decoded) >= 256:
                return decoded
    return decoded


def static_knowledge_text(raw_upstream: bytes) -> tuple[str, list[str]]:
    text = raw_upstream[:2_000_000].decode("utf-8", errors="ignore")
    decoded = decode_static_obfuscated_strings(text)
    if not decoded:
        return text, []
    return text + "\n" + "\n".join(decoded), decoded


def _plausible_hosts(hosts: list[str]) -> list[str]:
    unique = list(dict.fromkeys(str(value or "").strip().casefold() for value in hosts if str(value or "").strip()))
    output: list[str] = []
    for host in unique:
        if host in INFRASTRUCTURE_HOSTS:
            continue
        if "." not in host or any(host.endswith(suffix) for suffix in RESERVED_HOST_SUFFIXES):
            continue
        # A regex/string-table scan may stop inside a concatenated hostname
        # (api.pur, raw.githubu, ...). Prefer a longer host that proves the
        # shorter token was only a prefix, never a usable origin.
        if any(other != host and other.startswith(host) and len(other) >= len(host) + 3 for other in unique):
            continue
        if host not in output:
            output.append(host)
    return output


def _route_placeholder(key: str) -> str | None:
    key = key.casefold()
    if key in {"q", "query", "search", "keyword", "s"}:
        return "{query}"
    if key in {"id", "tmdb", "tmdbid", "tmdb_id"}:
        return "{id}"
    if key in {"media", "type", "media_type", "m"}:
        return "{media}"
    if key in {"season", "saison"}:
        return "{season}"
    if key in {"episode", "ep", "e"}:
        return "{episode}"
    return None


def normalize_route_literal(value: str) -> str | None:
    value = str(value or "").strip().replace("\\/", "/")
    if not value:
        return None
    if value.startswith(("http://", "https://")):
        try:
            parsed = urllib.parse.urlparse(value)
        except ValueError:
            return None
        value = parsed.path or "/"
        if parsed.query:
            value += "?" + parsed.query
    if not value.startswith("/") or value == "/":
        return None
    path, sep, query = value.partition("?")
    if re.search(r"/(?:search|recherche)/?$", path, re.I) and not sep:
        path = path.rstrip("/") + "/{query}"
    if not sep:
        return path
    parts: list[str] = []
    for raw_part in query.split("&"):
        if not raw_part:
            continue
        key, eq, raw_value = raw_part.partition("=")
        if not key:
            continue
        placeholder = _route_placeholder(key)
        if eq and not raw_value and placeholder:
            raw_value = placeholder
        parts.append(key + ("=" + raw_value if eq else ""))
    return path + ("?" + "&".join(parts) if parts else "")


def infer_api_recipe(
    knowledge: dict[str, Any],
    patch: dict[str, Any],
    fixed: dict[str, Any],
) -> dict[str, Any] | None:
    explicit = patch.get("api_recipe")
    if isinstance(explicit, dict) and explicit:
        return explicit
    fragments = [str(value) for value in knowledge.get("routeFragments") or []]
    search = next((value for value in fragments if "search" in value.casefold()), None)
    stream = next((value for value in fragments if re.search(r"/stream/?$", value, re.I)), None)
    media = next((value for value in fragments if re.search(r"/media/?$", value, re.I)), None)
    sheet = next((value for value in fragments if re.search(r"/sheet/?$", value, re.I)), None)
    episode = next((value for value in fragments if re.search(r"/episode/?$", value, re.I)), None)
    if not fixed.get("api") or not search or not stream:
        return None
    search_route = normalize_route_literal(search) or search
    if "{query}" not in search_route:
        search_route = search_route.rstrip("/") + "/{query}"

    # Common API providers expose one provider-internal id from search, then
    # separate movie and episodic source routes. Keep those route fragments as
    # data instead of collapsing them to the first "/stream/" token seen.
    movie_route = stream.rstrip("/") + "/{id}"
    if media and sheet:
        movie_route = media.rstrip("/") + "/{id}" + sheet
    recipe: dict[str, Any] = {
        "base": str(fixed.get("api") or "").strip(),
        "referer": str(fixed.get("referer") or "").strip() or None,
        "searchRoute": search_route,
        "movieRoute": movie_route,
        "idFields": ["id", "_id", "media_id", "post_id"],
        "titleFields": ["title", "name", "original_title", "post_title"],
        "yearFields": ["year", "release_date", "first_air_date"],
        "sourceFields": ["url", "stream_url", "stream", "source", "file"],
        "typeFields": ["type", "media_type", "mediaType", "kind", "category"],
    }
    if stream and episode:
        recipe["episodeRoute"] = (
            stream.rstrip("/") + "/{id}" + episode +
            "?season={season}&episode={episode}"
        )
    return recipe


def fetch_bytes(url: str, attempts: int = 3, timeout: int = 35) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,application/javascript,*/*",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
            if not data:
                raise RuntimeError("empty response")
            return data
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise RuntimeError(f"download failed for {url}: {last_error}")


def fetch_manifest(urls: list[str]) -> tuple[dict[str, Any], str]:
    errors: list[str] = []
    for url in urls:
        try:
            payload = json.loads(fetch_bytes(url).decode("utf-8-sig"))
            if not isinstance(payload, dict) or not isinstance(payload.get("scrapers"), list):
                raise ValueError("missing scrapers array")
            return payload, url
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("; ".join(errors))


def safe_fragment(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip(".-")
    return cleaned[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def validate_javascript(data: bytes, url: str) -> None:
    if len(data) < 100:
        raise ValueError(f"JavaScript file is too small ({len(data)} bytes): {url}")
    head = data[:500].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        raise ValueError(f"HTML received instead of JavaScript: {url}")


def exclusion_reason(entry: dict[str, Any], data: bytes | None, exclusions: dict[str, Any]) -> str | None:
    provider_id = canonical_id(str(entry.get("id") or entry.get("name") or ""))
    explicit_ids = {canonical_id(str(value)) for value in exclusions.get("provider_ids", [])}
    if provider_id in explicit_ids:
        return "explicitly excluded P2P/torrent provider id"

    metadata_text = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    for pattern in exclusions.get("metadata_patterns", []):
        if str(pattern).casefold() in metadata_text:
            return f"metadata contains excluded P2P/torrent marker: {pattern}"

    if data is not None:
        script_text = data[:2_000_000].decode("utf-8", errors="ignore").casefold()
        for pattern in exclusions.get("script_patterns", []):
            if str(pattern).casefold() in script_text:
                return f"script contains excluded P2P/torrent marker: {pattern}"
    return None


def observed_site_from_upstream(data: bytes, provider_id: str) -> str | None:
    """Extract the strongest provider-looking site hint without executing code."""
    text, _decoded = static_knowledge_text(data)
    token = re.sub(r"[^a-z0-9]", "", provider_id.casefold())
    raw_hosts: list[str] = []
    parsed_rows: list[tuple[str, str]] = []
    for raw in URL_RE.findall(text):
        raw = raw.rstrip(".,;")
        try:
            parsed = urllib.parse.urlparse(raw)
        except ValueError:
            continue
        host = (parsed.hostname or "").casefold()
        if not host:
            continue
        raw_hosts.append(host)
        parsed_rows.append((raw, host))
    hosts = set(_plausible_hosts(raw_hosts))
    candidates: list[tuple[int, str]] = []
    for raw, host in parsed_rows:
        if host not in hosts:
            continue
        normalized = re.sub(r"[^a-z0-9]", "", host)
        score = 3 if token and len(token) >= 4 and token in normalized else 1
        if host.startswith(("api.", "player.", "cdn.")):
            score -= 1
        parsed = urllib.parse.urlparse(raw)
        origin = f"{parsed.scheme if parsed.scheme in {'http', 'https'} else 'https'}://{host}"
        candidates.append((score, origin))
    if not candidates:
        return None
    candidates.sort(key=lambda row: (-row[0], row[1]))
    return candidates[0][1]


def known_site_for_provider(
    provider_id: str,
    raw_upstream: bytes,
    overrides: dict[str, Any],
) -> str | None:
    patch = (overrides.get("provider_patches") or {}).get(provider_id, {})
    if isinstance(patch, dict):
        for key in ("official_site", "official_api", "official_hub"):
            value = str(patch.get(key) or "").strip()
            if value:
                return value
    return observed_site_from_upstream(raw_upstream, provider_id)


def upstream_knowledge(provider_id: str, entry: dict[str, Any], raw_upstream: bytes) -> dict[str, Any]:
    """Extract bounded provider knowledge statically, including obfuscated string tables."""
    text, decoded = static_knowledge_text(raw_upstream)
    raw_urls: list[tuple[str, str]] = []
    raw_hosts: list[str] = []
    for raw in URL_RE.findall(text):
        raw = raw.rstrip(".,;")
        try:
            parsed = urllib.parse.urlparse(raw)
        except ValueError:
            continue
        host = (parsed.hostname or "").casefold()
        if not host:
            continue
        raw_urls.append((raw, host))
        raw_hosts.append(host)

    hosts = _plausible_hosts(raw_hosts)
    allowed_hosts = set(hosts)
    urls: list[str] = []
    routes: list[str] = []
    fragments: list[str] = []

    for raw, host in raw_urls:
        if host not in allowed_hosts:
            continue
        parsed = urllib.parse.urlparse(raw)
        safe_url = urllib.parse.urlunparse((
            parsed.scheme if parsed.scheme in {"http", "https"} else "https",
            host,
            parsed.path or "/",
            "",
            parsed.query,
            "",
        ))
        if safe_url not in urls:
            urls.append(safe_url)
        route = normalize_route_literal(safe_url)
        if route and route not in routes:
            routes.append(route)

    literals = decoded + [match.group(1) for match in ROUTE_LITERAL_RE.finditer(text)]
    for literal in literals:
        value = str(literal or "").strip()
        if not value.startswith("/"):
            continue
        if value not in fragments:
            fragments.append(value)
        route = normalize_route_literal(value)
        if route and route not in routes:
            routes.append(route)

    supported = entry.get("supportedTypes") if isinstance(entry, dict) else []
    if isinstance(supported, str):
        supported = [supported]
    return {
        "providerId": provider_id,
        "supportedTypes": [str(value) for value in supported or []][:8],
        "hosts": hosts[:32],
        "routes": routes[:64],
        "routeFragments": fragments[:64],
        "observedUrls": urls[:48],
        "decodedStaticStringCount": len(decoded),
        "codeRole": "knowledge-only",
        "codeExecuted": False,
    }


def merge_provider_knowledge(
    current: dict[str, Any],
    historical: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge static facts without turning historical JavaScript into executable input."""
    previous = historical if isinstance(historical, dict) else {}
    merged = dict(current)
    for key, limit in (
        ("hosts", 48),
        ("routes", 96),
        ("routeFragments", 96),
        ("observedUrls", 72),
    ):
        values: list[str] = []
        for source in (current.get(key), previous.get(key)):
            for raw in source if isinstance(source, list) else []:
                value = str(raw or "").strip()
                if value and value not in values:
                    values.append(value)
        merged[key] = values[:limit]
    merged["decodedStaticStringCount"] = int(current.get("decodedStaticStringCount") or 0) + int(
        previous.get("decodedStaticStringCount") or 0
    )
    merged["historicalKnowledgeMerged"] = bool(previous)
    merged["historicalCodeRole"] = "knowledge-only" if previous else None
    merged["historicalCodeExecuted"] = False
    return merged


def clean_provider_model(
    provider_id: str,
    knowledge: dict[str, Any],
    overrides: dict[str, Any],
    known_site: str | None,
) -> dict[str, Any]:
    """Merge trusted configuration with current static facts without reviving stale domains."""
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    capabilities = overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"), dict) else {}
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    capability = capabilities.get(provider_id) if isinstance(capabilities.get(provider_id), dict) else {}
    fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
    strategy = str(patch.get("capability") or capability.get("strategy") or "unknown").strip().casefold()

    trusted_values = [
        known_site,
        patch.get("official_site"),
        patch.get("official_hub"),
        patch.get("official_api"),
        fixed.get("api"),
        fixed.get("referer"),
    ]
    trusted_hosts: set[str] = set()
    trusted_origins: list[str] = []
    for raw in trusted_values:
        value = str(raw or "").strip()
        if not value:
            continue
        try:
            parsed = urllib.parse.urlparse(value)
        except ValueError:
            continue
        host = (parsed.hostname or "").casefold()
        if not host or host not in _plausible_hosts([host]):
            continue
        trusted_hosts.add(host)
        origin = f"{parsed.scheme if parsed.scheme in {'http', 'https'} else 'https'}://{parsed.netloc}"
        if parsed.netloc and origin not in trusted_origins:
            trusted_origins.append(origin)

    def host_is_trusted(host: str) -> bool:
        value = str(host or "").strip().casefold()
        if not value:
            return False
        if not trusted_hosts:
            return True
        return any(
            value == trusted
            or value.endswith("." + trusted)
            or trusted.endswith("." + value)
            for trusted in trusted_hosts
        )

    learned_routes: list[str] = []
    for source in (patch.get("learned_routes"), capability.get("routes"), knowledge.get("routes")):
        for raw in source if isinstance(source, list) else []:
            value = normalize_route_literal(str(raw or "").strip()) or str(raw or "").strip()
            if value and value != "/" and value not in learned_routes:
                learned_routes.append(value)

    learned_urls: list[str] = []
    for source in (patch.get("learned_urls"), capability.get("observed_urls"), knowledge.get("observedUrls")):
        for raw in source if isinstance(source, list) else []:
            value = str(raw or "").strip()
            if not value:
                continue
            try:
                host = (urllib.parse.urlparse(value).hostname or "").casefold()
            except ValueError:
                continue
            if not host or host not in _plausible_hosts([host] + list(knowledge.get("hosts") or [])):
                continue
            if strategy == "official_domain_hub" and not host_is_trusted(host):
                continue
            if value not in learned_urls:
                learned_urls.append(value)

    origin_candidates: list[str] = list(trusted_origins)
    for value in capability.get("observed_origins") or []:
        value = str(value or "").strip()
        if value:
            origin_candidates.append(value)
    for host in knowledge.get("hosts") or []:
        value = str(host or "").strip()
        if value:
            origin_candidates.append("https://" + value)
    for mapping_key in ("runtime_domain_replacements", "route_replacements", "replacements"):
        mapping = patch.get(mapping_key) if isinstance(patch.get(mapping_key), dict) else {}
        for raw in mapping.values():
            value = str(raw or "").strip()
            if value:
                origin_candidates.append(value if value.startswith(("http://", "https://")) else "https://" + value.lstrip("/"))

    origin_hosts: list[str] = []
    parsed_origins: list[tuple[str, str]] = []
    for value in origin_candidates:
        try:
            parsed = urllib.parse.urlparse(value)
        except ValueError:
            continue
        host = (parsed.hostname or "").casefold()
        if not host:
            continue
        origin_hosts.append(host)
        parsed_origins.append((value, host))
    allowed_origin_hosts = set(_plausible_hosts(origin_hosts + list(knowledge.get("hosts") or [])))
    origins: list[str] = []
    for value, host in parsed_origins:
        if host not in allowed_origin_hosts:
            continue
        if strategy == "official_domain_hub" and not host_is_trusted(host):
            continue
        parsed = urllib.parse.urlparse(value if value.startswith(("http://", "https://")) else "https://" + value.lstrip("/"))
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
        if origin and origin not in origins:
            origins.append(origin)

    recipe = infer_api_recipe(knowledge, patch, fixed)
    if isinstance(recipe, dict):
        recipe = dict(recipe)
        recipe.setdefault("typeFields", ["type", "media_type", "mediaType", "kind", "category"])
        if strategy == "official_domain_hub":
            for key in ("base", "referer", "origin"):
                raw = str(recipe.get(key) or "").strip()
                if not raw:
                    continue
                try:
                    host = (urllib.parse.urlparse(raw).hostname or "").casefold()
                except ValueError:
                    host = ""
                if not host_is_trusted(host):
                    recipe.pop(key, None)

    return {
        "knownSite": str(known_site or "").strip() or None,
        "strategy": strategy,
        "officialSite": str(patch.get("official_site") or "").strip() or None,
        "officialHub": str(patch.get("official_hub") or "").strip() or None,
        "officialApi": str(patch.get("official_api") or "").strip() or None,
        "fixedApi": str(fixed.get("api") or "").strip() or None,
        "origins": origins[:32],
        "observedUrls": learned_urls[:48],
        "routes": learned_routes[:64],
        "apiRecipe": recipe,
        "knowledgeRole": "structured-static-observation-only",
        "legacyCodeEmbedded": False,
        "legacyCodeExecuted": False,
    }


def reconstruction_manifest_entry(
    provider_id: str,
    entry: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Project durable semantic capability into a one-shot ProviderBase rebuild."""
    output = dict(entry) if isinstance(entry, dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    semantic: list[str] = []
    for raw in patch.get("published_types") if isinstance(patch.get("published_types"), list) else []:
        value = str(raw or "").strip().casefold()
        if value in {"movie", "tv", "anime"} and value not in semantic:
            semantic.append(value)
    if semantic:
        # build_clean_provider_seed deliberately prefers canonicalSupportedTypes.
        # Keep the upstream transport list intact for diagnostics, but never let
        # movie/tv aliases erase a proven semantic anime capability.
        output["canonicalSupportedTypes"] = semantic
    return output


def executable_seed(
    provider_id: str,
    entry: dict[str, Any],
    raw_upstream: bytes,
    provenance_rows: dict[str, Any],
    overrides: dict[str, Any],
    *,
    clean_reconstruction: bool,
    force_clean_reconstruction: bool = False,
) -> tuple[bytes, str, str | None, bool, dict[str, Any], dict[str, Any]]:
    previous = provenance_rows.get(provider_id)
    previous_row = previous if isinstance(previous, dict) else {}
    site = known_site_for_provider(provider_id, raw_upstream, overrides)
    knowledge = upstream_knowledge(provider_id, entry, raw_upstream)
    reconstruction_required = requires_clean_reconstruction(previous_row)

    pending_clean = is_clean_reconstruction_candidate(previous_row)
    if pending_clean and force_clean_reconstruction:
        # Corrective reconstruction may recover static facts from the exact
        # preserved production LKG, but never executes or embeds those bytes.
        historical_path, _historical_sha = resolve_runtime_base(
            provider_id,
            previous_row,
            require=False,
        )
        if historical_path is not None:
            historical_knowledge = upstream_knowledge(
                provider_id,
                entry,
                historical_path.read_bytes(),
            )
            knowledge = merge_provider_knowledge(knowledge, historical_knowledge)

    provider_model = clean_provider_model(provider_id, knowledge, overrides, site)
    reconstruction_entry = reconstruction_manifest_entry(provider_id, entry, overrides)

    if pending_clean and not force_clean_reconstruction:
        path, _digest = resolve_base(provider_id, previous_row, require=True)
        assert path is not None
        return (
            path.read_bytes(),
            "pending-niakvio-clean-reconstruction-v2",
            site,
            True,
            knowledge,
            provider_model,
        )

    if force_clean_reconstruction or (reconstruction_required and clean_reconstruction):
        return (
            build_clean_provider_seed(
                provider_id,
                reconstruction_entry,
                known_site=site,
                provider_model=provider_model,
            ),
            "new-niakvio-clean-seed",
            site,
            True,
            knowledge,
            provider_model,
        )

    if isinstance(previous, dict):
        path, _digest = resolve_base(provider_id, previous, require=False)
        if path is not None:
            return (
                path.read_bytes(),
                (
                    "legacy-providerbase-compatibility-only"
                    if reconstruction_required
                    else "existing-niakvio-provider-base-v2"
                ),
                site,
                reconstruction_required,
                knowledge,
                provider_model,
            )

    return (
        build_clean_provider_seed(
            provider_id,
            reconstruction_entry,
            known_site=site,
            provider_model=provider_model,
        ),
        "new-niakvio-clean-seed",
        site,
        True,
        knowledge,
        provider_model,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument(
        "--require-all-upstreams",
        action="store_true",
        help="Fail if any upstream manifest cannot be loaded.",
    )
    parser.add_argument(
        "--clean-reconstruction",
        action="store_true",
        help="Build reconstruction-required providers from a fresh NiakVIO seed instead of compatibility LKG bytes.",
    )
    parser.add_argument(
        "--force-clean-reconstruction",
        action="append",
        default=[],
        metavar="PROVIDER_ID",
        help="Explicitly rebuild only the named clean ProviderBase candidate from current structured knowledge. May be repeated.",
    )
    args = parser.parse_args()
    forced_reconstruction_ids = {canonical_id(value) for value in args.force_clean_reconstruction if canonical_id(value)}

    config = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    exclusions = config.get("exclusions", {})
    overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    try:
        provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        provenance = {"providers": {}}
    provenance_rows = provenance.get("providers") if isinstance(provenance, dict) else {}
    if not isinstance(provenance_rows, dict):
        provenance_rows = {}
    stage = args.stage.resolve()
    if stage.exists():
        shutil.rmtree(stage)
    providers_dir = stage / "providers"
    manifests_dir = stage / "manifests"
    providers_dir.mkdir(parents=True)
    manifests_dir.mkdir(parents=True)

    candidates: list[dict[str, Any]] = []
    seen_canonical_ids: dict[str, dict[str, str]] = {}
    duplicate_inputs: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    upstream_reports: dict[str, Any] = {}
    errors: list[str] = []

    upstream_lkg_registry = load_registry(ROOT)
    upstream_lkg_pending = create_pending(stage)

    for priority, (source_key, source_cfg) in enumerate(config["upstreams"].items()):
        manifest_origin = "live"
        live_manifest = False
        raw_provider_records: dict[str, tuple[bytes, str]] = {}
        try:
            manifest, manifest_url = fetch_manifest(source_cfg["manifest_urls"])
            validate_manifest_quality(manifest, source_key, upstream_lkg_registry)
            live_manifest = True
        except Exception as live_exc:
            snapshot = load_manifest_snapshot(upstream_lkg_registry, source_key, ROOT)
            if snapshot is None:
                message = f"{source_key}: live manifest unavailable/corrupt and no upstream LKG snapshot: {live_exc}"
                errors.append(message)
                upstream_reports[source_key] = {
                    "status": "published_fallback_only",
                    "error": str(live_exc),
                    "fallback": "current published provider bundles",
                }
                print(f"[ERROR] {message}", file=sys.stderr)
                continue
            manifest, manifest_url = snapshot
            validate_manifest_quality(manifest, source_key, upstream_lkg_registry)
            manifest_origin = "upstream_lkg"
            print(f"[WARN] {source_key}: using last-known-good upstream snapshot: {live_exc}", file=sys.stderr)

        (manifests_dir / f"{safe_fragment(source_key)}.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        source_count = 0
        source_excluded = 0
        source_failures: list[dict[str, str]] = []
        source_lkg_provider_fallbacks = 0

        for index, entry in enumerate(manifest["scrapers"]):
            if not isinstance(entry, dict):
                continue
            upstream_id = str(entry.get("id") or entry.get("name") or f"entry-{index}")
            provider_id = canonical_id(upstream_id)
            preliminary_reason = exclusion_reason(entry, None, exclusions)
            if preliminary_reason:
                excluded.append({"source": source_key, "id": upstream_id, "reason": preliminary_reason})
                source_excluded += 1
                print(f"[SKIP] {source_key}:{upstream_id}: {preliminary_reason}")
                continue
            if provider_id in seen_canonical_ids:
                existing = seen_canonical_ids[provider_id]
                duplicate_inputs.append({
                    "canonical_id": provider_id,
                    "rejected_source": source_key,
                    "rejected_id": upstream_id,
                    "existing_source": existing["source"],
                    "existing_key": existing["key"],
                })
                source_excluded += 1
                print(
                    f"[DUPLICATE] {source_key}:{upstream_id} rejected; "
                    f"{provider_id} already imported as {existing['key']}"
                )
                continue

            filename = entry.get("filename")
            if not isinstance(filename, str) or not filename.strip():
                source_failures.append({"id": upstream_id, "error": "missing filename"})
                continue

            provider_url = urllib.parse.urljoin(manifest_url, filename)
            local_dir = providers_dir / safe_fragment(source_key)
            local_dir.mkdir(parents=True, exist_ok=True)
            local_name = f"{safe_fragment(upstream_id)}.js"
            local_path = local_dir / local_name

            try:
                data: bytes | None = None
                download_error: Exception | None = None
                if live_manifest:
                    try:
                        data = fetch_bytes(provider_url)
                        validate_javascript(data, provider_url)
                        raw_provider_records[upstream_id] = (data, provider_url)
                    except Exception as exc:
                        download_error = exc
                if data is None:
                    data = load_provider_snapshot(upstream_lkg_registry, source_key, upstream_id, ROOT)
                    if data is not None:
                        source_lkg_provider_fallbacks += 1
                        validate_javascript(data, f"upstream-lkg:{source_key}:{upstream_id}")
                    elif not live_manifest:
                        # A partially populated LKG may still reference a reachable historical URL.
                        try:
                            data = fetch_bytes(provider_url)
                            validate_javascript(data, provider_url)
                        except Exception as exc:
                            download_error = exc
                if data is None:
                    raise RuntimeError(f"live and LKG provider downloads failed: {download_error}")

                reason = exclusion_reason(entry, data, exclusions)
                if reason:
                    excluded.append({"source": source_key, "id": upstream_id, "reason": reason})
                    source_excluded += 1
                    print(f"[SKIP] {source_key}:{upstream_id}: {reason}")
                    continue

                upstream_digest = hashlib.sha256(data).hexdigest()
                (
                    seed,
                    code_origin,
                    observed_site,
                    reconstruction_required,
                    knowledge,
                    provider_model,
                ) = executable_seed(
                    provider_id,
                    entry,
                    data,
                    provenance_rows,
                    overrides,
                    clean_reconstruction=bool(args.clean_reconstruction),
                    force_clean_reconstruction=provider_id in forced_reconstruction_ids,
                )
                clean_seed_origin = code_origin in {
                    "new-niakvio-clean-seed",
                    "pending-niakvio-clean-reconstruction-v2",
                }
                candidate_data, applied_patches = apply_overrides(
                    provider_id,
                    seed,
                    excluded_patch_scripts=(
                        CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS
                        if clean_seed_origin
                        else None
                    ),
                )
                validate_javascript(candidate_data, f"niakvio:{provider_id}")
                local_path.write_bytes(candidate_data)
                subprocess.run([
                    "node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(local_path)
                ], check=True, capture_output=True, text=True)
                digest = hashlib.sha256(candidate_data).hexdigest()
                candidates.append(
                    {
                        "key": f"{source_key}:{upstream_id}",
                        "source": source_key,
                        "source_name": source_cfg.get("name", source_key),
                        "source_priority": priority,
                        "source_repository": source_cfg.get("repository"),
                        "source_license": source_cfg.get("license"),
                        "source_license_evidence": source_cfg.get("license_evidence"),
                        "manifest_url": manifest_url,
                        "manifest_origin": manifest_origin,
                        "upstream_id": upstream_id,
                        "canonical_id": provider_id,
                        "provider_url": provider_url,
                        "observed_upstream_site": observed_site,
                        "local_path": str(local_path.relative_to(stage)),
                        "sha256": digest,
                        "upstream_sha256": upstream_digest,
                        "upstream_code_role": "knowledge-only",
                        "upstream_code_executed": False,
                        "upstream_knowledge": knowledge,
                        "clean_provider_model": provider_model,
                        "candidate_code_origin": code_origin,
                        "provider_base_reconstruction_required": bool(reconstruction_required),
                        "clean_reconstruction_mode": bool(
                            args.clean_reconstruction or provider_id in forced_reconstruction_ids
                        ),
                        "legacy_provider_js_executed_for_reconstruction": False,
                        "local_patches": applied_patches,
                        "bytes": len(candidate_data),
                        "metadata": reconstruction_manifest_entry(
                            provider_id, entry, overrides
                        ),
                    }
                )
                seen_canonical_ids[provider_id] = {
                    "source": source_key,
                    "key": f"{source_key}:{upstream_id}",
                }
                source_count += 1
                print(f"[OK] {source_key}:{upstream_id} ({manifest_origin})")
            except Exception as exc:
                source_failures.append({"id": upstream_id, "error": str(exc)})
                print(f"[WARN] {source_key}:{upstream_id}: {exc}", file=sys.stderr)

        if live_manifest:
            record_pending_source(
                upstream_lkg_pending, stage, source_key, manifest, manifest_url, raw_provider_records
            )
        upstream_reports[source_key] = {
            "status": "loaded" if live_manifest else "loaded_from_upstream_lkg",
            "manifest_origin": manifest_origin,
            "manifest_url": manifest_url,
            "declared": len(manifest["scrapers"]),
            "downloaded": source_count,
            "excluded": source_excluded,
            "provider_lkg_fallbacks": source_lkg_provider_fallbacks,
            "failures": source_failures,
        }

    write_pending(upstream_lkg_pending, stage)

    # Stage the currently published artifacts as low-priority baseline variants.
    # They are executed by the exact same movie/TV/anime health checks as fresh
    # upstream candidates. When an upstream update regresses to zero streams,
    # the last working local artifact can therefore win promotion instead of
    # being overwritten and pruned before the regression is visible in Nuvio.
    manifest_path = ROOT / "manifest.json"
    try:
        published_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        published_manifest = {"scrapers": []}
    baseline_dir = providers_dir / "published-baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    try:
        lkg_registry = json.loads(LKG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        lkg_registry = {"providers": {}}
    lkg_records = lkg_registry.get("providers", {}) if isinstance(lkg_registry, dict) else {}
    known_keys = {str(item.get("key")) for item in candidates}
    for entry in published_manifest.get("scrapers", []):
        if not isinstance(entry, dict):
            continue
        provider_id = canonical_id(str(entry.get("id") or entry.get("name") or ""))
        filename = entry.get("filename")
        if not provider_id or not isinstance(filename, str):
            continue
        source_path = (ROOT / filename).resolve()
        try:
            source_path.relative_to((ROOT / "providers").resolve())
        except ValueError:
            continue
        if not source_path.is_file() or exclusion_reason(entry, source_path.read_bytes(), exclusions):
            continue
        key = f"published:{provider_id}"
        if provider_id in seen_canonical_ids or key in known_keys:
            continue
        data = source_path.read_bytes()
        validate_javascript(data, filename)
        upstream_digest = hashlib.sha256(data).hexdigest()
        (
            seed,
            code_origin,
            observed_site,
            reconstruction_required,
            knowledge,
            provider_model,
        ) = executable_seed(
            provider_id,
            dict(entry),
            data,
            provenance_rows,
            overrides,
            clean_reconstruction=bool(args.clean_reconstruction),
            force_clean_reconstruction=provider_id in forced_reconstruction_ids,
        )
        clean_seed_origin = code_origin in {
            "new-niakvio-clean-seed",
            "pending-niakvio-clean-reconstruction-v2",
        }
        candidate_data, applied_patches = apply_overrides(
            provider_id,
            seed,
            excluded_patch_scripts=(
                CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS
                if clean_seed_origin
                else None
            ),
        )
        validate_javascript(candidate_data, f"niakvio:{provider_id}")
        local_path = baseline_dir / f"{safe_fragment(provider_id)}.js"
        local_path.write_bytes(candidate_data)
        subprocess.run([
            "node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(local_path)
        ], check=True, capture_output=True, text=True)
        digest = hashlib.sha256(candidate_data).hexdigest()
        lkg_record = lkg_records.get(provider_id, {}) if isinstance(lkg_records, dict) else {}
        is_registered_lkg = isinstance(lkg_record, dict) and lkg_record.get("sha256") == upstream_digest
        candidates.append({
            "key": key,
            "source": "published-baseline",
            "source_name": "Last published local artifact",
            "source_priority": len(config.get("upstreams", {})) + 100,
            "source_repository": config.get("repository", {}).get("name"),
            "source_license": "GPL-3.0-only",
            "source_license_evidence": "LICENSE",
            "manifest_url": "manifest.json",
            "upstream_id": str(entry.get("id") or provider_id),
            "canonical_id": provider_id,
            "provider_url": filename,
            "observed_upstream_site": observed_site,
            "local_path": str(local_path.relative_to(stage)),
            "sha256": digest,
            "upstream_sha256": upstream_digest,
            "upstream_code_role": "knowledge-only",
            "upstream_code_executed": False,
            "upstream_knowledge": knowledge,
            "clean_provider_model": provider_model,
            "candidate_code_origin": code_origin,
            "provider_base_reconstruction_required": bool(reconstruction_required),
            "clean_reconstruction_mode": bool(
                args.clean_reconstruction or provider_id in forced_reconstruction_ids
            ),
            "legacy_provider_js_executed_for_reconstruction": False,
            "local_patches": applied_patches,
            "baseline_origin": "published_manifest",
            "bytes": len(candidate_data),
            "metadata": reconstruction_manifest_entry(provider_id, dict(entry), overrides),
            "baseline": True,
            "lkg": is_registered_lkg,
            "lkg_verified_categories": list(lkg_record.get("verified_categories") or []) if is_registered_lkg else [],
        })
        known_keys.add(key)
        seen_canonical_ids[provider_id] = {"source": "published-baseline", "key": key}

    # Keep registered last-known-good artifacts available even after a future
    # manifest has moved to another hash. The pruner also retains these files.
    existing_entries = {
        canonical_id(str(entry.get("id") or entry.get("name") or "")): entry
        for entry in published_manifest.get("scrapers", []) if isinstance(entry, dict)
    }
    for provider_id, record in sorted(lkg_records.items() if isinstance(lkg_records, dict) else []):
        if not isinstance(record, dict):
            continue
        filename = record.get("filename")
        expected_sha = record.get("sha256")
        if not isinstance(filename, str) or not isinstance(expected_sha, str):
            continue
        source_path = (ROOT / filename).resolve()
        try:
            source_path.relative_to((ROOT / "providers").resolve())
        except ValueError:
            continue
        if not source_path.is_file():
            continue
        data = source_path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_sha:
            continue
        published_key = f"published:{provider_id}"
        published = next((item for item in candidates if item.get("key") == published_key), None)
        if published and published.get("sha256") == digest:
            published["lkg"] = True
            published["lkg_verified_categories"] = list(record.get("verified_categories") or [])
            continue
        key = f"lkg:{provider_id}"
        if provider_id in seen_canonical_ids or key in known_keys:
            continue
        local_path = baseline_dir / f"lkg-{safe_fragment(provider_id)}.js"
        local_path.write_bytes(data)
        metadata = dict(existing_entries.get(provider_id) or {"id": provider_id, "name": provider_id})
        metadata["filename"] = filename
        candidates.append({
            "key": key,
            "source": "local-lkg",
            "source_name": "Registered last-known-good artifact",
            "source_priority": len(config.get("upstreams", {})) + 101,
            "source_repository": config.get("repository", {}).get("name"),
            "source_license": "GPL-3.0-only",
            "source_license_evidence": "LICENSE",
            "manifest_url": "provider-lkg.json",
            "upstream_id": provider_id,
            "canonical_id": provider_id,
            "provider_url": filename,
            "local_path": str(local_path.relative_to(stage)),
            "sha256": digest,
            "upstream_sha256": digest,
            "local_patches": [],
            "baseline_origin": "provider_lkg_registry",
            "bytes": len(data),
            "metadata": metadata,
            "baseline": True,
            "lkg": True,
            "lkg_verified_categories": list(record.get("verified_categories") or []),
        })
        known_keys.add(key)
        seen_canonical_ids[provider_id] = {"source": "local-lkg", "key": key}

    # Every duplicate has already been rejected at import time. Health/Repair
    # therefore receives exactly one candidate per canonical provider.
    candidates = sorted(
        candidates,
        key=lambda row: (str(row.get("canonical_id") or ""), int(row.get("source_priority", 999))),
    )

    if len(candidates) != len({item["canonical_id"] for item in candidates}):
        raise RuntimeError("duplicate canonical candidate escaped input rejection")

    registry = {
        "schema_version": 65,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "canonical_provider_count": len(seen_canonical_ids),
        "input_duplicate_count": len(duplicate_inputs),
        "input_duplicates": duplicate_inputs,
        "excluded_count": len(excluded),
        "excluded": excluded,
        "upstreams": upstream_reports,
        "errors": errors,
        "candidates": candidates,
    }
    (stage / "candidates.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if not candidates:
        print("No non-P2P provider candidate was downloaded.", file=sys.stderr)
        return 1
    if errors and args.require_all_upstreams:
        published_fallbacks = sum(1 for item in candidates if item.get("source") == "published-baseline")
        if published_fallbacks <= 0:
            return 1
        print(
            f"[WARN] {len(errors)} upstream source(s) unavailable without an upstream snapshot; "
            f"continuing with {published_fallbacks} current published functional fallbacks.",
            file=sys.stderr,
        )

    print(
        f"Imported {len(candidates)} canonical providers "
        f"({registry['input_duplicate_count']} duplicate declaration(s) rejected at input); "
        f"excluded {len(excluded)} P2P/torrent entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
