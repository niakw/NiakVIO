#!/usr/bin/env python3
"""Materialize a bounded Brain architecture proposal during explicit FORCE.

The model may only edit allowlisted Brain/Core/Lab architecture surfaces.
Provider bundles, manifests, ProviderBase and publication files are forbidden.
Every edit is exact find/replace or a new isolated Brain layer/test file.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREFIXES = (
    "providers/", "provider-disabled/", "provider-bases/", "vf/",
)
FORBIDDEN_EXACT = {"manifest.json", "PROVENANCE.json", "provider-overrides.json"}
CREATE_PREFIXES = ("scripts/brain_layers/", "tests/brain_")
MAX_EDITS = 3
MAX_FIND = 600
MAX_REPLACE = 5000
MAX_CREATE = 12000


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def allowed_patterns(config: dict[str, Any]) -> list[str]:
    force = config.get("forceArchitecture") if isinstance(config.get("forceArchitecture"), dict) else {}
    generated = force.get("generatedEditAllowlist") if isinstance(force.get("generatedEditAllowlist"), list) else []
    values = generated or config.get("structuralProposalSurfaces") or []
    return [str(x) for x in values if str(x)]


def path_allowed(path: str, patterns: list[str]) -> bool:
    if not path or path.startswith("/") or ".." in Path(path).parts:
        return False
    if path in FORBIDDEN_EXACT or any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    for pattern in patterns:
        if pattern.endswith("*") and path.startswith(pattern[:-1]):
            return True
        if path == pattern:
            return True
    return any(path.startswith(prefix) for prefix in CREATE_PREFIXES)


def validate_edits(edits: list[dict[str, Any]], patterns: list[str], root: Path = ROOT) -> None:
    if not edits or len(edits) > MAX_EDITS:
        raise ValueError("architecture FORCE requires 1..3 bounded edits")
    code_edits = 0
    for edit in edits:
        op = str(edit.get("operation") or "")
        path = str(edit.get("path") or "")
        if not path_allowed(path, patterns):
            raise ValueError(f"architecture FORCE path outside allowlist: {path}")
        if not path.startswith("tests/"):
            code_edits += 1
        target = root / path
        if op == "replace":
            find = str(edit.get("find") or "")
            replace = str(edit.get("replace") or "")
            if not target.is_file():
                raise ValueError(f"replace target missing: {path}")
            if not find or len(find) > MAX_FIND or len(replace) > MAX_REPLACE:
                raise ValueError("invalid bounded replace")
            source = target.read_text(encoding="utf-8")
            if source.count(find) != 1:
                raise ValueError(f"replace find must occur exactly once: {path}")
            if find == replace:
                raise ValueError("architecture FORCE no-op")
        elif op == "create":
            body = str(edit.get("content") or "")
            if target.exists():
                raise ValueError(f"create target already exists: {path}")
            if not any(path.startswith(prefix) for prefix in CREATE_PREFIXES):
                raise ValueError("new files restricted to Brain layers/tests")
            if not body or len(body) > MAX_CREATE:
                raise ValueError("invalid bounded create")
        else:
            raise ValueError(f"unsupported architecture FORCE operation: {op}")
    if code_edits <= 0:
        raise ValueError("architecture FORCE must include an executable non-test change")


def apply_edits(edits: list[dict[str, Any]], root: Path = ROOT) -> list[str]:
    changed: list[str] = []
    for edit in edits:
        path = str(edit["path"])
        target = root / path
        if edit["operation"] == "replace":
            source = target.read_text(encoding="utf-8")
            target.write_text(source.replace(str(edit["find"]), str(edit.get("replace") or ""), 1), encoding="utf-8")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(edit["content"]), encoding="utf-8")
        changed.append(path)
    return changed


def select_blueprint(proposal: dict[str, Any]) -> dict[str, Any]:
    rows = [x for x in proposal.get("strategyBlueprints") or [] if isinstance(x, dict)]
    eligible = [x for x in rows if x.get("forcePromotionEligible") is True]
    if not eligible:
        raise ValueError("no FORCE-promotable architecture blueprint")
    return eligible[0]


def source_context(blueprint: dict[str, Any], patterns: list[str]) -> dict[str, str]:
    layer = str(blueprint.get("targetLayer") or "")
    candidates = ["scripts/brain_meta_learning.py", "scripts/brain_repair_runtime.py"]
    if layer in {"provider", "core"}:
        candidates.append("scripts/adaptive_runtime/runtime_repair.py")
    elif layer in {"harness", "network", "client-runtime"}:
        candidates.append("scripts/nuvio_client_lab.cjs")
    else:
        candidates.append("scripts/run_brain_learning_sandbox.py")
    out: dict[str, str] = {}
    for path in candidates:
        if path_allowed(path, patterns) and (ROOT / path).is_file():
            text = (ROOT / path).read_text(encoding="utf-8")
            out[path] = text[:12000]
    return out


def call_model(endpoint: str, model: str, payload: dict[str, Any]) -> dict[str, Any]:
    system = (
        "You are NiakVIO Brain architecture FORCE materializer. "
        "Return JSON only: {edits:[...]}. Create the smallest executable architecture change "
        "that implements the supplied blueprint. Never edit providers, manifests, ProviderBase, "
        "publication files or secrets. Use only exact source snippets supplied. Max 3 edits. "
        "Allowed operations: replace {operation,path,find,replace}; create {operation,path,content}. "
        "New files only under scripts/brain_layers/ or tests/brain_."
    )
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 1800,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
        ],
    }
    req = Request(
        endpoint.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=120) as response:
        value = json.loads(response.read().decode("utf-8"))
    raw = str(value["choices"][0]["message"]["content"]).strip()
    if raw.startswith("~~~") or raw.startswith(chr(96) * 3):
        raw = "\n".join(raw.splitlines()[1:-1]).strip()
        if raw.casefold().startswith("json"):
            raw = raw[4:].lstrip()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("architecture model output must be object")
    return parsed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--proposal", type=Path, required=True)
    p.add_argument("--self-config", type=Path, required=True)
    p.add_argument("--endpoint", default="http://127.0.0.1:8080")
    p.add_argument("--model", default="qwen2.5-coder-3b")
    p.add_argument("--response-file", type=Path)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()

    proposal = load(a.proposal)
    config = load(a.self_config)
    force = config.get("forceArchitecture") if isinstance(config.get("forceArchitecture"), dict) else {}
    if force.get("enabled") is not True:
        raise SystemExit("architecture FORCE disabled")
    blueprint = select_blueprint(proposal)
    patterns = allowed_patterns(config)
    payload = {
        "blueprint": blueprint,
        "architectureLayers": proposal.get("architectureLayers") or [],
        "allowedPaths": patterns,
        "sources": source_context(blueprint, patterns),
        "contract": {
            "providerPublicationAuthority": False,
            "productionProviderWritesAllowed": False,
            "requireExecutableDiff": True,
            "requireTargetedTests": True,
        },
    }
    if a.response_file:
        planned = load(a.response_file)
    else:
        planned = call_model(a.endpoint, a.model, payload)
    edits = [dict(x) for x in planned.get("edits") or [] if isinstance(x, dict)]
    validate_edits(edits, patterns)
    changed = apply_edits(edits) if a.apply else [str(x.get("path") or "") for x in edits]
    report = {
        "schemaVersion": 1,
        "strategyId": blueprint.get("strategyId"),
        "targetLayer": blueprint.get("targetLayer"),
        "changedFiles": changed,
        "editCount": len(edits),
        "applied": bool(a.apply),
        "providerPublicationAuthority": False,
        "productionProviderWritesAllowed": False,
        "requiresTargetedTests": True,
        "requiresRequiredCi": True,
    }
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("FIELD_BRAIN_ARCH_FORCE_MATERIALIZED edits=%d files=%s" % (len(edits), ",".join(changed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
