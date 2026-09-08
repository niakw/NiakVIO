#!/usr/bin/env python3
"""Project the currently live Kehflix terminal into structured Provider DATA.

Live proof on 2026-09-07 established that kehflix.lol redirects every path to the
kehflix.com root, while kehflix.wiki and kehflix.com both preserve the HOTD detail
path and expose the signed player chain. The official hub host is selected as the
canonical runtime terminal because it returned the richer episodic API proof.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
TERMINAL = "https://kehflix.wiki"
OLD = "kehflix.lol"
NEW = "kehflix.wiki"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: object required")
    return value


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_overrides(value: dict) -> bool:
    patches = value.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("kehflix"), dict):
        raise AssertionError("provider_patches.kehflix missing")
    patch = patches["kehflix"]
    before = json.dumps(patch, ensure_ascii=False, sort_keys=True)
    patch["official_site"] = TERMINAL
    patch["official_hub"] = TERMINAL + "/"
    substitutions = patch.get("domain_substitutions")
    substitutions = dict(substitutions) if isinstance(substitutions, dict) else {}
    substitutions[OLD] = NEW
    patch["domain_substitutions"] = dict(sorted(substitutions.items()))
    replacements = patch.get("runtime_domain_replacements")
    replacements = dict(replacements) if isinstance(replacements, dict) else {}
    replacements[OLD] = NEW
    patch["runtime_domain_replacements"] = dict(sorted(replacements.items()))
    patch["terminal_domain_proof"] = {
        "schemaVersion": 1,
        "observedAt": "2026-09-07",
        "authority": "official-hub-live-path-proof",
        "terminal": NEW,
        "alternateLiveTerminal": "kehflix.com",
        "rejectedRedirectOnly": OLD,
        "fixture": "house-of-the-dragon-s03e01",
        "signedPlayerObserved": True,
        "episodeApiMediaLikeValues": 5,
    }
    return before != json.dumps(patch, ensure_ascii=False, sort_keys=True)


def patch_knowledge(value: dict) -> bool:
    providers = value.get("providers")
    if not isinstance(providers, dict) or not isinstance(providers.get("kehflix"), dict):
        raise AssertionError("static knowledge kehflix row missing")
    row = providers["kehflix"]
    model = row.get("model")
    if not isinstance(model, dict):
        raise AssertionError("static knowledge kehflix.model missing")
    before = json.dumps(model, ensure_ascii=False, sort_keys=True)
    model["officialSite"] = TERMINAL
    model["knownSite"] = TERMINAL
    model["officialHub"] = TERMINAL + "/"
    substitutions = model.get("domainSubstitutions")
    substitutions = dict(substitutions) if isinstance(substitutions, dict) else {}
    substitutions[OLD] = NEW
    model["domainSubstitutions"] = dict(sorted(substitutions.items()))
    origins = [str(v).rstrip("/") for v in model.get("origins") or [] if str(v).strip()]
    model["origins"] = list(dict.fromkeys([TERMINAL, "https://kehflix.com", *origins]))
    observed = [str(v) for v in model.get("observedUrls") or [] if str(v).strip()]
    model["observedUrls"] = list(dict.fromkeys([TERMINAL + "/", "https://kehflix.com/", *observed]))
    return before != json.dumps(model, ensure_ascii=False, sort_keys=True)


def validate(overrides: dict, knowledge: dict) -> None:
    patch = overrides["provider_patches"]["kehflix"]
    model = knowledge["providers"]["kehflix"]["model"]
    assert patch.get("official_site") == TERMINAL
    assert (patch.get("domain_substitutions") or {}).get(OLD) == NEW
    assert model.get("officialSite") == TERMINAL
    assert model.get("knownSite") == TERMINAL
    assert (model.get("domainSubstitutions") or {}).get(OLD) == NEW
    assert "/title/tv/{id}-{slug}" in (model.get("routes") or []), model.get("routes")
    assert "/api/streams/episode?id&season&episode&k" in (model.get("routes") or []), model.get("routes")


def main() -> int:
    overrides = load(OVERRIDES)
    knowledge = load(KNOWLEDGE)
    changed_o = patch_overrides(overrides)
    changed_k = patch_knowledge(knowledge)
    validate(overrides, knowledge)
    if changed_o:
        write(OVERRIDES, overrides)
    if changed_k:
        write(KNOWLEDGE, knowledge)
    print(
        "KEHFLIX_TERMINAL_DOMAIN_V1_OK "
        f"changed={str(changed_o or changed_k).lower()} terminal={NEW} alternate=kehflix.com old_redirect={OLD}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
