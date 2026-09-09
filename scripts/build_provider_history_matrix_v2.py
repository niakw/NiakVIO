#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_BUILDER = ROOT / "scripts" / "build_provider_history_matrix.py"
OUT_JSON = ROOT / "automation" / "provider-history-matrix.json"
OUT_MD = ROOT / "automation" / "PROVIDER-HISTORY-MATRIX.md"
EVIDENCE = ROOT / "automation" / "provider-history-evidence-v1.json"
EXPECTED = 96

GREEN = "🟢"
YELLOW = "🟡"
ORANGE = "🟠"
RED = "🔴"
UNKNOWN = "⚪"


def canon(value: Any) -> str:
    return str(value or "").strip().casefold()


def git_json(ref: str, path: str) -> dict[str, Any]:
    p = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if p.returncode != 0:
        return {}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {}


def provider_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        canon(row.get("id")): row
        for row in (data.get("providers") or [])
        if isinstance(row, dict) and canon(row.get("id"))
    }


def lanes_from_quick(rows: list[dict[str, Any]]) -> dict[str, str]:
    lanes: dict[str, str] = {}
    for row in rows:
        media = canon(row.get("semantic_type"))
        if not media:
            continue
        status = str(row.get("status") or "unknown")
        lanes[media] = (
            "verified"
            if status == "playable_verified"
            else "wrong-content"
            if status == "wrong_content"
            else "zero"
            if status == "no_streams"
            else status
        )
    return lanes


