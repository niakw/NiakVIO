#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_override_pipeline.py"


def run_case(source: str, runtime_map: dict[str, str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stage = root / "staging"
        providers = stage / "providers"
        providers.mkdir(parents=True)
        provider_path = providers / "target.js"
        provider_path.write_text(source, encoding="utf-8")
        digest = hashlib.sha256(provider_path.read_bytes()).hexdigest()
        (stage / "candidates.json").write_text(
            json.dumps(
                {
                    "candidates": [
                        {
                            "key": "synthetic:target",
                            "canonical_id": "target",
                            "local_path": "providers/target.js",
                            "sha256": digest,
                            "upstream_sha256": digest,
                            "local_patches": [],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        config = root / "provider-overrides.json"
        config.write_text(
            json.dumps(
                {
                    "domain_replacements": {},
                    "provider_patches": {
                        "target": {
                            "runtime_domain_replacements": runtime_map,
                        }
                    },
                    "patch_profiles": {},
                }
            ),
            encoding="utf-8",
        )
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--stage",
                str(stage),
                "--config",
                str(config),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )


v3 = (
    '"use strict";\n'
    "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
    'const NIAKVIO_PROVIDER_MODEL=Object.freeze({"domainSubstitutions":{"old.example":"new.example"},'
    '"officialSite":"https://new.example"});\n'
)
result = run_case(v3, {"old.example": "new.example"})
assert result.returncode == 0, result.stdout + result.stderr

missing_terminal = (
    '"use strict";\n'
    "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
    'const NIAKVIO_PROVIDER_MODEL=Object.freeze({"officialSite":"https://other.example"});\n'
)
result = run_case(missing_terminal, {"old.example": "new.example"})
assert result.returncode != 0, result.stdout + result.stderr
assert "terminal target" in result.stdout or "terminal target" in result.stderr, result.stdout + result.stderr

legacy = '"use strict"; const endpoint="https://old.example";\n'
result = run_case(legacy, {"old.example": "new.example"})
assert result.returncode != 0, result.stdout + result.stderr
assert "forbidden pre-override value remains" in result.stdout, result.stdout + result.stderr

print("provider v3 override pipeline contract passed")
