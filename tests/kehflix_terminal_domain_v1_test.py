#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_kehflix_terminal_domain_v1 as k


overrides = {
    "provider_patches": {
        "kehflix": {
            "official_site": "https://kehflix.lol",
            "official_hub": "https://kehflix.wiki/",
            "domain_substitutions": {"kehflix.wiki": "kehflix.lol"},
            "runtime_domain_replacements": {"kehflix.wiki": "kehflix.lol"},
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

assert patch["official_site"] == "https://kehflix.wiki"
assert patch["domain_substitutions"] == {"kehflix.lol": "kehflix.wiki"}
assert patch["runtime_domain_replacements"] == {"kehflix.lol": "kehflix.wiki"}
assert model["officialSite"] == "https://kehflix.wiki"
assert model["knownSite"] == "https://kehflix.wiki"
assert model["domainSubstitutions"] == {"kehflix.lol": "kehflix.wiki"}
assert model["origins"][0] == "https://kehflix.wiki"
assert model["origins"][1] == "https://kehflix.com"
assert patch["terminal_domain_proof"]["reverifiedAt"] == "2026-09-14"

print("kehflix terminal-domain canonicalization test passed")
