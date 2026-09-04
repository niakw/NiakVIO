#!/usr/bin/env python3
"""Idempotent Provider v3 source-plan migration.

ProviderBase remains common/clean. Static Learning reads provider-local upstream
source for Gowaru, All-in-One-Nuvio and Yoru when available, while executable
publication stays NiakVIO-owned DATA + Lego/Core.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one migration anchor, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def migrate_sources() -> None:
    path = ROOT / "sources.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    upstreams = data["upstreams"]
    # Gowaru splits one provider across sibling modules. Config/HTTP modules
    # carry current base URLs, headers and route constants that extractor.js
    # alone cannot faithfully describe. Missing optional modules are tolerated
    # by fetch_provider_knowledge_bytes(), so one durable provider-directory
    # plan works for the whole Gowaru catalogue without provider exceptions.
    upstreams["gowaru"]["knowledge_raw_templates"] = [
        "https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/src/{provider_id}/config.js",
        "https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/src/{provider_id}/extractor.js",
        "https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/src/{provider_id}/http.js",
        "https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/src/{provider_id}/index.js",
    ]
    upstreams["aio"]["knowledge_raw_templates"] = [
        "https://raw.githubusercontent.com/NuvioPlugin/All-in-One-Nuvio/refs/heads/main/providers/{provider_id}.js",
        "https://raw.githubusercontent.com/D3adlyRocket/All-in-One-Nuvio/refs/heads/main/providers/{provider_id}.js",
    ]
    upstreams["yoru"]["knowledge_raw_templates"] = [
        "https://raw.githubusercontent.com/yoruix/nuvio-providers/refs/heads/main/providers/{provider_id}.js",
    ]
    write_json(path, data)


def migrate_overrides() -> None:
    path = ROOT / "provider-overrides.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    patches = data.setdefault("provider_patches", {})
    row = patches.setdefault("anime-sama", {})
    row["capability"] = "mixed_embed_resolver"
    row["official_hub"] = "https://anime-sama.wiki/"
    row["official_site"] = "https://anime-sama.to"
    row["published_types"] = ["movie", "anime"]
    row["identity_input"] = {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["title", "year", "mediaType"],
    }
    row["learned_routes"] = [
        "/template-php/defaut/fetch.php",
        "/catalogue/{slug}/saison{season}/{lang}/episodes.js",
        "/catalogue/{slug}/{lang}/episodes.js",
        "/catalogue/{slug}/film/{lang}/episodes.js",
    ]
    legos = [str(v) for v in row.get("provider_lego_scripts") or []]
    lego = "scripts/provider_patches/anime_sama_runtime_v1.py"
    if lego not in legos:
        legos.append(lego)
    row["provider_lego_scripts"] = legos
    options = row.setdefault("provider_lego_options", {})
    options[lego] = {
        "base": "https://anime-sama.to",
        "fallbackBases": ["https://anime-sama.store"],
        "languages": ["vostfr", "vf"],
        "targetStreams": 3,
    }
    substitutions = row.setdefault("domain_substitutions", {})
    for old in ("animes-sama.fr", "anime-sama.store", "anime-sama.fr"):
        substitutions[old] = "anime-sama.to"
    notes = [str(v) for v in row.get("notes") or []]
    note = (
        "Provider v3 runtime is a NiakVIO-owned catalogue/episodes.js Lego derived from the current "
        "upstream contract; upstream JavaScript is not embedded or executed."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    write_json(path, data)


def migrate_discovery() -> None:
    path = ROOT / "scripts" / "discover_candidates.py"
    text = path.read_text(encoding="utf-8")
    # The migration is intentionally replay-safe on the workbench branch.
    if "def fetch_provider_knowledge_bytes(" in text and "def infer_source_runtime_family(" in text:
        if '"sourceRuntimeFamily": str(knowledge.get("runtimeFamily") or "unknown")' not in text:
            raise RuntimeError("discover_candidates.py: partial source-plan migration detected")
        return

    replace_once(
        path,
        '''def safe_fragment(value: str) -> str:\n''',
        '''def fetch_provider_knowledge_bytes(\n    source_cfg: dict[str, Any], provider_id: str, compiled_data: bytes\n) -> tuple[bytes, str]:\n    """Prefer provider-local upstream source over a shared bundled artifact.\n\n    Bundled provider JS can contain common utilities for dozens of unrelated\n    providers. Provider-local source is static knowledge only and is never\n    executed or embedded in the published provider.\n    """\n    templates = source_cfg.get("knowledge_raw_templates")\n    if not isinstance(templates, list) or not templates:\n        return compiled_data, "compiled-provider"\n    chunks: list[bytes] = []\n    urls: list[str] = []\n    for raw in templates[:8]:\n        template = str(raw or "").strip()\n        if not template:\n            continue\n        try:\n            url = template.format(provider_id=provider_id)\n            data = fetch_bytes(url, attempts=1, timeout=12)\n            validate_javascript(data, url)\n            chunks.append(data)\n            urls.append(url)\n        except Exception:\n            continue\n    if not chunks:\n        return compiled_data, "compiled-provider-fallback"\n    banner = ("\\n/* NIAKVIO_STATIC_KNOWLEDGE_SOURCE " + " ".join(urls) + " */\\n").encode("utf-8")\n    return banner.join(chunks), "provider-local-source"\n\n\ndef safe_fragment(value: str) -> str:\n''',
    )
    replace_once(
        path,
        '''def upstream_knowledge(provider_id: str, entry: dict[str, Any], raw_upstream: bytes) -> dict[str, Any]:\n''',
        '''def infer_source_runtime_family(text: str) -> str:\n    low = text.casefold()\n    if "episodes.js" in low and "/catalogue/" in low:\n        return "catalogue-episodes-js"\n    if "/api/streams/episode" in low and "/player" in low:\n        return "signed-player-api"\n    if "/stream/movie/" in low and "/stream/series/" in low:\n        return "stremio-json"\n    if re.search(r"/(?:search|search-bar)[^\\n]{0,200}/stream", low):\n        return "api-search-stream"\n    if re.search(r"/(?:search|recherche)|[?&](?:s|q|query)=", low) and re.search(r"/(?:embed|player|watch)", low):\n        return "catalogue-html-embed"\n    if re.search(r"/(?:api/)?(?:stream|streams|source|sources)[/?]", low):\n        return "tmdb-direct-api"\n    return "unknown"\n\n\ndef upstream_knowledge(provider_id: str, entry: dict[str, Any], raw_upstream: bytes) -> dict[str, Any]:\n''',
    )
    replace_once(
        path,
        '''        "supportedTypes": [str(value) for value in supported or []][:8],\n        "hosts": hosts[:32],\n''',
        '''        "supportedTypes": [str(value) for value in supported or []][:8],\n        "runtimeFamily": infer_source_runtime_family(text),\n        "hosts": hosts[:32],\n''',
    )
    replace_once(
        path,
        '''    overrides: dict[str, Any],\n    *,\n    clean_reconstruction: bool,\n''',
        '''    overrides: dict[str, Any],\n    *,\n    knowledge_upstream: bytes | None = None,\n    clean_reconstruction: bool,\n''',
    )
    replace_once(
        path,
        '''    site = known_site_for_provider(provider_id, raw_upstream, overrides)\n    knowledge = upstream_knowledge(provider_id, entry, raw_upstream)\n''',
        '''    static_bytes = knowledge_upstream if knowledge_upstream is not None else raw_upstream\n    site = known_site_for_provider(provider_id, static_bytes, overrides)\n    knowledge = upstream_knowledge(provider_id, entry, static_bytes)\n''',
    )
    replace_once(
        path,
        '''        "apiRecipe": recipe,\n        "knowledgeRole": "structured-static-observation-only",\n''',
        '''        "apiRecipe": recipe,\n        "sourceRuntimeFamily": str(knowledge.get("runtimeFamily") or "unknown"),\n        "knowledgeRole": "structured-static-observation-only",\n''',
    )
    replace_once(
        path,
        '''                upstream_digest = hashlib.sha256(data).hexdigest()\n                (\n                    seed,\n''',
        '''                upstream_digest = hashlib.sha256(data).hexdigest()\n                knowledge_data, knowledge_source = fetch_provider_knowledge_bytes(\n                    source_cfg, provider_id, data\n                )\n                (\n                    seed,\n''',
    )
    replace_once(
        path,
        '''                    provenance_rows,\n                    overrides,\n                    clean_reconstruction=bool(args.clean_reconstruction),\n''',
        '''                    provenance_rows,\n                    overrides,\n                    knowledge_upstream=knowledge_data,\n                    clean_reconstruction=bool(args.clean_reconstruction),\n''',
    )
    replace_once(
        path,
        '''                        "upstream_code_role": "knowledge-only",\n                        "upstream_code_executed": False,\n                        "upstream_knowledge": knowledge,\n''',
        '''                        "upstream_code_role": "knowledge-only",\n                        "upstream_code_executed": False,\n                        "upstream_knowledge_source": knowledge_source,\n                        "upstream_knowledge": knowledge,\n''',
    )


def migrate_projection() -> None:
    materializer = ROOT / "scripts" / "materialize_provider_v3_all.py"
    materializer_text = materializer.read_text(encoding="utf-8")
    if '"sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown")' not in materializer_text:
        replace_once(
            materializer,
            '''        "apiRecipe": api_recipe,\n        "identityInput": identity_input(patch, routes, api_recipe),\n''',
            '''        "apiRecipe": api_recipe,\n        "sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown"),\n        "identityInput": identity_input(patch, routes, api_recipe),\n''',
        )

    base = ROOT / "scripts" / "provider_base_store.py"
    base_text = base.read_text(encoding="utf-8")
    if '"sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown")' not in base_text:
        replace_once(
            base,
            '''        "apiRecipe": (\n            incoming_model.get("apiRecipe")\n            if isinstance(incoming_model.get("apiRecipe"), dict)\n            else None\n        ),\n        "identityInput": _normalize_identity_input(incoming_model.get("identityInput")),\n''',
            '''        "apiRecipe": (\n            incoming_model.get("apiRecipe")\n            if isinstance(incoming_model.get("apiRecipe"), dict)\n            else None\n        ),\n        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),\n        "identityInput": _normalize_identity_input(incoming_model.get("identityInput")),\n''',
        )


def main() -> int:
    migrate_sources()
    migrate_overrides()
    migrate_discovery()
    migrate_projection()
    print(
        "PROVIDER_V3_SOURCE_PLAN_MIGRATION_OK "
        "upstream-local-source=gowaru,aio,yoru gowaru-modules=config,extractor,http,index "
        "anime-sama=provider-lego replay_safe=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
