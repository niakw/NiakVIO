#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, got {count}")
    return text.replace(old, new, 1)


def patch_prepare() -> None:
    path = "scripts/prepare_native_corpus_validation.py"
    text = read(path)
    anchor = (
        "from native_media_type_contract import fixture_runtime_media_type  # noqa: E402\n"
        'CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"'
    )
    replacement = (
        "from native_media_type_contract import fixture_runtime_media_type  # noqa: E402\n"
        "from rotating_corpus import fixture_by_slug as rotating_fixture_by_slug  # noqa: E402\n"
        'CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"'
    )
    if "from rotating_corpus import fixture_by_slug as rotating_fixture_by_slug" not in text:
        text = replace_once(text, anchor, replacement, "prepare import")
    pattern = re.compile(r"def fixture_by_slug\(slug: str\) -> dict:\n.*?\n\ndef manifest_providers", re.S)
    repl = '''def fixture_by_slug(slug: str) -> dict:
    try:
        return rotating_fixture_by_slug(slug)
    except KeyError as error:
        raise SystemExit(str(error)) from error


def manifest_providers'''
    text, count = pattern.subn(repl, text, count=1)
    if count != 1:
        raise SystemExit(f"prepare fixture resolver patch count={count}")
    write(path, text)


def patch_ios() -> None:
    path = "scripts/prepare_native_ios_reader_acceptance.py"
    text = read(path)
    if "from rotating_corpus import select_fixtures" not in text:
        text = replace_once(
            text,
            "from pathlib import Path\n",
            "from pathlib import Path\n\nfrom rotating_corpus import select_fixtures\n",
            "ios rotation import",
        )
    pattern = re.compile(r"def fixture_rows\(\) -> list\[dict\]:\n.*?\n\ndef kotlin_fixture_list", re.S)
    repl = '''def fixture_rows() -> list[dict]:
    rows = []
    for kind in ("movie", "tv", "anime"):
        selected = select_fixtures(kind, count=1, provider="ios-native")
        if len(selected) != 1:
            raise SystemExit(f"missing rotating fixture for {kind}")
        fixture = selected[0]
        rows.append(
            {
                "slug": fixture["slug"],
                "tmdbId": str(fixture.get("tmdbId") or ""),
                "mediaType": kind,
                "season": fixture.get("season"),
                "episode": fixture.get("episode"),
            }
        )
    return rows


def kotlin_fixture_list'''
    text, count = pattern.subn(repl, text, count=1)
    if count != 1:
        raise SystemExit(f"ios fixture_rows patch count={count}")
    write(path, text)


def patch_repair_queue() -> None:
    path = "scripts/validate_provider_v3_routes_sequential.py"
    text = read(path)
    if "from rotating_corpus import default_seed, select_fixtures" not in text:
        text = replace_once(
            text,
            "from provider_route_proof import filter_recipe_by_live_routes\n",
            "from provider_route_proof import filter_recipe_by_live_routes\n"
            "from rotating_corpus import default_seed, select_fixtures\n",
            "repair rotation import",
        )
    anchor = '''            for slug in SEMANTIC_FIXTURE_FALLBACKS.get(media_type, ()):
                row = by_slug.get(slug)
                if row is not None and all(existing["slug"] != slug for existing in selected):
                    selected.append(row)

        for row in fixtures:'''
    replacement = '''            for slug in SEMANTIC_FIXTURE_FALLBACKS.get(media_type, ()):
                row = by_slug.get(slug)
                if row is not None and all(existing["slug"] != slug for existing in selected):
                    selected.append(row)

            # PROVIDER_V3_ROTATING_CATALOGUE_SAMPLE_V1
            # A clean no-stream result is catalogue uncertainty, not broken-lane
            # proof. Add a bounded per-provider sample whose order changes with
            # each run. The reconstructor stops this lane only on playable proof.
            for rotated_fixture in select_fixtures(
                media_type, count=3, seed=default_seed(), provider=provider_id
            ):
                slug = str(rotated_fixture.get("slug") or "")
                if not slug or any(existing["slug"] == slug for existing in selected):
                    continue
                fixture = copy.deepcopy(rotated_fixture)
                fixture.pop("slug", None)
                fixture.pop("lane", None)
                selected.append({
                    "slug": slug,
                    "providers": set(),
                    "fixture": fixture,
                    "semantic_type": media_type,
                })

        for row in fixtures:'''
    if "PROVIDER_V3_ROTATING_CATALOGUE_SAMPLE_V1" not in text:
        text = replace_once(text, anchor, replacement, "repair rotating candidates")

    old_set = '{"terminal-blocked", "terminal-unreachable", "disabled-unqualified"}'
    new_set = '{"terminal-blocked", "terminal-unreachable", "disabled-unqualified", "resample-required"}'
    text = text.replace(old_set, new_set)
    write(path, text)


