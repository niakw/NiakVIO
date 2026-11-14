#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate deterministic language and no-anime manifest projections.

Outputs:
- vf/manifest.json: all declared/observed French-capable providers, preserving enabled state.
- no-anime/manifest.json: general manifest with clearly anime-specific providers removed.
- vf-no-anime/manifest.json: VF manifest with the same anime-specific filter.

The no-anime filter is intentionally conservative and deterministic: a provider
is excluded when it explicitly declares only ``anime`` as supported type, or
when its committed id/name contains ``anim`` (case-insensitive). A mixed
movie/tv/anime provider therefore remains unless its own id/name identifies it
as anime-oriented.

Classification comes from health-report.json, where observed runtime language
modes take precedence over broad upstream descriptions. When *no* declared or
observed language exists, a conservative fallback may infer French capability
from the provider's own public domain or homepage HTML. The fallback never
contradicts explicit runtime/manifest language evidence.

Provider filenames are rewritten relative to the nested manifest directories.
Provider ids are matched case-insensitively because Nuvio client activation
deliberately toggles id case when a provider transitions from disabled to enabled.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import socket
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

URL_RE = re.compile(r"https?://[^\s'\"`<>]+", re.IGNORECASE)
HTML_LANG_FR_RE = re.compile(
    r"<html\b[^>]*\blang\s*=\s*['\"]?fr(?:[-_][a-z]{2})?\b",
    re.IGNORECASE,
)
VF_RE = re.compile(r"(?<![a-z0-9])(?:vf|vostfr|french|fran[cç]ais)(?![a-z0-9])", re.IGNORECASE)
FRENCH_HOMEPAGE_CUES = (
    "films",
    "séries",
    "series",
    "regarder",
    "streaming gratuit",
    "accueil",
    "recherche",
    "épisodes",
    "episodes",
    "saison",
    "connexion",
    "nouveautés",
    "nouveautes",
)
STATIC_HOST_SUFFIXES = (
    "github.com",
    "githubusercontent.com",
    "postimg.cc",
    "tmdb.org",
    "themoviedb.org",
    "imdb.com",
    "google.com",
    "gstatic.com",
    "jsdelivr.net",
    "cloudflare.com",
)
FRENCH_HOST_TOKENS = (
    "french",
    "francais",
    "français",
    "vostfr",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def nested_entry(entry: dict[str, Any]) -> dict[str, Any]:
    copied = dict(entry)
    filename = str(copied.get("filename", ""))
    if filename and not filename.startswith(("http://", "https://", "/", "../")):
        copied["filename"] = f"../{filename}"
    return copied


def normalized_supported_types(entry: dict[str, Any]) -> list[str]:
    values = entry.get("supportedTypes", [])
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    return [str(value).strip().casefold() for value in values if str(value).strip()]


def semantic_supported_types(entry: dict[str, Any]) -> list[str]:
    """Return semantic capabilities, not Nuvio transport aliases."""
    canonical = entry.get("canonicalSupportedTypes")
    if isinstance(canonical, str):
        canonical = [canonical]
    if isinstance(canonical, list):
        values = [str(value).strip().casefold() for value in canonical if str(value).strip()]
        if values:
            return values
    return normalized_supported_types(entry)


def excluded_from_no_anime(entry: dict[str, Any]) -> bool:
    """Exclude semantic anime-only rows or providers whose committed identity says anime."""
    types = semantic_supported_types(entry)
    anime_only = bool(types) and set(types) == {"anime"}
    identity = " ".join(
        str(entry.get(key) or "").strip().casefold()
        for key in ("id", "name")
        if str(entry.get(key) or "").strip()
    )
    return anime_only or "anim" in identity


def build_no_anime_manifest(source: dict[str, Any], name_suffix: str = "Without anime providers") -> dict[str, Any]:
    """Copy a manifest while removing providers matching the deterministic anime filter."""
    entries = [
        nested_entry(entry)
        for entry in source.get("scrapers", [])
        if isinstance(entry, dict) and not excluded_from_no_anime(entry)
    ]
    return {
        "name": f"{source.get('name', 'NiakVIO')} — {name_suffix}",
        "version": source.get("version"),
        "scrapers": entries,
    }


def normalized_declared_languages(entry: dict[str, Any]) -> list[str]:
    declared = entry.get("contentLanguage", [])
    if isinstance(declared, str):
        declared = [declared]
    if not isinstance(declared, list):
        return []
    return [str(value).strip().casefold() for value in declared if str(value).strip()]


def france_only_catalog_rows(*, root: Path = ROOT) -> list[dict[str, Any]]:
    """Restore canonical VF-only providers from catalog during projection rebuild.

    A French-only provider is never inserted into Global. This step is read-only:
    activation, artifact placement and native acceptance stay owned by the
    lifecycle and final publication pipeline. Strict paths prevent source data
    from turning into arbitrary local or network dependencies.
    """
    catalog_path = root / "provider_catalog.json"
    if not catalog_path.is_file():
        return []
    catalog = load_json(catalog_path)
    if not isinstance(catalog, dict) or catalog.get("sourceOfTruth") is not True:
        raise ValueError("France-only catalog authority is invalid")
    providers = catalog.get("providers")
    if not isinstance(providers, list):
        raise ValueError("France-only catalog providers must be an array")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in providers:
        if not isinstance(record, dict):
            continue
        projection = record.get("projections")
        if not isinstance(projection, dict) or projection.get("vf") is not True or projection.get("general") is not False:
            continue
        row = record.get("scraper")
        if not isinstance(row, dict):
            raise ValueError("France-only catalog row is missing scraper DATA")
        cid = str(row.get("id") or "").strip().casefold()
        filename = str(row.get("filename") or "").strip()
        languages = normalized_declared_languages(row)
        if not re.fullmatch(r"[a-z0-9_-]{2,100}", cid) or cid in seen:
            raise ValueError(f"invalid or duplicate France-only provider: {cid}")
        if not any(lang == "fr" or lang.startswith("fr-") for lang in languages):
            raise ValueError(f"{cid}: France-only provider lacks declared French capability")
        if not re.fullmatch(r"(?:providers|provider-disabled)/[a-zA-Z0-9_.-]+[.]js", filename):
            raise ValueError(f"{cid}: unsafe or unmaterialized executable path")
        seen.add(cid)
        copied = dict(row)
        semantic = semantic_supported_types(copied)
        if "anime" in semantic and "tv" not in semantic:
            copied["canonicalSupportedTypes"] = semantic
            copied["supportedTypes"] = semantic + ["tv"]
        result.append(copied)
    return result


def _public_hostname(hostname: str) -> bool:
    """Reject local/private/special destinations before any homepage request."""
    host = str(hostname or "").strip().rstrip(".").casefold()
    if not host or host == "localhost" or host.endswith(".local"):
        return False
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            if item and len(item) >= 5 and item[4]
        }
    except OSError:
        return False
    if not addresses:
        return False
    for value in addresses:
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            return False
        if not address.is_global:
            return False
    return True


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def fetch_public_homepage(url: str, *, timeout: float = 4.0, limit: int = 196_608) -> str:
    """Fetch a small public HTML homepage without redirects or private-network access."""
    try:
        parsed = urlsplit(url)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    if not _public_hostname(parsed.hostname):
        return ""
    origin = f"{parsed.scheme}://{parsed.hostname}"
    if parsed.port:
        origin += f":{parsed.port}"
    request = urllib.request.Request(
        origin + "/",
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NiakVIO-LanguageProbe/1.0)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        },
        method="GET",
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            content_type = str(response.headers.get("Content-Type", "")).casefold()
            if content_type and "html" not in content_type and "text/" not in content_type:
                return ""
            raw = response.read(limit + 1)
            if len(raw) > limit:
                raw = raw[:limit]
            charset = response.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="ignore")
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, ValueError):
        return ""


