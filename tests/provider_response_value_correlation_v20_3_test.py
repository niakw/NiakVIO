#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_response_value_correlation_v20_3.py"

spec = importlib.util.spec_from_file_location("v203", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V20.3 migration")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# The migration is intentionally idempotent and runs after the existing repair
# chain. Running it here gives the contract test the exact composed source shape
# used by the live targeted workflow.
module.patch_worker()
module.patch_proof()
module.patch_recovery()
module.patch_materializer()
module.patch_base()
module.validate_worker()
module.validate_proof()
module.validate_recovery()
module.validate_materializer()
module.validate_base()

proof = module.PROOF.read_text(encoding="utf-8")
base = module.BASE.read_text(encoding="utf-8")

required_proof = (
    "PROVIDER_RESPONSE_VALUE_CORRELATION_V20_3",
    "def _urlencoded_text_body_spec",
    "urllib.parse.parse_qsl",
    '"application/x-www-form-urlencoded" in content_type',
    'spec["bodyKind"] = "form"',
    'spec["body"] = form_body',
)
for needle in required_proof:
    assert needle in proof, needle

# Generic reconstruction proof for a French-Manga-shaped request: the decoded
# title must become {query}, while static pagination remains literal. The test is
# deliberately provider-name/host independent.
namespace: dict[str, object] = {}
exec(
    "import urllib.parse\n"
    "def canonical(value): return str(value or '').strip().casefold()\n"
    "def unique(values, limit=256):\n"
    " out=[]\n"
    " for raw in values:\n"
    "  value=str(raw or '').strip()\n"
    "  if value and value not in out: out.append(value)\n"
    "  if len(out)>=limit: break\n"
    " return out\n"
    "PROVIDER_VALUE_KEYS={'id','slug'}\n"
    "BODY_TITLE_KEYS={'q','query','search','title','keyword','story','name'}\n"
    "BODY_SEASON_KEYS={'s','season','season_number','seasonid','season_id'}\n"
    "BODY_EPISODE_KEYS={'e','ep','episode','episode_number','episodeid','episode_id'}\n"
    "BODY_MEDIA_KEYS={'type','mediatype','media_type','media','category','kind'}\n"
    "BODY_TMDB_KEYS={'id','tmdb','tmdbid','tmdb_id','movie','tv'}\n"
    "BODY_YEAR_KEYS={'year','releaseyear','release_year'}\n"
    "SEMANTIC_TYPES={'movie','tv','anime'}\n"
    + proof[proof.index("def _request_scalar_placeholder("):proof.index("def derive_request_spec(")]
    + proof[proof.index("def _urlencoded_text_body_spec("):proof.index("def derive_request_spec(")],
    namespace,
)
fixture = {
    "title": "Jujutsu Kaisen",
    "aliases": [],
    "tmdbId": "95479",
    "mediaType": "anime",
    "season": 1,
    "episode": 1,
}
body, substitutions, residue = namespace["_urlencoded_text_body_spec"](
    "query=Jujutsu%20Kaisen&page=1", fixture, set()
)
assert residue == [], residue
assert body == {"query": "{query}", "page": "1"}, body
assert any(row.get("placeholder") == "{query}" for row in substitutions), substitutions

# The Python DATA projection must retain both provider-value identity forms.
assert "NIAKVIO_PROVIDER_RESPONSE_VALUE_PROJECTION_V20_3" in base
assert '"{slug}" in str(step.get("route") or "")' in base
assert 'and "{id}" in str(step.get("route") or "")\n' not in base

print("provider response-value correlation V20.3 tests passed")