def quick_by_provider(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in data.get("rows") or []:
        if not isinstance(row, dict):
            continue
        pid = canon(row.get("provider_id"))
        if pid:
            out.setdefault(pid, []).append(row)
    return out


def lane_state(lanes: dict[str, str], *, source: str) -> dict[str, str]:
    if not lanes:
        return {"icon": UNKNOWN, "label": "no-proof", "source": source}
    values = set(lanes.values())
    if values and values <= {"verified"}:
        return {"icon": GREEN, "label": "verified", "source": source}
    if "verified" in values:
        return {"icon": YELLOW, "label": "partial", "source": source}
    if "wrong-content" in values:
        return {"icon": YELLOW, "label": "wrong-content", "source": source}
    if values and values <= {"zero"}:
        return {"icon": RED, "label": "no-streams", "source": source}
    return {"icon": UNKNOWN, "label": "inconclusive", "source": source}


def availability_state(row: dict[str, Any] | None, *, source: str) -> dict[str, str]:
    if not row:
        return {"icon": UNKNOWN, "label": "no-report", "source": source}
    status = canon(row.get("status"))
    if status in {"healthy", "reachable"}:
        return {"icon": GREEN, "label": status, "source": source}
    if status in {"degraded", "blocked"}:
        return {"icon": YELLOW, "label": status, "source": source}
    if status in {"no_streams", "runtime_error", "unavailable"}:
        return {"icon": RED, "label": status.replace("_", "-"), "source": source}
    if status == "provider_unreachable":
        host_health = row.get("host_health") or {}
        has_playable_host = any(
            isinstance(v, dict)
            and (canon(v.get("last_category")) == "playable" or v.get("reachable") is True)
            for v in host_health.values()
        )
        if has_playable_host:
            return {"icon": YELLOW, "label": "provider-unreachable/playable-host", "source": source}
        return {"icon": UNKNOWN, "label": "provider-unreachable/inconclusive", "source": source}
    return {"icon": UNKNOWN, "label": status or "inconclusive", "source": source}


def current_state(row: dict[str, Any]) -> dict[str, str]:
    guard = row.get("currentPublishedGuard") or {}
    field = row.get("currentTvField") or []
    classification = str(row.get("classification") or "")
    values = set(guard.values())

    if field:
        if "wrong-content" in values or ("verified" in values and "zero" in values):
            return {"icon": YELLOW, "label": "field-green/partial", "source": "field+published-guard"}
        return {"icon": GREEN, "label": "field-verified", "source": "current-TV-field"}
    if guard:
        if values and values <= {"verified"}:
            return {"icon": GREEN, "label": "published-verified", "source": "published-byte-guard"}
        if "verified" in values or "wrong-content" in values:
            return {"icon": YELLOW, "label": "published-partial", "source": "published-byte-guard"}
        return {"icon": RED, "label": "published-red", "source": "published-byte-guard"}
    if classification == "CANDIDATE_GREEN":
        return {"icon": YELLOW, "label": "candidate-green", "source": "recent-reconstruction"}
    if classification == "LEARN":
        return {"icon": ORANGE, "label": "learn-debt", "source": "repair-handoff"}
    if classification == "UPSTREAM_DRIFT":
        return {"icon": RED, "label": "current-red/upstream-drift", "source": "historical-replay+current"}
    if classification == "CURRENT_RED":
        return {"icon": RED, "label": "current-red", "source": "current-evidence"}
    if classification == "HISTORICAL_GREEN_UNRETESTED":
        return {"icon": UNKNOWN, "label": "current-untested", "source": "no-current-proof"}
    return {"icon": UNKNOWN, "label": "current-unverified", "source": "no-current-proof"}


def render_snapshot(snapshot: str, state: dict[str, str]) -> str:
    if snapshot == "—":
        return f"{UNKNOWN} —"
    return f"{state['icon']} {state['label']} · {snapshot}"


def lanes_text(lanes: dict[str, str]) -> str:
    if not lanes:
        return "—"
    icon = {"verified": "✓", "wrong-content": "⚠", "zero": "0"}
    order = [x for x in ("movie", "tv", "anime") if x in lanes]
    order += sorted(x for x in lanes if x not in {"movie", "tv", "anime"})
    return " ".join(f"{x}:{icon.get(lanes[x], lanes[x])}" for x in order)


def main() -> int:
    subprocess.run(["python3", str(BASE_BUILDER)], cwd=ROOT, check=True)

    matrix = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if int(matrix.get("providerCount") or 0) != EXPECTED:
        raise SystemExit(f"expected {EXPECTED} providers, got {matrix.get('providerCount')}")

    snapshots = evidence.get("snapshots") or {}
    ref0 = str((snapshots.get("tag_5_21_0") or {}).get("ref") or "5.21.0")
    ref16 = str((snapshots.get("tag_5_21_16") or {}).get("ref") or "5.21.16")
    ref36 = str(
        (snapshots.get("release_5_21_36") or {}).get("ref")
        or "b4d5bff4c2e3b8e9944c1eaaf8ae9690cb00d5cf"
    )

    avail0 = provider_map(git_json(ref0, "availability-report.json"))
    avail16 = provider_map(git_json(ref16, "availability-report.json"))
    q36 = quick_by_provider(git_json(ref36, "provider-v3-quick-yield.json"))
    current_key = str(matrix.get("currentManifestVersion") or "current")

    regression_watch: list[str] = []
    for row in matrix.get("providers") or []:
        pid = canon(row.get("provider"))

        # Critical invariant: 5.21.36 evidence is ONLY 5.21.36 evidence.
        # Never fall back to the current quick-yield when the old snapshot lacks a row.
        lanes36 = lanes_from_quick(q36.get(pid) or [])
        row["historical52136"] = lanes36

        states = {
            "5.21.0": availability_state(avail0.get(pid), source="5.21.0 availability-report"),
            "5.21.16": availability_state(avail16.get(pid), source="5.21.16 availability-report"),
            "5.21.36": lane_state(lanes36, source="5.21.36 provider-v3-quick-yield"),
            current_key: current_state(row),
        }
        row["snapshotStates"] = states

        historical_green = any(states[v]["icon"] == GREEN for v in ("5.21.0", "5.21.16", "5.21.36"))
        current_red = states[current_key]["icon"] in {RED, ORANGE}
        if historical_green and current_red:
            row["regressionWatch"] = True
            regression_watch.append(pid)
        else:
            row["regressionWatch"] = False

    matrix["schemaVersion"] = 2
    matrix["stateLegend"] = {
        GREEN: "live/health proof positive for that exact snapshot",
        YELLOW: "partial, degraded, blocked, wrong-content, or candidate-only",
        ORANGE: "repair debt handed to LEARN",
        RED: "explicit failure/no-stream/current published guard red",
        UNKNOWN: "no reliable live proof or inconclusive snapshot",
    }
    matrix["regressionWatchProviders"] = regression_watch
    OUT_JSON.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = matrix.get("classificationCounts") or {}
    desktop = str(matrix.get("desktopMacFieldObservation") or "")
    lines = [
        "# Provider history & live classification — 96/96",
        "",
        f"- Current manifest: **{current_key}**, providers: **{EXPECTED}**.",
        "- Historical snapshots are compared without cross-version fallback: **5.21.0 → 5.21.16 → 5.21.36 → current**.",
        "- State legend: **🟢 positive**, **🟡 partial/degraded**, **🟠 LEARN debt**, **🔴 explicit failure**, **⚪ unknown/inconclusive**.",
        "- A version/hash is not treated as green unless that exact snapshot has matching evidence.",
        "- Live precedence for current: TV field evidence / current published-byte guard > reconstruction candidate > historical evidence.",
        f"- Desktop macOS field observation: **{desktop or 'no field evidence'}**",
        "- Non-regression policy: a known-good provider/lane is immutable until a replacement wins an A/B live check.",
        "",
        "## Classification counts",
        "",
    ]
    for key, value in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- **{key}**: {value}")

    lines += [
        "",
        "## Version regression watch",
        "",
        f"- Providers with at least one **🟢 historical snapshot** and a **🔴/🟠 current state**: **{len(regression_watch)}**.",
        "- " + (", ".join(f"`{x}`" for x in regression_watch) if regression_watch else "None."),
        "",
        "## 96-provider matrix",
        "",
        "| Provider | Types | Family | 5.21.0 state | 5.21.16 state | 5.21.36 state | Current state | Retained | 5.21.36 live | Current published/field | Class | Action |",
        "|---|---|---|---|---|---|---|---:|---|---|---|---|",
    ]

    for row in matrix.get("providers") or []:
        states = row["snapshotStates"]
        ev: list[str] = []
        if row.get("currentPublishedGuard"):
            ev.append("guard " + lanes_text(row["currentPublishedGuard"]))
        if row.get("currentTvField"):
            ev.append(
                "field "
                + "; ".join(
                    f"{x['semanticType']}:✓ {x['fixture']}" for x in row["currentTvField"]
                )
            )
        if not ev:
            ev = ["—"]
        retained = str(row.get("retainedGenerationCount") or 0)
        if row.get("publishedBaselineRetained"):
            retained += " +baseline"
        watch = " ⚠️" if row.get("regressionWatch") else ""
        lines.append(
            "| {p}{watch} | {types} | {family} | {v0} | {v16} | {v36} | {cur} | {retained} | {h36} | {ev} | **{klass}** | {action} |".format(
                p=row["provider"],
                watch=watch,
                types=", ".join(row.get("types") or []) or "—",
                family=row.get("family") or "—",
                v0=render_snapshot(row["snapshots"].get("5.21.0", "—"), states["5.21.0"]),
                v16=render_snapshot(row["snapshots"].get("5.21.16", "—"), states["5.21.16"]),
                v36=render_snapshot(row["snapshots"].get("5.21.36", "—"), states["5.21.36"]),
                cur=render_snapshot(row["snapshots"].get(current_key, "—"), states[current_key]),
                retained=retained,
                h36=lanes_text(row.get("historical52136") or {}),
                ev="; ".join(ev),
                klass=row.get("classification") or "—",
                action=str(row.get("action") or "").replace("|", "/"),
            )
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- **🟢** means positive evidence tied to that exact version, not merely that the provider file existed.",
        "- **🟡** means useful but incomplete evidence: partial lane, degraded/blocked health, wrong-content, or candidate-only.",
        "- **🔴** means the exact snapshot/report produced an explicit failure such as no streams/runtime error or a current published-byte guard failure.",
        "- **⚪** means unknown/inconclusive; it must never be silently treated as broken or green.",
        "- Rows marked **⚠️** are regression-watch providers: an earlier exact snapshot was green while the current state is red/LEARN debt.",
        "- `PROTECT` / `PARTIAL_PROTECT`: preserve proven lanes and require A/B live proof before replacement.",
        "- `LEARN`: bounded manual Repair is exhausted; route/data discovery belongs to LEARN unless a shared family fix is proven.",
        "",
        "### Priority/VF providers",
        "",
    ]
    for row in matrix.get("providers") or []:
        if row.get("priority") or row.get("vfRegressionGuard"):
            lines.append(
                f"- **{row['provider']}** — {row['snapshotStates'][current_key]['icon']} {row['classification']}: "
                f"{row['historyVerdict']} Action: {row['action']}"
            )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        "PROVIDER_HISTORY_MATRIX_V2_OK "
        f"providers={len(matrix.get('providers') or [])} regression_watch={len(regression_watch)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
