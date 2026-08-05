#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "automation" / "strict-main-reactivation.json"
TARGETS: dict[str, dict[str, Any]] = {
    # 4KHDHub is useful for movies even when short-lived TV download workers
    # temporarily answer 403. Never publish the failing rows, but do not hide
    # independently proven movie output either.
    "4khdhubnew": {
        "require_title_in_output": True,
        "minimum_valid_fixtures": 1,
        "probe_attempts": 2,
    },
    "animezey": {
        "require_title_in_output": False,
        "probe_attempts": 2,
    },
    "hianime": {
        "require_title_in_output": False,
        "probe_attempts": 2,
    },
    "kisskh": {
        "require_title_in_output": True,
        "probe_attempts": 2,
    },
}
FORBIDDEN = re.compile(r"(?:magnet:|\.torrent(?:[?#]|$)|btih:|tracker\.|peer[-_]?id|webtorrent)", re.I)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char)).casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def meaningful_title_tokens(fixture: dict[str, Any]) -> list[str]:
    tokens = normalize(fixture.get("title") or fixture.get("label")).split()
    return [token for token in tokens if len(token) >= 4 and token not in {"season", "saison", "episode"}]


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        try:
            value = json.loads(line.strip())
        except Exception:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def probe(path: Path, fixture: dict[str, Any], timeout_seconds: int = 160) -> dict[str, Any]:
    env = dict(os.environ)
    env["NODE_OPTIONS"] = "--max-old-space-size=1024"
    try:
        process = subprocess.run(
            [
                "node", "scripts/nuvio_tv_probe_v2.cjs", str(path),
                json.dumps(fixture, ensure_ascii=False), "{}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
    except Exception as error:
        return {"ok": False, "result": None, "error": f"{type(error).__name__}: {error}"}
    parsed = parse_probe(process.stdout)
    return {
        "ok": bool(parsed and int(parsed.get("playable_stream_count") or 0) > 0),
        "returncode": process.returncode,
        "result": parsed,
        "stdout_tail": process.stdout[-3500:],
        "stderr_tail": process.stderr[-1800:],
    }


def first_fixture(config: dict[str, Any], category: str) -> dict[str, Any]:
    rows = config.get("fixtures", {}).get(category, [])
    if not rows:
        raise RuntimeError(f"missing health fixture: {category}")
    fixture = dict(rows[0])
    fixture.setdefault("category", category)
    return fixture


def fixtures_for(row: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    supported = {
        str(value).strip().casefold()
        for value in (row.get("supportedTypes") or row.get("types") or [])
        if str(value).strip()
    }
    categories: list[str] = []
    if "movie" in supported:
        categories.append("movie")
    if "tv" in supported:
        categories.append("tv")
    if "anime" in supported:
        categories.append("anime")
    if not categories:
        categories.append("movie")
    return [first_fixture(config, category) for category in categories[:3]]


def strict_media(media: dict[str, Any]) -> bool:
    return bool(
        media.get("playable")
        and not media.get("error")
        and (
            media.get("starts_extm3u")
            or media.get("binary_signature")
            or media.get("kind") == "dash"
        )
    )


def validate_output(
    provider_id: str,
    fixture: dict[str, Any],
    result: dict[str, Any],
    require_title: bool,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    parsed = result.get("result") or {}
    playable = [item for item in parsed.get("streams") or [] if strict_media(item.get("media") or {})]
    if not playable:
        return False, ["no strict playable media"]

    title_tokens = meaningful_title_tokens(fixture)
    matched_title = False
    for item in playable:
        row = item.get("row") if isinstance(item.get("row"), dict) else {}
        media = item.get("media") if isinstance(item.get("media"), dict) else {}
        combined_raw = " ".join(
            str(value or "")
            for value in (
                row.get("name"), row.get("title"), row.get("description"),
                row.get("size"), row.get("url"), media.get("url"),
            )
        )
        if FORBIDDEN.search(combined_raw):
            issues.append("P2P/torrent marker in output")
        combined = normalize(combined_raw)
        if title_tokens and any(token in combined for token in title_tokens):
            matched_title = True

    if require_title and not matched_title:
        issues.append("requested title not present in any playable output")
    return not issues, issues


def main() -> int:
    manifest = load(ROOT / "manifest.json")
    vf_manifest = load(ROOT / "vf" / "manifest.json")
    provenance = load(ROOT / "PROVENANCE.json")
    health = load(ROOT / "health-config.json")
    rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or [] if isinstance(row, dict)
    }
    vf_ids = {
        str(row.get("id") or "").casefold()
        for row in vf_manifest.get("scrapers") or [] if isinstance(row, dict)
    }
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "main manifest only",
        "contract": "NuvioTV four positional arguments and global SCRAPER_SETTINGS",
        "media_gate": "#EXTM3U, DASH MPD, or real video container signature; no P2P/torrent",
        "activation_policy": "All declared fixtures by default; an explicit per-provider minimum may retain independently proven media types while failed rows remain untrusted.",
        "providers": {},
        "reactivated": [],
        "preserved_disabled": [],
    }

    for provider_id, policy in TARGETS.items():
        row = rows.get(provider_id)
        entry: dict[str, Any] = {"id": provider_id, "fixtures": []}
        report["providers"][provider_id] = entry
        if row is None:
            entry["error"] = "manifest row missing"
            report["preserved_disabled"].append(provider_id)
            continue
        if provider_id in vf_ids:
            entry["error"] = "provider unexpectedly present in VF manifest"
            report["preserved_disabled"].append(provider_id)
            continue
        bundle = ROOT / str(row.get("filename") or "")
        if not bundle.is_file():
            entry["error"] = f"bundle missing: {bundle}"
            report["preserved_disabled"].append(provider_id)
            continue

        fixtures = fixtures_for(row, health)
        requested_minimum = policy.get("minimum_valid_fixtures")
        minimum_valid = len(fixtures) if requested_minimum is None else int(requested_minimum)
        minimum_valid = max(1, min(minimum_valid, len(fixtures)))
        attempts_allowed = max(1, min(int(policy.get("probe_attempts") or 1), 3))
        valid_count = 0
        unsafe_detected = False
        degraded_fixtures: list[str] = []

        for fixture in fixtures:
            attempt_rows: list[dict[str, Any]] = []
            selected_result: dict[str, Any] = {"ok": False, "result": None, "error": "probe not run"}
            selected_issues: list[str] = ["probe not run"]
            selected_valid = False

            for attempt_number in range(1, attempts_allowed + 1):
                result = probe(bundle, fixture)
                valid, issues = validate_output(
                    provider_id,
                    fixture,
                    result,
                    bool(policy.get("require_title_in_output")),
                )
                attempt_rows.append(
                    {
                        "attempt": attempt_number,
                        "valid": valid,
                        "issues": issues,
                        "probe": result,
                    }
                )
                selected_result = result
                selected_issues = issues
                selected_valid = valid
                if any("P2P/torrent" in issue for issue in issues):
                    unsafe_detected = True
                    break
                if valid:
                    break

            label = str(fixture.get("label") or fixture.get("title") or fixture.get("category") or "fixture")
            if selected_valid:
                valid_count += 1
            else:
                degraded_fixtures.append(label)

            fixture_entry: dict[str, Any] = {
                "fixture": fixture,
                "valid": selected_valid,
                "issues": selected_issues,
                "probe": selected_result,
            }
            if len(attempt_rows) > 1:
                fixture_entry["attempts"] = attempt_rows
            entry["fixtures"].append(fixture_entry)

        entry["valid_fixture_count"] = valid_count
        entry["fixture_count"] = len(fixtures)
        entry["minimum_valid_fixtures"] = minimum_valid
        entry["partial_activation"] = valid_count < len(fixtures)
        entry["degraded_fixtures"] = degraded_fixtures
        entry["unsafe_output_detected"] = unsafe_detected

        if unsafe_detected or valid_count < minimum_valid:
            report["preserved_disabled"].append(provider_id)
            continue

        row["enabled"] = True
        partial = valid_count < len(fixtures)
        current = dict(provenance.setdefault("providers", {}).get(provider_id) or {})
        current.update(
            {
                "id": provider_id,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "check_status": "healthy",
                "activation_eligible": True,
                "strict_activation_eligible": True,
                "runtime_evidence_eligible": True,
                "activation_mode": "strict_main_only_reactivation",
                "activation_blockers": [],
                "degraded_fixtures": degraded_fixtures,
                "partial_media_type_evidence": partial,
                "reactivation_reason": (
                    f"{valid_count}/{len(fixtures)} declared media fixture(s) returned relevant strict direct media under the exact NuvioTV contract; "
                    "failed fixtures remain recorded as degraded and no P2P/torrent output was detected."
                ),
            }
        )
        provenance["providers"][provider_id] = current
        report["reactivated"].append(provider_id)

    provenance["generated_at"] = datetime.now(timezone.utc).isoformat()
    provenance["schema_version"] = int(provenance.get("schema_version") or 0) + 1
    dump(ROOT / "manifest.json", manifest)
    dump(ROOT / "PROVENANCE.json", provenance)
    dump(REPORT_PATH, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["reactivated"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
