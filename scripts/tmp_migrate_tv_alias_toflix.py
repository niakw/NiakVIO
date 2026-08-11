#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
TV_TEST = ROOT / "tests" / "tv_provider_hardening_test.py"
AUDIT = ROOT / "scripts" / "audit_catalogue_identity_media.py"
FIXTURE_TEST = ROOT / "tests" / "tv_catalogue_fixture_coverage_test.py"

OLD_PUBLIC = "scripts/provider_patches/streamzo_public_catalogue.py"
NEW_PUBLIC = "scripts/provider_patches/streamzo_public_catalogue_v2.py"
OLD_IDENTITY = "scripts/provider_patches/streamzo_source_identity_v2.py"
NEW_IDENTITY = "scripts/provider_patches/streamzo_source_identity_v3.py"
TOFLIX_V1 = "scripts/provider_patches/toflix_explicit_vf_v1.py"
TOFLIX_V2 = "scripts/provider_patches/toflix_explicit_vf_v2.py"


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_script(entry: dict, old: str, new: str):
    scripts = list(entry.get("patch_scripts") or [])
    scripts = [new if item == old else item for item in scripts]
    if new not in scripts:
        scripts.append(new)
    scripts = [item for item in scripts if item != old]
    entry["patch_scripts"] = scripts
    opts = entry.setdefault("patch_script_options", {})
    inherited = dict(opts.pop(old, {}) or {})
    current = dict(opts.get(new, {}) or {})
    inherited.update(current)
    opts[new] = inherited


def main() -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = data["provider_patches"]

    streamzo = patches["streamzo"]
    replace_script(streamzo, OLD_PUBLIC, NEW_PUBLIC)
    replace_script(streamzo, OLD_IDENTITY, NEW_IDENTITY)
    streamzo["patch_script_options"][NEW_PUBLIC].setdefault("base_url", "https://streamzo.fr")
    streamzo["patch_script_options"][NEW_PUBLIC].setdefault("provider_name", "StreamZo")
    streamzo["patch_script_options"][NEW_PUBLIC]["max_aliases"] = 4
    streamzo["patch_script_options"][NEW_IDENTITY].setdefault("base_url", "https://streamzo.fr")
    streamzo["patch_script_options"][NEW_IDENTITY].setdefault("timeout_ms", 6500)

    toflix = patches["toflix"]
    replace_script(toflix, TOFLIX_V1, TOFLIX_V2)
    toflix["patch_script_options"][TOFLIX_V2]["require_french_host"] = True

    write_json(OVERRIDES, data)

    source = TV_TEST.read_text(encoding="utf-8")
    source = source.replace(OLD_IDENTITY, NEW_IDENTITY)
    if "streamzo_public =" not in source:
        source = source.replace(
            "streamzo_identity = 'scripts/provider_patches/streamzo_source_identity_v3.py'\n",
            "streamzo_identity = 'scripts/provider_patches/streamzo_source_identity_v3.py'\nstreamzo_public = 'scripts/provider_patches/streamzo_public_catalogue_v2.py'\n",
        )
        source = source.replace(
            "assert streamzo_identity in streamzo_scripts\n",
            "assert streamzo_public in streamzo_scripts\nassert streamzo_identity in streamzo_scripts\nassert streamzo_scripts.index(streamzo_public) < streamzo_scripts.index(streamzo_identity)\n",
        )
        source = source.replace(
            "identity_source = (ROOT / streamzo_identity).read_text(encoding='utf-8')\n",
            "public_source = (ROOT / streamzo_public).read_text(encoding='utf-8')\nassert 'original_title' in public_source and 'maxAliases' in public_source\nidentity_source = (ROOT / streamzo_identity).read_text(encoding='utf-8')\nassert 'original_title' in identity_source and 'aliases.some' in identity_source\n",
        )
    TV_TEST.write_text(source, encoding="utf-8")

    audit = AUDIT.read_text(encoding="utf-8")
    if '"animated_movie_ninja_3"' not in audit:
        anchor = '    "impossible_movie": {\n'
        fixture = '''    "animated_movie_ninja_3": {\n        "label": "Mon ninja et moi 3",\n        "tmdbId": "1215638",\n        "mediaType": "movie",\n        "title": "Mon ninja et moi 3",\n        "year": 2025,\n        "expectedDurationMinutes": 88,\n    },\n'''
        if anchor not in audit:
            raise SystemExit("audit fixture anchor missing")
        audit = audit.replace(anchor, fixture + anchor, 1)
        # Keep the global audit bounded: exercise the animated/localized title on
        # VF and known identity-sensitive providers, rather than adding another
        # network probe to every movie provider on every deep publication.
        anchor2 = '        if is_vf and "anime" in types:\n            fixture_names.append("vf_mushoku_s01e01")\n'
        replacement2 = anchor2 + '        if "movie" in types and (is_vf or provider_id in SUSPECTS):\n            fixture_names.append("animated_movie_ninja_3")\n'
        if anchor2 not in audit:
            raise SystemExit("audit selection anchor missing")
        audit = audit.replace(anchor2, replacement2, 1)
    AUDIT.write_text(audit, encoding="utf-8")

    coverage = FIXTURE_TEST.read_text(encoding="utf-8")
    additions = [
        "assert '\"animated_movie_ninja_3\"' in source",
        "assert '\"tmdbId\": \"1215638\"' in source",
        "assert '\"title\": \"Mon ninja et moi 3\"' in source",
        "assert 'fixture_names.append(\"animated_movie_ninja_3\")' in source",
    ]
    marker = "\nprint('TV catalogue Revenant/Mushoku fixture coverage tests passed')"
    if additions[0] not in coverage:
        if marker not in coverage:
            raise SystemExit("fixture test print anchor missing")
        coverage = coverage.replace(marker, "\n" + "\n".join(additions) + "\n\nprint('TV catalogue Revenant/Mushoku/animated-movie fixture coverage tests passed')", 1)
    FIXTURE_TEST.write_text(coverage, encoding="utf-8")

    print("TV alias + ToFlix V2 migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
