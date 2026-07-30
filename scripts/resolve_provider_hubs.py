#!/usr/bin/env python3
"""Resolve official address hubs and persist only runtime-validated migrations.

A hub such as purstream.wiki is not treated as the provider itself. The script
extracts the official site, inspects that site's HTML/JavaScript for an API
origin, probes configured runtime routes, and only then writes durable host
replacements. Failed or incomplete discovery is report-only.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "provider-overrides.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def fetch(url: str, timeout: float = 10.0) -> tuple[int, str, str, dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"})
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read(2_000_000)
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, response.geturl(), raw.decode(charset, errors="replace"), dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body = exc.read(300_000).decode("utf-8", errors="replace")
        return exc.code, exc.geturl(), body, dict(exc.headers.items())


def host(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


def same_brand(provider_id: str, candidate: str) -> bool:
    compact = re.sub(r"[^a-z0-9]", "", host(candidate).split(".")[0])
    brand = re.sub(r"[^a-z0-9]", "", provider_id.lower())
    return bool(brand and (brand in compact or compact in brand))


def links(document: str, base: str) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    pattern = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>([\s\S]*?)</a>", re.I)
    for href, label in pattern.findall(document):
        text = re.sub(r"<[^>]+>", " ", html.unescape(label))
        text = re.sub(r"\s+", " ", text).strip()
        url = urllib.parse.urljoin(base, html.unescape(href))
        if url.startswith(("http://", "https://")):
            output.append((url, text))
    # visible bare URLs are common on official-address dashboards
    for url in re.findall(r"https?://[a-z0-9.-]+(?:/[A-Za-z0-9_./?=&%+#-]*)?", document, re.I):
        output.append((html.unescape(url), "visible_url"))
    return output


def choose_official(provider_id: str, hub_url: str, document: str, labels: list[str]) -> tuple[str | None, list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    hub_host = host(hub_url)
    for url, label in links(document, hub_url):
        if host(url) == hub_host or not same_brand(provider_id, url):
            continue
        score = 50
        normalized = label.casefold()
        if any(token.casefold() in normalized for token in labels):
            score += 40
        if "official" in normalized or "officielle" in normalized or "vérifi" in normalized or "verifi" in normalized:
            score += 10
        candidates.append({"url": url.rstrip("/"), "label": label, "score": min(score, 100)})
    candidates.sort(key=lambda item: (-item["score"], item["url"]))
    return (candidates[0]["url"] if candidates and candidates[0]["score"] >= 80 else None), candidates


def extract_api_candidates(site_url: str, document: str, provider_id: str, templates: list[str]) -> list[str]:
    found: set[str] = set()
    for value in re.findall(r"https?://[a-z0-9.-]+(?::\d+)?(?:/[A-Za-z0-9_./?=&%+#{}:-]*)?", document, re.I):
        if "api" in host(value) and same_brand(provider_id, value):
            found.add(value.rstrip("/"))
    site_host = host(site_url)
    tld = ".".join(site_host.split(".")[1:]) if "." in site_host else ""
    for template in templates:
        found.add(template.format(site=site_url.rstrip("/"), host=site_host, tld=tld).rstrip("/"))
    return sorted(found)


def probe(base: str, routes: list[str], success_statuses: set[int], timeout: float) -> dict[str, Any]:
    observations = []
    for route in routes or ["/"]:
        url = urllib.parse.urljoin(base.rstrip("/") + "/", route.lstrip("/"))
        try:
            status, final, body, headers = fetch(url, timeout)
            ok = status in success_statuses
            observations.append({"url": url, "final_url": final, "status": status, "ok": ok, "content_type": headers.get("Content-Type", "")})
            if ok:
                return {"ok": True, "base": base, "observation": observations[-1], "observations": observations}
        except Exception as exc:
            observations.append({"url": url, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return {"ok": False, "base": base, "observations": observations}


def update_provider_patch(config: dict[str, Any], provider_id: str, hub_cfg: dict[str, Any], site_url: str, api_url: str | None) -> list[dict[str, str]]:
    patches = config.setdefault("provider_patches", {})
    patch = patches.setdefault(provider_id, {})
    replacements = patch.setdefault("replacements", {})
    runtime = patch.setdefault("runtime_domain_replacements", {})
    changes: list[dict[str, str]] = []
    new_site_host = host(site_url)
    for old in hub_cfg.get("old_site_hosts") or []:
        if old != new_site_host:
            replacements[old] = new_site_host
            runtime[old] = new_site_host
            changes.append({"from": old, "to": new_site_host, "kind": "site"})
    if api_url:
        new_api_host = host(api_url)
        for old in hub_cfg.get("old_api_hosts") or []:
            if old != new_api_host:
                replacements[old] = new_api_host
                runtime[old] = new_api_host
                changes.append({"from": old, "to": new_api_host, "kind": "api"})
    patch["capability"] = "official_domain_hub"
    patch["official_hub"] = hub_cfg.get("hub")
    patch["official_site"] = site_url
    if api_url:
        patch["official_api"] = api_url
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="health-output/provider-hub-report.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    hubs = config.get("official_domain_hubs") or {}
    report: dict[str, Any] = {"schema_version": 1, "providers": {}, "applied": 0}
    changed = False
    for provider_id, hub_cfg in sorted(hubs.items()):
        item: dict[str, Any] = {"provider_id": provider_id, "hub": hub_cfg.get("hub"), "status": "inconclusive"}
        try:
            status, final_hub, document, _headers = fetch(str(hub_cfg["hub"]), args.timeout)
            item["hub_status"] = status
            item["hub_final_url"] = final_hub
            if status < 200 or status >= 400:
                item["reason"] = "hub_http_failure"
                report["providers"][provider_id] = item
                continue
            site, candidates = choose_official(provider_id, final_hub, document, list(hub_cfg.get("official_link_labels") or []))
            item["site_candidates"] = candidates
            if not site:
                item["reason"] = "no_high_confidence_official_site"
                report["providers"][provider_id] = item
                continue
            item["official_site"] = site
            site_status, final_site, site_document, _ = fetch(site, args.timeout)
            item["site_status"] = site_status
            item["site_final_url"] = final_site
            if site_status < 200 or site_status >= 400:
                item["reason"] = "official_site_http_failure"
                report["providers"][provider_id] = item
                continue
            api_candidates = extract_api_candidates(final_site, site_document, provider_id, list(hub_cfg.get("api_templates") or []))
            item["api_candidates"] = api_candidates
            validated_api = None
            api_probes = []
            for candidate in api_candidates:
                result = probe(candidate, list(hub_cfg.get("api_probe_routes") or []), set(hub_cfg.get("api_success_statuses") or [200, 400, 401, 403, 404, 405]), args.timeout)
                api_probes.append(result)
                if result["ok"]:
                    validated_api = candidate
                    break
            item["api_probes"] = api_probes
            require_api = bool(hub_cfg.get("require_api_validation", True))
            if require_api and not validated_api:
                item["reason"] = "api_not_runtime_validated"
                report["providers"][provider_id] = item
                continue
            item["validated_api"] = validated_api
            item["status"] = "validated"
            item["reason"] = "official_site_and_runtime_endpoint_validated"
            if args.apply:
                changes = update_provider_patch(config, provider_id, hub_cfg, final_site.rstrip("/"), validated_api)
                item["applied_changes"] = changes
                if changes:
                    report["applied"] += len(changes)
                    changed = True
        except Exception as exc:
            item["reason"] = "exception"
            item["error"] = f"{type(exc).__name__}: {exc}"
        report["providers"][provider_id] = item

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if changed:
        CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"provider hub resolution complete: validated={sum(1 for x in report['providers'].values() if x.get('status') == 'validated')} applied={report['applied']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