def patch_reconstruct() -> None:
    path = "scripts/reconstruct_provider_v3_sequential_live.py"
    text = read(path)
    old_skip = '''        already_validated = {
            str(value or "").strip().casefold() for value in evaluation.get("validatedTypes") or []
        }
        if semantic_type in already_validated:'''
    new_skip = '''        already_validated = {
            str(value or "").strip().casefold() for value in evaluation.get("playableChainValidatedTypes") or []
        }
        if semantic_type in already_validated:'''
    if old_skip in text:
        text = replace_once(text, old_skip, new_skip, "repair playable-only skip")
    elif new_skip not in text:
        raise SystemExit("repair playable-only skip anchor missing")

    old_break = '''            if is_qualified(evaluation) or semantic_type in {
                str(value or "").strip().casefold() for value in evaluation.get("validatedTypes") or []
            }:
                break'''
    new_break = '''            if is_qualified(evaluation) or semantic_type in {
                str(value or "").strip().casefold() for value in evaluation.get("playableChainValidatedTypes") or []
            }:
                break'''
    if old_break in text:
        text = replace_once(text, old_break, new_break, "repair playable-only break")
    elif new_break not in text:
        raise SystemExit("repair playable-only break anchor missing")

    if "def resample_required_lanes(" not in text:
        helper_anchor = "\n\ndef prove_final_bundle(\n"
        helper = '''

def resample_required_lanes(
    rows: list[dict[str, Any]],
    evaluation: dict[str, Any],
) -> list[str]:
    """Return unproved lanes whose sampled works all ended as clean no-streams."""
    required = {
        str(value or "").strip().casefold()
        for value in evaluation.get("requiredTypes") or []
        if str(value or "").strip()
    }
    playable = {
        str(value or "").strip().casefold()
        for value in evaluation.get("playableChainValidatedTypes") or []
        if str(value or "").strip()
    }
    missing = required - playable
    if not missing:
        return []
    clean: set[str] = set()
    for media_type in missing:
        lane_rows = [
            row for row in rows
            if str(row.get("semantic_type") or "").strip().casefold() == media_type
        ]
        if not lane_rows or any(row.get("status") != "no_streams" for row in lane_rows):
            continue
        http_error = any(
            int(fetch.get("status") or 0) >= 400
            for row in lane_rows
            for fetch in row.get("fetches") or []
            if isinstance(fetch, dict)
        )
        if not http_error:
            clean.add(media_type)
    return sorted(missing) if missing <= clean else []


def prove_final_bundle(
'''
        text = replace_once(text, helper_anchor, helper, "resample helper")

    if "FIELD_PROVIDER_RESAMPLE_REQUIRED" not in text:
        main_anchor = '''        if completion_state is None:
            completion_state, origin_evidence = terminal_state(
                evaluation, model, patch, origin_timeout
            )

        if completion_state is None and provider.get("enabled") is False:'''
        main_replacement = '''        if completion_state is None:
            completion_state, origin_evidence = terminal_state(
                evaluation, model, patch, origin_timeout
            )

        if completion_state is None and provider.get("enabled") is not False:
            resample_lanes = resample_required_lanes(_rows, evaluation)
            if resample_lanes:
                completion_state = "resample-required"
                print(
                    "FIELD_PROVIDER_RESAMPLE_REQUIRED "
                    f"provider={provider_id} lanes={','.join(resample_lanes)} "
                    "reason=clean_zero_stream_catalogue_sample next_action=rotate_fixture",
                    flush=True,
                )

        if completion_state is None and provider.get("enabled") is False:'''
        text = replace_once(text, main_anchor, main_replacement, "resample completion")
    write(path, text)


