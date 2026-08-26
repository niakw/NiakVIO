#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.provider_patches.runtime_repository_domain_materializer_v1 import MARKER, apply

REPOSITORY_URL = "https://raw.githubusercontent.com/example/repository/main/domains.json"


def materialize(
    source: str,
    function_name: str,
    value: object,
    *,
    provider_id: str = "fixture",
    extra_options: dict[str, object] | None = None,
) -> str:
    options: dict[str, object] = {
        "resolver_function": function_name,
        "materialized_value": value,
        "forbidden_urls": [REPOSITORY_URL],
    }
    options.update(extra_options or {})
    return apply(source, options=options, context={"provider_id": provider_id})


object_source = f'''const DOMAINS_URL="{REPOSITORY_URL}";
function getDomains(){{return fetch(DOMAINS_URL).then(r=>r.json())}}
const keepObject=true;
'''
object_result = materialize(
    object_source,
    "getDomains",
    {
        "cineby": "https://www.cineby.at",
        "speedracelight": "https://api.speedracelight.com",
    },
)
assert REPOSITORY_URL not in object_result
assert MARKER in object_result
assert 'Promise.resolve({"cineby":"https://www.cineby.at","speedracelight":"https://api.speedracelight.com"})' in object_result
assert "const keepObject=true" in object_result

list_source = f'''const DOMAINS_URL="{REPOSITORY_URL}";
function domainCandidates(){{return fetch(DOMAINS_URL).then(r=>r.json()).then(d=>[d.UHDMovies])}}
const keepList=true;
'''
list_result = materialize(list_source, "domainCandidates", ["https://uhdmovies.autos"])
assert REPOSITORY_URL not in list_result
assert 'Promise.resolve(["https://uhdmovies.autos"])' in list_result
assert "const keepList=true" in list_result

scalar_source = f'''const DOMAINS_URL="{REPOSITORY_URL}";
function fetchLatestDomain(){{return fetch(DOMAINS_URL).then(r=>r.json()).then(d=>d["4KHDHub"])}}
const keepScalar=true;
'''
scalar_result = materialize(scalar_source, "fetchLatestDomain", "https://new4.hdhub4u.cl")
assert REPOSITORY_URL not in scalar_result
assert 'Promise.resolve("https://new4.hdhub4u.cl")' in scalar_result
assert "const keepScalar=true" in scalar_result

# Context references deliberately use real configured providers. The expected
# values are read from the same durable routing state written by
# resolve_provider_hubs.py; tests therefore keep following a newly validated
# domain instead of pinning yesterday's terminal URL.
config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
providers = config["provider_patches"]
cineby_site = str(providers["cineby"]["official_site"]).rstrip("/")
cineby_api = str(providers["cineby"]["official_api"]).rstrip("/")
zink_site = str(providers["zinkmovies"]["official_site"]).rstrip("/")

resolved_source = f'''const DOMAINS_URL="{REPOSITORY_URL}";
function getDomains(){{return fetch(DOMAINS_URL).then(r=>r.json())}}
'''
resolved_result = materialize(
    resolved_source,
    "getDomains",
    {
        "site": {"$from": "official_site", "fallback": "https://fallback.invalid"},
        "api": {"$from": "official_api", "fallback": "https://fallback-api.invalid"},
    },
    provider_id="cineby",
)
assert f'"site":{json.dumps(cineby_site)}' in resolved_result
assert f'"api":{json.dumps(cineby_api)}' in resolved_result

# Zink-style discovery is side-effect based: refreshDomains() historically
# mutated baseUrl rather than returning a registry object. Preserve that API
# shape while removing the repository fetch and following the persisted terminal.
assign_source = f'''let baseUrl="https://old.invalid";
const DOMAINS_JSON_URL="{REPOSITORY_URL}";
function refreshDomains(){{return fetch(DOMAINS_JSON_URL).then(r=>r.json()).then(d=>{{baseUrl=d.zinkmovies}})}}
const keepAssign=true;
'''
assign_result = materialize(
    assign_source,
    "refreshDomains",
    {"$from": "official_site", "fallback": "https://fallback.invalid"},
    provider_id="zinkmovies",
    extra_options={"mode": "assign", "assign_target": "baseUrl"},
)
assert REPOSITORY_URL not in assign_result
assert f'baseUrl={json.dumps(zink_site)};return Promise.resolve();' in assign_result
assert "const keepAssign=true" in assign_result

# Idempotent/purified input: when both the historical resolver and its registry
# dependency are already absent there is nothing left to materialize. This is
# the shape used by global-Core fixtures and by providers after purification.
clean_source = "const untouched=true;"
assert materialize(clean_source, "missingResolver", "https://example.com") == clean_source

# Fail closed only when the repository dependency still exists but the expected
# resolver has disappeared/renamed. That is a genuine upstream-shape drift.
try:
    materialize(
        f'const DOMAINS_URL="{REPOSITORY_URL}"; const untouched=true;',
        "missingResolver",
        "https://example.com",
    )
except ValueError as exc:
    assert "resolver not found while registry dependency remains" in str(exc)
else:
    raise AssertionError("missing resolver with live registry dependency must fail closed")

print("runtime repository domain materializer tests passed: object/list/scalar/context/assign/idempotence + fail-closed")
