#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import textwrap

ROOT = Path(__file__).resolve().parents[1]

memory = ROOT / "MEMORY.md"
text = memory.read_text(encoding="utf-8")
marker = "## 2026-09-07 — Accepted 5.21.37 / Terminal Session V29 / live-yield checkpoint"
if marker not in text:
    checkpoint = textwrap.dedent(r'''

    ## 2026-09-07 — Accepted 5.21.37 / Terminal Session V29 / live-yield checkpoint

    - **This checkpoint supersedes all earlier wording that says the public release is still 5.21.35 or that 5.21.36/5.21.37 is pending.** Current public release is **5.21.37**.
    - Publication workflow: `FIX - Publish Terminal Session V29`, run **34120732027**, job **101737919476**, completed success.
    - Final publication commit: **`6f74939efa11b2c886e82002c242b923a4f87f6c`** (`fix(core): publish terminal labels and stale-session isolation V29`). Push to `main` completed successfully.
    - Public manifests verified after push: `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json` all report **5.21.37**.
    - 96/96 published Provider JS were rematerialized and physically verified to contain `tmdb-data-contract-launch-gate-v29-native-abort-race`, `requestAbortPromise(controller,requestToken)`, and presentation client-projection V20.
    - V29 closes the stale-session hole where a native QuickJS fetch bridge may ignore `AbortSignal`: provider fetch now races the native call against request cancellation. Functional regression with an intentionally never-resolving old native fetch completed in ~1 ms after supersede and observed only `/1/one` then `/2/one`; superseded fallback `/1/two` never reached network.
    - Terminal stream-label bug was localized outside provider-specific quality calculation: Engine V2 accepted labels such as `Kehflix - Inconnue` as provider names. Engine V2 now strips terminal placeholder suffixes and mirrors final projected `title` into `name`, matching the client-facing Core projection. Placeholder quality (`Unknown`, `Inconnue`, `N/A`, etc.) collapses to provider-only; meaningful qualities remain, including `1080p` and `2160p -> 4K`.
    - `CORE.STREAM_SANITIZER.V6` output guard passed across all 96; release integrity and fixed-point override checks passed.
    - Nuvio client upstream drift seen during release: NuvioDesktop audited contract remained accepted; NuvioMobile had a safe upstream advance; NuvioTV had a separate semantic-sensitive subtitle-cache drift requiring review. Provider publication intentionally continued against pinned audited client contract refs.

    ### Live yield on exact 5.21.37 candidate

    - Interstellar matrix tested **55 enabled movie-capable providers**. Only **6** returned automatic streams: `castle`, `hindmoviez`, `streamflix`, `streamzo`, `videasy`, `wookafr`. VF automatic providers: **2**, `streamzo` + `wookafr`. **49/55** returned no streams. This is materially better than the earlier native observation of only StreamZo/Kehflix/Castle in one client session, but still far below the 96-provider objective and must not be considered provider recovery completion.
    - Notably Kehflix returned zero in the CI Interstellar matrix even though it is a known viable provider in other live/native fixtures; treat this as route/runtime/fixture evidence, not provider-wide disablement.
    - User Desktop anime fixture was correctly identified as **The Unwanted Undead Adventurer S01E02**, IMDb `tt30177477`, not Hell Mode. Candidate matrix tested **62 episodic/anime-capable providers**: **2 positive** (`anime-sama`, `neko-sama`), network reached **49**, successful provider HTTP **37**.
    - Secondary Hell Mode S01E12 (`tt38646634`) matrix produced the same provider-positive set: **2/62**, `anime-sama` + `neko-sama`; network reached 49, successful HTTP 36.
    - These anime results prove the global `series -> tv/anime` transport is not completely broken, but extraction/runtime route yield is still severely underperforming after successful network access for many providers.
    - User Desktop logs separately showed DNS/host failures including `api.nakios.live`, `*.eat-peach.sbs`, and VidLink-related traffic. Current main domains can be alive while historical/API subdomains or route families are stale; domain, route, extraction and player evidence must remain separately classified.

    ### Current priority after 5.21.37

    1. Keep V29 terminal-label/session isolation immutable while provider recovery continues.
    2. Resume **proof-first real route recovery across all 96**, including disabled/off rows for recoverability; test a route live at discovery time and never promote static fragments as executable routes.
    3. Use `MAIN - Route Proof Reconstruction 96` as a non-public candidate workflow. Its baseline must derive from `.github/triggers/route-proof-reconstruction.json`, not be hard-coded to 5.21.35.
    4. For every candidate, compare live yield against the accepted 5.21.37 baselines: Interstellar 6/55 automatic (2 VF), Unwanted Undead 2/62, Hell Mode 2/62. A structurally green reconstruction that does not improve/accurately explain these results is not completion.
    5. Route families already requiring scrutiny include VidLink historical `/api/b/...` versus current documented `/movie/{tmdbId}` and `/tv/{tmdbId}/{season}/{episode}`, and Nakios principal-site versus stale `api.nakios.live`. Do not replace routes solely from documentation; require provider-specific executable HTTP proof before promotion.
    6. Preserve the five Native Labs requirement after route/runtime stabilization: TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows.
    7. Continue automatic `MEMORY.md` checkpoints for every important green/red run, root cause, architecture change, publication, native proof, and security proof.
    ''').rstrip()
    memory.write_text(text.rstrip() + "\n" + checkpoint + "\n", encoding="utf-8")
    print("MEMORY_CHECKPOINT_52137_ADDED")
else:
    print("MEMORY_CHECKPOINT_52137_ALREADY_PRESENT")

