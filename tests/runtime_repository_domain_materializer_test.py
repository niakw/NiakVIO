#!/usr/bin/env python3
from __future__ import annotations

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

# Context references deliberately use a real configured provider so the test
# proves that resolve_provider_hubs.py -> provider-overrides.json -> patch bytes
# is an actual data path rather than a duplicated constant.
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
assert '"site":"https://www.cineby.at"' in resolved_result
assert '"api":"https://api.speedracelight.com"' in resolved_result

# Zink-style discovery is side-effect based: refreshDomains() historically
# mutated baseUrl rather than returning a registry object. Preserve that API
# shape while removing the repository fetch.
assign_source = f'''let baseUrl="https://old.invalid";
const DOMAINS_JSON_URL="{REPOSITORY_URL}";
function refreshDomains(){{return fetch(DOMAINS_JSON_URL).then(r=>r.json()).then(d=>{{baseUrl=d.zinkmovies}})}}
const keepAssign=true;
'''
assign_result = materialize(
    assign_source,
    "refreshDomains",
    {"$from": "official_site", "fallback": "https://zinkmovies.wtf"},
    provider_id="zinkmovies",
    extra_options={"mode": "assign", "assign_target": "baseUrl"},
)
assert REPOSITORY_URL not in assign_result
assert 'baseUrl="https://zinkmovies.wtf";return Promise.resolve();' in assign_result
assert "const keepAssign=true" in assign_result

try:
    materialize("const untouched=true;", "missingResolver", "https://example.com")
except ValueError as exc:
    assert "resolver not found" in str(exc)
else:
    raise AssertionError("missing resolver must fail closed")

print("runtime repository domain materializer tests passed: object/list/scalar/context/assign + fail-closed")
