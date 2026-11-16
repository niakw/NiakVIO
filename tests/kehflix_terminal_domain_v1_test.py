#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_kehflix_terminal_domain_v1 as k


historical_proof = {
    "schemaVersion": 2,
    "observedAt": "2026-09-07",
    "reverifiedAt": "2026-09-14",
    "authority": "official-hub-live-path-proof",
    "terminal": "kehflix.wiki",
    "alternateLiveTerminal": "kehflix.com",
}
overrides = {
    "provider_patches": {
        "kehflix": {
            "official_site": "https://kehflix.lol",
            "official_hub": "https://kehflix.wiki/",
            "domain_substitutions": {"kehflix.wiki": "kehflix.lol"},
            "runtime_domain_replacements": {"kehflix.wiki": "kehflix.lol"},
            "terminal_domain_proof": copy.deepcopy(historical_proof),
        }
    }
}
knowledge = {
    "providers": {
        "kehflix": {
            "model": {
                "officialSite": "https://kehflix.lol",
                "knownSite": "https://kehflix.lol",
                "officialHub": "https://kehflix.wiki/",
                "domainSubstitutions": {"kehflix.wiki": "kehflix.lol"},
                "origins": ["https://kehflix.lol"],
                "observedUrls": ["https://kehflix.lol"],
                "routes": [
                    "/title/tv/{id}-{slug}",
                    "/api/streams/episode?id&season&episode&k",
                ],
            }
        }
    }
}

assert k.patch_overrides(overrides) is True
assert k.patch_knowledge(knowledge) is True
k.validate(overrides, knowledge)

patch = overrides["provider_patches"]["kehflix"]
model = knowledge["providers"]["kehflix"]["model"]

assert patch["official_site"] == "https://kehflix.com"
assert patch["official_hub"] == "https://kehflix.wiki/"
assert patch["domain_substitutions"] == {
    "kehflix.lol": "kehflix.com",
    "kehflix.wiki": "kehflix.com",
}
assert patch["runtime_domain_replacements"] == {
    "kehflix.lol": "kehflix.com",
    "kehflix.wiki": "kehflix.com",
}
assert patch["terminal_domain_proof"] == historical_proof
assert model["officialSite"] == "https://kehflix.com"
assert model["knownSite"] == "https://kehflix.com"
assert model["officialHub"] == "https://kehflix.wiki/"
assert model["domainSubstitutions"] == {
    "kehflix.lol": "kehflix.com",
    "kehflix.wiki": "kehflix.com",
}
assert model["origins"][0] == "https://kehflix.com"
assert model["origins"][1] == "https://kehflix.wiki"

print("kehflix terminal-domain current-authority test passed")
