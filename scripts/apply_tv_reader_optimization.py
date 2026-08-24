#!/usr/bin/env python3
"""One-shot source migration for bounded/resumable TV native-reader orchestration."""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_suite() -> None:
    path = Path("scripts/run_native_corpus_tv_suite.sh")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'FRONTEND_WATCHER="${NIAKVIO}/scripts/watch_native_device_frontend.sh"\n',
        'FRONTEND_WATCHER="${NIAKVIO}/scripts/watch_native_device_frontend.sh"\nCHECKPOINT_TOOL="${NIAKVIO}/scripts/native_tv_route_checkpoint.py"\n',
        "checkpoint tool",
    )
    text = replace_once(
        text,
        'REGRESSION_STREAM_SCOPE="${NIAKVIO_REGRESSION_STREAM_SCOPE:-2}"\n',
        'REGRESSION_STREAM_SCOPE="${NIAKVIO_REGRESSION_STREAM_SCOPE:-2}"\nTV_PRIORITY_APPEND="${NIAKVIO_TV_PRIORITY_APPEND:-1}"\nROUTE_TIMEOUT_MINUTES="${NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES:-45}"\nCHECKPOINT_ROOT="${NIAKVIO_TV_CHECKPOINT_DIR:-${EVIDENCE_ROOT}/checkpoints}"\nRESUME_CHECKPOINT_ROOT="${NIAKVIO_TV_RESUME_CHECKPOINT_DIR:-${CHECKPOINT_ROOT}}"\n',
        "TV route controls",
    )
    text = replace_once(
        text,
        'if [[ "$TARGET_MANIFEST" = "manifest.json" ]]; then\n',
        'if [[ "$TARGET_MANIFEST" = "manifest.json" && "$TV_PRIORITY_APPEND" = "1" ]]; then\n',
        "priority append guard",
    )
    text = replace_once(
        text,
        'mkdir -p "$EVIDENCE_ROOT"\n',
        'mkdir -p "$EVIDENCE_ROOT" "$CHECKPOINT_ROOT"\nif ! [[ "$ROUTE_TIMEOUT_MINUTES" =~ ^[0-9]+$ ]] || (( ROUTE_TIMEOUT_MINUTES < 10 || ROUTE_TIMEOUT_MINUTES > 90 )); then\n  echo "invalid NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES=$ROUTE_TIMEOUT_MINUTES" >&2\n  exit 2\nfi\nMANIFEST_PATH="${NIAKVIO}/${TARGET_MANIFEST}"\n',
        "checkpoint setup",
    )
    old_loop = '''  STREAM_SCOPE="$REGRESSION_STREAM_SCOPE"\n  if [[ "$fixture" = "$PRIMARY_FIXTURE" ]]; then STREAM_SCOPE="$PRIMARY_STREAM_SCOPE"; fi\n  if [[ "$READER_ACCEPTANCE" = "1" ]]; then\n    PROVIDER_SCOPE="$TARGET_PROVIDER"\n    if [[ -z "$PROVIDER_SCOPE" || "$PROVIDER_SCOPE" = "fixture" ]]; then PROVIDER_SCOPE="$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE"; fi\n    if [[ -z "$PROVIDER_SCOPE" ]]; then PROVIDER_SCOPE="fixture"; fi\n    python3 "$ACCEPTANCE_PREPARE" tv --fixture "$fixture" --workspace "$WORKSPACE" --provider "$PROVIDER_SCOPE" --streams "$STREAM_SCOPE" --manifest "$TARGET_MANIFEST" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }\n  else\n'''
    new_loop = '''  STREAM_SCOPE="$REGRESSION_STREAM_SCOPE"\n  if [[ "$fixture" = "$PRIMARY_FIXTURE" ]]; then STREAM_SCOPE="$PRIMARY_STREAM_SCOPE"; fi\n  PROVIDER_SCOPE="${TARGET_PROVIDER:-all}"\n  if [[ "$READER_ACCEPTANCE" = "1" ]]; then\n    if [[ -z "$PROVIDER_SCOPE" || "$PROVIDER_SCOPE" = "fixture" ]]; then PROVIDER_SCOPE="$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE"; fi\n    if [[ -z "$PROVIDER_SCOPE" ]]; then PROVIDER_SCOPE="fixture"; fi\n  fi\n  LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"\n  CHECKPOINT="${CHECKPOINT_ROOT}/${fixture}.json"\n  RESUME_CHECKPOINT="${RESUME_CHECKPOINT_ROOT}/${fixture}.json"\n  if python3 "$CHECKPOINT_TOOL" verify \\\n      --checkpoint "$RESUME_CHECKPOINT" --log "$LOG" --fixture "$fixture" \\\n      --manifest "$MANIFEST_PATH" --client-root "$TV_ROOT" \\\n      --provider-scope "$PROVIDER_SCOPE" --stream-scope "$STREAM_SCOPE"; then\n    echo "FIELD_NATIVE_CORPUS_TV_RESUME fixture=$fixture checkpoint=$RESUME_CHECKPOINT reused=true"\n    continue\n  fi\n  if [[ "$READER_ACCEPTANCE" = "1" ]]; then\n    python3 "$ACCEPTANCE_PREPARE" tv --fixture "$fixture" --workspace "$WORKSPACE" --provider "$PROVIDER_SCOPE" --streams "$STREAM_SCOPE" --manifest "$TARGET_MANIFEST" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }\n  else\n'''
    text = replace_once(text, old_loop, new_loop, "per-fixture resume")
    text = replace_once(
        text,
        '  "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --console=plain 2>&1 | tee "$GRADLE_LOG"\n  RUNTIME_STATUS=${PIPESTATUS[0]}\n',
        '  timeout --signal=TERM --kill-after=2m "${ROUTE_TIMEOUT_MINUTES}m" "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --console=plain 2>&1 | tee "$GRADLE_LOG"\n  RUNTIME_STATUS=${PIPESTATUS[0]}\n  if [[ "$RUNTIME_STATUS" -eq 124 || "$RUNTIME_STATUS" -eq 137 ]]; then\n    echo "FIELD_NATIVE_CORPUS_TV_ROUTE_TIMEOUT fixture=$fixture minutes=$ROUTE_TIMEOUT_MINUTES status=$RUNTIME_STATUS" | tee -a "$GRADLE_LOG"\n  fi\n',
        "route hard timeout",
    )
    old_status = '''  OBSERVED_READER_STATUS=0\n  node "$READER_GATE" "$LOG" || OBSERVED_READER_STATUS=$?\n  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 || "$COVERAGE_STATUS" -ne 0 || "$OBSERVED_READER_STATUS" -ne 0 ]]; then\n'''
    new_status = '''  OBSERVED_READER_STATUS=0\n  node "$READER_GATE" "$LOG" || OBSERVED_READER_STATUS=$?\n  python3 "$CHECKPOINT_TOOL" record \\\n    --checkpoint "$CHECKPOINT" --log "$LOG" --fixture "$fixture" \\\n    --manifest "$MANIFEST_PATH" --client-root "$TV_ROOT" \\\n    --provider-scope "$PROVIDER_SCOPE" --stream-scope "$STREAM_SCOPE" \\\n    --runtime-status "$RUNTIME_STATUS" --collection-status "$ANALYSIS_STATUS" \\\n    --coverage-status "$COVERAGE_STATUS" --reader-status "$OBSERVED_READER_STATUS"\n  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 || "$COVERAGE_STATUS" -ne 0 || "$OBSERVED_READER_STATUS" -ne 0 ]]; then\n'''
    text = replace_once(text, old_status, new_status, "checkpoint record")
    path.write_text(text, encoding="utf-8")


