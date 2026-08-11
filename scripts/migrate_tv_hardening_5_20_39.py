#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUR = 'scripts/provider_patches/purstream_tv_identity_v3.py'
PAPA = 'scripts/provider_patches/papadustream_anime_tv_v1.py'
PLAY = 'scripts/provider_patches/nuvio_tv_playable_first_v1.py'
STREAMZO_ID = 'scripts/provider_patches/streamzo_source_identity_v2.py'
TOFLIX_VF_V1 = 'scripts/provider_patches/toflix_explicit_vf_v1.py'
TOFLIX_VF = 'scripts/provider_patches/toflix_explicit_vf_v2.py'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def append_patch(cfg: dict, path: str, options: dict | None = None) -> None:
    scripts = cfg.setdefault('patch_scripts', [])
    scripts[:] = [value for value in scripts if value != path]
    scripts.append(path)
    if options is not None:
        cfg.setdefault('patch_script_options', {})[path] = options


def main() -> int:
    overrides_path = ROOT / 'provider-overrides.json'
    overrides = load(overrides_path)
    patches = overrides.setdefault('provider_patches', {})

    pur = patches.setdefault('purstream', {})
    append_patch(pur, PUR, {'duration_tolerance': 0.35, 'timeout_ms': 7000, 'max_probes': 3})

    papa = patches.setdefault('papadustream', {})
    papa['published_types'] = ['movie', 'tv', 'anime']
    append_patch(papa, PAPA, {})

    for provider_id in ('4khdhubnew', 'animezey', 'vegamovies'):
        cfg = patches.setdefault(provider_id, {})
        append_patch(cfg, PLAY, {'max_probes': 6, 'timeout_ms': 6500})

    streamzo = patches.setdefault('streamzo', {})
    scripts = streamzo.setdefault('patch_scripts', [])
    scripts[:] = [value for value in scripts if value not in {STREAMZO_ID, PLAY}]
    scripts.extend([STREAMZO_ID, PLAY])
    opts = streamzo.setdefault('patch_script_options', {})
    opts[STREAMZO_ID] = {'base_url': 'https://streamzo.fr', 'timeout_ms': 6500}
    opts[PLAY] = {'max_probes': 8, 'timeout_ms': 6500}

    # Replace the earlier browser-URL-dependent ToFlix wrapper with V2.  V2 is
    # QuickJS-safe and only propagates FR when the stream itself says VF and the
    # resolved media URL is explicitly on the french.* delivery branch.
    toflix = patches.setdefault('toflix', {})
    toflix_scripts = toflix.setdefault('patch_scripts', [])
    toflix_scripts[:] = [value for value in toflix_scripts if value not in {TOFLIX_VF_V1, TOFLIX_VF}]
    toflix_scripts.append(TOFLIX_VF)
    toflix_opts = toflix.setdefault('patch_script_options', {})
    toflix_opts.pop(TOFLIX_VF_V1, None)
    toflix_opts[TOFLIX_VF] = {'require_french_host': True}

    dump(overrides_path, overrides)

    policy_path = ROOT / 'provider-type-policy.json'
    policy = load(policy_path)
    policy['providers']['papadustream']['supportedTypes'] = ['movie', 'tv', 'anime']
    dump(policy_path, policy)

    for relative in ('manifest.json', 'vf/manifest.json'):
        path = ROOT / relative
        data = load(path)
        found = False
        for row in data.get('scrapers', []):
            if str(row.get('id') or '').casefold() == 'papadustream':
                row['supportedTypes'] = ['movie', 'tv', 'anime']
                found = True
        if not found:
            raise SystemExit(f'PapaDuStream missing from {relative}')
        dump(path, data)

    vf_test_path = ROOT / 'tests' / 'vf_movie_policy_test.py'
    text = vf_test_path.read_text(encoding='utf-8')
    text = text.replace(
        "assert by_id['papadustream']['supportedTypes'] == ['movie', 'tv']\nassert patches['papadustream']['published_types'] == ['movie', 'tv']\nassert type_policy['papadustream']['supportedTypes'] == ['movie', 'tv']",
        "assert by_id['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']\nassert patches['papadustream']['published_types'] == ['movie', 'tv', 'anime']\nassert type_policy['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']",
    )
    vf_test_path.write_text(text, encoding='utf-8')

    package_path = ROOT / 'package.json'
    package = load(package_path)
    command = package['scripts']['test']
    addition = 'python3 tests/tv_provider_hardening_test.py'
    if addition not in command:
        command += ' && ' + addition
    package['scripts']['test'] = command
    dump(package_path, package)

    print('Nuvio TV hardening profiles wired: Purstream identity, Papa anime, playable-first, StreamZo source identity, ToFlix explicit VF v2')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
