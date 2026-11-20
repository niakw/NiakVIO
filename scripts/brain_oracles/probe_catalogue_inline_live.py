#!/usr/bin/env python3
"""Bounded, read-only source-contract probe driven by official-TV diagnostic evidence.

Independent HTTP from a CI runner is NOT the official Android TV network.
Only pre-allowlisted provider origins, fixed catalogue/episode paths and a
sanitized source-shape summary are supported. No player, token, stream or
authentication endpoint is requested.
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
MAX_REQUESTS = 12
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
        valid_path = (
            parsed.path == self.prefix
            or parsed.path.startswith(self.prefix + "/")
        )
        if (not valid_path or parsed.query or parsed.fragment
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


def run(root: Path, request: dict, *, fetcher: Callable[[str], tuple[int, str, bool, str, str]] = fetch) -> dict:
    details, hosts = attest(root, request)
    slug, season, voice = details["catalogueSlug"], details["season"], details["voice"]
    # Fixed paths only. Never request a player, signed HLS URL or opaque token resolver.
    templates = (
        ("catalogue", f"/catalogue/{slug}/"),
        ("season_page", f"/catalogue/{slug}/saison{season}/{voice}/"),
        ("legacy_script", f"/catalogue/{slug}/saison{season}/{voice}/episodes.js"),
        ("language_page", f"/catalogue/{slug}/{voice}/"),
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
            observations.append({
                "originHost": host,
                "routeKind": kind,
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
          "official_tv=false proof=false publication=false")


if __name__ == "__main__":
    main()
