#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

PLAYER = "FIELD_NATIVE_IOS_PLAYER "
SUITE = "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS "
FIXTURE_END = "FIELD_NATIVE_IOS_FIXTURE_END "
EXPECTED = {"interstellar", "breaking-bad-s01e01", "jujutsu-kaisen-s01e01"}

LANGUAGE_ALIASES = {
    "eng": "en", "english": "en", "anglais": "en",
    "fra": "fr", "fre": "fr", "french": "fr", "francais": "fr", "français": "fr",
    "deu": "de", "ger": "de", "german": "de", "deutsch": "de",
    "spa": "es", "spanish": "es", "espanol": "es", "español": "es",
    "por": "pt", "portuguese": "pt", "portugues": "pt", "português": "pt",
    "ita": "it", "italian": "it", "italiano": "it",
    "jpn": "ja", "japanese": "ja", "japonais": "ja",
    "kor": "ko", "korean": "ko", "coreen": "ko", "coréen": "ko",
    "zho": "zh", "chi": "zh", "chinese": "zh", "chinois": "zh",
}


def normalize_languages(raw: object) -> list[str]:
    output: list[str] = []
    for value in str(raw or "").split(","):
        token = value.strip().casefold().replace("_", "-")
        if not token or token == "und":
            continue
        direct = LANGUAGE_ALIASES.get(token)
        if direct:
            normalized = direct
            if normalized not in output:
                output.append(normalized)
            continue
        first_word = token.split(" ", 1)[0].split("(", 1)[0]
        if first_word in LANGUAGE_ALIASES:
            normalized = LANGUAGE_ALIASES[first_word]
            if normalized not in output:
                output.append(normalized)
            continue
        parts = [part for part in token.split("-") if part]
        if not parts:
            continue
        parts[0] = LANGUAGE_ALIASES.get(parts[0], parts[0])
        normalized = "-".join(parts)
        if normalized not in output:
            output.append(normalized)
    return output


def language_coverage(expected: list[str], observed: list[str]) -> bool:
    used: set[int] = set()
    for language in expected:
        match = next(
            (
                index
                for index, candidate in enumerate(observed)
                if index not in used and (
                    language == candidate
                    or language.split("-", 1)[0] == candidate.split("-", 1)[0]
                )
            ),
            None,
        )
        if match is None:
            return False
        used.add(match)
    return True


def parse_fields(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for token in text.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[key] = value
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    # This script is CI-only and intentionally accepts only the two fixed paths
    # owned by the current GitHub Actions workspace. CLI arguments are retained
    # as an explicit workflow contract, but never become filesystem authority.
    workspace = Path.cwd().resolve(strict=True)
    log_path = workspace / "mobile-ios-native-corpus.log"
    output_dir = workspace / "mobile-ios-diagnostics"
    if args.log.resolve(strict=False) != log_path:
        raise SystemExit(f"--log must be the workspace-owned iOS corpus log: {log_path}")
    if args.output_dir.resolve(strict=False) != output_dir:
        raise SystemExit(f"--output-dir must be the workspace-owned diagnosis directory: {output_dir}")

    text = log_path.read_text(encoding="utf-8", errors="replace")
    suite_lines = [line for line in text.splitlines() if SUITE in line]
    if not suite_lines or "status=completed" not in suite_lines[-1]:
        raise SystemExit("iOS native Lab did not emit a completed suite marker")

    ended: set[str] = set()
    players: list[dict] = []
    for raw in text.splitlines():
        marker = raw.find("FIELD_NATIVE_")
        if marker < 0:
            continue
        line = raw[marker:].strip()
        if line.startswith(FIXTURE_END):
            fixture = parse_fields(line[len(FIXTURE_END):]).get("fixture", "")
            if fixture:
                ended.add(fixture)
        elif line.startswith(PLAYER):
            try:
                row = json.loads(line[len(PLAYER):])
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                players.append(row)

    if ended != EXPECTED:
        raise SystemExit(
            f"incomplete iOS fixture traversal: ended={sorted(ended)} expected={sorted(EXPECTED)}"
        )

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    output_dir.mkdir(parents=True, exist_ok=True)
    for fixture in sorted(EXPECTED):
        observations = []
        for row in players:
            if str(row.get("fixture") or "") != fixture:
                continue
            state = str(row.get("state") or "unknown")
            master_audio_tracks = int(row.get("masterAudioTrackCount") or 0)
            player_audio_tracks = int(
                row.get("audioTrackCount") if row.get("audioTrackCount") is not None else -1
            )
            master_audio_languages = normalize_languages(row.get("masterAudioTrackLanguages"))
            player_audio_languages = normalize_languages(row.get("audioTrackLanguages"))
            multi_audio_count_collapsed = master_audio_tracks >= 2 and player_audio_tracks < 2
            multi_audio_language_collapsed = (
                len(master_audio_languages) >= 2
                and (
                    len(player_audio_languages) < 2
                    or not language_coverage(master_audio_languages, player_audio_languages)
                )
            )
            multi_audio_collapsed = multi_audio_count_collapsed or multi_audio_language_collapsed
            healthy = state in {"ready", "ended"} and not multi_audio_collapsed
            observations.append(
                {
                    "client": "mobile-ios",
                    "provider": str(row.get("provider") or ""),
                    "fixture": fixture,
                    "requestType": str(row.get("mediaType") or "unknown"),
                    "routeMode": "declared",
                    "observationLayer": "player",
                    "failureClass": (
                        "healthy"
                        if healthy
                        else "multi_audio_language_collapsed"
                        if multi_audio_language_collapsed
                        else "multi_audio_player_collapsed"
                        if multi_audio_count_collapsed
                        else "reader_timeout"
                        if state == "timeout"
                        else "player_error"
                    ),
                    "readerState": state,
                    "engine": str(row.get("engine") or "nuvio-mobile-ios-production"),
                    "durationSeconds": float(row.get("durationSeconds") or 0.0),
                    "host": str(row.get("host") or ""),
                    "masterAudioTrackCount": master_audio_tracks,
                    "playerAudioTrackCount": player_audio_tracks,
                    "masterAudioTrackLanguages": master_audio_languages,
                    "playerAudioTrackLanguages": player_audio_languages,
                    "failureOwner": "client_runtime" if multi_audio_collapsed else "",
                    "blocking": multi_audio_collapsed,
                }
            )
        payload = {
            "schemaVersion": 1,
            "generatedAt": now,
            "evidenceComplete": True,
            "client": "mobile-ios",
            "fixture": fixture,
            "observations": observations,
        }
        (output_dir / f"mobile-ios-route-{fixture}-brain.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    healthy = sum(1 for row in players if str(row.get("state") or "") in {"ready", "ended"})
    print(
        "FIELD_NATIVE_IOS_DIAGNOSIS "
        f"fixtures={len(EXPECTED)} player_observations={len(players)} healthy={healthy}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
