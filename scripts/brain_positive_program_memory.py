#!/usr/bin/env python3
"""Durable sanitized memory for strictly accepted Brain runtime programs.

This file is evidence/prior only. It never publishes candidate provider JavaScript
or bypasses current-byte playback, identity, and non-regression gates. Records are
created only from the strict accepted-program compiler output.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MEMORY_PATH = ROOT / "automation" / "brain-positive-program-memory.json"
_BINDING = re.compile(r"\{(?:binding:)?(id|slug)\}", re.I)


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load_memory(path: Path = MEMORY_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        value = {}
    if not isinstance(value, dict):
        value = {}
    entries = value.get("entries")
    if not isinstance(entries, list):
        entries = []
    return {
        "schemaVersion": 1,
        "role": "validated-positive-program-prior-only",
        "entries": [row for row in entries if isinstance(row, dict)][:1000],
        "safety": {
            "candidateJavaScriptPersisted": False,
            "publicationAuthority": False,
            "sameProviderReplayAllowed": True,
            "peerTransferRequiresSkillMaturity": True,
            "currentByteValidationRequired": True,
        },
    }


def _fingerprint(row: dict[str, Any]) -> str:
    payload = {
        "providerId": cid(row.get("providerId")),
        "failureClass": str(row.get("failureClass") or ""),
        "signature": str(row.get("signature") or ""),
        "profile": str(row.get("profile") or ""),
        "experimentVariant": max(0, int(row.get("experimentVariant") or 0)),
        "experimentGeneration": max(1, int(row.get("experimentGeneration") or 1)),
        "compiledProgram": row.get("compiledProgram") if isinstance(row.get("compiledProgram"), dict) else {},
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def positive_record(
    accepted: dict[str, Any],
    compiled: dict[str, Any],
) -> dict[str, Any]:
    provider = cid(accepted.get("provider") or compiled.get("provider"))
    if not provider:
        raise ValueError("positive program missing provider")
    plan = accepted.get("brainPlan") if isinstance(accepted.get("brainPlan"), dict) else {}
    program = accepted.get("acceptedProgram") if isinstance(accepted.get("acceptedProgram"), dict) else {}
    options = program.get("options") if isinstance(program.get("options"), dict) else {}
    failure_class = str(
        plan.get("failureClass")
        or options.get("experiment_failure_class")
        or ""
    ).strip()
    profile = str(accepted.get("profile") or program.get("profile") or "").strip()
    row = {
        "providerId": provider,
        "validated": True,
        "validationAuthority": "strict-deep-playable-improvement",
        "profile": profile,
        "failureClass": failure_class,
        "signature": str(plan.get("signature") or "").strip(),
        "experimentVariant": max(
            0,
            int(plan.get("experimentVariant") or options.get("experiment_variant") or 0),
        ),
        "experimentGeneration": max(
            1,
            int(plan.get("experimentGeneration") or options.get("experiment_generation") or 1),
        ),
        "reason": str(accepted.get("reason") or ""),
        "statusBefore": accepted.get("statusBefore"),
        "statusAfter": accepted.get("statusAfter"),
        "playableBefore": max(0, int(accepted.get("playableBefore") or 0)),
        "playableAfter": max(0, int(accepted.get("playableAfter") or 0)),
        "compiledProgram": copy.deepcopy(compiled),
    }
    row["fingerprint"] = _fingerprint(row)
    return row


def merge_records(
    accepted_compiled: list[tuple[dict[str, Any], dict[str, Any]]],
    *,
    path: Path = MEMORY_PATH,
) -> dict[str, Any]:
    memory = load_memory(path)
    by_fingerprint = {
        str(row.get("fingerprint") or _fingerprint(row)): copy.deepcopy(row)
        for row in memory.get("entries") or []
        if isinstance(row, dict)
    }
    for accepted, compiled in accepted_compiled:
        row = positive_record(accepted, compiled)
        by_fingerprint[row["fingerprint"]] = row
    memory["entries"] = sorted(
        by_fingerprint.values(),
        key=lambda row: (
            cid(row.get("providerId")),
            str(row.get("failureClass") or ""),
            str(row.get("signature") or ""),
            int(row.get("experimentGeneration") or 1),
            int(row.get("experimentVariant") or 0),
            str(row.get("fingerprint") or ""),
        ),
    )[:1000]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return memory


def provider_entries(provider_id: str, *, path: Path = MEMORY_PATH) -> list[dict[str, Any]]:
    wanted = cid(provider_id)
    return [
        copy.deepcopy(row)
        for row in load_memory(path).get("entries") or []
        if cid(row.get("providerId")) == wanted and row.get("validated") is True
    ]


def _recipe(
    *,
    base: object,
    route: object,
    spec: object,
    role: str,
    semantic_types: object,
    required_bindings: list[str] | None = None,
    response_kind: object = "html-or-text",
    stream_proof: bool = False,
) -> list[dict[str, Any]]:
    base = str(base or "").strip().rstrip("/")
    route = str(route or "").strip()
    spec = spec if isinstance(spec, dict) else {}
    if not base.startswith(("http://", "https://")) or not route.startswith("/"):
        return []
    headers = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
    header_names = sorted({str(key).casefold() for key in headers if str(key).strip()})
    method = str(spec.get("method") or "GET").upper()
    body_kind = str(spec.get("bodyKind") or "none").casefold()
    body = copy.deepcopy(spec.get("body")) if isinstance(spec.get("body"), dict) else {}
    types = [
        str(value).casefold()
        for value in (semantic_types if isinstance(semantic_types, list) else [])
        if str(value).casefold() in {"movie", "tv", "anime"}
    ] or [""]
    output = []
    for media_type in types:
        output.append({
            "route": route,
            "origin": base,
            "role": role,
            "method": method,
            "bodyKind": body_kind,
            "body": body,
            "headerNames": header_names,
            "response": str(response_kind or "html-or-text").casefold()
            if str(response_kind or "html-or-text").casefold() in {"json", "html-or-text"}
            else "html-or-text",
            "semanticType": media_type,
            "streamProof": stream_proof is True,
            "requiredBindings": list(required_bindings or []),
            "executable": True,
            "source": "positive-program-memory",
        })
    return output


def provider_request_recipes(provider_id: str, *, path: Path = MEMORY_PATH) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in provider_entries(provider_id, path=path):
        compiled = entry.get("compiledProgram") if isinstance(entry.get("compiledProgram"), dict) else {}
        for row in compiled.get("searchRequestPlan") or []:
            if not isinstance(row, dict):
                continue
            for recipe in _recipe(
                base=row.get("base"),
                route=row.get("route"),
                spec=row.get("requestSpec"),
                role="search",
                semantic_types=row.get("semanticTypes"),
                response_kind=row.get("responseKind"),
                stream_proof=row.get("streamProof") is True,
            ):
                key = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
                if key not in seen:
                    seen.add(key)
                    output.append(recipe)
        for plan in compiled.get("providerValuePlan") or []:
            if not isinstance(plan, dict):
                continue
            for step in plan.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                route = str(step.get("route") or "")
                bindings = sorted({m.group(1).casefold() for m in _BINDING.finditer(route)})
                for binding in bindings:
                    route = re.sub(
                        r"\{" + re.escape(binding) + r"\}",
                        "{binding:" + binding + "}",
                        route,
                        flags=re.I,
                    )
                for recipe in _recipe(
                    base=step.get("base"),
                    route=route,
                    spec=step.get("requestSpec"),
                    role=str(step.get("role") or "detail").casefold(),
                    semantic_types=plan.get("semanticTypes"),
                    required_bindings=bindings,
                    response_kind=step.get("responseKind"),
                    stream_proof=step.get("streamProof") is True,
                ):
                    key = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
                    if key not in seen:
                        seen.add(key)
                        output.append(recipe)
    return output[:32]


def provider_user_agent(provider_id: str, *, path: Path = MEMORY_PATH) -> str:
    """Return the first sanitized User-Agent that participated in accepted proof."""
    for entry in reversed(provider_entries(provider_id, path=path)):
        compiled = entry.get("compiledProgram") if isinstance(entry.get("compiledProgram"), dict) else {}
        plans = [
            *(compiled.get("searchRequestPlan") or []),
            *(compiled.get("providerValuePlan") or []),
        ]
        for plan in plans:
            if not isinstance(plan, dict):
                continue
            specs = []
            if isinstance(plan.get("requestSpec"), dict):
                specs.append(plan["requestSpec"])
            if isinstance(plan.get("searchRequestSpec"), dict):
                specs.append(plan["searchRequestSpec"])
            for step in plan.get("steps") or []:
                if isinstance(step, dict) and isinstance(step.get("requestSpec"), dict):
                    specs.append(step["requestSpec"])
            for spec in specs:
                headers = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
                for key, value in headers.items():
                    if str(key).casefold() != "user-agent":
                        continue
                    user_agent = str(value or "").strip()
                    if 8 <= len(user_agent) <= 240 and "\n" not in user_agent and "\r" not in user_agent:
                        return user_agent
    return ""


def provider_routes(provider_id: str, *, path: Path = MEMORY_PATH) -> list[str]:
    output: list[str] = []
    for entry in provider_entries(provider_id, path=path):
        compiled = entry.get("compiledProgram") if isinstance(entry.get("compiledProgram"), dict) else {}
        for value in compiled.get("learnedRoutes") or []:
            route = str(value or "").strip()
            if route.startswith("/") and route not in output:
                output.append(route)
    return output[:64]


def learned_skills(*, path: Path = MEMORY_PATH) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in load_memory(path).get("entries") or []:
        if not isinstance(row, dict) or row.get("validated") is not True:
            continue
        failure = str(row.get("failureClass") or "").strip()
        profile = str(row.get("profile") or "").strip()
        if not failure or not profile:
            continue
        groups.setdefault(f"{failure}:{profile}", []).append(row)
    output: dict[str, dict[str, Any]] = {}
    for key, rows in groups.items():
        providers = sorted({cid(row.get("providerId")) for row in rows if cid(row.get("providerId"))})
        signatures = sorted({str(row.get("signature") or "") for row in rows if str(row.get("signature") or "")})
        output[key] = {
            "id": key,
            "failureClass": str(rows[0].get("failureClass") or ""),
            "profile": str(rows[0].get("profile") or ""),
            "validated": True,
            "maturity": "experimental",
            "confidence": 1.0,
            "providers": providers,
            "signatures": signatures,
            "successCount": len(rows),
            "failureCount": 0,
            "actions": [f"replay sanitized validated program prior for {key} under current-byte gates"],
            "autoApply": False,
            "source": "brain-positive-program-memory",
        }
    return output