wf = ROOT / ".github/workflows/main-route-proof-reconstruction.yml"
w = wf.read_text(encoding="utf-8")
old_baseline = '''      - name: Freeze exact 5.21.35 baseline
        shell: bash
        run: |
          set -euo pipefail
          cp manifest.json "$RUNNER_TEMP/manifest.before.json"
          cp provider-overrides.json "$RUNNER_TEMP/provider-overrides.before.json"
          cp automation/provider-v3-static-knowledge.json "$RUNNER_TEMP/static-knowledge.before.json"
          python -c "import json; m=json.load(open('manifest.json')); assert m.get('version')=='5.21.35',m.get('version'); assert len(m.get('scrapers') or [])==96; print('ROUTE_PROOF_BASELINE_OK version=5.21.35 providers=96')"
          git rev-parse HEAD | tee "$RUNNER_TEMP/base.sha"
'''
new_baseline = '''      - name: Freeze trigger-declared public baseline
        shell: bash
        run: |
          set -euo pipefail
          cp manifest.json "$RUNNER_TEMP/manifest.before.json"
          cp provider-overrides.json "$RUNNER_TEMP/provider-overrides.before.json"
          cp automation/provider-v3-static-knowledge.json "$RUNNER_TEMP/static-knowledge.before.json"
          python - <<'PY'
          import json
          manifest=json.load(open('manifest.json'))
          trigger=json.load(open('.github/triggers/route-proof-reconstruction.json'))
          expected=str(trigger.get('expectedPublicBaseline') or '').strip()
          assert expected, trigger
          assert manifest.get('version')==expected, (manifest.get('version'), expected)
          assert len(manifest.get('scrapers') or [])==96, len(manifest.get('scrapers') or [])
          print(f"ROUTE_PROOF_BASELINE_OK version={expected} providers=96")
          PY
          git rev-parse HEAD | tee "$RUNNER_TEMP/base.sha"
'''
if old_baseline in w:
    w = w.replace(old_baseline, new_baseline, 1)
elif "Freeze trigger-declared public baseline" not in w:
    raise SystemExit("route-proof baseline anchor not found")

hotd = '''      - name: Final real HOTD S3E1 proof - Kehflix and Purstream
        timeout-minutes: 8
        shell: bash
        run: |
          set -euo pipefail
          python scripts/hotd_s3e1_live_probe.py \\
            --output automation/hotd-s3e1-live.json \\
            --timeout 90

'''
compare = '''      - name: Compare candidate live yield with accepted 5.21.37 baseline
        timeout-minutes: 25
        shell: bash
        run: |
          set -euo pipefail
          python scripts/interstellar_nuvio_matrix.py --workers 12 --timeout 35 --output automation/interstellar-route-proof-matrix.json
          python scripts/desktop_series_provider_matrix.py \\
            --id tt30177477 \\
            --title "The Unwanted Undead Adventurer" \\
            --season 1 \\
            --episode 2 \\
            --category anime \\
            --workers 10 \\
            --timeout 35 \\
            --output automation/unwanted-undead-route-proof-matrix.json
          python scripts/desktop_series_provider_matrix.py \\
            --id tt38646634 \\
            --title "HELL MODE: The Hardcore Gamer Dominates in Another World with Garbage Balancing" \\
            --season 1 \\
            --episode 12 \\
            --category anime \\
            --workers 10 \\
            --timeout 35 \\
            --output automation/hellmode-route-proof-matrix.json
          python - <<'PY'
          import json
          from pathlib import Path
          i=json.loads(Path('automation/interstellar-route-proof-matrix.json').read_text())
          u=json.loads(Path('automation/unwanted-undead-route-proof-matrix.json').read_text())
          h=json.loads(Path('automation/hellmode-route-proof-matrix.json').read_text())
          print(
              'ROUTE_PROOF_LIVE_YIELD '
              f"interstellar={i.get('automatic_stream_provider_count',0)}/{i.get('enabled_movie_providers_tested',0)} "
              f"interstellar_vf={i.get('automatic_vf_provider_count',0)} "
              f"unwanted={u.get('positive_count',0)}/{u.get('providers_tested',0)} "
              f"hellmode={h.get('positive_count',0)}/{h.get('providers_tested',0)}"
          )
          PY

'''
if hotd in w and "Compare candidate live yield with accepted 5.21.37 baseline" not in w:
    w = w.replace(hotd, compare + hotd, 1)
elif "Compare candidate live yield with accepted 5.21.37 baseline" not in w:
    raise SystemExit("HOTD anchor not found")

artifact = "            automation/hotd-s3e1-live.json\n"
artifact_plus = (
    "            automation/hotd-s3e1-live.json\n"
    "            automation/interstellar-route-proof-matrix.json\n"
    "            automation/unwanted-undead-route-proof-matrix.json\n"
    "            automation/hellmode-route-proof-matrix.json\n"
)
if artifact in w and "automation/interstellar-route-proof-matrix.json" not in w.split("path: |", 1)[-1]:
    w = w.replace(artifact, artifact_plus, 1)
wf.write_text(w, encoding="utf-8")

trigger_path = ROOT / ".github/triggers/route-proof-reconstruction.json"
trigger = json.loads(trigger_path.read_text(encoding="utf-8"))
trigger["retry"] = int(trigger.get("retry") or 0) + 1
trigger["expectedPublicBaseline"] = "5.21.37"
trigger["targetVersion"] = "5.21.38-candidate"
trigger["requiredFinalProof"] = "proof-v5-96+interstellar+unwanted-undead+hellmode+hotd"
trigger["triggeredAfter"] = "6f74939efa11b2c886e82002c242b923a4f87f6c"
trigger_path.write_text(json.dumps(trigger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("ROUTE_PROOF_BASELINE_SYNCED expected=5.21.37")
