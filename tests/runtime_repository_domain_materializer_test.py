#!/usr/bin/env python3
from __future__ import annotations

from scripts.provider_patches.runtime_repository_domain_materializer_v1 import MARKER, apply

REPOSITORY_URL = "https://raw.githubusercontent.com/example/repository/main/domains.json"


def materialize(source: str, function_name: str, value: object) -> str:
    return apply(
        source,
        options={
            "resolver_function": function_name,
            "materialized_value": value,
            "forbidden_urls": [REPOSITORY_URL],
        },
        context={"provider_id": "fixture"},
    )


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

try:
    materialize("const untouched=true;", "missingResolver", "https://example.com")
except ValueError as exc:
    assert "resolver not found" in str(exc)
else:
    raise AssertionError("missing resolver must fail closed")

print("runtime repository domain materializer tests passed: object/list/scalar + fail-closed")
