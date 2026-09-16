#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/non_display_recovery_runtime_v1.py"
PROVIDERS = {
    "animesama-co": "https://animesama.co",
    "animevostfr": "https://v2.animevostfr.org",
    "coflix": "https://coflix.wiki",
    "neko-sama": "https://animes-sama.su",
    "sekai": "https://sekai.one",
    "voiranime-rip": "https://voiranime.rip",
}


def main() -> None:
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    patches = doc.setdefault("provider_patches", {})
    changed: list[str] = []
    for provider, base in PROVIDERS.items():
        row = patches.get(provider)
        if not isinstance(row, dict):
            raise SystemExit(f"missing provider patch row: {provider}")
        scripts = row.setdefault("provider_lego_scripts", [])
        if LEGO not in scripts:
            scripts.append(LEGO)
            changed.append(provider)
        options = row.setdefault("provider_lego_options", {})
        wanted = {"provider": provider, "base": base, "max_streams": 4}
        if options.get(LEGO) != wanted:
            options[LEGO] = wanted
            if provider not in changed:
                changed.append(provider)

    # Fresh 2026-09 live parity proves that coflix.wiki is the challenge-free
    # current catalogue/API surface. Do not normalize it back to stale .group.
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
        # Historical Coflix terminals can safely converge on the current surface.
        for host in list(mapping):
            if host.startswith("coflix.") and host != "coflix.wiki":
                mapping[host] = "coflix.wiki"
        if mapping != before and "coflix" not in changed:
            changed.append("coflix")

    # Sekai's current transport is page/sitemap based, not the stale /api.php model.
    sekai = patches["sekai"]
    if sekai.get("official_site") != "https://sekai.one":
        sekai["official_site"] = "https://sekai.one"
        if "sekai" not in changed:
            changed.append("sekai")

    PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("NON_DISPLAY_RECOVERY_REGISTERED providers=" + ",".join(sorted(PROVIDERS)) + " changed=" + ",".join(sorted(changed)))


if __name__ == "__main__":
    main()
