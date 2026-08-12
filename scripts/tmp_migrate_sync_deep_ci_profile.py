#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = ROOT / ".github" / "workflows" / "sync.yml"
text = workflow.read_text(encoding="utf-8")

step_anchor = """      # Phase 3: execute provider access, generate provider-agnostic adaptive\n      # candidates for failures, then retest the exact generated JavaScript.\n      - name: Test provider access and repair failed routes\n"""
step_replacement = """      # Phase 3: execute provider access, generate provider-agnostic adaptive\n      # candidates for failures, then retest the exact generated JavaScript.\n      # CI gets bounded extra parallelism in deep mode only; repository defaults\n      # and all validation gates/timeouts remain unchanged.\n      - name: Prepare bounded CI health profile\n        env:\n          NUVIO_VALIDATION_MODE: ${{ steps.resolve-mode.outputs.validation_mode }}\n        run: |\n          python - <<'PY'\n          import json\n          import os\n          from pathlib import Path\n\n          source = Path('health-config.json')\n          target = Path('health-output/ci-health-config.json')\n          config = json.loads(source.read_text(encoding='utf-8'))\n          before = int(config.get('concurrency') or 4)\n          if os.environ.get('NUVIO_VALIDATION_MODE') == 'deep':\n              config['concurrency'] = 6\n          target.parent.mkdir(parents=True, exist_ok=True)\n          target.write_text(json.dumps(config, indent=2, ensure_ascii=False) + '\\n', encoding='utf-8')\n          print(\n              f\"CI health concurrency: {before} -> {config.get('concurrency')} \"\n              f\"for mode={os.environ.get('NUVIO_VALIDATION_MODE')}; policy/timeouts unchanged\"\n          )\n          PY\n\n      - name: Test provider access and repair failed routes\n"""

if "- name: Prepare bounded CI health profile" not in text:
    if step_anchor not in text:
        raise SystemExit("sync deep profile step anchor missing")
    text = text.replace(step_anchor, step_replacement, 1)

env_anchor = """          NUVIO_DNS_PREFLIGHT_RESULTS: health-output/dns-preflight-report.json\n          NUVIO_WORKER_MEMORY_MB: \"1024\"\n"""
env_replacement = """          NUVIO_DNS_PREFLIGHT_RESULTS: health-output/dns-preflight-report.json\n          NUVIO_HEALTH_CONFIG: health-output/ci-health-config.json\n          NUVIO_WORKER_MEMORY_MB: \"1024\"\n"""
if "NUVIO_HEALTH_CONFIG: health-output/ci-health-config.json" not in text:
    if env_anchor not in text:
        raise SystemExit("sync health config env anchor missing")
    text = text.replace(env_anchor, env_replacement, 1)

required = (
    "- name: Prepare bounded CI health profile",
    "config['concurrency'] = 6",
    "NUVIO_HEALTH_CONFIG: health-output/ci-health-config.json",
    "NUVIO_WORKER_MEMORY_MB: \"1024\"",
)
for token in required:
    if token not in text:
        raise SystemExit(f"sync migration verification failed: {token}")

workflow.write_text(text, encoding="utf-8")
print("sync deep CI profile migration applied: deep=6 workers, quick/default unchanged")
