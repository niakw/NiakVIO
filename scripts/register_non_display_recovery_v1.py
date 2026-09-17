#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
PROVIDERS = {
    "animesama-co": {
        "script": "scripts/provider_patches/animesamaco_nondisplay_runtime_v1.py",
        "base": "https://animesama.co"
    },
    "animevostfr": {
        "script": "scripts/provider_patches/animevostfr_nondisplay_runtime_v1.py",
        "base": "https://v2.animevostfr.org"
    },
    "coflix": {
        "script": "scripts/provider_patches/coflix_nondisplay_runtime_v1.py",
        "base": "https://coflix.wiki"
    },
    "neko-sama": {
        "script": "scripts/provider_patches/neko_sama_nondisplay_runtime_v1.py",
        "base": "https://animes-sama.su"
    },
    "sekai": {
        "script": "scripts/provider_patches/sekai_nondisplay_runtime_v1.py",
        "base": "https://sekai.one"
    },
    "voiranime-rip": {
        "script": "scripts/provider_patches/voiranime_rip_nondisplay_runtime_v1.py",
        "base": "https://voiranime.rip"
    }
}


def apply_document(doc: dict[str, Any]) -> list[str]:
    patches = doc.setdefault("provider_patches", {})
    changed: list[str] = []
    for provider, spec in PROVIDERS.items():
        row = patches.get(provider)
        if not isinstance(row, dict):
            raise ValueError(f"missing provider patch row: {provider}")
        lego = str(spec["script"])
        scripts = [x for x in row.setdefault("provider_lego_scripts", []) if x != "scripts/provider_patches/non_display_recovery_runtime_v1.py"]
        if lego not in scripts:
            scripts.append(lego)
            changed.append(provider)
        row["provider_lego_scripts"] = scripts
        options = row.setdefault("provider_lego_options", {})
        options.pop("scripts/provider_patches/non_display_recovery_runtime_v1.py", None)
        wanted = {"provider": provider, "base": spec["base"], "max_streams": 4}
        if options.get(lego) != wanted:
            options[lego] = wanted
            if provider not in changed:
                changed.append(provider)

    coflix = patches["coflix"]
    if coflix.get("official_site") != "https://coflix.wiki":
        coflix["official_site"] = "https://coflix.wiki"
        if "coflix" not in changed:
            changed.append("coflix")
    for key in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
        mapping = coflix.get(key)
        if not isinstance(mapping, dict):
            continue
        before = dict(mapping)
        mapping.pop("coflix.wiki", None)
        for host in list(mapping):
            if host.startswith("coflix.") and host != "coflix.wiki":
                mapping[host] = "coflix.wiki"
        if mapping != before and "coflix" not in changed:
            changed.append("coflix")

    sekai = patches["sekai"]
    if sekai.get("official_site") != "https://sekai.one":
        sekai["official_site"] = "https://sekai.one"
        if "sekai" not in changed:
            changed.append("sekai")
    return changed


def validate_document(doc: dict[str, Any]) -> None:
    patches = doc.get("provider_patches") or {}
    for provider, spec in PROVIDERS.items():
        row = patches.get(provider)
        if not isinstance(row, dict):
            raise AssertionError(provider)
        lego = str(spec["script"])
        if lego not in (row.get("provider_lego_scripts") or []):
            raise AssertionError(f"{provider}: recovery Lego missing")
        options = row.get("provider_lego_options") or {}
        if (options.get(lego) or {}).get("base") != spec["base"]:
            raise AssertionError(f"{provider}: recovery base drift")
    coflix = patches["coflix"]
    if coflix.get("official_site") != "https://coflix.wiki":
        raise AssertionError("coflix current authority drift")
    for key in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
        mapping = coflix.get(key)
        if isinstance(mapping, dict) and mapping.get("coflix.wiki") not in (None, "coflix.wiki"):
            raise AssertionError(f"coflix.wiki stale rewrite remains in {key}")
    if patches["sekai"].get("official_site") != "https://sekai.one":
        raise AssertionError("sekai current authority drift")


def main() -> None:
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(doc)
    validate_document(doc)
    PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("NON_DISPLAY_RECOVERY_REGISTERED providers=" + ",".join(sorted(PROVIDERS)) + " changed=" + ",".join(sorted(changed)))


if __name__ == "__main__":
    main()
