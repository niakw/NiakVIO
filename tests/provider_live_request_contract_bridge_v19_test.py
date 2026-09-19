#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_live_request_contract_bridge_v19 as v19


def positive(route: str, *, origin: str = "https://provider.example", method: str = "POST", semantic: str = "anime"):
    return {
        "route": route,
        "origin": origin,
        "role": "search",
        "method": method,
        "semanticType": semantic,
        "status": 200,
        "taskStreamCount": 2,
        "taskRawStreamCount": 2,
        "requestSpecReusable": False,
    }


# A current positive POST may borrow an already-sanitized spec only from the
# exact same live origin+route+method.  The sibling may itself be a zero-stream
# fixture: it proves transport shape, while the positive row proves causality.
row = positive("/engine/ajax/search.php")
sibling = {
    **row,
    "taskStreamCount": 0,
    "taskRawStreamCount": 0,
    "requestSpecReusable": True,
    "requestSpec": {
        "method": "POST",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "bodyKind": "form",
        "body": {"query": "{query}", "page": "1"},
    },
}
plans = v19.build_live_search_plans([row, sibling], [])
assert len(plans) == 1, plans
assert plans[0]["requestShapeAuthority"] == "observed-same-request", plans
assert plans[0]["requestSpec"]["body"] == {"query": "{query}", "page": "1"}, plans


# If the current positive body was non-reusable, an exact reviewed/executed
# static contract may provide shape and neutral defaults.  Its hostname cannot
# provide authority: the current live origin owns the plan base.
row = positive("/1:search", origin="https://rotating-worker.example", semantic="tv")
contract = {
    "route": "/1:search",
    "role": "search",
    "method": "POST",
    "bodyFields": ["q", "page_token", "page_index"],
    "bodyDefaults": {"page_token": None, "page_index": 0},
    "jsonEncoded": True,
    "refererRequired": True,
    "executedEvidence": True,
}
plans = v19.build_live_search_plans([row], [contract])
assert len(plans) == 1, plans
plan = plans[0]
assert plan["base"] == "https://rotating-worker.example", plan
assert plan["requestShapeAuthority"] == "reviewed-executed-contract", plan
assert plan["requestSpec"]["method"] == "POST", plan
assert plan["requestSpec"]["bodyKind"] == "json", plan
assert plan["requestSpec"]["body"] == {"q": "{query}", "page_token": None, "page_index": 0}, plan
assert plan["requestSpec"]["headers"]["Referer"] == "https://rotating-worker.example/", plan


# A static contract never creates a route by itself, even if marked executed.
assert v19.build_live_search_plans([], [contract]) == []

# Route/method mismatch remains fail-closed.
wrong_route = dict(contract, route="/other:search")
wrong_method = dict(contract, method="GET")
assert v19.build_live_search_plans([row], [wrong_route, wrong_method]) == []

# Unknown dynamic body fields cannot be guessed.
unknown = dict(contract, bodyFields=["q", "opaque_session"], bodyDefaults={})
assert v19.build_live_search_plans([row], [unknown]) == []

# Fully reusable current proof stays owned by V14 and is not duplicated by V19.
reusable = dict(row, requestSpecReusable=True, requestSpec={"method": "POST", "bodyKind": "json", "body": {"q": "{query}"}})
assert v19.build_live_search_plans([reusable], [contract]) == []

source = (ROOT / "scripts" / "provider_live_request_contract_bridge_v19.py").read_text(encoding="utf-8").casefold()
for forbidden in ("animezey", "french-manga", "animesama", "cineby", "movieblast", "workers.dev"):
    assert forbidden not in source, forbidden

print("provider live request contract bridge V19 tests passed")