def patch_gate_ios() -> None:
    path = "scripts/gate_native_declared_provider_matrix.py"
    text = read(path)
    anchor = '''                    if r[0] in provider_ids:
                        lane_outcomes[r] = merge_outcome(lane_outcomes[r], outcome)
                    elif r[0] in disabled_ids:'''
    replacement = '''                    if r[0] in provider_ids:
                        completed.add(r)
                        lane_outcomes[r] = merge_outcome(lane_outcomes[r], outcome)
                    elif r[0] in disabled_ids:'''
    if "completed.add(r)\n                        lane_outcomes[r]" not in text:
        text = replace_once(text, anchor, replacement, "ios dynamic completion")
    write(path, text)


def patch_suite_defaults() -> None:
    old = "DEFAULT_FIXTURES=(interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01)"
    new = '''DEFAULT_FIXTURES=()
while IFS= read -r fixture; do
  [[ -n "$fixture" ]] && DEFAULT_FIXTURES+=("$fixture")
done < <(python3 "${NIAKVIO}/scripts/rotating_corpus.py" select --lane all --count-per-lane 1)
[[ ${#DEFAULT_FIXTURES[@]} -eq 3 ]] || { echo "rotating corpus must select movie/tv/anime" >&2; exit 2; }'''
    for path in (
        "scripts/run_native_corpus_desktop_suite.sh",
        "scripts/run_native_corpus_mobile_suite.sh",
        "scripts/run_native_corpus_tv_suite.sh",
    ):
        text = read(path)
        if old in text:
            text = text.replace(old, new, 1)
        elif "rotating corpus must select movie/tv/anime" not in text:
            raise SystemExit(f"{path}: default fixture anchor missing")
        write(path, text)


def patch_desktop_workflow() -> None:
    path = ".github/workflows/native-desktop-reader-acceptance.yml"
    text = read(path)
    old = "          FIXTURES=(interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01)"
    new = '''          FIXTURES=()
          while IFS= read -r fixture; do
            [[ -n "$fixture" ]] && FIXTURES+=("$fixture")
          done < <(python3 "$GITHUB_WORKSPACE/niakvio/scripts/rotating_corpus.py" select --lane all --count-per-lane 1)
          [[ ${#FIXTURES[@]} -eq 3 ]] || { echo "rotating corpus must select exactly three lanes" >&2; exit 2; }'''
    if old in text:
        text = replace_once(text, old, new, "desktop workflow fixtures")
    elif "rotating corpus must select exactly three lanes" not in text:
        raise SystemExit("desktop workflow fixture anchor missing")
    old_fallback = "            printf '%s\\n' interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01 > \"$FIXTURE_FILE\""
    new_fallback = '            python3 "$GITHUB_WORKSPACE/niakvio/scripts/rotating_corpus.py" select --lane all --count-per-lane 1 > "$FIXTURE_FILE"'
    if old_fallback in text:
        text = replace_once(text, old_fallback, new_fallback, "desktop diagnosis fallback")
    elif new_fallback not in text:
        raise SystemExit("desktop diagnosis fallback anchor missing")
    write(path, text)


