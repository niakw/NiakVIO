#!/usr/bin/env python3
"""Provider v3 strategy-to-executable-plan contract for the full 96 catalogue.

Catalogue membership and activation are separate concerns:
- all 96 canonical Provider Objects remain present for census/recoverability;
- exactly the 46 providers in ``hub-lab-matrix-46.json`` are enabled targets;
- the remaining 50 providers stay disabled and Repair must not widen the set;
- a provider with executable LIVE DATA/recipe/Lego is directly executable;
- a provider without a currently executable plan is accepted only when Repair V6
  attached an audited ``routeDataState=repair`` or ``routeDataState=off``
  disposition whose activation state matches the exact 46-target policy;
- quarantined providers carry an audited OFF disposition so runtime execution
  remains fail-closed rather than pretending that quarantine is a live route.

Hub presence is discovery knowledge, not activation or execution authority.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))
HUB46 = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"
ALLOWED = {
    "mixed_embed_resolver",
    "official_domain_hub",
    "html_scraper",
    "direct_media",
    "api_stream_resolver",
    "iframe_player",
    "quarantined",
}
TERMINAL_DISABLED = {"terminal-blocked", "terminal-unreachable"}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def route_kind(route: object) -> str:
    value = str(route or "").strip().casefold()
    if not value:
        return "ignore"
    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|search|story)=", value):
        return "search"
    if re.search(r"/template-php/[^?#]*fetch\.php(?:[?#]|$)", value):
        return "search"
    if re.search(r"/(?:video[-_]?player|watchplayer|iframeplayer|player|embed|play)(?:[/?#.-]|$)", value):
        return "player"
    if re.search(r"/(?:download|file|mediafile|source|sources)(?:[/?#.-]|$)", value):
        return "source"
    if re.search(r"/(?:episodes?(?:\.js|\.json|\.txt)?|season-list|episode-list)(?:[/?#.-]|$)", value):
        return "episode-index"
    if re.search(r"/api(?:[./?#]|$)", value):
        return "api"
    if re.search(
        r"\{(?:id|tmdb|tmdb_id|tmdbid|imdb|imdb_id|imdbid|title|query|slug|season|episode)\}|"
        r"/(?:title|movie|movies|film|films|tv|serie|series|show|watch|media|anime|animes|voir-series|episode|saison|season|saga|catalogue)(?:[/?#.-]|$)",
        value,
    ):
        return "detail"
    return "other"


def module_fix_id(script: str) -> str:
    path = (ROOT / script).resolve()
    if ROOT not in path.parents or not path.is_file():
        raise AssertionError(f"missing provider Lego: {script}")
    spec = importlib.util.spec_from_file_location("plan_contract_" + path.stem, path)
    assert spec and spec.loader, script
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return str(getattr(module, "MANAGED_FIX_ID", "") or "").strip().upper()


def run_child_test(filename: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tests" / filename)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def terminal_evidence_ok(model: dict, patch: dict, state: str) -> bool:
    gate = patch.get("live_route_gate") if isinstance(patch.get("live_route_gate"), dict) else {}
    recognition = model.get("routeRecognition") if isinstance(model.get("routeRecognition"), dict) else {}
    if gate.get("completion_state") != state or recognition.get("completionState") != state:
        return False
    if recognition.get("sequentialProviderGate") is not True:
        return False
    if state == "terminal-blocked":
        return int(gate.get("provider_request_count") or 0) > 0
    evidence = recognition.get("originEvidence") if isinstance(recognition.get("originEvidence"), list) else []
    return bool(evidence) and all(isinstance(row, dict) and row.get("reachable") is False for row in evidence)


def disposition_activation_ok(disposition: dict, expected_enabled: bool) -> bool:
    expected_state = "enabled" if expected_enabled else "disabled"
    return (
        disposition.get("authority") == "provider-repair-disposition-v1"
        and disposition.get("activationAuthority") == "hub-lab-matrix-46"
        and disposition.get("activationState") == expected_state
        and bool(disposition.get("forcedEnabled")) == expected_enabled
    )


def repair_evidence_ok(patch: dict, expected_enabled: bool) -> bool:
    disposition = patch.get("repair_disposition") if isinstance(patch.get("repair_disposition"), dict) else {}
    if not disposition_activation_ok(disposition, expected_enabled):
        return False
    if disposition.get("routeDataState") != "repair":
        return False
    missing = disposition.get("missingLanes") if isinstance(disposition.get("missingLanes"), list) else []
    reasons = disposition.get("reasonCodes") if isinstance(disposition.get("reasonCodes"), list) else []
    if not missing or not reasons:
        return False
    if disposition.get("completeCapabilityProof") is not False:
        return False
    return True


def off_evidence_ok(patch: dict, expected_enabled: bool) -> bool:
    disposition = patch.get("repair_disposition") if isinstance(patch.get("repair_disposition"), dict) else {}
    if not disposition_activation_ok(disposition, expected_enabled):
        return False
    if disposition.get("routeDataState") != "off":
        return False
    reasons = disposition.get("reasonCodes") if isinstance(disposition.get("reasonCodes"), list) else []
    if not reasons or disposition.get("completeCapabilityProof") is not False:
        return False
    terminal = str(disposition.get("terminalState") or "").strip().casefold()
    quarantined = disposition.get("quarantined") is True
    return quarantined or terminal in TERMINAL_DISABLED


def hub46_targets() -> set[str]:
    matrix = json.loads(HUB46.read_text(encoding="utf-8"))
    rows = matrix.get("rows") if isinstance(matrix.get("rows"), list) else []
    targets = {
        cid(row.get("manifestId"))
        for row in rows
        if isinstance(row, dict) and cid(row.get("manifestId"))
    }
    assert int(matrix.get("hubCount") or 0) == 46, matrix.get("hubCount")
    assert len(targets) == 46, len(targets)
    return targets


def main() -> int:
    run_child_test("provider_contract_recognizer_test.py")
    run_child_test("provider_v3_local_recognition_contract_test.py")

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    knowledge = json.loads(
        (ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8")
    )
    targets = hub46_targets()

    rows = manifest.get("scrapers") or []
    assert len(rows) == 96, f"expected full 96-provider catalogue, got {len(rows)}"
    ids = [cid(row.get("id")) for row in rows]
    assert len(set(ids)) == 96, "provider ids must be unique after canonical case-fold"
    missing_targets = sorted(targets - set(ids))
    assert not missing_targets, f"hub46 targets missing from catalogue: {missing_targets}"

    patches = overrides.get("provider_patches") or {}
    capabilities = overrides.get("provider_capabilities") or {}
    static = knowledge.get("providers") or {}

    failures: list[str] = []
    counts: dict[str, int] = {}
    quarantined: list[str] = []
    terminal_audited: list[str] = []
    repair_audited: list[str] = []
    off_audited: list[str] = []
    enabled_count = 0

    for row, provider_id in zip(rows, ids):
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        capability = (
            capabilities.get(provider_id)
            if isinstance(capabilities.get(provider_id), dict)
            else {}
        )
        model_row = static.get(provider_id) if isinstance(static.get(provider_id), dict) else {}
        model = model_row.get("model") if isinstance(model_row.get("model"), dict) else {}

        expected_enabled = provider_id in targets
        enabled = row.get("enabled") is True
        if enabled:
            enabled_count += 1
        if enabled != expected_enabled:
            failures.append(
                f"{provider_id}: hub46 activation mismatch enabled={enabled} expected={expected_enabled}"
            )
            continue

        strategy = str(
            patch.get("capability")
            or capability.get("strategy")
            or model.get("strategy")
            or "unknown"
        ).strip().casefold()
        counts[strategy] = counts.get(strategy, 0) + 1

        if strategy not in ALLOWED:
            failures.append(f"{provider_id}: unsupported strategy={strategy!r}")
            continue

        legos = [
            str(value).strip()
            for value in patch.get("provider_lego_scripts") or []
            if str(value).strip()
        ]
        for script in legos:
            fix_id = module_fix_id(script)
            expected = f"PROVIDER.{provider_id.upper()}."
            if not fix_id.startswith(expected):
                failures.append(
                    f"{provider_id}: Lego {script} owns {fix_id!r}, expected prefix {expected!r}"
                )

        recipe = isinstance(patch.get("api_recipe"), dict) and bool(patch.get("api_recipe"))
        recipe = recipe or (isinstance(model.get("apiRecipe"), dict) and bool(model.get("apiRecipe")))

        routes: list[str] = []
        for source in (
            patch.get("learned_routes"),
            capability.get("routes"),
            model.get("routes"),
        ):
            for raw in source if isinstance(source, list) else []:
                value = str(raw or "").strip()
                if value and value not in routes:
                    routes.append(value)
        kinds = {route_kind(route) for route in routes}
        kinds.discard("ignore")

        # A discovery hub is intentionally not sufficient to make an execution
        # base. It may still appear in structured knowledge, but executable
        # strategy proof comes from actual site/API/origin/route evidence.
        bases = [
            patch.get("official_site"),
            patch.get("official_api"),
            (patch.get("fixed_endpoint") or {}).get("api")
            if isinstance(patch.get("fixed_endpoint"), dict)
            else None,
            model.get("knownSite"),
            model.get("officialSite"),
            model.get("officialApi"),
            model.get("fixedApi"),
            *(model.get("origins") or []),
        ]
        bases = [str(value).strip() for value in bases if str(value or "").strip()]

        if strategy == "quarantined":
            quarantined.append(provider_id)
            notes = patch.get("notes")
            reason = patch.get("quarantine_reason")
            note_text = json.dumps(notes, ensure_ascii=False).casefold() if notes else ""
            if not reason and "quarantin" not in note_text and "inert" not in note_text:
                failures.append(f"{provider_id}: quarantine must carry explicit evidence/reason")
            if not off_evidence_ok(patch, expected_enabled):
                failures.append(
                    f"{provider_id}: quarantine must carry audited routeDataState=off with matching hub46 activation"
                )
            continue

        executable = bool(legos) or recipe
        if not executable:
            executable = bool(
                {"api", "search", "detail", "player", "source", "episode-index"} & kinds
            ) and bool(bases)

        if not executable:
            recognition = model.get("routeRecognition") if isinstance(model.get("routeRecognition"), dict) else {}
            state = str(recognition.get("completionState") or "").strip()
            if not enabled and state in TERMINAL_DISABLED and terminal_evidence_ok(model, patch, state):
                terminal_audited.append(provider_id)
                continue
            if off_evidence_ok(patch, expected_enabled):
                off_audited.append(provider_id)
                continue
            if repair_evidence_ok(patch, expected_enabled):
                repair_audited.append(provider_id)
                continue
            failures.append(
                f"{provider_id}: strategy={strategy} has no executable LIVE DATA/recipe/Lego "
                f"and no audited hub46-aligned repair/off disposition "
                f"(routeKinds={sorted(kinds)}, bases={len(bases)}, enabled={enabled}, terminal={state or 'none'})"
            )

    if enabled_count != 46:
        failures.append(f"hub46 enabled count mismatch: {enabled_count} != 46")

    if failures:
        raise AssertionError("\n".join(failures))

    diagnostic_non_executable = len(quarantined) + len(terminal_audited) + len(off_audited) + len(repair_audited)
    executable_count = 96 - diagnostic_non_executable
    print(
        "PROVIDER_V3_STRATEGY_PLAN_OK "
        f"providers=96 enabled=46 disabled=50 executable={executable_count} diagnostic_non_executable={diagnostic_non_executable} "
        f"quarantined={len(quarantined)} terminal_legacy={len(terminal_audited)} "
        f"off_diagnostic={len(off_audited)} repair_diagnostic={len(repair_audited)} "
        f"strategies={json.dumps(counts, sort_keys=True)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
