#!/usr/bin/env python3
"""Static Provider v3 contract recognizer.

Recognizes provider request contracts from upstream source/bundles without executing
upstream JavaScript. The recognizer is source-aware:

- Gowaru: provider-local modular source is preferred (extractor/http/index/config).
- Yoru: compiled provider bundle supplies provider DATA while the public template
  branch supplies method/interface evidence only.
- All-in-One: compiled provider bundle is treated as opaque static knowledge.

The output remains NiakVIO-owned DATA: routes, runtime family, request semantics,
identity dependencies and recognition provenance. Upstream code is never embedded,
executed or published.
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
OVERRIDES = ROOT / "provider-overrides.json"
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
USER_AGENT = "NiakVIO-ProviderContractRecognizer/2"
EXPECTED = 96

YORU_METHOD_TEMPLATE_URLS = (
    "https://raw.githubusercontent.com/yoruix/nuvio-providers/template/src/_template/extractor.js",
    "https://raw.githubusercontent.com/yoruix/nuvio-providers/template/src/_template/http.js",
    "https://raw.githubusercontent.com/yoruix/nuvio-providers/template/src/_template/index.js",
)

FULL_URL_RE = re.compile(r"https?://[^\s\"'`<>)]+", re.I)
ROUTE_RE = re.compile(
    r"/(?:api|search|recherche|watch|embed|player|play|video|videos|stream|streams|"
    r"source|sources|server|servers|resolve|proxy|movie|movies|media|sheet|film|films|"
    r"tv|series|show|episode|episodes|season|saison|anime|catalogue|template-php|engine|"
    r"data|wp-json|wp-admin|index\.php)[^\"'`<>\\\r\n\t ]{0,700}",
    re.I,
)
JS_TEMPLATE_EXPR_RE = re.compile(r"\$\{([^{}]{1,180})\}")
FETCH_CALL_RE = re.compile(
    r"(?P<fn>fetchJson|fetchText|safeFetch|fetch|postSearch|request)\s*\(",
    re.I,
)
GETSTREAMS_RE = re.compile(r"(?:async\s+)?function\s+(?:getStreams|extractStreams)\s*\(([^)]*)\)", re.I)

NON_EXECUTABLE_TOKENS = (
    "q=ponyfill",
    "/license",
    "lodash.com",
    "openjsf.org",
    "underscorejs.org",
    "npms.io",
    "raw.githubusercontent.com",
    "github.com",
)
JUNK_ROUTE_PATTERNS = (
    re.compile(r"/(?:feed|comments?/feed|wp-json/oembed|wp-admin|admin|login|register)(?:[/?#.-]|$)", re.I),
    re.compile(r"/(?:resolvers?|metadata|utils?|helpers?|build|package)\.js(?:[?#]|$)", re.I),
    re.compile(r"\.(?:css|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)", re.I),
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
    if any(token in low for token in ("query", "search", "cleantitle", "sanitized", "keyword", "story")):
        return "{query}"
    if any(token in low for token in ("slug", "permalink")):
        return "{slug}"
    if any(token in low for token in ("media", "type", "kind")):
        return "{media}"
    if any(token in low for token in ("lang", "language")):
        return "{lang}"
    if re.search(r"(?:^|[.\[(])(?:anime)?id(?:$|[.\])])", low) or low.endswith("id"):
        return "{id}"
    if any(token in low for token in ("title", "name")):
        return "{query}"
    return None


def normalize_dynamic(value: str) -> str | None:
    raw = str(value or "").strip().replace("\\/", "/")
    if not raw:
        return None
    raw = raw.rstrip(",;)]}")

    def repl(match: re.Match[str]) -> str:
        return expression_placeholder(match.group(1)) or "{dynamic}"

    raw = JS_TEMPLATE_EXPR_RE.sub(repl, raw)
    raw = raw.replace("{dynamic}", "")
    if raw.startswith(("http://", "https://")):
        try:
            parsed = urllib.parse.urlparse(raw)
        except ValueError:
            return None
        raw = parsed.path or "/"
        if parsed.query:
            raw += "?" + parsed.query
    elif raw.startswith("//"):
        raw = "/" + raw.lstrip("/")

    if not raw.startswith("/") or raw == "/":
        return None
    if any(token in raw.casefold() for token in NON_EXECUTABLE_TOKENS):
        return None

    path, sep, query = raw.partition("?")
    if sep:
        parts: list[str] = []
        for part in query.split("&"):
            if not part:
                continue
            key, eq, val = part.partition("=")
            if not key:
                continue
            lower = key.casefold()
            if eq and not val:
                if lower in {"q", "query", "search", "keyword", "story", "s"}:
                    val = "{query}"
                elif lower in {"id", "anime_id", "post_id", "movieid", "mediaid"}:
                    val = "{id}"
                elif lower in {"tmdb", "tmdbid", "tmdb_id"}:
                    val = "{tmdbId}"
                elif lower in {"season", "saison"}:
                    val = "{season}"
                elif lower in {"episode", "ep", "e"}:
                    val = "{episode}"
                elif lower in {"type", "media", "m"}:
                    val = "{media}"
            parts.append(key + ("=" + val if eq else ""))
        raw = path + ("?" + "&".join(parts) if parts else "")

    raw = re.sub(r"//+", "/", raw)
    if len(raw) > 700:
        return None
    return raw


def route_is_junk(route: str) -> bool:
    value = str(route or "").strip()
    if not value or value == "/":
        return True
    low = value.casefold()
    if any(token in low for token in NON_EXECUTABLE_TOKENS):
        return True
    return any(pattern.search(value) for pattern in JUNK_ROUTE_PATTERNS)


def route_kind(route: str) -> str:
    value = route.casefold()
    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|story)=", value):
        return "search"
    if re.search(r"/(?:engine/ajax/search\.php|template-php/[^?#]*/fetch\.php)(?:[?#]|$)", value):
        return "search"
    if re.search(r"/(?:get_seasons\.php|eps_[^/?#]+\.txt)(?:[?#]|$)", value):
        return "episode-index"
    if re.search(r"/(?:player|embed|play)(?:[/?#.-]|$)", value):
        return "player"
    if re.search(r"/(?:api)(?:[./?#]|$)", value):
        return "api"
    if re.search(r"/(?:stream|streams|source|sources|resolve|proxy)(?:[/?#.-]|$)", value):
        return "source"
    if re.search(r"\{(?:id|tmdbid|tmdb_id|slug|query|title|season|episode)\}", value):
        return "detail"
    if re.search(r"/(?:title|movie|movies|film|films|tv|series|show|watch|media|anime|episode|season|saison|catalogue)(?:[/?#.-]|$)", value):
        return "detail"
    return "other"


def route_is_executable_candidate(route: str, *, explicit: bool = False) -> bool:
    if route_is_junk(route):
        return False
    if explicit:
        return True
    kind = route_kind(route)
    if kind in {"search", "api", "player", "source", "episode-index"}:
        return True
    if "{" in route and "}" in route and kind == "detail":
        return True
    if re.search(r"/(?:episodes\.js|full-story\.php|controller\.php)(?:[?#]|$)", route, re.I):
        return True
    return False


def extract_routes(text: str) -> list[str]:
    routes: list[str] = []
    candidates: list[str] = []
    candidates.extend(FULL_URL_RE.findall(text))
    candidates.extend(match.group(0) for match in ROUTE_RE.finditer(text))
    for match in re.finditer(
        r"(?:fetchJson|fetchText|safeFetch|fetch|postSearch|request)\s*\(\s*[`\"']([^`\"']{1,700})[`\"']",
        text,
        re.I,
    ):
        candidates.append(match.group(1))
    for candidate in candidates:
        route = normalize_dynamic(candidate)
        if route and not route_is_junk(route) and route not in routes:
            routes.append(route)
        if len(routes) >= 160:
            break
    return routes


def _nearest_fetch_name(text: str, start: int) -> str:
    window = text[max(0, start - 220):start]
    matches = list(FETCH_CALL_RE.finditer(window))
    if not matches:
        return ""
    return str(matches[-1].group("fn") or "").strip()


def _request_window(text: str, start: int, end: int) -> str:
    return text[max(0, start - 220):min(len(text), end + 650)]


def _body_fields(window: str) -> list[str]:
    fields: list[str] = []
    for match in re.finditer(r"(?:body\s*:\s*)?[`\"']([^`\"']{1,500})[`\"']", window, re.I):
        value = match.group(1)
        if "=" not in value:
            continue
        for key in re.findall(r"(?:^|[&?])([A-Za-z_][A-Za-z0-9_-]{0,40})=", value):
            low = key.casefold()
            if low not in fields:
                fields.append(low)
    return fields[:16]


def recognize_request_contracts(text: str, routes: list[str] | None = None) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    all_routes = routes if isinstance(routes, list) else extract_routes(text)
    for route in all_routes:
        # Find the strongest occurrence of this route (or its stable prefix) near a request call.
        needles = [route]
        stable = re.sub(r"\{[^}]+\}", "", route).split("?", 1)[0].rstrip("/")
        if stable and stable not in needles:
            needles.append(stable)
        occurrence = -1
        for needle in needles:
            if not needle:
                continue
            occurrence = text.find(needle)
            if occurrence >= 0:
                break
        if occurrence < 0:
            continue
        fn = _nearest_fetch_name(text, occurrence)
        window = _request_window(text, occurrence, occurrence + len(route))
        explicit_method = re.search(r"method\s*:\s*[\"'](GET|POST|PUT|PATCH|DELETE)[\"']", window, re.I)
        method = (explicit_method.group(1).upper() if explicit_method else ("POST" if fn.casefold() == "postsearch" else "GET"))
        body_fields = _body_fields(window)
        is_form = bool(re.search(r"application/x-www-form-urlencoded|urlsearchparams", window, re.I))
        has_referer = bool(re.search(r"\bReferer\b|\breferer\b", window))
        has_origin = bool(re.search(r"\bOrigin\b|\borigin\b", window))
        response = "json" if fn.casefold() == "fetchjson" else "unknown"
        if response == "unknown" and re.search(r"JSON\.parse|\.json\s*\(", window):
            response = "json"
        if response == "unknown" and re.search(r"cheerio\.load|\.text\s*\(", window):
            response = "html-or-text"
        executed = bool(fn)
        # Template/assignment-built routes (episodes.js etc.) may be fetched by variable later.
        if not executed and re.search(r"episodes\.js|get_seasons\.php|eps_", route, re.I):
            executed = bool(re.search(r"fetch(?:Json|Text)?\s*\(\s*(?:url|target|endpoint|.*Url)\b", text, re.I))
        contracts.append({
            "route": route,
            "role": route_kind(route),
            "method": method,
            "bodyFields": body_fields,
            "formEncoded": is_form,
            "refererRequired": has_referer,
            "originRequired": has_origin,
            "response": response,
            "executedEvidence": executed,
            "call": fn or None,
        })
    # Stable unique order by route/method.
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in contracts:
        key = (str(row.get("route") or ""), str(row.get("method") or "GET"))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out[:96]


def infer_family(text: str, routes: list[str], contracts: list[dict[str, Any]] | None = None) -> str:
    low = text.casefold()
    joined = "\n".join(routes).casefold()
    contract_rows = contracts or []
    if "/engine/ajax/search.php" in low and (
        "get_seasons.php" in low or "eps_" in low or "full-story.php" in low or "newsid=" in low
    ):
        return "dle-film-api"
    if "episodes.js" in low and "/catalogue/" in low:
        return "catalogue-episodes-js"
    if "/api/streams/episode" in low and "/player" in low:
        return "signed-player-api"
    if "/stream/movie/" in low and "/stream/series/" in low:
        return "stremio-json"
    has_post_search = any(row.get("role") == "search" and row.get("method") == "POST" for row in contract_rows)
    has_embed = bool(re.search(r"/(?:embed|player|watch|video)", joined)) or bool(re.search(r"iframe|videoplayer|sibnet|vidmoly|streamtape|sendvid|voe", low))
    if has_post_search or "application/x-www-form-urlencoded" in low or "postsearch(" in low:
        return "catalogue-form-html-embed" if has_embed else "catalogue-form-html"
    if re.search(r"/(?:search|recherche)|[?&](?:s|q|query|story)=", joined) and has_embed:
        return "catalogue-html-embed"
    if re.search(r"/(?:search|recherche)|[?&](?:s|q|query|story)=", joined):
        return "catalogue-html"
    if re.search(r"/(?:api/)?(?:stream|streams|source|sources)[/?]", joined):
        return "tmdb-direct-api"
    if routes and ("cheerio" in low or "extractstreams" in low):
        return "catalogue-html"
    return "unknown"


def recognize_input_contract(provider_text: str, method_text: str = "") -> dict[str, Any]:
    combined = provider_text + "\n" + method_text
    signature = []
    match = GETSTREAMS_RE.search(combined)
    if match:
        signature = [part.strip() for part in match.group(1).split(",") if part.strip()][:8]
    low = provider_text.casefold()
    type_evidence: list[str] = []
    if re.search(r"mediatype\s*={2,3}\s*[\"']movie[\"']|case\s+[\"']movie[\"']", provider_text, re.I):
        type_evidence.append("movie")
    if re.search(r"mediatype\s*={2,3}\s*[\"'](?:tv|series)[\"']|case\s+[\"']tv[\"']", provider_text, re.I):
        type_evidence.append("tv")
    if re.search(r"mediatype\s*={2,3}\s*[\"']anime[\"']|case\s+[\"']anime[\"']", provider_text, re.I):
        type_evidence.append("anime")
    metadata_dependencies: list[str] = []
    if re.search(r"getTmdbTitles|getTmdbData|__nuvioCoreGetTmdbData|api\.themoviedb\.org", provider_text, re.I):
        metadata_dependencies.append("tmdb-metadata")
    if re.search(r"resolveTargetEpisodes|absolute.?episode", provider_text, re.I):
        metadata_dependencies.append("episode-mapping")
    return {
        "signature": signature,
        "typeEvidence": type_evidence,
        "metadataDependencies": metadata_dependencies,
        "acceptsTmdbId": bool(re.search(r"\btmdbId\b", combined)),
        "acceptsSeasonEpisode": bool(re.search(r"\bseason\b", combined) and re.search(r"\bepisode\b", combined)),
        "templateInterfaceEvidence": bool(method_text),
    }


def recognize_identity(routes: list[str], input_contract: dict[str, Any]) -> dict[str, Any]:
    kinds = {route_kind(route) for route in routes}
    has_tmdb_route = any(re.search(r"\{tmdbId\}|\{tmdb_id\}", route, re.I) for route in routes)
    has_provider_id = any("{id}" in route for route in routes)
    if "search" in kinds and has_provider_id:
        mode = "catalog-search-provider-id-chain"
    elif "search" in kinds:
        mode = "catalog-search"
    elif has_tmdb_route:
        mode = "tmdb-direct"
    else:
        mode = "unknown"
    return {
        "mode": mode,
        "requiresCoreMetadata": bool(input_contract.get("metadataDependencies")) or "search" in kinds,
        "usesProviderInternalId": has_provider_id and "search" in kinds,
        "usesTmdbIdInProviderRoute": has_tmdb_route,
    }


def merge_unique(target: list[str], values: list[str], limit: int) -> None:
    for value in values:
        value = str(value or "").strip()
        if value and value not in target:
            target.append(value)
        if len(target) >= limit:
            break


def source_mode(source_key: str, successful_urls: list[str]) -> str:
    if source_key == "gowaru" and any("/src/" in url for url in successful_urls):
        return "modular-source"
    if source_key == "yoru":
        return "compiled-bundle-plus-template-interface"
    if source_key == "aio":
        return "compiled-bundle"
    return "provider-source"


def family_specificity(value: str) -> int:
    family = str(value or "unknown").casefold()
    if family in {"unknown", "catalogue-html", "tmdb-direct-api"}:
        return 1
    if family in {"catalogue-html-embed", "catalogue-form-html", "catalogue-form-html-embed"}:
        return 2
    return 3


def derive_identity_input(identity: dict[str, Any]) -> dict[str, Any] | None:
    mode = str(identity.get("mode") or "")
    if mode.startswith("catalog-search"):
        return {
            "mode": "catalog_search",
            "requiresTmdbBeforeRun": True,
            "requiredFields": ["title", "year", "mediaType"],
        }
    if mode == "tmdb-direct":
        return {
            "mode": "tmdb_direct",
            "requiresTmdbBeforeRun": False,
            "requiredFields": ["tmdbId", "mediaType"],
        }
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    config = load(SOURCES)
    overrides = load(OVERRIDES) if OVERRIDES.is_file() else {}
    knowledge_path = args.knowledge.resolve()
    payload = load(knowledge_path)
    providers = payload.get("providers")
    if not isinstance(providers, dict) or len(providers) != EXPECTED:
        raise ValueError(f"durable knowledge provider count must be {EXPECTED}")

    upstreams = config.get("upstreams") if isinstance(config.get("upstreams"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    enriched = 0
    fetched_modules = 0
    recognized_requests = 0
    corrected_families = 0
    pruned_routes = 0
    failures: list[str] = []

    yoru_method_text = ""
    try:
        yoru_method_text = "\n".join(fetch_text(url) for url in YORU_METHOD_TEMPLATE_URLS)
        fetched_modules += len(YORU_METHOD_TEMPLATE_URLS)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        yoru_method_text = ""

    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        raw_knowledge = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}
        source_rows = row.get("sources") if isinstance(row.get("sources"), list) else []

        provider_texts: list[str] = []
        successful_urls: list[str] = []
        chosen_source = ""
        for source_row in source_rows:
            if not isinstance(source_row, dict):
                continue
            source_key = str(source_row.get("source") or "").strip()
            upstream_id = str(source_row.get("upstreamId") or provider_id).strip()
            source_cfg = upstreams.get(source_key) if isinstance(upstreams.get(source_key), dict) else {}
            templates = source_cfg.get("knowledge_raw_templates") if isinstance(source_cfg.get("knowledge_raw_templates"), list) else []
            local_texts: list[str] = []
            local_urls: list[str] = []
            for raw_template in templates[:8]:
                template = str(raw_template or "").strip()
                if not template:
                    continue
                url = template.format(provider_id=upstream_id)
                try:
                    local_texts.append(fetch_text(url))
                    local_urls.append(url)
                    fetched_modules += 1
                except (urllib.error.URLError, TimeoutError, ValueError, OSError):
                    continue
            if local_texts:
                provider_texts = local_texts
                successful_urls = local_urls
                chosen_source = source_key
                break

        if not provider_texts:
            continue

        provider_text = "\n".join(provider_texts)
        method_text = yoru_method_text if chosen_source == "yoru" else ""
        extracted_routes = extract_routes(provider_text)
        contracts = recognize_request_contracts(provider_text, extracted_routes)
        recognized_requests += sum(1 for contract in contracts if contract.get("executedEvidence"))
        family = infer_family(provider_text, extracted_routes, contracts)
        input_contract = recognize_input_contract(provider_text, method_text)
        identity = recognize_identity(extracted_routes, input_contract)
        mode = source_mode(chosen_source, successful_urls)
        confidence = 0.98 if mode == "modular-source" else (0.84 if mode == "compiled-bundle" else 0.80)

        explicit_patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        explicit_routes = [
            str(value).strip()
            for value in explicit_patch.get("learned_routes") or []
            if str(value).strip()
        ]
        existing_routes = [str(value).strip() for value in model.get("routes") or [] if str(value).strip()]
        recognized_routes = [
            str(contract.get("route") or "").strip()
            for contract in contracts
            if contract.get("executedEvidence") and route_is_executable_candidate(str(contract.get("route") or ""))
        ]
        recognized_routes.extend(
            route for route in extracted_routes
            if route_is_executable_candidate(route)
        )

        cleaned_existing = [
            route for route in existing_routes
            if route in explicit_routes or route_is_executable_candidate(route)
        ]
        pruned_routes += max(0, len(existing_routes) - len(cleaned_existing))
        model_routes: list[str] = []
        merge_unique(model_routes, explicit_routes, 128)
        merge_unique(model_routes, recognized_routes, 128)
        merge_unique(model_routes, cleaned_existing, 128)

        knowledge_routes = [
            str(value).strip() for value in raw_knowledge.get("routes") or []
            if str(value).strip() and not route_is_junk(str(value))
        ]
        knowledge_fragments = [
            str(value).strip() for value in raw_knowledge.get("routeFragments") or []
            if str(value).strip() and not route_is_junk(str(value))
        ]
        merge_unique(knowledge_routes, extracted_routes, 192)
        merge_unique(knowledge_fragments, extracted_routes, 192)

        before_family = str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold()
        if family != "unknown" and (
            family_specificity(family) > family_specificity(before_family)
            or before_family == "unknown"
            or (mode == "modular-source" and family != before_family)
        ):
            if family != before_family:
                corrected_families += 1
            model["sourceRuntimeFamily"] = family
        knowledge_family = str(raw_knowledge.get("runtimeFamily") or "unknown").strip().casefold()
        if family != "unknown" and family_specificity(family) >= family_specificity(knowledge_family):
            raw_knowledge["runtimeFamily"] = family

        model["routes"] = model_routes
        raw_knowledge["routes"] = knowledge_routes
        raw_knowledge["routeFragments"] = knowledge_fragments

        if not isinstance(model.get("identityInput"), dict) or not model.get("identityInput"):
            derived = derive_identity_input(identity)
            if derived:
                model["identityInput"] = derived

        recognition = {
            "schemaVersion": 2,
            "source": chosen_source,
            "sourceMode": mode,
            "confidence": confidence,
            "providerSourceUrls": successful_urls[:8],
            "upstreamCodeExecuted": False,
            "upstreamCodeEmbedded": False,
            "runtimeFamily": family,
            "input": input_contract,
            "identity": identity,
            "requests": contracts,
            "extractedRouteCount": len(extracted_routes),
            "executableRouteCount": len(model_routes),
        }
        raw_knowledge["recognizedContract"] = recognition
        row["model"] = model
        row["knowledge"] = raw_knowledge
        enriched += 1

        strategy = str(model.get("strategy") or "unknown").strip().casefold()
        executable = bool(model.get("apiRecipe"))
        kinds = {route_kind(str(route)) for route in model_routes}
        if strategy != "quarantined" and not executable:
            executable = bool({"api", "search", "detail", "player", "source", "episode-index"} & kinds) and bool(
                model.get("knownSite") or model.get("officialSite") or model.get("officialHub") or model.get("officialApi") or model.get("fixedApi") or model.get("origins")
            )
        if strategy != "quarantined" and not executable:
            failures.append(
                f"{provider_id}:{strategy}:family={model.get('sourceRuntimeFamily','unknown')}:routes={sorted(kinds)}"
            )

    if failures:
        raise AssertionError("static source plan remains unresolved: " + "; ".join(failures))

    payload["contractRecognition"] = {
        "schemaVersion": 2,
        "method": "static-source-aware-provider-contract-recognition",
        "upstreamCodeExecuted": False,
        "upstreamCodeEmbedded": False,
        "providersRecognized": enriched,
    }

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
        "PROVIDER_CONTRACT_RECOGNITION_OK "
        f"providers={len(providers)} recognized={enriched} fetched_modules={fetched_modules} "
        f"request_contracts={recognized_requests} pruned_routes={pruned_routes} "
        f"corrected_families={corrected_families} routeful={routeful} familyful={familyful} "
        "upstream_code_executed=false upstream_code_embedded=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
