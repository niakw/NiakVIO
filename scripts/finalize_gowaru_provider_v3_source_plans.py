#!/usr/bin/env python3
"""Finalize Gowaru Provider v3 DATA from the pinned provider-local src tree.

The upstream JavaScript is read strictly as static knowledge.  It is never
executed, bundled, copied into provider output, or used as ProviderBase bytes.
Observable request/path shapes are normalized into NiakVIO placeholders and a
small runtime-family label consumed by the common ProviderBase reader.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
GOWARU_REF = "c3ce6f43a1ba8ccf2f3838b5cd9db40745c33fa2"
RAW_ROOT = f"https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/{GOWARU_REF}/src"
MODULES = ("config.js", "extractor.js", "http.js", "index.js")
USER_AGENT = "NiakVIO-Gowaru-Static-Plan/1"

TEMPLATE_RE = re.compile(r"`([^`]{1,1600})`", re.S)
QUOTED_ROUTE_RE = re.compile(r"[\"']((?:https?://|/)[^\"'\r\n]{1,900})[\"']", re.I)
FULL_URL_RE = re.compile(r"https?://[^\s\"'`<>)]+", re.I)
EXPR_RE = re.compile(r"\$\{([^{}]{1,220})\}")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def fetch(provider_id: str, module: str) -> str:
    url = f"{RAW_ROOT}/{provider_id}/{module}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/javascript,text/plain,*/*"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        data = response.read(2_000_000)
    if not data:
        raise ValueError("empty source")
    text = data.decode("utf-8", errors="ignore")
    if text.lstrip().casefold().startswith(("<!doctype html", "<html")):
        raise ValueError("HTML instead of JavaScript")
    return text


def placeholder(expression: str) -> str:
    value = re.sub(r"\s+", "", expression).casefold()
    for prefix in ("encodeuricomponent(", "decodeuricomponent("):
        if prefix in value:
            value = value.split(prefix, 1)[1].rstrip(")")
    if any(token in value for token in ("tmdbid", "tmdb_id", "tmdb.id")):
        return "{tmdbId}"
    if any(token in value for token in ("imdbid", "imdb_id", "imdb.id")):
        return "{imdbId}"
    if "season" in value or "saison" in value:
        return "{season}"
    if any(token in value for token in ("episode", "epnum", "episodenum", "targetep")):
        return "{episode}"
    if any(token in value for token in ("query", "search", "title", "cleantitle", "keyword", "sanitized")):
        return "{query}"
    if any(token in value for token in ("slug", "permalink")):
        return "{slug}"
    if any(token in value for token in ("mediatype", "media_type", "transporttype", "type")):
        return "{media}"
    if re.search(r"(?:^|[.\[(])(?:news|anime|series|movie|provider)?id(?:$|[.\])])", value) or value.endswith("id"):
        return "{id}"
    # Base URL expressions are deliberately erased; the common reader supplies
    # trusted origins from Provider DATA.
    if any(token in value for token in ("base_url", "baseurl", "site.base", "config.base")):
        return ""
    return ""


def normalize_route(raw: str) -> str | None:
    value = str(raw or "").strip().replace("\\/", "/")
    if not value:
        return None
    value = EXPR_RE.sub(lambda m: placeholder(m.group(1)), value)

    # A template commonly starts with ${BASE_URL}; after static substitution it
    # is now a relative path.  Full URLs are reduced to path/query DATA because
    # the origin is already persisted separately.
    if value.startswith(("http://", "https://")):
        match = re.match(r"https?://[^/]+(.*)$", value, re.I | re.S)
        value = match.group(1) if match else ""
    if not value.startswith("/"):
        first = value.find("/")
        if first >= 0:
            value = value[first:]
    value = value.strip().rstrip(";,)]}")
    if not value.startswith("/") or value == "/":
        return None

    # Normalize a handful of literal JS artifacts without guessing provider
    # semantics. Unknown expressions were erased above rather than executed.
    value = re.sub(r"\s+", "", value)
    value = value.replace("&&", "&")
    value = value.replace("{query}{query}", "{query}")
    if len(value) > 900:
        return None
    low = value.casefold()
    if any(token in low for token in ("q=ponyfill", "/license", "lodash.com", "openjsf.org", "underscorejs.org", "npms.io")):
        return None
    if "${" in value or "encodeuricomponent(" in low:
        return None
    return value


def extract_routes(text: str) -> list[str]:
    raw_values: list[str] = []
    raw_values.extend(TEMPLATE_RE.findall(text))
    raw_values.extend(QUOTED_ROUTE_RE.findall(text))
    raw_values.extend(FULL_URL_RE.findall(text))

    # Also recover URL expressions whose template starts with a BASE variable;
    # the template regex already has the full body, so no JS evaluation occurs.
    routes: list[str] = []
    for raw in raw_values:
        route = normalize_route(raw)
        if not route or route in routes:
            continue
        if not re.search(
            r"\{(?:query|slug|id|tmdbId|imdbId|season|episode|media)\}"
            r"|[?&](?:s|q|query|search|story|keyword|newsId|id)="
            r"|/(?:api|engine|template-php|search|recherche|anime|animes|movie|movies|film|films|"
            r"serie|series|voir-series|episode|saison|season|saga|catalogue|watch|player|embed|stream|hls)(?:[/?#.-]|$)",
            route,
            re.I,
        ):
            continue
        routes.append(route)
        if len(routes) >= 160:
            break
    return routes


def infer_family(text: str, routes: list[str]) -> str:
    low = text.casefold()
    joined = "\n".join(routes).casefold()
    if "playepisode(" in low and "controller.php?mod=playepisode" in low:
        return "dle-playepisode-form"
    if "episodesdata.js" in low and "saga-" in low and "episodehd" in low:
        return "slug-saga-inline-media"
    if "full-story.php" in low and "ep-item" in low and "content_player_" in low:
        return "dle-full-story"
    if "postsearch(" in low and "template-php/defaut/fetch.php" in low:
        return "catalogue-form-html-embed"
    if "/api/search" in low and ("slug" in low or "permalink" in low):
        return "catalogue-json-html-detail"
    if re.search(r"[?&]s=", joined) and "/episode/" in low:
        return "wordpress-search-episode"
    if "story=" in joined and ("cheerio" in low or "extractstreams" in low):
        return "dle-search-html"
    if "episodes.js" in low and "/catalogue/" in low:
        return "catalogue-episodes-js"
    if "/api/streams/episode" in low and "/player" in low:
        return "signed-player-api"
    if "/stream/movie/" in low and "/stream/series/" in low:
        return "stremio-json"
    if re.search(r"[?&](?:s|q|query|story)=", joined) and ("iframe" in low or "resolveStream".casefold() in low):
        return "catalogue-html-embed"
    if routes and "cheerio" in low:
        return "catalogue-html"
    return "unknown"


def merge(target: list[str], values: list[str], limit: int) -> list[str]:
    out = [str(value) for value in target if str(value).strip()]
    for value in values:
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out[:limit]


def has_gowaru_source(row: dict[str, Any]) -> tuple[bool, str]:
    for source in row.get("sources") or []:
        if not isinstance(source, dict):
            continue
        if str(source.get("source") or "").strip() == "gowaru":
            upstream_id = str(source.get("upstreamId") or "").strip()
            return True, upstream_id
    return False, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    args = parser.parse_args()
    path = args.knowledge.resolve()
    payload = load(path)
    providers = payload.get("providers")
    if not isinstance(providers, dict) or len(providers) != 96:
        raise ValueError("expected durable knowledge for exactly 96 providers")

    gowaru_count = 0
    source_modules = 0
    family_count = 0
    route_count = 0
    missing_source: list[str] = []

    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        is_gowaru, upstream_id = has_gowaru_source(row)
        if not is_gowaru:
            continue
        gowaru_count += 1
        upstream_id = upstream_id or provider_id
        chunks: list[str] = []
        for module in MODULES:
            try:
                chunks.append(fetch(upstream_id, module))
                source_modules += 1
            except (urllib.error.URLError, TimeoutError, ValueError, OSError):
                continue
        if not chunks:
            missing_source.append(provider_id)
            continue

        text = "\n".join(chunks)
        routes = extract_routes(text)
        family = infer_family(text, routes)
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        knowledge = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}
        model["routes"] = merge(model.get("routes") or [], routes, 160)
        knowledge["routes"] = merge(knowledge.get("routes") or [], routes, 192)
        knowledge["routeFragments"] = merge(knowledge.get("routeFragments") or [], routes, 192)

        # Strong provider-local family evidence supersedes a generic family label.
        if family != "unknown":
            model["sourceRuntimeFamily"] = family
            knowledge["runtimeFamily"] = family
            family_count += 1
        model["sourceKnowledgeRef"] = GOWARU_REF
        row["model"] = model
        row["knowledge"] = knowledge
        route_count += len(routes)

    if missing_source:
        raise AssertionError("missing pinned Gowaru src modules for: " + ",".join(sorted(missing_source)))

    payload["gowaruSourceRef"] = GOWARU_REF
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_V3_GOWARU_SOURCE_PLANS_OK "
        f"providers={gowaru_count} modules={source_modules} families={family_count} routes={route_count} "
        f"ref={GOWARU_REF} upstream_code_executed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
