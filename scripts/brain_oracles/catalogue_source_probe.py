#!/usr/bin/env python3
"""Bounded read-only contract probe; never fetch player, media or token endpoints."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable
from catalogue_inline_episode_source import classify

ROOT = Path(__file__).resolve().parents[2]
IDENT = re.compile(r"[a-z0-9][a-z0-9-]{0,95}\Z")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,125}\Z")
HOST = re.compile(r"(?=.{1,253}\Z)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\Z")
MAX_HOSTS, MAX_REQUESTS, MAX_BODY, TIMEOUT = 3, 12, 524288, 5
FLAGS = ("proofAuthority", "publicationAuthority", "nativePlaybackAuthority", "providerMutationAuthority")

def load(root: Path, filename: str) -> dict:
    value = json.loads((root / filename).read_text("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("invalid JSON object: " + filename)
    return value

def origin(url: str) -> str:
    """Accept public-looking HTTPS DNS origins only from precommitted provider config."""
    try:
        parsed = urllib.parse.urlsplit(str(url or "").strip().lower())
        name, port = parsed.hostname or "", parsed.port
    except (ValueError, TypeError):
        return ""
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or port is not None or not HOST.fullmatch(name) or "." not in name
            or re.fullmatch(r"[0-9.]+", name)
            or name.endswith((".internal", ".local", ".localhost", ".invalid", ".test"))):
        return ""
    return name

def attest(root: Path, req: dict) -> tuple[dict, list[str]]:
    if (not isinstance(req, dict) or req.get("schemaVersion") != 1
            or req.get("probeKind") != "catalogue-inline-source-contract"):
        raise ValueError("unrecognized probe contract")
    provider, fixture = str(req.get("providerId") or ""), str(req.get("fixture") or "")
    slug, voice = str(req.get("catalogueSlug") or ""), str(req.get("voice") or "")
    source, artifact = str(req.get("sourceNiakvioSha") or ""), str(req.get("providerArtifactSha256") or "")
    run, season = str(req.get("sourceRunId") or ""), req.get("season")
    if (not all(IDENT.fullmatch(x) for x in (provider, fixture, voice))
            or not SLUG.fullmatch(slug) or type(season) is not int or not 0 <= season <= 100
            or not re.fullmatch(r"[0-9]{8,20}\Z", run)
            or not re.fullmatch(r"[0-9a-f]{40}\Z", source)
            or not re.fullmatch(r"[0-9a-f]{64}\Z", artifact)
            or any(req.get(flag) is not False for flag in FLAGS)):
        raise ValueError("invalid or untrusted probe identity")
    ledger = load(root, "automation/brain-android-tv-emulator-history.json")
    if (ledger.get("schemaVersion") != 1
            or ledger.get("authority") != "official-android-tv-emulator-diagnostic-only"
            or any(ledger.get(flag) is not False for flag in FLAGS)):
        raise ValueError("untrusted official TV evidence ledger")
    matches = [
        row for row in (ledger.get("rows") or [])[:1400]
        if isinstance(row, dict)
        and row.get("provider") == provider and row.get("fixture") == fixture
        and str(row.get("nativeRunId") or "") == run
        and row.get("sourceNiakvioSha") == source
        and row.get("providerArtifactSha256") == artifact
        and row.get("appSelected") is True
        and row.get("readerEvidenceComplete") is True
        and row.get("nativeExtractionZeroObserved") is True
        and row.get("manifestScope") in {"manifest.json", "vf/manifest.json"}
        and any(x in {"script_http_missing", "script_html_2xx"}
                for x in (row.get("nativeSourceScriptShapePatterns") or [])[:2])
        and all(row.get(flag) is False for flag in FLAGS)
    ]
    if len(matches) != 1:
        raise ValueError("exact source/fixture/run/artifact not attested uniquely")
    scope = str(matches[0]["manifestScope"])
    manifest = load(root, scope)
    chosen = [item for item in (manifest.get("scrapers") or [])
              if isinstance(item, dict) and item.get("id") == provider]
    if len(chosen) != 1:
        raise ValueError("manifest provider mismatch")
    relative = str(chosen[0].get("filename") or "")
    if not relative.startswith("providers/") or not relative.endswith(".js"):
        raise ValueError("unsafe provider filename")
    file = (root / relative).resolve()
    file.relative_to(root.resolve())
    if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != artifact:
        raise ValueError("provider bytes drifted since official TV run")
    patch = (load(root, "provider-overrides.json").get("provider_patches") or {}).get(provider)
    if not isinstance(patch, dict):
        raise ValueError("registered provider override absent")
    urls: list[str] = []
    for opt in (patch.get("provider_lego_options") or {}).values():
        if not isinstance(opt, dict):
            continue
        if voice not in (opt.get("languages") or []):
            raise ValueError("voice absent from provider configuration")
        urls += [opt.get("base"), *(opt.get("fallbackBases") or [])]
    urls.append(patch.get("official_site"))
    hub = (load(root, "provider-hubs.json").get("providers") or {}).get(provider)
    if isinstance(hub, dict):
        urls += [hub.get("direct"), *(hub.get("direct_candidates") or [])]
    hosts: list[str] = []
    for value in urls:
        host = origin(value)
        if host and host not in hosts:
            hosts.append(host)
        if len(hosts) >= MAX_HOSTS:
            break
    if not hosts:
        raise ValueError("no curated HTTPS origin")
    return {"providerId": provider, "fixture": fixture, "sourceRunId": run,
            "sourceNiakvioSha": source, "providerArtifactSha256": artifact,
            "manifestScope": scope, "catalogueSlug": slug,
            "voice": voice, "season": season}, hosts

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

def redirect_target(current_url: str, location: str, registered: list[str]) -> dict:
    """Read-only Location classification: never request or store full target URL."""
    if not location:
        return {"redirectHostScope": "location_missing", "redirectTargetHost": "",
                "redirectPathScope": "unknown", "redirectPathChangeKind": "unknown",
                "redirectCandidateCatalogueSlug": "", "redirectQueryPresent": False}
    if not isinstance(location, str) or len(location) > 2048:
        return {"redirectHostScope": "unsafe_or_oversized", "redirectTargetHost": "",
                "redirectPathScope": "unknown", "redirectPathChangeKind": "unknown",
                "redirectCandidateCatalogueSlug": "", "redirectQueryPresent": False}
    try:
        target = urllib.parse.urljoin(current_url, location)
        parsed = urllib.parse.urlsplit(target)
        current = urllib.parse.urlsplit(current_url)
        host = origin(target)
        if not host:
            raise ValueError("unsafe redirect")
    except (ValueError, TypeError):
        return {"redirectHostScope": "unsafe_or_oversized", "redirectTargetHost": "",
                "redirectPathScope": "unknown", "redirectPathChangeKind": "unknown",
                "redirectCandidateCatalogueSlug": "", "redirectQueryPresent": False}
    scope = ("same_origin" if host == current.hostname
             else "registered_fallback" if host in registered
             else "unregistered_candidate")
    route = ("same_path" if parsed.path == current.path
             else "catalogue_route" if parsed.path.startswith("/catalogue/")
             else "root" if parsed.path in {"", "/"} else "other_path")
    target_parts = parsed.path.strip("/").split("/")
    original_parts = current.path.strip("/").split("/")
    target_slug = (target_parts[1] if len(target_parts) >= 2
                   and target_parts[0] == "catalogue"
                   and SLUG.fullmatch(target_parts[1]) else "")
    previous_slug = (original_parts[1] if len(original_parts) >= 2
                     and original_parts[0] == "catalogue" else "")
    path_change = (
        "exact_path" if parsed.path == current.path
        else "trailing_slash_only" if parsed.path.rstrip("/") == current.path.rstrip("/")
        else "catalogue_slug_changed" if target_slug and target_slug != previous_slug
        else "same_catalogue_other_path" if target_slug and target_slug == previous_slug
        else "root" if parsed.path in {"", "/"} else "other_path"
    )
    return {"redirectHostScope": scope, "redirectTargetHost": host,
            "redirectPathScope": route, "redirectPathChangeKind": path_change,
            "redirectCandidateCatalogueSlug": (
                target_slug if path_change == "catalogue_slug_changed" else ""
            ),
            "redirectQueryPresent": bool(parsed.query)}


def fetch(url: str) -> tuple[int, str, bool, bool, str]:
    """One GET; no redirects, cookies, browser or secondary requests."""
    req = urllib.request.Request(url, method="GET", headers={
        "User-Agent": "Mozilla/5.0 (compatible; NiakVIO-SourceShape/1.0)",
        "Accept": "text/html,application/javascript,text/plain;q=0.8,*/*;q=0.5",
    })
    try:
        response = urllib.request.build_opener(NoRedirect()).open(req, timeout=TIMEOUT)
    except urllib.error.HTTPError as error:
        response = error
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return 0, "", False, True, ""
    try:
        with response:
            raw = response.read(MAX_BODY + 1)
            oversized = len(raw) > MAX_BODY
            location = str(response.headers.get("Location") or "")
            return (int(response.status), "" if oversized
                    else raw.decode("utf-8", errors="replace"), oversized, False,
                    location[:2049])
    except (TimeoutError, OSError, ValueError):
        return 0, "", False, True, ""

def run(root: Path, request: dict, fetcher: Callable[[str], tuple[int, str, bool, bool, str]] = fetch) -> dict:
    info, hosts = attest(root, request)
    slug, season, voice = info["catalogueSlug"], info["season"], info["voice"]
    # No redirects, dynamic navigation, token-resolution API, or player/media URL.
    routes = (("catalogue", f"/catalogue/{slug}/"),
              ("season_page", f"/catalogue/{slug}/saison{season}/{voice}/"),
              ("legacy_script", f"/catalogue/{slug}/saison{season}/{voice}/episodes.js"),
              ("language_page", f"/catalogue/{slug}/{voice}/"))
    rows = []
    for host in hosts:
        for kind, path in routes:
            request_url = "https://" + host + path
            status, body, oversized, transport_error, location = fetcher(request_url)
            if (type(status) is not int or not 0 <= status <= 599
                    or not isinstance(body, str) or len(body) > MAX_BODY
                    or type(oversized) is not bool or type(transport_error) is not bool):
                raise ValueError("invalid transport adapter result")
            shape = classify(status, "" if oversized else body)
            redirect = redirect_target(request_url, location, hosts) if 300 <= status < 400 else {
                "redirectHostScope": "not_redirect", "redirectTargetHost": "",
                "redirectPathScope": "unknown", "redirectPathChangeKind": "unknown",
                "redirectCandidateCatalogueSlug": "", "redirectQueryPresent": False,
            }
            rows.append({
                "originHost": host, "routeKind": kind,
                "httpStatus": status,
                "httpStatusClass": "3xx" if 300 <= status < 400 else shape["httpStatusClass"],
                "redirectObserved": 300 <= status < 400,
                "sourceShape": shape["shape"],
                "inlineSlotArrayObserved": shape["inlineSlotArrayObserved"],
                "opaqueLinkTokenObserved": shape["opaqueLinkTokenObserved"],
                "jetonDeclarationObserved": shape["jetonDeclarationObserved"],
                "languageListDeclarationObserved": shape["languageListDeclarationObserved"],
                "responseTooLarge": oversized, "transportError": transport_error,
                **redirect,
            })
            if len(rows) >= MAX_REQUESTS:
                break
        if len(rows) >= MAX_REQUESTS:
            break
    return {"schemaVersion": 1,
            "authority": "independent-ci-source-shape-diagnostic-only",
            **{x: info[x] for x in ("providerId", "fixture", "sourceRunId",
                                   "sourceNiakvioSha", "providerArtifactSha256", "manifestScope")},
            "probeRequestCount": len(rows),
            "inlineTokenResponseCount": sum(x["sourceShape"] == "catalogue_inline_token_episode" for x in rows),
            "independentNetworkNotOfficialClient": True,
            "catalogueIdentityVerified": False, "episodeIdentityVerified": False,
            "sourceContractVerifiedOnOfficialTv": False, "observations": rows,
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerMutationAuthority": False}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    report = run(args.source_root, json.loads(args.request.read_text("utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FIELD_BRAIN_CATALOGUE_PROBE provider={report['providerId']} "
          f"run={report['sourceRunId']} requests={report['probeRequestCount']} "
          f"inline={report['inlineTokenResponseCount']} official_tv=false publication=false")

if __name__ == "__main__":
    main()
