#!/usr/bin/env python3
"""Bounded, read-only source-contract probe driven by official-TV diagnostic evidence.

Independent HTTP from a CI runner is NOT the official Android TV network.
Only pre-allowlisted provider origins, fixed catalogue/episode paths and a
sanitized source-shape summary are supported. When an inline token contract is
observed, at most one same-origin resolver request and one bounded resolved-target
shape request per origin may be performed. The opaque token, jeton, resolver
response body, resolved URL and target body are ephemeral and are never persisted
or granted playback/mutation authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from .catalogue_inline_episode_source import classify
except ImportError:
    # importlib.spec_from_file_location (offline tests) does not add this
    # script's sibling directory to sys.path; CLI execution does.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from catalogue_inline_episode_source import classify

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r"[a-z0-9][a-z0-9-]{0,79}")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,125}")
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
HOST = re.compile(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")
MAX_BODY = 524288
MAX_HOSTS = 3
MAX_REQUESTS = 18
TARGET_MAX_BODY = 65536
RESOLVER_CONTRACT = "same-origin-api-lien-j-l-v1"
JETON_VALUE = re.compile(r"""\b(?:var|let|const)\s+epsJeton\s*=\s*["']([A-Za-z0-9_.:-]{1,256})["']""")
LINK_VALUE = re.compile(r"""["']lien:([A-Za-z0-9_.:-]{1,200})["']""")
TIMEOUT = 5


def load(root: Path, name: str) -> dict:
    value = json.loads((root / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected object: " + name)
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def origin_host(value: str) -> str:
    """No userinfo, port, path, query, IP literal, local DNS or HTTP scheme."""
    value = str(value or "").strip().lower()
    if not value or "://" not in value:
        return ""
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return ""
    hostname = parsed.hostname or ""
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or parsed.port is not None or not HOST.fullmatch(hostname)
            or "." not in hostname or hostname.endswith((".local", ".internal"))
            or re.fullmatch(r"[0-9.]+", hostname)):
        return ""
    return hostname


def attest(root: Path, request: dict) -> tuple[dict, list[str]]:
    """Fail closed on stale JS or an untrusted ledger; never authorize mutation."""
    if request.get("schemaVersion") != 1 or request.get("probeKind") != "catalogue-inline-source-contract":
        raise ValueError("unsupported source probe request")
    provider = str(request.get("providerId") or "").lower()
    slug = str(request.get("catalogueSlug") or "").lower()
    voice = str(request.get("voice") or "").lower()
    run = str(request.get("sourceRunId") or "")
    source = str(request.get("sourceNiakvioSha") or "").lower()
    artifact = str(request.get("providerArtifactSha256") or "").lower()
    fixture = str(request.get("fixture") or "")
    season = request.get("season")
    if (not ID.fullmatch(provider) or not SLUG.fullmatch(slug)
            or not ID.fullmatch(voice) or type(season) is not int or not 0 <= season <= 100
            or not re.fullmatch(r"[0-9]{8,20}", run)
            or not SHA40.fullmatch(source) or not SHA64.fullmatch(artifact)
            or not ID.fullmatch(fixture)):
        raise ValueError("malformed source probe identifier")
    if any(request.get(flag) is not False for flag in (
        "proofAuthority", "publicationAuthority",
        "nativePlaybackAuthority", "providerMutationAuthority"
    )):
        raise ValueError("probe cannot carry authority")
    ledger = load(root, "automation/brain-android-tv-emulator-history.json")
    if (ledger.get("schemaVersion") != 1
            or ledger.get("authority") != "official-android-tv-emulator-diagnostic-only"
            or any(ledger.get(flag) is not False for flag in (
                "proofAuthority", "publicationAuthority",
                "nativePlaybackAuthority", "providerMutationAuthority"
            ))):
        raise ValueError("untrusted official-TV evidence ledger")
    candidates = [
        row for row in (ledger.get("rows") or [])[:1400]
        if isinstance(row, dict)
        and row.get("provider") == provider and row.get("fixture") == fixture
        and str(row.get("nativeRunId")) == run
        and row.get("sourceNiakvioSha") == source
        and row.get("providerArtifactSha256") == artifact
        and row.get("appSelected") is True
        and row.get("readerEvidenceComplete") is True
        and row.get("nativeExtractionZeroObserved") is True
        and row.get("manifestScope") in {"manifest.json", "vf/manifest.json"}
        and any(x in {"script_html_2xx", "script_http_missing"}
                for x in row.get("nativeSourceScriptShapePatterns") or [])
        and all(row.get(flag) is False for flag in (
            "proofAuthority", "publicationAuthority",
            "nativePlaybackAuthority", "providerMutationAuthority"
        ))
    ]
    if len(candidates) != 1:
        raise ValueError("exact official source/run/artifact diagnostic not unique")
    scope = str(candidates[0]["manifestScope"])
    manifest = load(root, scope)
    chosen = [x for x in manifest.get("scrapers") or []
              if isinstance(x, dict) and x.get("id") == provider]
    if len(chosen) != 1:
        raise ValueError("provider manifest identity unavailable")
    relative = str(chosen[0].get("filename") or "")
    if not relative.startswith("providers/") or not relative.endswith(".js"):
        raise ValueError("invalid materialized provider location")
    file = (root / relative).resolve()
    file.relative_to(root.resolve())
    if not file.is_file() or sha256(file) != artifact:
        raise ValueError("materialized provider bytes drifted since official TV observation")
    overrides = load(root, "provider-overrides.json")
    patch = (overrides.get("provider_patches") or {}).get(provider)
    if not isinstance(patch, dict):
        raise ValueError("provider override missing")
    options = (patch.get("provider_lego_options") or {})
    urls: list[str] = []
    for value in options.values():
        if isinstance(value, dict):
            urls += [value.get("base"), *(value.get("fallbackBases") or [])]
            langs = value.get("languages") or []
            if isinstance(langs, list) and voice not in langs:
                raise ValueError("voice absent from registered runtime")
    urls += [patch.get("official_site")]
    urls += ["https://" + key for key in (patch.get("domain_substitutions") or {})]
    hubs = load(root, "provider-hubs.json")
    hub = (hubs.get("providers") or {}).get(provider)
    if isinstance(hub, dict):
        urls += [hub.get("direct"), *(hub.get("direct_candidates") or [])]
    hosts: list[str] = []
    for url in urls:
        host = origin_host(str(url or ""))
        if host and host not in hosts:
            hosts.append(host)
        if len(hosts) >= MAX_HOSTS:
            break
    if not hosts:
        raise ValueError("no curated HTTPS source origin")
    return {
        "providerId": provider, "fixture": fixture, "sourceRunId": run,
        "sourceNiakvioSha": source, "providerArtifactSha256": artifact,
        "catalogueSlug": slug, "voice": voice, "season": season,
        "manifestScope": scope
    }, hosts


class _CuratedRedirect(urllib.request.HTTPRedirectHandler):
    """At most two HTTPS hops within predeclared hosts and the same catalogue."""

    max_redirections = 2
    max_repeats = 2

    def __init__(self, approved_hosts: tuple[str, ...], slug: str):
        super().__init__()
        self.approved_hosts = frozenset(approved_hosts)
        self.prefix = "/catalogue/" + slug

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        dest = urllib.parse.urljoin(req.full_url, newurl)
        parsed = urllib.parse.urlsplit(dest)
        original = urllib.parse.urlsplit(req.full_url)
        is_search = original.path.rstrip("/") == "/catalogue"
        valid_path = (
            parsed.path.rstrip("/") == "/catalogue" if is_search
            else parsed.path == self.prefix or parsed.path.startswith(self.prefix + "/")
        )
        valid_query = (
            parsed.query in {"", original.query} if is_search
            else not parsed.query
        )
        if (not valid_path or not valid_query or parsed.fragment
                or origin_host(dest) not in self.approved_hosts):
            return None
        return super().redirect_request(req, fp, code, msg, headers, dest)


def fetch(url: str, *, approved_hosts: tuple[str, ...] = (),
          slug: str = "") -> tuple[int, str, bool, str, str]:
    """Only curated catalogue redirects, no cookies/media/body persistence."""
    request = urllib.request.Request(url, method="GET", headers={
        "User-Agent": "Mozilla/5.0 (compatible; NiakVIO-SourceContract-ReadOnly/1)",
        "Accept": "text/html,application/javascript,text/plain;q=0.8,*/*;q=0.5",
    })
    opener = urllib.request.build_opener(_CuratedRedirect(approved_hosts, slug))
    try:
        response = opener.open(request, timeout=TIMEOUT)
    except urllib.error.HTTPError as error:
        response = error
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return 0, "", False, "transport_error", ""
    try:
        with response:
            status = int(response.status)
            location = response.headers.get("Location", "") if 300 <= status < 400 else ""
            target = origin_host(location) if location else origin_host(response.geturl())
            raw = response.read(MAX_BODY + 1)
            oversized = len(raw) > MAX_BODY
            return status, "" if oversized else raw.decode("utf-8", errors="replace"), oversized, "", target
    except (TimeoutError, OSError, ValueError):
        return 0, "", False, "transport_error", ""


def resolver_material(body: str) -> tuple[str, str] | None:
    """Extract one bounded opaque pair in memory; callers must never persist it."""
    if not isinstance(body, str) or len(body) > MAX_BODY:
        return None
    jeton = JETON_VALUE.search(body)
    link = LINK_VALUE.search(body)
    if not jeton or not link:
        return None
    return jeton.group(1), link.group(1)


def resolver_shape(status: int, body: str, oversized: bool) -> dict[str, Any]:
    """Return only shape booleans; raw resolver data never leaves this function."""
    obj = None
    if not oversized and 200 <= status < 300 and isinstance(body, str) and len(body) <= MAX_BODY:
        try:
            value = json.loads(body)
            obj = value if isinstance(value, dict) else None
        except (json.JSONDecodeError, UnicodeError, TypeError):
            obj = None
    url_value = obj.get("u") if isinstance(obj, dict) else None
    url_observed = isinstance(url_value, str) and bool(url_value.strip())
    https_observed = False
    if url_observed:
        try:
            parsed = urllib.parse.urlsplit(url_value.strip())
            https_observed = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and not parsed.username and not parsed.password
            )
        except ValueError:
            https_observed = False
    return {
        "resolverJsonObjectObserved": isinstance(obj, dict),
        "resolverUrlFieldObserved": url_observed,
        "resolverHttpsUrlObserved": https_observed,
        "resolverContract": RESOLVER_CONTRACT,
    }


def resolver_target_url(status: int, body: str, oversized: bool) -> str:
    """Return one safe HTTPS target ephemerally; callers must never persist it."""
    if oversized or not 200 <= status < 300 or not isinstance(body, str) or len(body) > MAX_BODY:
        return ""
    try:
        value = json.loads(body)
    except (json.JSONDecodeError, UnicodeError, TypeError):
        return ""
    target = str(value.get("u") or "").strip() if isinstance(value, dict) else ""
    if not target or not origin_host(target):
        return ""
    try:
        parsed = urllib.parse.urlsplit(target)
    except ValueError:
        return ""
    return target if parsed.scheme == "https" and not parsed.fragment else ""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a resolved player/media redirect during diagnostic probing."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_resolved_target(url: str, referer: str) -> tuple[int, str, bool, str, str]:
    """Read only a bounded prefix of one ephemeral HTTPS target, with no redirects."""
    if not origin_host(url) or not origin_host(referer):
        return 0, "", False, "unsafe_target", ""
    request = urllib.request.Request(url, method="GET", headers={
        "User-Agent": "Mozilla/5.0 (compatible; NiakVIO-TargetShape-ReadOnly/1)",
        "Accept": "application/vnd.apple.mpegurl,application/dash+xml,text/html,application/json,text/plain;q=0.8,*/*;q=0.5",
        "Referer": referer,
        "Range": f"bytes=0-{TARGET_MAX_BODY - 1}",
    })
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        response = opener.open(request, timeout=TIMEOUT)
    except urllib.error.HTTPError as error:
        response = error
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return 0, "", False, "transport_error", ""
    try:
        with response:
            status = int(response.status)
            content_type = str(response.headers.get("Content-Type", "") or "").split(";", 1)[0].strip().lower()[:80]
            raw = response.read(TARGET_MAX_BODY + 1)
            oversized = len(raw) > TARGET_MAX_BODY
            prefix = raw[:TARGET_MAX_BODY].decode("utf-8", errors="replace")
            return status, prefix, oversized, "", content_type
    except (TimeoutError, OSError, ValueError):
        return 0, "", False, "transport_error", ""


def resolved_target_shape(
    status: int, body: str, oversized: bool, content_type: str,
) -> dict[str, Any]:
    """Classify only terminal response shape; never return body, URL or host."""
    ctype = str(content_type or "").casefold()
    raw = str(body or "")
    stripped = raw.lstrip()
    lowered = stripped.casefold()
    if status == 0:
        shape = "transport_error"
    elif 300 <= status < 400:
        shape = "redirect"
    elif not 200 <= status < 300:
        shape = "http_error"
    elif ctype.startswith(("video/", "audio/")) or ctype in {
        "application/octet-stream", "application/mp4", "video/mp2t",
    }:
        shape = "media_binary"
    elif stripped.startswith("#EXTM3U"):
        shape = "hls_manifest"
    elif "<mpd" in lowered[:4096]:
        shape = "dash_manifest"
    elif lowered.startswith(("<!doctype", "<html")) or "<iframe" in lowered[:16384]:
        player_markers = (
            "<iframe", "<video", "<source", "jwplayer", "videojs",
            "video.js", "playerjs", "plyr", "hls.js",
        )
        shape = "html_player" if any(marker in lowered[:32768] for marker in player_markers) else "html_page"
    elif ctype in {"application/json", "text/json"} or stripped.startswith(("{", "[")):
        shape = "json"
    elif "javascript" in ctype:
        shape = "javascript"
    elif not stripped:
        shape = "empty"
    elif oversized:
        shape = "oversized"
    else:
        shape = "text"
    return {
        "resolvedTargetShape": shape,
        "resolvedTargetDirectMediaObserved": shape in {"hls_manifest", "dash_manifest", "media_binary"},
        "resolvedTargetPlayerEmbedObserved": shape == "html_player",
        "resolvedTargetRedirectObserved": shape == "redirect",
    }


def catalogue_search_matches(body: str, expected: str, origin: str) -> tuple[int, bool, str, int]:
    """Only same-host catalogue slugs: source candidates are never identity proof."""
    if (not isinstance(body, str) or len(body) > MAX_BODY
            or not body.lstrip().lower().startswith(("<!doctype", "<html"))):
        return 0, False, "", 0
    slugs: set[str] = set()
    for match in re.finditer(r"""href\s*=\s*["']([^"']{1,1024})["']""", body, re.I):
        uri = match.group(1).replace("&amp;", "&")
        parsed = urllib.parse.urlsplit(urllib.parse.urljoin("https://" + origin + "/", uri))
        if parsed.scheme != "https" or parsed.hostname != origin:
            continue
        stem = re.match(r"^/catalogue/([a-z0-9][a-z0-9-]{0,125})(?:/|$)", parsed.path, re.I)
        if stem:
            slugs.add(stem.group(1).lower())
        if len(slugs) >= 32:
            break
    wanted = {part for part in expected.split("-") if len(part) > 2}
    ranked = []
    for name in slugs:
        common = wanted & {part for part in name.split("-") if len(part) > 2}
        overlap = round(100 * len(common) / max(1, len(wanted)))
        if overlap >= 50 and len(common) >= min(2, len(wanted)):
            ranked.append((overlap, name))
    ranked.sort(key=lambda row: (-row[0], len(row[1]), row[1]))
    candidate = ranked[0][1] if ranked else ""
    score = ranked[0][0] if ranked else 0
    return min(32, len(slugs)), expected in slugs, candidate, score


def run(
    root: Path,
    request: dict,
    *,
    fetcher: Callable[[str], tuple[int, str, bool, str, str]] = fetch,
    target_fetcher: Callable[[str], tuple[int, str, bool, str, str]] | None = None,
) -> dict:
    details, hosts = attest(root, request)
    slug, season, voice = details["catalogueSlug"], details["season"], details["voice"]
    # Fixed source paths only. Resolver and target probes below are single-use,
    # bounded diagnostics whose opaque material never leaves this process.
    templates = (
        ("catalogue", f"/catalogue/{slug}/"),
        ("season_page", f"/catalogue/{slug}/saison{season}/{voice}/"),
        ("legacy_script", f"/catalogue/{slug}/saison{season}/{voice}/episodes.js"),
        ("catalogue_search", "/catalogue/?search=" + urllib.parse.quote(slug.replace("-", " "), safe="")),
    )
    observations = []
    for host in hosts:
        for kind, path in templates:
            url = "https://" + host + path
            if fetcher is fetch:
                status, body, oversized, error, redirect_host = fetch(
                    url, approved_hosts=tuple(hosts), slug=slug
                )
            else:
                status, body, oversized, error, redirect_host = fetcher(url)
            if type(status) is not int or not 0 <= status <= 599:
                raise ValueError("invalid probe transport status")
            if not isinstance(body, str) or len(body) > MAX_BODY or type(oversized) is not bool:
                raise ValueError("invalid probe transport body")
            if not isinstance(redirect_host, str) or (redirect_host and not HOST.fullmatch(redirect_host)):
                raise ValueError("invalid sanitized redirect host")
            result = classify(status, "" if oversized else body)
            search_count, search_exact, candidate_slug, candidate_score = (
                catalogue_search_matches(
                    "" if oversized or status < 200 or status >= 300 else body,
                    slug,
                    redirect_host if redirect_host in hosts else host,
                ) if kind == "catalogue_search" else (0, False, "", 0)
            )
            observations.append({
                "originHost": host,
                "routeKind": kind,
                "catalogueSearchLinkCount": search_count,
                "catalogueSearchExactSlugPresent": search_exact,
                "catalogueCandidateSlugUnverified": candidate_slug,
                "catalogueCandidateTokenOverlapPercent": candidate_score,
                "responseHost": (redirect_host if not 300 <= status < 400
                                 and redirect_host in hosts else host),
                "httpStatus": status,
                "httpStatusClass": ("3xx" if 300 <= status < 400 else
                                    "transport" if status == 0 else result["httpStatusClass"]),
                "redirectTargetHost": redirect_host if 300 <= status < 400 else "",
                "redirectTargetCurated": redirect_host in hosts if 300 <= status < 400 and redirect_host else False,
                "sourceShape": result["shape"],
                "inlineSlotArrayObserved": result["inlineSlotArrayObserved"],
                "opaqueLinkTokenObserved": result["opaqueLinkTokenObserved"],
                "jetonDeclarationObserved": result["jetonDeclarationObserved"],
                "languageListDeclarationObserved": result["languageListDeclarationObserved"],
                "oversizedResponse": oversized,
                "transportError": error == "transport_error",
            })
            # V2 diagnostic: resolve exactly one opaque id from an attested
            # inline season page. The request is same-origin and ephemeral;
            # only response shape booleans enter the report.
            material = (
                resolver_material(body)
                if kind == "season_page"
                and status == 200 and not oversized
                and result["shape"] == "catalogue_inline_token_episode"
                else None
            )
            if material is not None and len(observations) < MAX_REQUESTS:
                jeton, link_id = material
                resolver_url = (
                    "https://" + host + "/api/lien.php?"
                    + urllib.parse.urlencode({"j": jeton, "l": link_id})
                )
                if fetcher is fetch:
                    r_status, r_body, r_oversized, r_error, r_redirect_host = fetch(
                        resolver_url, approved_hosts=(host,), slug=slug
                    )
                else:
                    r_status, r_body, r_oversized, r_error, r_redirect_host = fetcher(resolver_url)
                if (type(r_status) is not int or not 0 <= r_status <= 599
                        or not isinstance(r_body, str) or len(r_body) > MAX_BODY
                        or type(r_oversized) is not bool
                        or not isinstance(r_redirect_host, str)
                        or (r_redirect_host and not HOST.fullmatch(r_redirect_host))):
                    raise ValueError("invalid resolver probe transport")
                shape = resolver_shape(r_status, r_body, r_oversized)
                observations.append({
                    "originHost": host,
                    "routeKind": "token_resolver",
                    "responseHost": (
                        r_redirect_host
                        if not 300 <= r_status < 400 and r_redirect_host == host else host
                    ),
                    "httpStatus": r_status,
                    "httpStatusClass": (
                        "3xx" if 300 <= r_status < 400 else
                        "transport" if r_status == 0 else
                        "2xx" if 200 <= r_status < 300 else
                        "4xx" if 400 <= r_status < 500 else
                        "5xx" if 500 <= r_status <= 599 else "other"
                    ),
                    "redirectTargetHost": r_redirect_host if 300 <= r_status < 400 else "",
                    "redirectTargetCurated": (
                        r_redirect_host == host if 300 <= r_status < 400 and r_redirect_host else False
                    ),
                    "sourceShape": "unknown_response_shape",
                    "inlineSlotArrayObserved": False,
                    "opaqueLinkTokenObserved": False,
                    "jetonDeclarationObserved": False,
                    "languageListDeclarationObserved": False,
                    "oversizedResponse": r_oversized,
                    "transportError": r_error == "transport_error",
                    **shape,
                })
                target_url = resolver_target_url(r_status, r_body, r_oversized)
                target_probe = target_fetcher
                if target_probe is None and fetcher is fetch:
                    target_probe = lambda value: fetch_resolved_target(
                        value, "https://" + host + "/"
                    )
                if target_url and target_probe is not None and len(observations) < MAX_REQUESTS:
                    t_status, t_body, t_oversized, t_error, t_content_type = target_probe(target_url)
                    if (type(t_status) is not int or not 0 <= t_status <= 599
                            or not isinstance(t_body, str) or len(t_body) > TARGET_MAX_BODY
                            or type(t_oversized) is not bool or not isinstance(t_error, str)
                            or not isinstance(t_content_type, str) or len(t_content_type) > 80):
                        raise ValueError("invalid resolved target probe transport")
                    target_shape = resolved_target_shape(
                        t_status, t_body, t_oversized, t_content_type,
                    )
                    observations.append({
                        "originHost": host,
                        "routeKind": "resolved_target",
                        "responseHost": host,
                        "httpStatus": t_status,
                        "httpStatusClass": (
                            "3xx" if 300 <= t_status < 400 else
                            "transport" if t_status == 0 else
                            "2xx" if 200 <= t_status < 300 else
                            "4xx" if 400 <= t_status < 500 else
                            "5xx" if 500 <= t_status <= 599 else "other"
                        ),
                        "redirectTargetHost": "",
                        "redirectTargetCurated": False,
                        "sourceShape": "unknown_response_shape",
                        "inlineSlotArrayObserved": False,
                        "opaqueLinkTokenObserved": False,
                        "jetonDeclarationObserved": False,
                        "languageListDeclarationObserved": False,
                        "oversizedResponse": t_oversized,
                        "transportError": t_error == "transport_error",
                        "resolvedTargetSameOrigin": origin_host(target_url) == host,
                        **target_shape,
                    })
            if len(observations) >= MAX_REQUESTS:
                break
        if len(observations) >= MAX_REQUESTS:
            break
    return {
        "schemaVersion": 1,
        "authority": "independent-ci-source-shape-diagnostic-only",
        **{key: details[key] for key in (
            "providerId", "fixture", "sourceRunId", "sourceNiakvioSha",
            "providerArtifactSha256", "manifestScope"
        )},
        "independentNetworkNotOfficialClient": True,
        "catalogueIdentityVerified": False,
        "episodeIdentityVerified": False,
        "sourceContractVerifiedOnOfficialTv": False,
        "observations": observations,
        "probeRequestCount": len(observations),
        "inlineTokenResponseCount": sum(x["sourceShape"] == "catalogue_inline_token_episode" for x in observations),
        "tokenResolverProbeCount": sum(x["routeKind"] == "token_resolver" for x in observations),
        "tokenResolverJsonUrlCount": sum(
            x.get("resolverJsonObjectObserved") is True
            and x.get("resolverUrlFieldObserved") is True
            and x.get("resolverHttpsUrlObserved") is True
            for x in observations if x["routeKind"] == "token_resolver"
        ),
        "resolvedTargetProbeCount": sum(
            x["routeKind"] == "resolved_target" for x in observations
        ),
        "resolvedTargetDirectMediaCount": sum(
            x.get("resolvedTargetDirectMediaObserved") is True
            for x in observations if x["routeKind"] == "resolved_target"
        ),
        "resolvedTargetPlayerPageCount": sum(
            x.get("resolvedTargetPlayerEmbedObserved") is True
            for x in observations if x["routeKind"] == "resolved_target"
        ),
        "proofAuthority": False,
        "publicationAuthority": False,
        "nativePlaybackAuthority": False,
        "providerMutationAuthority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    data = json.loads(args.request.read_text(encoding="utf-8"))
    output = run(args.source_root, data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("FIELD_BRAIN_CATALOGUE_SOURCE_PROBE "
          f"provider={output['providerId']} run={output['sourceRunId']} "
          f"requests={output['probeRequestCount']} inline={output['inlineTokenResponseCount']} "
          f"resolver={output['tokenResolverJsonUrlCount']}/{output['tokenResolverProbeCount']} "
          "official_tv=false proof=false publication=false")


if __name__ == "__main__":
    main()
