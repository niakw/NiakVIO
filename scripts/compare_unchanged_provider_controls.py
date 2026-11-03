#!/usr/bin/env python3
"""Observe exact baseline/current bundles without waiving publication gates."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import audit_provider_quick_yield as census
from current_provider_scope import cid

ROOT = Path(__file__).resolve().parents[1]


def git_bytes(ref: str, path: str) -> bytes:
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'], cwd=ROOT)


def published_bytes(manifest: dict, provider: str, ref: str | None) -> tuple[str, bytes]:
    rows = [row for row in manifest.get('scrapers', [])
            if cid(row.get('id')) == provider and row.get('enabled') is True]
    if len(rows) != 1:
        raise ValueError('expected one enabled published provider')
    filename = rows[0]['filename']
    if not re.fullmatch(r'providers/[a-zA-Z0-9_-]+-[0-9a-f]{16}\.js', filename):
        raise ValueError('invalid published provider path')
    data = git_bytes(ref, filename) if ref else (ROOT / filename).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if not filename.endswith(f'-{digest[:16]}.js'):
        raise ValueError('published provider digest mismatch')
    return filename, data


def compare(base_ref: str, providers: set[str], output: Path) -> dict:
    # This observer has no model client. Do not pass billing credentials to Node.
    for key in ('OPENAI_API_KEY', 'NIAKVIO_OPENAI_API_KEY', 'NIAKVIO_ALLOW_PAID_API'):
        os.environ.pop(key, None)
    if not re.fullmatch(r'[0-9a-f]{40}', base_ref):
        raise ValueError('baseline must be an exact commit SHA')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    baseline_manifest = json.loads(git_bytes(base_ref, 'manifest.json'))
    current_manifest = census.load(ROOT / 'manifest.json')
    history = census.load(ROOT / 'automation/provider-census-proof-history.json')
    tasks, count = census.build_tasks(providers, history=history)
    if count != len(providers) or not tasks:
        raise ValueError('unknown or unpublished comparison provider')
    rows = []
    with tempfile.TemporaryDirectory(prefix='niakvio-baseline-controls-') as directory:
        selected = []
        for provider in sorted(providers):
            old_path, old_data = published_bytes(baseline_manifest, provider, base_ref)
            new_path, new_data = published_bytes(current_manifest, provider, None)
            if old_data != new_data:
                raise ValueError(f'{provider}: this observer requires unchanged published bytes')
            baseline_file = Path(directory) / f'{provider}.js'
            baseline_file.write_bytes(old_data)
            selected.append((provider, old_path, new_path, baseline_file,
                             hashlib.sha256(new_data).hexdigest()))

        def observe(item):
            provider, old_path, new_path, baseline_file, digest = item
            observations = []
            for task in (task for task in tasks if task['provider_id'] == provider):
                # Use the same retained-proof-first fixture on both sides.
                fixture = task['fixtures'][0]
                for attempt in (1, 2):
                    for side, filename in (('baseline', str(baseline_file)), ('candidate', new_path)):
                        result = census.run_single({**task, 'filename': filename, 'fixture': fixture},
                                                   timeout_seconds=40)
                        observations.append({
                            'side': side, 'attempt': attempt, 'lane': task['semantic_type'],
                            'fixture': {key: fixture[key] for key in
                                        ('tmdbId', 'mediaType', 'season', 'episode') if key in fixture},
                            'status': result['status'], 'failureStage': result['debug_stage'],
                            'raw': result['raw'], 'playable': result['playable'],
                            'censusVerified': result['verified'],
                            'contradictions': result['contradictions'],
                        })
            return {'provider': provider, 'baselineAsset': old_path, 'candidateAsset': new_path,
                    'bundleSha256': digest, 'publishedBytesUnchanged': True,
                    'observations': observations}

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            rows = list(executor.map(observe, selected))
    report = {'schemaVersion': 1, 'baselineRef': base_ref, 'candidateRef': head,
              'publicationAuthority': False, 'decodedVideoProof': False,
              'providers': rows}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ref', required=True)
    parser.add_argument('--provider', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    providers = set(args.provider)
    if not all(re.fullmatch(r'[a-z0-9-]{1,80}', provider) for provider in providers):
        parser.error('invalid provider id')
    print('UNCHANGED_PROVIDER_CONTROLS=' + json.dumps(
        compare(args.base_ref, providers, args.output), separators=(',', ':')))


if __name__ == '__main__':
    main()
