#!/usr/bin/env python3
"""Project the currently live Kehflix terminal into structured Provider DATA.

Live proof established that kehflix.lol redirects every detail path to the
kehflix.com root, while kehflix.wiki and kehflix.com preserve the requested
catalogue path. kehflix.wiki is the canonical runtime terminal; kehflix.com is
kept as an alternate live terminal. The redirect-only .lol host must never be
the target of a substitution from the canonical .wiki host.
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
ALTERNATE = "kehflix.com"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: object required")
    return value


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonicalize_mapping(raw: object) -> dict[str, str]:
    mapping = dict(raw) if isinstance(raw, dict) else {}
    # Historical bad DATA inverted the proven direction and produced
    # kehflix.wiki -> kehflix.lol. Remove any mapping *from* the canonical
    # terminal before installing the one safe redirect-only -> terminal rule.
    mapping.pop(NEW, None)
    mapping[OLD] = NEW
    return dict(sorted((str(k), str(v)) for k, v in mapping.items() if str(k).strip() and str(v).strip()))


def patch_overrides(value: dict) -> bool:
    patches = value.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("kehflix"), dict):
        raise AssertionError("provider_patches.kehflix missing")
    patch = patches["kehflix"]
    before = json.dumps(patch, ensure_ascii=False, sort_keys=True)
    patch["official_site"] = TERMINAL
    patch["official_hub"] = TERMINAL + "/"
    patch["domain_substitutions"] = canonicalize_mapping(patch.get("domain_substitutions"))
    patch["runtime_domain_replacements"] = canonicalize_mapping(patch.get("runtime_domain_replacements"))
    patch["terminal_domain_proof"] = {
        "schemaVersion": 2,
        "observedAt": "2026-09-07",
        "reverifiedAt": "2026-09-14",
        "authority": "official-hub-live-path-proof",
        "terminal": NEW,
        "alternateLiveTerminal": ALTERNATE,
        "rejectedRedirectOnly": OLD,
        "pathRetentionFixtures": ["interstellar-2014", "house-of-the-dragon-s03e01"],
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
    model["domainSubstitutions"] = canonicalize_mapping(model.get("domainSubstitutions"))
    origins = [str(v).rstrip("/") for v in model.get("origins") or [] if str(v).strip()]
    model["origins"] = list(dict.fromkeys([TERMINAL, f"https://{ALTERNATE}", *origins]))
    observed = [str(v) for v in model.get("observedUrls") or [] if str(v).strip()]
    model["observedUrls"] = list(dict.fromkeys([TERMINAL + "/", f"https://{ALTERNATE}/", *observed]))
    return before != json.dumps(model, ensure_ascii=False, sort_keys=True)


def validate(overrides: dict, knowledge: dict) -> None:
    patch = overrides["provider_patches"]["kehflix"]
    model = knowledge["providers"]["kehflix"]["model"]
    substitutions = patch.get("domain_substitutions") or {}
    replacements = patch.get("runtime_domain_replacements") or {}
    model_substitutions = model.get("domainSubstitutions") or {}
    assert patch.get("official_site") == TERMINAL
    assert patch.get("official_hub") == TERMINAL + "/"
    assert substitutions.get(OLD) == NEW
    assert NEW not in substitutions
    assert replacements.get(OLD) == NEW
    assert NEW not in replacements
    assert model.get("officialSite") == TERMINAL
    assert model.get("knownSite") == TERMINAL
    assert model.get("officialHub") == TERMINAL + "/"
    assert model_substitutions.get(OLD) == NEW
    assert NEW not in model_substitutions
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
        f"changed={str(changed_o or changed_k).lower()} terminal={NEW} alternate={ALTERNATE} old_redirect={OLD}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
