#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from upstream_lkg import finalize_pending

parser = argparse.ArgumentParser()
parser.add_argument('--pending', type=Path, required=True)
parser.add_argument('--keep-generations', type=int, default=2)
args = parser.parse_args()
result = finalize_pending(args.pending.resolve(), keep_generations=args.keep_generations)
print(f"upstream LKG finalized: sources={result['changed_sources']} manifests={result['manifest_files']} providers={result['provider_files']}")