def patch_android_workflow() -> None:
    path = ".github/workflows/native-mobile-android-reader.yml"
    text = read(path)
    tv_old = '          python3 niakvio/scripts/prepare_native_reader_acceptance.py tv --fixture interstellar --workspace "$GITHUB_WORKSPACE" --manifest manifest.json --provider declared-type --streams 2 --initial'
    tv_new = '''          ROTATED_FIXTURES="$(python3 niakvio/scripts/rotating_corpus.py select --lane all --count-per-lane 1 | paste -sd' ' -)"
          test "$(wc -w <<<"$ROTATED_FIXTURES")" -eq 3
          PRIMARY_FIXTURE="${ROTATED_FIXTURES%% *}"
          {
            echo "NIAKVIO_REPRESENTATIVE_FIXTURES=$ROTATED_FIXTURES"
            echo "NIAKVIO_TARGET_FIXTURES=$ROTATED_FIXTURES"
            echo "NIAKVIO_PRIMARY_FIXTURE=$PRIMARY_FIXTURE"
          } >> "$GITHUB_ENV"
          echo "FIELD_ROTATING_CORPUS client=tv fixtures=$ROTATED_FIXTURES"
          python3 niakvio/scripts/prepare_native_reader_acceptance.py tv --fixture "$PRIMARY_FIXTURE" --workspace "$GITHUB_WORKSPACE" --manifest manifest.json --provider declared-type --streams 2 --initial'''
    if tv_old in text:
        text = replace_once(text, tv_old, tv_new, "android tv selector")
    elif "FIELD_ROTATING_CORPUS client=tv" not in text:
        raise SystemExit("android tv selector anchor missing")

    mobile_old = '          python3 niakvio/scripts/prepare_native_reader_acceptance.py mobile --fixture interstellar --workspace "$GITHUB_WORKSPACE" --manifest manifest.json --provider declared-type --streams all --initial'
    mobile_new = '''          ROTATED_FIXTURES="$(python3 niakvio/scripts/rotating_corpus.py select --lane all --count-per-lane 1 | paste -sd' ' -)"
          test "$(wc -w <<<"$ROTATED_FIXTURES")" -eq 3
          PRIMARY_FIXTURE="${ROTATED_FIXTURES%% *}"
          {
            echo "NIAKVIO_REPRESENTATIVE_FIXTURES=$ROTATED_FIXTURES"
            echo "NIAKVIO_TARGET_FIXTURES=$ROTATED_FIXTURES"
            echo "NIAKVIO_PRIMARY_FIXTURE=$PRIMARY_FIXTURE"
          } >> "$GITHUB_ENV"
          echo "FIELD_ROTATING_CORPUS client=mobile fixtures=$ROTATED_FIXTURES"
          python3 niakvio/scripts/prepare_native_reader_acceptance.py mobile --fixture "$PRIMARY_FIXTURE" --workspace "$GITHUB_WORKSPACE" --manifest manifest.json --provider declared-type --streams all --initial'''
    if mobile_old in text:
        text = replace_once(text, mobile_old, mobile_new, "android mobile selector")
    elif "FIELD_ROTATING_CORPUS client=mobile" not in text:
        raise SystemExit("android mobile selector anchor missing")

    fixed_targets = '          NIAKVIO_TARGET_FIXTURES: "interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01"\n'
    if fixed_targets in text:
        if text.count(fixed_targets) != 2:
            raise SystemExit(f"android fixed target count={text.count(fixed_targets)}")
        text = text.replace(fixed_targets, "")
    fixed_primary = "          NIAKVIO_PRIMARY_FIXTURE: interstellar\n"
    if fixed_primary in text:
        if text.count(fixed_primary) != 4:
            raise SystemExit(f"android fixed primary count={text.count(fixed_primary)}")
        text = text.replace(fixed_primary, "")
    write(path, text)


def main() -> int:
    patch_prepare()
    patch_ios()
    patch_repair_queue()
    patch_reconstruct()
    patch_gate_ios()
    patch_suite_defaults()
    patch_desktop_workflow()
    patch_android_workflow()
    print("rotation integration patch complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
