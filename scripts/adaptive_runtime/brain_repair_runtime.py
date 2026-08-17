#!/usr/bin/env python3
from __future__ import annotations

"""Bounded production overlay for the ARCHI2 Brain planner transport.

The canonical Brain implementation lives in ``scripts/brain_repair_runtime.py``.
Quick repair imports ``scripts/adaptive_runtime`` first, so this overlay reuses
that implementation and replaces only the planner transport. A malformed or
oversized planner batch is recursively bisected; one irreducible provider can
be deferred without aborting the other provider plans or the full transaction.
"""

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

_BASE_PATH = Path(__file__).resolve().parents[1] / "brain_repair_runtime.py"
_SPEC = importlib.util.spec_from_file_location("_niakvio_brain_base", _BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load canonical Brain runtime: {_BASE_PATH}")
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)

# Preserve the canonical public/internal surface. In particular PLANS and
# RUNTIME_STATE are the exact same mutable objects used by the base wrappers.
for _name in dir(_BASE):
    if _name.startswith("__"):
        continue
    globals().setdefault(_name, getattr(_BASE, _name))


def _deferred_transport_plan(item: dict[str, Any], error_class: str) -> dict[str, Any]:
    candidate = item.get("candidate") if isinstance(item.get("candidate"), dict) else {}
    provider_id = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold()
    return {
        "brainVersion": 0,
        "providerId": provider_id,
        "failureClass": "unknown_failure",
        "signature": None,
        "action": "deferred_retry",
        "exitReason": "planner_transport_isolated",
        "hypotheses": [],
        "allowedProfiles": [],
        "budget": {},
        "fallbackPolicy": "lkg_only_after_repair_budget",
        "coreMutationPolicy": "proposal_only",
        "skillPolicy": {},
        "plannerErrorClass": error_class[:240],
    }


def _run_planner_batch(base_payload: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not items:
        return {}
    payload = dict(base_payload)
    payload["items"] = items
    planner_input = _BASE._strict_json_dumps(payload).encode("ascii")
    try:
        # Verify the exact bytes locally before they cross the Python -> Node
        # boundary. Any later parse failure is therefore a transport concern.
        json.loads(planner_input.decode("ascii"))
        completed = subprocess.run(
            ["node", str(_BASE.PLAN_SCRIPT)],
            cwd=_BASE.ROOT,
            input=planner_input,
            capture_output=True,
            check=True,
            timeout=30,
        )
        parsed = json.loads((completed.stdout or b"{}").decode("utf-8"))
        return {
            str(key): row
            for key, row in (parsed.get("plans") or {}).items()
            if isinstance(row, dict)
        }
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, UnicodeDecodeError, json.JSONDecodeError) as exc:
        if len(items) > 1:
            midpoint = max(1, len(items) // 2)
            plans = _run_planner_batch(base_payload, items[:midpoint])
            plans.update(_run_planner_batch(base_payload, items[midpoint:]))
            return plans
        key = str(items[0].get("key") or "")
        if not key:
            return {}
        if isinstance(exc, subprocess.CalledProcessError):
            detail = _BASE._safe_planner_stderr(exc.stderr)
            error_class = f"planner_exit_{exc.returncode}:{detail or 'empty'}"
        elif isinstance(exc, subprocess.TimeoutExpired):
            error_class = "planner_timeout"
        else:
            error_class = type(exc).__name__
        return {key: _deferred_transport_plan(items[0], error_class)}


def update_plans(registry_path: Path, report: dict[str, Any], mode: str) -> dict[str, dict[str, Any]]:
    registry = _BASE._load_json(registry_path, {})
    candidates = {
        str(row.get("key")): row
        for row in registry.get("candidates") or []
        if isinstance(row, dict) and row.get("key")
    }
    items: list[dict[str, Any]] = []
    for result in report.get("results") or []:
        if not isinstance(result, dict) or not result.get("key"):
            continue
        raw_key = str(result["key"])
        candidate = candidates.get(raw_key)
        if not candidate:
            continue
        parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
        plan_key = parent_key or raw_key
        if parent_key and plan_key in _BASE.PLANS:
            continue
        items.append({
            "key": plan_key,
            "candidate": _BASE._planner_candidate(candidate),
            "result": _BASE._planner_result(result),
            "state": _BASE._public_state(candidate, plan_key),
        })
    if not items:
        return _BASE.PLANS

    base_payload = {
        "mode": mode,
        "policy": _BASE.policy(),
        "learnedSkills": _BASE.learned_skills(),
    }
    # 24 keeps normal stdin payloads well below the failing ~500 KiB batch seen
    # in production while retaining efficient multi-provider planning.
    for start in range(0, len(items), 24):
        _BASE.PLANS.update(_run_planner_batch(base_payload, items[start:start + 24]))
    return _BASE.PLANS


def wrap_run_health(base_run_health: Callable[..., dict[str, Any]], mode: str) -> Callable[..., dict[str, Any]]:
    def _run_health(*, stage: Path, registry_path: Path, output_dir: Path, mode: str = mode, health_check: Path):
        report = base_run_health(
            stage=stage,
            registry_path=registry_path,
            output_dir=output_dir,
            mode=mode,
            health_check=health_check,
        )
        update_plans(registry_path, report, mode)
        return report
    return _run_health
