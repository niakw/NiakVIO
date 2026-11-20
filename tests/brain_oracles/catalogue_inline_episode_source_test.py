#!/usr/bin/env python3
"""Synthetic source-shape proof, upstream-contract mismatch and privacy negatives."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/brain_oracles/catalogue_inline_episode_source.py"
spec = importlib.util.spec_from_file_location("catalogue_episode_oracle", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

inline_html = """<!doctype html><html><script>
var eps1 = ["lien:PRIVATE_TOKEN_123", "lien:PRIVATE_TOKEN_456"];
var epsJeton = "PRIVATE_AUTH";
var epsMeta = {"PRIVATE_TOKEN_123": ["server"]};
var lecteursInfos = {"server": {"nom": "Reader"}};
var languesDispo = ["vostfr", "vf"];
</script></html>"""
inline = mod.classify(200, inline_html)
assert inline["shape"] == "catalogue_inline_token_episode"
assert inline["inlineSlotArrayObserved"] and inline["opaqueLinkTokenObserved"]
assert inline["jetonDeclarationObserved"] and inline["languageListDeclarationObserved"]
assert inline["readerMapDeclarationObserved"]
legacy = mod.classify(200, 'var eps1 = ["https://source.invalid/embed?token=PRIVATE"];')
assert legacy["shape"] == "legacy_external_episode_javascript"
assert legacy["legacyMediaUrlArrayObserved"] and not legacy["opaqueLinkTokenObserved"]
shell = mod.classify(200, "<!doctype html><html><body>catalogue shell</body></html>")
assert shell["shape"] == "script_html_2xx"
assert mod.classify(404, inline_html)["shape"] == "script_http_missing"
assert mod.classify(403, inline_html)["shape"] == "unknown_response_shape"
assert mod.classify(200, '<!doctype html><html><script>var eps1=[];</script></html>')[
    "shape"
] == "script_html_2xx"

declared = mod.current_family(ROOT, "anime-sama")
assert declared["declaredLegacyEpisodeScriptRoutes"] >= 2
assert declared["inlineTokenLegoPresent"] is False
assert declared["currentSiteContractVerified"] is False
candidate = mod.discriminate(inline, declared)
assert candidate["diagnosticFamily"] == "catalogue_inline_token_contract_drift_candidate"
assert candidate["requiresOfficialClientReplay"] is True
assert candidate["candidateMutationAllowed"] is False
assert mod.discriminate(shell, declared)["diagnosticFamily"] == "catalogue_source_contract_unresolved"

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    (root / "provider-overrides.json").write_text(
        json.dumps({"provider_patches": {"demo": {
            "learned_routes": ["/catalogue/{slug}/saison1/vf/episodes.js"],
            "provider_lego_scripts": [],
        }}}),
        encoding="utf-8",
    )
    assert not mod.current_family(root, "demo")["inlineTokenLegoPresent"]

for row in (inline, legacy, shell, declared, candidate):
    serialized = json.dumps(row)
    for sensitive in ("PRIVATE", "source.invalid", "https://", "lien:", "epsJeton"):
        assert sensitive not in serialized, sensitive
    for flag in ("proofAuthority", "publicationAuthority",
                 "nativePlaybackAuthority", "providerMutationAuthority"):
        assert row[flag] is False

try:
    mod.classify(200, "x" * (mod.MAX_BODY_CHARS + 1))
    raise AssertionError("oversized HTML accepted")
except ValueError:
    pass
print("Catalogue inline episode-source schema and privacy oracle passed")
