#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
health_check = ROOT / "scripts" / "health_check.mjs"
deep_loop = ROOT / "scripts" / "deep_repair_loop.py"

health_text = health_check.read_text(encoding="utf-8")
health_old = "const concurrency = Math.max(1, Number(config.concurrency || 4));"
health_new = """function configuredConcurrency() {
  const fallback = Number(config.concurrency || 4);
  const requested = Number(process.env.NUVIO_HEALTH_CONCURRENCY || fallback);
  if (!Number.isFinite(requested)) return Math.max(1, Math.min(8, Math.round(fallback || 4)));
  return Math.max(1, Math.min(8, Math.round(requested)));
}

const concurrency = configuredConcurrency();"""
if health_new not in health_text:
    if health_old not in health_text:
        raise SystemExit("health_check concurrency anchor missing")
    health_text = health_text.replace(health_old, health_new, 1)
health_check.write_text(health_text, encoding="utf-8")

deep_text = deep_loop.read_text(encoding="utf-8")
deep_old = """    env = os.environ.copy()\n    env.update(\n"""
deep_new = """    env = os.environ.copy()\n    # Deep validation is network-bound. Six workers materially reduce wall time\n    # while remaining bounded; callers can lower/raise it explicitly (health\n    # check itself clamps the value to 1..8). Quick/availability modes are not\n    # routed through this loop and retain the repository default concurrency.\n    env.setdefault(\"NUVIO_HEALTH_CONCURRENCY\", \"6\")\n    env.update(\n"""
if 'env.setdefault("NUVIO_HEALTH_CONCURRENCY", "6")' not in deep_text:
    if deep_old not in deep_text:
        raise SystemExit("deep repair environment anchor missing")
    deep_text = deep_text.replace(deep_old, deep_new, 1)
deep_loop.write_text(deep_text, encoding="utf-8")

checks = {
    "health env override": "process.env.NUVIO_HEALTH_CONCURRENCY" in health_text,
    "health bounded max": "Math.min(8" in health_text,
    "deep default six": 'env.setdefault("NUVIO_HEALTH_CONCURRENCY", "6")' in deep_text,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("deep concurrency migration verification failed: " + ", ".join(failed))

print("bounded deep concurrency migration applied: deep default=6, explicit override=1..8, quick/default unchanged")