def patch_workflow() -> None:
    path = Path(".github/workflows/native-android-route-reader.yml")
    text = path.read_text(encoding="utf-8")
    trigger = '      - "scripts/run_native_corpus_tv_suite.sh"\n'
    if text.count(trigger) != 2:
        raise SystemExit(f"workflow trigger anchor count={text.count(trigger)}")
    text = text.replace(
        trigger,
        trigger
        + '      - "scripts/native_tv_route_checkpoint.py"\n'
        + '      - "scripts/build_native_reader_retest_manifest.py"\n'
        + '      - "tests/native_tv_route_resume_test.py"\n',
    )
    text = replace_once(
        text,
        '      tv_sha: ${{ steps.refs.outputs.tv_sha }}\n      runtime_fingerprint: ${{ steps.refs.outputs.runtime_fingerprint }}\n',
        '      tv_sha: ${{ steps.refs.outputs.tv_sha }}\n      tv_shards: ${{ steps.refs.outputs.tv_shards }}\n      runtime_fingerprint: ${{ steps.refs.outputs.runtime_fingerprint }}\n',
        "resolve tv_shards output",
    )
    shard_inject = '''          python3 - <<'PY' >> "$GITHUB_OUTPUT"\n          import json\n          import os\n          from pathlib import Path\n          data = json.loads(Path('.github/triggers/nuvio-client-lab.json').read_text(encoding='utf-8'))\n          fixtures = os.environ['NIAKVIO_REPRESENTATIVE_FIXTURES'].split()\n          for fixture in (data.get('native_reader_acceptance') or {}).get('tv_priority_regressions') or []:\n              fixture = str(fixture).strip()\n              if fixture and fixture not in fixtures:\n                  fixtures.append(fixture)\n          shards = [[], []]\n          for index, fixture in enumerate(fixtures):\n              shards[index % len(shards)].append(fixture)\n          matrix = {'include': [\n              {'shard': str(index), 'fixtures': ' '.join(values)}\n              for index, values in enumerate(shards) if values\n          ]}\n          flattened = [fixture for row in matrix['include'] for fixture in row['fixtures'].split()]\n          if len(matrix['include']) != 2 or sorted(flattened) != sorted(fixtures):\n              raise SystemExit('invalid TV shard construction')\n          print('tv_shards=' + json.dumps(matrix, separators=(',', ':')))\n          PY\n'''
    text = replace_once(
        text,
        '            --output health-output/nuvio-android-lab-heads.json\n',
        '            --output health-output/nuvio-android-lab-heads.json\n' + shard_inject,
        "dynamic TV shard output",
    )
    text = replace_once(
        text,
        '''  tv-route-reader:\n    needs: resolve\n    runs-on: ubuntu-latest\n    timeout-minutes: ${{ github.event_name == 'pull_request' && 100 || 180 }}\n''',
        '''  tv-route-reader:\n    needs: resolve\n    strategy:\n      fail-fast: false\n      matrix: ${{ fromJSON(needs.resolve.outputs.tv_shards) }}\n    runs-on: ubuntu-latest\n    timeout-minutes: ${{ github.event_name == 'pull_request' && 100 || 160 }}\n''',
        "TV matrix job",
    )
    text = replace_once(
        text,
        '          python3 niakvio/scripts/prepare_native_reader_acceptance.py tv --fixture sinners-2025 --workspace "$GITHUB_WORKSPACE" --manifest manifest.json --provider all --streams all --initial\n',
        '          FIRST_FIXTURE="${{ matrix.fixtures }}"\n          FIRST_FIXTURE="${FIRST_FIXTURE%% *}"\n          python3 niakvio/scripts/prepare_native_reader_acceptance.py tv --fixture "$FIRST_FIXTURE" --workspace "$GITHUB_WORKSPACE" --manifest manifest.json --provider all --streams all --initial\n',
        "TV first shard fixture",
    )
    execute_anchor = '      - name: Execute representative routes in one TV boot\n'
    restore_step = '''      - name: Restore completed TV shard checkpoints from an earlier attempt\n        if: github.run_attempt > 1\n        continue-on-error: true\n        uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c\n        with:\n          pattern: native-tv-route-representative-${{ github.run_id }}-attempt-*-shard-${{ matrix.shard }}\n          path: .\n          merge-multiple: true\n'''
    text = replace_once(text, execute_anchor, restore_step + execute_anchor, "restore shard checkpoints")
    text = replace_once(
        text,
        '          NIAKVIO_TARGET_FIXTURES: "sinners-2025 breaking-bad-s01e01 jujutsu-kaisen-s01e01"\n          NIAKVIO_TARGET_PROVIDER: all\n          NIAKVIO_TARGET_MANIFEST: manifest.json\n          NIAKVIO_READER_ACCEPTANCE: "1"\n          NIAKVIO_PRIMARY_FIXTURE: sinners-2025\n          NIAKVIO_PRIMARY_STREAM_SCOPE: all\n          NIAKVIO_REGRESSION_STREAM_SCOPE: all\n          NIAKVIO_REQUIRE_READER_SUCCESS: "1"\n',
        '          NIAKVIO_TARGET_FIXTURES: ${{ matrix.fixtures }}\n          NIAKVIO_TARGET_PROVIDER: all\n          NIAKVIO_TARGET_MANIFEST: manifest.json\n          NIAKVIO_READER_ACCEPTANCE: "1"\n          NIAKVIO_TV_PRIORITY_APPEND: "0"\n          NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES: "45"\n          NIAKVIO_TV_CHECKPOINT_DIR: ${{ github.workspace }}/native-evidence/tv/checkpoints\n          NIAKVIO_TV_RESUME_CHECKPOINT_DIR: ${{ github.workspace }}/native-evidence/tv/checkpoints\n          NIAKVIO_PRIMARY_FIXTURE: sinners-2025\n          NIAKVIO_PRIMARY_STREAM_SCOPE: all\n          NIAKVIO_REGRESSION_STREAM_SCOPE: all\n          NIAKVIO_REQUIRE_READER_SUCCESS: "1"\n',
        "TV shard runtime env",
    )
    text = replace_once(
        text,
        '''      - name: Diagnose complete TV evidence\n        if: always()\n        shell: bash\n        run: |\n          set -euo pipefail\n          for fixture in $NIAKVIO_REPRESENTATIVE_FIXTURES; do\n''',
        '''      - name: Diagnose complete TV shard evidence\n        if: always()\n        env:\n          NIAKVIO_TV_SHARD_FIXTURES: ${{ matrix.fixtures }}\n        shell: bash\n        run: |\n          set -euo pipefail\n          for fixture in $NIAKVIO_TV_SHARD_FIXTURES; do\n''',
        "TV shard diagnostics",
    )
    brain_download = '''      - name: Download representative TV evidence from this exact run\n        uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c\n        with:\n          name: native-tv-route-representative-${{ github.run_id }}\n          path: baseline-reader/tv\n'''
    bounded_download = '''      - name: Download all TV evidence shards from this exact attempt\n        uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c\n        with:\n          pattern: native-tv-route-representative-${{ github.run_id }}-attempt-${{ github.run_attempt }}-shard-*\n          path: baseline-reader/tv\n          merge-multiple: true\n'''
    text = replace_once(text, brain_download, bounded_download, "Brain TV shard merge")
    text = replace_once(
        text,
        '          name: native-tv-route-representative-${{ github.run_id }}\n',
        '          name: native-tv-route-representative-${{ github.run_id }}-attempt-${{ github.run_attempt }}-shard-${{ matrix.shard }}\n',
        "TV shard artifact name",
    )
    count_block = '''          echo "proposals=$COUNT" >> "$GITHUB_OUTPUT"\n          echo "FIELD_NATIVE_REPRESENTATIVE_REPAIR_BASELINE fixtures=3 proposals=$COUNT"\n          cat niakvio/native-reader-repair/repair-report.json\n'''
    bounded_block = '''          echo "proposals=$COUNT" >> "$GITHUB_OUTPUT"\n          if [[ "$COUNT" != "0" ]]; then\n            python3 niakvio/scripts/purify_native_reader_repair.py --output-dir niakvio/native-reader-repair\n            python3 niakvio/scripts/build_native_reader_retest_manifest.py \\\n              --manifest niakvio/native-reader-repair/manifest.json \\\n              --repair-report niakvio/native-reader-repair/repair-report.json \\\n              --output niakvio/native-reader-repair/retest-manifest.json \\\n              --scope-output niakvio/native-reader-repair/retest-scope.json\n          fi\n          echo "FIELD_NATIVE_REPRESENTATIVE_REPAIR_BASELINE fixtures=3 proposals=$COUNT"\n          cat niakvio/native-reader-repair/repair-report.json\n          if [[ "$COUNT" != "0" ]]; then cat niakvio/native-reader-repair/retest-scope.json; fi\n'''
    text = replace_once(text, count_block, bounded_block, "bounded Brain manifest build")
    text = replace_once(
        text,
        '--manifest native-reader-repair/manifest.json --provider all --streams all --initial',
        '--manifest native-reader-repair/retest-manifest.json --provider all --streams all --initial',
        "Brain first bounded retest prep",
    )
    text = replace_once(
        text,
        '      - name: Re-read every provider and returned stream for all representative routes after Brain mutation\n',
        '      - name: Re-read mutated providers plus deterministic sentinels after Brain mutation\n',
        "Brain bounded retest name",
    )
    text = replace_once(
        text,
        '          NIAKVIO_TARGET_MANIFEST: native-reader-repair/manifest.json\n',
        '          NIAKVIO_TARGET_MANIFEST: native-reader-repair/retest-manifest.json\n          NIAKVIO_TV_PRIORITY_APPEND: "0"\n          NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES: "45"\n',
        "Brain bounded retest env",
    )
    text = replace_once(
        text,
        '            niakvio/native-reader-repair/repair-report.json\n            niakvio/native-reader-repair/providers/*.js\n',
        '            niakvio/native-reader-repair/repair-report.json\n            niakvio/native-reader-repair/retest-manifest.json\n            niakvio/native-reader-repair/retest-scope.json\n            niakvio/native-reader-repair/providers/*.js\n',
        "Brain bounded evidence upload",
    )
    path.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    path = Path("tests/native_corpus_device_lab_test.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    "native-tv-route-representative-${{ github.run_id }}",\n',
        '    "native-tv-route-representative-${{ github.run_id }}-attempt-${{ github.run_attempt }}-shard-${{ matrix.shard }}",\n',
        "test TV artifact contract",
    )
    text = replace_once(
        text,
        '    "Re-read every provider and returned stream for all representative routes after Brain mutation",\n',
        '    "Re-read mutated providers plus deterministic sentinels after Brain mutation",\n',
        "test bounded Brain retest label",
    )
    text = replace_once(
        text,
        'assert android_reader.count(\'NIAKVIO_TARGET_FIXTURES: "sinners-2025 breaking-bad-s01e01 jujutsu-kaisen-s01e01"\') >= 3\n',
        'assert android_reader.count(\'NIAKVIO_TARGET_FIXTURES: "sinners-2025 breaking-bad-s01e01 jujutsu-kaisen-s01e01"\') >= 2\nassert \'matrix: ${{ fromJSON(needs.resolve.outputs.tv_shards) }}\' in android_reader\nassert \'NIAKVIO_TARGET_FIXTURES: ${{ matrix.fixtures }}\' in android_reader\nassert \'NIAKVIO_TV_PRIORITY_APPEND: "0"\' in android_reader\nassert \'NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES: "45"\' in android_reader\nassert \'merge-multiple: true\' in android_reader\nassert \'native-reader-repair/retest-manifest.json\' in android_reader\nassert \'build_native_reader_retest_manifest.py\' in android_reader\nassert \'NIAKVIO_TARGET_MANIFEST: native-reader-repair/manifest.json\' not in android_reader\n',
        "test TV shard topology",
    )
    text = replace_once(
        text,
        'assert "TV_PRIORITY_FIXTURES" in tv_suite\n',
        'assert "TV_PRIORITY_FIXTURES" in tv_suite\nassert "native_tv_route_checkpoint.py" in tv_suite\nassert "timeout --signal=TERM --kill-after=2m" in tv_suite\nassert "FIELD_NATIVE_CORPUS_TV_RESUME" in tv_suite\nassert "FIELD_NATIVE_CORPUS_TV_ROUTE_TIMEOUT" in tv_suite\n',
        "test TV runner resilience",
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_suite()
    patch_workflow()
    patch_tests()
    print("TV reader orchestration migration applied")