def homepage_suggests_french(html: str) -> bool:
    text = str(html or "")
    if not text:
        return False
    if HTML_LANG_FR_RE.search(text):
        return True
    lowered = re.sub(r"\s+", " ", text.casefold())
    cue_count = sum(1 for cue in FRENCH_HOMEPAGE_CUES if cue in lowered)
    if VF_RE.search(lowered) and cue_count >= 1:
        return True
    return cue_count >= 5


def domain_suggests_french(hostname: str) -> bool:
    host = str(hostname or "").strip().rstrip(".").casefold()
    if not host:
        return False
    if host.endswith(".fr"):
        return True
    compact = re.sub(r"[^a-z0-9ç]+", "-", host)
    return any(token in compact for token in FRENCH_HOST_TOKENS)


def provider_homepage_candidates(entry: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    """Extract likely provider origins from its own bundle, excluding common asset/CDN hosts."""
    filename = str(entry.get("filename", ""))
    if not filename or filename.startswith(("http://", "https://", "/", "../")):
        return []
    target = (root / filename).resolve()
    providers_root = (root / "providers").resolve()
    try:
        target.relative_to(providers_root)
    except ValueError:
        return []
    if not target.is_file():
        return []
    try:
        source = target.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    origins: list[str] = []
    seen: set[str] = set()
    for match in URL_RE.findall(source):
        candidate = match.rstrip("),.;]}\\")
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            continue
        host = str(parsed.hostname or "").casefold()
        if not host or any(host == suffix or host.endswith("." + suffix) for suffix in STATIC_HOST_SUFFIXES):
            continue
        origin = f"{parsed.scheme.casefold()}://{host}"
        if parsed.port:
            origin += f":{parsed.port}"
        if origin in seen:
            continue
        seen.add(origin)
        origins.append(origin)
        if len(origins) >= 4:
            break
    return origins


def infer_french_from_domain_or_homepage(
    entry: dict[str, Any],
    *,
    root: Path = ROOT,
    homepage_fetcher: Callable[[str], str] = fetch_public_homepage,
) -> bool:
    """Conservative fallback used only when upstream/runtime language evidence is absent."""
    for origin in provider_homepage_candidates(entry, root=root):
        try:
            host = urlsplit(origin).hostname or ""
        except ValueError:
            continue
        if domain_suggests_french(host):
            return True
        try:
            html = homepage_fetcher(origin)
        except Exception:  # External probe failures must remain inconclusive, never fatal.
            html = ""
        if homepage_suggests_french(html):
            return True
    return False


def build_manifest(
    source: dict[str, Any],
    language_by_id: dict[str, str],
    accepted_groups: set[str],
    name_suffix: str,
    *,
    root: Path = ROOT,
    homepage_fetcher: Callable[[str], str] = fetch_public_homepage,
) -> dict[str, Any]:
    normalized_language_by_id = {
        str(provider_id).casefold(): str(group).casefold()
        for provider_id, group in language_by_id.items()
    }
    entries: list[dict[str, Any]] = []
    for entry in source.get("scrapers", []):
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id", ""))
        declared = normalized_declared_languages(entry)
        declared_fr = any(value.startswith("fr") for value in declared)
        observed_group = normalized_language_by_id.get(provider_id.casefold(), "").strip()
        observed_accepted = observed_group in accepted_groups

        # Domain/homepage evidence is a final metadata fallback only. Explicit
        # declared languages or a concrete observed language group always win.
        no_declared_language = not declared
        no_observed_language = observed_group in {"", "other", "unknown", "unclassified", "none"}
        inferred_fr = False
        if not observed_accepted and not declared_fr and no_declared_language and no_observed_language:
            inferred_fr = infer_french_from_domain_or_homepage(
                entry,
                root=root,
                homepage_fetcher=homepage_fetcher,
            )

        if not observed_accepted and not declared_fr and not inferred_fr:
            continue
        entries.append(nested_entry(entry))

    # The canonical provider catalog owns France-only identities. Rebuilding
    # from Global alone must never erase them or leak them into General.
    general_ids = {
        str(row.get("id") or "").strip().casefold()
        for row in source.get("scrapers", [])
        if isinstance(row, dict)
    }
    for france_row in france_only_catalog_rows(root=root):
        identity = str(france_row["id"]).strip().casefold()
        if identity in general_ids:
            raise ValueError(f"{identity}: France-only provider was duplicated in Global")
        entries.append(nested_entry(france_row))

    return {
        "name": f"{source.get('name', 'NiakVIO')} — {name_suffix}",
        "version": source.get("version"),
        "scrapers": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--report", type=Path, default=ROOT / "health-report.json")
    args = parser.parse_args()

    manifest = load_json(args.manifest.resolve())
    report = load_json(args.report.resolve())
    language_by_id = {
        str(item.get("id", "")).casefold(): str(item.get("manifest_ordering", {}).get("language_group", "other"))
        for item in report.get("providers", [])
        if isinstance(item, dict)
    }

    vf_manifest = build_manifest(manifest, language_by_id, {"vf"}, "VF uniquement")
    general_no_anime = build_no_anime_manifest(manifest)
    vf_no_anime = build_no_anime_manifest(vf_manifest)

    atomic_write_json(ROOT / "vf" / "manifest.json", vf_manifest)
    atomic_write_json(ROOT / "no-anime" / "manifest.json", general_no_anime)
    atomic_write_json(ROOT / "vf-no-anime" / "manifest.json", vf_no_anime)

    print(
        "Generated manifest projections: "
        f"VF={len(vf_manifest['scrapers'])}, "
        f"general_no_anime={len(general_no_anime['scrapers'])}, "
        f"vf_no_anime={len(vf_no_anime['scrapers'])}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
