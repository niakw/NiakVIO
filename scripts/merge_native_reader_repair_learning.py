#!/usr/bin/env python3
"""Merge sanitized native-reader repair outcomes into persistent Brain memory.

The input comparison contains no raw media locators or credential values. This
script persists only provider/fixture/failure-class/generic-skill identities and
aggregate success/failure counters so future Learning Lab repair attempts can
prefer proven skills and avoid repeating failed ones.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECTION_BEGIN = "<!-- NATIVE_READER_REPAIR_MEMORY_BEGIN -->"
SECTION_END = "<!-- NATIVE_READER_REPAIR_MEMORY_END -->"


def read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def clean(value: Any, limit: int = 128) -> str:
    text = str(value or "").strip()
    if "://" in text or any(token in text.casefold() for token in ("authorization=", "cookie=", "token=")):
        return ""
    return text[:limit]


def memory_key(row: dict[str, Any]) -> str:
    return "\0".join((row["providerId"], row["fixture"], row["failureClass"], row["skill"]))


def sanitize_entry(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    provider = clean(raw.get("providerId"), 128).casefold()
    fixture = clean(raw.get("fixture"), 96)
    failure = clean(raw.get("failureClass"), 96) or "unknown_failure"
    skill = clean(raw.get("skill"), 96)
    if not provider or not fixture or not skill:
        return None
    return {
        "providerId": provider,
        "fixture": fixture,
        "failureClass": failure,
        "skill": skill,
        "attempts": max(0, int(raw.get("attempts") or 0)),
        "successes": max(0, int(raw.get("successes") or 0)),
        "failures": max(0, int(raw.get("failures") or 0)),
        "inconclusive": max(0, int(raw.get("inconclusive") or 0)),
        "consecutiveFailures": max(0, int(raw.get("consecutiveFailures") or 0)),
        "lastOutcome": clean(raw.get("lastOutcome"), 32) or None,
        "lastReason": clean(raw.get("lastReason"), 120) or None,
        "lastSeenAt": clean(raw.get("lastSeenAt"), 48) or None,
    }


def sanitized_run_ids(*memories: Any, limit: int = 100) -> list[str]:
    """Keep a bounded ordered set of previously imported GitHub Actions run IDs."""
    values: list[str] = []
    for memory in memories:
        if not isinstance(memory, dict):
            continue
        for raw in memory.get("importedRunIds") or []:
            value = clean(raw, 32)
            if not value.isdigit() or value in values:
                continue
            values.append(value)
    return values[-max(1, int(limit)):]


def proposal_key(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    return "|".join(
        clean(row.get(key), 128)
        for key in ("type", "providerId", "failureClass", "skill", "fixture")
    )


def render_markdown(base: str, entries: list[dict[str, Any]], stats: list[dict[str, Any]], imported: int) -> str:
    if SECTION_BEGIN in base and SECTION_END in base:
        prefix = base.split(SECTION_BEGIN, 1)[0].rstrip()
        suffix = base.split(SECTION_END, 1)[1].lstrip()
        base = prefix + ("\n\n" + suffix if suffix else "")
    lines = [
        SECTION_BEGIN,
        "## Native reader repair memory",
        "",
        f"Reader repair memory entries: **{len(entries)}**  ",
        f"Reader repair outcomes imported this run: **{imported}**  ",
        f"Generic reader repair skills observed: **{len(stats)}**",
        "",
    ]
    if stats:
        lines.extend(["| Skill | Maturity | Successes | Failures | Proven providers |", "|---|---:|---:|---:|---:|"])
        for row in stats[:20]:
            lines.append(
                f"| `{clean(row.get('skill'), 96)}` | {clean(row.get('maturity'), 24)} | "
                f"{int(row.get('successes') or 0)} | {int(row.get('failures') or 0)} | {int(row.get('provenProviderCount') or 0)} |"
            )
        lines.append("")
    lines.append(SECTION_END)
    return base.rstrip() + "\n\n" + "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--previous-state", type=Path)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-input", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--max-entries", type=int, default=1200)
    parser.add_argument("--avoid-threshold", type=int, default=2)
    args = parser.parse_args()

    state = read_json(args.state)
    previous = read_json(args.previous_state)
    comparison = read_json(args.comparison)
    output = args.output or args.state
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    memory: dict[str, dict[str, Any]] = {}
    previous_memory = previous.get("nativeReaderRepairMemory") if isinstance(previous.get("nativeReaderRepairMemory"), dict) else {}
    current_memory = state.get("nativeReaderRepairMemory") if isinstance(state.get("nativeReaderRepairMemory"), dict) else {}
    imported_run_ids = sanitized_run_ids(previous_memory, current_memory)
    for source in (previous_memory, current_memory):
        for raw in source.get("entries") or []:
            entry = sanitize_entry(raw)
            if entry:
                memory[memory_key(entry)] = entry

    outcome_groups = (
        ("accepted", "accepted"),
        ("rejected", "rejected"),
        ("inconclusive", "inconclusive"),
    )
    imported = 0
    for field, outcome in outcome_groups:
        for row in comparison.get(field) or []:
            if not isinstance(row, dict):
                continue
            provider = clean(row.get("provider"), 128).casefold()
            fixture = clean(row.get("fixture") or comparison.get("fixture"), 96)
            failure_classes = [clean(value, 96) for value in row.get("failureClasses") or [] if clean(value, 96)] or ["unknown_failure"]
            skills = [clean(value, 96) for value in row.get("skills") or [] if clean(value, 96)]
            reason = clean(row.get("reason"), 120)
            if not provider or not fixture:
                continue
            for failure in failure_classes:
                for skill in skills:
                    template = {
                        "providerId": provider,
                        "fixture": fixture,
                        "failureClass": failure,
                        "skill": skill,
                        "attempts": 0,
                        "successes": 0,
                        "failures": 0,
                        "inconclusive": 0,
                        "consecutiveFailures": 0,
                        "lastOutcome": None,
                        "lastReason": None,
                        "lastSeenAt": None,
                    }
                    key = memory_key(template)
                    entry = memory.get(key, template)
                    entry["attempts"] += 1
                    if outcome == "accepted":
                        entry["successes"] += 1
                        entry["consecutiveFailures"] = 0
                    elif outcome == "rejected":
                        entry["failures"] += 1
                        entry["consecutiveFailures"] += 1
                    else:
                        entry["inconclusive"] += 1
                    entry["lastOutcome"] = outcome
                    entry["lastReason"] = reason or outcome
                    entry["lastSeenAt"] = now
                    memory[key] = entry
                    imported += 1

    entries = sorted(
        memory.values(),
        key=lambda row: (str(row.get("lastSeenAt") or ""), int(row.get("attempts") or 0)),
        reverse=True,
    )[: max(1, int(args.max_entries))]

    skill_stats: dict[str, dict[str, Any]] = {}
    for entry in entries:
        skill = entry["skill"]
        stats = skill_stats.setdefault(skill, {
            "skill": skill,
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "inconclusive": 0,
            "provenProviders": set(),
            "failedProviders": set(),
        })
        for key in ("attempts", "successes", "failures", "inconclusive"):
            stats[key] += int(entry.get(key) or 0)
        if int(entry.get("successes") or 0) > 0:
            stats["provenProviders"].add(entry["providerId"])
        if int(entry.get("failures") or 0) > 0 and int(entry.get("successes") or 0) == 0:
            stats["failedProviders"].add(entry["providerId"])

    stats_rows = []
    for stats in skill_stats.values():
        proven = sorted(stats.pop("provenProviders"))
        failed = sorted(stats.pop("failedProviders"))
        stats_rows.append({
            **stats,
            "provenProviderCount": len(proven),
            "failedProviderCount": len(failed),
            "provenProviders": proven[:48],
            "failedProviders": failed[:48],
            "maturity": "reusable" if len(proven) >= 2 and int(stats["successes"]) >= 2 else ("promising" if proven else "experimental"),
        })
    stats_rows.sort(key=lambda row: (-int(row["successes"]), int(row["failures"]), row["skill"]))

    avoid_threshold = max(1, int(args.avoid_threshold))
    proposals = [row for row in state.get("proposals") or [] if isinstance(row, dict)]
    for entry in entries:
        if int(entry["successes"]) == 0 and int(entry["consecutiveFailures"]) >= avoid_threshold:
            proposals.append({
                "type": "avoid_native_reader_skill",
                "priority": "high",
                "providerId": entry["providerId"],
                "fixture": entry["fixture"],
                "failureClass": entry["failureClass"],
                "skill": entry["skill"],
                "evidenceCount": entry["failures"],
                "reason": "Fresh native-reader retests repeatedly rejected this generic repair skill for the same provider/failure class.",
            })
    for stats in stats_rows:
        if stats["maturity"] in {"promising", "reusable"}:
            proposals.append({
                "type": "native_reader_skill_evidence",
                "priority": "high" if stats["maturity"] == "reusable" else "medium",
                "skill": stats["skill"],
                "maturity": stats["maturity"],
                "evidenceCount": stats["successes"],
                "provenProviderCount": stats["provenProviderCount"],
                "reason": "The generic repair skill has fresh official-reader success evidence and should be preferred over unproven alternatives when causally compatible.",
            })

    deduped: dict[str, dict[str, Any]] = {}
    for proposal in proposals:
        key = proposal_key(proposal) or json.dumps(proposal, sort_keys=True)
        deduped[key] = proposal
    state["proposals"] = list(deduped.values())
    state["nativeReaderRepairMemory"] = {
        "schemaVersion": 1,
        "updatedAt": now,
        "importedOutcomesThisRun": imported,
        "importedRunIds": imported_run_ids,
        "entries": entries,
        "skillStats": stats_rows,
    }
    native = state.get("nativeFeedback") if isinstance(state.get("nativeFeedback"), dict) else {}
    native["readerRepairAccepted"] = int(comparison.get("acceptedCount") or 0)
    native["readerRepairRejected"] = int(comparison.get("rejectedCount") or 0)
    native["readerRepairInconclusive"] = int(comparison.get("inconclusiveCount") or 0)
    state["nativeFeedback"] = native
    state["privacy"] = "No raw URLs, tokens, header values, cookies or private notes are copied into persistent Brain learning state. Native reader repair memory stores only sanitized ids and aggregate outcomes."

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.markdown_output:
        base = "# NiakVIO Brain Learning\n"
        if args.markdown_input and args.markdown_input.is_file():
            base = args.markdown_input.read_text(encoding="utf-8")
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(base, entries, stats_rows, imported), encoding="utf-8")

    print(f"FIELD_NATIVE_READER_LEARNING imported={imported} entries={len(entries)} skills={len(stats_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
