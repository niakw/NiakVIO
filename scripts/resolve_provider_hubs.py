#!/usr/bin/env python3
"""Resolve provider address sources into validated terminal routes.

The registry supports several complementary discovery methods:
- official address hubs and wikis;
- public Telegram address channels;
- redirector pages;
- curated direct candidates;
- bounded public search-engine fallback (deep mode only);
- persistent last-known-good domain history.

A hub, search result page or Telegram page is never persisted as the provider
itself. Every terminal candidate is validated first. Search-only discoveries
require confirmation on two consecutive runs before they may replace a known
route. When discovery is inconclusive, the current last-known-good route is
retained rather than being overwritten.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import ipaddress
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "provider-overrides.json"
HUBS_PATH = ROOT / "provider-hubs.json"
HISTORY_PATH = ROOT / "provider-domain-history.json"
UA = "NuvioProviderDomainResolver/5.20 (+https://github.com/niakw/niakw-nuvio-providers-group-1-0)"
SOCIAL_HOST_SUFFIXES = (
    "telegram.org", "t.me", "discord.gg", "discord.com", "facebook.com",
    "x.com", "twitter.com", "youtube.com", "youtu.be", "instagram.com",
)
SEARCH_HOST_SUFFIXES = (
    "yandex.com", "yandex.fr", "yandex.ru", "duckduckgo.com", "google.com",
    "bing.com", "search.yahoo.com",
)
INFRASTRUCTURE_HOST_SUFFIXES = (
    "cloudflare.com", "github.com", "githubusercontent.com", "jsdelivr.net",
    "gstatic.com", "googleapis.com", "cdnjs.com", "unpkg.com",
)
PARKING_MARKERS = (
    "domain is for sale", "buy this domain", "domain parked", "sedo domain parking",
    "this domain may be for sale", "website is under construction",
)
HUB_MARKERS = (
    "liste des adresses", "address hub", "hub d’accès", "hub d'acces",
    "nouvelle adresse officielle", "adresse officielle active", "domaines historiques",
)
SEARCH_CHALLENGE_MARKERS = (
    "captcha", "verify you are human", "unusual traffic", "robot check",
    "smart captcha", "are you not a robot",
)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_json(path: Path, payload: Any) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def host(url: str) -> str:
    return (urllib.parse.urlparse(str(url)).hostname or "").lower().strip(".")


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def canonical_provider_id(value: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", str(value).casefold()).strip(".-").replace("_", "-")


def is_http_url(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower().startswith(("http://", "https://"))


def is_public_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.strip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return True
    return not (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast)


def fetch(url: str, timeout: float = 10.0) -> tuple[int, str, str, dict[str, str]]:
    if not is_public_url(url):
        raise ValueError(f"unsafe or unsupported URL: {url}")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*;q=0.6",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.7,en;q=0.6",
            "Cache-Control": "no-cache",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read(2_000_000)
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, response.geturl(), raw.decode(charset, errors="replace"), dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body = exc.read(300_000).decode("utf-8", errors="replace")
        return exc.code, exc.geturl(), body, dict(exc.headers.items())


def aliases_for(provider_id: str, cfg: dict[str, Any]) -> list[str]:
    values = [provider_id, *(cfg.get("aliases") or []), *(cfg.get("terminal_aliases") or [])]
    return sorted({compact(value) for value in values if compact(value)})


def exact_allowed_hosts(cfg: dict[str, Any]) -> set[str]:
    values: list[str] = []
    values.extend(str(item) for item in cfg.get("allowed_terminal_hosts") or [])
    values.extend(str(item) for item in cfg.get("known_hosts") or [])
    for url in cfg.get("direct_candidates") or []:
        values.append(host(str(url)))
    fallback = cfg.get("direct_fallback")
    if fallback:
        values.append(host(str(fallback)))
    return {item.lower().strip(".") for item in values if item}


def allowed_by_host_pattern(hostname: str, cfg: dict[str, Any]) -> bool:
    for raw_pattern in cfg.get("allowed_terminal_host_patterns") or []:
        pattern = str(raw_pattern).strip()
        if not pattern or len(pattern) > 240:
            continue
        try:
            if re.fullmatch(pattern, hostname, re.I):
                return True
        except re.error:
            continue
    return False


def same_brand(provider_id: str, candidate: str, cfg: dict[str, Any]) -> bool:
    hostname = host(candidate)
    if not hostname:
        return False
    if hostname in exact_allowed_hosts(cfg) or allowed_by_host_pattern(hostname, cfg):
        return True
    labels = [compact(part) for part in hostname.split(".") if part]
    aliases = aliases_for(provider_id, cfg)
    return any(alias in label or label in alias for alias in aliases for label in labels if len(label) >= 3)


def _decode_search_redirect(url: str) -> str:
    parsed = urllib.parse.urlparse(html.unescape(url))
    query = urllib.parse.parse_qs(parsed.query)
    for key in ("uddg", "url", "u", "target", "r"):
        value = query.get(key, [None])[0]
        if value and str(value).startswith(("http://", "https://")):
            return urllib.parse.unquote(str(value))
    return url




class _TelegramPublicParser(HTMLParser):
    """Collect links together with the numeric Telegram post containing them.

    Public Telegram pages expose stable ``data-post=channel/message_id`` values.
    Using the message id is safer than assuming that raw document order always
    corresponds to publication order (pinned posts and partial pages can alter it).
    """

    def __init__(self, base: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self._context_stack: list[tuple[str, int | None]] = []
        self._current_message_id: int | None = None
        self._anchor: dict[str, Any] | None = None
        self._message_text: dict[int, list[str]] = {}
        self.rows: list[dict[str, Any]] = []
        self._index = 0

    @staticmethod
    def _post_id(attrs: dict[str, str | None]) -> int | None:
        value = str(attrs.get("data-post") or "")
        match = re.search(r"/(\d+)(?:$|[?#])", value)
        return int(match.group(1)) if match else None

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        previous = self._current_message_id
        message_id = self._post_id(attrs) or previous
        if tag.casefold() not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self._context_stack.append((tag.casefold(), previous))
        self._current_message_id = message_id
        if tag.casefold() == "a" and attrs.get("href"):
            self._anchor = {
                "url": urllib.parse.urljoin(self.base, html.unescape(str(attrs["href"]))),
                "label_parts": [],
                "message_id": message_id,
                "document_index": self._index,
            }
            self._index += 1

    def handle_startendtag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        # Self-closing tags do not alter the inherited message context.
        if tag.casefold() == "a":
            self.handle_starttag(tag, attrs_list)
            self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self._current_message_id is not None:
            self._message_text.setdefault(self._current_message_id, []).append(text)
        if self._anchor is not None:
            self._anchor["label_parts"].append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "a" and self._anchor is not None:
            url = _decode_search_redirect(str(self._anchor["url"]))
            if url.startswith(("http://", "https://")):
                self.rows.append({
                    "url": url,
                    "label": " ".join(self._anchor["label_parts"]).strip(),
                    "message_id": self._anchor["message_id"],
                    "document_index": self._anchor["document_index"],
                })
            self._anchor = None
        lowered = tag.casefold()
        while self._context_stack:
            opened, previous = self._context_stack.pop()
            if opened == lowered:
                self._current_message_id = previous
                break

    def finalized_rows(self) -> list[dict[str, Any]]:
        for row in self.rows:
            message_id = row.get("message_id")
            row["context"] = " ".join(self._message_text.get(message_id, []))[:4000] if message_id is not None else ""
        return self.rows


def telegram_links(document: str, base: str) -> list[dict[str, Any]]:
    parser = _TelegramPublicParser(base)
    try:
        parser.feed(document)
        parser.close()
    except Exception:
        # Public Telegram HTML occasionally contains malformed fragments. The
        # generic link parser remains available as a conservative fallback.
        return []
    seen: set[tuple[str, int | None]] = set()
    output: list[dict[str, Any]] = []
    for row in parser.finalized_rows():
        normalized = str(row.get("url") or "").rstrip("/")
        key = (normalized, row.get("message_id"))
        if not normalized or key in seen:
            continue
        seen.add(key)
        row["url"] = normalized
        output.append(row)
    return output


def links(document: str, base: str) -> list[tuple[str, str, int]]:
    output: list[tuple[str, str, int]] = []
    pattern = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>([\s\S]*?)</a>", re.I)
    for index, (href, label) in enumerate(pattern.findall(document)):
        text = re.sub(r"<[^>]+>", " ", html.unescape(label))
        text = re.sub(r"\s+", " ", text).strip()
        url = urllib.parse.urljoin(base, html.unescape(href))
        url = _decode_search_redirect(url)
        if url.startswith(("http://", "https://")):
            output.append((url, text, index))
    decoded = html.unescape(document).replace("\\/", "/")
    dynamic_patterns = [
        r"https?://[a-z0-9.-]+(?:/[A-Za-z0-9_./?=&%+#~:@-]*)?",
        r"(?:href|url|officialUrl|official_url|currentUrl|current_url|target|destination)\s*[:=]\s*[\"'](https?://[^\"']+)",
        r"(?:window\.)?location(?:\.href)?\s*=\s*[\"'](https?://[^\"']+)",
        r"content=[\"'][^\"']*url=(https?://[^\"'; ]+)",
    ]
    offset = len(output)
    for pattern_value in dynamic_patterns:
        for match in re.findall(pattern_value, decoded, re.I):
            url = match if isinstance(match, str) else match[0]
            url = _decode_search_redirect(url.rstrip("\\"))
            output.append((url, "dynamic terminal URL", offset))
            offset += 1
    seen: set[str] = set()
    unique: list[tuple[str, str, int]] = []
    for url, label, index in output:
        normalized = url.rstrip("/")
        if normalized not in seen:
            seen.add(normalized)
            unique.append((url, label, index))
    return unique


def _default_source_type(url: str, resolver: str) -> str:
    hostname = host(url)
    if hostname.endswith(("t.me", "telegram.me")) or resolver == "latest_telegram_domain":
        return "telegram_public"
    if resolver == "redirect":
        return "redirect"
    return "hub"


def _search_query_from_legacy(value: str) -> str | None:
    text = str(value).strip()
    if not text or is_http_url(text):
        return None
    match = re.search(r"(?:terme suivant[^:]*:|recherche[^:]*:)\s*(.+)$", text, re.I)
    return (match.group(1) if match else text).strip().strip('"')


def merge_hub_registry(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    merged = {
        canonical_provider_id(key): dict(value)
        for key, value in (config.get("official_domain_hubs") or {}).items()
        if isinstance(value, dict)
    }
    registry = load_json(HUBS_PATH, {"providers": {}})
    providers = registry.get("providers") or {}
    if isinstance(providers, list):
        providers = {str(row.get("id")): row for row in providers if isinstance(row, dict) and row.get("id")}
    if not isinstance(providers, dict):
        raise ValueError("provider-hubs.json providers must be an object or array")

    for raw_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        provider_id = canonical_provider_id(raw_id)
        target = merged.setdefault(provider_id, {})
        target.setdefault("aliases", row.get("aliases") or [provider_id])
        target.setdefault("terminal_aliases", row.get("terminal_aliases") or [])
        target.setdefault("resolver", row.get("resolver") or "official_outbound")
        target.setdefault("official_link_labels", row.get("official_link_labels") or [
            "Accéder", "Accedez", "site officiel", "adresse officielle", "ouvrir",
            "website", "click here", "go to homepage", "watch now", "visit now",
        ])
        target.setdefault("require_api_validation", bool(row.get("require_api_validation", False)))
        target.setdefault("persist_official_site_without_api", True)
        target.setdefault("manifest_status", row.get("manifest_status"))
        target.setdefault("blocked_hosts", row.get("blocked_hosts") or [])
        target.setdefault("allowed_terminal_host_patterns", row.get("allowed_terminal_host_patterns") or [])
        target.setdefault("terminal_markers", row.get("terminal_markers") or [])
        target.setdefault("search_confirmation_runs", int(row.get("search_confirmation_runs") or 2))

        sources = [dict(item) for item in (target.get("sources") or []) if isinstance(item, dict)]
        for item in row.get("sources") or []:
            if isinstance(item, dict):
                sources.append(dict(item))

        hub_value = row.get("hub")
        if is_http_url(hub_value):
            target.setdefault("hub", str(hub_value).strip())
            sources.append({
                "type": _default_source_type(str(hub_value), str(row.get("resolver") or target.get("resolver"))),
                "url": str(hub_value).strip(),
                "priority": 100,
            })
        else:
            query = _search_query_from_legacy(str(hub_value or ""))
            if query:
                target.setdefault("search_queries", []).append(query)

        for query in row.get("search_queries") or []:
            if str(query).strip():
                target.setdefault("search_queries", []).append(str(query).strip())
        for query in target.get("search_queries") or []:
            sources.append({"type": "search", "query": query, "priority": 35})

        direct_values: list[str] = []
        direct = row.get("direct")
        if is_http_url(direct):
            direct_values.append(str(direct).strip())
        direct_values.extend(str(item).strip() for item in row.get("direct_candidates") or [] if is_http_url(item))
        direct_values.extend(str(item).strip() for item in target.get("direct_candidates") or [] if is_http_url(item))
        direct_values = list(dict.fromkeys(direct_values))
        if direct_values:
            target["direct_candidates"] = direct_values
            target.setdefault("direct_fallback", direct_values[0])

        allowed = set(str(item) for item in target.get("allowed_terminal_hosts") or [] if item)
        allowed.update(str(item) for item in row.get("allowed_terminal_hosts") or [] if item)
        allowed.update(host(url) for url in direct_values if host(url))
        target["allowed_terminal_hosts"] = sorted(allowed)

        dedup_sources: list[dict[str, Any]] = []
        seen_sources: set[tuple[str, str]] = set()
        for source in sources:
            source_type = str(source.get("type") or "hub")
            identity = str(source.get("url") or source.get("query") or "").strip()
            if not identity:
                continue
            key = (source_type, identity)
            if key in seen_sources:
                continue
            seen_sources.add(key)
            source.setdefault("priority", 50)
            dedup_sources.append(source)
        target["sources"] = sorted(dedup_sources, key=lambda item: -int(item.get("priority") or 0))

    # Keep explicit config values authoritative when the registry has no value.
    for provider_id, target in merged.items():
        direct = target.get("direct_fallback")
        candidates = [str(item) for item in target.get("direct_candidates") or [] if is_http_url(item)]
        if is_http_url(direct) and str(direct) not in candidates:
            candidates.insert(0, str(direct))
        target["direct_candidates"] = list(dict.fromkeys(candidates))
        allowed = set(target.get("allowed_terminal_hosts") or [])
        allowed.update(host(url) for url in target["direct_candidates"] if host(url))
        target["allowed_terminal_hosts"] = sorted(allowed)
        target.setdefault("sources", [])
    return merged


def candidate_score(provider_id: str, cfg: dict[str, Any], url: str, label: str, index: int, total: int) -> int:
    candidate_host = host(url)
    if not candidate_host or not is_public_url(url):
        return -1
    hub_hosts = {host(str(source.get("url"))) for source in cfg.get("sources") or [] if source.get("type") in {"hub", "telegram_public"}}
    if candidate_host in hub_hosts:
        return -1
    if candidate_host.endswith(SOCIAL_HOST_SUFFIXES + SEARCH_HOST_SUFFIXES + INFRASTRUCTURE_HOST_SUFFIXES):
        return -1
    if candidate_host in {str(item).lower() for item in cfg.get("blocked_hosts") or []}:
        return -1
    normalized = compact(label)
    labels = [compact(str(value)) for value in (cfg.get("official_link_labels") or [])]
    resolver = str(cfg.get("resolver") or "official_outbound")
    brand = same_brand(provider_id, url, cfg)
    label_match = any(token and token in normalized for token in labels)
    if not brand and not label_match:
        return -1
    score = 55 if brand else 25
    if label_match:
        score += 30
    if any(token in normalized for token in ("official", "officiel", "actuel", "verifie", "verified", "principal")):
        score += 10
    if resolver == "service_catalogue" and any(token in normalized for token in ("catalogue", "streaming", "service")):
        score += 20
    if resolver == "latest_telegram_domain":
        score += int(20 * ((index + 1) / max(total, 1)))
    if resolver == "alias_outbound" and brand:
        score += 10
    return min(score, 100)


def _telegram_context_score(provider_id: str, cfg: dict[str, Any], label: str, context: str) -> int:
    combined = compact(f"{label} {context}")
    aliases = aliases_for(provider_id, cfg)
    mentions_brand = any(alias and alias in combined for alias in aliases)
    announcement = any(token in combined for token in (
        "nouveaulien", "nouvelleadresse", "adresseofficielle", "siteofficiel",
        "urlnouveausite", "changementdadresse", "acceder", "regarder",
    ))
    if mentions_brand and announcement:
        return 25
    if mentions_brand:
        return 10
    return 0


def choose_official(provider_id: str, cfg: dict[str, Any], hub_url: str, document: str) -> tuple[list[dict[str, Any]], str | None]:
    resolver = str(cfg.get("resolver") or "official_outbound")
    candidates: list[dict[str, Any]] = []
    if resolver == "latest_telegram_domain":
        extracted_rows = telegram_links(document, hub_url)
        if extracted_rows:
            for row in extracted_rows:
                url = str(row["url"])
                label = str(row.get("label") or "")
                context = str(row.get("context") or "")
                index = int(row.get("document_index") or 0)
                score = candidate_score(provider_id, cfg, url, label, index, max(len(extracted_rows), 1))
                context_bonus = _telegram_context_score(provider_id, cfg, label, context)
                # A Telegram announcement can introduce a new official hostname
                # before it is present in the curated allow-list. Require both a
                # provider mention and an address announcement in that case.
                if score < 0 and context_bonus >= 25:
                    candidate_host = host(url)
                    if candidate_host and not candidate_host.endswith(SOCIAL_HOST_SUFFIXES + SEARCH_HOST_SUFFIXES + INFRASTRUCTURE_HOST_SUFFIXES):
                        score = 45 + context_bonus
                elif score >= 0:
                    score += context_bonus
                if score >= 0:
                    candidates.append({
                        "url": url.rstrip("/"),
                        "label": label or "Telegram address announcement",
                        "score": min(score, 100),
                        "document_index": index,
                        "message_id": row.get("message_id"),
                    })
        else:
            # Conservative compatibility fallback for Telegram mirrors whose
            # HTML omits data-post attributes.
            extracted = links(document, hub_url)
            for url, label, index in extracted:
                score = candidate_score(provider_id, cfg, url, label, index, len(extracted))
                if score >= 0:
                    candidates.append({"url": url.rstrip("/"), "label": label, "score": score, "document_index": index})
    else:
        extracted = links(document, hub_url)
        for url, label, index in extracted:
            score = candidate_score(provider_id, cfg, url, label, index, len(extracted))
            if score >= 0:
                candidates.append({"url": url.rstrip("/"), "label": label, "score": score, "document_index": index})

    fallback = str(cfg.get("direct_fallback") or "").strip().rstrip("/")
    if fallback and host(fallback) != host(hub_url):
        candidates.append({"url": fallback, "label": "curated direct fallback", "score": 70, "document_index": -1, "fallback": True})
    if resolver == "latest_telegram_domain":
        candidates.sort(key=lambda row: (
            row.get("fallback", False),
            -int(row.get("message_id") or -1),
            -int(row.get("score") or 0),
            -int(row.get("document_index") or -1),
            row["url"],
        ))
    else:
        candidates.sort(key=lambda row: (-int(row["score"]), row.get("fallback", False), int(row["document_index"]), row["url"]))
    return candidates, candidates[0]["url"] if candidates else None


def search_engine_urls(query: str) -> list[tuple[str, str]]:
    encoded = urllib.parse.quote_plus(query)
    return [
        ("yandex", f"https://yandex.com/search/?text={encoded}"),
        ("duckduckgo", f"https://html.duckduckgo.com/html/?q={encoded}"),
    ]


def search_candidates(provider_id: str, cfg: dict[str, Any], query: str, timeout: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for engine, url in search_engine_urls(query):
        try:
            status, final, document, _headers = fetch(url, timeout)
            lowered = document[:200_000].casefold()
            challenged = any(marker in lowered for marker in SEARCH_CHALLENGE_MARKERS)
            observations.append({"engine": engine, "url": url, "status": status, "final_url": final, "challenged": challenged})
            if not 200 <= status < 400 or challenged:
                continue
            for result_url, label, index in links(document, final):
                result_host = host(result_url)
                if not result_host or result_host.endswith(SEARCH_HOST_SUFFIXES + SOCIAL_HOST_SUFFIXES + INFRASTRUCTURE_HOST_SUFFIXES):
                    continue
                if not same_brand(provider_id, result_url, cfg):
                    continue
                candidates.append({
                    "url": result_url.rstrip("/"),
                    "label": label or f"{engine} search result",
                    "score": 45 - min(index, 10),
                    "source_type": "search",
                    "source": engine,
                    "query": query,
                    "document_index": index,
                })
                if len(candidates) >= 8:
                    break
        except Exception as exc:
            observations.append({"engine": engine, "url": url, "error": f"{type(exc).__name__}: {exc}"})
    return candidates, observations


def validate_terminal(provider_id: str, cfg: dict[str, Any], candidate: str, timeout: float) -> dict[str, Any]:
    try:
        status, final, document, headers = fetch(candidate, timeout)
    except Exception as exc:
        return {"url": candidate, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    final_host = host(final)
    content_type = headers.get("Content-Type", headers.get("content-type", ""))
    allowed_statuses = {int(item) for item in cfg.get("terminal_success_statuses") or list(range(200, 400))}
    blocked_hosts = {str(item).casefold().strip(".") for item in cfg.get("blocked_hosts") or []}
    ok = status in allowed_statuses and bool(final_host) and is_public_url(final) and final_host not in blocked_hosts
    if ok and not same_brand(provider_id, final, cfg):
        ok = False
    lowered = re.sub(r"\s+", " ", document[:150_000].casefold())
    if ok and any(marker in lowered for marker in PARKING_MARKERS):
        ok = False
    source_hosts = {
        host(str(source.get("url")))
        for source in cfg.get("sources") or []
        if source.get("url") and source.get("type") in {"hub", "telegram_public"}
    }
    # Address hubs and public announcement channels are discovery sources, never
    # catalogue origins. A 200 response or a cached history entry must not turn
    # the hub itself into the provider terminal route.
    if ok and final_host in source_hosts:
        ok = False
    required_markers = [str(item).casefold() for item in cfg.get("terminal_markers") or [] if str(item).strip()]
    if ok and required_markers and not any(marker in lowered for marker in required_markers):
        ok = False
    return {
        "url": candidate,
        "final_url": final.rstrip("/"),
        "status": status,
        "ok": ok,
        "content_type": content_type,
        "brand_match": same_brand(provider_id, final, cfg),
    }


def extract_api_candidates(site_url: str, document: str, provider_id: str, cfg: dict[str, Any]) -> list[str]:
    found: set[str] = set()
    for value in re.findall(r"https?://[a-z0-9.-]+(?::\d+)?(?:/[A-Za-z0-9_./?=&%+#{}:~-]*)?", document.replace("\\/", "/"), re.I):
        if "api" in host(value) and same_brand(provider_id, value, cfg):
            found.add(value.rstrip("/"))
    site_host = host(site_url)
    tld = ".".join(site_host.split(".")[1:]) if "." in site_host else ""
    for template in cfg.get("api_templates") or []:
        found.add(str(template).format(site=site_url.rstrip("/"), host=site_host, tld=tld).rstrip("/"))
    return sorted(found)


def probe(base: str, routes: list[str], success_statuses: set[int], timeout: float) -> dict[str, Any]:
    observations = []
    for route in routes or ["/"]:
        url = urllib.parse.urljoin(base.rstrip("/") + "/", route.lstrip("/"))
        try:
            status, final, _body, headers = fetch(url, timeout)
            ok = status in success_statuses
            observation = {"url": url, "final_url": final, "status": status, "ok": ok, "content_type": headers.get("Content-Type", "")}
            observations.append(observation)
            if ok:
                return {"ok": True, "base": base, "observation": observation, "observations": observations}
        except Exception as exc:
            observations.append({"url": url, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return {"ok": False, "base": base, "observations": observations}


def _candidate_identity(candidate: dict[str, Any]) -> str:
    return str(candidate.get("url") or "").rstrip("/")


def gather_candidates(provider_id: str, cfg: dict[str, Any], history_row: dict[str, Any], mode: str, timeout: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []

    for index, url in enumerate(cfg.get("direct_candidates") or []):
        if is_http_url(url):
            candidates.append({
                "url": str(url).rstrip("/"), "label": "curated direct candidate",
                "score": 72 - min(index, 10), "source_type": "curated_direct", "source": "provider-hubs.json",
            })
    current = history_row.get("current") if isinstance(history_row, dict) else None
    if isinstance(current, dict) and is_http_url(current.get("url")):
        candidates.append({
            "url": str(current["url"]).rstrip("/"), "label": "last-known-good domain",
            "score": 78, "source_type": "history_lkg", "source": "provider-domain-history.json",
        })

    for source in cfg.get("sources") or []:
        if not isinstance(source, dict):
            continue
        source_type = str(source.get("type") or "hub")
        if source_type == "search":
            continue
        url = str(source.get("url") or "").strip()
        if not is_http_url(url):
            continue
        try:
            status, final, document, _headers = fetch(url, timeout)
            observation = {"source_type": source_type, "url": url, "status": status, "final_url": final}
            observations.append(observation)
            if not 200 <= status < 400:
                continue
            if source_type == "redirect" and host(final) != host(url):
                candidates.append({
                    "url": final.rstrip("/"), "label": "validated redirect destination",
                    "score": 92, "source_type": source_type, "source": url,
                })
            source_cfg = dict(cfg)
            source_cfg["hub"] = final
            if source_type == "telegram_public":
                source_cfg["resolver"] = "latest_telegram_domain"
            source_candidates, _preferred = choose_official(provider_id, source_cfg, final, document)
            base_priority = int(source.get("priority") or 50)
            for row in source_candidates:
                row = dict(row)
                row["score"] = min(100, int(row.get("score") or 0) + max(0, min(15, (base_priority - 50) // 4)))
                row["source_type"] = source_type
                row["source"] = url
                candidates.append(row)
        except Exception as exc:
            observations.append({"source_type": source_type, "url": url, "error": f"{type(exc).__name__}: {exc}"})

    disabled = str(cfg.get("manifest_status") or "").casefold() in {"désactivé", "desactive", "disabled"}
    if mode == "deep" and (not disabled or bool(cfg.get("search_when_disabled", False))):
        for query in list(dict.fromkeys(str(item).strip() for item in cfg.get("search_queries") or [] if str(item).strip()))[:2]:
            found, search_observations = search_candidates(provider_id, cfg, query, timeout)
            candidates.extend(found)
            observations.extend(search_observations)

    dedup: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        identity = _candidate_identity(candidate)
        if not identity or not is_public_url(identity):
            continue
        previous = dedup.get(identity)
        if previous is None or int(candidate.get("score") or 0) > int(previous.get("score") or 0):
            dedup[identity] = candidate
    ordered = sorted(dedup.values(), key=lambda row: (-int(row.get("score") or 0), row.get("source_type") == "search", row["url"]))
    return ordered, observations


def _hostish(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9.-]+", value.casefold())) and "." in value and "/" not in value


def update_provider_patch(config: dict[str, Any], provider_id: str, hub_cfg: dict[str, Any], site_url: str, api_url: str | None, history_row: dict[str, Any] | None = None) -> list[dict[str, str]]:
    patch = config.setdefault("provider_patches", {}).setdefault(provider_id, {})
    replacements = patch.setdefault("replacements", {})
    runtime = patch.setdefault("runtime_domain_replacements", {})
    changes: list[dict[str, str]] = []
    new_site_host = host(site_url)

    # A domain that becomes current must never remain a replacement source,
    # otherwise a later fs16 -> fs03 style rollback creates a migration cycle.
    for mapping in (replacements, runtime):
        if new_site_host in mapping:
            mapping.pop(new_site_host, None)
            changes.append({"from": new_site_host, "to": new_site_host, "kind": "cycle_removed"})

    old_hosts = {str(item).lower().strip(".") for item in hub_cfg.get("old_site_hosts") or [] if item}
    previous_site = patch.get("official_site")
    if previous_site and host(str(previous_site)):
        old_hosts.add(host(str(previous_site)))
    for direct in hub_cfg.get("direct_candidates") or []:
        if host(str(direct)):
            old_hosts.add(host(str(direct)))
    if isinstance(history_row, dict):
        current = history_row.get("current")
        if isinstance(current, dict) and host(str(current.get("url") or "")):
            old_hosts.add(host(str(current.get("url"))))
        for prior in history_row.get("previous") or []:
            if isinstance(prior, dict) and host(str(prior.get("url") or "")):
                old_hosts.add(host(str(prior.get("url"))))

    for old in sorted(old_hosts):
        if old and old != new_site_host:
            if replacements.get(old) != new_site_host or runtime.get(old) != new_site_host:
                replacements[old] = new_site_host
                runtime[old] = new_site_host
                changes.append({"from": old, "to": new_site_host, "kind": "site"})

    if api_url:
        new_api_host = host(api_url)
        old_api_hosts = {str(item).lower().strip(".") for item in hub_cfg.get("old_api_hosts") or [] if item}
        previous_api = patch.get("official_api")
        if previous_api and host(str(previous_api)):
            old_api_hosts.add(host(str(previous_api)))
        for mapping in (replacements, runtime):
            if new_api_host in mapping:
                mapping.pop(new_api_host, None)
                changes.append({"from": new_api_host, "to": new_api_host, "kind": "api_cycle_removed"})
        for old in sorted(old_api_hosts):
            if old and old != new_api_host:
                if replacements.get(old) != new_api_host or runtime.get(old) != new_api_host:
                    replacements[old] = new_api_host
                    runtime[old] = new_api_host
                    changes.append({"from": old, "to": new_api_host, "kind": "api"})

    patch["official_hub"] = hub_cfg.get("hub") or next((source.get("url") for source in hub_cfg.get("sources") or [] if source.get("type") in {"hub", "telegram_public"}), None)
    patch["official_site"] = site_url
    if api_url:
        patch["official_api"] = api_url

    fixed_endpoint = patch.get("fixed_endpoint")
    if isinstance(fixed_endpoint, dict):
        fixed_endpoint["referer"] = site_url.rstrip("/") + "/"
        if api_url:
            fixed_endpoint["api"] = api_url.rstrip("/")
        else:
            existing_api = str(fixed_endpoint.get("api") or "")
            existing_api_host = host(existing_api)
            if existing_api_host.startswith("api.") and new_site_host:
                parsed_api = urllib.parse.urlparse(existing_api)
                new_api_host = "api." + new_site_host
                fixed_endpoint["api"] = urllib.parse.urlunparse((
                    parsed_api.scheme or "https", new_api_host, parsed_api.path,
                    parsed_api.params, parsed_api.query, parsed_api.fragment,
                )).rstrip("/")

    script_options = patch.setdefault("patch_script_options", {})
    toflix_script = "scripts/provider_patches/toflix_official_endpoint.py"
    if toflix_script in (patch.get("patch_scripts") or []):
        options = script_options.setdefault(toflix_script, {})
        options["site"] = site_url.rstrip("/")
        api_base = (api_url or f"https://api.{new_site_host}").rstrip("/")
        options["fallback_api"] = api_base if api_base.endswith("toflix_api.php") else api_base + "/toflix_api.php"
    recovery_script = "scripts/provider_patches/vf_catalogue_recovery.py"
    if recovery_script in (patch.get("patch_scripts") or []):
        options = script_options.setdefault(recovery_script, {})
        options["base_url"] = site_url.rstrip("/")
        if str(options.get("strategy") or "") == "api_discovery":
            if api_url:
                options["api_url"] = api_url.rstrip("/")
            else:
                options["api_url"] = f"https://api.{new_site_host}".rstrip("/")
    # `required_values` is reserved for concrete code markers injected by a
    # patch profile/script. A resolved domain is routing metadata and may never
    # appear literally in a provider bundle (for example when the endpoint is
    # discovered dynamically or supplied by an API). Treating bare hosts as
    # required code markers caused false pipeline failures after successful
    # domain resolution. Remove legacy host-only entries and let replacement,
    # fixed-endpoint and runtime-wrapper records prove that a route patch landed.
    required = [str(value) for value in (patch.get("required_values") or [])]
    required = [value for value in required if not _hostish(value)]
    patch["required_values"] = required
    manifest_overrides = patch.get("manifest_overrides")
    if isinstance(manifest_overrides, dict) and manifest_overrides.get("logo"):
        logo_host = host(str(manifest_overrides["logo"]))
        if logo_host in old_hosts and logo_host != new_site_host:
            manifest_overrides["logo"] = f"https://{new_site_host}/favicon.ico"
    return changes


def _apply_confirmation(history_row: dict[str, Any], terminal: str, source_type: str, required_runs: int) -> tuple[bool, dict[str, Any]]:
    if source_type != "search":
        history_row.pop("pending", None)
        return True, {"required": 1, "observed": 1}
    pending = history_row.get("pending") if isinstance(history_row.get("pending"), dict) else {}
    observed = int(pending.get("count") or 0) + 1 if pending.get("url") == terminal else 1
    history_row["pending"] = {"url": terminal, "count": observed, "source_type": source_type, "last_seen": now_iso()}
    return observed >= required_runs, {"required": required_runs, "observed": observed}


def resolve_one(provider_id: str, cfg: dict[str, Any], history_row: dict[str, Any], mode: str, timeout: float) -> dict[str, Any]:
    item: dict[str, Any] = {"provider_id": provider_id, "status": "inconclusive"}
    candidates, source_observations = gather_candidates(provider_id, cfg, history_row, mode, timeout)
    item["sources"] = source_observations
    item["site_candidates"] = candidates
    validations: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    for candidate in candidates:
        validation = validate_terminal(provider_id, cfg, str(candidate["url"]), timeout)
        validation["source_type"] = candidate.get("source_type")
        validation["source"] = candidate.get("source")
        validation["candidate_score"] = candidate.get("score")
        validations.append(validation)
        if validation.get("ok"):
            selected = {**candidate, **validation}
            break
    item["site_validations"] = validations
    if not selected:
        current = history_row.get("current") if isinstance(history_row, dict) else None
        if isinstance(current, dict) and current.get("url"):
            item["status"] = "retained_last_known_good"
            item["official_site"] = current.get("url")
            item["reason"] = "no_new_candidate_validated"
        else:
            item["reason"] = "no_runtime_validated_terminal_site"
        return item

    terminal = str(selected["final_url"]).rstrip("/")
    source_type = str(selected.get("source_type") or "unknown")
    confirmed, confirmation = _apply_confirmation(history_row, terminal, source_type, int(cfg.get("search_confirmation_runs") or 2))
    item["confirmation"] = confirmation
    item["official_site"] = terminal
    item["selected_source_type"] = source_type
    item["selected_source"] = selected.get("source")
    if not confirmed:
        item["status"] = "pending_confirmation"
        item["reason"] = "search_only_candidate_requires_consecutive_confirmation"
        return item

    try:
        site_status, final_site, site_document, _headers = fetch(terminal, timeout)
    except Exception as exc:
        item["reason"] = "terminal_refetch_failed"
        item["error"] = f"{type(exc).__name__}: {exc}"
        return item
    item["site_status"] = site_status
    item["site_final_url"] = final_site
    api_candidates = extract_api_candidates(final_site, site_document, provider_id, cfg)
    item["api_candidates"] = api_candidates
    validated_api = None
    api_probes = []
    for candidate in api_candidates:
        result = probe(candidate, list(cfg.get("api_probe_routes") or []), set(cfg.get("api_success_statuses") or [200, 400, 401, 403, 404, 405]), timeout)
        api_probes.append(result)
        if result["ok"]:
            validated_api = candidate
            break
    item["api_probes"] = api_probes
    if bool(cfg.get("require_api_validation", False)) and not validated_api:
        item["reason"] = "api_not_runtime_validated"
        return item
    item["validated_api"] = validated_api
    item["status"] = "validated" if validated_api else "site_validated"
    item["reason"] = "terminal_site_runtime_validated"
    return item


def update_history_row(history_row: dict[str, Any], item: dict[str, Any]) -> None:
    if item.get("status") not in {"validated", "site_validated"}:
        return
    terminal = str(item.get("official_site") or "").rstrip("/")
    if not terminal:
        return
    current = history_row.get("current") if isinstance(history_row.get("current"), dict) else None
    if current and str(current.get("url") or "").rstrip("/") != terminal:
        previous = [current, *(history_row.get("previous") or [])]
        history_row["previous"] = previous[:5]
    history_row["current"] = {
        "url": terminal,
        "host": host(terminal),
        "validated_at": now_iso(),
        "source_type": item.get("selected_source_type"),
        "source": item.get("selected_source"),
    }
    history_row.pop("pending", None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="health-output/provider-hub-report.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mode", choices=("quick", "deep"), default="quick")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()

    config = load_json(CONFIG_PATH, {})
    hubs = merge_hub_registry(config)
    history = load_json(HISTORY_PATH, {"schema_version": 1, "providers": {}})
    history.setdefault("schema_version", 1)
    history_providers = history.setdefault("providers", {})
    selected_ids = {canonical_provider_id(item) for item in args.provider}

    work: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for provider_id, cfg in sorted(hubs.items()):
        if selected_ids and provider_id not in selected_ids:
            continue
        if not args.include_disabled and str(cfg.get("manifest_status") or "").casefold() in {"désactivé", "desactive", "disabled"}:
            continue
        work.append((provider_id, cfg, history_providers.setdefault(provider_id, {})))

    report: dict[str, Any] = {
        "schema_version": 3,
        "generated_at": now_iso(),
        "mode": args.mode,
        "providers": {},
        "applied": 0,
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 16))) as pool:
        future_map = {
            pool.submit(resolve_one, provider_id, cfg, history_row, args.mode, args.timeout): (provider_id, cfg, history_row)
            for provider_id, cfg, history_row in work
        }
        for future in concurrent.futures.as_completed(future_map):
            provider_id, cfg, history_row = future_map[future]
            try:
                item = future.result()
            except Exception as exc:
                item = {"provider_id": provider_id, "status": "inconclusive", "reason": "exception", "error": f"{type(exc).__name__}: {exc}"}
            if args.apply and item.get("status") in {"validated", "site_validated"}:
                changes = update_provider_patch(config, provider_id, cfg, str(item["official_site"]), item.get("validated_api"), history_row)
                item["applied_changes"] = changes
                report["applied"] += len(changes)
                update_history_row(history_row, item)
            report["providers"][provider_id] = item

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output, report)
    if args.apply:
        atomic_write_json(CONFIG_PATH, config)
        history["updated_at"] = now_iso()
        atomic_write_json(HISTORY_PATH, history)
    validated = sum(1 for row in report["providers"].values() if row.get("status") in {"validated", "site_validated"})
    retained = sum(1 for row in report["providers"].values() if row.get("status") == "retained_last_known_good")
    pending = sum(1 for row in report["providers"].values() if row.get("status") == "pending_confirmation")
    print(f"provider hub resolution complete: validated={validated} retained_lkg={retained} pending={pending} applied={report['applied']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
