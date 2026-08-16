#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_language_manifests", ROOT / "scripts" / "generate_language_manifests.py"
)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def bundle(root: Path, name: str, source: str) -> dict:
    providers = root / "providers"
    providers.mkdir(parents=True, exist_ok=True)
    path = providers / f"{name}.js"
    path.write_text(source, encoding="utf-8")
    return {
        "id": name,
        "name": name,
        "filename": f"providers/{name}.js",
        "enabled": True,
    }


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)

    fr_domain = bundle(root, "fr-domain", 'const BASE = "https://cinema-exemple.fr/api";')
    assert module.infer_french_from_domain_or_homepage(
        fr_domain, root=root, homepage_fetcher=lambda _url: ""
    ) is True

    html_lang = bundle(root, "html-lang", 'const BASE = "https://cinema-example.com/api";')
    assert module.infer_french_from_domain_or_homepage(
        html_lang,
        root=root,
        homepage_fetcher=lambda _url: '<html lang="fr-FR"><body>Accueil</body></html>',
    ) is True

    vf_homepage = bundle(root, "vf-homepage", 'const BASE = "https://example.net/api";')
    assert module.infer_french_from_domain_or_homepage(
        vf_homepage,
        root=root,
        homepage_fetcher=lambda _url: "Films en streaming VF — regarder les épisodes",
    ) is True

    weak_homepage = bundle(root, "weak-homepage", 'const BASE = "https://example.org/api";')
    assert module.infer_french_from_domain_or_homepage(
        weak_homepage,
        root=root,
        homepage_fetcher=lambda _url: "Watch films online",
    ) is False

    source = {
        "name": "test",
        "version": "1.0.0",
        "scrapers": [fr_domain],
    }
    vf = module.build_manifest(
        source,
        {"fr-domain": "other"},
        {"vf"},
        "VF uniquement",
        root=root,
        homepage_fetcher=lambda _url: "",
    )
    assert [row["id"] for row in vf["scrapers"]] == ["fr-domain"]

    # Explicit non-French metadata must never be overridden by a French-looking domain.
    explicit_en = dict(fr_domain)
    explicit_en["id"] = "explicit-en"
    explicit_en["contentLanguage"] = ["en"]
    vf = module.build_manifest(
        {"name": "test", "version": "1.0.0", "scrapers": [explicit_en]},
        {"explicit-en": "other"},
        {"vf"},
        "VF uniquement",
        root=root,
        homepage_fetcher=lambda _url: '<html lang="fr">VF</html>',
    )
    assert vf["scrapers"] == []

    # Concrete observed non-VF language also wins over fallback evidence.
    observed_en = dict(fr_domain)
    observed_en["id"] = "observed-en"
    vf = module.build_manifest(
        {"name": "test", "version": "1.0.0", "scrapers": [observed_en]},
        {"observed-en": "en"},
        {"vf"},
        "VF uniquement",
        root=root,
        homepage_fetcher=lambda _url: '<html lang="fr">VF</html>',
    )
    assert vf["scrapers"] == []

assert module.domain_suggests_french("example.fr") is True
assert module.domain_suggests_french("french-stream.example") is True
assert module.domain_suggests_french("example.com") is False
assert module.homepage_suggests_french('<html lang="fr">') is True
assert module.homepage_suggests_french("VF films") is True
assert module.homepage_suggests_french("Watch movies") is False

print("domain/homepage language fallback tests passed")
