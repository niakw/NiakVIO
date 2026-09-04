#!/usr/bin/env python3
"""Enrich durable Provider v3 DATA from provider-local upstream source, statically.

The three configured upstream repositories remain knowledge-only inputs.  This
module never executes, bundles or publishes upstream JavaScript.  It recognizes
route expressions used by those historical providers (including template
literals) and converts only their observable request shapes into deterministic
NiakVIO DATA placeholders.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources.json"
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
USER_AGENT = "NiakVIO-ProviderV3-Static-Plan/1"
EXPECTED = 96

FULL_URL_RE = re.compile(r"https?://[^\s\"'`<>)]+", re.I)
ROUTE_RE = re.compile(
    r"/(?:api|search|recherche|watch|embed|player|play|video|videos|stream|streams|"
    r"source|sources|server|servers|resolve|proxy|movie|movies|media|sheet|film|films|"
    r"tv|series|show|episode|episodes|season|saison|anime|catalogue|template-php|wp-json|"
    r"wp-admin|index\.php)[^\"'`<>\\\r\n\t ]{0,700}",
    re.I,
)
JS_TEMPLATE_EXPR_RE = re.compile(r"\$\{([^{}]{1,160})\}")
NON_EXECUTABLE_TOKENS = (
    "q=ponyfill",
    "/license",
    "lodash.com",
    "openjsf.org",
    "underscorejs.org",
    "npms.io",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def canonical(value: object) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip(".-").replace("_", "-")


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/javascript,text/javascript,text/plain,*/*",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read(2_000_000)
    if len(data) < 20:
        raise ValueError("source too small")
    text = data.decode("utf-8", errors="ignore")
    if text.lstrip().casefold().startswith(("<!doctype html", "<html")):
        raise ValueError("HTML instead of JavaScript")
    return text


def expression_placeholder(expression: str) -> str | None:
    low = re.sub(r"\s+", "", expression).casefold()
    if not low:
        return None
    if "encodeuricomponent(" in low:
        inner = low.split("encodeuricomponent(", 1)[1].rstrip(")")
        low = inner
    if any(token in low for token in ("tmdbid", "tmdb_id", "tmdb.id")):
        return "{tmdbId}"
    if any(token in low for token in ("imdbid", "imdb_id", "imdb.id")):
        return "{imdbId}"
    if any(token in low for token in ("season", "saison")):
        return "{season}"
    if any(token in low for token in ("episode", "episodenumber", "epnum", "ep.")):
        return "{episode}"
    if any(token in low for token in ("query", "search", "cleantitle", "sanitized", "keyword")):
        return "{query}"
    if any(token in low for token in ("slug", "permalink")):
        return "{slug}"
    if any(token in low for token in ("media", "type", "kind")):
        return "{media}"
    # Provider-internal catalogue identifiers must stay distinct from TMDB.
    if re.search(r"(?:^|[.\[(])(?:anime)?id(?:$|[.\])])", low) or low.endswith("id"):
        return "{id}"
    if any(token in low for token in ("title", "name")):
        return "{query}"
    return None


def normalize_dynamic(value: str) -> str | None:
    raw = str(value or "").strip().replace("\\/", "/")
    if not raw:
        return None
    # Strip punctuation commonly captured after a JS expression.
    raw = raw.rstrip(",;)]}")

    def repl(match: re.Match[str]) -> str:
        placeholder = expression_placeholder(match.group(1))
        return placeholder or "{dynamic}"

    raw = JS_TEMPLATE_EXPR_RE.sub(repl, raw)
    raw = raw.replace("{dynamic}", "")
    raw = re.sub(r"//+", "/", raw) if not raw.startswith(("http://", "https://")) else raw

    if raw.startswith(("http://", "https://")):
        try:
            parsed = urllib.parse.urlparse(raw)
        except ValueError:
            return None
        raw = parsed.path or "/"
        if parsed.query:
            raw += "?" + parsed.query

    if not raw.startswith("/") or raw == "/":
        return None
    if any(token in raw.casefold() for token in NON_EXECUTABLE_TOKENS):
        return None

    path, sep, query = raw.partition("?")
    # Normalize common empty query parameters to NiakVIO placeholders.
    if sep:
        parts: list[str] = []
        for part in query.split("&"):
            if not part:
                continue
            key, eq, val = part.partition("=")
            lower = key.casefold()
            if eq and not val:
                if lower in {"q", "query", "search", "keyword", "story", "s"}:
                    val = "{query}"
                elif lower in {"id", "anime_id", "post_id"}:
                    val = "{id}"
                elif lower in {"tmdb", "tmdbid", "tmdb_id"}:
                    val = "{tmdbId}"
                elif lower in {"season", "saison"}:
                    val = "{season}"
                elif lower in {"episode", "ep", "e"}:
                    val = "{episode}"
            parts.append(key + ("=" + val if eq else ""))
        raw = path + ("?" + "&".join(parts) if parts else "")

    if len(raw) > 700:
        return None
    return raw


def extract_routes(text: str) -> list[str]:
    routes: list[str] = []
    candidates: list[str] = []
    candidates.extend(FULL_URL_RE.findall(text))
    candidates.extend(match.group(0) for match in ROUTE_RE.finditer(text))

    # Search-form endpoints often have a neutral filename (fetch.php/ajax.php)
    # but are still an executable catalogue route when paired with query=... .
    for match in re.finditer(
        r"(?:fetch|safeFetch|postSearch)\s*\(\s*[`\"']([^`\"']{1,700})[`\"']",
        text,
        re.I,
    ):
        candidates.append(match.group(1))

    for candidate in candidates:
        route = normalize_dynamic(candidate)
        if route and route not in routes:
            routes.append(route)
        if len(routes) >= 128:
            break
    return routes


def infer_family(text: str, routes: list[str]) -> str:
    low = text.casefold()
    joined = "\n".join(routes).casefold()
    if "episodes.js" in low and "/catalogue/" in low:
        return "catalogue-episodes-js"
    if "postsearch(" in low or "application/x-www-form-urlencoded" in low:
        if "iframe" in low or "videoplayer" in low or "sibnet" in low:
            return "catalogue-form-html-embed"
        return "catalogue-form-html"
    if "/api/streams/episode" in low and "/player" in low:
        return "signed-player-api"
    if "/stream/movie/" in low and "/stream/series/" in low:
        return "stremio-json"
    if re.search(r"/(?:search|recherche)|[?&](?:s|q|query|story)=", joined) and re.search(r"/(?:embed|player|watch|video|episode|anime|film|series)", joined):
        return "catalogue-html-embed"
    if re.search(r"/(?:api/)?(?:stream|streams|source|sources)[/?]", joined):
        return "tmdb-direct-api"
    if routes and ("cheerio" in low or "extractstreams" in low):
        return "catalogue-html"
    return "unknown"


def route_kind(route: str) -> str:
    value = route.casefold()
    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|story)=", value):
        return "search"
    if re.search(r"/(?:api)(?:[./?#]|$)", value):
        return "api"
    if re.search(r"/(?:player|embed|play)(?:[/?#.-]|$)", value):
        return "player"
    if re.search(r"\{(?:id|tmdbid|tmdb_id|tmdbid|slug|query|title|season|episode)\}", value):
        return "detail"
    if re.search(r"/(?:title|movie|movies|film|films|tv|series|show|watch|media|anime|episode|season|saison|catalogue)(?:[/?#.-]|$)", value):
        return "detail"
    return "other"


def merge_unique(target: list[str], values: list[str], limit: int) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)
        if len(target) >= limit:
            break


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    config = load(SOURCES)
    knowledge_path = args.knowledge.resolve()
    payload = load(knowledge_path)
    providers = payload.get("providers")
    if not isinstance(providers, dict) or len(providers) != EXPECTED:
        raise ValueError(f"durable knowledge provider count must be {EXPECTED}")

    upstreams = config.get("upstreams") if isinstance(config.get("upstreams"), dict) else {}
    enriched = 0
    fetched_modules = 0
    failures: list[str] = []

    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        raw_knowledge = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}
        source_rows = row.get("sources") if isinstance(row.get("sources"), list) else []

        source_texts: list[str] = []
        for source_row in source_rows:
            if not isinstance(source_row, dict):
                continue
            source_key = str(source_row.get("source") or "").strip()
            upstream_id = str(source_row.get("upstreamId") or provider_id).strip()
            source_cfg = upstreams.get(source_key) if isinstance(upstreams.get(source_key), dict) else {}
            templates = source_cfg.get("knowledge_raw_templates") if isinstance(source_cfg.get("knowledge_raw_templates"), list) else []
            for raw_template in templates[:8]:
                template = str(raw_template or "").strip()
                if not template:
                    continue
                url = template.format(provider_id=upstream_id)
                try:
                    source_texts.append(fetch_text(url))
                    fetched_modules += 1
                except (urllib.error.URLError, TimeoutError, ValueError, OSError):
                    continue
            if source_texts:
                break

        if not source_texts:
            continue
        text = "\n".join(source_texts)
        routes = extract_routes(text)
        family = infer_family(text, routes)

        model_routes = model.get("routes") if isinstance(model.get("routes"), list) else []
        knowledge_routes = raw_knowledge.get("routes") if isinstance(raw_knowledge.get("routes"), list) else []
        knowledge_fragments = raw_knowledge.get("routeFragments") if isinstance(raw_knowledge.get("routeFragments"), list) else []
        before = len(model_routes)
        merge_unique(model_routes, routes, 128)
        merge_unique(knowledge_routes, routes, 160)
        merge_unique(knowledge_fragments, routes, 160)
        model["routes"] = model_routes
        raw_knowledge["routes"] = knowledge_routes
        raw_knowledge["routeFragments"] = knowledge_fragments

        current_family = str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold()
        if current_family == "unknown" and family != "unknown":
            model["sourceRuntimeFamily"] = family
        current_knowledge_family = str(raw_knowledge.get("runtimeFamily") or "unknown").strip().casefold()
        if current_knowledge_family == "unknown" and family != "unknown":
            raw_knowledge["runtimeFamily"] = family

        row["model"] = model
        row["knowledge"] = raw_knowledge
        if len(model_routes) != before or family != "unknown":
            enriched += 1

        strategy = str(model.get("strategy") or "unknown").strip().casefold()
        enabled = True
        executable = bool(model.get("apiRecipe"))
        kinds = {route_kind(str(route)) for route in model_routes}
        if strategy != "quarantined" and not executable:
            executable = bool({"api", "search", "detail", "player"} & kinds) and bool(
                model.get("knownSite") or model.get("officialSite") or model.get("officialHub") or model.get("officialApi") or model.get("fixedApi") or model.get("origins")
            )
        if strategy != "quarantined" and enabled and not executable:
            failures.append(f"{provider_id}:{strategy}:family={model.get('sourceRuntimeFamily','unknown')}:routes={sorted(kinds)}")

    if failures:
        raise AssertionError("static source plan remains unresolved: " + "; ".join(failures))

    if not args.check:
        knowledge_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    familyful = sum(
        1 for row in providers.values()
        if isinstance(row, dict)
        and isinstance(row.get("model"), dict)
        and str(row["model"].get("sourceRuntimeFamily") or "unknown") != "unknown"
    )
    routeful = sum(
        1 for row in providers.values()
        if isinstance(row, dict)
        and isinstance(row.get("model"), dict)
        and bool(row["model"].get("routes"))
    )
    print(
        "PROVIDER_V3_SOURCE_PLAN_ENRICHMENT_OK "
        f"providers={len(providers)} enriched={enriched} fetched_modules={fetched_modules} "
        f"routeful={routeful} familyful={familyful} upstream_code_executed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
