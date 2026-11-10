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
import tempfile
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
    requested = str(payload.get("forcePreferredStrategy") or "").strip().casefold()
    # This adapter is Deep's actual planner transport. Keep the explicitly
    # scoped CLI intent that the canonical Brain bound before any health run.
    # An ordinary batch may split/defer; a FORCE replay must never silently
    # return a different or unmarked plan in place of its requested strategy.
    if requested:
        if len(items) != 1:
            raise RuntimeError("Explicit FORCE planner transport requires one representative")
        if not payload.get("explorationChain") or str(payload.get("mode") or "") == "learning":
            raise RuntimeError("Explicit FORCE preference escaped production exploration")
        print(
            f"FIELD_BRAIN_FORCE_ADAPTIVE_INPUT requested={requested} items={len(items)} "
            "origin=explicit-deep-planner",
            flush=True,
        )
    planner_input = _BASE._strict_json_dumps(payload).encode("ascii")
    try:
        # Verify the exact bytes locally before they cross the Python -> Node
        # boundary. Any later parse failure is therefore a transport concern.
        json.loads(planner_input.decode("ascii"))
        try:
            completed = subprocess.run(
                ["node", str(_BASE.PLAN_SCRIPT)],
                cwd=_BASE.ROOT,
                input=planner_input,
                capture_output=True,
                check=True,
                timeout=30,
            )
        except subprocess.CalledProcessError as first_exc:
            detail = _BASE._safe_planner_stderr(first_exc.stderr)
            if first_exc.returncode != 2 or "brain_planner_input_invalid" not in detail:
                raise
            # Retry the exact locally-validated bytes through a regular file.
            # This removes stdin/pipe transport from the equation without
            # mutating, truncating or reserializing the planner payload.
            with tempfile.NamedTemporaryFile(prefix="niakvio-brain-", suffix=".json", delete=True) as handle:
                handle.write(planner_input)
                handle.flush()
                env = dict(__import__("os").environ)
                env["NUVIO_BRAIN_PLANNER_INPUT_FILE"] = handle.name
                completed = subprocess.run(
                    ["node", str(_BASE.PLAN_SCRIPT)],
                    cwd=_BASE.ROOT,
                    input=b"",
                    env=env,
                    capture_output=True,
                    check=True,
                    timeout=30,
                )
        parsed = json.loads((completed.stdout or b"{}").decode("utf-8"))
        plans = {
            str(key): row
            for key, row in (parsed.get("plans") or {}).items()
            if isinstance(row, dict)
        }
        if requested:
            expected_keys = {str(item.get("key") or "") for item in items}
            if set(plans) != expected_keys:
                raise RuntimeError("Explicit FORCE planner output omits or adds a candidate")
            for key, row in plans.items():
                reported = str(row.get("forcePreferredRequested") or "").strip().casefold()
                if reported != requested:
                    print(
                        f"FIELD_BRAIN_FORCE_ADAPTIVE_INTENT_MISMATCH requested={requested} "
                        f"returned={reported or 'none'}",
                        flush=True,
                    )
                    raise RuntimeError("Adaptive Brain planner dropped explicit FORCE strategy")
                print(
                    f"FIELD_BRAIN_FORCE_ADAPTIVE_SELECTION requested={requested} "
                    f"selected={str(row.get('forcePreferredSelected') is True).lower()} "
                    f"profile={str(row.get('postExhaustionStrategyProfile') or 'none')[:100]}",
                    flush=True,
                )
        return plans
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



def replan_observation(
    candidate: dict[str, Any],
    result: dict[str, Any],
    *,
    plan_key: str | None = None,
    mode: str = "deep",
) -> dict[str, Any]:
    """Replan one exploration parent through the bounded adaptive transport."""
    key = str(plan_key or candidate.get("key") or "")
    if not key:
        return {}
    item = {
        "key": key,
        "candidate": _BASE._planner_candidate(candidate),
        "result": _BASE._planner_result(result),
        "state": _BASE._public_state(candidate, key),
    }
    base_payload = _BASE._planner_base_payload(
        mode, _BASE.planner_transient_negative_memory(candidate)
    )
    plans = _run_planner_batch(base_payload, [item])
    _BASE.PLANS.update(plans)
    return _BASE.PLANS.get(key) or {}


def update_plans(registry_path: Path, report: dict[str, Any], mode: str, *, stage: Path | None = None) -> dict[str, dict[str, Any]]:
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
        # Do not duplicate or truncate the canonical planner's current-byte
        # structural evidence. This adaptive overlay owns batch transport,
        # not source-diagnosis semantics. Its stage is the same sandbox used
        # for the health result; no provider mutations are performed here.
        planner_candidate = _BASE._planner_candidate(candidate)
        if stage is not None:
            evidence = _BASE._current_source_structural_repair_evidence(
                stage, candidate, result
            )
            if evidence:
                planner_candidate["structuralRepairEvidence"] = evidence
        items.append({
            "key": plan_key,
            "candidate": planner_candidate,
            "result": _BASE._planner_result(result),
            "state": _BASE._public_state(candidate, plan_key),
        })
    if not items:
        return _BASE.PLANS

    base_payload = _BASE._planner_base_payload(mode)
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
        update_plans(registry_path, report, mode, stage=stage)
        return report
    return _run_health
