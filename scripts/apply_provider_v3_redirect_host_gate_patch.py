#!/usr/bin/env python3
'''Apply the redirect-aware Provider v3 contract-host repair.

This is intentionally narrow and idempotent. A provider request that starts on a
canonical provider host and follows an HTTP redirect to the provider's current
terminal must remain eligible as provider-chain evidence. officialHub is also
canonical authority and therefore belongs in the contract-host set.
'''
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"

text = TARGET.read_text(encoding="utf-8")
original = text

old_hosts = 'for key in ("knownSite", "officialSite", "officialApi", "fixedApi"):'
new_hosts = 'for key in ("knownSite", "officialSite", "officialHub", "officialApi", "fixedApi"):'
if old_hosts in text:
    text = text.replace(old_hosts, new_hosts, 1)
elif new_hosts not in text:
    raise SystemExit("provider contract host tuple marker not found")

old_fetch = '''def _fetch_on_contract_host(fetch: dict[str, Any], hosts: set[str]) -> bool:
    if not hosts:
        return True
    raw = str(fetch.get("final_url") or fetch.get("url") or "")
    try:
        host = (urllib.parse.urlsplit(raw).hostname or "").casefold()
    except ValueError:
        return False
    return host in hosts
'''
new_fetch = '''def _fetch_on_contract_host(fetch: dict[str, Any], hosts: set[str]) -> bool:
    if not hosts:
        return True

    # Preserve request identity across redirects. A call that was initiated on a
    # canonical provider host may legitimately land on the provider's current
    # terminal domain. Checking only final_url rejected that successful chain and
    # produced false "200 but no declared-type proof" failures.
    for raw in (fetch.get("url"), fetch.get("final_url")):
        value = str(raw or "").strip()
        if not value:
            continue
        try:
            host = (urllib.parse.urlsplit(value).hostname or "").casefold()
        except ValueError:
            continue
        if host in hosts:
            return True
    return False
'''
if old_fetch in text:
    text = text.replace(old_fetch, new_fetch, 1)
elif new_fetch not in text:
    raise SystemExit("_fetch_on_contract_host marker not found")

if text != original:
    TARGET.write_text(text, encoding="utf-8")
    print("PROVIDER_V3_REDIRECT_HOST_GATE_PATCHED changed=true")
else:
    print("PROVIDER_V3_REDIRECT_HOST_GATE_PATCHED changed=false")
